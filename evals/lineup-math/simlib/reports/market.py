import os, statistics
from fetch_data import SEASON_TAG
from .. import gp
from ..board import (
    BOARD_MIN_GP, board_rates, board_rows, newest_board, pool, pool_seasons,
    season_or_latest)
from ..data import SEASON_STR
from ..gp import (
    GP_BOOT, GP_FOLDS, GP_KNOT, GP_MIN_RATE, GP_MODELS, GP_SHUFFLES,
    PROJECT_GP_NOTE, SEASONS, gp_fit, gp_model, gp_rows)
from ..roster import our_roster
from ..stats import ols


def report_gp():
    """Is a per-player GP projection defensible AT ALL?

    GP is the dominant input here and the only one with no market price: the
    boards supply BASE, nothing supplies GP. So the question is not "how accurate
    can we get", it is "what is the smallest defensible input". Candidates are
    ranked out of sample and the winner is what `project_gp` does.
    """
    rows = gp_rows()
    allrows = gp_rows(min_rate=0.0)
    print("%d seasons of pool data (%s-%s); %d of %d players have a birthday."
          % (len(SEASONS), SEASONS[0], SEASONS[-1],
             sum(1 for v in pool().values() if v.get("born")), len(pool())))
    print("CENSORED, and it caps everything below: a player who misses a WHOLE")
    print("season is absent from the pool rather than a zero, so every figure here")
    print("is expected GP GIVEN he plays at all.")
    print("\n%d-fold CV grouped by player, errors averaged over %d fold shuffles,"
          % (GP_FOLDS, GP_SHUFFLES))
    print("then a %d-sample bootstrap CLUSTERED ON PLAYER for the interval. The"
          % GP_BOOT)
    print("interval is the point: gaps here are ~0.1-0.7 RMSE and the player")
    print("sampling error on them is ~0.15, so a gap whose interval straddles 0")
    print("is NOT a result. `P` = P(this model beats gp1).")

    def bake_off(b):
        """One bootstrap's model table. Printed by one function because the three
        blocks below are read against each other, and a column that means
        something different in one of them is a comparison that has already gone
        wrong by the time anyone notices."""
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
    print("  Even where all five seasons EXIST the interval straddles 0. More")
    print("  history is not measurably worse than one season, and it is certainly")
    print("  not better -- so one season, on Occam, not on a measured loss.")

    print("\nWHY THE RATE TERM IS KNOTTED at %.0f. Mean next-season GP by last"
          % GP_KNOT)
    print("season's rate is CONCAVE and turns DOWN, so a linear term keeps paying")
    print("for rate the pool says buys no games. Bias = predicted - actual, both")
    print("models fitted IN SAMPLE on the whole pool: the SHAPE across rate bands")
    print("is the claim here, and the out-of-sample verdict is the bootstrap under")
    print("it. In sample is the harder test for the point being made -- a linear")
    print("term that still runs high on its own fitting rows runs higher off them.")
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
    print("  The linear term runs +7 GP high on the rate>=45 rows -- exactly the")
    print("  players every headline table on this page is built on.")
    k = gp.gp_bootstrap(allrows, models=("gp1+knot",), ref="gp1+rate")["gp1+knot"]
    print("  knot vs the UNKNOTTED rate term, same clustered bootstrap:")
    print("    %+.3f RMSE [%+.3f, %+.3f], P(knot better) %.3f -- this is the"
          % (k["delta"], k["lo"], k["hi"], k["p"]))
    print("    comparison the adoption rests on, so it is printed rather than")
    print("    inferred by subtracting two gaps that share a reference.")

    a, b, c = gp_model()
    print("\nADOPTED -- %s" % PROJECT_GP_NOTE)
    print("  GP = %.1f + %.3f x last GP + %.3f x min(last FPts/G, %.0f)"
          % (a, b, c, GP_KNOT))
    print("  The rate term separates a bench body from a starter -- expected GP")
    print("  runs ~40 at rate <10 against ~63 at rate 30-40 -- and the knot stops")
    print("  it running on past where the pool stops paying.")
    print("  %-24s %7s %6s %6s %7s"
          % ("player", "pool gp", "rate", "proj", "delta"))
    print("  'pool gp' is the season the projection actually READ -- not always the")
    print("  roster file's, which rounds some seasons a game differently. 'proj' is")
    print("  taken straight from our_roster(), so this table cannot drift from the")
    print("  GP the scenarios are actually run on.")
    for q in sorted(our_roster(), key=lambda r: r["gp"]):
        s = pool_seasons(q["n"])
        pgp = season_or_latest(s, SEASON_STR)[1] if s else q["gp"]
        print("  %-24s %7d %6.1f %6d %+7d"
              % (q["n"], pgp, q["avg"], q["gp"], q["gp"] - pgp))
    print("  Weakest where the most recent season is a FRAGMENT: it regresses hard")
    print("  but still reads that season as the only evidence, because measured,")
    print("  that is all it is. Read the fragment rows off the table above.")


def report_market():
    """Board rank <-> FPts/G, and how much of a GP season carries forward.

    Answers the question every break-even above raises and none of them can:
    is the incoming rate a break-even demands actually BUYABLE, and at what rank?
    """
    pairs = board_rates()
    # WHICH snapshot, printed: the month moves and the old file stays put, so a
    # table that does not name its board cannot be checked against one.
    print("board: %s" % os.path.basename(newest_board()))
    print("board rank -> %s FPts/G, %d of the board's %d ranked players."
          % (SEASON_TAG, len(pairs), len(board_rows())))
    print("This is the bridge from what a trade COSTS (rank) to what it PAYS")
    print("(rate). Everything else here assumes it; nothing else measures it.")
    # The drop is not noise at the bottom: a whole season missed is exactly how a
    # rank-7 name leaves, so the table reads shallower than the board is.
    print("The other %d carry no %s season of >=%d games in the pool -- a missed"
          % (len(board_rows()) - len(pairs), SEASON_TAG, BOARD_MIN_GP))
    print("year, or a name the two sources spell differently. So every rate here")
    print("is CONDITIONAL on having played, and the players it drops are not")
    print("drawn evenly from the ranks.")
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
        # max(ok) is the DEEPEST board rank that has ever supplied the rate --
        # how far down you might have to look, which is the bound that binds.
        print("    %2d FPts/G: %3d players clear it; %s"
              % (want, len(ok),
                 "deepest rank %d (best %d)" % (max(ok), min(ok))
                 if ok else "NOBODY"))
    print("  Read a 4-for-1 break-even against this: if it demands a rate only a")
    print("  handful of players reach, the deal is not purchasable at a fair price")
    print("  regardless of what the win table says.")

    print("\nGP PERSISTENCE. next-season GP = a + b x this-season GP, over every")
    print("consecutive pair in the pool -- the one-season baseline the richer")
    print("models are ranked against in `sim.py gp`.")
    print("  %12s %7s %7s %7s %9s" % ("population", "n", "a", "b", "converges"))
    for thr in (0, 10, 20, 25, 30):
        a, b, n = gp_fit(thr)
        print("  %11s+ %7d %7.1f %7.3f %9.1f"
              % ("rate %d" % thr, n, a, b, a / (1 - b)))
    print("  Among rotation-quality players only ~17-28% of a GP deviation")
    print("  carries forward, so everyone converges to ~59-62 GP whatever he just")
    print("  did. That is the strongest possible form of 'regress GP hard'.")
