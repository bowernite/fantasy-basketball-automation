"""Rebuild the data files `sim.py` reads. Bump `SEASON`, then run.

    ./run fetch_data.py            # schedule + league (fast, ~30 requests)
    ./run fetch_data.py pool       # + players-<season>.json (~20 min, resumable)
    ./run fetch_data.py roster 160941 161020    # any team, for `./run sim.py --roster`
    ./run fetch_data.py roster                  # all 12

`roster-<team_id>-<season>.json`  schema `sim.py` prices: `{n, tm, avg, tot,
    gp, posLabel, elig}`. Membership from `FetchLeagueRosters`, rates from
    `FetchRoster?season=` (see `merged_rows` -- the season endpoint's
    membership goes stale after March). `assumed_trades.apply_all` then
    overlays deals we treat as done even if the wire still shows them pending.

`teams-<season>.json`  `{team_id: team name}`, written by the same `roster` run.

`nba-schedule-*.json`  ET date -> NBA teams playing, from ESPN's scoreboard API
    (NBA CDN and data.nba.com both 403). Postponed games dropped -- ESPN lists
    them at both the original and makeup date. All-Star dropped; NBA Cup final
    kept (real box scores).

`league-<season>.json`  fantasy calendar + real weekly scores, from
    Fleaflicker. `periods` comes from `eligibleSchedulePeriods` -- do not
    assume 7-day weeks or 23 of them.

`players-<season>.json`  every player Fleaflicker has data for: FPts/G and GP
    for five past seasons plus a birthday. Feeds the board-rank -> FPts/G
    bridge and the expected-GP prior. Re-running is cheap -- only fetches
    what's missing.
"""
import collections
import datetime
import json
import os
import time
import urllib.request
import zoneinfo

import assumed_trades

HERE = os.path.dirname(os.path.abspath(__file__))
ET = zoneinfo.ZoneInfo("America/New_York")


def dest_path(name):
    """roster-* -> rosters/; everything else -> data/."""
    folder = "rosters" if os.path.basename(name).startswith("roster-") else "data"
    return os.path.join(HERE, folder, os.path.basename(name))

# `sim.py` imports SEASON from here, not vice versa, since it loads these data
# files at import time. Filenames carry the tag so bumping this writes new
# files instead of overwriting last season's
SEASON = 2025                                  # Fleaflicker start-year: '25-26
SEASON_TAG = "%d-%02d" % (SEASON, (SEASON + 1) % 100)

MONTHS = (["%d%02d" % (SEASON, m) for m in (10, 11, 12)]
          + ["%d%02d" % (SEASON + 1, m) for m in (1, 2, 3, 4)])
LEAGUE = 30579
TEAM = 161025                                  # ours, and just an id like any other
ALLSTAR = {"STARS", "STRIPES", "WORLD"}


def get(url, tries=5):
    """Retries -- a ~700-request serial pull hits transient TLS/socket errors
    often enough to kill the run."""
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(url, timeout=60))
        except Exception as e:                   # noqa: BLE001 -- any transport error
            if i == tries - 1:
                raise
            print("    retry %d after %s" % (i + 1, type(e).__name__))
            time.sleep(3 * (i + 1))


def nba_schedule():
    events = {}
    for m in MONTHS:
        events.update({e["id"]: e for e in get(
            "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
            "/scoreboard?dates=%s&limit=500" % m)["events"]})
    daymap = collections.defaultdict(set)
    for e in events.values():
        if e["season"]["type"] != 2:            # 2 = regular season
            continue
        comp = e["competitions"][0]
        if comp["status"]["type"]["name"] == "STATUS_POSTPONED":
            continue
        tms = {c["team"]["abbreviation"] for c in comp["competitors"]}
        if tms & ALLSTAR:
            continue
        d = (datetime.datetime.strptime(e["date"], "%Y-%m-%dT%H:%MZ")
             .replace(tzinfo=datetime.timezone.utc).astimezone(ET).date())
        daymap[d.isoformat()] |= tms
    return {"daymap": {d: sorted(t) for d, t in sorted(daymap.items())}}


