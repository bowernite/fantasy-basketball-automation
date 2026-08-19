"""Canned Fleaflicker payloads for fetch tests."""

def pro_player(name, pid, tm="LAC", pos="G", elig=("PG", "SG")):
    return {"id": pid, "nameFull": name, "position": pos,
            "proTeamAbbreviation": tm, "positionEligibility": list(elig)}

def snapshot_payload(*rows):
    """`FetchRoster?season=` for a whole team, one (proPlayer, FPts/G, total)
    per body"""
    return {"groups": [{"slots": [
        {"leaguePlayer": {"proPlayer": p, "seasonAverage": {"value": avg},
                          "seasonTotal": {"value": tot}}}
        for p, avg, tot in rows]}]}

def league_payload(*teams):
    """`FetchLeagueRosters` with no `season=`: live ownership for all 12 teams
    as a flat player list per team, and -- the whole reason the snapshot is
    still fetched -- no stat line anywhere on it"""
    return {"rosters": [{"team": {"id": tid, "name": "Team %d" % tid},
                         "players": [{"proPlayer": p} for p in pros]}
                        for tid, pros in teams]}

STUB_FLEAFLICKER = '''"""`fetch_data.py` against a canned Fleaflicker: the same
__main__, the same files, no network. `feed.json` beside this file supplies the
two endpoints the roster flow calls."""
import io, json, runpy, sys, time, urllib.request

FEED = json.load(open("feed.json"))


def urlopen(url, timeout=None):
    if "FetchLeagueRosters" in url:
        payload = FEED["league"]
    elif "FetchRoster" in url:
        payload = FEED["snapshots"][url.split("team_id=")[1].split("&")[0]]
    else:
        raise AssertionError("unstubbed request: " + url)
    return io.BytesIO(json.dumps(payload).encode())


urllib.request.urlopen = urlopen
time.sleep = lambda *a: None                  # the 1.1s courtesy pause per team
sys.argv = ["fetch_data.py"] + sys.argv[1:]
runpy.run_path("fetch_data.py", run_name="__main__")
'''
