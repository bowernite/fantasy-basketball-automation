"""The league's raw facts: the NBA calendar, the scoring periods that count
toward the standings, and our real weekly scores and margins.

The basis every PF figure in the study is quoted on. Loads files, computes
nothing about players."""
import collections, json, os, statistics
from fetch_data import SEASON, SEASON_TAG


# The data files sit beside `sim.py`, one level up from this package.
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SEASON_STR = str(SEASON)          # the pool keys seasons as strings


# Fleaflicker abbrev -> ESPN abbrev (schedule file uses ESPN's)
FF2ESPN = {"GSW": "GS", "NOP": "NO", "WAS": "WSH", "UTA": "UTAH",
           "NYK": "NY", "SAS": "SA", "BRK": "BKN"}


def _load(name):
    with open(os.path.join(HERE, name)) as f:
        return json.load(f)


NIGHTS = [(d, set(tms)) for d, tms in sorted(_load(
    "nba-schedule-%s.json" % SEASON_TAG)["daymap"].items())]


PERIODS = _load("league-%s.json" % SEASON_TAG)["periods"]  # eligibleSchedulePeriods


def _scores(periods):
    """team -> period ordinal -> PF, over every game in `periods`."""
    out = collections.defaultdict(dict)
    for p in periods:
        for away, away_pf, home, home_pf in p["games"]:
            out[away][p["ordinal"]] = away_pf
            out[home][p["ordinal"]] = home_pf
    return out


SCORES = _scores(PERIODS)


US = "Bathroom club"


# ONE basis for every PF figure in this study: the periods that count toward the
# standings (1-20 here). Periods 21-23 are the playoff/consolation bracket, and
# the standings' PF column excludes them -- calibrating on a 23-period total and
# comparing it to standings PF overstates ours by 18%.
SCORED = [i for i, p in enumerate(PERIODS) if "regular" in p["kinds"]]


WEEKS = len(SCORED)


def _week_of(date):
    """Index into SCORED for an ET date, or None if the date scores nothing.

    Do NOT bucket nights evenly. Real periods run 4-7 nights and 28-56 NBA
    games: the Cup knockout week has 28, the All-Star week 31, a full week 52-56.
    That spread is a first-order source of weekly variance and an even split
    deletes it. The fantasy season also ENDS before the NBA's -- 34 nights and
    22% of the NBA's games fall outside the scored periods entirely.
    """
    for w, i in enumerate(SCORED):
        if PERIODS[i]["start"] <= date <= PERIODS[i]["end"]:
            return w
    return None


WEEK_OF = [_week_of(d) for d, _ in NIGHTS]


SCORING_NIGHTS = [i for i, w in enumerate(WEEK_OF) if w is not None]


SCORED_ORDINALS = [PERIODS[i]["ordinal"] for i in SCORED]


# The scored periods we have a score of our own for. Written once because OURS and
# MARGINS_BY_WEEK have to be the same periods in the same order -- a margin cluster
# that does not line up with the score it was taken against is not a cluster.
OUR_ORDINALS = [p for p in SCORED_ORDINALS if p in SCORES[US]]


# Our operating point: real weekly scores on the scored-period basis.
OURS = [SCORES[US][p] for p in OUR_ORDINALS]


# Our score minus each other team's in the SAME period -- the distribution a
# matchup is actually decided on. Grouped by period as well as pooled: the margins
# in a period share OUR score for it, so they are one cluster, not one draw each.
# Any interval on them has to resample the period (see pf_per_win_band).
MARGINS_BY_WEEK = [[SCORES[US][p] - s[p] for t, s in SCORES.items()
                    if t != US and p in s]
                   for p in OUR_ORDINALS]


MARGINS = [m for wk in MARGINS_BY_WEEK for m in wk]


REAL_WK_MEAN, REAL_WK_SD = statistics.mean(OURS), statistics.stdev(OURS)


REAL_MATCHUPS = len(OURS)