def fantasy_calendar():
    sb = get("https://www.fleaflicker.com/api/FetchLeagueScoreboard"
             "?sport=NBA&league_id=%d&season=%d" % (LEAGUE, SEASON))
    periods = []
    for p in sb["eligibleSchedulePeriods"]:
        day = lambda k: (datetime.datetime.fromtimestamp(
            int(p[k]["startEpochMilli"]) / 1000, ET).date().isoformat())
        # `scoring_period` is a 1-indexed DAY ordinal, not a period ordinal;
        # `schedule_period` 400s. Take the day ordinal from `low`.
        r = get("https://www.fleaflicker.com/api/FetchLeagueScoreboard?sport=NBA"
                "&league_id=%d&season=%d&scoring_period=%d"
                % (LEAGUE, SEASON, p["low"]["ordinal"]))
        assert r["schedulePeriod"]["ordinal"] == p["ordinal"]
        games, kinds = {}, set()
        for g in r["games"]:                     # dedupe on game id
            kinds.add("playoff" if g.get("isPlayoffs") else
                      "consolation" if g.get("isConsolation") else "regular")
            games[g["id"]] = [g["away"]["name"], g["awayScore"]["score"]["value"],
                              g["home"]["name"], g["homeScore"]["score"]["value"]]
        periods.append({"ordinal": p["ordinal"], "start": day("low"),
                        "end": day("high"), "kinds": sorted(kinds),
                        "games": [games[k] for k in sorted(games)]})
        time.sleep(1.1)                          # sustained requests 403
    return {"periods": periods}


def roster_rows(payload):
    """`FetchRoster?season=` -> roster rows `sim.our_roster` reads.

    `elig` from `proPlayer.positionEligibility`, not `rankFantasy.positions[]`,
    which is absent for a player who missed the season.

    GP = `seasonTotal / seasonAverage` -- the only place GP appears here.
    Fleaflicker omits zero fields, so absent stats mean 0 games.
    """
    out = []
    for g in payload["groups"]:
        for s in g["slots"]:
            lp = s.get("leaguePlayer")
            if not lp:
                continue
            pro = lp["proPlayer"]
            avg = lp.get("seasonAverage", {}).get("value") or 0.0
            tot = lp.get("seasonTotal", {}).get("value") or 0.0
            out.append({"n": pro["nameFull"],
                        "tm": pro.get("proTeamAbbreviation", "FA"),
                        "avg": avg, "tot": tot,
                        "gp": round(tot / avg) if avg else 0,
                        "posLabel": pro.get("position", ""),
                        "elig": sorted(pro.get("positionEligibility", []))})
    return out


def merged_rows(league, team_id, snapshot, pool):
    """One team's LIVE roster in the priceable schema.

    Membership from `FetchLeagueRosters`, rates from `FetchRoster?season=` --
    the season endpoint's membership is stale as of its last lineup period
    (~end of March), so it's never the source of truth for who's on a roster.

    A body missing from the snapshot played for somebody else last season, so
    his rate comes off the player pool instead of reading 0.

    Joins on Fleaflicker's player id, not name -- the league has rostered two
    Jaylin Williamses. The pool fallback joins on name, since `player_pool`
    keys on it.

    `tm`/`posLabel`/`elig` come from the live feed, the fresher of the two.
    """
    rated = {}
    for g in snapshot["groups"]:
        for s in g["slots"]:
            lp = s.get("leaguePlayer")
            if lp:
                rated[lp["proPlayer"]["id"]] = lp
    live = [t for t in league["rosters"] if t["team"]["id"] == team_id]
    if not live:
        raise KeyError("team %d is not in league %d -- ids are in the "
                       "`team-info` Skill" % (team_id, LEAGUE))
    # snapshot order, adds appended -- this seeds `sim.swap`/`sim.pad`'s rng
    # draw, so the live feed's order would re-roll every player and shift
    # published figures within noise
    order = list(rated).index
    players = sorted(live[0]["players"],
                     key=lambda p: order(p["proPlayer"]["id"])
                     if p["proPlayer"]["id"] in rated else len(rated))
    out = []
    for p in players:
        pro = p["proPlayer"]
        lp = rated.get(pro["id"], {})
        avg = lp.get("seasonAverage", {}).get("value") or 0.0
        tot = lp.get("seasonTotal", {}).get("value") or 0.0
        gp = round(tot / avg) if avg else 0
        if not avg:
            avg, gp = pool.get(pro["nameFull"], {}).get(
                "seasons", {}).get(str(SEASON), (0.0, 0))
            tot = avg * gp
        out.append({"n": pro["nameFull"],
                    "tm": pro.get("proTeamAbbreviation", "FA"),
                    "avg": avg, "tot": tot, "gp": gp,
                    "posLabel": pro.get("position", ""),
                    "elig": sorted(pro.get("positionEligibility", []))})
    return out


