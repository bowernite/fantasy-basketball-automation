"""What steering the September auction on the NBA calendar buys."""
from .roster import AUCTION_NAMES
from .schedule import NBA_TEAMS, team_light_nights


def coverage_picks(n, teams=None, best=True):
    """`n` NBA teams for `n` auction bodies, chosen greedily on `coverage`"""
    teams = sorted(NBA_TEAMS if teams is None else teams)
    got, picks = set(), []

    def gain(t):
        nights = team_light_nights(t)
        return len(nights - got), len(nights)

    for _ in range(n):
        tm = (max if best else min)(teams, key=gain)
        picks.append(tm)
        got |= team_light_nights(tm)
    return picks


AUCTION_N = 7  # 3 rookie picks + a 7-man FA auction fill Sept '26 (league-info)


def auction_slots(roster):
    """Indices of the bodies a September auction fills (`pad`'s FA grades)"""
    return [i for i, p in enumerate(roster) if p["n"] in AUCTION_NAMES]


def steer(roster, tms):
    """`roster` with its auction bodies moved onto `tms`, in order; roster
    order is otherwise untouched (it drives the per-season rng draws)"""
    slots = auction_slots(roster)
    if len(tms) != len(slots):
        raise ValueError("%d schedules for %d auction bodies"
                         % (len(tms), len(slots)))
    out = [dict(p) for p in roster]
    for i, tm in zip(slots, tms):
        out[i]["tm"] = tm
    return out
