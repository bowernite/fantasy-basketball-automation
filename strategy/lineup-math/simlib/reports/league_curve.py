"""Re-cut the 12-roster 38th-body curve that formula Δw interpolates."""
import os, statistics
from .. import engine
from ..data import DELTA_W_CAL, ROSTER_DIR
from ..league_curve import CURVE_GP, CURVE_PF60, CURVE_RATE
from ..roster import our_roster, pad, star

SEEDS = (101, 301, 501)
RATES = CURVE_RATE
GP_CHECK = 78
CHECK_RATES = (14, 26, 40)


def _mean_pf(roster):
    return statistics.mean(
        engine.run(roster, cal=DELTA_W_CAL, seed0=s)["pf"] for s in SEEDS)


def _fit_high(rates, values, floor=26):
    xs, ys = zip(*[(r, v) for r, v in zip(rates, values) if r >= floor])
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sl = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum(
        (x - mx) ** 2 for x in xs)
    return sl, mx - my / sl


def report_league_curve():
    files = sorted(f for f in os.listdir(ROSTER_DIR) if f.endswith(".json"))
    bases = {f: pad(our_roster(f), 37) for f in files}
    base_pf = {f: _mean_pf(r) for f, r in bases.items()}
    tot = {r: [] for r in RATES}
    print("38th-body PF, GP %d, mean of 12 rosters, seeds %s"
          % (CURVE_GP, ",".join(str(s) for s in SEEDS)))
    print("  rate " + " ".join("%6d" % r for r in RATES))
    for f in files:
        for rt in RATES:
            body = star(rt, int(CURVE_GP), ("SF", "PF"), "LAC", "ADD")
            tot[rt].append(_mean_pf(bases[f] + [body]) - base_pf[f])
    mean60 = [statistics.mean(tot[r]) for r in RATES]
    print("  PF   " + " ".join("%6.0f" % v for v in mean60))
    shipped = list(CURVE_PF60)
    print("  ship " + " ".join("%6.0f" % v for v in shipped))
    sl, intercept = _fit_high(RATES, mean60)
    print("  linear rate>=26: %.1f PF/rate-pt @ GP %d = %.3f PF/G ; "
          "x-intercept %.1f" % (sl, CURVE_GP, sl / CURVE_GP, intercept))
    drift = max(abs(a - b) for a, b in zip(mean60, shipped))
    print("  max |PF - shipped table|: %.1f" % drift)
    print("\nGP %d / GP %d" % (GP_CHECK, CURVE_GP))
    for rt in CHECK_RATES:
        v60 = statistics.mean(tot[rt])
        v78 = statistics.mean(
            _mean_pf(bases[f] + [star(rt, GP_CHECK, ("SF", "PF"), "LAC", "ADD")])
            - base_pf[f] for f in files)
        print("  rate %d: %.3f  (expect %.3f)"
              % (rt, v78 / v60 if v60 else 0, GP_CHECK / CURVE_GP))
