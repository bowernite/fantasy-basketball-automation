"""Player progression for every rostered player: FP/G, GP and P(still
playing) by future season, and the 20-season weighted value.

    ./run sim.py progression                                   # the table
    ./run -m simlib.reports.progression player "Cade Cunningham"  # 20 years, one player
    ./run -m simlib.reports.progression freeze                 # preseason archive (each October)
"""
import csv, glob, json, math, os, re, shutil, sys
import fetch_data
from fetch_data import LIVE_SEASON, LIVE_TAG, SEASON, SEASON_TAG
from .. import progression as prog, roster as roster_mod
from ..board import _key, pool
from ..data import DATA_DIR, HERE, ROSTER_DIR, _load
from ..gp import age_at
from ..projections import projected_rate
from ..stats import ols

YEARS, PATHS = 20, 1000
SHOWN = (2, 3, 5, 10)                  # year indexes the table prints
EVALS = os.path.join(HERE, os.pardir)
SKILLS = os.path.join(EVALS, os.pardir, ".claude", "skills")
SNAPSHOTS = os.path.join(EVALS, "board-snapshots")
INJURY = os.path.join(SNAPSHOTS, "projections", "injury-overrides.json")
ARCHIVE = os.path.join(SNAPSHOTS, "archive")
BBREF = "bbref-%s.json" % SEASON_TAG
STAR_HINGES = (38, 46)                 # FP/G


def report_progression():
    rows, unplaced = rostered()
    runs = prog.project_many([pl for _, pl, _ in rows], YEARS, PATHS)
    p = prog.params()
    print("PROGRESSION  per player, %d paths, params fit %s through %d-%02d (%s)"
          % (PATHS, p["fit"]["date"], p["fit"]["through_season"] - 1,
             p["fit"]["through_season"] % 100, os.path.basename(prog.PARAMS)))
    print("Year 1 (%s) is the projection as-is; spread starts in year 2. Rate cells"
          % _label(1))
    print("  are FP/G among paths that play >= %d GP: median [p10-p90]. P(act) ="
          % prog.ACTIVE)
    print("  plays >= %d GP; P(use) = also >= %.0f FP/G. Stg: D draftee, S one NBA"
          % (prog.ACTIVE, p["usable"]))
    print("  season done, V vet. WRV = sum over 20 seasons of E[GP x max(0, FP/G - %.0f)],"
          % p["wrv_rg"])
    print("  years 1-7 weighted 1.0, then 0.95^(t-7); split 1-3 / 4-7 / 8-20 in 1000s.")
    print("  Diagnostic only: not BASE, not Delta w, not in Score. Beyond year 7 the")
    print("  backtest has little to check against. Flags: noproj (no feed rate), noBPM,")
    print("  board+/- (board ranks him well below/above his inputs: review), inj x (override),")
    print("  noBBRef (no BBRef join: career year off the pool, no BPM), noDOB (no birthday\n"
          "  in the pool or either Dizzle tab: not projected).")
    head = "  %-24s  %-7s %4s %3s  %11s  " % ("player", "owner", "age", "stg", _label(1) + " /GP")
    head += "  ".join("%-17s" % (_label(t) + " FP/G") for t in SHOWN[:3])
    head += "  %-14s  %-11s  %s" % (_label(SHOWN[3]) + " FP/G", "P(act/use)5", "WRV 1-3/4-7/8-20 = tot")
    print("\n" + head)
    order = sorted(zip(rows, runs), key=lambda x: (x[0][0], -prog.wrv(x[1])))
    for (owner, pl, flags), ys in order:
        print(_row(owner, pl, flags, ys))
    for owner, name in unplaced:
        print("  %-24s  %-7s %4s  noDOB" % (name, owner, "-"))


