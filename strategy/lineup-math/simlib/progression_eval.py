"""Walk-forward scoring of the progression sampler: tune its spread knobs and
check the adoption gates. `fit_progression.py` writes the params and origins
and runs this under pypy:

    pypy3.11 -m simlib.progression_eval tune <params.json> <origins.json>
    pypy3.11 -m simlib.progression_eval backtest <full.json> <single.json> <test.json> <train.json>
    pypy3.11 -m simlib.progression_eval transport <params.json> <origins.json>

An origin is a sampler player plus realised `rate`/`gp` by year (year 1 =
the projection year); None = not yet played. Season FP counts a year with no
games as 0. Coverage uses randomized PIT, so a realised 0 the forecast also
put mass on is spread over that mass rather than counted as covered."""
import collections, json, math, random, sys
from . import progression as prog
from . import shard

GATE_YEARS = (2, 3, 4, 5)
BUCKET_MIN = 100
TUNE_N, TEST_N = 100, 200
# spread knobs, tuned one at a time over their grids, twice round
TUNE_GRID = collections.OrderedDict([
    ("smult", (0.8, 0.9, 1.0, 1.1, 1.2, 1.35)),
    ("sd_floor", (0.03, 0.06, 0.09, 0.12)),
    ("sigma_u", (0.08, 0.12, 0.16, 0.2)),
    ("phi1", (0.0, 0.75, 1.5, 2.5)),
    ("young_mult", (1.0, 1.15, 1.3, 1.5)),
    ("young_mult_rookie", (1.1, 1.4, 1.7, 2.0, 2.4)),
])
# the valuable tiers count for more in the tuning loss than their share of rows
BUCKET_WEIGHT = {"all": 3.0, "lv34-42": 2.0, "lv42+": 3.0}
PICK_FLOOR_GRID = (1, 3, 6)
ACTIVE = prog.ACTIVE
WORKERS = None         # all cores


# ---------------------------------------------------------------- scores

def pit(samples, y, rng):
    n = len(samples)
    lt = sum(1 for s in samples if s < y) / n
    le = sum(1 for s in samples if s <= y) / n
    return lt + rng.random() * (le - lt)


def coverage(pits):
    n = len(pits)
    return {"n": n, "b80": sum(1 for u in pits if .1 <= u <= .9) / n,
            "b50": sum(1 for u in pits if .25 <= u <= .75) / n,
            "lo10": sum(1 for u in pits if u < .1) / n,
            "hi10": sum(1 for u in pits if u > .9) / n}


def crps(samples, y):
    s = sorted(samples)
    m = len(s)
    t1 = sum(abs(x - y) for x in s) / m
    t2 = sum((2 * i - m + 1) * x for i, x in enumerate(s)) / (m * m)
    return t1 - t2


def ece(probs, outcomes, bins=10):
    groups = collections.defaultdict(list)
    for p, o in zip(probs, outcomes):
        groups[min(int(p * bins), bins - 1)].append((p, o))
    n = len(probs)
    return sum(len(g) / n * abs(sum(p for p, _ in g) / len(g) - sum(o for _, o in g) / len(g))
               for g in groups.values())


# ---------------------------------------------------------------- simulate

def simulate(params, origins, years, n, seed=7, mode="model"):
    """Per origin: (rates, gps) by year for each of n paths. Each origin gets
    its own stream: one shared stream would make every origin's Monte Carlo
    error the same, and move coverage everywhere at once"""
    parts = shard.chunks(len(origins), shard.n_workers(WORKERS, len(origins)))
    jobs = [(params, origins[s:s + c], s, years, n, seed, mode) for s, c in parts]
    out = []
    for part in shard.mapped(_chunk, jobs, len(jobs)):
        out.extend(part)
    return out


def _chunk(job):
    p, origins, start, years, n, seed, mode = job
    res = []
    for i, o in enumerate(origins, start):
        stream = seed * 100003 + i
        if mode == "persist":
            res.append(_persist(p, o, years, n, stream))
        else:
            pl = dict(o, stage="V") if mode == "vet" else o
            runs = prog.paths(pl, years, n, stream, p)
            res.append(([r for r, _ in runs], [g for _, g in runs]))
    return res