def league_rosters():
    """LIVE ownership for all 12 teams, in one request.

    No `season=` -- with it, the response is the same stale end-of-March
    snapshot `FetchRoster?season=` returns. Carries no stat line; rates still
    come from the season endpoint.
    """
    return get("https://www.fleaflicker.com/api/FetchLeagueRosters?sport=NBA"
               "&league_id=%d" % LEAGUE)


def team_roster(team_id, league, pool):
    """One roster, live and priceable by `sim.py --roster`. See `merged_rows`.

    `season=` is required here for rates -- omit it and `seasonAverage`
    disappears from every row.
    """
    d = get("https://www.fleaflicker.com/api/FetchRoster?sport=NBA"
            "&league_id=%d&team_id=%d&season=%d" % (LEAGUE, team_id, SEASON))
    name = next((t["team"]["name"] for t in league["rosters"]
                 if t["team"]["id"] == team_id), "?")
    rows = merged_rows(league, team_id, d, pool)
    snap = {q["n"] for q in roster_rows(d)}
    off_pool = [r["n"] for r in rows if r["avg"] and r["n"] not in snap]
    blank = [r["n"] for r in rows if not r["avg"]]
    print("  team %d (%s): %d bodies%s%s"
          % (team_id, name, len(rows),
             "; off the pool: " + ", ".join(off_pool) if off_pool else "",
             "; no last-season line: " + ", ".join(blank) if blank else ""))
    return rows


def load_pool():
    """`players-<season>.json` if present. Absent is not fatal -- it costs a
    March add his last-season line."""
    path = dest_path("players-%s.json" % SEASON_TAG)
    if not os.path.exists(path):
        print("  no %s -- a body the season snapshot lacks will read 0/0"
              % os.path.basename(path))
        return {}
    with open(path) as f:
        return json.load(f)


POOL_SEASONS = [SEASON - i for i in range(5)]
SEASON_DONE = 300          # a fully paged season yields ~450 player-seasons


def player_pool(path=None):
    """name -> {id, tm, elig, born, seasons: {season: [FPts/G, GP]}}.

    Reads `viewingActualPoints(Average)`, not `seasonAverage`/`seasonTotal`,
    which are empty for any season the league itself hasn't run and disagree
    slightly with the game log even for the current one. Totals are
    regular-season only -- `FetchPlayerProfile`'s game log is not, so it's
    the wrong GP source.

    `sort=` only works for the season with `seasonAverage` populated, so page
    the whole pool regardless. `resultTotal` (1300) understates it and the
    server clamps the offset, so walk to 1330.

    Incremental and resumable -- reloads `path`, skips seasons/players already
    cached, and checkpoints so an interrupt costs one season, not the run.
    """
    out = {}
    path = path or dest_path("players-%s.json" % SEASON_TAG)
    if os.path.exists(path):
        with open(path) as f:
            out = json.load(f)

    def save():
        with open(path, "w") as f:
            json.dump(out, f, indent=0, sort_keys=True)

    for season in POOL_SEASONS:
        # gates on `id` too -- a file written before ids existed has seasons
        # but no id
        have = [v for v in out.values() if str(season) in v["seasons"]]
        if len(have) >= SEASON_DONE and all(v.get("id") for v in have):
            print("  season %d: cached" % season)
            continue
        n = 0
        for off in range(0, 1331, 30):
            r = get("https://www.fleaflicker.com/api/FetchPlayerListing?sport=NBA"
                    "&league_id=%d&filter.free_agent_only=false"
                    "&sort=SORT_SEASON_AVERAGE&sort_season=%d&result_offset=%d"
                    % (LEAGUE, season, off))
            for p in r.get("players", []):
                pro, avg = p["proPlayer"], p.get("viewingActualPointsAverage", {})
                tot = p.get("viewingActualPoints", {})
                # absent stats are `{"formatted": "-"}` with no `.value` --
                # key presence alone is a false positive
                if "value" not in avg or "value" not in tot or not avg["value"]:
                    continue
                e = out.setdefault(pro["nameFull"], {
                    "tm": pro.get("proTeamAbbreviation", "FA"),
                    "elig": pro.get("positionEligibility", []), "seasons": {}})
                e["id"] = pro["id"]
                e["seasons"][str(season)] = [round(avg["value"], 3),
                                             round(tot["value"] / avg["value"])]
                n += 1
            time.sleep(1.1)                      # sustained requests 403
        print("  season %d: %d player-seasons" % (season, n))
        save()

    todo = [n for n, v in out.items() if "born" not in v and v.get("id")]
    print("  birthdays: %d cached, %d to fetch" % (len(out) - len(todo), len(todo)))
    for i, name in enumerate(todo):
        d = get("https://www.fleaflicker.com/api/FetchPlayerProfile?sport=NBA"
                "&league_id=%d&player_id=%d" % (LEAGUE, out[name]["id"])
                ).get("detail", {})
        # UTC, not local -- `date.fromtimestamp` would put a midnight-UTC dob
        # on the previous day west of Greenwich
        out[name]["born"] = (datetime.datetime.fromtimestamp(
            int(d["dob"]) / 1000, datetime.timezone.utc).date().isoformat()
            if d.get("dob") else None)
        if i % 25 == 24:
            save()
            print("    %d/%d" % (i + 1, len(todo)))
        time.sleep(1.1)
    save()
    return out


