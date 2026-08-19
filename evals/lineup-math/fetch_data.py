"""Rebuild the data files `sim.py` reads. Bump `SEASON`, then run.

    ./run fetch_data.py            # schedule + league (fast, ~30 requests)
    ./run fetch_data.py pool       # + players-<season>.json (~20 min, resumable)
    ./run fetch_data.py roster 160941 161020    # any team, for `./run sim.py --roster`
    ./run fetch_data.py roster                  # all 12

`roster-<team_id>-<season>.json`  one team's LIVE roster in the schema `sim.py`
    prices: `{n, tm, avg, tot, gp, posLabel, elig}`. Membership comes from
    `FetchLeagueRosters` and only the rates from `FetchRoster?season=` -- see
    `merged_rows` for why reading membership off the season endpoint quietly
    priced four teams off bodies they no longer owned. OURS is written by the
    same command (`roster 161025`), so re-fetching after a trade executes lands
    on the file `sim.ROSTER` reads. Body counts still differ between teams, so
    pad to a common count (`sim.pad`) before comparing R or WINS across two.

`teams-<season>.json`  `{team_id: team name}` for all 12, written by the same
    `roster` run whatever ids it was given. Its only job is labelling output:
    every table `sim.py` prints names the roster it priced, and a bare
    `roster-161020-2025-26.json` is a team only to a reader holding the
    `team-info` table. Absent is not fatal -- the id is printed alone.

`nba-schedule-*.json`  ET date -> NBA teams playing. From ESPN's scoreboard API
    (`site.api.espn.com/.../basketball/nba/scoreboard?dates=YYYYMM`); the NBA CDN
    and data.nba.com both 403. Postponed games are dropped -- ESPN lists them at
    BOTH the original and the makeup date, which is what put 10 teams on 83 games
    in the first version of this file. All-Star is dropped. The NBA Cup final is
    kept: it is an 83rd game for its two participants and it produces real box
    scores, so it scores in fantasy.

`league-<season>.json`  the fantasy calendar and the real weekly scores, from
    Fleaflicker. `periods` comes from `eligibleSchedulePeriods` -- do NOT assume
    7-day weeks or 23 of them. Each period's `games` are [away, awayPF, home,
    homePF], which calibrates the sim, prices PF in wins, and keeps the
    head-to-head pairing so the margin distribution is auditable both pooled and
    per actual opponent.

`players-<season>.json`  every player Fleaflicker has data for, with FPts/G and
    GP for five past seasons plus a birthday. Two things depend on it and nothing
    else can supply them: the **board-rank -> FPts/G bridge** (is a scenario
    purchasable at all?) and a **measured** expected-GP prior (the input `sim.py`
    calls dominant). Re-running is cheap -- it only fetches what it lacks.
"""
import collections
import datetime
import json
import os
import time
import urllib.request
import zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
ET = zoneinfo.ZoneInfo("America/New_York")

# THE season constant, for both files -- `sim.py` imports it from here rather
# than the other way round, because `sim.py` loads these data files at import and
# so cannot be imported before they exist. Every data filename carries the tag,
# so rolling the season writes new files instead of overwriting last season's
# under last season's name. Bump this, re-run, then bump nothing else.
SEASON = 2025                                  # Fleaflicker start-year: '25-26
SEASON_TAG = "%d-%02d" % (SEASON, (SEASON + 1) % 100)

MONTHS = (["%d%02d" % (SEASON, m) for m in (10, 11, 12)]
          + ["%d%02d" % (SEASON + 1, m) for m in (1, 2, 3, 4)])
LEAGUE = 30579
TEAM = 161025                                  # ours, and just an id like any other
ALLSTAR = {"STARS", "STRIPES", "WORLD"}


