"""Offline guard for FanScout GP parse and season check. No network."""
import json
import os
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fanscout_gp

HTML = open(os.path.join(HERE, "fixtures", "fanscout-projections.html")).read()
ROOKIES = ["AJ Dybantsa", "Darryn Peterson", "Cameron Boozer"]


def fake_site(board, honors_players_param=True):
    """Stands in for fanscout.pro: serves the top 150 unless `?players=N` asks for more."""
    class Response:
        def __init__(self, body):
            self.body = body

        def read(self):
            return self.body.encode("utf-8")

    def urlopen(req, timeout=None):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(req.full_url).query)
        shown = 150
        if honors_players_param and "players" in query:
            shown = int(query["players"][0])
        rows = [{"gamesPlayed": 70, "playerName": name, "team": "SAS"}
                for name in board[:shown]]
        chunk = "7a:" + json.dumps(["$", "$L7b", None, {"data": rows}])
        return Response(
            "<html><head><title>NBA Player Projections 2026–27 | FanScout</title></head>"
            "<body><script>self.__next_f.push([1,%s])</script></body></html>"
            % json.dumps(chunk))

    return urlopen


def with_fake_site(urlopen, fn):
    real = fanscout_gp.urllib.request.urlopen
    fanscout_gp.urllib.request.urlopen = urlopen
    try:
        return fn()
    finally:
        fanscout_gp.urllib.request.urlopen = real


def test_pull_gets_the_whole_board_not_the_sites_default_top_150():
    board = ["Player %d" % i for i in range(478)] + ROOKIES

    parsed = with_fake_site(fake_site(board), fanscout_gp.pull)

    assert len(parsed["rows"]) == 481
    assert sorted(r["name"] for r in parsed["rookies"]) == sorted(ROOKIES)


def test_pull_refuses_a_board_cut_short_even_when_the_rookies_made_it():
    board = ROOKIES + ["Player %d" % i for i in range(478)]
    site = fake_site(board, honors_players_param=False)

    try:
        with_fake_site(site, fanscout_gp.pull)
    except ValueError as e:
        assert "SHORT BOARD" in str(e)
        assert "150" in str(e)
    else:
        assert False, "a 150-row board must refuse, not replace a 481-row snapshot"


def test_parse_takes_the_name_and_gamesPlayed():
    parsed = fanscout_gp.parse(HTML)
    by_name = {r["name"]: r["gp"] for r in parsed["rows"]}
    assert by_name == {
        "Victor Wembanyama": 68.0,
        "AJ Dybantsa": 73.0,
        "Darryn Peterson": 68.0,
        "Cameron Boozer": 73.0,
    }
    assert parsed["season"] == "2026-27"


def test_parse_refuses_a_board_missing_the_incoming_rookies():
    html = HTML.replace("AJ Dybantsa", "Cooper Flagg")
    try:
        fanscout_gp.parse(html)
    except ValueError as e:
        assert "STALE" in str(e) or "rookie" in str(e).lower()
    else:
        assert False, "missing 2026-27 rookies must refuse, not pass as current season"


def test_snapshot_records_fetch_time_depth_and_rookie_proof():
    parsed = fanscout_gp.parse(HTML)
    snap = fanscout_gp.snapshot(parsed, fetched="2026-08-29T15:23:00Z")
    assert snap["fetched"] == "2026-08-29T15:23:00Z"
    assert snap["depth"] == 4
    assert snap["source"] == "fanscout projections"
    assert snap["url"] == "https://fanscout.pro/projections?players=1000"
    by_name = {r["name"]: r["gp"] for r in snap["rookies"]}
    assert by_name == {
        "AJ Dybantsa": 73.0,
        "Darryn Peterson": 68.0,
        "Cameron Boozer": 73.0,
    }
    assert [r["name"] for r in snap["rows"]] == [r["name"] for r in parsed["rows"]]


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
