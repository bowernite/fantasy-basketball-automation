"""Every team's PF, PF rank and P(title) by season, seasons 1-7: all 12
rosters rolled forward on progression paths, with exits, drafts off the pick
ledger (`fetch_data.py picks`) and cuts to 38. No trades."""
import datetime, json, os, statistics, tempfile, time
from fetch_data import LIVE_SEASON, SEASON_TAG
from .. import bracket, future, progression as prog, title
from ..data import ROSTER_DIR, _load
from ..roster import our_roster
from ..score import board_base
from . import progression as players

PATHS, SEED, YEARS = 300, 1, 7
T_ENG, T_IN = 10, 200          # inner trials per team-season; the paths carry the spread
LAST = os.path.join(tempfile.gettempdir(), "ff-sim-future-last.json")
LEDGER = "picks-%s.json" % SEASON_TAG


def report_future():
    t0 = time.time()
    start, template, flat = inputs()
    ledger, fetched = pick_ledger()
    teams1 = bracket.team_levels()
    title1 = title.full_season(teams1)
    runs = future.simulate(start, teams1, ledger, template, PATHS, SEED, YEARS, T_ENG, T_IN)
    out = summary(runs, teams1, title1)
    _preamble(fetched, flat)
    _main_table(out)
    _picks_table(out)
    _delta(out)
    _save(out)
    print("\nran in %.0f s (%d paths x %d seasons x 12 teams; %d engine / %d title trials each)"
          % (time.time() - t0, PATHS, YEARS - 1, T_ENG, T_IN))


def _label(t):
    y = LIVE_SEASON + t
    return "'%02d-%02d" % (y % 100, (y + 1) % 100)


# ---------------------------------------------------------------- inputs

def inputs():
    """({team path: [{row, pl, base}]}, the 48-rookie class template best
    first, names held flat for want of a birthday)"""
    owners = players.owner_names()
    placed, unplaced = players.rostered()
    by_name = {(o, pl["name"]): pl for o, pl, _ in placed}
    rosters = {p: our_roster(p) for p in _roster_paths()}
    base = board_base([r for rows in rosters.values() for r in rows])
    start = {}
    for path, rows in rosters.items():
        owner = owners.get(path.split("-")[1])
        start[path] = [{"row": r, "pl": by_name.get((owner, r["n"])), "base": base[r["n"]]}
                       for r in rows]
    rookies = sorted((e for es in start.values() for e in es if e["pl"] and e["pl"]["stage"] == "D"),
                     key=lambda e: (-e["base"], e["pl"]["pick"] or 99))
    picks = future.ROUNDS * len(start)
    if len(rookies) < picks:
        raise ValueError("%d rostered draftees for a %d-pick class template" % (len(rookies), picks))
    template = [dict(e["pl"], bres=None, rate_mult=None, n=e["row"]["n"], tm=e["row"]["tm"],
                     elig=e["row"]["elig"], base=e["base"]) for e in rookies[:picks]]
    return start, template, [n for _, n in unplaced]


def _roster_paths():
    return sorted(f for f in os.listdir(ROSTER_DIR)
                  if f.startswith("roster-") and f.endswith("-%s.json" % SEASON_TAG))


def pick_ledger():
    """({(season, round, original team path): holder path}, fetch stamp)"""
    try:
        d = _load(LEDGER)
    except OSError:
        raise OSError("no %s -- `./run fetch_data.py picks` writes it" % LEDGER)
    path = lambda tid: "roster-%s-%s.json" % (tid, SEASON_TAG)
    return ({(p["season"], p["round"], path(p["owner"])): path(p["holder"]) for p in d["picks"]},
            d["fetched"])


# ---------------------------------------------------------------- summary

def summary(runs, teams1, title1):
    owners = players.owner_names()
    paths = [t.path for t in teams1]
    n = len(runs)
    out = {"paths": PATHS, "seed": SEED, "years": [_label(t) for t in range(YEARS)],
           "drafts": ["'%02d" % ((LIVE_SEASON + 1 + s) % 100) for s in range(YEARS - 1)], "teams": {}}
    ranks = []
    for pfs, _, _ in runs:
        ranks.append([{p: k + 1 for k, p in enumerate(sorted(paths, key=lambda q: -pf[q]))} for pf in pfs])
    for p in paths:
        flows = [[f[p] for f in fl] for _, _, fl in runs]
        out["teams"][owners.get(p.split("-")[1], p)] = {
            "pf": [statistics.mean(r[0][y][p] for r in runs) for y in range(YEARS)],
            "rank": [statistics.mean(rk[y][p] for rk in ranks) for y in range(YEARS)],
            "title": [title1[p].title] + [statistics.mean(r[1][y][p] for r in runs)
                                          for y in range(YEARS - 1)],
            "picks": [[sum(1 for rnd, _ in flows[0][s]["picks"] if rnd == k)
                       for k in range(1, future.ROUNDS + 1)] for s in range(YEARS - 1)],
            "slot1": [_mean([slot for f in flows for rnd, slot in f[s]["picks"] if rnd == 1])
                      for s in range(YEARS - 1)],
            **{k: [sum(f[s][k] for f in flows) / n for s in range(YEARS - 1)]
               for k in ("rookies", "exits", "cuts")}}
    return out


