import collections, math, statistics
from .. import engine
from ..data import (
    DELTA_W_MATCHUPS, MARGINS, NIGHTS, REAL_WK_MEAN, REAL_WK_SD,
    SCORED_ORDINALS, SCORES, SCORING_NIGHTS, US, WEEK_OF, WEEKS)
from ..roster import our_roster
from ..schedule import games_on
from ..wins import (
    MARGIN_MEAN, MARGIN_SD, PF_PER_WIN, margin_pwin, pf_per_win, pf_per_win_band,
    pf_wins)


def report_calibration():
    sides = sum(len(t) for _, t in NIGHTS)
    print("NBA calendar: %d nights, %d games, mean %.2f/night"
          % (len(NIGHTS), sides // 2, sides / 2 / len(NIGHTS)))
    g = collections.Counter()
    for i in SCORING_NIGHTS:
        g[WEEK_OF[i]] += games_on(NIGHTS[i][1])
    gv = sorted(g.values())
    print("fantasy season: %d scored periods over %d of those nights (%d games)."
          % (WEEKS, len(SCORING_NIGHTS), sum(gv)))
    print("  games per period %d-%d, mean %.1f, CV %.1f%%  <- NOT flat"
          % (gv[0], gv[-1], statistics.mean(gv),
             100 * statistics.stdev(gv) / statistics.mean(gv)))
    print("  %d NBA nights fall after the last scored period and are worth 0."
          % (len(NIGHTS) - len(SCORING_NIGHTS)))

    raw = our_roster(projected=False)
    a = engine.run(raw)
    print("\nCALIBRATION  '25-26 roster at '25-26 rates, standings basis")
    print("  simulated season PF : %8.0f" % a["pf"])
    print("  real standings PF   : %8.0f  (%d scored periods)"
          % (REAL_WK_MEAN * WEEKS, WEEKS))
    print("  ratio               : %8.3f" % (a["pf"] / (REAL_WK_MEAN * WEEKS)))
    print("  weekly mean / sd    : %.0f / %.0f   real %.0f / %.0f"
          % (a["wk_mean"], a["wk_sd"], REAL_WK_MEAN, REAL_WK_SD))
    print("  weekly CV           : %.1f%%          real %.1f%%"
          % (100 * a["cv"], 100 * REAL_WK_SD / REAL_WK_MEAN))
    print("  sim/real CV - 1     : %+.0f%%"
          % (100 * (a["cv"] / (REAL_WK_SD / REAL_WK_MEAN) - 1)))
    b = engine.run(raw, bursty=True)
    print("  bursty absences     : %+.2f%% of PF (EV only)"
          % (100 * (b["pf"] / a["pf"] - 1)))

    print("\nPF -> WINS")
    print("  margins over %d scored periods (n=%d): mean %+.0f, sd %.0f, "
          "P(win) %.3f"
          % (WEEKS, len(MARGINS), MARGIN_MEAN, MARGIN_SD, margin_pwin()))
    # scored periods only, matching MARGIN_SD -- pooling over every period
    # would compare two different seasons
    scored = set(SCORED_ORDINALS)
    ind = math.sqrt(REAL_WK_SD ** 2 + statistics.stdev(
        [v for t, s in SCORES.items() if t != US
         for p, v in s.items() if p in scored]) ** 2)
    print("  independence instead: sd %.0f (%.2fx), correlation rho = %.2f"
          % (ind, ind / MARGIN_SD, 1 - MARGIN_SD ** 2 / ind ** 2))
    print("  1 win = %.0f PF, independent %.0f"
          % (PF_PER_WIN, pf_per_win(MARGIN_MEAN, ind)))
    blo, bhi = pf_per_win_band()
    print("  band, bootstrap clustered on period: [%.0f, %.0f] = +-%.0f%%"
          % (blo, bhi, 100 * max(bhi - PF_PER_WIN, PF_PER_WIN - blo) / PF_PER_WIN))
    # through `pf_wins`, not `PF_PER_WIN` directly -- the constant is quoted
    # per season PF over DELTA_W_MATCHUPS, so dividing raw PF by it would be
    # ~5% off that matchup basis
    print("  %d matchups off a %d-period PF:" % (DELTA_W_MATCHUPS, WEEKS))
    shifts = (250, 500, 1000, 2000, 3000)
    print("  %6s %s" % ("+PF", "  ".join("%6d" % d for d in shifts)))
    print("  %6s %s" % ("curve", "  ".join(
        "%+6.2f" % (DELTA_W_MATCHUPS * (margin_pwin(d / WEEKS) - margin_pwin()))
        for d in shifts)))
    print("  %6s %s" % ("wins()", "  ".join("%+6.2f" % pf_wins(d)
                                            for d in shifts)))
