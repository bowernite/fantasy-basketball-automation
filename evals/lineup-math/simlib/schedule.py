"""The NBA calendar: who plays when, which nights are light, and what a set of
teams covers. Knows nothing about our roster or about scoring."""
import functools
from fetch_data import SEASON_TAG
from .data import FF2ESPN, NIGHTS, SCORING_NIGHTS


# THE schedule every synthetic body is priced on. Which NBA team a body sits on
# moves its added PF by 218 across the 30 schedules (mean 1483, sd 56, OKC +1600
# to DET +1383) = ~4.2 rate points, so a study that mixes teams charges a
# schedule handicap and books it as body count. Change it in ONE place or not at all.
SIM_TM = "LAC"


# For a MULTI-body row, reusing SIM_TM three times would swap a schedule
# handicap for a stacking one: three bodies sharing one team's nights cannibalise
# each other's slots, worth ~120 PF over three. So spread them. Against the
# 30-team mean 1483: LAC -25, TOR -3, MEM +24, trio mean 1482 -- no net handicap
# either way.
SIM_TMS = (SIM_TM, "TOR", "MEM")


# What the roster feed writes for a player on no NBA team -- `fetch_data`'s
# default for a missing `proTeamAbbreviation`. A STATEMENT by the feed, unlike a
# team string the schedule happens not to carry (see `team_nights`).
UNSIGNED = "FA"


def unsigned(tm):
    """Is this the feed's "no NBA team" sentinel? Not "resolves to no schedule" --
    a team the schedule file does not carry is a JOIN FAILURE, which `team_nights`
    refuses outright."""
    return tm == UNSIGNED


@functools.lru_cache(maxsize=None)
def team_nights(tm):
    """Night indices `tm` plays; SIM_TM's if the feed says he is UNSIGNED.

    An unsigned body is a body with an UNKNOWN schedule, and SIM_TM is already
    what this study prices an unknown schedule on -- every synthetic body runs on
    it. Suiting him up for nothing instead costs him most of a body in `Δw`, and
    books a snapshot artifact as a finding about the player. `report_players` flags
    the row `fa` so the assumption travels with the number.

    Any OTHER string the schedule cannot resolve is refused. The feed spells teams
    SAS/NYK/UTA/GSW/NOP/WAS where the schedule says SA/NY/UTAH/GS/NO/WSH, so the
    join runs through FF2ESPN and one rename on either side breaks it -- and
    inheriting SIM_TM there is not a documented assumption, it is the DEEPEST
    light-night schedule of the 30 applied silently, with nothing printing an error.
    """
    if unsigned(tm):
        return team_nights(SIM_TM)
    esp = FF2ESPN.get(tm, tm)
    idxs = [i for i, (_, tms) in enumerate(NIGHTS) if esp in tms]
    if not idxs:
        raise KeyError(
            "%r: no NBA team by that name in %s (as %r). A body with no team is "
            "%r, which the feed writes itself; anything else is a failed join -- "
            "check the spelling and FF2ESPN."
            % (tm, "nba-schedule-%s.json" % SEASON_TAG, esp, UNSIGNED))
    return tuple(idxs)


# A night this small is one where the 9-slot cap binds and presence beats rate.
# `nights` measures what share of the season's unfilled slots they carry.
LIGHT_GAMES = 5


def games_on(tms):
    """NBA games on a night `tms` are in action on. A night carries BOTH sides of
    every game, so the count is half the teams. This is the per-night key `engine`
    groups its tables on and `is_light` thresholds, so the two cannot disagree;
    season totals halve their own sums (`calibration`, `schedules`)."""
    return len(tms) // 2


def is_light(tms, games=LIGHT_GAMES):
    """Is a night on which `tms` are in action a light one?"""
    return games_on(tms) <= games


@functools.lru_cache(maxsize=None)
def light_nights(games=LIGHT_GAMES):
    """Scored night indices carrying `games` NBA games or fewer.

    SCORING_NIGHTS, not the calendar: 34 NBA nights fall after the last scored
    period and are worth nothing, 6 of them light. Counting the whole calendar
    moves a team by up to 5 (NY 9 light nights -> 14, DEN 8 -> 13) and reshuffles
    the order a schedule choice is made on.
    """
    return tuple(i for i in SCORING_NIGHTS if is_light(NIGHTS[i][1], games))


@functools.lru_cache(maxsize=None)
def team_light_nights(tm):
    """`tm`'s light nights -- through `team_nights`, so an unsigned body inherits
    SIM_TM's light nights exactly as he inherits its schedule everywhere else."""
    return frozenset(team_nights(tm)) & set(light_nights())


NBA_TEAMS = tuple(sorted({t for _, tms in NIGHTS for t in tms}))


def coverage(tms):
    """Distinct light nights a set of NBA teams reaches AT ALL.

    THE payoff quantity (`Eval Definitions §Where our format pulls off consensus`
    5): a second body on a night already covered is chasing the slot the first
    one took, so summing per-team night counts prices a stack as though it were a
    spread. Seven bodies on the deepest light-night schedule SUM to 84 and COVER
    12, and 84 is the ceiling on that sum.
    """
    return len({i for t in tms for i in team_light_nights(t)})