def _row(owner, pl, flags, ys):
    w = [sum(y.value * prog.weight(t) for t, y in enumerate(ys, 1) if lo <= t <= hi) / 1000
         for lo, hi in ((1, 3), (4, 7), (8, YEARS))]
    cells = "  ".join("%-17s" % _band(ys[t - 1]) for t in SHOWN[:3])
    y5 = ys[4]
    return ("  %-24s  %-7s %4.1f %3s  %5.1f / %3.0f  %s  %-14s  %.2f / %.2f  %4.1f/%4.1f/%4.1f = %5.1f  %s"
            % (pl["name"], owner, pl["age1"], pl["stage"], pl["rate1"], pl["gp1"], cells,
               _band(ys[SHOWN[3] - 1], short=True), y5.p_active, y5.p_usable,
               w[0], w[1], w[2], sum(w), " ".join(flags))).rstrip()


def _band(y, short=False):
    if y.rate_p50 is None:
        return "-"
    if short:
        return "%.1f" % y.rate_p50
    return "%.1f [%.0f-%.0f]" % (y.rate_p50, y.rate_p10, y.rate_p90)


def _label(t):
    y = LIVE_SEASON + t - 1
    return "'%02d-%02d" % (y % 100, (y + 1) % 100)


# ---------------------------------------------------------------- inputs

def rostered():
    """([(owner, player, flags)], [(owner, name)]) over all 12 roster files:
    the projectable, then those with no birthday anywhere"""
    owners, bb, injured = owner_names(), _load(BBREF), injury_overrides()
    newbies = newcomers()
    out, unplaced = [], []
    for path in sorted(glob.glob(os.path.join(ROSTER_DIR, "roster-*-%s.json" % SEASON_TAG))):
        tid = os.path.basename(path).split("-")[1]
        owner = owners.get(tid, tid)
        for row in roster_mod.our_roster(path):
            pl = _vet(row, bb.get(row["n"])) or _draftee(row, newbies.get(_key(row["n"])))
            if pl:
                out.append((owner, pl, []))
            else:
                unplaced.append((owner, row["n"]))
    for _, pl, flags in out:
        if projected_rate(pl["name"]) is None:
            flags.append("noproj")
        if pl["stage"] != "D" and pl["name"] not in bb:
            flags.append("noBBRef")
        elif pl["stage"] != "D" and pl["bpm"] is None:
            flags.append("noBPM")
        hurt = injured.get(_key(pl["name"]))
        if hurt:
            pl["rate_mult"] = hurt["rate_mult"]
            flags.append("inj x%.2f" % hurt["rate_mult"])
    for (_, pl, flags), bres in zip(out, board_residuals([pl for _, pl, _ in out])):
        pl["bres"] = bres
        if bres is not None and abs(bres) > prog.params()["board"]["flag"]:
            flags.append("board%+.1f" % bres)
    return out, unplaced


def _vet(row, bb):
    v = pool().get(row["n"]) or {}
    if not v.get("born"):
        return None
    age1 = age_at(v["born"], LIVE_SEASON)
    debut = bb["debut"] if bb else min(int(y) for y in v["seasons"])
    cy1 = LIVE_SEASON - debut + 1
    last = v.get("seasons", {}).get(str(SEASON))
    return {"name": row["n"], "tm": row["tm"], "rate1": max(row["avg"], prog.MIN_RATE),
            "gp1": float(row["gp"]), "age1": age1, "cy1": cy1,
            "stage": "D" if cy1 <= 1 else "S" if cy1 == 2 else "V",
            "bpm": bb and bb["bpm"], "gp_last": float(last[1]) if last else None,
            "pick": bb and bb["pick"], "age_rookie": age1 - (cy1 - 1)}


def _draftee(row, rk):
    """A rostered player with no NBA season, so none in the pool"""
    if not rk:
        return None
    age1 = age_at(rk["born"], LIVE_SEASON)
    return {"name": row["n"], "tm": row["tm"], "rate1": max(row["avg"], prog.MIN_RATE),
            "gp1": float(row["gp"]), "age1": age1, "cy1": 1, "stage": "D", "bpm": None, "gp_last": None,
            "pick": rk["pick"], "age_rookie": age1}


