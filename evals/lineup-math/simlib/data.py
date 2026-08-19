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
# comparing it to standings PF overstates ours by 18%. Overlaps BRACKET below at
# period 20 (`league-info`).
SCORED = [i for i, p in enumerate(PERIODS) if "regular" in p["kinds"]]


WEEKS = len(SCORED)


# Games in a period every team plays: 12 teams, 6 games.
FULL_FIELD = max(len(p["games"]) for p in PERIODS)


def _bracket():
    """Period indices of the bracket: the trailing run of short-field periods.
    Never taken from `kinds` (`league-info` §Matchup periods)."""
    out = []
    for i in reversed(range(len(PERIODS))):
        if len(PERIODS[i]["games"]) == FULL_FIELD:
            break
        out.append(i)
    out.reverse()
    short = [i for i, p in enumerate(PERIODS) if len(p["games"]) < FULL_FIELD]
    assert out == short, (
        "short-field periods %s are not one trailing run: the bracket window "
        "cannot be read off the field size in %s"
        % ([PERIODS[i]["ordinal"] for i in short], "league-%s.json" % SEASON_TAG))
    assert out, ("no bracket in league-%s.json: every period is full-field"
                 % SEASON_TAG)
    flagged = {i for i, p in enumerate(PERIODS) if "playoff" in p["kinds"]}
    assert flagged <= set(out), (
        "periods %s are flagged playoff and fall outside the derived window %s"
        % (sorted(PERIODS[i]["ordinal"] for i in flagged - set(out)),
           [PERIODS[i]["ordinal"] for i in out]))
    return out


BRACKET = _bracket()


REGULAR = [i for i in range(len(PERIODS)) if i not in set(BRACKET)]


def period_nights(i):
    """Night indices inside PERIODS[i]'s date range."""
    return tuple(n for n, (d, _) in enumerate(NIGHTS)
                 if PERIODS[i]["start"] <= d <= PERIODS[i]["end"])


BRACKET_NIGHTS = [period_nights(i) for i in BRACKET]


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


# Which nights `season` scores and which bucket each falls in. `engine.run`
# takes one as `cal`: SCORED_CAL (the standings basis) by default, BRACKET_CAL
# for a bracket round.
Calendar = collections.namedtuple("Calendar", "nights week_of weeks")


def _calendar(buckets):
    """A Calendar over `buckets`, one group of night indices per bucket."""
    where = [None] * len(NIGHTS)
    for w, nights in enumerate(buckets):
        for n in nights:
            where[n] = w
    return Calendar([n for g in buckets for n in g], where, len(buckets))


SCORED_CAL = Calendar(SCORING_NIGHTS, WEEK_OF, WEEKS)


# ONE basis for every `Delta w` figure: scored periods minus bracket R1 (period
# 20 / W20). Standings PF still counts R1; pricing it again in wins would
# double-count the week `Bracket value.md` prices in `W20`-`W23`.
DELTA_W_SCORED = [i for i in SCORED if i not in BRACKET[:1]]
DELTA_W_MATCHUPS = len(DELTA_W_SCORED)
DELTA_W_CAL = _calendar([period_nights(i) for i in DELTA_W_SCORED])


BRACKET_CAL = _calendar(BRACKET_NIGHTS)


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
