"""Our league's scoring, applied to a raw stat line.

`league-info` §Scoring owns the rules; this is the executable copy. `SKILL.md`
§What the scoring does owns why there are two entry points.
"""
import math

DD_CATS = ("Pts", "Reb", "Ast", "Stl", "Blk")


def _linear_points(line):
    """Every scoring term but the DD/TD bonus -- the ones an average passes through.

    `Reb` is the total, so `OReb` is the *additional* point an offensive board
    earns -- `FetchLeagueRules` carries the two as separate +1 rules, not one +2."""
    return (line.get("Pts", 0.0)
            + line.get("Reb", 0.0)
            + line.get("OReb", 0.0)
            + line.get("3PM", 0.0)
            + 1.5 * line.get("Ast", 0.0)
            + 3.0 * line.get("Stl", 0.0)
            + 2.0 * line.get("Blk", 0.0)
            - 1.0 * line.get("TO", 0.0)
            - 0.25 * (line.get("FGA", 0.0) - line.get("FGM", 0.0))
            - 0.25 * (line.get("3PA", 0.0) - line.get("3PM", 0.0)))


def _threshold_bonus(line):
    """The DD/TD bonus ONE game's line earns. Cumulative, not exclusive: a
    triple-double pays the +2 AND the +5."""
    reached = sum(1 for c in DD_CATS if line.get(c, 0.0) >= 10)
    return (2 if reached >= 2 else 0) + (5 if reached >= 3 else 0)


def fantasy_points(line):
    """Fantasy points for ONE game's raw stat line."""
    return _linear_points(line) + _threshold_bonus(line)


def _p_reaches_10(mean):
    if mean <= 0:
        return 0.0
    term, below = math.exp(-mean), 0.0
    for k in range(10):
        below += term
        term *= mean / (k + 1)
    return max(0.0, 1.0 - below)


def expected_bonus(line):
    """Expected DD/TD points per game, from a season-average line.

    Poisson deliberately, not negative binomial: a projection publishes a mean
    and no variance, and fitting the observed variance measures no better
    (mean |err| 0.085 against 0.088, and a worse tail)."""
    reach = [_p_reaches_10(line.get(c, 0.0)) for c in DD_CATS]
    # Poisson-binomial over the five categories: dist[k] = P(exactly k of them).
    dist = [1.0]
    for p in reach:
        nxt = [0.0] * (len(dist) + 1)
        for k, dk in enumerate(dist):
            nxt[k] += dk * (1 - p)
            nxt[k + 1] += dk * p
        dist = nxt
    return 2 * sum(dist[2:]) + 5 * sum(dist[3:])


def line_from_sleeper(stats):
    """A Sleeper/RotoWire projection row -> the stat line our scoring reads.

    The feed's own `dd`/`td` are unusable and deliberately go unread; that trap
    and the OReb one are `SKILL.md` §What the scoring does."""
    reb = stats.get("reb", 0.0)
    return {"Pts": stats.get("pts", 0.0),
            "Reb": reb,
            "OReb": max(0.0, reb - stats.get("dreb", 0.0)),
            "Ast": stats.get("ast", 0.0),
            "Stl": stats.get("stl", 0.0),
            "Blk": stats.get("blk", 0.0),
            "TO": stats.get("to", 0.0),
            "FGM": stats.get("fgm", 0.0),
            "FGA": stats.get("fga", 0.0),
            "3PM": stats.get("tpm", 0.0),
            "3PA": stats.get("tpa", 0.0)}


def rate(avg_line):
    """FPts/G from a season-average stat line -- what a projection scores to."""
    return _linear_points(avg_line) + expected_bonus(avg_line)