def get(url, tries=5):
    """Retries. A ~700-request serial pull hits a transient TLS/socket error often
    enough that one kills the run, and dropping a page silently biases the pool."""
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
    """`FetchRoster?season=` -> the roster rows `sim.our_roster` reads.

    `elig` off `proPlayer.positionEligibility`, NOT `rankFantasy.positions[]`:
    the two agree on every row that played, but `rankFantasy` is keyed to season
    TOTALS and is absent entirely for a player who missed the season, which is
    how two guards reached the roster file with `elig: []`.

    GP is `seasonTotal / seasonAverage` -- the only place GP appears on this
    endpoint. Fleaflicker omits zero fields, so absent stats mean 0 games.
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

    MEMBERSHIP off `FetchLeagueRosters`, rates off `FetchRoster?season=`, and
    the split is the whole point. The season endpoint answers as of the season's
    LAST LINEUP PERIOD (~end of March): every add after it is missing and every
    drop is still on it, silently. Four teams were priced for months off bodies
    they no longer owned, so membership is never the season endpoint's to state.

    A body the snapshot has no line for played the season for somebody else, so
    his line comes off the player pool (`players-<season>.json`, already on
    disk) rather than reading 0. `our_roster` takes the RATE from the projection
    -- but a player the feed does not carry keeps this one and prints `noproj`,
    and a zero there prices a real producer as an empty body. A player neither
    source has is 0/0, which is the `nopool` path `our_roster` documents.

    MEMBERSHIP and rates join on Fleaflicker's player id, never on the name:
    the league has rostered two Jaylin Williamses. The POOL fallback above is
    the exception and joins on the name, because `player_pool` keys on it --
    two players spelled the same share one entry there and so one `seasons`
    history, wherever the pool is read (`simlib.board.pool`).

    `tm`/`posLabel`/`elig` come off the LIVE feed, which is the fresher of the
    two for an NBA team that changed after March.
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
    # In the SNAPSHOT's order, adds on the end. Order is the rng draw order
    # (`sim.swap`, `sim.pad`), so taking the live feed's would re-roll every
    # player on a roster nobody traded on and move every published figure
    # inside its own noise.
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
    """LIVE ownership for all 12 teams, in ONE request.

    No `season=`. The param is not ignored: with it the response is the same
    end-of-March snapshot `FetchRoster?season=` returns, which is the thing this
    call exists to correct. It carries no stat line of any kind, so the season
    endpoint is still what supplies rates.
    """
    return get("https://www.fleaflicker.com/api/FetchLeagueRosters?sport=NBA"
               "&league_id=%d" % LEAGUE)


def team_roster(team_id, league, pool):
    """One roster, live and priceable by `sim.py --roster`. See `merged_rows`.

    `season=` is REQUIRED here for rates: omit it and `seasonAverage` disappears
    from every row. Body counts still differ between teams, so pad to a common
    count (`sim.pad`) before comparing R or WINS across two.
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
    """`players-<season>.json` if it is there. Absent is not fatal -- it costs
    a March add his last-season line, and `merged_rows` says what that means."""
    path = os.path.join(HERE, "players-%s.json" % SEASON_TAG)
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

    Read `viewingActualPoints` / `viewingActualPointsAverage`, NOT
    `seasonAverage` / `seasonTotal`. The latter exist only for seasons the league
    itself has run (`sortSeasons.eligibleValues`), so they are empty for every
    prior season -- and even for the current one they disagree slightly with the
    game log, while `viewingActualPoints` reconciles to it exactly. Historical
    points come back re-scored under our CURRENT rules, so a year-over-year
    comparison is apples-to-apples.

    `sort=` only works for a season with `seasonAverage` populated; for prior
    seasons the sort silently does nothing, so page the whole pool. `resultTotal`
    (1300) understates it and the server clamps the offset, so walk to 1330.
    Totals here are regular season only -- `FetchPlayerProfile`'s game log is not
    (96 rows for a 2025 starter), so it is the wrong source for GP.

    INCREMENTAL AND RESUMABLE. ~1 req/s serial, so five seasons plus one profile
    call per player is ~20 min: it reloads `path`, skips any season already
    complete and any player whose birthday is already known, and checkpoints so
    an interrupt costs one season rather than the run. `born` (not `age`) so the
    cache does not silently go stale.
    """
    out = {}
    path = path or os.path.join(HERE, "players-%s.json" % SEASON_TAG)
    if os.path.exists(path):
        with open(path) as f:
            out = json.load(f)

    def save():
        with open(path, "w") as f:
            json.dump(out, f, indent=0, sort_keys=True)

    for season in POOL_SEASONS:
        # `id` gates too: the birthday pass needs one per player, and a file
        # written before ids were stored has the seasons but not the ids.
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
                # Absent stats are `{"formatted": "-"}` with no `.value`, so test
                # for `value`; key presence is a false positive.
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
        # UTC, not local: `date.fromtimestamp` puts a midnight-UTC dob on the
        # previous day west of Greenwich, which is machine-dependent.
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

Rebuilds the data files sim.py reads, beside this script.

  (no argument)   nba-schedule-<season>.json + league-<season>.json  (~30 requests)
  pool            + players-<season>.json                    (~20 min, resumable)
  roster [ids]    roster-<id>-<season>.json per team, all 12 if no ids, and
                  teams-<season>.json
  teams           teams-<season>.json alone: the id -> team name labels

Every file it writes is announced by absolute path. Exits non-zero on an
unrecognised argument rather than falling through to a re-scrape."""


def write(name, build, **dump):
    """Build FIRST, write second, and land it by rename.

    `open(path, "w")` around the build truncated the good file and then let a
    transport error out of it, so a failed re-scrape left a ZERO-BYTE
    `league-<season>.json` where the season was. Every `sim.py` run after that
    died on a JSON decode error naming nothing that had happened.
    """
    data = build()
    path = os.path.join(HERE, name)
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
        # Every id validated BEFORE the first request: `roster abc` used to make
        # a league call, truncate a roster file and only then die on `int()`.
        bad = [t for t in args[1:] if not t.isdigit()]
        if bad:
            sys.exit("not a team id: %s\nids are numeric (`team-info`); "
                     "`roster` with none re-cuts all 12.\n\n%s"
                     % (", ".join(bad), USAGE))
        # ONE league call for membership, then one snapshot call per team. No
        # ids means all 12: they drift independently and a team you did not
        # re-cut is a team priced off whoever it owned in March.
        league, pool = league_rosters(), load_pool()
        # All 12 names whichever ids were asked for -- the labels cost nothing
        # extra and a partial map makes the output of one report inconsistent
        # with the next.
        write("teams-%s.json" % SEASON_TAG, lambda: team_names(league),
              indent=0, sort_keys=True)
        ids = args[1:] or sorted(team_names(league))
        unknown = [t for t in ids if t not in team_names(league)]
        if unknown:
            sys.exit("no such team in league %d: %s\nthe league carries: %s"
                     % (LEAGUE, ", ".join(unknown),
                        ", ".join("%s (%s)" % (i, n)
                                  for i, n in sorted(team_names(league).items()))))
        for t in ids:
            # key order is the schema
            write("roster-%s-%s.json" % (t, SEASON_TAG),
                  lambda t=t: team_roster(int(t), league, pool))
            time.sleep(1.1)                          # sustained requests 403
        sys.exit(0)
    # Anything unrecognised REFUSES rather than falling through: `fetch_data.py
    # rosters` (plural), `fetch_data.py 161025` and `fetch_data.py players` each
    # re-scraped the schedule and the calendar, printed `wrote ...` and exited 0.
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
