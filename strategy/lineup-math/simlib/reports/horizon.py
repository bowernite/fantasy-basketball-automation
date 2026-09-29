"""Naive multi-year PF ranks: pool age-bucket YoY rate deltas, GP re-projected."""
import glob, os
from fetch_data import SEASON_TAG
from .. import bracket, roster as roster_mod
from ..board import pool
from ..data import ROSTER_DIR, _load
from ..gp import age_at, project_gp

# Mean next-season FPts/G delta by age (pool, rotation players, rate>=20 GP>=30).
AGE_DELTA = ((20, 25, +0.65), (25, 30, -0.90), (30, 35, -3.43), (35, 50, -3.15))

LOTTERY_PRIOR = {
    5: "1.05–1.11", 6: "1.05–1.11", 7: "1.03–1.10", 8: "1.03–1.09",
    9: "1.02–1.09", 10: "1.02–1.09", 11: "1.01–1.08", 12: "1.01–1.07",
}


def _rate_delta(age):
    for lo, hi, d in AGE_DELTA:
        if lo <= age < hi:
            return d
    return 0.0


def _aged_roster(path, years):
    rows = roster_mod.our_roster(path)
    out = []
    for p in rows:
        q = dict(p)
        born = (pool().get(p["n"]) or {}).get("born")
        if born:
            age = age_at(born, str(2026 + years - 1))
            q["avg"] = max(6.0, q["avg"] + _rate_delta(age) * years)
            q["gp"] = round(project_gp(p["n"], gp=q["gp"], rate=q["avg"]))
        out.append(q)
    return roster_mod.pad(out, path=path)


def _sept_slot(rank):
    if rank <= 4:
        return "1.%02d" % (13 - rank)
    return LOTTERY_PRIOR[rank]


def _year_rows(years):
    teams = _load("teams-%s.json" % SEASON_TAG)
    paths = sorted(glob.glob(os.path.join(ROSTER_DIR, "roster-*-%s.json"
                                          % SEASON_TAG)))
    rows = []
    for path in paths:
        tid = os.path.basename(path).split("-")[1]
        t = bracket.measure(_aged_roster(path, years), os.path.basename(path))
        rows.append((tid, teams[tid], int(t.pf)))
    rows.sort(key=lambda x: -x[2])
    return [(i + 1, tid, name, pf, _sept_slot(i + 1))
            for i, (tid, name, pf) in enumerate(rows)]


def report_horizon(years=(0, 1, 2)):
    print("Naive horizon: today's projected rates + GP, then per player")
    print("  rate += age-bucket YoY mean x years (pool, rotation players);")
    print("  GP re-projected off the shifted rate. Same 28 bodies, no")
    print("  trades, no draft picks, no attrition. Not BASE, not Delta w.")
    print("Age buckets (FPts/G per year): 20-25 +0.65, 25-30 -0.90,")
    print("  30-35 -3.43, 35+ -3.15. Re-measure -> season PF rank.")
    labels = ("'26-27", "'27-28", "'28-29")
    for years, label in zip(years, labels):
        rows = _year_rows(years)
        print("\n%s  (years=%d)" % (label, years))
        print("  %4s  %-36s  %7s  slot" % ("rank", "team", "PF"))
        for rank, tid, name, pf, slot in rows:
            print("  %4d  %-36s  %7d  %s" % (rank, name, pf, slot))
