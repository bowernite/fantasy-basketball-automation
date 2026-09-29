"""PF -> wins. One conversion constant, measured off the real margin
distribution, and the band around it."""
import random, statistics
from .data import MARGINS, MARGINS_BY_WEEK, DELTA_W_MATCHUPS, REAL_MATCHUPS, WEEKS
from .stats import cdf, phi


MARGIN_MEAN, MARGIN_SD = statistics.mean(MARGINS), statistics.stdev(MARGINS)


def margin_pwin(shift=0.0):
    return cdf((MARGIN_MEAN + shift) / MARGIN_SD)


def pf_per_win(mu, sd):
    return WEEKS * sd / phi(mu / sd) / REAL_MATCHUPS


# Measured off the real (correlated) margin distribution, not by summing our sd
# and the opponent's independently, which overstates it ~1.67x. +-14% band from
# a period-clustered bootstrap: 597 [518, 679]
PF_PER_WIN = pf_per_win(MARGIN_MEAN, MARGIN_SD)


def pf_per_win_band(n=2000, seed=7, lo=0.025, hi=0.975):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        ms = []
        for _ in MARGINS_BY_WEEK:
            ms += rng.choice(MARGINS_BY_WEEK)
        out.append(pf_per_win(statistics.mean(ms), statistics.stdev(ms)))
    out.sort()
    return out[int(lo * n)], out[int(hi * n)]


# PF of weekly edge that buys one win in ONE matchup: PF_PER_WIN with the
# season/matchup count it was quoted against divided back out
PF_PER_WIN_WEEK = PF_PER_WIN * REAL_MATCHUPS / WEEKS


def pf_wins(dpf, periods=WEEKS, games=None):
    """`periods` is the basis this is converted over, not `games`"""
    games = DELTA_W_MATCHUPS if games is None else games
    return dpf / periods / PF_PER_WIN_WEEK * games


def wins(res, baseline, games=None):
    if len(res["wk"]) != len(baseline["wk"]):
        raise ValueError(
            "%d-period run against a %d-period baseline -- run both on one "
            "`cal`" % (len(res["wk"]), len(baseline["wk"])))
    return pf_wins(res["pf"] - baseline["pf"], len(res["wk"]), games)