USAGE = """usage: ./run fetch_data.py [pool]
       ./run fetch_data.py roster [team id ...]
       ./run fetch_data.py teams

Rebuilds the data files sim.py reads, into rosters/ and data/.

  (no argument)   nba-schedule + league  (~30 requests)
  pool            + players  (~20 min, resumable)
  roster [ids]    roster + teams files, all 12 if no ids. Applies
                  assumed-through overlays (`assumed_trades`)
  teams           teams file alone: id -> team name labels"""


def write(name, build, **dump):
    """Build first, write second, land by rename -- so a failed re-scrape
    can't leave a zero-byte file where a good one was."""
    data = build()
    path = dest_path(name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "w") as f:
        json.dump(data, f, **dump)
    os.replace(tmp, path)
    print("wrote", path)


def team_names(league):
    """`{team_id: name}`, all 12, for labelling every table `sim.py` prints."""
    return {str(t["team"]["id"]): t["team"]["name"] for t in league["rosters"]}


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if {"-h", "--help", "help"} & set(args):
        print(USAGE)
        sys.exit(0)
    if args[:1] == ["teams"] and len(args) == 1:
        write("teams-%s.json" % SEASON_TAG,
              lambda: team_names(league_rosters()), indent=0, sort_keys=True)
        sys.exit(0)
    if args[:1] == ["roster"]:
        # validated before the first request -- `roster abc` used to make a
        # league call and truncate a roster file before dying on `int()`
        bad = [t for t in args[1:] if not t.isdigit()]
        if bad:
            sys.exit("not a team id: %s\nids are numeric (`team-info`); "
                     "`roster` with none re-cuts all 12.\n\n%s"
                     % (", ".join(bad), USAGE))
        league, pool = league_rosters(), load_pool()
        # all 12 names whichever ids were asked for -- a partial map makes one
        # report's header inconsistent with the next
        names = team_names(league)
        write("teams-%s.json" % SEASON_TAG, lambda: names,
              indent=0, sort_keys=True)
        ids = args[1:] or sorted(names)
        unknown = [t for t in ids if t not in names]
        if unknown:
            sys.exit("no such team in league %d: %s\nthe league carries: %s"
                     % (LEAGUE, ", ".join(unknown),
                        ", ".join("%s (%s)" % (i, n)
                                  for i, n in sorted(names.items()))))
        asked = [int(t) for t in ids]
        fetch_ids = assumed_trades.expand_ids(asked)
        extra = [i for i in fetch_ids if i not in asked]
        if extra:
            print("  assumed overlay: also re-cutting %s"
                  % ", ".join("%s (%s)" % (i, names[str(i)]) for i in extra))
        built = {}
        for t in fetch_ids:
            built[t] = team_roster(t, league, pool)
            time.sleep(1.1)                          # sustained requests 403
        nchg = assumed_trades.apply_all(built)
        if nchg:
            print("  assumed overlay: moved bodies on %d roster(s)" % nchg)
        for t in fetch_ids:
            # key order is the schema
            write("roster-%s-%s.json" % (t, SEASON_TAG),
                  lambda t=t: built[t])
        sys.exit(0)
    # unrecognised args refuse rather than falling through to a re-scrape
    unknown = [a for a in args if a != "pool"]
    if unknown:
        sys.exit("unrecognised argument: %s\n\n%s" % (", ".join(unknown), USAGE))
    write("nba-schedule-%s.json" % SEASON_TAG, nba_schedule,
          indent=0, sort_keys=True)
    write("league-%s.json" % SEASON_TAG, fantasy_calendar,
          indent=0, sort_keys=True)
    if "pool" in args:
        write("players-%s.json" % SEASON_TAG, player_pool,
              indent=0, sort_keys=True)