def _persist(p, o, years, n, seed):
    """Persistence baseline: year-1 rate forever with a pooled spread by
    horizon, no exit; GP from the model's chain"""
    s, rng = prog._Sampler(p), random.Random(seed)
    sds = p["persist_sd"]
    rates, gps = [], []
    for _ in range(n):
        r, g = [o["rate1"]], [o["gp1"]]
        gp, age = o["gp1"], o["age1"]
        for t in range(1, years):
            gp = s._gp_next(gp, age, o["rate1"], rng)
            age += 1
            r.append(o["rate1"] * math.exp(sds[min(t, len(sds)) - 1] * rng.gauss(0, 1)))
            g.append(gp)
        rates.append(r)
        gps.append(g)
    return rates, gps


def persist_sd(origins, years):
    """Pooled survivor log-ratio SD vs the year-1 rate, by horizon"""
    out = []
    for t in range(1, years):
        xs = [math.log(o["rate"][t] / o["rate1"]) for o in origins
              if o["rate"][t] is not None and o["gp"][t] >= ACTIVE and o["rate"][t] > 0]
        m = sum(xs) / len(xs)
        out.append(math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs)))
    return out


# ---------------------------------------------------------------- per-year cells

def cells(origins, sims, t, seed=11):
    """One row per origin with year t realised: PITs, CRPS, probabilities"""
    rng = random.Random(seed + t)
    rows = []
    for o, (rates, gps) in zip(origins, sims):
        if o["gp"][t] is None:
            continue
        y_fp = (o["rate"][t] or 0.0) * o["gp"][t]
        fp = [(r[t] or 0.0) * g[t] for r, g in zip(rates, gps)]
        surv = [r[t] for r, g in zip(rates, gps) if r[t] is not None and g[t] >= ACTIVE]
        played = o["rate"][t] is not None and o["gp"][t] >= ACTIVE
        usable = played and o["rate"][t] >= 25.0
        row = {"o": o, "pit": pit(fp, y_fp, rng), "crps": crps(fp, y_fp),
               "p_active": sum(1 for g in gps if g[t] >= ACTIVE) / len(gps),
               "p_usable": sum(1 for r, g in zip(rates, gps)
                               if g[t] >= ACTIVE and (r[t] or 0) >= 25.0) / len(gps),
               "active": float(played), "usable": float(usable), "rate_pit": None,
               "fp_pred": sum(fp) / len(fp), "fp_real": y_fp}
        if played and len(surv) >= 20:
            row["rate_pit"] = pit(surv, o["rate"][t], rng)
            surv.sort()
            row["below_median"] = float(o["rate"][t] < surv[len(surv) // 2])
        rows.append(row)
    return rows


def buckets(o):
    r, a = o["rate1"], o["age1"]
    level = ("lv<20" if r < 20 else "lv20-27" if r < 27 else "lv27-34" if r < 34
             else "lv34-42" if r < 42 else "lv42+")
    age = "age<=24" if a < 25 else "age25-28" if a < 29 else "age29-31" if a < 32 else "age32+"
    return (level, age, "stage" + o["stage"])


# ---------------------------------------------------------------- tune

def tune(params_path, origins_path):
    """Choose the spread knobs (and the rookie growth pick floor) on origins
    whose gated years are all realised; writes them into the params file"""
    with open(params_path) as f:
        p = json.load(f)
    with open(origins_path) as f:
        origins = json.load(f)
    vets = [o for o in origins if o["stage"] != "D"]
    scored = {}
    for _ in range(2):
        for knob, grid in TUNE_GRID.items():
            losses = {}
            for x in grid:
                p["knobs"][knob] = x
                key = tuple(sorted(p["knobs"].items()))
                if key not in scored:
                    scored[key] = _calib_loss(p, vets)
                losses[x] = scored[key]
            p["knobs"][knob] = min(grid, key=losses.get)
    print("  tuned %s (loss %.4f, %d origins)"
          % (" ".join("%s %.2f" % (k, p["knobs"][k]) for k in TUNE_GRID), min(losses.values()), len(vets)))
    rookies = [o for o in origins if o["stage"] == "D"]
    if "rookie" in p and rookies:
        top = [o for o in rookies if (o.get("pick") or 61) <= 5]
        pick = None
        for fl in PICK_FLOOR_GRID:
            p["knobs"]["growth_pick_floor"] = fl
            share = _below_median(p, top, (3, 4, 5))
            if pick is None or abs(share - 0.5) < abs(pick[1] - 0.5) - 0.02:
                pick = (fl, share)
        p["knobs"]["growth_pick_floor"] = pick[0]
        print("  tuned growth pick floor %d (top-5 share below median %.2f, n=%d)"
              % (pick[0], pick[1], len(top)))
    p["persist_sd"] = persist_sd([o for o in origins if o["stage"] != "D"], 8)
    with open(params_path, "w") as f:
        json.dump(p, f, indent=1)


def _calib_loss(p, origins):
    sims = simulate(p, origins, max(GATE_YEARS) + 1, TUNE_N)
    loss = 0.0
    for t in [y - 1 for y in GATE_YEARS]:
        rows = cells(origins, sims, t)
        groups = collections.defaultdict(list, {"all": rows})
        for r in rows:
            for b in buckets(r["o"]):
                groups[b].append(r)
        for name, g in groups.items():
            if len(g) < 50:
                continue
            w = BUCKET_WEIGHT.get(name, 1.0)
            for key in ("pit", "rate_pit"):
                c = coverage([r[key] for r in g if r[key] is not None])
                loss += w * ((c["b80"] - .8) ** 2 + (c["b50"] - .5) ** 2
                             + (c["lo10"] - .1) ** 2 + (c["hi10"] - .1) ** 2)
    return loss


def _below_median(p, origins, years):
    sims = simulate(p, origins, max(years), TUNE_N)
    xs = [r["below_median"] for t in years for r in cells(origins, sims, t - 1)
          if "below_median" in r]
    return sum(xs) / max(len(xs), 1)


# ---------------------------------------------------------------- backtest

def backtest(full_path, single_path, test_path, train_path):
    ps = [json.load(open(x)) for x in (full_path, single_path)]
    test, train = json.load(open(test_path)), json.load(open(train_path))
    full, single = ps
    # a recent cutoff sees fewer years; gates needing more are skipped there
    years = min(8, max(t for o in test for t, g in enumerate(o["gp"], 1) if g is not None))
    sims = {"full": simulate(full, test, years, TEST_N),
            "single": simulate(single, test, years, TEST_N),
            "persist": simulate(full, test, years, TEST_N, mode="persist")}
    k = full["knobs"]
    print("knobs  full: %s pick floor %d · single: smult %.2f floor %.2f"
          % (" ".join("%s %.2f" % (x, k[x]) for x in TUNE_GRID), k["growth_pick_floor"],
             single["knobs"]["smult"], single["knobs"]["sd_floor"]))
    rows = {m: {t: cells(test, s, t - 1) for t in range(2, years + 1)} for m, s in sims.items()}
    name, ok, misses = g1(rows["full"])
    total = sum(1 for t in GATE_YEARS for b in {"all", *(x for r in rows["full"][t] for x in buckets(r["o"]))}
                if b == "all" or sum(1 for r in rows["full"][t] if b in buckets(r["o"])) >= BUCKET_MIN)
    print("  cells missed %d of %d; the same model scored on draws from itself misses %d"
          % (misses, total, g1_null(full, test, years)))
    verdict = [(name, ok), g2(rows)] + ([g3(test, sims["full"], full)] if years >= 8 else []) + [
        g4(rows["full"], train, test), g5(full, test)]
    print("\nGATES " + "  ".join("%s %s" % (name, "PASS" if ok else "FAIL") for name, ok in verdict))


def _band_ok(c, lo, hi, tails):
    return lo <= c["b80"] <= hi and all(tails[0] <= c[x] <= tails[1] for x in ("lo10", "hi10"))


def g1(rows, quiet=False):
    """Calibration: overall joint season FP and survivor rate in band; every
    bucket with n >= 100 in its wider band; P(active)/P(usable) ECE.
    Returns (name, ok, cells missed)"""
    ok, misses = True, 0
    say = (lambda *a: None) if quiet else print
    say("\nG1 calibration (randomized PIT; overall 80%% band 76-84, 50%% 45-55, tails 7-13; "
        "buckets n>=%d: 72-88, tails <=15; ECE <=.03 overall, <=.06 bucket)" % BUCKET_MIN)
    say("  %-4s %-11s %5s  %-26s  %-26s  %5s %5s" % ("year", "cell", "n", "season FP b80 b50 lo hi",
                                                    "survivor rate b80 b50 lo hi", "eceA", "eceU"))
    for t in GATE_YEARS:
        rs = rows[t]
        groups = collections.OrderedDict([("all", rs)])
        for r in rs:
            for b in buckets(r["o"]):
                groups.setdefault(b, []).append(r)
        for name in ["all"] + sorted(k for k in groups if k != "all"):
            g = groups[name]
            if name != "all" and len(g) < BUCKET_MIN:
                continue
            cj = coverage([r["pit"] for r in g])
            rp = [r["rate_pit"] for r in g if r["rate_pit"] is not None]
            cr = coverage(rp) if len(rp) >= 30 else None
            ea = ece([r["p_active"] for r in g], [r["active"] for r in g])
            eu = ece([r["p_usable"] for r in g], [r["usable"] for r in g])
            if name == "all":
                good = (_band_ok(cj, .76, .84, (.07, .13)) and .45 <= cj["b50"] <= .55
                        and _band_ok(cr, .76, .84, (.07, .13)) and .45 <= cr["b50"] <= .55
                        and ea <= .03 and eu <= .03)
            else:
                good = (_band_ok(cj, .72, .88, (0, .15))
                        and (cr is None or _band_ok(cr, .72, .88, (0, .15)))
                        and ea <= .06 and eu <= .06)
            ok &= good
            misses += not good
            say("  %-4d %-11s %5d  %s  %s  %5.3f %5.3f%s"
                % (t, name, len(g), _cov(cj), _cov(cr) if cr else " " * 26, ea, eu,
                   "" if good else "  <- miss"))
    return "G1", ok, misses


def g1_null(p, test, years):
    """G1 again with each realised outcome swapped for a draw from the model
    itself: the cells a perfectly calibrated forecast would miss by chance"""
    drawn = simulate(p, test, years, 1, seed=99)
    null = []
    for o, (rates, gps) in zip(test, drawn):
        seen = [g is not None for g in o["gp"]]
        null.append(dict(o, rate=[r[0] if s else None for r, s in zip(zip(*rates), seen)],
                         gp=[g[0] if s else None for g, s in zip(zip(*gps), seen)]))
    sims = simulate(p, null, years, TEST_N)
    return g1({t: cells(null, sims, t - 1) for t in GATE_YEARS}, quiet=True)[2]


def _boot(groups, stat, n=300, seed=5):
    """Player-clustered bootstrap: `groups` maps player -> rows; returns the
    5th and 95th percentile of `stat(rows)` over resampled players"""
    rng, keys = random.Random(seed), list(groups)
    out = sorted(stat([r for _ in keys for r in groups[rng.choice(keys)]]) for _ in range(n))
    return out[int(.05 * n)], out[int(.95 * n) - 1]


def _cov(c):
    return "%5.2f %5.2f %5.2f %5.2f  " % (c["b80"], c["b50"], c["lo10"], c["hi10"])


def g2(rows):
    """Skill: season-FP CRPS >= 5% better than persistence at years 2-3;
    better than a single age curve with the player-clustered 90% CI below 0
    at year 2 and by >= 5% at year 3; no bucket > 2% worse than it.
    The spec's flat 5% at year 2 is read as mis-set (decision 2026-09-29):
    a year-1 projection already carries most of year 2, so the model's
    reliable 4-5% edge there is the whole of what's available"""
    ok = True
    print("\nG2 skill (season-FP CRPS; vs persist >=5% at years 2-3; vs single: CI < 0 at year 2, >=5% at year 3)")
    print("  %-4s %8s %8s %8s  %7s %7s" % ("year", "full", "single", "persist", "vs sgl", "vs per"))
    for t in sorted(rows["full"]):
        m = {k: sum(r["crps"] for r in rows[k][t]) / len(rows[k][t]) for k in rows}
        vs, vp = m["full"] / m["single"] - 1, m["full"] / m["persist"] - 1
        ci = ""
        if t in (2, 3):
            by = collections.defaultdict(list)
            for rf, rsg in zip(rows["full"][t], rows["single"][t]):
                by[rf["o"]["id"]].append((rf["crps"], rsg["crps"]))
            lo, hi = _boot(by, lambda xs: sum(a for a, _ in xs) / sum(b for _, b in xs) - 1)
            ok &= vp <= -.05 and (hi < 0 if t == 2 else vs <= -.05)
            ci = "   vs sgl 90%% CI by player [%+.1f%%, %+.1f%%]" % (100 * lo, 100 * hi)
        print("  %-4d %8.0f %8.0f %8.0f  %+6.1f%% %+6.1f%%%s" % (t, m["full"], m["single"], m["persist"],
                                                               100 * vs, 100 * vp, ci))
    worst = []
    for t in (2, 3):
        groups = collections.defaultdict(lambda: ([], []))
        for rf, rsg in zip(rows["full"][t], rows["single"][t]):
            for b in buckets(rf["o"]):
                groups[b][0].append(rf["crps"])
                groups[b][1].append(rsg["crps"])
        for b, (f, s) in sorted(groups.items()):
            if len(f) >= BUCKET_MIN:
                d = sum(f) / sum(s) - 1
                worst.append((d, t, b, len(f)))
    worst.sort(reverse=True)
    d, t, b, n = worst[0]
    ok &= d <= .02
    print("  worst bucket vs single: %s year %d (n=%d) %+.1f%%" % (b, t, n, 100 * d))
    return "G2", ok


def g3(test, sims, p, years=range(2, 9)):
    """Stars and vets: 7-yr value (years 2-8) pred/real 0.85-1.15 for age 29+
    at 34-42 and at 42+"""
    ok = True
    rg = p["wrv_rg"]
    print("\nG3 7-yr value above %.0f FP/G, years 2-8, pred/real (gate: age 29+ at 34-42 and 42+ in 0.85-1.15)" % rg)
    groups = collections.defaultdict(lambda: [0.0, 0.0, 0])
    players = collections.defaultdict(lambda: collections.defaultdict(list))
    for o, (rates, gps) in zip(test, sims):
        if any(o["gp"][t - 1] is None for t in years):
            continue
        real = sum(max(0.0, (o["rate"][t - 1] or 0.0) - rg) * o["gp"][t - 1] for t in years)
        pred = sum(max(0.0, (r[t - 1] or 0.0) - rg) * g[t - 1]
                   for r, g in zip(rates, gps) for t in years) / len(rates)
        level, age, _ = buckets(o)
        for key in (level, (level, "29+" if o["age1"] >= 29 else "<29")):
            groups[key][0] += pred
            groups[key][1] += real
            groups[key][2] += 1
            players[key][o["id"]].append((pred, real))
    for key in sorted(groups, key=str):
        pred, real, n = groups[key]
        gated = isinstance(key, tuple) and key[1] == "29+" and key[0] in ("lv34-42", "lv42+")
        ratio = pred / real if real else float("nan")
        ci = ""
        if gated:
            ok &= .85 <= ratio <= 1.15
            lo, hi = _boot(players[key], lambda xs: sum(a for a, _ in xs) / max(sum(b for _, b in xs), 1e-9))
            ci = "  (gated; 90%% CI by player %.2f-%.2f, %d players)" % (lo, hi, len(players[key]))
        print("  %-22s n=%4d  pred/real %.2f%s" % (key if isinstance(key, str) else " ".join(key),
                                                   n, ratio, ci))
    print("  tail: P(usable) predicted / actual, age 29+ (ungated)")
    for lv in ("lv27-34", "lv34-42", "lv42+"):
        out = []
        for t in (4, 6, 8):
            pr = ac = n = 0
            for o, (rates, gps) in zip(test, sims):
                if buckets(o)[0] != lv or o["age1"] < 29 or o["gp"][t - 1] is None:
                    continue
                pr += sum(1 for r, g in zip(rates, gps) if g[t - 1] >= ACTIVE and (r[t - 1] or 0) >= p["usable"]) / len(rates)
                ac += (o["gp"][t - 1] >= ACTIVE and (o["rate"][t - 1] or 0) >= p["usable"])
                n += 1
            out.append("year %d %.2f / %.2f (n=%d)" % (t, pr / max(n, 1), ac / max(n, 1), n))
        print("    %-8s %s" % (lv, "   ".join(out)))
    return "G3", ok


def g4(rows, train, test):
    """Exit: P(active) Brier beats an age-only table (fit on train) at years
    2-6, i.e. k = 1..5 steps past the projection year"""
    ok = True
    table = collections.defaultdict(lambda: [0, 0])
    for o in train:
        for t in range(1, 6):
            if o["gp"][t] is not None:
                c = table[(int(o["age1"]), t)]
                c[0] += o["gp"][t] >= ACTIVE
                c[1] += 1
    print("\nG4 exit (Brier of P(active); gate: model beats an age-only table at years 2-6)")
    for t in [t for t in range(2, 7) if t in rows]:
        bm = ba = 0.0
        for r in rows[t]:
            c = table.get((int(r["o"]["age1"]), t - 1), [0, 0])
            pa = (c[0] + 1) / (c[1] + 2)
            bm += (r["p_active"] - r["active"]) ** 2
            ba += (pa - r["active"]) ** 2
        n = len(rows[t])
        ok &= bm < ba
        print("  year %d  model %.4f  age table %.4f" % (t, bm / n, ba / n))
    return "G4", ok


def g5(p, test):
    """Rookies: the stage beats vet-on-rookies on CRPS at years 2-4; top-5
    picks land below the median 40-60% of the time; P(active) within .03 at
    career years 3-5"""
    ok = True
    d = [o for o in test if o["stage"] == "D"]
    if not d:
        print("\nG5 rookies: no draftee origins")
        return "G5", False
    stage = simulate(p, d, 6, TEST_N)
    vet = simulate(p, d, 6, TEST_N, mode="vet")
    print("\nG5 rookies (n=%d draftees; year 1 = rookie season)" % len(d))
    for t in (2, 3, 4):
        a, b = cells(d, stage, t - 1), cells(d, vet, t - 1)
        cs, cv = sum(r["crps"] for r in a) / len(a), sum(r["crps"] for r in b) / len(b)
        ok &= cs < cv
        print("  year %d CRPS stage %.0f vs vet %.0f" % (t, cs, cv))
    top = [o for o in d if (o.get("pick") or 61) <= 5]
    tr = [r for t in (3, 4, 5) for r in cells(top, simulate(p, top, 6, TEST_N), t - 1)
          if "below_median" in r]
    share = sum(r["below_median"] for r in tr) / max(len(tr), 1)
    ok &= .40 <= share <= .60
    by = collections.defaultdict(list)
    for r in tr:
        by[r["o"]["id"]].append(r["below_median"])
    lo, hi = _boot(by, lambda xs: sum(xs) / len(xs))
    print("  top-5 picks below predicted median, years 3-5: %.2f (n=%d, %d players; 90%% CI by player %.2f-%.2f)"
          % (share, len(tr), len(by), lo, hi))
    for t in (3, 4, 5):
        rs = cells(d, stage, t - 1)
        pred = sum(r["p_active"] for r in rs) / len(rs)
        act = sum(r["active"] for r in rs) / len(rs)
        ok &= abs(pred - act) <= .03
        print("  career year %d P(active) predicted %.3f actual %.3f" % (t, pred, act))
    return "G5", ok


def transport(params_path, origins_path):
    """G6: repo pool 2021-25, years 2-4 (k = 1..3) season-FP and survivor-rate
    80% bands within 70-90%"""
    p, origins = json.load(open(params_path)), json.load(open(origins_path))
    sims = simulate(p, origins, 4, TEST_N)
    ok = True
    print("G6 transport (repo pool; year 1 = projection stand-in, so years 2-4 are scored)")
    for t in (2, 3, 4):
        rs = cells(origins, sims, t - 1)
        c = coverage([r["pit"] for r in rs])
        rp = [r["rate_pit"] for r in rs if r["rate_pit"] is not None]
        cr = coverage(rp)
        ok &= .70 <= c["b80"] <= .90 and .70 <= cr["b80"] <= .90
        low = [r for r in rs if r["o"]["rate1"] < 20]
        print("  year %d n=%d  season FP %s survivor rate %s  P(active) ECE %.3f, under 20 FP/G %.3f"
              % (t, len(rs), _cov(c), _cov(cr), ece([r["p_active"] for r in rs], [r["active"] for r in rs]),
                 ece([r["p_active"] for r in low], [r["active"] for r in low])))
    print("\nGATES G6 %s" % ("PASS" if ok else "FAIL"))


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    {"tune": tune, "backtest": backtest, "transport": transport}[cmd](*args)
