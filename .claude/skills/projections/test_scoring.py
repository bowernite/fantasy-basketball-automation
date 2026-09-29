"""Offline guard for `scoring.py`. No network.

Fixtures are real Fleaflicker game lines with the fantasy points Fleaflicker
itself scored (`games[].pointsActual`), so a passing run is proof against the
league's own arithmetic rather than against a restatement of the rules.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import scoring

LINES = json.load(open(os.path.join(HERE, "fixtures", "game-lines.json")))
SEASONS = json.load(open(os.path.join(HERE, "fixtures", "seasons.json")))
SLEEPER_ROWS = json.load(open(os.path.join(HERE, "fixtures", "sleeper-rows.json")))


def test_every_fixture_line_matches_fleaflicker():
    bad = []
    for r in LINES:
        got = scoring.fantasy_points(r["stats"])
        if abs(got - r["expected_fpts"]) > 1e-9:
            bad.append((r["player"], r["expected_fpts"], got))
    assert not bad, "%d/%d rows disagree: %s" % (len(bad), len(LINES), bad[:5])


def test_scoring_an_average_line_recovers_the_seasons_actual_rate():
    """A projection is an average line, and the DD/TD bonus is a per-game event
    that an average cannot carry. Scored right, the season's true FPts/G comes
    back to within a fraction of a point.
    """
    bad = []
    for r in SEASONS:
        off = scoring.rate(r["avg_line"]) - r["true_fpts_per_g"]
        if abs(off) > 0.4:
            bad.append((r["player"], round(off, 3)))
    assert not bad, "off by more than 0.4 FPts/G: %s" % bad


def test_a_sleeper_row_scores_with_offensive_rebounds_split_back_out():
    """Sleeper publishes total and defensive boards; our scoring pays the
    offensive ones double, so the split has to come back out of the pair.
    """
    rows = {r["name"]: r for r in SLEEPER_ROWS}
    adams = scoring.line_from_sleeper(rows["Steven Adams"]["stats"])
    assert round(adams["OReb"], 2) == 2.61

    # Collapsing the split back into the total costs Edey his 3.9 offensive
    # boards a SECOND time -- the extra point on top is what pays them double
    edey = scoring.line_from_sleeper(rows["Zach Edey"]["stats"])
    collapsed = dict(edey, OReb=0.0)
    assert round(scoring.rate(edey) - scoring.rate(collapsed), 2) == 3.90


def test_the_double_double_bonus_comes_off_the_line_not_off_the_feeds_own_counts():
    """The feed publishes `dd`/`td` on some rows and omits them on others -- 45
    of the top 150 scorers carry none, and missing is indistinguishable from
    zero. Edey is one of them, and a 12.8/10.5 line doubles up most nights, so
    reading the feed there would pay him nothing for the biggest bonus on his
    row (`projections` §What the scoring does).
    """
    rows = {r["name"]: r for r in SLEEPER_ROWS}

    edey = rows["Zach Edey"]["stats"]
    assert "dd" not in edey and "td" not in edey, "fixture no longer shows the trap"
    # Priced off the feed's silence this line reads 32.65 instead
    assert scoring.rate(scoring.line_from_sleeper(edey)) > 33.5

    # And the counts the feed does publish cannot move a row either way
    jokic = rows["Nikola Jokić"]["stats"]
    assert (jokic["dd"], jokic["td"]) == (0.8, 0.41)
    scored = scoring.rate(scoring.line_from_sleeper(jokic))
    for counts in ({"dd": 0.0, "td": 0.0}, {"dd": 1.0, "td": 1.0}):
        assert scoring.rate(scoring.line_from_sleeper(dict(jokic, **counts))) == scored


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