def newcomers():
    """key(name) -> {born, pick (NBA overall)} for players the pool can't carry.
    The Dizzle rookie tab wins (`Draft Pick` is round.pick, 30 a round); the
    dynasty tab covers earlier draftees, their pick off BBRef's draft history"""
    dz = os.path.join(SNAPSHOTS, "dizzle-dynasty")
    picks = _nba_picks()
    out = {}
    for row in _csv(_base().newest(dz)):
        if row.get("DOB"):
            out[_key(row["Player"])] = {"born": row["DOB"], "pick": picks.get(_key(row["Player"]))}
    for row in _csv(_base().newest(dz, "rookie-ranks-points.csv")):
        m = re.match(r"(\d)\.(\d+)$", (row.get("Draft Pick") or "").strip())
        if row.get("DOB"):
            out[_key(row["Player"])] = {
                "born": row["DOB"],
                "pick": (int(m.group(1)) - 1) * 30 + int(m.group(2).ljust(2, "0")) if m else None}
    return out


def _nba_picks():
    """key(name) -> NBA overall pick, the newest draft winning a shared name"""
    rows = _csv(os.path.join(fetch_data.bbref_mirror(), "Draft Pick History.csv"))
    out = {}
    for r in sorted(rows, key=lambda r: -int(r["season"])):
        if r["lg"] == "NBA" and r["overall_pick"].isdigit():
            out.setdefault(_key(r["player"]), int(r["overall_pick"]))
    return out


def _csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def owner_names():
    """team_id -> the owner Name we call each team by (`team-info`)"""
    path = os.path.join(SKILLS, "team-info", "team-info.md")
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 5 and cells[1].isdigit():
                out[cells[1]] = cells[4]
    return out


def injury_overrides():
    """key(name) -> row of the manual major-injury file"""
    if not os.path.isfile(INJURY):
        return {}
    with open(INJURY) as f:
        return {_key(n): r for n, r in json.load(f).get("players", {}).items()}


def board_residuals(players):
    """Per player, the log BASE-blend rank left over once the model's own
    inputs (level, age, BPM, GP, stage) are fitted out, refit on this set.
    Positive = the boards rank him worse than those inputs imply. None where
    no board carries him"""
    ranks = [_board_rank(pl) for pl in players]
    s = prog._Sampler(prog.params())
    feats = [_bres_features(pl, s) for pl in players]
    fit = [(f, math.log(r)) for f, r in zip(feats, ranks) if r is not None]
    beta = ols([f for f, _ in fit], lambda f: f, [y for _, y in fit])
    return [None if r is None else
            math.log(r) - beta[0] - sum(b * x for b, x in zip(beta[1:], f))
            for f, r in zip(feats, ranks)]


def _bres_features(pl, sampler):
    lL = math.log(pl["rate1"] / 30)
    a = pl["age1"] - 28
    # log rank bends hard at the very top; without the hinges every star reads board-loved
    top = [max(lL - math.log(x / 30), 0.0) for x in STAR_HINGES]
    return (lL, lL * lL, *top, a, a * a, a * lL, sampler._bpm(pl)[0],
            math.log(max(pl["gp1"], 1.0)), float(pl["stage"] == "D"), float(pl["stage"] == "S"))


def _board_rank(pl):
    """BASE's blend (`eval-player/base.py`), read back as the rank it is worth"""
    base = _base()
    k = base.key(pl["name"])
    num = tot = 0.0
    seen = False
    for (name, w, _, _, _, _), b in zip(base.BOARDS, _boards()):
        if not w:
            continue
        try:
            r = base.pick(b.get(k) or [], pl["tm"], k in _collisions())
        except base.Refused:
            return None
        seen |= r is not None
        num, tot = num + w * (_V()(r) if r is not None else 0.0), tot + w
    if not seen:
        return None
    blend = num / tot
    a, D = math.sqrt(_D()), _D()
    K = 9999 * (a + 1) / (D - 1)
    return min(max((K * D - blend * a) / (blend + K), 1.0), float(D))


def _base():
    path = os.path.join(SKILLS, "eval-player")
    if path not in sys.path:
        sys.path.insert(0, path)
    import base
    return base


_CACHE = {}


def _boards():
    if "boards" not in _CACHE:
        base = _base()
        _CACHE["boards"] = [base.load(p, rc, nc, tc) for _, _, p, rc, nc, tc in base.BOARDS]
    return _CACHE["boards"]