def _mean(xs):
    return statistics.mean(xs) if xs else None


# ---------------------------------------------------------------- print

def _order(out):
    return sorted(out["teams"], key=lambda o: -out["teams"][o]["pf"][0])


def _preamble(fetched, flat):
    p = prog.params()
    print("FUTURE  %d paths, seed %d; progression params fit %s; pick ledger fetched %s"
          % (PATHS, SEED, p["fit"]["date"], fetched))
    print("Uncalibrated read. Season 1 is `title` (projections as-is); from season 2 every player")
    print("  follows his own progression path (FP/G, GP, exit), `sim.py progression`'s model.")
    print("Each offseason: exits leave; the draft (4 rounds, one order: top 4 by record pick")
    print("  12-9, the rest worst first, worst 4 draw 1.01 at 50/25/15/10) slots a pick by its")
    print("  ORIGINAL team's sampled finish and hands the rookie to its holder; '30+ picks own.")
    print("  A rookie is a fresh path off the 2026 class's player at that ordinal (rostered")
    print("  draftees by board BASE). Then cuts to 38 by BASE + 300 x formula Delta w on the")
    print("  latest season (Score without its sim terms; BASE frozen at today's boards), and")
    print("  pads with the year-1 FA filler.")
    print("Known biases: no trades or FA pickups; BASE never ages; every class = the 2026 class")
    print("  (strong top); role vets 29+ run high and top-5 picks over-project (progression")
    print("  limits); schedule = 2026-27 every season. Held flat (no birthday): %s."
          % (", ".join(flat) or "none"))
    print("PF = mean regular-season PF (k); rk = mean PF rank; P = P(title) %, sums to 100 per season.")


def _main_table(out):
    print("\n  %-8s" % "team" + "".join("  %-16s" % y for y in out["years"]))
    print("  %-8s" % "" + "".join("  %-16s" % "PF    rk    P" for _ in out["years"]))
    for o in _order(out):
        t = out["teams"][o]
        print("  %-8s" % o + "".join("  %4.1f %4.1f %5.1f" % (t["pf"][y] / 1000, t["rank"][y], 100 * t["title"][y])
                                     for y in range(YEARS)))


def _picks_table(out):
    print("\nPicks held R1.R2.R3.R4 @ mean 1st slot, then per offseason the mean rookies kept /")
    print("  exits / cuts (the draft after season N feeds season N+1).")
    print("  %-8s" % "team" + "".join("  %-17s" % d for d in out["drafts"]))
    for o in _order(out):
        t = out["teams"][o]
        cells = []
        for s in range(YEARS - 1):
            slot = "@%4.1f" % t["slot1"][s] if t["slot1"][s] is not None else "     "
            cells.append("%s %s" % (".".join(str(c) for c in t["picks"][s]), slot))
        print("  %-8s" % o + "".join("  %-17s" % c for c in cells))
        print("  %-8s" % "" + "".join("  %-17s" % ("%.1f / %.1f / %.1f" % (t["rookies"][s], t["exits"][s], t["cuts"][s]))
                                      for s in range(YEARS - 1)))


def _delta(out):
    try:
        with open(LAST) as f:
            last = json.load(f)
    except (OSError, ValueError):
        return
    if (last.get("paths"), last.get("seed"), last.get("years")) != (out["paths"], out["seed"], out["years"]):
        print("\nΔ vs last run: skipped, the last run (%s) used other paths/seed/seasons" % last.get("saved"))
        return
    moved = {o: t for o, t in out["teams"].items()
             if o in last["teams"] and any(abs(a - b) > 1e-9 for k in ("pf", "title")
                                           for a, b in zip(t[k], last["teams"][o][k]))}
    if not moved:
        print("\nΔ vs last run (%s): same as the last run" % last["saved"])
        return
    print("\nΔ vs last run (%s): PF (k) and P(title) points, teams that moved" % last["saved"])
    print("  %-8s" % "team" + "".join("  %-12s" % y for y in out["years"]))
    for o in _order(out):
        if o in moved:
            t, b = out["teams"][o], last["teams"][o]
            print("  %-8s" % o + "".join("  %+5.2f %+5.1f" % ((t["pf"][y] - b["pf"][y]) / 1000,
                                                             100 * (t["title"][y] - b["title"][y]))
                                         for y in range(YEARS)))


def _save(out):
    with open(LAST, "w") as f:
        json.dump(dict(out, saved=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")), f)
