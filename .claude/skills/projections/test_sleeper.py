"""Offline guard for `sleeper.py`'s join. No network -- fixtures only.

The join is the dangerous half of this skill: a name that fails to match is
indistinguishable from a player with no projection, and both would silently
leave a stale rate in place (`eval-player` §Joining names to board rows).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import sleeper

ROWS = json.load(open(os.path.join(HERE, "fixtures", "sleeper-rows.json")))


def test_a_suffixed_league_name_matches_the_feeds_unsuffixed_one():
    # Fleaflicker carries "Michael Porter Jr."; the feed carries "Michael Porter"
    idx = sleeper.index(ROWS)
    assert sleeper.lookup("Michael Porter Jr.", idx) is not None


def test_an_ascii_spelling_finds_the_feeds_accented_row():
    """28 of the feed's 587 rows carry diacritics. A roster file or an eval that
    spells one of them in ASCII must land on the same man rather than reading as
    a player with no projection -- the two are indistinguishable downstream.
    """
    idx = sleeper.index(ROWS)
    assert sleeper.lookup("Nikola Jokic", idx) == sleeper.lookup("Nikola Jokić", idx)
    assert sleeper.lookup("Nikola Jokic", idx) is not None


def test_a_projection_is_scored_as_a_season_average_not_as_one_nights_line():
    """Every scoring term is linear under averaging except the DD/TD bonus,
    which is a per-game threshold: charged off the averages it pays a
    10.5-rebound center +2 every night and an 8.8-assist guard nothing at all.
    That is worth enough to reorder the column it feeds (`projections`
    §What the scoring does).
    """
    rated, _ = sleeper.apply([{"n": "Zach Edey"}, {"n": "Michael Porter"},
                              {"n": "Josh Giddey"}], sleeper.index(ROWS))
    edey, porter, giddey = [p["avg"] for p in rated]

    # Scored as one night's line these two read 34.65 / 34.62 -- Edey ahead.
    assert porter > edey, "%.2f !> %.2f -- Edey was paid a nightly +2" % (porter, edey)
    # The same charge the other way: 8.1 reb / 8.8 ast is a double-double often
    # enough to be worth 1.7 FPts/G, and a threshold read pays it nothing.
    assert giddey > 41.0, "%.2f -- Giddey's double-doubles went unpaid" % giddey


def test_an_unprojected_player_is_reported_and_priced_toward_a_fringe_body():
    roster = [{"n": "Josh Giddey", "avg": 42.2, "gp": 70},
              {"n": "Chaney Johnson", "avg": 19.1, "gp": 18},
              {"n": "Emanuel Sharp", "avg": 0.0, "gp": 0}]
    rated, missing = sleeper.apply(roster, sleeper.index(ROWS))
    giddey, johnson, sharp = [p["avg"] for p in rated]
    assert missing == ["Chaney Johnson", "Emanuel Sharp"]
    assert giddey != 42.2                   # re-rated off the projection
    assert sleeper.NO_PROJECTION_RATE < johnson < 19.1
    assert sharp == sleeper.NO_PROJECTION_RATE


def test_a_row_with_no_stat_line_never_becomes_a_projection():
    """The feed answers with a row for every player it has an ADP for, and only
    ~587 of them carry a stat line. One of the rest reaching the index hands a
    real player a near-zero rate that reads exactly like a projection -- worse
    than the missing one it replaced, which at least publishes `noproj`.
    """
    raw = [{"player": {"first_name": "Josh", "last_name": "Giddey"},
            "team": "CHI", "stats": {"pts": 17.24, "reb": 8.14, "ast": 8.81},
            "updated_at": 1785671433355},
           {"player": {"first_name": "Vince", "last_name": "Carter"},
            "team": None, "stats": {"adp_dynasty": 402.1},
            "updated_at": 1785671433817}]
    rows = sleeper.projected_rows(raw)
    assert [r["name"] for r in rows] == ["Josh Giddey"]
    assert sleeper.lookup("Vince Carter", sleeper.index(rows)) is None


def test_the_snapshot_records_when_the_feed_was_last_cut():
    """`Eval Template.md` makes every eval publish each source's update
    stamp and depth. A snapshot that does not carry its own stamp cannot be
    cited without re-fetching it, and the feed re-cuts a row at a time -- so the
    stamp is the newest row's, not whichever one happens to come back first.
    """
    raw = [{"player": {"first_name": "Josh", "last_name": "Giddey"},
            "team": "CHI", "stats": {"pts": 20.0}, "updated_at": 1785671433355},
           {"player": {"first_name": "Zach", "last_name": "Edey"},
            "team": "MEM", "stats": {"pts": 12.8}, "updated_at": 1785671433817}]
    snap = sleeper.snapshot(sleeper.projected_rows(raw))
    assert snap["updated"] == 1785671433817
    assert snap["depth"] == 2


def test_two_players_sharing_a_normalised_name_refuse_to_index():
    collided = ROWS + [dict(ROWS[0], team="XXX")]
    try:
        sleeper.index(collided)
    except ValueError as e:
        assert "collide" in str(e).lower()
    else:
        assert False, "a colliding name must refuse, not silently win"


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok   %s" % name)
            except AssertionError as e:
                fails += 1
                print("FAIL %s\n     %s" % (name, e))
    sys.exit(1 if fails else 0)