def _collisions():
    return {k for b in _boards() for k, hits in b.items() if len(hits) > 1}


def _D():
    return _base().TEAMS * _base().ROSTER_SIZE


def _V():
    return _base().curve(_D())[1]


# ---------------------------------------------------------------- CLI

def detail(names):
    projected, unplaced = rostered()
    rows = {pl["name"]: (owner, pl, flags) for owner, pl, flags in projected}
    for name in names:
        if name in {n for _, n in unplaced}:
            sys.exit("%s: no birthday in the pool or either Dizzle tab -- not projected" % name)
        if name not in rows:
            sys.exit("%s: not on a roster -- spelling as in the roster files" % name)
        owner, pl, flags = rows[name]
        ys = prog.project(pl, YEARS, PATHS)
        print("%s (%s, age %.1f, stage %s, BPM %s, board resid %s) %s"
              % (name, owner, pl["age1"], pl["stage"], _fmt(pl["bpm"]), _fmt(pl.get("bres")),
                 " ".join(flags)))
        print("  %-6s %-18s %5s %6s %6s  %-17s %7s" % ("year", "FP/G p50 [p10-p90]", "E[GP]",
                                                     "P(act)", "P(use)", "season FP p10/50/90", "value"))
        for t, y in enumerate(ys, 1):
            print("  %-6s %-18s %5.1f %6.2f %6.2f  %5.0f/%5.0f/%5.0f %7.0f"
                  % (_label(t), _band(y), y.gp_mean, y.p_active, y.p_usable,
                     y.fp_p10, y.fp_p50, y.fp_p90, y.value))
        print("  WRV %.0f\n" % prog.wrv(ys))


def _fmt(x):
    return "-" if x is None else "%+.2f" % x


def freeze():
    """Archive this preseason's inputs and outputs once: the only way to
    measure the feed's year-1 error and refit the board term later"""
    dest = os.path.join(ARCHIVE, "%s-preseason" % LIVE_TAG)
    if os.path.exists(dest):
        sys.exit("%s already exists -- a preseason is frozen once" % dest)
    rows, unplaced = rostered()
    runs = prog.project_many([pl for _, pl, _ in rows], YEARS, PATHS)
    os.makedirs(dest)
    for src in freeze_sources():
        shutil.copy2(src, dest)
    with open(os.path.join(dest, "progression.json"), "w") as f:
        json.dump([{"owner": o, "player": pl, "flags": fl, "wrv": prog.wrv(ys),
                    "years": [y._asdict() for y in ys]}
                   for (o, pl, fl), ys in zip(rows, runs)], f, indent=0)
    print("froze %d players and %d inputs into %s" % (len(rows), len(freeze_sources()), dest))
    if unplaced:
        print("not frozen, no birthday: %s" % ", ".join(n for _, n in unplaced))


def freeze_sources():
    proj = os.path.join(SNAPSHOTS, "projections")
    dz = os.path.join(SNAPSHOTS, "dizzle-dynasty")
    ht = os.path.join(SNAPSHOTS, "hashtag-basketball")
    return [p for p in (
        os.path.join(proj, "sleeper-%d.json" % LIVE_SEASON),
        os.path.join(proj, "hashtag-gp-%d.json" % LIVE_SEASON),
        os.path.join(proj, "fanscout-gp-%d.json" % LIVE_SEASON),
        os.path.join(proj, "overrides-%d.json" % LIVE_SEASON), INJURY,
        _base().newest(dz), _base().newest(dz, "rookie-ranks-points.csv"),
        os.path.join(ht, "expert-dynasty-points.csv"), os.path.join(ht, "manifest.csv"),
        os.path.join(DATA_DIR, BBREF), prog.PARAMS) if os.path.isfile(p)]


if __name__ == "__main__":
    cmd = sys.argv[1:2]
    if cmd == ["player"] and sys.argv[2:]:
        detail(sys.argv[2:])
    elif cmd == ["freeze"]:
        freeze()
    else:
        sys.exit(__doc__)
