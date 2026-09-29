"""Offline guard for Hashtag GP parse and join. No network."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import hashtag_gp
import sleeper

HTML = open(os.path.join(HERE, "fixtures", "hashtag-projections.html")).read()


def test_parse_takes_the_full_name_and_the_gp_column():
    parsed = hashtag_gp.parse(HTML)
    by_name = {r["name"]: r["gp"] for r in parsed["rows"]}
    assert by_name == {"Nikola Jokic": 72.0, "Victor Wembanyama": 66.0}
    assert parsed["season"] == "2026-27"
    assert parsed["duration"] == "0"
    assert "Rest of Season" in parsed["duration_label"]
    assert "STREAM" not in parsed["duration_label"]


def test_parse_refuses_a_short_term_board():
    html = HTML.replace(
        'value="0">2026-27 Rest of Season Projections',
        'value="777">2026-27 Short Term Projections (STREAM7)')
    html = html.replace('selected="selected" value="0"',
                        'selected="selected" value="777"')
    try:
        hashtag_gp.parse(html)
    except ValueError as e:
        assert "STREAM" in str(e) or "short term" in str(e).lower()
    else:
        assert False, "a STREAM duration must refuse, not silently become season GP"


def test_an_ascii_feed_name_matches_the_accented_pool_name():
    idx = hashtag_gp.index([{"name": "Nikola Jokic", "gp": 72}])
    assert hashtag_gp.lookup("Nikola Jokić", idx) == 72.0
    assert hashtag_gp.lookup("Nikola Jokic", idx) == 72.0
    assert sleeper.norm("Nikola Jokic") == sleeper.norm("Nikola Jokić")


def test_two_players_sharing_a_normalised_name_refuse_to_index():
    try:
        hashtag_gp.index([{"name": "Jaylin Williams", "gp": 60},
                          {"name": "Jaylin Williams", "gp": 40}])
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
            except Exception as e:
                fails += 1
                print("ERROR %s\n      %s: %s" % (name, type(e).__name__, e))
    sys.exit(1 if fails else 0)
