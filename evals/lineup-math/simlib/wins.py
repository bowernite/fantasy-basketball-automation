"""PF -> wins. One conversion constant, measured off the real margin
distribution, and the band around it."""
import random, statistics
from .data import MARGINS, MARGINS_BY_WEEK, REAL_MATCHUPS, WEEKS
from .stats import cdf, phi


MARGIN_MEAN, MARGIN_SD = statistics.mean(MARGINS), statistics.stdev(MARGINS)


def margin_pwin(shift=0.0):
    """P(we win a matchup) if every weekly score moves by `shift`."""
    return cdf((MARGIN_MEAN + shift) / MARGIN_SD)


def pf_per_win(mu, sd):
    """Season PF per win, off a margin distribution of mean `mu` and sd `sd`.

    ONE expression, because three figures are read against each other -- the
    constant below, its bootstrap band, and `calibration`'s "what independence
    would have given you instead" -- and they compare only if the distribution
    handed in is the only thing that differs.
    """
    return WEEKS * sd / phi(mu / sd) / REAL_MATCHUPS


# 1 win per this many season PF. Measured off the real MARGIN distribution, NOT by
# adding our sd and the opponent's in quadrature: the two are correlated rho = 0.64
# through the shared NBA calendar, so independence overstates the margin sd 1.67x
# and gives 993. Treat as +-14% (period-clustered bootstrap: 597 [518, 679]);
# the corroborations in findings.md are on the SAME score matrix, not independent.
PF_PER_WIN = pf_per_win(MARGIN_MEAN, MARGIN_SD)


def pf_per_win_band(n=2000, seed=7, lo=0.025, hi=0.975):
    """(lo, hi) for PF_PER_WIN, bootstrapped CLUSTERED ON PERIOD.

    Printed, not asserted: `eval-team` prices every verdict through this constant
    and quotes the band, so the band has to be re-derivable here. The corroborating
    figures in findings.md are other estimators on the SAME score matrix, so they are
    not independent of it and do not widen it.
    """
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        ms = []
        for _ in MARGINS_BY_WEEK:
            ms += rng.choice(MARGINS_BY_WEEK)
        out.append(pf_per_win(statistics.mean(ms), statistics.stdev(ms)))
    out.sort()
    return out[int(lo * n)], out[int(hi * n)]


def wins(res, baseline, games=None):
    """Extra wins per `games` matchups vs a baseline `run`.

    Converts DELTA PF at our real operating point, not by running a normal CDF on
    the sim's own weekly mean: the sim's absolute level is a calibration artifact,
    and pwin() out in the tail compresses deltas non-uniformly, which distorts the
    ordering rather than just the scale.
    """
    games = REAL_MATCHUPS if games is None else games
    return (res["pf"] - baseline["pf"]) / PF_PER_WIN * (games / REAL_MATCHUPS)
