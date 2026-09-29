"""The NBA calendar: who plays when, which nights are light, and what a set of
teams covers. Knows nothing about our roster or about scoring."""
import functools
from fetch_data import SEASON_TAG
from .data import (
    BRACKET_NIGHTS, FF2ESPN, NIGHTS, SCORING_NIGHTS, period_nights)


# The schedule every synthetic body is priced on. Change in ONE place, not per
# caller: which NBA team a body sits on moves its added PF materially.
SIM_TM = "LAC"


# Spread across teams so a multi-body row doesn't stack bodies on one team's
# nights and cannibalise each other's slots.
SIM_TMS = (SIM_TM, "TOR", "MEM")


UNSIGNED = "FA"  # fetch_data's default for a missing proTeamAbbreviation


def unsigned(tm):
    return tm == UNSIGNED


@functools.lru_cache(maxsize=None)
def team_nights(tm):
    """Night indices `tm` plays; SIM_TM's if unsigned. Raises for any other
    unresolvable team string -- that's a failed join, not a missing schedule"""
    if unsigned(tm):
        return team_nights(SIM_TM)
    esp = FF2ESPN.get(tm, tm)
    idxs = [i for i, (_, tms) in enumerate(NIGHTS) if esp in tms]
    if not idxs:
        raise KeyError(
            "%r: no NBA team by that name in %s (as %r) -- check the "
            "spelling and FF2ESPN"
            % (tm, "nba-schedule-%s.json" % SEASON_TAG, esp))
    return tuple(idxs)


LIGHT_GAMES = 5  # a night this small is one where the 9-slot cap binds


def games_on(tms):
    return len(tms) // 2


def is_light(tms, games=LIGHT_GAMES):
    return games_on(tms) <= games


@functools.lru_cache(maxsize=None)
def light_nights(games=LIGHT_GAMES):
    return tuple(i for i in SCORING_NIGHTS if is_light(NIGHTS[i][1], games))


@functools.lru_cache(maxsize=None)
def team_light_nights(tm):
    return frozenset(team_nights(tm)) & set(light_nights())


@functools.lru_cache(maxsize=None)
def bracket_games(tm):
    """In round order"""
    nights = set(team_nights(tm))
    return tuple(sum(1 for n in wk if n in nights) for wk in BRACKET_NIGHTS)


def period_games(i):
    return sum(games_on(NIGHTS[n][1]) for n in period_nights(i))


NBA_TEAMS = tuple(sorted({t for _, tms in NIGHTS for t in tms}))


def coverage(tms):
    """Distinct light nights a set of NBA teams reaches at all -- a second
    body on an already-covered night adds nothing"""
    return len({i for t in tms for i in team_light_nights(t)})
