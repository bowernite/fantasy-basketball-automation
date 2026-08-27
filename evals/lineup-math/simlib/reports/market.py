import os, statistics
from fetch_data import SEASON_TAG
from .. import gp
from ..board import (
    BOARD_MIN_GP, board_rates, board_rows, newest_board, pool, pool_seasons,
    season_or_latest)
from ..data import SEASON_STR
from ..gp import (
    GP_BOOT, GP_FOLDS, GP_KNOT, GP_MIN_RATE, GP_MODELS, GP_SHUFFLES, SEASONS,
    gp_fit, gp_model, gp_rows)
from ..roster import our_roster
from ..stats import ols


def report_gp():
    rows = gp_rows()
    allrows = gp_rows(min_rate=0.0)
    print("%d seasons of pool data (%s-%s); %d of %d players have a birthday."
          % (len(SEASONS), SEASONS[0], SEASONS[-1],
             sum(1 for v in pool().values() if v.get("born")), len(pool())))
    print("expected GP GIVEN he plays at all: a whole missed season is absent "
          "from the pool.")
    print("\n%d-fold CV grouped by player, errors averaged over %d fold "
          "shuffles, then a\n%d-sample bootstrap clustered on player for the "
          "interval. `P` = P(model beats gp1)."
          % (GP_FOLDS, GP_SHUFFLES, GP_BOOT))

    def bake_off(b):
        # one function since the three blocks below are read against each
        # other -- a column meaning something different in one breaks the
        # comparison
        print("  %-10s %7s %9s %-18s %6s"
              % ("model", "RMSE", "vs gp1", "95% CI on that gap", "P"))
        for k, v in sorted(b.items(), key=lambda kv: kv[1]["rmse"]):
            print("  %-10s %7.2f %+9.2f  [%+.2f, %+.2f]%5s %6.3f"
                  % (k, v["rmse"], v["delta"], v["lo"], v["hi"], "", v["p"]))

    for label, rs in (("rate >= %.0f, the players we trade" % GP_MIN_RATE, rows),
                      ("the whole pool, bench included", allrows)):
        ys = [r["y"] for r in rs]
        print("\n%s -- %d rows, %d players, target GP mean %.1f sd %.1f"
              % (label, len(rs), len({r["name"] for r in rs}),
                 statistics.mean(ys), statistics.stdev(ys)))
        bake_off(gp.gp_bootstrap(rs))

    deeprows = gp_rows(min_hist=4)
    print("\nwhat the 4th and 5th season buy, on the %d rows that HAVE 4+ prior"
          % len(deeprows))
    print("seasons (RMSE comparable only within this block):")
    bake_off(gp.gp_bootstrap(deeprows, models=("mean", "age", "gp1", "gp5")))

    print("\nRATE TERM KNOTTED at %.0f. bias = predicted - actual, both models"
          % GP_KNOT)
    print("fitted IN SAMPLE on the whole pool:")
    fits = {m: ols(allrows, GP_MODELS[m], [r["y"] for r in allrows])
            for m in ("gp1+rate", "gp1+knot")}
    print("  %9s %6s %8s %10s %10s"
          % ("rate band", "n", "actual", "linear", "knotted"))
    for lo, hi in ((0, 10), (10, 20), (20, 30), (30, 40), (40, 45), (45, 999)):
        idx = [i for i, r in enumerate(allrows) if lo <= r["rate"] < hi]
        act = statistics.mean(allrows[i]["y"] for i in idx)
        cells = []
        for m in ("gp1+rate", "gp1+knot"):
            f, be = GP_MODELS[m], fits[m]
            pred = statistics.mean(
                be[0] + sum(x * z for x, z in zip(be[1:], f(allrows[i])))
                for i in idx)
            cells.append(pred - act)
        print("  %4d-%-4s %6d %8.1f %+10.1f %+10.1f"
              % (lo, "+" if hi > 900 else hi, len(idx), act, cells[0], cells[1]))
    k = gp.gp_bootstrap(allrows, models=("gp1+knot",), ref="gp1+rate")["gp1+knot"]
    print("  knot vs the UNKNOTTED rate term, same clustered bootstrap:")
    print("    %+.3f RMSE [%+.3f, %+.3f], P(knot better) %.3f"
          % (k["delta"], k["lo"], k["hi"], k["p"]))

    a, b, c = gp_model()
    print("\nADOPTED")
    print("  GP = %.1f + %.3f x last GP + %.3f x min(last FPts/G, %.0f)"
          % (a, b, c, GP_KNOT))
    print("  %-24s %7s %6s %6s %7s"
          % ("player", "pool gp", "rate", "proj", "delta"))
    for q in sorted(our_roster(), key=lambda r: r["gp"]):
        s = pool_seasons(q["n"])
        pgp = season_or_latest(s, SEASON_STR)[1] if s else q["gp"]
        print("  %-24s %7d %6.1f %6d %+7d"
              % (q["n"], pgp, q["avg"], q["gp"], q["gp"] - pgp))


def report_market():
    pairs = board_rates()
    print("board: %s" % os.path.basename(newest_board()))
    print("board rank -> %s FPts/G, %d of the board's %d ranked players."
          % (SEASON_TAG, len(pairs), len(board_rows())))
    print("unmatched %d: no %s season of >=%d games in the pool."
          % (len(board_rows()) - len(pairs), SEASON_TAG, BOARD_MIN_GP))
    print("  %10s %7s %9s %9s %9s" % ("rank band", "n", "median", "p25", "p75"))
    for lo, hi in ((1, 12), (13, 24), (25, 36), (37, 60), (61, 96),
                   (97, 150), (151, 250), (251, 456)):
        v = sorted(r for k, r in pairs if lo <= k <= hi)
        if not v:
            continue
        print("  %4d-%-5d %7d %9.1f %9.1f %9.1f"
              % (lo, hi, len(v), statistics.median(v),
                 v[len(v) // 4], v[3 * len(v) // 4]))
    print("\n  rate needed -> the best rank that has historically supplied it:")
    for want in (30, 40, 45, 50, 55, 60, 65):
        ok = [k for k, r in pairs if r >= want]
        # max(ok): deepest board rank that has ever supplied the rate
        print("    %2d FPts/G: %3d players clear it; %s"
              % (want, len(ok),
                 "deepest rank %d (best %d)" % (max(ok), min(ok))
                 if ok else "NOBODY"))

    print("\nGP PERSISTENCE. next-season GP = a + b x this-season GP, over every")
    print("consecutive pair in the pool.")
    print("  %12s %7s %7s %7s %9s" % ("population", "n", "a", "b", "converges"))
    for thr in (0, 10, 20, 25, 30):
        a, b, n = gp_fit(thr)
        print("  %11s+ %7d %7.1f %7.3f %9.1f"
              % ("rate %d" % thr, n, a, b, a / (1 - b)))
