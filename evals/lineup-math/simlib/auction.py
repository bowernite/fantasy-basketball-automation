"""What steering the September auction on the NBA calendar buys."""
from .roster import AUCTION_NAMES
from .schedule import NBA_TEAMS, team_light_nights


def coverage_picks(n, teams=None, best=True):
    """`n` NBA teams for `n` auction bodies, chosen greedily on `coverage`.

    ONE rule for the ladder and the headline, which is the only way "the best 7"
    is a single number: greedy is prefix-consistent, so rung k of the saturation
    ladder IS the best-k and rung n IS the best-n. Two rules would let the ladder
    total more at n picks than the best-n it ends at.

    Chosen on COVERAGE, not on measured PF: coverage is the quantity
    `Eval Definitions §Where our format pulls off consensus` 5 tells an eval to
    steer on, so selecting on it and MEASURING wins is the test of that rule
    rather than an assumption of it. Repeats are allowed -- a second body on an
    already-covered team is exactly the pick the rule should be caught making
    once coverage saturates.

    Ties break on the team's own light-night count and then alphabetically
    (candidates are sorted; max/min keep the first), so the answer does not depend
    on the order the caller happened to offer teams in.
    """
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


# `league-info`: 3 rookie picks + a 7-man FA auction fill Sept '26, and only the
# seven are a schedule we choose -- a rookie lands where he was drafted.
AUCTION_N = 7


def auction_slots(roster):
    """Indices of the bodies a September auction fills -- `pad`'s FA grades.

    By NAME, off `pad`'s own output (`AUCTION_NAMES`), so a roster already at 38
    has none rather than steering somebody's real player onto a schedule he does
    not play. Positional, not a count from the end: `pad` appends the three rookie
    slots FIRST and then keeps going past 38 for a short counterparty file.
    """
    return [i for i, p in enumerate(roster) if p["n"] in AUCTION_NAMES]


def steer(roster, tms):
    """`roster` with its auction bodies moved onto `tms`, in order.

    Grade, GP, eligibility and ROSTER ORDER are untouched -- order drives the
    per-season rng draw order, so rebuilding the list would turn a
    common-random-numbers comparison between two schedule choices into an
    independent one (see `swap`).
    """
    slots = auction_slots(roster)
    if len(tms) != len(slots):
        # Counted off the roster in hand, never assumed to be AUCTION_N: `pad`
        # invents an FA slot only where a roster is short of 38, so a full one
        # has none to steer and a 35-body file has three. Recycling or truncating
        # a seven-team list answers a different question and still prints a win.
        raise ValueError("%d schedules for %d auction bodies: `pad` invents an FA"
                         " slot only where a roster is short of 38, so name one "
                         "team per slot THIS roster has" % (len(tms), len(slots)))
    out = [dict(p) for p in roster]
    for i, tm in zip(slots, tms):
        out[i]["tm"] = tm
    return out
