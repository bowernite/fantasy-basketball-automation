"""The league's raw facts: the NBA calendar, the scoring periods that count
toward the standings, and our real weekly scores and margins."""
import collections, json, os, statistics
from fetch_data import SEASON, SEASON_TAG


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(HERE, "data")
ROSTER_DIR = os.path.join(HERE, "rosters")


SEASON_STR = str(SEASON)          # the pool keys seasons as strings


FF2ESPN = {"GSW": "GS", "NOP": "NO", "WAS": "WSH", "UTA": "UTAH",
           "NYK": "NY", "SAS": "SA", "BRK": "BKN"}  # Fleaflicker -> ESPN abbrev


def _path(name):
    """Bare `roster-*` -> rosters/; other bare names -> data/; abs as-is"""
    if os.path.isabs(name):
        return name
    if os.path.dirname(name):
        return os.path.join(HERE, name)
    folder = ROSTER_DIR if name.startswith("roster-") else DATA_DIR
    return os.path.join(folder, name)


def roster_path(name):
    """`--roster` resolve: bare name in rosters/, abs as-is, else off HERE"""
    if os.path.isabs(name):
        return name
    if os.path.dirname(name):
        return os.path.join(HERE, name)
    return os.path.join(ROSTER_DIR, name)


def _load(name):
    with open(_path(name)) as f:
        return json.load(f)


NIGHTS = [(d, set(tms)) for d, tms in sorted(_load(
    "nba-schedule-%s.json" % SEASON_TAG)["daymap"].items())]


PERIODS = _load("league-%s.json" % SEASON_TAG)["periods"]  # eligibleSchedulePeriods


def _scores(periods):
    out = collections.defaultdict(dict)
    for p in periods:
        for away, away_pf, home, home_pf in p["games"]:
            out[away][p["ordinal"]] = away_pf
            out[home][p["ordinal"]] = home_pf
    return out


SCORES = _scores(PERIODS)


US = "Bathroom club"


# Periods that count toward the standings (excludes the 21-23 bracket window,
# which overlaps BRACKET below at period 20)
SCORED = [i for i, p in enumerate(PERIODS) if "regular" in p["kinds"]]


WEEKS = len(SCORED)


FULL_FIELD = max(len(p["games"]) for p in PERIODS)  # games in a full-field period


def _bracket():
    """Period indices of the bracket: the trailing run of short-field periods"""
    out = []
    for i in reversed(range(len(PERIODS))):
        if len(PERIODS[i]["games"]) == FULL_FIELD:
            break
        out.append(i)
    out.reverse()
    short = [i for i, p in enumerate(PERIODS) if len(p["games"]) < FULL_FIELD]
    assert out == short, "short-field periods are not one trailing run"
    assert out, "no bracket in league-%s.json" % SEASON_TAG
    flagged = {i for i, p in enumerate(PERIODS) if "playoff" in p["kinds"]}
    assert flagged <= set(out), "playoff-flagged periods fall outside the bracket window"
    return out


BRACKET = _bracket()


REGULAR = [i for i in range(len(PERIODS)) if i not in set(BRACKET)]


def period_nights(i):
    return tuple(n for n, (d, _) in enumerate(NIGHTS)
                 if PERIODS[i]["start"] <= d <= PERIODS[i]["end"])


BRACKET_NIGHTS = [period_nights(i) for i in BRACKET]


def _week_of(date):
    for w, i in enumerate(SCORED):
        if PERIODS[i]["start"] <= date <= PERIODS[i]["end"]:
            return w
    return None


WEEK_OF = [_week_of(d) for d, _ in NIGHTS]


SCORING_NIGHTS = [i for i, w in enumerate(WEEK_OF) if w is not None]


Calendar = collections.namedtuple("Calendar", "nights week_of weeks")


def _calendar(buckets):
    where = [None] * len(NIGHTS)
    for w, nights in enumerate(buckets):
        for n in nights:
            where[n] = w
    return Calendar([n for g in buckets for n in g], where, len(buckets))


SCORED_CAL = Calendar(SCORING_NIGHTS, WEEK_OF, WEEKS)


# Basis for every `Delta w` figure: scored periods minus bracket R1, which
# standings PF already counts (avoids double-counting that week)
DELTA_W_SCORED = [i for i in SCORED if i not in BRACKET[:1]]
DELTA_W_MATCHUPS = len(DELTA_W_SCORED)
DELTA_W_CAL = _calendar([period_nights(i) for i in DELTA_W_SCORED])


BRACKET_CAL = _calendar(BRACKET_NIGHTS)


SCORED_ORDINALS = [PERIODS[i]["ordinal"] for i in SCORED]


OUR_ORDINALS = [p for p in SCORED_ORDINALS if p in SCORES[US]]


OURS = [SCORES[US][p] for p in OUR_ORDINALS]


# Our score minus each other team's in the SAME period, grouped by period so a
# bootstrap can resample the period rather than pooled margins independently
MARGINS_BY_WEEK = [[SCORES[US][p] - s[p] for t, s in SCORES.items()
                    if t != US and p in s]
                   for p in OUR_ORDINALS]


MARGINS = [m for wk in MARGINS_BY_WEEK for m in wk]


REAL_WK_MEAN, REAL_WK_SD = statistics.mean(OURS), statistics.stdev(OURS)


REAL_MATCHUPS = len(OURS)
