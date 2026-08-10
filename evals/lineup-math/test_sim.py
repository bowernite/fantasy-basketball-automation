"""python3 -m unittest test_sim -v"""
import collections
import contextlib
import glob
import importlib
import io
import itertools
import json
import math
import os
import random
import re
import runpy
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

import fetch_data
import sim
from simlib import bracket, engine, gp, roster as roster_mod, value
from simlib import reports
from simlib.reports import durability

THEIR_ROSTER = "roster-161020-2025-26.json"
ROOKIE_ROSTER = "roster-160941-2025-26.json"
THREE_OUT = ["Jalen Suggs", "Coby White", "Myles Turner"]
SNAPSHOT = os.path.join(sim.HERE, os.pardir, "board-snapshots", "projections",
                        "sleeper-2026.json")


@contextlib.contextmanager
def cheap_monte_carlo(trials=4, blocks=1):
    """A trial count that answers whether a report runs, not what it says

    These three bind their sample size as a default at import, so lowering
    `TRIALS` alone changes nothing. Patched on the module that defines each
    one, since `sim` forwards them both ways
    """
    real_run, real_wins, real_boot = (engine.run, value.player_wins,
                                      gp.gp_bootstrap)
    was_blocks = value.PLAYER_BLOCKS
    engine.run = lambda roster, **kw: real_run(roster, **dict(kw, trials=trials))
    value.player_wins = lambda roster, names, **kw: real_wins(
        roster, names, **dict(kw, trials=trials))
    gp.gp_bootstrap = lambda rows, **kw: real_boot(rows, **dict(kw, n=50))
    value.PLAYER_BLOCKS = blocks
    bracket.league.cache_clear()
    try:
        yield
    finally:
        engine.run, value.player_wins, gp.gp_bootstrap = (real_run, real_wins,
                                                          real_boot)
        value.PLAYER_BLOCKS = was_blocks
        bracket.league.cache_clear()


@contextlib.contextmanager
def league_rates(k):
    """Every projected rate in the league scaled by `k`, at the one place a
    roster reads the feed -- so every team inflates together, which is the only
    way to move a level without moving anybody's edge"""
    real = roster_mod.projected_rate
    roster_mod.projected_rate = lambda n: (None if real(n) is None
                                           else k * real(n))
    bracket.league.cache_clear()
    try:
        yield
    finally:
        roster_mod.projected_rate = real
        bracket.league.cache_clear()


@contextlib.contextmanager
def recorded_rosters(trials=2):
    """Every roster `engine.run` is handed while the block runs, by name. Which
    bodies a column was priced on is not visible in the number it returns,
    since two bottom-grade rooms are under the noise apart"""
    seen, real = [], engine.run
    engine.run = lambda roster, **kw: (
        seen.append([p["n"] for p in roster]),
        real(roster, **dict(kw, trials=trials)))[1]
    try:
        yield seen
    finally:
        engine.run = real


@contextlib.contextmanager
def projection_snapshot(text):
    """Points `projections` at a snapshot file we wrote and lets the sim read
    it through its own loader, scorer and name join, so the file on disk is the
    only thing stubbed. `text=None` points it at a path with nothing on it"""
    sleeper = skill_module("projections", "sleeper")
    path = os.path.join(tempfile.mkdtemp(), "sleeper-2026.json")
    if text is not None:
        with open(path, "w") as f:
            f.write(text)
    was, sleeper.SNAPSHOT = sleeper.SNAPSHOT, path
    sim._projections.cache_clear()
    try:
        yield
    finally:
        sleeper.SNAPSHOT = was
        sim._projections.cache_clear()


def sleeper_rows(*lines):
    """A snapshot payload, in the feed's own shape"""
    return json.dumps({"season": "2026", "source": "test", "updated": 0,
                       "depth": len(lines),
                       "rows": [{"name": n, "updated": 0, "stats": s}
                                for n, s in lines]})


def roster_file(*rows):
    """A one-off roster file in the shape `fetch_data.py roster` writes, the
    only way to hand `our_roster` a row no committed file carries"""
    path = os.path.join(tempfile.mkdtemp(), "theirs.json")
    with open(path, "w") as f:
        json.dump(list(rows), f)
    return path


def committed_rosters():
    """Every roster file in the tree for THIS season. The league is 12 and they
    are re-cut with `fetch_data.py roster <id>`, so the set is the directory's
    to state -- and the previous season's files sit beside them"""
    return sorted(glob.glob(os.path.join(sim.HERE, bracket.ROSTERS)))


def rostered(name, path=None, projected=True):
    """His row on a loaded roster, exactly one or the unpacking says so"""
    p, = [q for q in sim.our_roster(path, projected=projected)
          if q["n"] == name]
    return p


def season_value(p):
    """Rate x games, the whole season of production a body supplies"""
    return p["avg"] * p["gp"]


def flat_R(rate=15.0):
    """One replacement level for all three slot groups, for a test whose
    subject is not which group a body lands in"""
    return dict.fromkeys(sim.GROUPS, rate)


def skills_path(*parts):
    return os.path.join(sim.HERE, os.pardir, os.pardir, ".claude", "skills",
                        *parts)


def skill_module(skill, name):
    path = skills_path(skill)
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module(name)


def read_text(path):
    with open(path) as f:
        return f.read()


def one_line(text):
    """Single-spaced, so a sentence can be matched across the wraps it is
    printed or written in"""
    return " ".join(text.split())


def render(report, roster=None):
    """The stdout of one report, driven the way `__main__` drives it.
    `roster_mod` is where `basis` reads the default path from, so this sets it
    there"""
    was = roster_mod.ROSTER
    if roster:
        roster_mod.ROSTER = roster
    buf = io.StringIO()
    try:
        with cheap_monte_carlo(), contextlib.redirect_stdout(buf):
            sim.REPORTS[report]()
    finally:
        roster_mod.ROSTER = was
    return buf.getvalue()


def cli(*args):
    """One `python3 sim.py ...`, argv parsing and all, without the process

    Returns (exit status, everything the run said). `sim.py` exits with its
    explanation as the status, so that text is folded into the output too
    """
    was_argv, was_roster = sys.argv, roster_mod.ROSTER
    sys.argv = ["sim.py"] + list(args)
    buf, status = io.StringIO(), 0
    try:
        with cheap_monte_carlo(), contextlib.redirect_stdout(buf):
            runpy.run_path(sim.__file__, run_name="__main__")
    except SystemExit as e:
        status = e.code
    finally:
        sys.argv, roster_mod.ROSTER = was_argv, was_roster
    return status, buf.getvalue() + (status if isinstance(status, str) else "")


def sim_process(*args):
    """One real `python3 sim.py ...`, real interpreter, real argv, real exit
    status, at the published trial counts. The paths worth this are the ones
    `cli` cannot reach, how the command behaves as it is actually typed"""
    return subprocess.run([sys.executable, "sim.py"] + list(args),
                          cwd=sim.HERE, capture_output=True, text=True)


def roster_payload(**over):
    """One `FetchRoster?season=` row, trimmed to the keys the transform reads.
    Fleaflicker omits zero and default fields entirely, so the shape that bites
    is a row with no `seasonAverage`, `seasonTotal` or `rankFantasy` at all"""
    row = {"proPlayer": {"id": 1, "nameFull": "Darius Garland", "position": "G",
                         "proTeamAbbreviation": "LAC",
                         "positionEligibility": ["PG", "SG"]},
           "seasonAverage": {"value": 31.894444},
           "seasonTotal": {"value": 1435.25},
           "rankFantasy": {"positions": [
               {"position": {"eligibility": ["PG"]}},
               {"position": {"eligibility": ["SG"]}}]}}
    row.update(over)
    return {"groups": [{"slots": [{}, {"leaguePlayer": row}]}]}


class FetchRosterTransform(unittest.TestCase):
    """`--roster their.json` is advertised for any counterparty, so the row
    shape `fetch_data` writes is what makes `REPL theirs` reproducible.
    Asserted rather than described"""

    def test_a_played_season_becomes_a_priceable_roster_row(self):
        self.assertEqual(fetch_data.roster_rows(roster_payload()),
                         [{"n": "Darius Garland", "tm": "LAC",
                           "avg": 31.894444, "tot": 1435.25, "gp": 45,
                           "posLabel": "G", "elig": ["PG", "SG"]}])

    def test_a_player_who_missed_the_whole_season_still_carries_his_positions(self):
        """A 0-GP row has no `seasonAverage`, so it has no `rankFantasy`
        either, which is how a player reaches the roster file with `elig: []`
        and gets guessed at as a guard. `positionEligibility` is on the row
        whether or not he played"""
        p = roster_payload(proPlayer={"id": 2, "nameFull": "Kyrie Irving",
                                      "position": "G",
                                      "proTeamAbbreviation": "DAL",
                                      "positionEligibility": ["PG", "SG"]})
        del p["groups"][0]["slots"][1]["leaguePlayer"]["seasonAverage"]
        del p["groups"][0]["slots"][1]["leaguePlayer"]["seasonTotal"]
        del p["groups"][0]["slots"][1]["leaguePlayer"]["rankFantasy"]
        self.assertEqual(fetch_data.roster_rows(p),
                         [{"n": "Kyrie Irving", "tm": "DAL", "avg": 0.0,
                           "tot": 0.0, "gp": 0, "posLabel": "G",
                           "elig": ["PG", "SG"]}])


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


class LiveRosterMerge(unittest.TestCase):
    """`FetchRoster?season=` is a snapshot as of the season's LAST LINEUP
    PERIOD, so every add after it is silently missing and every drop is
    silently still there -- four teams were priced for months off bodies they
    no longer owned. Membership is therefore the live league feed's to state
    and only the rates come off the snapshot"""

    def test_a_body_added_after_the_snapshot_is_on_the_roster(self):
        league = league_payload((161014, [
            pro_player("Darius Garland", 1),
            pro_player("Steven Adams", 9, "HOU", "C", ("C",))]))
        rows = fetch_data.merged_rows(league, 161014, roster_payload(), {})
        self.assertEqual([r["n"] for r in rows],
                         ["Darius Garland", "Steven Adams"])

    def test_a_body_dropped_after_the_snapshot_is_off_the_roster(self):
        """The other half of the same defect, and the more expensive one: a
        traded-away player left on the file is priced as an asset the team no
        longer has"""
        snapshot = snapshot_payload(
            (pro_player("Darius Garland", 1), 31.9, 1435.25),
            (pro_player("Nick Richards", 7, "PHX", "C", ("C",)), 20.0, 1000.0))
        league = league_payload((161014, [pro_player("Darius Garland", 1)]))
        rows = fetch_data.merged_rows(league, 161014, snapshot, {})
        self.assertEqual([r["n"] for r in rows], ["Darius Garland"])

    def test_a_body_the_snapshot_never_saw_takes_last_season_off_the_pool(self):
        """He played the season, just not for this team, so his own team's
        snapshot has no line for him -- `players-<season>.json` does, and it is
        already on disk. Zeroing him instead publishes a real producer as an
        empty body, and `noproj` would then price him at nothing"""
        league = league_payload((161014, [
            pro_player("Steven Adams", 9, "HOU", "C", ("C",))]))
        pool = {"Steven Adams": {"seasons": {"2024": [10.0, 5], "2025": [23.117, 32]}}}
        row, = fetch_data.merged_rows(league, 161014, snapshot_payload(), pool)
        self.assertEqual(row, {"n": "Steven Adams", "tm": "HOU", "avg": 23.117,
                               "tot": 739.744, "gp": 32, "posLabel": "C",
                               "elig": ["C"]})

    def test_the_bodies_keep_the_snapshot_order_and_the_new_ones_append(self):
        """Roster ORDER is the rng draw order (`swap`, `pad`), so re-ordering a
        file nobody traded on re-rolls every player's availability and moves
        every published figure inside its own noise. The live feed lists bodies
        in its own order; taking it would do exactly that, so the snapshot's
        order stands and an add goes on the end the way `pad` appends"""
        snapshot = snapshot_payload(
            (pro_player("Darius Garland", 1), 31.9, 1435.25),
            (pro_player("Zach Edey", 3, "MEM", "C", ("C",)), 33.7, 371.0))
        league = league_payload((161014, [
            pro_player("Steven Adams", 9, "HOU", "C", ("C",)),
            pro_player("Zach Edey", 3, "MEM", "C", ("C",)),
            pro_player("Darius Garland", 1)]))
        rows = fetch_data.merged_rows(league, 161014, snapshot, {})
        self.assertEqual([r["n"] for r in rows],
                         ["Darius Garland", "Zach Edey", "Steven Adams"])

    def test_two_bodies_who_share_a_name_keep_their_own_seasons(self):
        """The league has rostered two Jaylin Williamses. Joined on the name,
        one of them silently takes the other's rate and games, and the row that
        reaches the roster file is a body who never existed"""
        snapshot = snapshot_payload(
            (pro_player("Jaylin Williams", 4, "OKC", "F", ("PF", "C")),
             12.0, 600.0),
            (pro_player("Jaylin Williams", 5, "WAS", "F", ("PF",)), 30.0, 900.0))
        league = league_payload((161014, [
            pro_player("Jaylin Williams", 5, "WAS", "F", ("PF",)),
            pro_player("Jaylin Williams", 4, "OKC", "F", ("PF", "C"))]))
        rows = fetch_data.merged_rows(league, 161014, snapshot, {})
        self.assertEqual([(r["tm"], r["avg"], r["gp"]) for r in rows],
                         [("OKC", 12.0, 50), ("WAS", 30.0, 30)])

    def test_the_nba_team_is_the_live_feeds_and_not_the_march_snapshots(self):
        """`tm` is the SCHEDULE the sim prices a body on, so a February trade
        left him scoring on the nights his old NBA team played. Both feeds
        carry it and the live one is the fresher"""
        snapshot = snapshot_payload(
            (pro_player("Zach Edey", 3, "MEM", "C", ("C",)), 33.7, 371.0))
        league = league_payload((161014, [
            pro_player("Zach Edey", 3, "DAL", "F", ("PF", "C"))]))
        row, = fetch_data.merged_rows(league, 161014, snapshot, {})
        self.assertEqual(row, {"n": "Zach Edey", "tm": "DAL", "avg": 33.7,
                               "tot": 371.0, "gp": 11, "posLabel": "F",
                               "elig": ["C", "PF"]})

    def test_a_body_neither_feed_has_a_line_for_is_written_as_an_empty_one(self):
        """A rookie: no season snapshot anywhere and no pool history. 0/0 is
        the `nopool` row `our_roster` documents and prices off the projection,
        and the alternative here is a division by his zero rate"""
        league = league_payload((161014, [
            pro_player("Cooper Flagg", 11, "DAL", "F", ("SF", "PF"))]))
        row, = fetch_data.merged_rows(league, 161014, snapshot_payload(), {})
        self.assertEqual((row["avg"], row["tot"], row["gp"]), (0.0, 0.0, 0))

    def test_a_team_id_the_league_does_not_carry_refuses(self):
        """Writing what it found would be `[]`, and an empty roster file is the
        one input `our_roster` cannot tell from a real team -- it pads to 38 and
        prices the auction bodies as that owner's roster"""
        league = league_payload((161014, [pro_player("Darius Garland", 1)]))
        with self.assertRaises(KeyError) as e:
            fetch_data.merged_rows(league, 161099, roster_payload(), {})
        self.assertIn("161099", str(e.exception))


class CommittedRosterFiles(unittest.TestCase):
    """The twelve files are the counterparty flow's input and get re-cut with
    `fetch_data.py roster <id>` after every trade. A re-fetch that drops a
    team's positions prices that whole roster on guesses, and no report
    refuses, it fills slots with what it was given"""

    def test_every_committed_file_carries_the_eligibility_it_is_priced_on(self):
        """Asserted on the file rather than on the loaded row, because
        `our_roster` FILLS an empty `elig` from the one-letter `posLabel`, so a
        dropped "SF" comes back as PG/SG and every table still prints. The loss
        is only visible before the guess"""
        slots = {pos for elig in sim.GROUPS.values() for pos in elig}
        files = committed_rosters()
        self.assertGreaterEqual(len(files), 12, "a league of 12 has 12 rosters")
        for path in files:
            rows = json.loads(read_text(path))
            with self.subTest(roster=os.path.basename(path)):
                self.assertGreaterEqual(len(rows), 20, "a fragment, not a team")
                for r in rows:
                    self.assertTrue(r["elig"], "%s has no slot to fill" % r["n"])
                    self.assertLessEqual(set(r["elig"]), slots, r["n"])

    def test_every_committed_file_loads_into_bodies_that_price(self):
        """The other half. A body carrying neither a rate nor a games count
        plays 82 nights at nothing and drags the roster's own R down with it"""
        for path in committed_rosters():
            rows = sim.our_roster(os.path.basename(path))
            with self.subTest(roster=os.path.basename(path)):
                for p in rows:
                    self.assertGreater(p["avg"], 0, "%s prices as nothing" % p["n"])
                    self.assertTrue(0 < p["gp"] <= 82, "%s: %s gp" % (p["n"], p["gp"]))


class EmptyRosterFile(unittest.TestCase):
    """A fetch that reached nobody writes `[]`, and `basis` PADS that to 38
    auction-grade bodies. Every figure below it, replacement level above all,
    then comes out measured on pure filler under the file's name. The only
    thing that shows it is the table's own row count, and a reader looking at R
    is not counting rows"""

    def test_a_file_with_nobody_on_it_is_refused_instead_of_padded_into_a_team(self):
        p = sim_process("--roster", roster_file(), "players")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("wins lost if swapped", p.stdout)

    def test_the_refusal_names_the_file_that_carried_nobody(self):
        """The import path (`trades` step 5) reaches the same padding with no
        banner above it at all, and the file it was handed is the only thing
        telling the caller which of the twelve to re-fetch"""
        path = roster_file()
        with self.assertRaises(ValueError) as e:
            sim.basis(path)
        self.assertIn(path, str(e.exception))


class CLI(unittest.TestCase):
    def test_a_misspelled_report_name_fails_instead_of_printing_another_one(self):
        """`trades` and `eval-team` both mandate a sim run before recommending
        a deal. A silent fallback to `calibration` means `sim.py breakeven`
        exits 0 having printed a table the reader did not ask for, and he books
        it as the break-evens he thinks he just ran"""
        p = sim_process("breakeven")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("CALIBRATION", p.stdout)
        for name in sim.REPORTS:
            self.assertIn(name, p.stdout + p.stderr)

    def test_the_roster_flag_reaches_the_report_it_precedes(self):
        """`render` puts the path on `roster_mod` itself, so nothing it covers
        touches the flag parsing that is supposed to put a counterparty's file
        there. A `--roster` that quietly kept OUR file prints our players under
        his team's name, and `Δw theirs` is the one number the counterparty
        workflow exists to produce"""
        status, out = cli("--roster", THEIR_ROSTER, "players")
        self.assertEqual(status, 0, out)
        self.assertIn(THEIR_ROSTER, out, "the run has to name the file it priced")
        theirs = {p["n"] for p in sim.our_roster(THEIR_ROSTER)}
        for name in sorted(theirs):
            self.assertIn(name, out)
        for name in sorted({p["n"] for p in sim.our_roster()} - theirs):
            self.assertNotIn(name, out)

    def test_a_bad_name_beside_a_good_one_runs_neither(self):
        """Same booking hazard as a lone misspelling, one step later. `sim.py
        players breakeven` printing PLAYERS and then dying leaves a table on
        screen from a command that exited 1, and the reader quotes it as the
        run he asked for"""
        status, out = cli("players", "bogus")
        self.assertNotEqual(status, 0)
        self.assertNotIn("PLAYERS", out)

    def test_a_file_that_is_not_a_roster_is_refused_before_any_table_prints(self):
        """The existence check passed and the run then died on a JSON decode
        error mid-report, under a header that reads as a started run -- exactly
        what the path check above it was written to prevent. `--roster
        findings.md` and a half-written fetch both land here"""
        path = os.path.join(tempfile.mkdtemp(), "notaroster.json")
        with open(path, "w") as f:
            f.write("# notes\n")
        p = sim_process("--roster", path, "players")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertNotIn("PLAYERS", p.stdout)
        self.assertIn(path, p.stdout + p.stderr)

    def test_a_report_that_refuses_says_so_without_a_traceback(self):
        """Half these refusals are written as prose -- `schedules` on a roster
        with no auction slots, a missing board snapshot, a name the pool has
        never seen. They arrived wrapped in a stack trace, which reads as the
        command being broken rather than as the answer it is"""
        full = roster_file(*[
            {"n": "Body %d" % i, "tm": "LAC", "avg": 20.0, "tot": 0.0, "gp": 60,
             "posLabel": "F", "elig": ["SF", "PF"]} for i in range(38)])
        p = sim_process("--roster", full, "schedules", "positions")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("auction", p.stdout + p.stderr)
        self.assertIn("positions", p.stdout + p.stderr,
                      "the run died without saying what it never ran")

    def test_a_report_that_breaks_is_not_dressed_up_as_one_that_refuses(self):
        """The refusals above are authored prose and are caught as
        `ValueError`. `statistics.StatisticsError` IS a `ValueError`, and
        `playoffs` alone makes ~20 `mean`/`stdev` calls -- caught with them, a
        broken run prints a tidy one-line explanation with no file, no line and
        no traceback, and reads exactly like an answer"""
        name = sorted(sim.ROSTER_FREE)[0]
        was = reports.REPORTS[name]
        reports.REPORTS[name] = lambda: statistics.mean([])
        try:
            with self.assertRaises(statistics.StatisticsError):
                cli(name)
        finally:
            reports.REPORTS[name] = was

    def test_help_describes_every_report_without_running_one(self):
        """The whole point of the flag: an agent handed this command learns the
        surface from the command, not from README.md. A `--help` treated as a
        report name exits 1 with a bare list of words, which reads as a failure
        and describes nothing"""
        p = sim_process("--help")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertNotIn("=" * 72, p.stdout, "--help ran a report")
        for name in sim.REPORTS:
            self.assertIn(name, p.stdout)
            self.assertIn(sim.BLURB[name], p.stdout)

    def test_help_says_which_reports_refuse_a_counterparty_roster(self):
        """`--roster` on one of the four is the commonest way to mistype this
        command, and the refusal is the only place that list appears"""
        p = sim_process("--help")
        for name in sim.OURS_ONLY:
            self.assertRegex(p.stdout, r"%s.*\(ours only\)" % name)

    def test_a_slow_report_names_itself_before_it_finishes(self):
        """Two of the fourteen run for minutes, and every caller captures this
        through a pipe, which Python block-buffers. A run cut short then hands
        back ZERO bytes -- no report name, nothing separating slow from hung
        from crashed"""
        p = subprocess.Popen([sys.executable, "sim.py", "schedules"],
                             cwd=sim.HERE, stdout=subprocess.PIPE, text=True)
        first = []
        reader = threading.Thread(target=lambda: first.append(p.stdout.readline()))
        reader.daemon = True
        reader.start()
        reader.join(20)
        p.kill()
        p.wait()
        p.stdout.close()
        self.assertTrue(first, "nothing reached the pipe in 20s")
        self.assertIn("=", first[0])

    def test_each_report_header_names_the_roster_that_report_priced(self):
        """One banner on line 1 of a multi-report run leaves thousands of lines
        between it and the tables, and a single table lifted out of the run --
        which is how these get quoted -- carries no team at all"""
        status, out = cli("--roster", THEIR_ROSTER, "players", "positions")
        self.assertEqual(status, 0, out)
        heads = [l for l in out.splitlines()
                 if l.startswith(("PLAYERS", "POSITIONS"))]
        self.assertEqual(len(heads), 2, out)
        for head in heads:
            self.assertIn(THEIR_ROSTER, head)

    def test_a_report_that_reads_no_roster_does_not_claim_one(self):
        """`market` is the board and the pool; its table is byte-identical
        whatever `--roster` says. A header naming a counterparty over it
        attributes to that team a measurement of nobody"""
        status, out = cli("--roster", THEIR_ROSTER, "market")
        self.assertEqual(status, 0, out)
        self.assertNotIn(THEIR_ROSTER, out.splitlines()[1])

    def test_the_header_names_the_team_not_just_its_id(self):
        """`roster-161020-2025-26.json` is a team only to a reader holding the
        `team-info` table. The command knows the name at fetch time, so the run
        it labels should not send its reader to a skill file to find out whose
        roster he is looking at"""
        teams = json.loads(read_text(
            os.path.join(sim.HERE, "teams-%s.json" % fetch_data.SEASON_TAG)))
        status, out = cli("--roster", THEIR_ROSTER, "positions")
        self.assertEqual(status, 0, out)
        self.assertIn(teams[THEIR_ROSTER.split("-")[1]], out.splitlines()[1])

    def test_every_report_named_in_one_run_prints(self):
        """The README advertises the reports on one line, so a run that takes
        the first name and drops the rest answers half of what was asked with
        no sign that it did"""
        status, out = cli("nights", "formula")
        self.assertEqual(status, 0, out)
        self.assertIn("NIGHTS", out)
        self.assertIn("FORMULA", out)


class EveryReportRunsEndToEnd(unittest.TestCase):
    """A report that names the players it trades as literals breaks the moment
    the roster file is re-cut, and every unit underneath it stays green. The
    file is re-cut after every trade, so that is a standing hazard for any
    report holding a name, which is what makes every one worth paying for"""

    def test_every_report_runs_on_our_roster(self):
        for name in sorted(sim.REPORTS):
            with self.subTest(report=name):
                self.assertTrue(render(name).strip(), "printed nothing")

    def test_every_report_not_scoped_to_us_runs_on_a_counterparty_roster(self):
        """The other half of the same hazard. A counterparty's file is a
        DIFFERENT shape, 26 bodies not 28, unsigned players, whole seasons
        missing, none of our names, and `--roster` is advertised for any of
        them"""
        for name in sorted(set(sim.REPORTS) - sim.OURS_ONLY):
            with self.subTest(report=name):
                self.assertTrue(render(name, THEIR_ROSTER).strip(),
                                "printed nothing")


class FetchDataCLI(unittest.TestCase):
    """The other half of the command surface. It WRITES the files every report
    reads, so its failure modes are quieter and cost more"""

    def fetch(self, *args):
        return subprocess.run([sys.executable, "fetch_data.py"] + list(args),
                              cwd=sim.HERE, capture_output=True, text=True,
                              timeout=30)

    def test_an_unrecognised_argument_refuses_instead_of_re_scraping(self):
        """`rosters` (plural), `players`, a bare team id -- each fell through to
        the default branch, spent 30 requests overwriting the schedule and the
        calendar, printed `wrote ...` and exited 0"""
        before = {p: os.path.getmtime(p)
                  for p in glob.glob(os.path.join(sim.HERE, "*.json"))}
        p = self.fetch("rosters")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("wrote", p.stdout)
        self.assertEqual({q: os.path.getmtime(q) for q in before}, before)

    def test_a_non_numeric_team_id_is_caught_before_any_request(self):
        """`int(t)` raised only after a league call had been made and a roster
        file already truncated"""
        p = self.fetch("roster", "brett")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("brett", p.stdout + p.stderr)

    def test_help_names_every_thing_it_can_be_asked_for(self):
        p = self.fetch("--help")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        for word in ("pool", "roster", "teams"):
            self.assertIn(word, p.stdout)


class DataFileWrites(unittest.TestCase):
    """One function lands every file `sim.py` reads, and none of them is
    re-fetchable at will: the pool is a 20-minute scrape and the season it
    describes is over"""

    def test_a_rebuild_that_dies_mid_scrape_leaves_the_good_file_alone(self):
        """Opening the path for writing AROUND the build truncated it first, so
        a transport error left a zero-byte `league-<season>.json` where the
        season was, and every `sim.py` run after it died on a JSON decode error
        naming nothing that had happened"""
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "league-x.json"), "w") as f:
            f.write('{"periods": [1, 2, 3]}')

        def transport_error():
            raise RuntimeError("connection reset by peer")

        was = fetch_data.HERE
        fetch_data.HERE = d
        try:
            with self.assertRaises(RuntimeError):
                fetch_data.write("league-x.json", transport_error)
        finally:
            fetch_data.HERE = was
        self.assertEqual(read_text(os.path.join(d, "league-x.json")),
                         '{"periods": [1, 2, 3]}')
        self.assertEqual(os.listdir(d), ["league-x.json"],
                         "a half-written file was left behind to be read next")


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


class FetchDataWritesWhatSimReads(unittest.TestCase):
    """`fetch_data.py roster` is the sole writer of the twelve files every
    counterparty table is priced off, and of the id -> name map that labels
    them. Driven against a canned league so the files it lands can be read
    back, which is the only thing that shows the fetch and the sim agree on a
    schema"""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        shutil.copy(fetch_data.__file__, self.dir)
        with open(os.path.join(self.dir, "stub_fleaflicker.py"), "w") as f:
            f.write(STUB_FLEAFLICKER)
        self.ids = [161001 + i for i in range(12)]
        bodies = {t: [pro_player("Starter %d" % t, t * 10),
                      pro_player("Bench %d" % t, t * 10 + 1, "HOU", "C", ("C",))]
                  for t in self.ids}
        with open(os.path.join(self.dir, "feed.json"), "w") as f:
            json.dump({"league": league_payload(*sorted(bodies.items())),
                       "snapshots": {str(t): snapshot_payload(
                           (bodies[t][0], 30.0, 1500.0), (bodies[t][1], 10.0, 400.0))
                           for t in self.ids}}, f)

    def fetch(self, *args):
        return subprocess.run(
            [sys.executable, "stub_fleaflicker.py"] + list(args),
            cwd=self.dir, capture_output=True, text=True, timeout=60)

    def rosters(self):
        return sorted(f for f in os.listdir(self.dir) if f.startswith("roster-"))

    def test_naming_no_team_re_cuts_all_twelve(self):
        """They drift independently, so a team left un-recut is a team priced
        off whoever owned him in March -- which is how four went stale"""
        p = self.fetch("roster")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.rosters(),
                         sorted("roster-%d-%s.json" % (t, fetch_data.SEASON_TAG)
                                for t in self.ids))

    def test_the_rows_it_lands_are_the_rows_sim_prices(self):
        """The schema is this file's to state and `--roster` is the only reader
        of it, so a key renamed on either side shows up nowhere else"""
        self.assertEqual(self.fetch("roster", "161001").returncode, 0)
        rows = json.loads(read_text(os.path.join(
            self.dir, "roster-161001-%s.json" % fetch_data.SEASON_TAG)))
        self.assertEqual(rows, [
            {"n": "Starter 161001", "tm": "LAC", "avg": 30.0, "tot": 1500.0,
             "gp": 50, "posLabel": "G", "elig": ["PG", "SG"]},
            {"n": "Bench 161001", "tm": "HOU", "avg": 10.0, "tot": 400.0,
             "gp": 40, "posLabel": "C", "elig": ["C"]}])

    def test_asking_for_one_team_still_writes_all_twelve_labels(self):
        """The labels cost nothing extra, and a partial map makes the header of
        one report inconsistent with the next"""
        self.assertEqual(self.fetch("roster", "161001").returncode, 0)
        teams = json.loads(read_text(os.path.join(
            self.dir, "teams-%s.json" % fetch_data.SEASON_TAG)))
        self.assertEqual(teams, {str(t): "Team %d" % t for t in self.ids})

    def test_a_team_id_the_league_lacks_stops_the_run_before_any_roster(self):
        """Re-cutting eleven and dying on the twelfth leaves the directory half
        stale, and nothing downstream can tell which half"""
        p = self.fetch("roster", "161001", "999999")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("999999", p.stdout + p.stderr)
        self.assertEqual(self.rosters(), [])

    def test_the_file_it_says_it_wrote_is_the_file_it_wrote(self):
        """`wrote teams-2025-26.json` says nothing about where, and the answer
        is never the directory the caller is standing in"""
        p = self.fetch("teams")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        wrote = [os.path.realpath(l.split(None, 1)[1])
                 for l in p.stdout.splitlines() if l.startswith("wrote ")]
        self.assertEqual(wrote, [os.path.realpath(os.path.join(
            self.dir, "teams-%s.json" % fetch_data.SEASON_TAG))])
        self.assertTrue(os.path.exists(wrote[0]))
        self.assertEqual(self.rosters(), [], "`teams` re-cut a roster")


class OutputIsSelfDescribing(unittest.TestCase):
    """A caller reads these tables in a terminal, not next to findings.md. A
    figure whose units live in another file is a figure he has to go and look
    up -- and the commonest way that ends is that he does not"""

    def test_every_report_opens_with_the_units_its_numbers_are_in(self):
        """`+2.01` is per 20-matchup regular season. Nothing on stdout said so,
        so it read equally well as per week, per matchup or per game -- and a
        legend that arrives BELOW the table it explains is one a reader who
        scrolled to his row never sees"""
        for name in sorted(sim.REPORTS):
            with self.subTest(report=name):
                raw = render(name)
                legend = reports.OWN_UNITS.get(name, reports.UNITS)
                self.assertTrue(raw.startswith(legend),
                                "%s opens with:\n%s" % (name, raw[:200]))
                if "win" not in one_line(raw).lower():
                    continue
                self.assertRegex(one_line(raw), r"%d-matchup regular season"
                                 % sim.REAL_MATCHUPS)

    def test_the_consolidation_ladder_converts_at_the_rate_it_prints(self):
        """`wins` is `dPF` through the PF-per-win on line 1, and the note above
        the table says so. It is the one place these tables cross from points
        into wins, and every scenario in `trades` is quoted out of this column"""
        out = render("scenarios")
        pf_per_win = float(re.search(r"1 win = (\d+) PF", out).group(1))
        rows = re.findall(r"([-+]\d+) +\d+\.\d% +([-+]\d+\.\d\d)$", out, re.M)
        self.assertGreater(len(rows), 10, out)
        for dpf, wins in rows:
            self.assertAlmostEqual(float(wins), float(dpf) / pf_per_win,
                                   delta=0.01, msg=out)

    def test_the_formula_error_is_signed_the_way_its_own_note_says(self):
        """`+ means the formula pays him more than the sim does`. The direction
        is what a reader books -- reversed, the bodies the shorthand overpays
        read as the ones it underpays, and he sorts on it backwards"""
        out = render("formula")
        rows = re.findall(r"([-+]\d+\.\d\d) +([-+]\d+\.\d\d) +([-+]\d+)% +"
                          r"([-+]\d+)%$", out, re.M)
        self.assertGreaterEqual(len(rows), 10, out)
        for sim_w, one_r, err, _ in rows:
            self.assertEqual(float(err) > 0, float(one_r) > float(sim_w),
                             "%s vs %s reads as err %s%%" % (one_r, sim_w, err))

    def test_the_per_player_table_names_its_columns(self):
        """Seven columns, no header row: `+-0.001` and a trailing `48.5` next to
        a name reads as two more scores"""
        out = render("players")
        head, = [l for l in out.splitlines() if l.strip().startswith("player")]
        for col in ("rate", "gp", "elig", "wins", "sd", "next", "flags"):
            self.assertIn(col, head)

    def test_the_per_player_header_sits_over_the_numbers_it_names(self):
        """Naming the columns is only half of it -- a header shifted off its own
        data reads `sd` over the wins figure, and the reader books the wrong
        column"""
        lines = render("players").splitlines()
        head, = [l for l in lines if l.strip().startswith("player")]
        row = lines[lines.index(head) + 1]
        at = 0
        for col, pattern in (("wins", r"[-+]\d+\.\d{2}"),
                             ("sd", r"\+-\d+\.\d{3}"),
                             ("next", r"inf|\d+\.\d")):
            with self.subTest(column=col):
                at = re.compile(pattern).search(row, at).end()
                self.assertEqual(re.search(r"%s\b" % col, head).end(), at,
                                 "`%s` does not end over its own column:\n%s\n%s"
                                 % (col, head, row))


class OptimalLineup(unittest.TestCase):
    """"Lineups are set optimally every night" is the premise under every PF
    figure here, and what lets the README call absolute PF an UPPER bound.
    Greedy placement with Kuhn augmentation is only exact because capacities
    are 1 and players are added in descending value, and a matching that misses
    a swap loses points on exactly the crowded nights the study is about"""

    def best_possible(self, avail):
        """The optimum by dynamic programming over subsets of the 9 slots, a
        different algorithm from the augmenting placement `lineup` uses"""
        dp = {0: 0.0}
        for val, elig, _ in avail:
            nxt = dict(dp)
            for mask, total in dp.items():
                for si, (_, slot) in enumerate(sim.SLOTS):
                    bit = 1 << si
                    if mask & bit or not elig & slot:
                        continue
                    if total + val > nxt.get(mask | bit, -1.0):
                        nxt[mask | bit] = total + val
            dp = nxt
        return max(dp.values())

    def test_no_other_legal_lineup_scores_more(self):
        """On real nights, not toy ones. The bodies and eligibilities are drawn
        from the 38-man roster, at the sizes `nights` says the cap actually
        bites on"""
        roster = sim.basis()
        rng = random.Random(3)
        for case in range(30):
            up = rng.sample(roster, rng.randint(4, 18))
            avail = [(p["avg"], set(p["elig"]), i) for i, p in enumerate(up)]
            with self.subTest(case=case, n=len(up)):
                total, filled, who = sim.lineup(avail)
                self.assertEqual(len(who), len(set(who)))
                self.assertEqual(filled, len(who))
                self.assertLessEqual(filled, len(sim.SLOTS))
                self.assertAlmostEqual(total, self.best_possible(avail), places=6)

    def test_a_body_with_no_legal_slot_left_does_not_start(self):
        """The positional half of the 9-slot cap. A pure center reaches C and
        the two ANY slots and no further, so the 4th-best center on the roster
        scores nothing however good he is"""
        centers = [(float(40 - i), {"C"}, i) for i in range(12)]
        total, filled, who = sim.lineup(centers)
        self.assertEqual(filled, sim.group_slots(("C",)))
        self.assertEqual(sorted(who), [0, 1, 2])
        self.assertEqual(total, 40 + 39 + 38)


class Schedule(unittest.TestCase):
    """Every conclusion is a count of slot-nights, so a phantom game is a
    phantom night of value"""

    def test_every_team_plays_82_games(self):
        played = collections.Counter()
        for _, tms in sim.NIGHTS:
            for t in tms:
                played[t] += 1
        # the NBA Cup final is an 83rd game for its two participants
        self.assertEqual(sorted(collections.Counter(played.values()).items()),
                         [(82, 28), (83, 2)])


class FantasyCalendar(unittest.TestCase):
    """Weekly scores are the unit a matchup is won in, so how nights bucket
    into periods is not cosmetic"""

    def test_games_per_period_matches_the_real_spread(self):
        """Real periods carry 28-56 NBA games. An even split of nights across
        periods implies ~49-56 and erases most of the weekly variance the sim
        exists to explain"""
        games = collections.Counter()
        for (_, tms), w in zip(sim.NIGHTS, sim.WEEK_OF):
            if w is not None:
                games[w] += len(tms) // 2
        self.assertEqual((min(games.values()), max(games.values())), (28, 56))


class NightToPeriodMapping(unittest.TestCase):
    """A night reaches a period two independent ways: the points column buckets
    it through the scoring calendar's `WEEK_OF`, and the games count comes off
    `period_nights`, a date-range test against the period. Let those drift and
    the two columns of the same row describe different weeks"""

    def test_the_scoring_nights_are_exactly_the_scored_periods_nights_in_order(self):
        """Same nights AND same order, since position `w` in the points column
        is the `w`th scored period. A scoring calendar that carried an extra
        night, or ran them in another order, would still total the same season
        """
        self.assertEqual([n for i in sim.SCORED for n in sim.period_nights(i)],
                         list(sim.SCORING_NIGHTS))

    def test_every_night_buckets_into_the_period_it_falls_inside(self):
        """The off-by-one guard. A shift of one leaves the season total alone
        and moves nearly every entry of the column"""
        for w, i in enumerate(sim.SCORED):
            for n in sim.period_nights(i):
                with self.subTest(period=sim.PERIODS[i]["ordinal"],
                                  night=sim.NIGHTS[n][0]):
                    self.assertEqual(sim.WEEK_OF[n], w)

    def test_no_night_falls_inside_two_periods_at_once(self):
        """Periods are read off start/end dates, so an inclusive end meeting an
        inclusive start double-counts that night's games in both"""
        seen = collections.Counter(n for i in range(len(sim.PERIODS))
                                   for n in sim.period_nights(i))
        self.assertTrue(seen)
        self.assertEqual(max(seen.values()), 1,
                         sorted(n for n, c in seen.items() if c > 1))

    def test_bracket_round_one_is_the_only_night_the_two_calendars_share(self):
        """Period 20 is both the last scored period and R1, so the standings
        basis and the bracket basis overlap there and NOWHERE else. An overlap
        that grew would score playoff-only nights into the standings; one that
        vanished would leave R1 out of the basis its own seeding is cut from"""
        self.assertEqual(set(sim.SCORED_CAL.nights) & set(sim.BRACKET_CAL.nights),
                         set(sim.BRACKET_NIGHTS[0]))


class GameCountsAgree(unittest.TestCase):
    """A bracket period's size is printed as the games on its nights and drives
    every per-player `W` column as that team's games in the round. The two are
    counted over separately built night lists, and a window that slipped a
    night on one side prices bodies off a schedule the printed table never
    showed"""

    def test_a_bracket_round_is_the_same_window_counted_per_night_and_per_team(self):
        for w, i in enumerate(sim.BRACKET):
            with self.subTest(period=sim.PERIODS[i]["ordinal"]):
                self.assertEqual(2 * sim.period_games(i),
                                 sum(sim.bracket_games(t)[w]
                                     for t in sim.NBA_TEAMS))


def light_nights_per_team():
    """{team: the light nights it plays}, the table `schedules` prints and the
    quantity every coverage bound is read off. Derived rather than a literal,
    since the deepest and emptiest schedules move with the calendar every
    season"""
    return {t: len(sim.team_light_nights(t)) for t in sim.NBA_TEAMS}


class LightNights(unittest.TestCase):
    """The nights the 9-slot cap binds on, and the only nights a schedule
    choice can pay on. The fantasy season ENDS before the NBA's, so a team
    whose light nights sit in April has none that count"""

    def test_light_nights_outside_the_scored_periods_are_dropped(self):
        whole = [i for i, (_, tms) in enumerate(sim.NIGHTS)
                 if len(tms) // 2 <= sim.LIGHT_GAMES]
        self.assertLess(len(sim.light_nights()), len(whole))
        self.assertTrue(set(sim.light_nights()) <= set(sim.SCORING_NIGHTS))

    def test_every_team_spelling_in_the_feed_finds_a_real_schedule(self):
        """The roster feed and the NBA schedule spell teams differently,
        SAS/NYK/UTA against SA/NY/UTAH, so all 30 resolve only through
        `FF2ESPN` and a rename on either side breaks the join. Driven off the
        committed roster files rather than a hand list, because the vocabulary
        is the feed's to change"""
        feed = set()
        for path in committed_rosters():
            feed |= {r["tm"] for r in json.loads(read_text(path))}
        feed -= {sim.UNSIGNED}          # no schedule to resolve
        self.assertEqual(len(feed), 30, sorted(feed))
        self.assertEqual({sim.team_light_nights(t) for t in feed},
                         {sim.team_light_nights(t) for t in sim.NBA_TEAMS})

    def test_a_team_is_counted_on_the_nights_it_actually_plays(self):
        for tm in ("LAC", "CLE", "BKN"):
            with self.subTest(tm=tm):
                self.assertEqual(
                    sim.team_light_nights(tm),
                    frozenset(i for i in sim.light_nights()
                              if tm in sim.NIGHTS[i][1]))


class Coverage(unittest.TestCase):
    """`Eval Definitions §Where our format pulls off consensus` 5. What pays is
    the count of DISTINCT light nights the roster reaches, never a body's own
    night count, and the two diverge by 7x on a stack"""

    def test_seven_bodies_on_one_team_only_get_you_that_teams_nights(self):
        deepest = max(light_nights_per_team().values())
        self.assertEqual(deepest, 12)
        self.assertEqual(sim.coverage(["LAC"] * 7), 12)

    def test_spreading_the_same_seven_out_covers_way_more_nights(self):
        spread = sim.coverage(["OKC", "LAC", "UTAH", "SA", "NY", "MIN", "BOS"])
        self.assertGreater(spread, 2 * sim.coverage(["LAC"] * 7))
        self.assertLessEqual(spread, len(sim.light_nights()))


class CoveragePicks(unittest.TestCase):
    """The selection rule every steering figure is cut on, stated once so the
    ladder and the headline cannot be two different rules. A greedy ladder ENDS
    at its own best-7 by construction, since rung k is the best-k"""

    def test_the_first_k_picks_are_always_the_best_k(self):
        picks = sim.coverage_picks(7)
        for k in range(1, 8):
            with self.subTest(k=k):
                self.assertEqual(sim.coverage_picks(k), picks[:k])

    def test_coverage_saturates_after_about_three_picks(self):
        """The section's whole point. Three picks buy most of it and the last
        buy nothing, and if the rule did not saturate the ladder would be a
        straight line and "steer the first few" would be wrong advice"""
        cov = [sim.coverage(sim.coverage_picks(k)) for k in range(1, 8)]
        self.assertEqual(cov, sorted(cov))
        self.assertEqual(cov[-1], cov[-2], "the 7th pick still bought a night")
        self.assertGreater(cov[2], 0.8 * cov[-1])

    def test_the_worst_seven_all_pile_onto_the_emptiest_schedule(self):
        worst = sim.coverage_picks(7, best=False)
        self.assertEqual(len(set(worst)), 1)
        self.assertEqual(sim.coverage(worst),
                         min(light_nights_per_team().values()))

    def test_only_the_teams_actually_on_offer_can_be_picked(self):
        """An auction shows you a slice of the league, not all 30, so the
        realistic figure is the best 7 of what is on the block and a rule that
        quietly reaches outside it prices a draft nobody ran"""
        offer = ("BKN", "CHI", "POR", "ATL", "DET")
        self.assertTrue(set(sim.coverage_picks(7, teams=offer)) <= set(offer))


class SchedulesReport(unittest.TestCase):
    """Every win figure README `Light-night coverage` quotes comes off this
    report, and the same choice gets printed three times, ladder, headline and
    coverage row, so the hazard is the three disagreeing.

    Rendered once for the class, since `schedules` sweeps 30 schedules at 11
    rates and is the priciest report here even at four trials"""

    @classmethod
    def setUpClass(cls):
        cls.out = render("schedules")

    def headline(self):
        """The best-7 win figure, the one number README quotes and the one
        three separate places on this page have to agree on"""
        m = re.search(r"best 7, all 30 teams on offer\s*:\s*([-+][\d.]+)",
                      self.out)
        self.assertIsNotNone(m, self.out)
        return float(m.group(1))

    def ladder(self):
        """The cumulative +wins row, rung by rung"""
        rungs = re.search(r"cumulative \+wins(.*)", self.out).group(1).split()
        self.assertEqual(len(rungs), 7, self.out)
        return [float(x) for x in rungs]

    def test_the_ladder_total_is_the_same_number_as_the_headline(self):
        """The ladder total and the best-7 headline are the same choice, so a
        reader given two figures has no way to tell which one to act on"""
        self.assertEqual(self.ladder()[-1], self.headline(), self.out)

    def test_the_stacked_seven_row_is_seven_times_the_deepest_schedule(self):
        """Seven bodies on one NBA team cannot sum past 7x the deepest light-
        night schedule. The report prints the sum and the coverage side by
        side, so the gap between them has to be the finding rather than an
        arithmetic error"""
        summed, covered = re.search(
            r"seven on \w+\s*:\s*(\d+) body-nights summed, (\d+) distinct",
            self.out).groups()
        deepest = max(light_nights_per_team().values())
        self.assertEqual(int(summed), 7 * deepest)
        self.assertEqual(int(covered), deepest)
        got = float(re.search(r"distinct, ([-+][\d.]+) wins", self.out).group(1))
        self.assertIn("lands %s not caring" % ("BELOW" if got < 0 else "above"),
                      self.out)

    def per_team_counts(self):
        """The printed light-nights-per-team table, as {team: count}"""
        listed = {}
        for n, tms in re.findall(r"^ +(\d+) +((?:[A-Z]{2,4} ?)+)$", self.out, re.M):
            for tm in tms.split():
                listed[tm] = int(n)
        return listed

    def test_every_team_is_listed_under_its_own_light_night_count(self):
        """The one table here a reader ACTS on, "prefer a body from these
        teams", and the one README republishes verbatim. A team dropped from
        it, or filed under a neighbouring count, sends the auction after the
        wrong schedule and no win figure above would look any different"""
        self.assertEqual(self.per_team_counts(), light_nights_per_team())

    def per_body_rows(self):
        """The 30-schedule sweep, one row per body grade (rate, meanPF, sdPF,
        sd wins, sdRate, spanRate)"""
        rows = [tuple(map(float, m)) for m in re.findall(
            r"^ +(\d+) +(\d+) +([\d.]+) +([\d.]+) +([\d.]+) +([\d.]+)$",
            self.out, re.M)]
        self.assertTrue(rows, self.out)
        return rows

    def test_the_schedule_swing_converts_through_the_one_pf_per_win(self):
        """The only place the file converts a PF spread into the rate points a
        board prices in, and the whole tiebreak is denominated by it. A second
        PF to wins constant living here would quote the threshold in a currency
        no other number on the page uses, and every row would still look
        plausible"""
        for rate, _, sdpf, sdwins, _, _ in self.per_body_rows():
            with self.subTest(rate=rate):
                self.assertAlmostEqual(sdwins, sdpf / sim.PF_PER_WIN, delta=0.001)

    def test_the_schedule_spread_shrinks_as_the_body_gets_better(self):
        """The shape the section is sold on. The body's own value climbs far
        faster than the schedule spread under it, so the schedule matters most
        exactly where the body matters least, the auction tier"""
        rows = self.per_body_rows()
        self.assertEqual([r[1] for r in rows], sorted(r[1] for r in rows))
        self.assertGreater(rows[0][4], rows[-1][4] * 1.5)

    def test_the_sub_proportional_line_comes_off_its_own_table(self):
        """The line under the table quotes four of its numbers. If a re-cut
        ever makes the schedule spread grow WITH the body, this stops being
        sub-proportional and the whole "cheap tiebreak, never a price" framing
        goes with it"""
        rows = self.per_body_rows()
        body = rows[-1][1] / rows[0][1]
        swing = rows[-1][2] / rows[0][2]
        if body > swing:
            self.assertIn("SUB-PROPORTIONAL", self.out)
        else:
            self.assertNotIn("SUB-PROPORTIONAL", self.out)
        self.assertIn("the body grows %dx from rate %d to %d while the"
                      % (round(body), rows[0][0], rows[-1][0]), self.out)
        self.assertIn("schedule sd under it grows only %dx" % round(swing),
                      self.out)
        self.assertIn("%.1f rate points at %d and %.1f at %d"
                      % (rows[0][4], rows[0][0], rows[-1][4], rows[-1][0]),
                      self.out)

    def test_the_threshold_it_prints_comes_off_the_row_we_actually_bid_at(self):
        """The rule is spent at 8-14 FPts and nowhere else, and the exchange
        rate halves by rate 40, so a threshold quoted off the wrong row is ~2x
        wrong in the direction that overpays. It is the one number from this
        report that gets carried into a live acquisition"""
        rows = self.per_body_rows()
        thresh = re.search(r"so ~([\d.]+) rate points is the threshold",
                           self.out)
        self.assertIsNotNone(thresh, self.out)
        self.assertEqual(float(thresh.group(1)), round(rows[0][4], 1))
        self.assertLessEqual(rows[0][0], 8)

    def test_the_spread_seven_row_uses_the_same_seven_as_the_headline(self):
        """Third place the same choice gets printed, and the one sitting in a
        table beside a stack it is supposed to beat. A coverage row scoring its
        own private best-7 splits the headline in two again"""
        covered, wins = re.search(
            r"spread best 7\s*:\s*\d+ body-nights summed, (\d+) distinct, "
            r"([-+][\d.]+) wins", self.out).groups()
        self.assertEqual(float(wins), self.headline(), self.out)
        self.assertEqual(int(covered), sim.coverage(sim.coverage_picks(7)))

    def test_the_last_picks_verdict_matches_the_sigma_it_prints(self):
        """The figure a reader acts on, "stop steering after k". On a
        counterparty file the ladder can peak at seven, so whether the last
        pick bought anything is a comparison against its own paired sigma
        rather than a fixed sentence"""
        inc, se = re.search(r"buys ([-+][\d.]+) against a paired \+-([\d.]+)",
                            self.out).groups()
        self.assertIn("which is %s" % ("nothing measurable"
                                       if abs(float(inc)) < 2 * float(se)
                                       else "a REAL increment"), self.out)

    def test_the_picks_it_prints_are_the_ones_the_rule_actually_makes(self):
        """The rungs are only comparable because every one of them is the same
        greedy-on-coverage rule taken k deep (`CoveragePicks`), and README
        quotes the picks and the nights they reach as fact. A ladder on any
        other rule reads as a measurement of steering and is a measurement of
        something else"""
        picks = re.search(r"picks: (.+)", self.out).group(1).split()
        self.assertEqual(picks, list(sim.coverage_picks(7)), self.out)
        cover = re.search(r"steered picks cover(.*)", self.out).group(1).split()
        self.assertEqual([int(c) for c in cover],
                         [sim.coverage(picks[:k]) for k in range(1, 8)])

    def test_the_percentages_it_quotes_match_its_own_ladder(self):
        """The only sentence here telling a reader where to stop paying
        attention, and it is a ratio of two numbers on the row above it. The
        ladder is re-cut every season and the sentence has to move with it"""
        cum = self.ladder()
        peak = max(cum)
        got = re.search(r"(\d+) picks buy (\d+)% of the peak and (\d+) buy (\d+)%",
                        self.out)
        self.assertIsNotNone(got, self.out)
        a, sa, b, sb = (int(x) for x in got.groups())
        self.assertEqual(sa, round(100 * cum[a - 1] / peak))
        self.assertEqual(sb, round(100 * cum[b - 1] / peak))

    def test_a_15_team_offer_is_worth_less_than_having_all_30(self):
        """Fewer teams on the block is strictly less to choose from. Printing
        the two the other way round, or reading the wrong one into an eval,
        doubles the case for a rule already sitting at the 0.1-win floor"""
        real = float(re.search(r"random 15-team offer\s*:\s*([-+][\d.]+)",
                               self.out).group(1))
        full = self.headline()
        worst = float(re.search(r"worst 7 .*:\s*([-+][\d.]+)",
                                self.out).group(1))
        self.assertLess(real, full, self.out)
        self.assertLess(worst, real, self.out)
        self.assertGreater(full - worst, 4 * (full - real))

    def test_the_coverage_call_comes_off_the_two_r2s_it_prints(self):
        """"Coverage, not a summed night count" is the section's central claim
        and this report is the only thing that measures it, so the verdict is
        DERIVED from the two R2s and a re-cut that flips them flips the
        sentence too"""
        cov = float(re.search(r"nights COVERED.*R2 ([\d.]+)", self.out).group(1))
        summed = float(re.search(r"nights SUMMED.*R2 ([\d.]+)", self.out).group(1))
        self.assertIn("Coverage %s that comparison"
                      % ("wins" if cov > summed else "LOSES"), self.out)


class AuctionSteering(unittest.TestCase):
    """Sept '26 fills 10 slots, 3 rookie picks and a 7-man FA auction (`league-
    info`). Only the auction seven are a schedule we CHOOSE, so a steering
    figure that quietly re-points any of the other 31 prices a choice nobody
    has"""

    def test_steering_moves_the_auction_seven_and_nobody_else(self):
        """Two targets, so a body that already sat on the target team cannot
        pass for one that stayed put. The rookie grades carry a schedule too,
        so a rule reaching one body further would price a pick we do not get to
        aim, and would still print seven steered bodies"""
        full = sim.basis()
        a, b = sim.steer(full, ["BKN"] * 7), sim.steer(full, ["CHI"] * 7)
        moved = [p["n"] for p, x, y in zip(full, a, b)
                 if not p["tm"] == x["tm"] == y["tm"]]
        self.assertEqual(len(moved), 7)
        owned = {p["n"] for p in sim.our_roster()}
        self.assertFalse(owned & set(moved), "steered a player we already own")
        auction = [p["n"] for p in sim.EXPANSION if p["n"].startswith("FA")]
        self.assertEqual(moved, auction, "steered something we do not bid on")

    def test_a_steered_body_is_the_same_body_on_a_different_schedule(self):
        """The whole comparison is schedule against schedule at matched grade,
        so a steered body that also picked up a rate or a slot group would book
        those as the schedule's doing"""
        full = sim.basis()
        for a, b in zip(full, sim.steer(full, ["BKN"] * 7)):
            self.assertEqual((a["n"], a["avg"], a["gp"], a["elig"]),
                             (b["n"], b["avg"], b["gp"], b["elig"]))

    def test_a_target_list_that_is_not_seven_teams_fails(self):
        """Seven is a league fact, not a loop bound. Silently steering the
        first three of a seven-team list answers a different question and still
        prints a win figure"""
        full = sim.basis()
        with self.assertRaises(ValueError):
            sim.steer(full, ["BKN", "LAC", "OKC"])

    def test_an_unsigned_body_covers_the_same_nights_the_sim_gives_him(self):
        """`team_nights` puts an unsigned body on SIM_TM rather than inventing
        him a calendar, and coverage cannot quietly disagree with it and call
        him a body that covers nothing"""
        self.assertEqual(sim.coverage([sim.UNSIGNED]),
                         sim.coverage([sim.SIM_TM]))


class CommonRandomNumbers(unittest.TestCase):
    def test_swapping_a_player_for_his_own_clone_changes_nothing(self):
        """A scenario must perturb only what it changes. Appending the incoming
        player rather than replacing in place shifts every later player's
        availability draw, which buries sub-0.1-win deltas in Monte-Carlo noise
        """
        full = sim.our_roster() + sim.EXPANSION
        clone = dict(full[0])
        same = sim.swap(full, [clone["n"]], [clone])
        self.assertEqual(sim.run(same, trials=8)["pf"], sim.run(full, trials=8)["pf"])

    def test_a_three_for_three_of_clones_changes_nothing_either(self):
        """A different path, and the one a real offer is priced on. With three
        bodies leaving and three arriving, a `swap` that appended the arrivals
        instead of seating them in the vacated slots re-orders everything below
        them and shifts every later draw, worth several tenths of a win against
        a joint-vs-summed gap of about one"""
        full = sim.basis()
        clones = [dict(p) for p in full[:3]]
        same = sim.swap(full, [p["n"] for p in clones], clones)
        self.assertEqual(sim.run(same, trials=8)["pf"], sim.run(full, trials=8)["pf"])


class AbsenceBlocks(unittest.TestCase):
    """`_availability` places IL blocks CIRCULARLY, so the onset scan has to be
    circular too. ~26% of player-seasons come out with both their first and
    last team-game night absent, and a left-to-right scan splits that one block
    in two, letting a single injury surprise you twice"""

    def test_a_block_that_wraps_the_end_of_the_season_is_one_block(self):
        # his team-game nights, absent for 50 then 10 and 20, so ONE block
        self.assertEqual(sim._onsets([10, 20, 30, 40, 50], {30, 40}), [50])

    def test_the_block_statistics_are_measured_on_the_roster_you_pass(self):
        """The lock-in correction is worth exactly the ratio of absence NIGHTS
        to absence BLOCKS, and no fixed pair of numbers describes both rosters,
        so it is measured live per roster"""
        small = sim.absence_blocks(sim.our_roster(), seeds=6)
        big = sim.absence_blocks(sim.our_roster() + sim.EXPANSION, seeds=6)
        self.assertGreater(big["nights"], small["nights"] + 100)
        self.assertGreater(small["mean_block"], 7.0)


class SurpriseScratches(unittest.TestCase):
    """A scratch can only surprise a lineup-setter on the FIRST night of an
    absence block, since after that he is on the public injury report. Drawing
    the surprise from every absence night instead makes the lock-in penalty
    ~10x too large"""

    def test_a_season_long_absence_can_only_surprise_you_once(self):
        """EXACTLY once, both ways. More than one is the whole season sampled
        as surprises, and none at all is the other half of the circular fix,
        since with nothing played there is no night before that he played and a
        scan needing one drops the opening night that IS the surprise"""
        glass = [dict(sim.star(45, 0, ("SF", "PF"), "LAL", "GLASS"), surprise=1.0)]
        for seed in (101, 202, 303):
            _, starts, pts, _ = sim.season(glass, seed=seed, bursty=True)
            self.assertEqual(starts["GLASS"], 1)
            self.assertEqual(pts["GLASS"], 0.0)      # started, scores nothing

    def test_a_lone_scattered_absence_is_still_a_surprise(self):
        # his one missed night is its own onset, and ~79% of NBA nights fall in
        # the scored periods, so over 20 seeds it lands in window ~16 times
        """Guard on the other side. A rest day IS the first night of its own
        block, so the correction must not suppress it, and a high-GP veteran
        resting scattered single games is the shape the lock-in costs the most
        """
        rester = [dict(sim.star(45, 81, ("SF", "PF"), "LAL", "REST"), surprise=1.0)]
        wasted = 0
        for seed in range(101, 121):
            _, starts, pts, _ = sim.season(rester, seed=seed, bursty=True)
            wasted += starts["REST"] - round(pts["REST"] / 45)
        self.assertGreaterEqual(wasted, 10)

    def test_a_small_surprise_rate_still_costs_something(self):
        """Each block has to be an INDEPENDENT draw. `round(q x blocks)`
        truncates to zero for every player with fewer than ~5 absence blocks,
        which is most of a roster, so a 10% rate silently becomes 0% and the
        corrected penalty reads as exactly nothing"""
        full = sim.our_roster() + sim.EXPANSION
        base = sim.run(full, trials=40, bursty=True)["pf"]
        risky = sim.run(full, trials=40, bursty=True, surprise=0.10)["pf"]
        self.assertLess(risky, base - 20)

    def test_a_scratch_you_started_costs_the_bench_body_who_would_have_played(self):
        """Lineups lock before tip, so the slot is spent, not freed. Ten bodies
        all on one NBA team and all eligible everywhere, so every night has one
        more body than the nine slots: starting the scratched man benches the
        10th, and what the season loses is HIS rate, not the scratched man's"""
        every = ("PG", "SG", "SF", "PF", "C")
        def deep(spare):
            return ([sim.star(50.0, 41, every, "MEM", "OUT")]
                    + [sim.star(40.0 - i, 82, every, "MEM", "B%d" % i)
                       for i in range(1, 9)]
                    + [sim.star(spare, 82, every, "MEM", "SPARE")])
        cost = {}
        for spare in (31.0, 10.0):
            r = deep(spare)
            cost[spare] = (sim.run(r, trials=3)["pf"]
                           - sim.run(r, trials=3, surprise=1.0)["pf"])
        self.assertGreater(cost[31.0], 0)
        self.assertAlmostEqual(cost[31.0] / 31.0, cost[10.0] / 10.0, places=6)

    def test_a_scratch_costs_nothing_when_there_is_nobody_to_bench(self):
        """The other half of the same claim, and the one that says the cost is
        the FOREGONE body rather than the scratched man's own points. Nine
        bodies for nine slots: whether he is started or known out, the same
        eight teammates play and the night scores the same"""
        every = ("PG", "SG", "SF", "PF", "C")
        thin = ([sim.star(50.0, 41, every, "MEM", "OUT")]
                + [sim.star(40.0 - i, 82, every, "MEM", "B%d" % i)
                   for i in range(1, 9)])
        self.assertEqual(sim.run(thin, trials=3, surprise=1.0)["pf"],
                         sim.run(thin, trials=3)["pf"])


class WeeklyPointsColumn(unittest.TestCase):
    """`wk` is the per-period points column a bracket opponent's level is
    measured from. A run that buckets a night into the wrong period is
    invisible in the season total and wrong everywhere the column is read"""

    def test_a_period_totals_its_own_nights_and_no_others(self):
        """An ironman on one NBA team scores his rate once per team game in the
        period, so every one of the 20 entries is pinned. Shift the buckets by
        one and `pf` is untouched while most of the column moves"""
        body = sim.star(30.0, 82, ("C",), "MEM", "IRON")
        out = sim.run([body], trials=2)
        played = set(sim.team_nights("MEM"))
        self.assertEqual(
            [round(x, 6) for x in out["wk"]],
            [round(30.0 * len(played & set(sim.period_nights(i))), 6)
             for i in sim.SCORED])


class AvailabilityIsSeasonLong(unittest.TestCase):
    """GP/82 is a season-long rate, drawn over the WHOLE season even when only
    the bracket weeks are scored. Restrict the draw to the scored window and
    every bracket column comes out systematically wrong"""

    def test_a_41_gp_body_scores_about_half_the_bracket_an_ironman_does(self):
        """Not zero and not full: the four bracket rounds are a sample of a
        season-long absence pattern, so a half-season body loses about half of
        them. Zero means the draw ran out before the bracket, full means it
        never ran on the rounds being scored"""
        iron = sim.run([sim.star(30.0, 82, ("C",), "MEM", "IRON")],
                       trials=60, cal=sim.BRACKET_CAL)
        half = sim.run([sim.star(30.0, 41, ("C",), "MEM", "HALF")],
                       trials=60, cal=sim.BRACKET_CAL)
        self.assertEqual(
            [round(x, 6) for x in iron["wk"]],
            [round(30.0 * g, 6) for g in sim.bracket_games("MEM")])
        self.assertAlmostEqual(sum(half["wk"]) / sum(iron["wk"]), 0.5, delta=0.06)


class DuplicateNames(unittest.TestCase):
    """`season` scores a night off a `{name: points}` built from the players
    available, so two bodies sharing a name collapse into one entry and the
    night's total counts whichever one the dict kept, twice. `star()` names
    every synthetic body the same by default, and the league also rosters two
    real Jaylin Williamses"""

    def test_two_bodies_sharing_a_name_score_as_two_bodies(self):
        roster = [sim.star(40, 82, ("SF", "PF"), "LAC", "TWIN"),
                  sim.star(10, 82, ("PG", "SG"), "LAC", "TWIN")]
        distinct = [dict(roster[0], n="A"), dict(roster[1], n="B")]
        self.assertAlmostEqual(sim.run(roster, trials=4)["pf"],
                               sim.run(distinct, trials=4)["pf"], places=6)

    def test_two_unnamed_bodies_in_one_deal_stay_two_distinct_bodies(self):
        """The documented multi-piece path, `swap(full, [a, b], [star(),
        star()])`, names neither incoming body. PF survives that, since it is
        keyed on the roster index, but everything a reader does with the deal
        afterwards does not, the two collapse into one `season` points row and
        moving either of them on reads as ambiguous"""
        full = sim.basis()
        deal = sim.swap(full, ["Jalen Suggs", "Coby White"],
                        [sim.star(45, 68, ("PG", "SG")), sim.star(12, 68, ("C",))])
        incoming = [p["n"] for p in deal if p["n"] not in {q["n"] for q in full}]
        self.assertEqual(len(set(incoming)), 2, incoming)
        pts = sim.season(deal, seed=101)[2]
        self.assertGreater(pts[incoming[0]], pts[incoming[1]])
        sim.swap(deal, [incoming[0]], [sim.star(30)])

    def test_trading_away_an_ambiguous_name_fails_instead_of_guessing(self):
        """Which of the two Jaylin Williamses left is not a question `swap` can
        answer, and the roster it returns is a different trade either way"""
        roster = [sim.star(40, 82, ("SF", "PF"), "LAC", "Jaylin Williams"),
                  sim.star(20, 82, ("C",), "OKC", "Jaylin Williams"),
                  sim.star(30, 82, ("PG", "SG"), "LAC", "Someone Else")]
        with self.assertRaises(KeyError):
            sim.swap(roster, ["Jaylin Williams"], [sim.star(45)])
        self.assertGreater(sim.run(roster, trials=2)["pf"], 0)


class PerPositionReplacement(unittest.TestCase):
    """`replacement` prints an `R` per slot group and the README calls the
    single-R error "a third of the formula's error". Pricing a center against a
    forward's 17.1 when his own group's is 20.5 is worth 0.07-0.09 wins cross-
    position, so the counterfactual has to be a body of the outgoing player's
    OWN group"""

    def test_a_player_is_priced_against_a_replacement_of_his_own_slot_group(self):
        full = sim.basis()
        with cheap_monte_carlo(40):
            groups = {g: sim.replacement(full, 68, e)[0]
                      for g, e in sim.GROUPS.items()}
            self.assertGreater(groups["center"], groups["forward"] + 1.0,
                               "this roster's center group is not the tight one")
            base = sim.run(full, seed0=101)

            def against(R, elig):
                return sim.wins(base, sim.run(
                    sim.swap(full, ["Jakob Poeltl"], [sim.star(R, 68, elig)]),
                    seed0=101))
            own = against(groups["center"], ("C",))
            forward = against(groups["forward"], ("SF", "PF"))
            got, = sim.player_wins(full, ["Jakob Poeltl"], blocks=1).values()
        self.assertAlmostEqual(got[0], own, delta=0.02)
        self.assertGreater(forward, own + 0.02, "the two counterfactuals agree, "
                           "so this roster cannot tell them apart")

    def test_the_table_states_the_replacement_rate_it_used_for_each_group(self):
        """The counterfactual is the whole meaning of the number (`Eval
        Definitions §Δw`), so a header naming one rate for a table priced on
        three is worse than no header, and naming three rates the rows were not
        priced against is worse still. The rates are deterministic given the
        seeds, so the header is checked against a re-fit rather than inspected
        for the words"""
        buf = io.StringIO()
        with cheap_monte_carlo(8):
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["players"]()
            fitted = sim.group_replacement(sim.basis())
        header = buf.getvalue()
        for g, R in fitted.items():
            with self.subTest(group=g):
                stated = re.search(r"%s (\d+\.\d)" % g, header)
                self.assertIsNotNone(stated, header)
                self.assertAlmostEqual(float(stated.group(1)), R, delta=0.05)


class FormulaCounterfactual(unittest.TestCase):
    """`formula` grades both formulas against a `sim` column, so that column
    has to use the same per-slot-group counterfactual `players` does. Measured
    against one 68-GP forward for every player, the per-position-R error it
    publishes is a residual against the wrong number, and the fix it recommends
    is scored against the bug it fixes"""

    ROW = re.compile(r"^  (\S.*?) +[\d.]+ +\d+ +([-+][\d.]+)", re.M)

    def test_the_sim_column_uses_the_same_counterfactual_the_players_report_does(self):
        full = sim.basis()
        buf = io.StringIO()
        with cheap_monte_carlo(8):
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["formula"]()
            rows = dict(self.ROW.findall(buf.getvalue()))
            elig = {p["n"]: p["elig"] for p in sim.our_roster()}
            name = next(n for n in rows
                        if sim.slot_group(elig[n]) != "forward")
            got, = sim.player_wins(full, [name], blocks=1,
                                   R=sim.group_replacement(full)).values()
        self.assertAlmostEqual(float(rows[name]), got[0], delta=0.01)


class PerPlayerWins(unittest.TestCase):
    """The top of `sim.py players` decides a rank the README then asserts off
    it. Those rows sit ~0.01 wins apart while a single block moves several
    times that between seeds, so the value has to be an average over blocks and
    it has to carry the sd a reader can test a gap against"""

    def test_two_independent_runs_land_far_inside_the_smallest_tradeable_gap(self):
        full = sim.basis()
        who = [p["n"] for p in sorted(sim.our_roster(),
                                      key=lambda p: -p["avg"])[:2]]
        with cheap_monte_carlo(40):
            R = sim.group_replacement(full)
        a = sim.player_wins(full, who, blocks=3, trials=40, seed0=101, R=R)
        b = sim.player_wins(full, who, blocks=3, trials=40, seed0=9001, R=R)
        for n in who:
            self.assertGreater(a[n][1], 0.0, "%s reports no uncertainty" % n)
            # An absolute bound on purpose. `3 x (sd_a + sd_b)` widens with the
            # instability it is meant to catch, and 0.06 sits well inside the
            # ~0.1 wins §sigma calls the smallest tradeable gap
            self.assertLess(abs(a[n][0] - b[n][0]), 0.06,
                            "%s: %s vs %s" % (n, a[n], b[n]))


class AdjacentRowSigma(unittest.TestCase):
    """`Eval Definitions §sigma` reads the ORDER of two adjacent rows off this
    column and states none below ~2. Every row is measured on the SAME seed
    blocks, which is what `swap`'s common random numbers buy, so the gap
    between two rows is a within-block quantity and combining the two sds as if
    independent runs up to 3x out in BOTH directions, which is the difference
    between an ordered pair and a tie"""

    ROW = re.compile(r"^ +(?P<n>\S.*?) +[\d.]+ +\d+ +\S+ "
                     r"+(?P<w>[-+][\d.]+) +\+-[\d.]+ +(?P<next>[-\d.]+|inf)?",
                     re.M)

    def test_the_gap_is_measured_on_the_blocks_the_two_rows_share(self):
        full = sim.basis()
        blocks = 3
        ours = sim.our_roster()
        with cheap_monte_carlo(8, blocks=blocks):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["players"]()
            w = sim.player_wins(full, [p["n"] for p in ours], blocks=blocks,
                                R=sim.group_replacement(full))
        rows = self.ROW.findall(buf.getvalue())
        self.assertEqual(len(rows), len(ours), rows)
        top, second = rows[0][0], rows[1][0]
        printed = float(rows[0][2])
        d = [a - b for a, b in zip(w[top][2], w[second][2])]
        paired = statistics.mean(d) / (statistics.stdev(d) / math.sqrt(len(d)))
        independent = (w[top][0] - w[second][0]) / math.sqrt(
            (w[top][1] ** 2 + w[second][1] ** 2) / blocks)
        self.assertAlmostEqual(printed, paired, delta=0.15)
        self.assertGreater(abs(printed - independent), 0.5,
                           "the two formulas agree on this pair, so it cannot "
                           "tell them apart -- pick another")


class IncomingWins(unittest.TestCase):
    """`Eval Definitions §Columns` wants a `Δw ours` for every player on a
    counterparty's roster. `--roster their.json players` prices them on THEIR
    roster, which is `Δw theirs`, a different column the same file forbids
    sorting on, so without this the counterparty half of every eval is 28 hand-
    typed `swap` calls with the counterfactual retyped each time"""

    def test_acquiring_a_player_is_worth_what_losing_him_costs(self):
        """The mirror, and the reason this belongs beside `player_wins` rather
        than beside a hand-written swap. Same counterfactual, a replacement
        body of his own slot group, so the two columns are comparable.

        Both sides padded back to the SAME 38, since the mirror only holds at a
        common body count (§Δw), and a gain priced one body deeper than the
        loss it mirrors is the depth mismatch this pair exists to catch"""
        full = sim.basis()
        n = "Cade Cunningham"
        row = next(p for p in sim.our_roster() if p["n"] == n)
        without = sim.pad([p for p in full if p["n"] != n], len(full))
        with cheap_monte_carlo(60):
            R = sim.group_replacement(full)
            lost, = sim.player_wins(full, [n], blocks=1, R=R).values()
            gained, = sim.incoming_wins(without, [row], blocks=1, R=R).values()
        self.assertEqual(len(without), len(full))
        self.assertGreater(lost[0], 1.0, "pick a player worth something")
        self.assertAlmostEqual(gained[0], lost[0], delta=0.15)

    def test_an_arrival_is_priced_at_the_same_38_bodies_a_departure_is(self):
        """`Eval Definitions §Δw` compares rosters only at a COMMON body count.
        `player_wins` prices a departure at 38, `swap` replacing in place and
        refusing a 39th body outright, so pricing an arrival AS the 39th costs
        the marginal body.

        The count is the assertion because the win difference is ~0.01 here,
        under the noise. What is wrong is the basis, not the digit"""
        full = sim.basis()
        row = max(sim.our_roster(THEIR_ROSTER), key=season_value)
        with cheap_monte_carlo(4):
            R = sim.group_replacement(full)
            with recorded_rosters(trials=4) as seen:
                sim.incoming_wins(full, [row], blocks=1, R=R)
        self.assertEqual({len(names) for names in seen}, {len(full)})

    def test_the_roster_an_arrival_joins_is_the_one_the_recipe_re_pads(self):
        """§Columns' recipe is "add him to our roster file, re-run", and at 38
        that costs a PADDED slot, our real bodies re-padded one shallower and
        him on the end. Nothing else names a body it is defensible to drop, so
        any other room prices him against a team we could not field.

        The room is the assertion because the win difference between two
        bottom-grade rooms is under the noise. What is wrong when this breaks
        is which team the column describes, not the digit.

        `R` is passed a couple of points apart across groups because that is
        the shape every real fit has (`group_fits`), and a flat one hides this.
        Rank the pads by `(rate - R) * gp` and the group spread alone decides
        which of three near-identical bottom bodies loses its slot"""
        full = sim.basis()
        recipe = [p["n"] for p in sim.pad(sim.our_roster(), len(full) - 1)]
        R = {"guard": 18.0, "forward": 17.0, "center": 20.0}
        with recorded_rosters() as seen:
            sim.incoming_wins(full, [sim.star(40.0, 68, ("SF", "PF"), n="IN")],
                              blocks=1, trials=2, R=R)
        priced = [ns for ns in seen if {"IN", "REPL"} & set(ns)]
        self.assertTrue(priced)
        for names in priced:
            self.assertEqual([n for n in names if n not in ("IN", "REPL")],
                             recipe)

    def test_a_real_body_keeps_his_slot_however_cheap_he_scores(self):
        """The slot spent is an INVENTED one, so no roster file loses a player
        to it. Ranking every body by `(rate - R) * gp` and evicting the minimum
        instead reads the line below `R`, where `replacement` says it is not an
        ordering at all, and on five of the twelve league files the body it
        picks is a real player"""
        full = sim.basis()
        roster = [dict(p) for p in full[:-1]]
        roster.insert(3, sim.star(1.0, 82, ("PG", "SG"), n="SCRUB"))
        with recorded_rosters() as seen:
            sim.incoming_wins(roster, [sim.star(40.0, 68, ("SF", "PF"), n="IN")],
                              blocks=1, trials=2, R=flat_R())
        priced = [set(ns) for ns in seen if {"IN", "REPL"} & set(ns)]
        self.assertTrue(priced)
        for names in priced:
            self.assertEqual(len(names), len(roster))
            self.assertIn("SCRUB", names,
                          "a body off the roster file paid for the arrival")
            self.assertLess(len(names & roster_mod.PAD_NAMES),
                            len(set(p["n"] for p in roster)
                                & roster_mod.PAD_NAMES))

    def test_a_roster_with_nothing_padded_is_refused_rather_than_thinned(self):
        """From Sept '26 the 38 are all real and the recipe runs out of
        anything to spend, so somebody we field has to go. Which one is the
        caller's call, the same as `swap` says for that decision on the way
        out, and the alternatives sit a rate point apart on a line
        `replacement` says does not rank, so a default here is a coin flip that
        prints as a measurement"""
        full = [dict(p, n="Real %d" % i) for i, p in enumerate(sim.basis())]
        with self.assertRaises(ValueError) as e:
            sim.incoming_wins(full, [sim.star(40.0, 68, ("C",), n="IN")],
                              blocks=1, trials=2,
                              R=flat_R())
        self.assertIn("38", str(e.exception))

    def test_every_player_on_a_counterparty_file_is_priced_at_once(self):
        """"Never a shortlist, either side" (`Eval Definitions §Δw`), since a
        blank reads as zero. One call, one row per body on the file"""
        theirs = sim.our_roster(THEIR_ROSTER)
        with cheap_monte_carlo(20):
            w = sim.incoming_wins(sim.basis(), theirs, blocks=1)
        self.assertEqual(sorted(w), sorted(p["n"] for p in theirs))
        best = max(theirs, key=season_value)
        self.assertGreater(w[best["n"]][0], 0.3, best["n"])

    def test_a_name_our_own_roster_already_carries_is_still_priced_as_himself(self):
        """`Δw ours` seats the arrival on OUR roster, so a name we already hold
        is a collision this column cannot avoid, and the committed files
        collide today. The result is keyed by name either way, so a collision
        never shows up as a missing row, it shows up as a number belonging to
        the wrong body, under the right name, on the column a buy decision
        reads"""
        full = sim.basis()
        theirs = max(sim.our_roster(THEIR_ROSTER), key=season_value)
        ours = full[0]["n"]
        R = flat_R()
        namesake = sim.incoming_wins(full, [dict(theirs, n=ours)], blocks=1,
                                     trials=30, R=R)
        alone = sim.incoming_wins(full, [dict(theirs, n="A NAME NOBODY HOLDS")],
                                  blocks=1, trials=30, R=R)
        self.assertGreater(alone["A NAME NOBODY HOLDS"][0], 0.3, theirs["n"])
        self.assertAlmostEqual(namesake[ours][0], alone["A NAME NOBODY HOLDS"][0],
                               places=9)

    def test_two_arrivals_of_one_name_are_refused_rather_than_priced_as_one(self):
        """The league rosters two Jaylin Williamses, so one trade puts both on
        a file this column is asked to price. Keyed by NAME, the second row
        overwrites the first, which is worse than the blank §Δw forbids, since
        a blank reads as zero and this reads as measured. `swap` refuses
        exactly this ambiguity on the way out"""
        both = [sim.star(45.0, 70, ("C",), n="Jaylin Williams"),
                sim.star(12.0, 40, ("PG", "SG"), n="Jaylin Williams")]
        with self.assertRaises(ValueError) as e:
            sim.incoming_wins(sim.basis(), both, blocks=1, trials=2)
        self.assertIn("Jaylin Williams", str(e.exception))


class Thin(unittest.TestCase):
    def test_thinning_to_the_roster_you_already_have_measures_the_same_thing(self):
        """Roster ORDER drives the rng draw order, so a `thin` that sorted
        makes `thin(full, 38)` a different measurement from `full` itself,
        which is how three values of replacement level come to circulate for
        one roster"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            self.assertEqual(sim.replacement(sim.thin(full, len(full)))[0],
                             sim.replacement(full)[0])

    def test_a_live_counterparty_file_is_nowhere_near_our_padded_r(self):
        """`R` is the x-intercept of value in rate, so it moves with the body
        COUNT by construction: ~17 on our padded 38 against ~11 on a live
        27-man file. That gap is why `thin` takes the roster's own"""
        with cheap_monte_carlo(20):
            self.assertLess(sim.replacement(sim.our_roster(THEIR_ROSTER))[0],
                            14.0)

    def test_thinning_at_a_stale_r_keeps_a_different_set_of_bodies(self):
        """Six rate points out does not merely relabel the order -- it prefers
        rate to games where the roster's own level prefers games, and keeps
        other bodies.

        BUILT, not read off a roster file. Whether two R's happen to order one
        real 27-man file differently is a fact about that week's transactions,
        and this test went green on a trade"""
        grinders = [sim.star(15.0, gp=82, elig=("SF", "PF"), n="GRIND%d" % i)
                    for i in range(3)]
        scorers = [sim.star(30.0, gp=30, elig=("SF", "PF"), n="SCORE%d" % i)
                   for i in range(3)]
        roster = [p for pair in zip(grinders, scorers) for p in pair]
        # (15-5)*82 = 820 against (30-5)*30 = 750, and at R=12 it is 246
        # against 540 -- the same six bodies, ranked the other way up
        self.assertEqual({p["n"] for p in sim.thin(roster, 3, R=5.0)},
                         {"GRIND0", "GRIND1", "GRIND2"})
        self.assertEqual({p["n"] for p in sim.thin(roster, 3, R=12.0)},
                         {"SCORE0", "SCORE1", "SCORE2"})


class Pad(unittest.TestCase):
    """R and WINS compare across teams only at a COMMON body count, and no two
    live rosters have one. Measured on live bodies a counterparty's R lands
    near 23 against ours at 16, so every player on his roster reads as cheaper
    than one of ours"""

    def test_the_real_bodies_survive_padding_in_their_own_order(self):
        their = sim.our_roster(THEIR_ROSTER)
        padded = sim.pad(their, 38)
        self.assertEqual(len(padded), 38)
        self.assertEqual([p["n"] for p in padded[:len(their)]],
                         [p["n"] for p in their])
        self.assertEqual(len({p["n"] for p in padded}), 38)  # names index the rng

    def test_every_report_measures_a_counterparty_at_the_common_count(self):
        """`+ EXPANSION` is 10 BODIES, not a body count, so a 38-man baseline
        built that way measures a 26-man roster at 36 and reports his R, break-
        evens and per-player wins off that"""
        self.assertEqual(len(sim.basis(THEIR_ROSTER)), 38)
        self.assertEqual(len(sim.basis()), 38)

    def test_padding_our_28_is_the_38_man_basis_every_table_is_measured_on(self):
        """Pinning test, not a cycle. Every 38-man figure in the README is
        measured on `our_roster() + EXPANSION` and the counterparty recipe says
        `pad`, so if those two stop being the same measurement one of the two
        bases is wrong and the README's cross-team comparisons go with it"""
        self.assertEqual(
            sim.run(sim.pad(sim.our_roster(), 38), trials=8)["pf"],
            sim.run(sim.our_roster() + sim.EXPANSION, trials=8)["pf"])

    def test_padding_to_the_count_you_already_have_measures_the_same_roster(self):
        """Same reason `thin` preserves order. Roster order drives the rng draw
        order, so a pad that reordered would make the padded and unpadded
        measurements incomparable, which is the thing it exists to fix"""
        their = sim.our_roster(THEIR_ROSTER)
        self.assertEqual(sim.run(sim.pad(their, len(their)), trials=8)["pf"],
                         sim.run(their, trials=8)["pf"])


class Backfill(unittest.TestCase):
    def test_a_richer_backfill_grade_lowers_the_breakeven(self):
        """What the outgoing bodies 2..N are refunded at is an ASSUMPTION, not
        a fact, and every break-even in this study rides on it, so it has to be
        an argument for the bracket to be reportable"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            thin_pool = sim.breakeven(full, THREE_OUT,
                                      dead={"tm": "MIA", "avg": 6.0, "gp": 40,
                                            "elig": ["PG", "SG"]})
            deep_pool = sim.breakeven(full, THREE_OUT,
                                      dead={"tm": "MIA", "avg": 14.0, "gp": 55,
                                            "elig": ["PG", "SG"]})
        self.assertLess(deep_pool, thin_pool)


class SwapNames(unittest.TestCase):
    def test_taking_back_more_bodies_than_you_send_fails(self):
        """A 38-man roster has no room, and a silently returned 39-man one
        prices the deal with a free extra body, so the ladder that exists to
        charge for body count reads the wrong count. Attaching the drops is the
        caller's job and there is no defensible default for it"""
        full = sim.basis()
        with self.assertRaises(ValueError):
            sim.swap(full, ["Jalen Suggs"], [sim.star(45), sim.star(30)])
        self.assertEqual(len(sim.swap(full, ["Jalen Suggs", "Coby White"],
                                      [sim.star(45), sim.star(30)])), len(full))

    def test_naming_one_body_twice_on_the_send_side_fails(self):
        """One body cannot leave twice, or `len(out_names)` stops being the
        count of bodies going out and a hand-typed 3-for-1 prices as the
        1-for-1 nobody offered, on the ladder that exists to charge for body
        count"""
        full = sim.basis()
        with self.assertRaises(ValueError):
            sim.swap(full, ["Jalen Suggs", "Jalen Suggs"],
                     [sim.star(45), sim.star(30)])

    def test_trading_away_someone_who_is_not_on_the_roster_fails(self):
        """Matching on name and skipping what it does not find returns a roster
        with the incoming star ADDED and nobody removed. Every scenario built
        that way still prints, several hundred PF too high, with no sign of it
        """
        full = sim.basis()
        with self.assertRaises(KeyError):
            sim.swap(full, ["Jalen Sugs"], [sim.star(45)])


class WinsArgumentOrder(unittest.TestCase):
    """`sim.wins(after, before)`, where the argument order is the sign.
    Reversed it reads "wins lost", which is a legitimate call `report_formula`
    makes, so nothing in the code can guard it and both orders return a
    plausible-looking number. A convention that drifted would invert the
    verdict on every deal in every eval and leave the magnitudes untouched"""

    def test_an_upgrade_reads_positive_and_the_reversed_call_reads_the_loss(self):
        """Measured on the roster's own weakest body so the direction is not in
        question. The reversal is exact rather than approximate, the same pair
        of runs read the other way round, which is what makes "wins lost" a
        call a report can make rather than a second measurement"""
        full = sim.basis()
        worst = min(sim.our_roster(), key=season_value)
        base = sim.run(full, trials=20)
        better = sim.run(sim.swap(full, [worst["n"]],
                                  [sim.star(55, 75, tuple(worst["elig"]), n="UP")]),
                         trials=20)
        gained = sim.wins(better, base)
        self.assertGreater(gained, 1.0, "%s -> a 55/75 body is not an upgrade"
                           % worst["n"])
        self.assertAlmostEqual(sim.wins(base, better), -gained, places=9)


class MultiPieceDeal(unittest.TestCase):
    """`Eval Definitions §Δw` says price a multi-piece side with one joint
    `sim.run(sim.swap(...))`, never by adding rows. The rows are floats and
    nothing in the code can stop a caller adding them, so the rule is only
    worth what the gap between the two ways measures, and the published table
    is one column of addable numbers sitting next to a three-for-three offer"""

    def priced_both_ways(self, eligs):
        """The same three-for-three, priced as one deal and as three deals"""
        full = sim.basis()
        base = sim.run(full, trials=30, seed0=101)
        adds = [sim.star(46, 70, e, n="IN%d" % i) for i, e in enumerate(eligs)]
        joint = sim.wins(
            sim.run(sim.swap(full, THREE_OUT, adds), trials=30, seed0=101), base)
        summed = sum(
            sim.wins(sim.run(sim.swap(full, [o], [a]), trials=30, seed0=101), base)
            for o, a in zip(THREE_OUT, adds))
        return joint, summed

    def test_adding_the_rows_up_overstates_a_three_piece_package(self):
        """Three 46-rate centers for Suggs/White/Turner run +3.0 wins priced as
        one deal and +4.0 as three rows added. A third of the package is an
        arrival the nine slots have no room to start, and the sum cannot see
        it, which is a whole win on a deal whose verdict turns on tenths"""
        joint, summed = self.priced_both_ways([("C",)] * 3)
        self.assertGreater(summed - joint, 0.5,
                           "joint %.3f vs summed %.3f" % (joint, summed))

    def test_the_overstatement_is_worst_when_the_pieces_share_a_slot_group(self):
        """The mechanism, and the reason the rule is not a haircut a caller
        could apply from the sum alone. The same three bodies spread over
        guard/forward/center lose ~0.2 wins to the cap instead of ~1.0, so a
        package's sub-additivity is a fact about its shape against OUR roster's
        shape and has to be simulated"""
        stacked = self.priced_both_ways([("C",)] * 3)
        spread = self.priced_both_ways([("C",), ("PG", "SG"), ("SF", "PF")])
        self.assertGreater(stacked[1] - stacked[0],
                           (spread[1] - spread[0]) + 0.4,
                           "stacked %s spread %s" % (stacked, spread))


class SlotFillCurve(unittest.TestCase):
    """The whole point of the 9-slot cap. It binds on LIGHT nights and nowhere
    else, which is why breadth pays at all and why the surplus is the middle of
    the roster rather than its tail"""

    @classmethod
    def setUpClass(cls):
        cls.by_night = sim.run(sim.basis(), trials=40)["by_night"]

    def test_most_of_the_lost_slots_sit_on_the_lightest_nights(self):
        lost = {g: (9 - v[1]) * v[3] for g, v in self.by_night.items()}
        tot = sum(lost.values())
        share = lambda upto: sum(v for g, v in lost.items() if g <= upto) / tot
        self.assertAlmostEqual(share(3), 0.68, delta=0.03)
        self.assertAlmostEqual(share(5), 0.89, delta=0.03)
        self.assertAlmostEqual(tot / (9 * len(sim.SCORING_NIGHTS)), 0.091,
                               delta=0.005)

    def test_far_more_slots_go_empty_for_want_of_a_body_than_a_position(self):
        """"Positions rarely bind" is what licenses treating the positional
        premium as a tiebreak rather than a constraint to build around"""
        vals = self.by_night.values()
        no_slot = sum((min(9, v[0]) - v[1]) * v[3] for v in vals)
        no_body = sum(max(0.0, 9 - v[0]) * v[3] for v in vals)
        self.assertGreater(no_body, 3 * no_slot)


class SlotGroups(unittest.TestCase):
    """`replacement` explains its per-group `R` by the crowding behind it, and
    the crowded group is whichever the table says, so bodies and slots have to
    be countable for ANY group rather than just guards"""

    def test_a_body_takes_the_group_of_the_slots_he_is_confined_to(self):
        """`player_wins` prices every player against his own group's R, and the
        three run 3.4 rate points apart here, so where a PF/C lands is worth
        0.07-0.09 wins on his row. Only a body confined to {C} takes the center
        counterfactual"""
        self.assertEqual(sim.slot_group(["C"]), "center")
        self.assertEqual(sim.slot_group(["PF", "C"]), "forward")
        self.assertEqual(sim.slot_group(["PG", "SG"]), "guard")
        self.assertEqual(sim.slot_group(["SG", "SF"]), "forward")

    def test_a_group_counts_every_slot_it_can_fill(self):
        """The two ANY slots are what a hand count misses. A pure center chases
        3 of the 9, not the 1 the template labels C"""
        self.assertEqual(sim.group_slots(("C",)), 3)
        self.assertEqual(sim.group_slots(("PG", "SG")), 5)
        self.assertEqual(sim.group_slots(("SF", "PF")), 5)

    def test_only_a_body_that_cannot_leave_the_group_crowds_it(self):
        """A dual-eligible body relieves the crowding rather than adding to it,
        so it counts toward neither group"""
        roster = [sim.star(20, 60, ("PG", "SG")), sim.star(20, 60, ("SG", "SF")),
                  sim.star(20, 60, ("C",))]
        self.assertEqual(sim.pure_bodies(roster, ("PG", "SG")), 1)
        self.assertEqual(sim.pure_bodies(roster, ("SF", "PF")), 0)
        self.assertEqual(sim.pure_bodies(roster, ("C",)), 1)


class RosterScopedReports(unittest.TestCase):
    """Half the reports are built on OUR player names, `scenarios` trading
    Suggs and `durability` re-shaping him. Pointed at another team's file those
    names match nobody, so the report prints a full table of numbers answering
    nothing, and `--roster` is advertised for any team"""

    def test_an_our_roster_report_refuses_a_counterparty_file(self):
        """It has to name the ones it DOES serve. A bare refusal on the report
        a Skill just told you to run reads as "--roster is broken", and the 9
        that work are the whole counterparty workflow"""
        for name in sorted(sim.OURS_ONLY):
            with self.subTest(report=name):
                p = sim_process("--roster", THEIR_ROSTER, name)
                self.assertNotEqual(p.returncode, 0)
                for served in set(sim.REPORTS) - sim.OURS_ONLY:
                    self.assertIn(served, p.stdout + p.stderr)

    def test_the_roster_free_report_measures_the_same_thing_for_every_team(self):
        """Its header says it read no roster, which is a claim about the table
        under it: if `market` ever starts reading one, the header is the last
        place that shows, and a board table gets quoted as a team's"""
        for name in sorted(sim.ROSTER_FREE):
            with self.subTest(report=name):
                self.assertEqual(render(name), render(name, THEIR_ROSTER))

    def test_a_roster_the_labels_do_not_carry_is_headed_by_its_own_filename(self):
        """`--roster` takes any path, and the id -> name map only covers the
        twelve. A header that insisted on a name would take out every report in
        the run, including on a tree cut before the map existed"""
        self.assertEqual(roster_mod.label("roster-999999-%s.json"
                                          % fetch_data.SEASON_TAG),
                         "roster-999999-%s.json" % fetch_data.SEASON_TAG)

    def test_naming_no_report_at_all_refuses_the_one_it_falls_back_to(self):
        """`calibration` is the default, so a default applied AFTER the refusal
        hands you the exact report the refusal names, their simulated PF over
        OUR real standings PF, exit 0, under a header naming their file"""
        p = sim_process("--roster", THEIR_ROSTER)
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("CALIBRATION", p.stdout)
        self.assertIn("calibration", p.stdout + p.stderr)

    def test_a_served_report_runs_on_a_counterparty_from_the_shell(self):
        """Every other run of a SERVED report is in-process with the sample
        size shrunk, so this is the only thing showing the command as it is
        actually typed, real interpreter, real argv, exit 0, a table. The
        refusals all exit before loading anything"""
        p = sim_process("--roster", THEIR_ROSTER, "nights")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(THEIR_ROSTER, p.stdout)
        self.assertIn("NIGHTS", p.stdout)

    def test_the_flag_joined_to_its_file_by_an_equals_sign_still_loads_it(self):
        """`--roster=theirs.json` is the other half of how the flag gets typed.
        A parse matching only the bare word sends the whole token through to
        the report check, which comes back complaining about a report name, on
        a flag spelled correctly"""
        p = sim_process("--roster=%s" % THEIR_ROSTER, "nights")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(THEIR_ROSTER, p.stdout)
        self.assertIn("NIGHTS", p.stdout)

    def test_the_flag_with_nothing_after_the_equals_sign_says_what_it_wanted(self):
        """`--roster=` is one keystroke from `--roster=theirs.json`, and an
        arity guard that only counts argv is satisfied by the empty half, then
        loads the DIRECTORY the files sit in under a header saying it had a
        roster"""
        p = sim_process("--roster=", "nights")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("--roster", p.stdout + p.stderr)

    def test_a_roster_file_that_is_not_there_is_refused_before_any_table(self):
        """The commonest way to mistype this flag is a wrong path, and left as
        a traceback it comes after the roster banner and the report's own
        header, so the run reads as started. `_load` also joins against the
        DATA directory rather than the shell's cwd, so a path that exists where
        you typed it still has to be named back to you"""
        p = sim_process("--roster", "no-such-team.json", "players")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertNotIn("wins lost if swapped", p.stdout)
        self.assertIn("no-such-team.json", p.stdout + p.stderr)

    def test_the_readme_names_the_reports_the_flag_actually_refuses(self):
        """The counterparty workflow is followed out of the README, not out of
        `REPORTS`, and the refusal message above is only checked against
        whatever `OURS_ONLY` happens to hold. Move a report between the two
        sets and both stay green while the page sends the reader to run
        something that exits 1"""
        text = one_line(read_text(os.path.join(sim.HERE, "README.md")))
        refused = re.search(r"serves every report but ((?:\*\*)?(?:`\w+` ?)+)",
                            text)
        self.assertIsNotNone(refused, "the README stopped naming them")
        self.assertEqual(set(re.findall(r"`(\w+)`", refused.group(1))),
                         sim.OURS_ONLY)

    def test_the_module_docstring_names_the_reports_the_flag_refuses(self):
        """`sim.py`'s own docstring is the first thing anyone opening the file
        reads. A reader who believes it serves every report runs one of the
        four it refuses, gets exit 1, and reads the flag as broken rather than
        the sentence"""
        text = one_line(sim.__doc__)
        refused = re.search(r"refuse it: ([^.]+)\.", text)
        self.assertIsNotNone(refused, "the docstring stopped naming them")
        self.assertEqual(set(re.findall(r"\w+", refused.group(1))), sim.OURS_ONLY)

    def test_no_skill_carries_its_own_copy_of_the_report_list(self):
        """`trades` used to name the four reports `--roster` refuses. That list
        is `sim.py --help`'s to state -- a second copy in a file the command
        does not read is a copy that goes stale silently, and the skill is what
        gets loaded before a deal is priced"""
        for path in glob.glob(skills_path("*", "*.md")):
            with self.subTest(skill=os.path.basename(os.path.dirname(path))):
                text = one_line(read_text(path))
                named = [n for n in sim.OURS_ONLY if "`%s`" % n in text]
                self.assertLess(len(named), len(sim.OURS_ONLY), named)

    def test_every_report_the_skills_and_pages_cite_is_a_real_one(self):
        """`Eval Definitions`, `eval-team`, `eval-player` and `trades` all send
        a reader to a named `sim.py` run. A citation to a report the registry
        does not carry exits 1 on the command a skill just mandated"""
        pages = [os.path.join(sim.HERE, n) for n in
                 ("README.md", "method.md", "findings.md", "tldr.md")]
        pages += glob.glob(skills_path("*", "*.md"))
        pages += glob.glob(os.path.join(sim.HERE, os.pardir, "*.md"))
        cited = collections.Counter()
        for path in pages:
            for name in re.findall(r"sim\.py ([a-z]\w*)", read_text(path)):
                cited[name] += 1
                with self.subTest(page=os.path.basename(path), report=name):
                    self.assertIn(name, sim.REPORTS)
        self.assertIn("playoffs", cited)

    def test_roster_with_no_file_after_it_says_what_it_wanted(self):
        """Every other CLI error here exits with a written explanation. A
        traceback on the flag a Skill was just told to pass reads as a broken
        flag rather than as a command missing its argument"""
        p = sim_process("--roster")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("--roster", p.stdout + p.stderr)

    def test_the_positions_premium_is_explained_by_the_loaded_roster(self):
        """A pure-guard count typed into the `positions` header describes
        whatever roster produced the table. It has to come off the roster the
        bodies were ADDED to, the padded 38, not the live file, which is 4
        guards short of it here"""
        out = render("positions", THEIR_ROSTER)
        pure_g = sum(1 for q in sim.basis(THEIR_ROSTER)
                     if set(q["elig"]) <= {"PG", "SG"})
        self.assertIn("%d pure PG/SG" % pure_g, out)

    def test_the_light_night_premise_is_the_loaded_rosters_own(self):
        """What steering the auction buys is entirely a function of which light
        nights the OTHER 31 bodies already reach. Ours reach 31 of the 32,
        which is why the headline sits at the 0.1-win floor at all, so a report
        quoting our spread while pricing his auction hands a counterparty our
        ceiling and every table under it still prints"""
        flat = one_line(render("schedules", THEIR_ROSTER))
        full = sim.basis(THEIR_ROSTER)
        moved_a, moved_b = sim.steer(full, ["BKN"] * 7), sim.steer(full, ["CHI"] * 7)
        kept = [p["tm"] for p, x, y in zip(full, moved_a, moved_b)
                if p["tm"] == x["tm"] == y["tm"]]
        self.assertIn("the other %d stay where they are, and %d of the %d "
                      "light nights are already reached"
                      % (len(kept), sim.coverage(kept), len(sim.light_nights())),
                      flat)
        self.assertIn("spread of %d NBA teams"
                      % sum(1 for t in set(kept) if not sim.unsigned(t)), flat)

    def test_the_group_r_note_agrees_with_the_table_it_explains(self):
        """A report served for any team cannot explain its numbers with OUR
        roster's shape. Against a counterparty whose guard R is BELOW his
        forward R, a fixed guard sentence offers a body count as proof of the
        opposite of what the numbers say.

        Two things have to hold. The counts come off the roster R was FITTED
        on, the padded 38 rather than the live file, which is a different shape
        and 4-8 bodies short per group. And crowding is offered as an
        explanation only where it actually orders the three R's, since on our
        own padded roster guards and centers are equally crowded while center R
        is the higher"""
        out = render("replacement", THEIR_ROSTER)
        R = {lab: float(re.search(r"^ +%s +([\d.]+)" % lab, out, re.M).group(1))
             for lab in ("guard", "forward", "center")}
        note = re.search(r"guard ([-+]\d+\.\d), center ([-+]\d+\.\d)", out)
        self.assertIsNotNone(note, out)
        # The note is a 1-dp difference; `R` is the difference of two 1-dp
        # table cells. Each cell is up to 0.05 off, so 0.1 is the bound and it
        # has to be INCLUSIVE -- a gap of exactly 0.1 is a float 0.10000000009
        self.assertAlmostEqual(float(note.group(1)),
                               R["guard"] - R["forward"], delta=0.11)
        self.assertAlmostEqual(float(note.group(2)),
                               R["center"] - R["forward"], delta=0.11)
        padded = sim.basis(THEIR_ROSTER)
        for g, elig in sim.GROUPS.items():
            with self.subTest(group=g):
                self.assertIn("%s %d/%d" % (g, sim.pure_bodies(padded, elig),
                                            sim.group_slots(elig)), out)
        top = re.search(r"[Hh]ighest R is (\w+)", out)
        self.assertIsNotNone(top, out)
        self.assertEqual(top.group(1), max(R, key=R.get), out)
        crowd = {g: sim.pure_bodies(padded, e) / sim.group_slots(e)
                 for g, e in sim.GROUPS.items()}
        byR = sorted(R, key=lambda g: -R[g])
        orders = all(crowd[a] > crowd[b] for a, b in zip(byR, byR[1:]))
        self.assertIn("rowding %s the three here"
                      % ("orders" if orders else "does NOT order"), out)


class OneSchedule(unittest.TestCase):
    """Which NBA team a synthetic body sits on moves its added PF by ~220
    across the 30 schedules, several rate points rather than a rounding effect,
    so the study declares ONE schedule and puts every body on it"""

    def test_the_schedule_moves_a_body_more_than_the_tie_band_does(self):
        full = sim.basis()
        base = sim.run(full, trials=40)["pf"]

        def added(tm):
            body = sim.star(45, 68, ("SF", "PF"), tm, "ADD")
            return sim.run(full + [body], trials=40)["pf"] - base
        self.assertGreater(abs(added("OKC") - added("DET")), 100)

    def test_separate_one_for_ones_beat_a_consolidation_on_one_schedule(self):
        """Priced on the declared schedule the comparison is about bodies
        alone, which is the claim worth keeping. Spread the incoming bodies
        over different NBA teams and an unknown part of the gap is a schedule
        handicap booked as body count"""
        full = sim.basis()
        base = sim.run(full, trials=40)
        sep = sim.wins(sim.run(sim.swap(full, THREE_OUT, [
            sim.star(42, 68, ("SF", "PF"), sim.SIM_TM, "S%d" % i)
            for i in range(3)]), trials=40), base)
        con = sim.wins(sim.run(sim.swap(full, THREE_OUT, [
            sim.star(65.2, 65, ("C",), sim.SIM_TM)]), trials=40), base)
        self.assertGreater(sep, con)


class BreakEven(unittest.TestCase):
    def test_a_breakeven_outside_the_bracket_raises_rather_than_returning_an_end(self):
        """Bisection with no sign check converges on the nearer END of its own
        bracket and returns it as an answer, a number that looks measured, sits
        in the middle of the rates we trade at, and is really just `lo`. Both
        ends do it"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            with self.assertRaises(ValueError) as low:
                sim.breakeven(full, ["Jalen Suggs"], lo=60.0, hi=90.0)
            self.assertIn("60", str(low.exception))
            with self.assertRaises(ValueError) as high:
                sim.breakeven(full, THREE_OUT, lo=20.0, hi=30.0)
            self.assertIn("30", str(high.exception))

    def test_one_uncomputable_cell_does_not_take_the_table_with_it(self):
        """Every row of the break-evens table is a comprehension over
        2..N-for-1s, so the ValueError `breakeven` correctly raises for one
        cell kills the whole report. Out of bracket is a real answer ABOUT THAT
        CELL, "no such player exists, so the deal is unbuyable", so the cell
        says which end it fell off"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            self.assertIn(">30", sim.breakeven_cell(full, THREE_OUT,
                                                    lo=20.0, hi=30.0))
            self.assertIn("<60", sim.breakeven_cell(full, THREE_OUT[:1],
                                                    lo=60.0, hi=90.0))
            self.assertRegex(sim.breakeven_cell(full, THREE_OUT[:2]),
                             r"\d\d\.\d")

    def test_the_rate_it_returns_is_pf_neutral(self):
        """What a break-even IS. Seat a body at that rate in the slots the
        outgoing players vacated and the season's PF comes back where it
        started.

        Both sides are 20-trial figures on the same estimator the search
        bisected on, so what this pins is that the search converged, not that
        the published rate survives a re-measure at the published trial count
        """
        full = sim.basis()
        out = ["Jalen Suggs", "Coby White"]
        with cheap_monte_carlo(20):
            rate = sim.breakeven(full, out, gp=68, elig=("SF", "PF"))
            got = sim.run(sim.swap(full, out, [sim.star(rate, 68)]))["pf"]
            self.assertAlmostEqual(got, sim.run(full)["pf"], delta=40)

    def test_the_breakeven_moves_with_the_incoming_gp_and_slot(self):
        """"Read the row matching his shape." The same 3-for-1 needs several
        more rate points from a 65-GP center than from a 68-GP forward and
        fewer from a 78-GP one, which is how Jokic reads as a hair positive
        against his own row and a 6-point win against the forward row. A break-
        even quoted without its GP and slot is the wrong number, not a rounded
        one"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            forward = sim.breakeven(full, THREE_OUT, 68, ("SF", "PF"))
            center = sim.breakeven(full, THREE_OUT, 65, ("C",))
            durable = sim.breakeven(full, THREE_OUT, 78, ("SF", "PF"))
        self.assertGreater(center, forward + 3.0)
        self.assertLess(durable, forward - 1.5)


class BoardSnapshot(unittest.TestCase):
    """`dizzle-dynasty` snapshots are month-stamped and the month moves, and
    the Skill says never hardcode one. `board_rates` is the study's only rank
    to rate bridge, so a hardcoded month reads a stale board silently, and
    keeps reading it after the new snapshot lands beside it"""

    def test_the_newest_snapshot_is_the_one_read(self):
        d = tempfile.mkdtemp()
        for n in ("july-2026-dynasty-ranks-points.csv",
                  "december-2026-dynasty-ranks-points.csv",
                  "january-2027-dynasty-ranks-points.csv",   # newest, year wins
                  "january-2027-dynasty-ranks-9cat.csv"):    # wrong scoring
            open(os.path.join(d, n), "w").close()
        self.assertEqual(os.path.basename(sim.newest_board(d)),
                         "january-2027-dynasty-ranks-points.csv")

    def test_a_directory_with_no_snapshot_says_what_it_looked_for(self):
        with self.assertRaises(FileNotFoundError) as e:
            sim.newest_board(tempfile.mkdtemp())
        self.assertIn("dynasty-ranks-points.csv", str(e.exception))

    def test_the_report_names_the_snapshot_it_priced_off(self):
        """The month moves and the old file stays put, so a rank table that
        does not name its board cannot be checked against one, and the reader
        has no way to tell a re-snapshot from a re-rank"""
        self.assertIn(os.path.basename(sim.newest_board()), render("market"))


class BoardBridge(unittest.TestCase):
    """The framework converts board rank to wins through one constant, so a
    rank to FPts/G join that silently matches nothing would make every scenario
    look purchasable"""

    def test_the_top_of_the_board_joins_to_scoring_rates(self):
        pairs = sim.board_rates()
        top50 = [r for r, _ in pairs if r <= 50]
        self.assertGreater(len(top50), 40)

    def test_rate_falls_as_board_rank_rises(self):
        pairs = sim.board_rates()
        top = statistics.mean([v for r, v in pairs if r <= 30])
        deep = statistics.mean([v for r, v in pairs if 150 <= r <= 250])
        self.assertGreater(top, deep + 10)

    def test_the_rates_a_four_and_five_for_one_demands_barely_exist(self):
        """The case for the 3-for-1 cap that does NOT go through the win table.
        The 4-for-1 break-even at 45.1 and the 5-for-1 at 58.8 ask for rates
        almost nobody supplies, so those deals are unavailable at any price
        rather than merely expensive. If the pool ever gets deep in 45s that
        argument is gone"""
        pairs = sim.board_rates()
        self.assertEqual(len(pairs), 359)
        self.assertEqual(sum(1 for _, r in pairs if r >= 45), 8)
        self.assertEqual(sum(1 for _, r in pairs if r >= 50), 3)
        self.assertEqual(sum(1 for _, r in pairs if r >= 60), 1)

    def test_a_fragment_season_does_not_set_the_rate_a_rank_band_supplies(self):
        """The report prints the DEEPEST rank that has ever supplied a rate,
        how far down you might have to look, so one 5-game hot streak deep on
        the board moves the answer to a question about where 30-FPts players
        live. `min_gp` is what stops it"""
        deepest = lambda pairs: max(k for k, r in pairs if r >= 30)
        self.assertLess(deepest(sim.board_rates()),
                        deepest(sim.board_rates(min_gp=0)) - 50)
        self.assertEqual(sim.pool_seasons("Walker Kessler")["2025"][1], 5)


class PFPerWinBand(unittest.TestCase):
    """Every trade verdict is priced through this one constant and `eval-team`
    quotes a band for it, so the band has to be re-derivable rather than a
    number in prose.

    The CLUSTERING is the whole content. The 11 margins in a period all share
    our score for that period, so they are not 212 independent draws, and
    resampling them individually gives an interval several times too narrow"""

    def test_the_band_brackets_the_point_estimate_and_stays_wide(self):
        lo, hi = sim.pf_per_win_band(n=400)
        self.assertLess(lo, sim.PF_PER_WIN)
        self.assertGreater(hi, sim.PF_PER_WIN)
        self.assertGreater((hi - lo) / sim.PF_PER_WIN, 0.15)

    def test_one_win_is_about_600_pf(self):
        """"1 win ~ 600 PF" is the headline the whole framework converts
        through, and every +wins figure in the README divides by it. It is a
        measurement off the real margin distribution, so it moves when the
        score matrix or the scoring basis does and every table above it goes
        stale silently"""
        self.assertAlmostEqual(sim.PF_PER_WIN, 597, delta=10)


class StandingsBasis(unittest.TestCase):
    """ONE basis for every PF figure here, the periods that count toward the
    standings. Periods 21-23 are the playoff and consolation bracket and the
    standings PF column excludes them, so a 23-period total is a different
    season, and it is the number the API hands you first"""

    def test_the_scored_periods_are_the_ones_the_standings_count(self):
        self.assertEqual(sim.WEEKS, 20)
        self.assertEqual(len(sim.OURS), 20)
        self.assertEqual(round(sum(sim.OURS)), 27229)   # our standings PF column
        for i in sim.SCORED:
            self.assertNotIn("playoff", sim.PERIODS[i]["kinds"])

    def test_including_the_bracket_periods_inflates_the_total(self):
        """Not a rounding difference. Including them inflates the total 18.5%,
        which is several wins wherever it lands"""
        every = list(sim.SCORES[sim.US].values())
        self.assertEqual(len(every), 23)
        self.assertGreater(sum(every) / sum(sim.OURS), 1.15)


class Calibration(unittest.TestCase):
    """The one end-to-end check that the machinery, schedule, periods, the
    9-slot matching and the availability draw, reproduces a season that
    actually happened. §Method calls absolute PF good to ~5% and quotes it as a
    SANITY BOUND rather than a scale factor, so what is worth guarding is the
    order of magnitude"""

    def test_the_season_that_happened_simulates_to_roughly_what_it_scored(self):
        got = sim.run(sim.our_roster(projected=False), trials=40)["pf"]
        real = sim.REAL_WK_MEAN * sim.WEEKS
        self.assertAlmostEqual(got / real, 1.0, delta=0.2)


class CalibrationRatio(unittest.TestCase):
    """The ratio divides the CURRENT roster's simulated season by what the PRE-
    trade roster actually scored, since 27,229 is a standings column and the
    file is re-cut after every trade. Printed bare it reads as a 5.2% model
    error, which is the one number a reader would use to rescale the study"""

    def test_the_printed_ratio_says_it_is_measured_against_the_pre_trade_roster(self):
        out = render("calibration")
        self.assertIn("ratio", out)
        self.assertIn("pre-trade", out[out.index("ratio"):].lower())


class CalibrationUsesTheScoredPeriods(unittest.TestCase):
    """`SCORED`, the 20 periods that count toward the standings, is the ONE
    basis for every PF figure here. Setting MARGIN_SD over 20 periods against a
    pooled opponent sd taken over all 23 compares two different seasons"""

    def test_the_independence_check_is_on_the_same_periods_as_the_margins(self):
        out = render("calibration")
        rho = float(re.search(r"correlation rho = (\d+\.\d+)", out).group(1))

        def rho_over(ordinals):
            ind = math.sqrt(sim.REAL_WK_SD ** 2 + statistics.stdev(
                [v for t, s in sim.SCORES.items() if t != sim.US
                 for p, v in s.items() if p in ordinals]) ** 2)
            return 1 - sim.MARGIN_SD ** 2 / ind ** 2

        scored = {sim.PERIODS[i]["ordinal"] for i in sim.SCORED}
        self.assertAlmostEqual(rho, rho_over(scored), delta=0.006)
        self.assertGreater(abs(rho - rho_over(set(sim.SCORES[sim.US]))), 0.006,
                           "the two bases agree, so this cannot tell them apart")


class SeasonAge(unittest.TestCase):
    def test_age_is_taken_at_the_february_of_the_season_it_describes(self):
        # born 1995-02-19, and Fleaflicker's 2025 season hits Feb 1 2026
        """Season age has to be a fixed point inside that season. Reading
        `detail.age` instead dates every historical row to whenever the file
        was scraped, so a 5-season fit runs on drifting labels"""
        self.assertAlmostEqual(sim.age_at("1995-02-19", 2025), 30.95, places=1)
        self.assertAlmostEqual(sim.age_at("1995-02-19", 2021), 26.95, places=1)


class GPModelSelection(unittest.TestCase):
    """The comparison exists to REJECT models, so it has to be out of sample.
    An in-sample table always ranks the richest model first and would have us
    adopt per-player projections that predict nothing"""

    def test_nothing_beats_the_pool_mean_when_games_played_is_pure_noise(self):
        """The floor the bake-off is read against. On rows where GP is pure
        noise nothing may beat the flat prior, or the table is ranking overfit
        """
        rng = random.Random(7)
        rows = [{"name": "P%d" % i, "age": rng.uniform(20, 36),
                 "hist": [rng.gauss(58, 17) for _ in range(5)],
                 "rate": rng.uniform(20, 50), "y": rng.gauss(58, 17)}
                for i in range(500)]
        err = sim.gp_models(rows)
        self.assertIn("mean", err)
        for name, rmse in err.items():
            self.assertGreater(rmse, err["mean"] - 0.5,
                               "%s beat the mean on noise" % name)

    def test_age_wins_when_the_games_really_are_age_driven(self):
        """Guard the other way. A harness that always prefers the constant is
        just as useless, so make GP genuinely age-driven and age has to win"""
        rng = random.Random(7)
        rows = []
        for i in range(500):
            age = rng.uniform(20, 36)
            rows.append({"name": "P%d" % i, "age": age,
                         "hist": [rng.gauss(58, 17) for _ in range(5)],
                         "rate": rng.uniform(20, 50),
                         "y": 110 - 2.0 * age + rng.gauss(0, 6)})
        err = sim.gp_models(rows)
        self.assertLess(err["age"], err["mean"] - 5)


class GPFoldThatCannotBeFitted(unittest.TestCase):
    """Every model in the bake-off has to be scored on the SAME rows, or the
    RMSE column is not a comparison. A fold whose design comes back singular
    leaves that model's rows as NaN, and `_rmse` drops NaNs, so it ends up
    scored on 4/5 of the rows while its competitors get 5/5 and nothing prints
    """

    def test_a_model_that_loses_a_fold_is_refused_rather_than_scored_on_the_rest(self):
        rows = [{"name": "P%d" % i, "y": 60.0 + i, "hist": [60], "rate": 30.0,
                 "age": 25.0} for i in range(10)]
        self.addCleanup(gp.GP_MODELS.pop, "flat", None)
        # collinear with the intercept the fit always carries, so no fold of it
        # can be solved
        gp.GP_MODELS["flat"] = lambda r: (1.0,)
        with self.assertRaises(ValueError) as e:
            gp.gp_sq_errors(rows, models=("flat",))
        self.assertIn("flat", str(e.exception))


class GPUncertainty(unittest.TestCase):
    """The uncertainty a gap is judged against has to be resampled over
    PLAYERS. The sd across FOLD SHUFFLES is which player landed in which fold,
    not sampling uncertainty over the ~286 players, and it understates the real
    spread more than tenfold"""

    def test_the_reported_uncertainty_covers_the_gap_it_is_used_to_judge(self):
        b = sim.gp_bootstrap(sim.gp_rows(), models=("gp1", "gp5", "mean"), n=400)
        self.assertGreater(b["gp5"]["delta"], 0.0)
        self.assertLess(b["gp5"]["lo"], 0.0)
        self.assertGreater(b["mean"]["lo"], 0.0)


class GPRows(unittest.TestCase):
    def test_history_is_strictly_earlier_than_the_season_being_predicted(self):
        """A row whose `hist` contains its own target season makes every model
        look clairvoyant and would justify per-player projections outright"""
        rows = sim.gp_rows()
        self.assertGreater(len(rows), 300)
        for r in rows:
            self.assertTrue(r["seasons"], r)
            self.assertLess(max(r["seasons"]), r["season"], r)

    def test_history_is_most_recent_first(self):
        """`gp1` reads `hist[0]`, so the order carries meaning rather than
        being cosmetic"""
        for r in sim.gp_rows():
            self.assertEqual(r["seasons"], sorted(r["seasons"], reverse=True), r)


class GPProjection(unittest.TestCase):
    """GP is the input this study calls dominant, ~10x any format effect, and
    taking one injury season literally is the biggest error available here, so
    a projection has to regress toward the pool"""

    def test_the_gp_fit_coefficients_are_the_ones_the_readme_publishes(self):
        """The formula is quoted as one an eval author can apply by hand, and
        it is a FIT, so a re-scrape moves it silently while every GP in every
        table stays as printed. Pinned so a refit has to be a deliberate re-
        publish"""
        intercept, per_gp, per_rate = sim.gp_model()
        self.assertAlmostEqual(intercept, 25.7, delta=0.05)
        self.assertAlmostEqual(per_gp, 0.368, delta=0.005)
        self.assertAlmostEqual(per_rate, 0.432, delta=0.005)

    def test_an_outlier_injury_season_regresses_upward(self):
        self.assertGreater(sim.project_gp("Joel Embiid"), 45)

    def test_an_iron_man_season_regresses_downward(self):
        """Regression pulls the top down too, since 82 GP is not a projection
        """
        self.assertLess(sim.project_gp("Desmond Bane"), 75)

    def test_the_durable_player_still_projects_above_the_fragile_one(self):
        """Compressed, not erased, so the ordering has to survive"""
        self.assertGreater(sim.project_gp("Nikola Jokić"),
                           sim.project_gp("Joel Embiid"))

    def test_a_superstar_rate_does_not_buy_more_games_than_an_all_star_rate(self):
        """Empirical next-season GP by last-season rate is concave and turns
        DOWN, 57.6 at rate 20-25, peaking 63.2 at 30-35, then 59.6 above 45. A
        rate term that keeps adding past the peak over-projects exactly the
        star-rate players every headline table is built on"""
        self.assertLessEqual(sim.project_gp("nobody", gp=65, rate=65.0),
                             sim.project_gp("nobody", gp=65, rate=35.0) + 0.5)

    def test_a_fringe_player_projects_fewer_games_than_a_starter_at_the_same_gp(self):
        """Expected GP falls off hard below rotation quality, ~40 GP at rate
        <10 against ~63 at rate 30-40, so a fit gated to rotation players
        projects the whole bench ~10 games too high. Scoring rate is the
        feature that fixes it, and `sim.py gp` shows age does not"""
        self.assertGreater(sim.project_gp("Desmond Bane"),
                           sim.project_gp("Sion James") + 4)


class MissedSeasonRate(unittest.TestCase):
    """A roster file's rate is `seasonAverage`, which Fleaflicker omits for a
    player who missed the whole season, so his row reads 0.0. The projection is
    the only thing giving him a rate at all, and it has to reach ANY team's
    file, or a team holding Haliburton prices out at his value minus all of it
    """

    def test_a_missed_season_is_priced_off_the_projection(self):
        p, = sim.our_roster(roster_file(
            {"n": "Tyrese Haliburton", "tm": "IND", "avg": 0.0, "tot": 0.0,
             "gp": 0, "posLabel": "G", "elig": ["PG", "SG"]}))
        self.assertGreater(p["avg"], 20)
        self.assertLess(p["avg"], 35)
        self.assertGreater(p["gp"], 45)


class PoolJoinByName(unittest.TestCase):
    """The pool is joined on a NAME, and the board-join rule already says that
    is where accents and punctuation silently drop rows. An ASCII-spelled
    roster file that loses the pool season prices the man off his file row, so
    a whole missed season reads as 0 GP at 0.0 FPts"""

    def test_an_ascii_spelling_finds_the_same_pool_season(self):
        self.assertAlmostEqual(sim.project_gp("Luka Doncic"),
                               sim.project_gp("Luka Dončić"), places=6)

    def test_a_name_in_neither_the_pool_nor_the_call_fails_loudly(self):
        """Returning None, which `our_roster` then rounds, surfaces the failure
        as a TypeError inside `round()` several frames away, if at all"""
        with self.assertRaises(KeyError):
            sim.project_gp("Nobody At All")


class SymmetricProjection(unittest.TestCase):
    """The documented failure mode is projecting our own injured players
    forward while pricing theirs at their worst season. `our_roster` prices ANY
    team's file, so applying the fit there, to every player and with no hand-
    typed GP, is the only thing making that impossible rather than merely
    discouraged"""

    def test_every_player_regresses_toward_the_pool_not_just_a_named_few(self):
        proj = {p["n"]: p["gp"] for p in sim.our_roster()}
        raw = {p["n"]: p["gp"] for p in sim.our_roster(projected=False)}
        self.assertEqual(raw["Desmond Bane"], 82)
        self.assertLess(proj["Desmond Bane"], raw["Desmond Bane"])
        self.assertEqual(raw["Jalen Suggs"], 57)
        self.assertGreater(proj["Jalen Suggs"], raw["Jalen Suggs"])

    def test_a_pooled_players_games_come_off_his_pool_rate(self):
        """The GP fit was fitted on last season's ACTUAL rate, which is what
        the pool carries, so feeding it the projected rate would recalibrate
        every GP figure in the study silently"""
        for p in sim.our_roster():
            if sim.pool_seasons(p["n"]):
                with self.subTest(player=p["n"]):
                    self.assertEqual(p["gp"], round(sim.project_gp(p["n"])))

    def test_the_rate_applies_by_name_not_by_owner(self):
        """A projection keys on the player, so it has to survive him being
        traded. A counterparty's file re-reading last season's average
        regresses his team on a DIFFERENT rule from ours, the asymmetry
        `our_roster` exists to make structurally impossible"""
        def maluach_priced_off(avg):
            p, = sim.our_roster(roster_file(
                {"n": "Khaman Maluach", "tm": "PHX", "avg": avg, "tot": 377.0,
                 "gp": 46, "posLabel": "C", "elig": ["C"]}))
            return p["avg"]

        low, high = maluach_priced_off(8.2), maluach_priced_off(40.0)
        self.assertEqual(low, high)
        self.assertNotIn(low, (8.2, 40.0))

    def test_the_calibration_basis_is_the_season_that_actually_happened(self):
        """`projected=False` stays raw, rate and GP alike, zeros and all. The
        calibration compares the sim against real '25-26 PF at the rates and
        the GP that really occurred, so projecting either there would
        recalibrate the whole study against itself"""
        raw = sim._load(sim.ROSTER)
        self.assertEqual([(p["n"], p["avg"], p["gp"])
                          for p in sim.our_roster(projected=False)],
                         [(p["n"], p["avg"], p["gp"]) for p in raw])


class GPRunsOnTheActualRate(unittest.TestCase):
    """`Eval Definitions §Durability` says **`GP` is projected off last
    season's ACTUAL rate, never the projected one**, since that is the input
    the fit was built on and a projected rate through it recalibrates every
    `GPp` in the study against a variable it never saw.

    Two rates sit on the same roster row, so the wrong one is one keystroke
    away and the substitution is silent, every GP in every table moving with no
    figure on the page saying which variable produced it. `SymmetricProjection`
    guards the CALLER but takes its expectation from `project_gp`'s own
    default, so both sides of that comparison move together. These read the two
    rates apart instead"""

    OURS = "De'Anthony Melton"

    def test_the_games_come_off_the_rate_that_happened_not_the_one_forecast(self):
        actual, _ = sim.pool_seasons(self.OURS)["2025"]
        forecast = sim.projected_rate(self.OURS)
        self.assertLess(forecast, actual - 5)
        p = rostered(self.OURS)

        self.assertEqual(p["gp"], round(sim.project_gp(self.OURS, rate=actual)))
        self.assertGreater(p["gp"],
                           round(sim.project_gp(self.OURS, rate=forecast)) + 2)

    def test_a_counterparty_gets_the_same_games_off_the_same_season(self):
        """§Durability again, regressed **identically on both sides of every
        deal**. A counterparty's file is the only place a row's OWN `avg`/`gp`
        could be read instead of the pool season the fit was built on, which is
        the documented failure exactly, our injured man projected forward while
        theirs is priced at his worst line"""
        ours = rostered(self.OURS)
        theirs, = sim.our_roster(roster_file(
            {"n": self.OURS, "tm": "BKN", "avg": 3.1, "tot": 37.0,
             "gp": 12, "posLabel": "G", "elig": ["PG", "SG"]}))

        self.assertEqual(theirs["gp"], ours["gp"])
        actual, _ = sim.pool_seasons(self.OURS)["2025"]
        self.assertEqual(theirs["gp"], round(sim.project_gp(self.OURS,
                                                            rate=actual)))

    def test_a_whole_missed_season_reaches_back_to_the_last_one_that_happened(self):
        """A missed season is ABSENT from the pool rather than a zero
        (`§Durability`), so the fit's "last season" is the last one that
        exists. His is the row most exposed to the substitution, since his file
        `avg` is 0.0 and the projection is the only rate on it, while the
        actual he has to be fitted on is two years back and nowhere on the page
        """
        name = "Fred VanVleet"
        self.assertIn("miss", sim.evidence_flags(name))
        self.assertNotIn("2025", sim.pool_seasons(name))
        raw = rostered(name, projected=False)
        self.assertEqual((raw["avg"], raw["gp"]), (0.0, 0))

        actual, _ = sim.pool_seasons(name)["2024"]
        forecast = sim.projected_rate(name)
        p = rostered(name)

        self.assertEqual(p["gp"], round(sim.project_gp(name, rate=actual)))
        self.assertGreater(p["gp"], round(sim.project_gp(name, rate=forecast)) + 4)

    def test_a_row_the_pool_never_saw_is_fitted_on_the_actual_line_it_carries(self):
        """`nopool` is not only rookies. The pool is a separate scrape from the
        roster fetch and the join is by NAME, so an established player lands
        here with last season's actual line sitting on his file row. The fit
        has its input right there, and reaching past it for the forecast is the
        substitution §Durability forbids, on rows already flagged as the
        thinnest evidence in the study.

        A true rookie is the only row with no actual rate anywhere, and only
        there is the projection a defensible fallback (`NoPoolHistory`)"""
        name = "Vasilije Micić"
        self.assertEqual(sim.evidence_flags(name), ["nopool"])
        self.assertLess(sim.projected_rate(name), 15)

        p, = sim.our_roster(roster_file(
            {"n": name, "tm": "PHX", "avg": 21.5, "tot": 946.0,
             "gp": 44, "posLabel": "G", "elig": ["PG", "SG"]}))

        self.assertEqual(p["gp"], round(sim.project_gp(name, gp=44, rate=21.5)))

    def test_no_row_on_any_roster_is_fitted_on_the_forecast(self):
        """The class the cases above are drawn from. Every kind of player a
        roster can hold, long history, thin, fragment, a missed year,
        unprojected, unsigned, none at all, goes through the one `our_roster`,
        on ours and on a counterparty's alike, so a sweep is the only thing
        that says the rule holds for the rows nobody thought to name"""
        moved = 0
        for path in (None, THEIR_ROSTER, ROOKIE_ROSTER):
            raw = sim.our_roster(path, projected=False)
            self.assertGreater(len(raw), 20)
            for before, after in zip(raw, sim.our_roster(path)):
                n = before["n"]
                seasons = sim.pool_seasons(n)
                if seasons:
                    actual = (seasons.get("2025") or seasons[max(seasons)])[0]
                    gp_from_file = {}
                else:
                    actual = before["avg"]
                    gp_from_file = {"gp": before["gp"]}
                if not actual:
                    continue                     # a rookie, no actual rate exists
                forecast = sim.projected_rate(n)
                with self.subTest(roster=path or "ours", player=n):
                    self.assertEqual(
                        after["gp"],
                        round(sim.project_gp(n, rate=actual, **gp_from_file)))
                if forecast is not None and round(sim.project_gp(
                        n, rate=forecast, **gp_from_file)) != after["gp"]:
                    moved += 1
        self.assertGreater(moved, 15)

    def test_the_games_on_the_printed_row_are_the_projected_ones(self):
        """`Eval Definitions §Columns` says the `gp` a `players` row prints is
        `GPp`, the projection `Δw` runs on, and an eval copies it into the
        published table beside last season's actual `GP`. Raw and projected are
        the same field name one call apart, so a table rendered off the file
        prints last season's under the projected heading, and for a man who
        missed the year that is a bare 0 next to a real `Δw`. Every other test
        here stops at the roster row, which is not what anybody reads"""
        table = render("players")
        for name in ("Fred VanVleet", "Amen Thompson"):
            raw = rostered(name, projected=False)
            p = rostered(name)
            self.assertNotEqual(raw["gp"], p["gp"])
            row, = [l for l in table.splitlines() if l.startswith("  " + name)]
            printed, = re.findall(r"[\d.]+ +(\d+) +\S+ +[-+][\d.]+", row)
            self.assertEqual(int(printed), p["gp"], row)


class NoPoolHistory(unittest.TestCase):
    """`our_roster` feeds the GP fit the POOL's rate, and a player the pool has
    never seen has none to give it, so he is the one row where that branch goes
    the other way. A TRUE rookie's file row is a 0-GP, 0.0-rate shell with no
    actual rate anywhere on it, so without the projection he prices as a hole
    on a roster that really holds a body"""

    ROOKIE = "Thomas Sorber"

    def test_a_player_the_pool_has_never_seen_still_prices_as_a_body(self):
        raw, = [q for q in sim._load(ROOKIE_ROSTER) if q["n"] == self.ROOKIE]
        p = rostered(self.ROOKIE, ROOKIE_ROSTER)

        self.assertEqual((raw["avg"], raw["gp"]), (0.0, 0))
        self.assertEqual(sim.evidence_flags(self.ROOKIE), ["nopool"])
        self.assertAlmostEqual(p["avg"], sim.projected_rate(self.ROOKIE))
        self.assertGreater(p["gp"], 20)
        self.assertEqual(p["gp"], round(sim.project_gp(
            self.ROOKIE, gp=0, rate=sim.projected_rate(self.ROOKIE))))

    def test_a_body_with_neither_a_pool_season_nor_a_projection_still_prices(self):
        """Both fallbacks gone, an undrafted body the pool never saw and the
        feed does not carry. `project_gp` RAISES on a name with no rate at all
        (`PoolJoinByName`), and a roster that will not load prices no trade at
        all, so the last fallback has to be the row's own 0.0 rather than None
        """
        path = roster_file({"n": "Unknown Rookie", "tm": "LAC", "avg": 0.0,
                            "tot": 0.0, "gp": 0, "posLabel": "F",
                            "elig": ["SF", "PF"]})
        self.assertIsNone(sim.projected_rate("Unknown Rookie"))
        p, = sim.our_roster(path)
        self.assertEqual(p["gp"], round(sim.project_gp("Unknown Rookie",
                                                       gp=0, rate=0.0)))


class RateEvidence(unittest.TestCase):
    """A rate posted over a fragment season no longer carries the whole `Δw`,
    the projection replaces it. That same fragment is still the GP fit's main
    input and GP is the dominant one, so how many games the pool saw is what
    says whether the `Δw` is a measurement or an upper bound (`Eval Definitions
    §Δw`)"""

    def test_it_reports_the_games_the_gp_projection_rests_on(self):
        self.assertEqual(sim.rate_evidence("Kevin Porter")["gp"], 38)
        self.assertEqual(sim.rate_evidence("Precious Achiuwa")["gp"], 73)

    def test_it_reports_a_whole_season_missing_from_the_pool(self):
        """A missed season is ABSENT from the pool rather than a zero, so the
        GP fit cannot see it at all and expected GP is conditional on him
        playing"""
        self.assertTrue(sim.rate_evidence("Kevin Porter")["missed"])
        self.assertFalse(sim.rate_evidence("Precious Achiuwa")["missed"])

    def test_a_missed_most_recent_season_counts_too(self):
        """A trailing absence is the same censoring as an interior one and the
        one the GP fit is blindest to, so it cannot read as a full season"""
        self.assertTrue(sim.rate_evidence("Kyrie Irving")["missed"])
        self.assertTrue(sim.rate_evidence("Fred VanVleet")["missed"])

    def test_a_late_arrival_is_not_a_missed_season(self):
        """Seasons before a player entered the pool are not absences. Only a
        gap INSIDE his history is one, or every rookie reads as injured"""
        self.assertFalse(sim.rate_evidence("Stephon Castle")["missed"])

    def test_it_counts_the_rotation_seasons_the_role_rests_on(self):
        """Rate >= 15 is where GP starts measuring health rather than role
        (`Eval Definitions §Durability`), so it is also the bar a season clears
        to be evidence the role is real"""
        self.assertEqual(sim.rate_evidence("Kevin Porter")["rotation"], 4)
        self.assertEqual(sim.rate_evidence("Ty Jerome")["rotation"], 2)

    def test_it_names_every_flag_code_an_eval_has_to_carry(self):
        """`Eval Template.md` fixes the vocabulary and `Eval Definitions`
        §Durability
        fixes the fragment band at 10-25 games. An eval author reads these off
        here rather than eyeballing five seasons of pool rows per player, so
        the PUBLIC function has to name all four codes, or a caller gets two of
        the four with no sign the others exist"""
        self.assertEqual(sim.evidence_flags("Ty Jerome"), ["frag", "rot2"])
        self.assertEqual(sim.evidence_flags("Kevin Porter"), ["miss"])
        self.assertEqual(sim.evidence_flags("Precious Achiuwa"), [])
        self.assertEqual(sim.evidence_flags("Nobody At All"), ["nopool"])

    def test_a_season_below_the_fragment_band_still_flags(self):
        """§Durability writes the band as 10-25 to separate a fragment from a
        whole missed season, but a 5-game season is PRESENT in the pool rather
        than absent, so a lower bound silently passes the thinnest rows of all
        """
        self.assertEqual(sim.evidence_flags("Walker Kessler"), ["frag"])


class EvidenceFlagsInThePlayersTable(unittest.TestCase):
    """`rate_evidence` and `evidence_flags` are pinned against the pool by
    `RateEvidence`, but the reader never calls them, he reads `sim.py players`.
    The flag is the only thing on that row saying whether the `Δw` beside it is
    a measurement or an upper bound, and an unflagged row reads as a clean one,
    so a flag computed and not printed, or printed against the wrong row, is
    worse than no flag column at all"""

    @classmethod
    def setUpClass(cls):
        cls.rows = {}
        ours = sim.our_roster()
        for line in render("players").splitlines():
            for p in ours:
                if line.strip().startswith(p["n"] + " ") and p["n"] not in cls.rows:
                    cls.rows[p["n"]] = line

    def test_a_season_missing_from_the_pool_reaches_the_row_it_belongs_to(self):
        """Kyrie and VanVleet are the two on our roster with a whole season
        gone, and exactly the rows whose rate is an upper bound"""
        self.assertIn("miss", self.rows["Kyrie Irving"])
        self.assertIn("miss", self.rows["Fred VanVleet"])

    def test_every_row_prints_the_flags_its_evidence_implies_and_no_others(self):
        """Both ways. Whatever `evidence_flags` names is what his row carries,
        and a row carries nothing it did not earn, so a flag printed against
        the wrong row clears the first half and fails here.

        `rotN` carries the count rather than just a mark, the bar being 3
        seasons at rate >= 15 (`Eval Definitions §Durability`). Below it the
        rate is a role that has not held up yet, at or above it the reader may
        read the row clean"""
        for name, line in self.rows.items():
            with self.subTest(player=name):
                self.assertEqual(
                    re.findall(r"frag|miss|nopool|rot\d", line),
                    sim.evidence_flags(name), line)

    def test_the_table_has_a_row_for_every_player_on_the_roster(self):
        """The agreement above is vacuous for any player the scan missed"""
        self.assertEqual(sorted(self.rows),
                         sorted(p["n"] for p in sim.our_roster()))


def sim_sources():
    """Every python file the sim ships, source glued back across the `print`
    calls and comment lines a wrapped sentence is split over. A citation this
    code PRINTS spans two string literals and one in a comment spans two lines,
    so scanning the raw text checks a sentence nobody reads"""
    paths = [sim.__file__] + sorted(
        glob.glob(os.path.join(sim.HERE, "simlib", "**", "*.py"),
                  recursive=True))
    return {p: re.sub(r"\n\s*#+ ?", " ",
                      re.sub(r'"\)?\s*\n\s*(?:print\()?"', " ", read_text(p)))
            for p in paths}


def doc_sections(path):
    """Every heading in a markdown file, cut at the em-dash gloss -- the form a
    `§` citation names it by"""
    return {re.split(r" +[-—] +",
                     h.replace("`", "").replace("*", ""))[0].strip()
            for h in re.findall(r"^#+ +(.*)$", read_text(path), re.M)}


def eval_docs():
    """{the name a citation writes: path} for every page beside the evals.
    DISCOVERED, not listed: these pages get split and renamed, and a hardcoded
    path is a test that keeps passing while the citation dangles"""
    return {os.path.splitext(os.path.basename(p))[0]: p for p in
            sorted(glob.glob(os.path.join(sim.HERE, os.pardir, "*.md")))}


class DefinitionsVocabulary(unittest.TestCase):
    """The eval pages are cited by section instead of restated, and one of them
    owns the canonical flag table. Both halves only work if the citations
    resolve, since a `§Delta w` that names no section sends the reader looking
    for a definition that is not there, and a flag code printed on a row but
    absent from the table is a vocabulary the rest of the repo cannot carry"""

    LEAGUE = skills_path("league-info", "SKILL.md")
    # One canonical flag row, as the table writes it. Lower-case codes: the
    # column tables on these pages are keyed by upper-case column names, and
    # the two are the same markdown otherwise
    FLAG_ROW = r"^\| `([a-z0-9]\w*)` *\|([^|]*)\|"

    @classmethod
    def setUpClass(cls):
        cls.docs = {name: doc_sections(path)
                    for name, path in eval_docs().items()}
        cls.sources = sim_sources()
        owners = [path for path in eval_docs().values()
                  if len(re.findall(cls.FLAG_ROW, read_text(path), re.M)) > 1]
        assert len(owners) == 1, (
            "%d eval pages carry the canonical flag table: it has one owner "
            "and the codes travel with the row" % len(owners))
        cls.text = read_text(owners[0])

    def cited(self, pattern):
        """{(page cited, section cited): file that cites it}, over every
        source. The page is "" where the citation names none"""
        out = {}
        for path, text in self.sources.items():
            for m in re.findall(pattern, text):
                doc, name = m if isinstance(m, tuple) else ("", m)
                # A citation wraps across lines wherever the sentence does
                doc, name = one_line(doc), one_line(name)
                # `Delta w` and `Delta P(title)` are printed in ASCII by
                # reports that cannot rely on a UTF-8 terminal
                name = name.rstrip(".,:").replace("Delta ", "Δ").replace(
                    "Delta P", "ΔP")
                out[(doc, name)] = os.path.basename(path)
        return out

    def test_every_section_sim_cites_is_a_section_that_exists(self):
        """A citation names its page and runs to the closing backtick rather
        than to the first space, since the pages carry multi-word headings and
        stopping at the space checks a section name nobody wrote. Every
        citation has to be inside the backticks for that to hold, so the two
        counts are compared rather than assumed"""
        cited = self.cited(r"`(Eval [^§`]+)§([^`]+)`")
        self.assertTrue(cited, "nothing cites the eval pages any more")
        for text in self.sources.values():
            self.assertEqual(len(re.findall(r"`Eval [A-Za-z]+ §", text)),
                             len(re.findall(r"Eval [A-Za-z]+ §", text)),
                             "a citation outside backticks is not checked")
        for (doc, name), where in cited.items():
            with self.subTest(page=doc, section=name, file=where):
                self.assertIn(doc, self.docs)
                self.assertIn(name, self.docs[doc])

    def test_a_bare_section_mark_names_a_section_of_a_file_that_owns_one(self):
        """A `§` with no file in front of it is the same citation with the file
        named a sentence earlier, and it goes stale the same way -- so it is
        checked against every file this code cites by section, not skipped for
        being short.

        Section names carry spaces and the sentence carries on past them, so a
        citation resolves when some leading run of its words is a heading"""
        owned = set(doc_sections(self.LEAGUE))
        for sections in self.docs.values():
            owned |= sections
        for (_, name), where in self.cited(r"§([A-Za-z][^`\n]*)").items():
            words, heads = name.split(), set()
            for i in range(len(words)):
                head = " ".join(words[:i + 1])
                heads |= {head, re.sub(r"(?:'s)?[).,:;\"]*$", "", head)}
            with self.subTest(section=name, file=where):
                self.assertTrue(heads & owned, "%s cites no section that "
                                "exists" % name)

    def test_the_flag_legend_and_the_canonical_table_are_the_same_vocabulary(self):
        """Both directions. A code the table prints and `Eval Template` does not
        define cannot be carried into an eval, and a code it sources FROM
        `sim.py players` that this table never prints is a row the eval author
        is told to read off a report that does not emit it"""
        canon = dict(re.findall(r"^\| `(\w+)` *\|([^|]*)\|", self.text, re.M))
        out = render("players")
        legend = set(re.findall(r"`([a-z]\w*)`", out[out.index("flag column"):]))
        self.assertLessEqual(legend, set(canon), legend - set(canon))
        for code, desc in canon.items():
            if "sim.py players" in desc:
                with self.subTest(flag=code):
                    self.assertIn(code, legend)


class UnprojectedRates(unittest.TestCase):
    """`Eval Template.md` says a player the projection feed does not
    carry keeps LAST SEASON's average, which is a different kind of number from
    every other row in the column. Nothing in the rate itself says so, so the
    row has to carry `noproj` or a stale average reads as a projection"""

    UNPROJECTED = {"n": "Chaney Johnson", "tm": "BKN", "avg": 19.1,
                   "tot": 343.0, "gp": 18, "posLabel": "SG/SF",
                   "elig": ["SF", "SG"]}

    def test_a_player_with_no_projection_is_flagged_on_his_row(self):
        path = roster_file(self.UNPROJECTED)
        self.assertIsNone(sim.projected_rate("Chaney Johnson"))
        row, = [l for l in render("players", path).splitlines()
                if "Chaney Johnson" in l]
        self.assertIn("noproj", row)

    def test_a_projected_player_is_not_flagged(self):
        row, = [l for l in render("players").splitlines() if "Josh Giddey" in l]
        self.assertNotIn("noproj", row)

    def test_an_unprojected_rate_is_last_seasons_average_untouched(self):
        """The flag says the rate is last season's, nothing says it still IS. A
        fallback that regressed or part-projected him would be a third kind of
        number in the column with only two labels for it"""
        p, = sim.our_roster(roster_file(self.UNPROJECTED))
        self.assertEqual(p["avg"], self.UNPROJECTED["avg"])


class ProjectionSnapshot(unittest.TestCase):
    """The rate every `Δw` runs on is assembled across two directories and a
    file on disk. `projections` writes a snapshot of someone else's stat lines
    and `sim` joins it by name and scores it under our rules (`Eval Definitions
    §Δw`). Every other test here checks only whether a row was projected AT
    ALL, so the number itself could arrive halved, stale, hand-set or scored as
    one night's line and nothing would print differently"""

    def test_the_rate_on_a_roster_row_is_the_committed_snapshots_line_scored(self):
        stats = {r["name"]: r["stats"]
                 for r in json.loads(read_text(SNAPSHOT))["rows"]}
        scoring = skill_module("projections", "scoring")
        giddey = scoring.rate(scoring.line_from_sleeper(stats["Josh Giddey"]))

        self.assertGreater(giddey, 25)
        self.assertLess(giddey, 60)
        self.assertAlmostEqual(sim.projected_rate("Josh Giddey"), giddey, places=9)
        p = rostered("Josh Giddey")
        self.assertAlmostEqual(p["avg"], giddey, places=6)

    def test_the_join_reaches_essentially_the_whole_roster(self):
        """A join that rots, a normalisation change or a feed re-cut or a moved
        snapshot, puts last season's average back under every row it drops.
        `noproj` makes that visible one row at a time, and only a count makes
        it visible when it happens wholesale"""
        ours = sim.our_roster()
        missing = [p["n"] for p in ours if sim.projected_rate(p["n"]) is None]
        self.assertGreater(len(ours), 20)
        self.assertGreaterEqual(1 - len(missing) / len(ours), 0.93, missing)


class UnusableSnapshot(unittest.TestCase):
    """A snapshot that cannot be read is indistinguishable, row by row, from a
    feed that carries nobody. Every rate falls back to last season's average
    and every row flags `noproj`, which is the whole study re-cut onto the
    basis `projections` exists to replace, and every report but `players`
    prints no flag column at all"""

    def test_a_missing_snapshot_is_refused_rather_than_repricing_everybody(self):
        with projection_snapshot(None):
            with self.assertRaises(RuntimeError) as e:
                sim.our_roster()
        self.assertIn("sleeper-2026.json", str(e.exception))

    def test_a_snapshot_carrying_nobody_is_refused_too(self):
        """It parses, so nothing upstream complains, and a feed re-cut that
        breaks `projected_rows` writes exactly this file. Zero rows is not a
        thin feed, it is no feed"""
        with projection_snapshot(sleeper_rows()):
            with self.assertRaises(RuntimeError):
                sim.our_roster()

    def test_a_feed_that_simply_misses_a_player_still_prices_everyone_else(self):
        """The refusal is about the SNAPSHOT and must not swallow the one case
        that is a fact about a player, a usable feed that does not carry him.
        He keeps last season's average, everybody in the feed is priced off it,
        and only his row says so"""
        with projection_snapshot(sleeper_rows(
                ("Josh Giddey", {"pts": 30.0, "reb": 10.0, "dreb": 7.0,
                                 "ast": 10.0, "stl": 1.0, "blk": 0.5, "to": 3.0,
                                 "fgm": 11.0, "fga": 22.0, "ftm": 5.0,
                                 "fta": 6.0, "tpm": 3.0, "min": 35.0}))):
            priced = {p["n"]: p["avg"] for p in sim.our_roster()}
            self.assertIsNone(sim.projected_rate("Desmond Bane"))
        raw = {p["n"]: p["avg"] for p in sim.our_roster(projected=False)}

        self.assertNotEqual(priced["Josh Giddey"], raw["Josh Giddey"])
        self.assertEqual(priced["Desmond Bane"], raw["Desmond Bane"])


class ProjectedRateReachesTheWinFigure(unittest.TestCase):
    """The snapshot is joined, scored and stapled onto a roster row four files
    away from the thing that consumes it. Every other test here stops at the
    roster row, so a rate that never actually reached the nightly lineup, or a
    GP that moved when the projection did, would read as a clean pass"""

    def _snapshot_with(self, name, stats):
        snap = json.loads(read_text(SNAPSHOT))
        for r in snap["rows"]:
            if r["name"] == name:
                r["stats"] = stats
        return json.dumps(snap)

    def test_projecting_a_starter_up_pays_wins_without_buying_him_games(self):
        best = max(json.loads(read_text(SNAPSHOT))["rows"],
                   key=lambda r: sim.projected_rate(r["name"]) or 0)

        with projection_snapshot(self._snapshot_with("Josh Giddey",
                                                     best["stats"])):
            up = rostered("Josh Giddey")
            up_pf = sim.run(sim.basis(), trials=8)["pf"]
        base = rostered("Josh Giddey")
        base_pf = sim.run(sim.basis(), trials=8)["pf"]

        self.assertGreater(up["avg"], base["avg"] + 5)
        self.assertGreater(up_pf - base_pf, 500)
        self.assertEqual(up["gp"], base["gp"])

        with projection_snapshot(self._snapshot_with(
                "Josh Giddey", {"pts": 3.5, "reb": 1.4, "dreb": 1.0, "ast": 0.8,
                                "stl": 0.2, "blk": 0.1, "to": 0.7, "fgm": 1.4,
                                "fga": 3.8, "ftm": 0.6, "fta": 0.8, "tpm": 0.3,
                                "min": 9.0})):
            down = rostered("Josh Giddey")
        self.assertLess(down["avg"], 15)
        self.assertEqual(down["gp"], base["gp"])


class Durability(unittest.TestCase):
    """Characterisation test rather than a red to green cycle. It pins the
    conclusion the README's durability section rests on, that with
    foreknowledge of who plays GP-elasticity is 1, so the ONLY format-derived
    injury adjustment is the lock-in. If this stops holding, that section has
    to be rewritten"""

    def test_value_is_proportional_to_games_played(self):
        full = sim.our_roster() + sim.EXPANSION
        trials = 200

        def pf(gp):
            roster = [sim.star(45, gp) if p["n"] == "Jalen Suggs" else p for p in full]
            return sim.run(roster, trials=trials)["pf"]

        absent, healthy = pf(0), pf(82)
        for gp in (41, 62):
            retained = (pf(gp) - absent) / (healthy - absent)
            self.assertAlmostEqual(retained, gp / 82, delta=0.02)


class BackfillGrade(unittest.TestCase):
    """Regression pin rather than a red to green cycle. `scenarios` tells the
    reader that `breakevens` reports the bracket out to one named refund grade,
    which is a cross-table claim otherwise held together by two people typing
    the same pair of numbers into two files' worth of prints"""

    def test_the_grade_scenarios_cites_is_a_row_breakevens_actually_reports(self):
        cited, = re.findall(r"bracket to a (\S+) refund", render("scenarios"))
        rows = [l.split()[0] for l in render("breakevens").splitlines() if l.split()]
        self.assertIn(cited, rows)


class ScenarioShapes(unittest.TestCase):
    """`breakevens` states GP and position on every row "because they move the
    answer several points", and `scenarios` states them once above the table
    for the rows whose labels do not. So that sentence carries the whole
    table's worth of the warning, and a reader who takes a bare label at its
    word compares a real 65-GP center against a row priced as a 68-GP forward
    """

    @classmethod
    def setUpClass(cls):
        cls.head = render("scenarios").split("scenario ")[0]

    def test_the_center_rows_are_not_described_as_the_default_forward(self):
        self.assertRegex(self.head, r"Jokic[\s\S]*?65-GP C\b")

    def test_the_multi_body_rows_say_they_are_not_all_the_default_either(self):
        self.assertIn("76", self.head)


class DurabilityHeader(unittest.TestCase):
    """The GP row's header names its subject and quotes his line. `our_roster`
    re-projects both the rate and the GP every time the feed moves, so a line
    typed into the header describes whoever the roster carried the day it was
    typed while the row underneath is measured on today's"""

    def test_the_gp_row_quotes_the_subject_as_the_roster_carries_him(self):
        sub, = [p for p in sim.basis() if p["n"] == durability.SUBJECT]
        self.assertIn("%s (%.1f @ %d)"
                      % (durability.SUBJECT, sub["avg"], sub["gp"]),
                      render("durability"))


class UnsignedPlayer(unittest.TestCase):
    """Most committed rosters hold a player unsigned in the NBA, purely because
    the snapshot is taken in July. Given no schedule at all he suits up for
    nothing and prices as most of a body of `Δw` short, a snapshot artifact
    reading as a finding about the player. He is a body with an unknown
    schedule, which is what `SIM_TM` is for"""

    def test_an_unsigned_body_scores_what_he_would_on_the_assumed_schedule(self):
        """The whole claim in the only terms that matter, a season's PF. A
        floor, "he beats an empty slot", passes on a quarter of a schedule, and
        an rng-draw assertion tests the mechanism rather than the season"""
        base = sim.basis()
        free = {"n": "FREE", "tm": "FA", "avg": 30.0, "tot": 0.0, "gp": 70,
                "posLabel": "F", "elig": ["SF", "PF"]}
        unsigned = sim.run(base + [free], trials=8)["pf"]
        self.assertEqual(unsigned, sim.run(base + [dict(free, tm=sim.SIM_TM)],
                                           trials=8)["pf"])
        self.assertGreater(unsigned,
                           sim.run(base, trials=8)["pf"] + 500)

    def test_a_team_the_schedule_has_never_heard_of_fails(self):
        """The other side of the same boundary. "FA" is a fact the feed states,
        "PHO" is the feed having renamed Phoenix out from under the join, and
        inheriting SIM_TM there prices the body on the DEEPEST light-night
        schedule of the 30 while nothing prints an error"""
        base = sim.basis()
        renamed = {"n": "RENAMED", "tm": "PHO", "avg": 30.0, "tot": 0.0,
                   "gp": 70, "posLabel": "F", "elig": ["SF", "PF"]}
        with self.assertRaises(KeyError) as e:
            sim.run(base + [renamed], trials=1)
        self.assertIn("PHO", str(e.exception))

    def test_the_players_table_says_the_schedule_is_assumed(self):
        """`Δw` on an assumed schedule is not the same claim as `Δw` on his
        own, and nothing else on the row distinguishes them"""
        path = roster_file({"n": "Bradley Beal", "tm": "FA", "avg": 24.0,
                            "tot": 1000.0, "gp": 42, "posLabel": "G",
                            "elig": ["PG", "SG"]},
                           {"n": "Desmond Bane", "tm": "MEM", "avg": 33.0,
                            "tot": 2706.0, "gp": 82, "posLabel": "G",
                            "elig": ["PG", "SG"]})
        out = render("players", path)
        beal, = [l for l in out.splitlines() if "Bradley Beal" in l]
        bane, = [l for l in out.splitlines() if "Desmond Bane" in l]
        self.assertIn("fa", beal.split())
        self.assertNotIn("fa", bane.split())


class Facade(unittest.TestCase):
    """`sim` re-exports, and five names are state a caller REPLACES. A module
    `__getattr__` fires only when normal lookup FAILS, so an assignment on the
    facade creates the very entry that stops it failing, and the write reads
    back fine while reaching nobody inside `simlib`. Reads fixed and writes not
    is the silent-wrong-number shape, pointed the other way"""

    def test_setting_the_roster_on_the_facade_reaches_basis(self):
        self.addCleanup(setattr, roster_mod, "ROSTER", roster_mod.ROSTER)
        sim.ROSTER = THEIR_ROSTER
        self.assertEqual([p["n"] for p in sim.basis()],
                         [p["n"] for p in sim.basis(THEIR_ROSTER)])

    def test_setting_a_name_the_facade_only_re_exports_fails(self):
        """Five names are live state, and the facade re-exports a hundred more,
        every one of them bound here as a reference. An assignment to one of
        those lands in the facade's own dict, reads back the caller's value and
        leaves every reader inside `simlib` on the real one"""
        was = sim.SLOTS
        with self.assertRaises(AttributeError) as e:
            sim.SLOTS = []
        self.assertIs(sim.SLOTS, was)
        self.assertIn("simlib", str(e.exception))

    def test_a_name_the_facade_never_exported_is_settable_more_than_once(self):
        """`ModuleType.__setattr__` writes into the same module dict the
        refusal above asks about, so a name `simlib` has never heard of is
        accepted once and the second assignment comes back "re-exported from
        simlib, not owned here" about it. A guard that mis-states what it is
        guarding sends the reader looking for a `simlib` name that does not
        exist"""
        sim.scratch = 1
        self.addCleanup(delattr, sim, "scratch")
        sim.scratch = 2
        self.assertEqual(sim.scratch, 2)

    def test_replacing_run_on_the_facade_reaches_simlib(self):
        real = engine.run
        self.addCleanup(setattr, engine, "run", real)
        seen = []
        sim.run = lambda roster, **kw: (seen.append(len(roster))
                                        or real(roster, **dict(kw, trials=2)))
        R = flat_R()
        sim.player_wins(sim.basis(), ["Jalen Suggs"], blocks=1, trials=2, R=R)
        self.assertTrue(seen)

    def test_a_star_import_carries_the_five_live_names_and_not_the_plumbing(self):
        """`from sim import *` is what a REPL and a saved snippet do. It copies
        the module DICT, and the five live names are in nobody's dict, they are
        served by `__getattr__`, so `run`, the first line of the documented
        import path, comes out of a star import as a NameError.

        The same dict is why the star can hand back `sys`, `types` and four
        `simlib` module handles, rebinding whatever the caller already had
        under those names"""
        ns = {}
        exec("from sim import *", ns)
        starred = set(ns) - {"__builtins__"}
        self.assertLessEqual({"run", "player_wins", "gp_bootstrap",
                              "PLAYER_BLOCKS", "ROSTER", "basis"}, starred)
        self.assertIs(ns["run"], engine.run)
        self.assertEqual(starred & {"sys", "types", "roster", "value"}, set())


class PlayerBlocksIsOneConstant(unittest.TestCase):
    """`players` prints "averaged over N independent seed blocks" off the
    constant, while `player_wins`, the import path a deal is actually priced
    on, is what runs them. Move the constant and the printed caveat describes a
    measurement nobody ran, on the table `eval-team` quotes"""

    def test_player_wins_takes_its_block_count_from_the_constant(self):
        self.addCleanup(setattr, value, "PLAYER_BLOCKS", value.PLAYER_BLOCKS)
        value.PLAYER_BLOCKS = 2
        R = flat_R()
        w = sim.player_wins(sim.basis(), ["Jalen Suggs"], trials=2, R=R)
        self.assertEqual(len(w["Jalen Suggs"][2]), 2)

    def test_incoming_wins_takes_the_same_one(self):
        self.addCleanup(setattr, value, "PLAYER_BLOCKS", value.PLAYER_BLOCKS)
        value.PLAYER_BLOCKS = 2
        R = flat_R()
        body = sim.star(40.0, 68, ("C",), n="INCOMING")
        w = sim.incoming_wins(sim.basis(), [body], trials=2, R=R)
        self.assertEqual(len(w["INCOMING"][2]), 2)


class BracketWindow(unittest.TestCase):
    """Which periods the bracket is played over. Fleaflicker cannot label R1,
    so it arrives marked `regular` and a window taken off `kinds` is three
    rounds starting a week late. What separates a bracket period from a
    regular one on the wire is that not every team plays"""

    def test_the_wire_flags_fewer_rounds_than_are_actually_played(self):
        """The flags are a floor on the window, never the window. Some periods
        do arrive flagged, so the field reads as usable -- and taking the count
        from it drops R1 and prices a 3-round bracket starting a week late"""
        flagged = {i for i, p in enumerate(sim.PERIODS)
                   if "playoff" in p["kinds"]}
        self.assertTrue(flagged)
        self.assertLess(len(flagged), len(sim.BRACKET))

    def test_it_matches_the_window_league_info_states(self):
        """`league-info` is the verified owner of the bracket's shape and every
        skill reasons from it. A derivation that drifts from the page leaves
        both green and the two disagreeing about which weeks bind"""
        text = one_line(read_text(skills_path("league-info", "SKILL.md")))
        m = re.search(r"Bracket: (\d+) of (\d+) teams, (\d+) rounds, "
                      r"periods (\d+)\W(\d+)\*\*", text)
        self.assertIsNotNone(m, "the skill stopped stating the bracket")
        _, teams, rounds, first, last = (int(g) for g in m.groups())
        self.assertEqual(rounds, len(sim.BRACKET))
        self.assertEqual([first, last],
                         [sim.PERIODS[sim.BRACKET[0]]["ordinal"],
                          sim.PERIODS[sim.BRACKET[-1]]["ordinal"]])
        self.assertEqual(teams, 2 * sim.FULL_FIELD)


class BracketGames(unittest.TestCase):
    """`W20`-`W23` are a rate times a GAME COUNT, so the count is the whole
    column. Four a week for everybody is the assumption these exist to refuse"""

    def test_every_team_game_in_the_window_is_counted_once(self):
        for w, nights in enumerate(sim.BRACKET_NIGHTS):
            with self.subTest(week=w):
                self.assertEqual(
                    sum(sim.bracket_games(t)[w] for t in sim.NBA_TEAMS),
                    sum(len(sim.NIGHTS[n][1]) for n in nights))

    def test_the_weeks_are_not_flat_across_teams(self):
        """The spread is 2-5 in a week, and the last two periods -- the pair
        every seed band plays -- run 6 to 8 games across the 30 teams. A body
        priced at the mean is priced a third of a week wrong at either end"""
        per = {t: sim.bracket_games(t) for t in sim.NBA_TEAMS}
        self.assertEqual((min(min(c) for c in per.values()),
                          max(max(c) for c in per.values())), (2, 5))
        pair = [sum(c[-2:]) for c in per.values()]
        self.assertEqual((min(pair), max(pair)), (6, 8))

    def test_the_nba_schedule_covers_the_whole_window(self):
        """The bracket sits in March and the fantasy season ends before the
        NBA's, so a schedule file cut short leaves a bracket week with no
        nights at all and every W column in it reads 0"""
        for i, nights in zip(sim.BRACKET, sim.BRACKET_NIGHTS):
            with self.subTest(period=sim.PERIODS[i]["ordinal"]):
                self.assertTrue(nights)
                self.assertEqual(sim.NIGHTS[nights[0]][0],
                                 sim.PERIODS[i]["start"])
                self.assertEqual(sim.NIGHTS[nights[-1]][0],
                                 sim.PERIODS[i]["end"])


class SeedBands(unittest.TestCase):
    """Which rounds a seed has to win is the whole of why `Delta P(title)` is
    reported three times. Seeds 1-2 are double-byed into two games; 5-8 play
    four, so a body's bracket weeks are worth twice as many rounds to them"""

    def test_a_consolation_half_in_r1_is_named_where_it_is_read(self):
        """R1's field is read off the period's game count, and two seeds enter
        every round after it, so a period 20 that ever carried a consolation
        half beside the bracket reads as a wider entering band. `_bands`' own
        size assert passes on it and the failure surfaces rounds later as the
        snake draw disagreeing with the bands -- a message about the draw for a
        fact about the wire"""
        was = bracket.PERIODS
        first = dict(was[sim.BRACKET[0]])
        first["games"] = first["games"] * 2
        bracket.PERIODS = was[:sim.BRACKET[0]] + [first]
        try:
            with self.assertRaises(AssertionError) as raised:
                bracket._bands()
        finally:
            bracket.PERIODS = was
        self.assertIn("consolation", str(raised.exception))

    def test_a_band_enters_the_bracket_in_the_period_it_is_seeded_into(self):
        """Checked against the wire: a byed team has no score at all in the
        rounds before its entry, and every team in the band has one in the
        round it enters"""
        for band in sim.BANDS:
            skipped = [sim.PERIODS[i]["ordinal"] for i in sim.BRACKET
                       if i < band.periods[0]]
            entered = sim.PERIODS[band.periods[0]]["ordinal"]
            for t in band.seeds:
                with self.subTest(band=band.label, team=t):
                    self.assertIn(entered, sim.SCORES[t])
                    for o in skipped:
                        self.assertNotIn(o, sim.SCORES[t])

    def test_the_bands_partition_the_field_league_info_states(self):
        text = one_line(read_text(skills_path("league-info", "SKILL.md")))
        field = int(re.search(r"Bracket: (\d+) of \d+ teams", text).group(1))
        seeds = [t for band in sim.BANDS for t in band.seeds]
        self.assertEqual(len(seeds), field)
        self.assertEqual(sorted(seeds), sorted(sim.BRACKET_TEAMS))
        self.assertEqual(len(set(seeds)), field)

    def test_no_team_outside_the_bracket_plays_the_first_round(self):
        """Periods 21-23 run a consolation bracket alongside the playoff one,
        so appearing in one proves nothing. R1 is the one period only bracket
        teams are in, and the four missing from it are the four that missed"""
        first = sim.PERIODS[sim.BRACKET[0]]["ordinal"]
        played = {t for t, s in sim.SCORES.items() if first in s}
        self.assertTrue(played <= set(sim.BRACKET_TEAMS))
        self.assertEqual(played, set(sim.BANDS[-1].seeds))

    def test_every_bracket_round_ends_in_the_final(self):
        """A band's periods are the tail of the window from its entry round.
        `P(title)` is a product over them, each factor conditional on winning
        the one before, so a band that stops short is one that cannot win"""
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertEqual(list(band.periods),
                                 [i for i in sim.BRACKET if i >= band.periods[0]])
                self.assertEqual(band.periods[-1], sim.BRACKET[-1])
        self.assertEqual([len(b.periods) for b in sim.BANDS],
                         sorted(len(b.periods) for b in sim.BANDS))


class TheDraw(unittest.TestCase):
    """Who a seed can meet in a round is structure, not an average. The draw
    splits into two halves and each is climbed worst seed first, so a 1-seed's
    penultimate opponent comes only from its own half and can never be the 2 or
    the 3. Every opponent level in the model is a distribution over that"""

    def test_the_ladders_are_the_pairings_the_league_actually_played(self):
        """Every playoff game of last season's bracket, walked in seed terms:
        each half's climb, the winner carried forward on the wire's own scores,
        and the two survivors meeting in the final. A shape taken from anywhere
        but this is an assumption about who a seed can draw"""
        order, held = bracket._seeded(), []
        for ladder in sim.LADDERS:
            cur = order[ladder[0] - 1]
            for r, i in enumerate(sim.BRACKET[:-1]):
                nxt, o = order[ladder[r + 1] - 1], sim.PERIODS[i]["ordinal"]
                with self.subTest(period=o, seeds=(ladder[r + 1], ladder[:r + 1])):
                    self.assertIn({cur, nxt}, [{a, h} for a, _, h, _
                                               in sim.PERIODS[i]["games"]])
                cur = max((cur, nxt), key=lambda t: sim.SCORES[t][o])
            held.append(cur)
        self.assertIn(set(held),
                      [{a, h} for a, _, h, _
                       in sim.PERIODS[sim.BRACKET[-1]]["games"]])

    def test_every_seed_climbs_in_from_the_round_its_band_enters(self):
        """The ladders and the bands are two readings of one bracket -- the
        seeds a band holds are the seeds that enter where the band does, and a
        ladder that disagrees prices a bye nobody has"""
        entry = {s: sim.BRACKET.index(b.periods[0])
                 for b in sim.BANDS for s in b.slots}
        self.assertEqual(sorted(s for l in sim.LADDERS for s in l),
                         sorted(entry))
        for ladder in sim.LADDERS:
            for k, s in enumerate(ladder):
                with self.subTest(seed=s):
                    self.assertEqual(entry[s], max(0, k - 1))

    def test_the_half_a_seed_cannot_meet_early_is_the_half_it_meets_in_the_final(self):
        """Half the draw is unreachable until the last round and the other half
        is unreachable in it. Priced at the field's mean, every round is played
        against a blend of both -- which is a team no bracket can produce"""
        with cheap_monte_carlo(8):
            last = len(sim.BRACKET) - 1
            for b in sim.BANDS:
                for s in b.slots:
                    early = set().union(*[
                        set(sim.opp_dist(s, w))
                        for w in range(sim.BRACKET.index(b.periods[0]), last)])
                    late = set(sim.opp_dist(s, last))
                    with self.subTest(seed=s):
                        self.assertFalse(early & late)
                        self.assertEqual(len(early | late),
                                         len(sim.BRACKET_TEAMS) - 1)

    def test_the_final_is_played_against_a_survivor_not_against_the_field(self):
        """Whoever you meet in the last round has already won its way through
        its own half, which selects it above the level the field's mean quotes
        -- a final priced at that mean is priced against a team the bracket
        cannot produce"""
        with cheap_monte_carlo(8):
            last = len(sim.BRACKET) - 1
            for b in sim.BANDS:
                for s in b.slots:
                    with self.subTest(seed=s):
                        self.assertGreater(sim.opp_mean(last, s),
                                           sim.opp_mean(last))
                        self.assertAlmostEqual(
                            sum(sim.opp_dist(s, last).values()), 1.0)


class WeekPoints(unittest.TestCase):
    """`W20`-`W23` as `Eval Definitions` defines them: a rate times the games
    that player's NBA team plays inside the period, times the share of the
    season he is projected available for"""

    def test_an_ever_present_body_totals_his_rate_times_his_games_in_it(self):
        body = sim.star(30.0, len(sim.team_nights("MEM")), ("C",), "MEM")
        self.assertEqual(len(sim.week_points(body)), len(sim.BRACKET))
        self.assertAlmostEqual(sum(sim.week_points(body)),
                               30.0 * sum(sim.bracket_games("MEM")))

    def test_a_body_projected_for_half_a_season_scores_half_the_window(self):
        """The column is an EXPECTATION, so the share of the season he is
        projected available is in it: same rate, same NBA schedule, half the
        games and he is worth half the week"""
        tg = len(sim.team_nights("MEM"))
        iron = sim.star(30.0, tg, ("C",), "MEM")
        half = sim.star(30.0, tg // 2, ("C",), "MEM")
        self.assertAlmostEqual(
            sum(sim.week_points(half)) / sum(sim.week_points(iron)),
            (tg // 2) / tg)

    def test_a_gp_above_his_teams_own_game_count_is_capped_at_every_night(self):
        """`season` suits a body up for `min(gp, team games)` nights, so this
        column agrees with the sim only if it caps the same way: a GP over his
        team's game count is a body who plays every night, not one worth more
        than his rate"""
        tg = len(sim.team_nights("MEM"))
        self.assertEqual(sim.week_points(sim.star(30.0, tg + 12, ("C",), "MEM")),
                         sim.week_points(sim.star(30.0, tg, ("C",), "MEM")))

    def test_two_identical_rates_split_on_their_nba_schedules(self):
        """The whole reason the column exists. Same rate, same slot, 8 games in
        the last two rounds against 6, and nothing in a season rate says so"""
        pair = {t: sum(sim.bracket_games(t)[-2:]) for t in sim.NBA_TEAMS}
        deep, thin = max(pair, key=pair.get), min(pair, key=pair.get)
        self.assertGreater(sum(sim.week_points(sim.star(30.0, 68, ("C",), deep))[-2:]),
                           sum(sim.week_points(sim.star(30.0, 68, ("C",), thin))[-2:]))


class MarginSpread(unittest.TestCase):
    """`sigma` is a margin between two weekly scores, and which spreads belong
    inside it depends on what the model has already priced. An opponent the
    draw NAMES carries only its own week-to-week deviation, because its level
    is in `mus`; an opponent drawn unidentified out of the field carries the
    field's level spread on top"""

    def test_a_named_opponent_is_narrower_than_a_drawn_one_by_the_fields_spread(self):
        self.assertLess(sim.MARGIN_CV, sim.FIELD_MARGIN_CV)
        self.assertAlmostEqual(sim.FIELD_MARGIN_CV ** 2 - sim.MARGIN_CV ** 2,
                               sim.FIELD_LEVEL_CV ** 2)

    def test_the_drawn_opponent_carries_the_spread_of_the_field_it_comes_from(self):
        """`reg_mean` draws that opponent from all 11 other teams and the
        bracket's 8 are the top of the league by construction, so their levels
        are a truncated sample of it: last season the whole league's spread was
        twice the seeds'. A regular matchup priced on the seeds' spread is
        priced against a field it is not drawn from"""
        def level_sd(teams):
            rel = [[sim.SCORES[t][sim.PERIODS[i]["ordinal"]]
                    / statistics.mean(sim.SCORES[u][sim.PERIODS[i]["ordinal"]]
                                      for u in teams)
                    for i in sim.REGULAR] for t in teams]
            return statistics.stdev([statistics.mean(v) for v in rel])
        self.assertGreater(level_sd(sorted(sim.SCORES)),
                           level_sd(sim.BRACKET_TEAMS))
        self.assertGreater(sim.FIELD_LEVEL_CV, sim.LEVEL_CV)
        self.assertLess(sim.FIELD_LEVEL_CV, level_sd(sorted(sim.SCORES)))

    def test_the_split_recombines_onto_the_margins_it_was_taken_from(self):
        """Put both sides' level spread and both sides' weekly spread back
        together and it has to land ON the pair margins the eight seeds
        actually scored -- a margin is a difference, so the period mean each
        score was divided by cancels out of it and nothing about the split
        survives into the total. A split that lands short is a split that has
        eaten variance the margin needs, and every `sigma` here is that total"""
        pooled = statistics.stdev(
            [(x - y) / statistics.mean(pf)
             for pf in ([sim.SCORES[t][sim.PERIODS[i]["ordinal"]]
                         for t in sim.BRACKET_TEAMS] for i in sim.REGULAR)
             for x, y in itertools.permutations(pf, 2)])
        both = math.sqrt(2 * (sim.WITHIN_CV ** 2 + sim.LEVEL_CV ** 2))
        self.assertLess(abs(both - pooled) / pooled, 0.01)


class RoundProbability(unittest.TestCase):
    """One bracket round is one week's PF against the opponents that round can
    produce, so the model is a normal CDF on a margin mixed over the draw. What
    it is fitted to is the argument"""

    def test_a_better_week_wins_more_often(self):
        p = [sim.round_pwin(mu, 0, sim.BANDS[-1].slots[0])
             for mu in (1000.0, 1400.0, 1600.0, 2200.0)]
        self.assertEqual(p, sorted(p))
        self.assertTrue(all(0.0 < x < 1.0 for x in p), p)

    def test_a_week_at_the_opponents_level_is_a_coin_flip(self):
        """R1 is the one round nobody has survived into, so its opponent is a
        named team rather than a mixture and the margin is readable straight
        off `mus`. Every later round mixes, and a week at the mixture's mean
        is not a coin flip -- the mixture is what makes it not one"""
        seed = sim.BANDS[-1].slots[0]
        opp, = sim.opp_dist(seed, 0)
        self.assertAlmostEqual(sim.round_pwin(opp.mus[0], 0, seed), 0.5)

    def test_the_opponent_level_is_measured_for_the_week_it_is_played_in(self):
        """Periods run 28-56 NBA games and the bracket's four are all at the
        dense end, so an opponent quoted at the season mean is quoted for a
        week nobody plays. Which of the four is heaviest is the FIELD's own
        schedules, not the league-wide game count -- the two disagree here"""
        with cheap_monte_carlo(8):
            levels = [sim.opp_mean(w) for w in range(len(sim.BRACKET))]
            self.assertGreater(min(levels), sim.reg_mean())
        self.assertEqual(len(set(levels)), len(levels))

    def test_the_opponent_is_a_seed_rather_than_an_average_team(self):
        """A playoff opponent is one of the eight. Priced off all 12 the bar
        carries a team nobody can meet in the bracket, which lowers it in
        every round"""
        with cheap_monte_carlo(8):
            for w, i in enumerate(sim.BRACKET):
                whole = statistics.mean(t.mus[w] for t in sim.league())
                with self.subTest(period=sim.PERIODS[i]["ordinal"]):
                    self.assertGreater(sim.opp_mean(w), whole)

    def test_sigma_scales_with_the_level_it_is_measured_against(self):
        """A margin sd is a dispersion around a weekly level, so a denser week
        carries a proportionally wider one. Held flat, the densest bracket week
        reads as the most certain"""
        cv = [sim.sigma(w) / sim.field_mean(w) for w in range(len(sim.BRACKET))]
        for c in cv:
            self.assertAlmostEqual(c, cv[0])
        self.assertGreater(sim.sigma(max(range(len(sim.BRACKET)),
                                         key=sim.field_mean)),
                           sim.sigma(min(range(len(sim.BRACKET)),
                                         key=sim.field_mean)))

    def test_sigma_is_the_same_for_every_team_in_the_draw(self):
        """Every game in the bracket is priced with it, including the ones
        deciding who a later opponent is. Scaled off the field LESS the loaded
        roster, the eight seeds would each be running a bracket of their own"""
        was = roster_mod.ROSTER
        try:
            with cheap_monte_carlo(8):
                mine = [sim.sigma(w) for w in range(len(sim.BRACKET))]
                roster_mod.ROSTER = THEIR_ROSTER
                self.assertEqual([sim.sigma(w) for w in range(len(sim.BRACKET))],
                                 mine)
        finally:
            roster_mod.ROSTER = was


class MatchedBasis(unittest.TestCase):
    """`mu_us` and `mu_opp` are the SAME measurement of two rosters -- every
    team's file through this sim's own pipeline. Anything else prices a margin
    between two quantities that differ by more than the rosters do, and the
    difference lands in `P(round)` as an edge nobody has"""

    def test_inflating_every_teams_rates_leaves_every_band_where_it_was(self):
        """The property the matched basis IS. A league-wide 10% is a rescaling
        of the whole board, not an edge: our week grows and so does every
        opponent's, so no published figure may move. An opponent level taken
        off anything but this pipeline reads the inflation as an edge and books
        it.

        It does not cancel EXACTLY. `league_rates` reaches a rate through
        `projected_rate`, and the bodies `pad` tops each roster up to 38 with
        carry fixed grades no rate feed serves, so a team holding more real
        bodies rescales harder. Measured at 0.008 of a `P(title)`, which is
        what this tolerance sits just above: a bound on that leak, not slack.

        On BANDS rather than on single rounds, because a band averages over its
        four seeds. One round from one seed is one slot of the draw, and the
        7th and 8th projected seeds are 0.3% of a season apart -- they trade
        places under a re-run, which re-points that slot at a different team"""
        with cheap_monte_carlo(8):
            mus = sim.bracket_weeks(sim.basis())
            base = [sim.title_prob(mus, b) for b in sim.BANDS]
            with league_rates(1.10):
                mus = sim.bracket_weeks(sim.basis())
                got = [sim.title_prob(mus, b) for b in sim.BANDS]
        for b, was, now in zip(sim.BANDS, base, got):
            with self.subTest(band=b.label):
                self.assertAlmostEqual(was, now, delta=0.012)

    def test_the_field_is_the_top_eight_projected_teams(self):
        """Which teams seed next season is unknown, so the field is the rule
        stated in `method.md`: the league sorted on projected season PF, cut at
        the bracket's own size"""
        with cheap_monte_carlo(8):
            league, field = sim.league(), sim.field()
        self.assertEqual(len(field), len(sim.BRACKET_TEAMS))
        self.assertEqual(list(field), list(league)[:len(field)])
        self.assertGreater(min(t.pf for t in field),
                           max(t.pf for t in league[len(field):]))

    def test_a_team_is_never_its_own_opponent(self):
        """We are the strongest projected roster, so leaving ourselves in the
        field pulls the bar we are measured against up toward us and shrinks
        the edge by an eighth of it"""
        with cheap_monte_carlo(8):
            field = sim.field()
            ours = [t for t in field
                    if t.path == os.path.basename(roster_mod.ROSTER)]
            self.assertTrue(ours, "our own roster is not a projected seed")
            for w in range(len(sim.BRACKET)):
                with self.subTest(round=w):
                    self.assertAlmostEqual(
                        sim.opp_mean(w),
                        statistics.mean(t.mus[w] for t in field
                                        if t not in ours))

    def test_last_seasons_roster_files_are_not_a_second_league(self):
        """`fetch_data.py roster` writes `roster-<id>-<season>.json` and leaves
        the previous season's beside it, so the roll puts 24 files in the
        directory. Read season-blind the league is 24 teams, one franchise can
        take two seats in `field()`, and the bracket that comes out is a draw
        nobody plays -- with no short-field guard to trip"""
        stale = os.path.join(sim.HERE, "roster-161025-2020-21.json")
        with open(stale, "w") as f:
            f.write(read_text(os.path.join(sim.HERE, roster_mod.ROSTER)))
        try:
            with cheap_monte_carlo(4):
                teams = json.loads(read_text(os.path.join(
                    sim.HERE, "teams-%s.json" % fetch_data.SEASON_TAG)))
                self.assertEqual(len(sim.league()), len(teams))
        finally:
            os.remove(stale)

    def test_a_roster_priced_by_path_is_left_out_of_its_own_field(self):
        """`basis(path)` reads a file without moving the module global, so the
        import path in `sim.py`'s module docstring hands a counterparty's
        roster to a bracket that still believes ours is loaded: the
        counterparty is seeded against a clone of itself and the one seed it
        could never avoid drops out of the draw. Whose roster it is comes in as
        an argument here, the way every other import entry point takes it"""
        with cheap_monte_carlo(8):
            for t in sim.field():
                with self.subTest(team=t.path):
                    self.assertNotIn(t.path,
                                     [o.path for o in sim.opponents(t.path)])

    def test_a_stronger_roster_wins_more_rounds_than_a_weaker_one(self):
        """End to end: the only thing left between two teams' `P(round)` is
        the rosters, which is what the whole model is for"""
        seed = sim.BANDS[-1].slots[0]
        with cheap_monte_carlo(8):
            best, worst = sim.league()[0], sim.league()[-1]
            for w in range(len(sim.BRACKET)):
                with self.subTest(round=w):
                    self.assertGreater(sim.round_pwin(best.mus[w], w, seed),
                                       sim.round_pwin(worst.mus[w], w, seed))


class BracketWeeks(unittest.TestCase):
    """`mu_us` for a round is one week of the same sim every other figure here
    comes out of -- optimal nightly lineups, projected GP -- scored over that
    week's NBA nights and no others"""

    def test_a_week_scores_that_weeks_nights_and_no_others(self):
        """An ironman on one NBA team scores his rate once per team game in
        the period. Anything else and the run is bucketing the wrong nights"""
        body = sim.star(30.0, 82, ("C",), "MEM", "IRON")
        self.assertEqual([round(x, 6) for x in sim.bracket_weeks([body], trials=2)],
                         [30.0 * g for g in sim.bracket_games("MEM")])

    def test_the_last_three_rounds_score_nothing_toward_the_standings(self):
        """Periods 21-23 are outside `SCORED`, so a run on the standings basis
        never reaches them at all"""
        for i in sim.BRACKET[1:]:
            for n in sim.period_nights(i):
                with self.subTest(night=sim.NIGHTS[n][0]):
                    self.assertIsNone(sim.WEEK_OF[n])
                    self.assertIsNotNone(sim.BRACKET_CAL.week_of[n])

    def test_swapping_a_body_for_its_own_twin_moves_nothing(self):
        """Common random numbers, in the bracket path too. Without them the
        two rosters draw different availability and a no-op swap prints a
        `Delta P(title)` several times what a real one is worth"""
        full = sim.basis()
        p = sim.our_roster()[0]
        twin = sim.star(p["avg"], p["gp"], p["elig"], p["tm"], "TWIN")
        self.assertEqual(sim.bracket_weeks(full, trials=8),
                         sim.bracket_weeks(sim.swap(full, [p["n"]], [twin]),
                                           trials=8))


class TitleProbability(unittest.TestCase):
    """`Delta P(title)`: the same counterfactual `Delta w` uses, priced in the
    only currency the bracket pays in (`Eval Definitions`). Reported under
    every seed band, because which rounds bind is what the answer turns on"""

    def test_exactly_one_of_the_eight_seeds_wins_the_title(self):
        """The whole draw at once: each projected seed priced from its own
        slot, against the survivors of the parts of the bracket it is not in.
        Those eight are one bracket's outcomes and have to sum to 1. Priced
        against the field's MEAN instead, each seed is measured in a bracket of
        its own and the eight sum to whatever they sum to"""
        with cheap_monte_carlo(8):
            total = sum(sim.seed_title(t.mus, k + 1, path=t.path)
                        for k, t in enumerate(sim.field()))
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_a_starter_is_worth_more_than_the_body_that_replaces_him(self):
        full = sim.basis()
        with cheap_monte_carlo(20):
            got, = sim.player_title(full, ["Jalen Suggs"], blocks=2).values()
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                mean, sd, blocks = got[band.label]
                self.assertGreater(mean, 0.0)
                self.assertLess(mean, 1.0)
                self.assertEqual(len(blocks), 2)
                self.assertGreater(sd, 0.0)

    def test_he_is_priced_against_a_replacement_of_his_own_slot_group(self):
        """The counterfactual is the whole meaning of the number (`Eval
        Definitions §Δw`). A center priced against a forward's R is the
        single-R error, applied to the column a bracket-week call reads"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            R = sim.group_replacement(full)
            base = sim.bracket_weeks(full)
            own = sim.bracket_weeks(sim.swap(
                full, ["Jakob Poeltl"], [sim.group_body("center", R["center"])]))
            forward = sim.bracket_weeks(sim.swap(
                full, ["Jakob Poeltl"], [sim.group_body("forward", R["forward"])]))
            got, = sim.player_title(full, ["Jakob Poeltl"], blocks=1,
                                    R=R).values()
            # Priced inside the block: `title_prob` reads the league's own sim
            # for the opponent level, so it is a measurement at these trials
            want = {b.label: sim.title_prob(base, b) - sim.title_prob(own, b)
                    for b in sim.BANDS}
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertAlmostEqual(got[band.label][0], want[band.label],
                                       places=9)
        self.assertNotEqual(own, forward, "this roster cannot tell the two "
                            "counterfactuals apart -- pick another player")

    def test_a_side_of_a_deal_is_priced_in_one_joint_run(self):
        """`Eval Definitions §ΔP(title)` gives a multi-piece side one joint
        run and forbids added rows, and `Delta w` has `incoming_wins` for
        exactly that. Where the two paths overlap -- a change of ONE body --
        they are the same measurement on the same blocks and have to agree to
        the digit, which is what makes the joint number readable against the
        per-player column above it"""
        with cheap_monte_carlo(8):
            full, R = sim.basis(), flat_R()
            name = sim.our_roster()[0]["n"]
            body, = [p for p in full if p["n"] == name]
            without = sim.swap(full, [name],
                               [sim.group_body(sim.slot_group(body["elig"]),
                                               R[sim.slot_group(body["elig"])])])
            row, = sim.player_title(full, [name], blocks=2, R=R).values()
            joint = sim.roster_title(full, without, blocks=2)
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertEqual(joint[band.label], row[band.label])

    def test_the_import_path_prices_a_counterparty_as_the_cli_does(self):
        """The two documented ways to price a counterparty's bracket week --
        `--roster their.json playoffs` and `sim.player_title(sim.basis(
        "their.json"), names)` (`sim.py` module docstring, `trades` step 5) --
        are about the same team and have to answer the same. Left to read the
        module global the import path seeds a projected 2-seed against a
        bracket that still contains it, drops the one seed it could not avoid,
        and prints that under the counterparty's name"""
        theirs = "roster-161018-2025-26.json"
        with cheap_monte_carlo(8):
            full = sim.basis(theirs)
            name = sim.our_roster(theirs)[0]["n"]
            got, = sim.player_title(full, [name], blocks=1, R=flat_R(),
                                    path=theirs).values()
            was = roster_mod.ROSTER
            try:
                roster_mod.ROSTER = theirs
                cli_side, = sim.player_title(full, [name], blocks=1,
                                             R=flat_R()).values()
            finally:
                roster_mod.ROSTER = was
            ours_loaded, = sim.player_title(full, [name], blocks=1,
                                            R=flat_R()).values()
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertEqual(got[band.label], cli_side[band.label])
        self.assertNotEqual(got, ours_loaded, "this counterparty is priced the "
                            "same either way -- pick one inside the field")

    def test_a_name_not_on_the_roster_is_refused(self):
        with cheap_monte_carlo(4, blocks=1):
            with self.assertRaises(KeyError):
                sim.player_title(sim.basis(), ["Nobody At All"], blocks=1,
                                 R=flat_R())


class OneDraw(unittest.TestCase):
    """`P(title)`, `by seed` and the multiplier are single UNPAIRED draws of
    twelve rosters. Nothing in them cancels the way the `Delta P` column's
    paired blocks do, so measuring their spread means re-drawing the whole
    basis -- ours and the field's -- on one seed at a time"""

    def test_the_draw_the_report_publishes_is_the_one_its_own_seed_gives(self):
        """The published figures come off `bracket.SEED0` and the error bar off
        re-draws of the same thing. A re-draw that lands somewhere else on that
        seed is measuring the spread of a bracket nobody published"""
        pinned = {t.path: t.mus for t in bracket.league()}
        with bracket.draw(bracket.SEED0):
            self.assertEqual({t.path: t.mus for t in bracket.league()}, pinned)

    def test_a_re_draw_moves_the_field_and_not_only_the_loaded_roster(self):
        """`sigma`, `field_mean` and every opponent level are the field's own
        weeks. Re-drawing ours against a pinned field prices each round against
        a draw it was not scored on, and books the loaded roster's noise as the
        whole error"""
        pinned = {t.path: t.mus for t in bracket.league()}
        with bracket.draw(bracket.SEED0 + engine.TRIALS):
            moved = {t.path: t.mus for t in bracket.league()}
        self.assertEqual(set(moved), set(pinned))
        for path in sorted(pinned):
            with self.subTest(team=path):
                self.assertNotEqual(moved[path], pinned[path])

    def test_the_field_is_back_on_its_own_draw_afterwards(self):
        """Every other report in the run reads `league()` too"""
        pinned = {t.path: t.mus for t in bracket.league()}
        with bracket.draw(bracket.SEED0 + engine.TRIALS):
            pass
        self.assertEqual({t.path: t.mus for t in bracket.league()}, pinned)


class WeeksReport(unittest.TestCase):
    """`W20`-`W23` alone, for any roster. A rate times NBA games times a GP
    share is arithmetic off the roster file and the schedule, so the columns
    every team eval carries must not cost a bracket Monte Carlo to print"""

    ROW = re.compile(r"^  (\S.*?)" + r" +(\d+/\d+|-)" * 4 + r" *(.*)$", re.M)

    def test_it_prices_a_bracket_week_without_running_the_monte_carlo(self):
        """The whole reason it is a separate report. `playoffs` costs ~350
        simulated seasons for the same four columns, and eleven of twelve evals
        want only the columns"""
        with mock.patch.object(sim.engine, "run",
                               side_effect=AssertionError("ran the sim")):
            out = render("weeks")
        self.assertIn("W20", out)

    def test_every_rostered_player_gets_a_cell_per_bracket_round(self):
        out = render("weeks")
        rows = {m[0]: m[1:] for m in self.ROW.findall(out)}
        ours = sim.our_roster()
        self.assertEqual(set(rows), {p["n"] for p in ours}, out)
        for p in ours:
            if sim.unsigned(p["tm"]) or sim.projected_rate(p["n"]) is None:
                continue
            with self.subTest(player=p["n"]):
                for w, pts in enumerate(sim.week_points(p)):
                    self.assertEqual(rows[p["n"]][w], "%.0f/%d"
                                     % (pts, sim.bracket_games(p["tm"])[w]))

    def test_it_answers_about_a_counterparty(self):
        out = render("weeks", ROOKIE_ROSTER)
        self.assertEqual(
            {m[0] for m in self.ROW.findall(out)},
            {p["n"] for p in sim.our_roster(ROOKIE_ROSTER)}, out)


class PlayoffsReport(unittest.TestCase):
    """The report `Eval Definitions §ΔP(title)`, `eval-team` and `trades` all
    send a reader to. It answers about any team -- the opponent distribution is
    the league's, not our weekly scores -- so `--roster` has to serve it"""

    ROW = re.compile(r"^  (\S.*?) +(\S+) +(\S+) +(\S+) +(\S+)"
                     + r" +([-+][\d.]+) +\+-([\d.]+)" * 3 + r" *(.*)$", re.M)

    def test_every_player_gets_a_week_column_per_round_and_a_band_per_seed(self):
        out = render("playoffs")
        rows = {m[0]: m[1:] for m in self.ROW.findall(out)}
        ours = sim.our_roster()
        self.assertEqual(set(rows), {p["n"] for p in ours}, out)
        for i in sim.BRACKET:
            self.assertIn("W%d" % sim.PERIODS[i]["ordinal"], out)
        for band in sim.BANDS:
            self.assertIn(band.label, out)
        for p in ours:
            if sim.unsigned(p["tm"]) or sim.projected_rate(p["n"]) is None:
                continue
            with self.subTest(player=p["n"]):
                for w, pts in enumerate(sim.week_points(p)):
                    cell = rows[p["n"]][w]
                    self.assertEqual(cell, "%.0f/%d"
                                     % (pts, sim.bracket_games(p["tm"])[w]))

    def test_the_legend_above_it_states_the_unit_of_its_own_table(self):
        """One legend prints above every report and it is the first thing a
        reader meets. Wins, scored-period PF and a per-game rate are the other
        thirteen tables' units and none of the three is a column here -- so the
        one report whose standing rule is that its number is never read in wins
        opened by defining wins, and never named percentage points of a title
        at all"""
        legend = one_line("\n".join(render("playoffs").splitlines()[:2]))
        self.assertTrue(legend.startswith("units:"), legend)
        self.assertNotIn("wins", legend)
        self.assertIn("percentage points of title probability", legend)

    def test_the_projected_field_names_its_teams(self):
        """The one table here that ranks the whole league listed twelve file
        names. Which of them is the counterparty under discussion, and which is
        us, was a question only the `team-info` skill could answer"""
        out = render("playoffs")
        teams = json.loads(read_text(
            os.path.join(sim.HERE, "teams-%s.json" % fetch_data.SEASON_TAG)))
        for name in teams.values():
            self.assertIn(name, out)

    def test_a_body_with_no_nba_schedule_prints_no_week_columns(self):
        """`fa` runs on the sim's synthetic schedule so its `Delta w` exists,
        but `W20`-`W23` are that player's own games and he has none (`Eval
        Definitions §Columns`). Printing LAC's is a fact about the fetch date
        published as a fact about the player"""
        path = roster_file(
            {"n": "Nobody Signed", "tm": sim.UNSIGNED, "avg": 30.0, "tot": 0.0,
             "gp": 60, "posLabel": "C", "elig": ["C"]},
            {"n": "Victor Wembanyama", "tm": "SAS", "avg": 50.0, "tot": 0.0,
             "gp": 60, "posLabel": "C", "elig": ["C"]})
        rows = dict((m[0], m[1:]) for m in self.ROW.findall(render("playoffs", path)))
        self.assertEqual(list(rows["Nobody Signed"][:len(sim.BRACKET)]),
                         ["-"] * len(sim.BRACKET))
        self.assertNotIn("-", rows["Victor Wembanyama"][:len(sim.BRACKET)])

    def test_a_row_with_no_week_columns_carries_the_flag_that_explains_them(self):
        """Every body on the roster is priced for `Delta P(title)`, including
        one with no NBA team, so a row can print four blank W columns beside a
        percentage point of a title -- which reads as a player worth that while
        playing no bracket games. `players` answers it with the same `fa` and
        `noproj` (`Eval Template §Flags`), and the blanks are unreadable without
        them"""
        path = roster_file(
            {"n": "Nobody Signed", "tm": sim.UNSIGNED, "avg": 30.0, "tot": 0.0,
             "gp": 60, "posLabel": "C", "elig": ["C"]},
            {"n": "Victor Wembanyama", "tm": "SAS", "avg": 50.0, "tot": 0.0,
             "gp": 60, "posLabel": "C", "elig": ["C"]})
        rows = dict((m[0], m[1:]) for m in self.ROW.findall(render("playoffs", path)))
        self.assertIn("fa", rows["Nobody Signed"][-1].split())
        self.assertEqual(rows["Victor Wembanyama"][-1], "")

    def test_the_sigma_bound_is_taken_off_the_title_ladder_alone(self):
        """Single elimination: 8 seeds play 7 games for the title, and the 8th
        seeded pairing in those periods is two ELIMINATED seeds playing for
        third. Both-sides-seeded separated last season's tanked games only
        because every one of those happened to draw a non-seed, and a draw that
        pairs two eliminated seeds puts a game neither is trying to win inside
        the margin sd this bound is printed from"""
        out = render("playoffs")
        n, = re.findall(r"The (\d+) bracket games actually played", out)
        self.assertEqual(int(n), len(sim.BRACKET_TEAMS) - 1)

    ROUND = re.compile(
        r"^ +(\d+-\d+) +(W\d+) +(\d+) +(\d+) +(\d+) +(\d+) +(\d+) +([\d.]+)$",
        re.M)

    def test_the_basis_footer_states_what_the_probabilities_were_built_on(self):
        """A `P(round)` is only readable against the opponent level and the
        margin sd behind it, so every round of every band prints all three and
        the printed probability is the one they imply -- a footer describing
        some other run is worse than none.

        Not to the last digit: `P(round)` mixes `Phi` over the opponents the
        draw can produce and `mu_opp` is that mixture's MEAN, so the two differ
        by the curvature of `Phi` across it. That gap is what the tolerance
        here bounds"""
        out = render("playoffs")
        rows = self.ROUND.findall(out)
        self.assertEqual(
            [(r[0], r[1]) for r in rows],
            [(b.label, "W%d" % sim.PERIODS[i]["ordinal"])
             for b in sim.BANDS for i in b.periods], out)
        for band, label, _, mu_us, mu_opp, _, sd, p in rows:
            with self.subTest(band=band, round=label):
                z = (float(mu_us) - float(mu_opp)) / float(sd)
                self.assertAlmostEqual(float(p),
                                       0.5 * (1 + math.erf(z / math.sqrt(2))),
                                       delta=0.015)
        self.assertIn("x a regular-season game", out)

    def test_the_footer_names_every_team_the_opponent_level_is_measured_on(self):
        """`mu_opp` is 11 other roster files run through this same sim, and
        which teams those are is the whole basis. A level with no field under
        it is unauditable -- and the reader has to see the loaded team excluded
        from the bar it is measured against"""
        out = render("playoffs")
        for path in committed_rosters():
            with self.subTest(team=os.path.basename(path)):
                self.assertIn(os.path.basename(path), out)
        marked, = [l for l in out.splitlines() if "<- loaded" in l]
        self.assertIn(os.path.basename(roster_mod.ROSTER), marked)

    def test_each_band_carries_its_own_error_bar(self):
        """One `+-` per row cannot serve three bands. All three are transforms
        of ONE simulated week, so they move together: the widest band's noise
        is not the middle one's, and a reader comparing two bands is reading
        the number he was given against a spread nothing measured"""
        with cheap_monte_carlo():
            out = render("playoffs")
            name = sim.our_roster()[0]["n"]
            full = sim.basis()
            got, = sim.player_title(full, [name],
                                    R=sim.group_replacement(full)).values()
        row, = [m for m in self.ROW.findall(out) if m[0] == name]
        for k, band in enumerate(sim.BANDS):
            mean, sd, blocks = got[band.label]
            with self.subTest(band=band.label):
                self.assertAlmostEqual(float(row[5 + 2 * k]), 100 * mean,
                                       places=2)
                self.assertAlmostEqual(float(row[6 + 2 * k]),
                                       100 * sim.se_mean(blocks), places=2)

    def test_the_error_bar_it_publishes_is_measured_on_enough_blocks(self):
        """An sd on 2 dof carries ~50% of itself as error -- published, it
        reads as a measurement of a spread nobody measured. The row's own
        blocks are what it is computed from, so the count printed above the
        table is the count that ran"""
        out = render("playoffs")
        self.assertGreaterEqual(bracket.TITLE_BLOCKS - 1, 5)
        self.assertIn("averaged over %d shared" % bracket.TITLE_BLOCKS, out)
        with cheap_monte_carlo(4):
            full = sim.basis()
            got, = sim.player_title(full, [sim.our_roster()[0]["n"]],
                                    R=flat_R()).values()
        self.assertEqual(len(got[sim.BANDS[0].label][2]), bracket.TITLE_BLOCKS)

    SUMMARY = re.compile(r"^ +(\d+-\d+) +([\d.]+) +\+-([\d.]+)"
                         r" +([\d.]+)-([\d.]+) +\+-([\d.]+)"
                         r" +(\d+) +([\d.]+) \+-([\d.]+) \(", re.M)

    def test_the_unpaired_band_figures_carry_an_error_bar_too(self):
        """These three sit directly under a table whose every `Delta P` row
        carries a `+-`, and they are the ones that need it most: a `Delta P` is
        a paired difference at matched seeds and the opponent noise cancels out
        of it, while `P(title)` is one unpaired draw of twelve rosters. Bolded
        into `findings.md` bare, they read as the tighter of the two"""
        rows = self.SUMMARY.findall(render("playoffs"))
        self.assertEqual([r[0] for r in rows], [b.label for b in sim.BANDS])
        for row in rows:
            with self.subTest(band=row[0]):
                for k, what in ((2, "P(title)"), (5, "by seed"),
                                (8, "the multiplier")):
                    self.assertGreater(float(row[k]), 0,
                                       "%s printed a bar nothing measured"
                                       % what)

    def test_what_it_publishes_is_the_draw_the_basis_above_it_states(self):
        """The bar is measured by re-drawing the whole basis, and the figure
        beside it stays the draw the `mu_us` and `sigma` rows above were printed
        from -- a block mean there would describe a bracket no row on the page
        was built on"""
        out = render("playoffs")
        with cheap_monte_carlo():
            mus = sim.bracket_weeks(sim.basis(), seed0=bracket.SEED0)
            want = [sim.title_prob(mus, b) for b in sim.BANDS]
        for row, band, p in zip(self.SUMMARY.findall(out), sim.BANDS, want):
            with self.subTest(band=band.label):
                self.assertAlmostEqual(float(row[1]), p, places=3)

    def test_the_week_headers_sit_over_the_columns_they_name(self):
        """The four rounds are not interchangeable -- a 1-2 seed never plays
        W20 at all -- so a header shifted or reordered off its own data prints
        one period's points under another's name, and the reader books a
        bracket week the player does not have"""
        lines = render("playoffs").splitlines()
        head, = [l for l in lines if l.strip().startswith("player")]
        row = next(l for l in lines[lines.index(head) + 1:]
                   if len(re.findall(r"\d+/\d+", l)) == len(sim.BRACKET))
        at = 0
        for i in sim.BRACKET:
            col = "W%d" % sim.PERIODS[i]["ordinal"]
            with self.subTest(column=col):
                at = re.compile(r"\d+/\d+").search(row, at).end()
                self.assertEqual(re.search(r"\b%s\b" % col, head).end(), at,
                                 "`%s` does not end over its own column:\n%s\n%s"
                                 % (col, head, row))

    def test_the_rows_are_ordered_on_the_band_the_preamble_names(self):
        """28 rows is a list a reader reads the top of. The three bands
        disagree about the order -- which of two bodies matters more depends on
        how many rounds you have to win -- so an order taken off one band and
        announced as another's is a ranking of a question nobody asked"""
        out = render("playoffs")
        self.assertIn("Sorted on the %s band." % sim.BANDS[0].label,
                      one_line(out))
        col = [float(m[5]) for m in self.ROW.findall(out)]
        self.assertEqual(col, sorted(col, reverse=True))

    REG = re.compile(r"^ +reg +([\d.]+) +(\d+) +(\d+) +(\d+) +(\d+) +([\d.]+)"
                     r"  <- one regular period$", re.M)

    def test_the_sigma_column_is_the_level_times_the_spread_the_prose_names(self):
        """Two different opponents are priced on this table. A bracket round
        NAMES both teams, so their levels are in `mu_us` and `mu_opp` already
        and only the week-to-week deviation is left; the `reg` row -- the
        denominator the multiplier beside it divides by -- draws its opponent
        unidentified out of the league and carries that field's level spread on
        top. One spread for both prices a regular season's uncertainty into a
        bracket game, and the multiplier moves with it"""
        out = render("playoffs")
        self.assertIn("%.4f of the level" % sim.MARGIN_CV, out)
        self.assertIn("%.4f. Both off last season's wire" % sim.FIELD_MARGIN_CV,
                      out)
        for band, label, _, _, _, field, sd, _ in self.ROUND.findall(out):
            with self.subTest(band=band, round=label):
                self.assertAlmostEqual(float(sd),
                                       sim.MARGIN_CV * float(field), delta=1.0)
        reg, = self.REG.findall(out)
        _, mu_us, mu_opp, field, sd, p = (float(x) for x in reg)
        self.assertEqual(mu_opp, field, "the drawn opponent is the field's own "
                         "mean, not a survivor above it")
        self.assertAlmostEqual(sd, sim.FIELD_MARGIN_CV * field, delta=1.0)
        z = (mu_us - mu_opp) / sd
        self.assertAlmostEqual(p, 0.5 * (1 + math.erf(z / math.sqrt(2))),
                               delta=0.005)

    BAND = re.compile(r"^ +(\d+-\d+) +([\d.]+) +\+-[\d.]+"
                      r" +([\d.]+)-([\d.]+) +\+-[\d.]+ +(\d+)"
                      r" +([\d.]+) \+-[\d.]+ \(([\d.]+)-([\d.]+) by round\)$",
                      re.M)

    def test_each_band_figure_sits_inside_the_spread_printed_beside_it(self):
        """A band is a SEED RANGE and the figure is the mean over it, so both
        headlines are quoted with the spread they were averaged from and have
        to sit inside it. A headline outside its own range is averaging a
        different set of seeds or rounds from the one the range describes --
        and the range is the column a decision that turns on WHICH seed is
        told to read instead"""
        rows = self.BAND.findall(render("playoffs"))
        self.assertEqual([r[0] for r in rows], [b.label for b in sim.BANDS])
        for row, band in zip(rows, sim.BANDS):
            p, lo, hi, rounds, mult, mlo, mhi = (float(x) for x in row[1:])
            with self.subTest(band=band.label):
                self.assertEqual(rounds, len(band.periods))
                self.assertLessEqual(lo, hi)
                self.assertLessEqual(mlo, mhi)
                # Each end is printed to the headline's own precision, so a
                # tie sits within one rounded step of it.
                self.assertTrue(lo - 0.0005 <= p <= hi + 0.0005,
                                "P(title) %.3f is outside its own %.3f-%.3f"
                                % (p, lo, hi))
                self.assertTrue(mlo - 0.05 <= mult <= mhi + 0.05,
                                "the multiplier %.1f is outside its own "
                                "%.1f-%.1f by round" % (mult, mlo, mhi))

    SENSITIVITY = re.compile(
        r"sigma sensitivity\. The \d+ bracket games actually played give a "
        r"margin sd of (\d+) against the (\d+)-(\d+) above; at that sigma the "
        r"(\S+) band reads ([\d.]+) rather than ([\d.]+)\.")

    def test_the_sigma_sensitivity_reads_against_the_table_it_sits_under(self):
        """The one paragraph on the page that quotes a `P(title)` this run did
        not publish, and it is only readable as a distance from the one it did:
        both the sd it is compared against and the figure it displaces are
        columns printed above it. Sourced anywhere else the reader is handed a
        bound on a run he cannot see, in the direction he cannot check"""
        out = render("playoffs")
        m = self.SENSITIVITY.search(one_line(out))
        self.assertIsNotNone(m, out)
        tight, lo, hi, band, alt, basis = m.groups()
        sds = [float(r[6]) for r in self.ROUND.findall(out)]
        self.assertEqual((float(lo), float(hi)), (min(sds), max(sds)))
        published = {r[0]: float(r[1]) for r in self.BAND.findall(out)}
        self.assertEqual(float(basis), published[band])
        self.assertLess(float(tight), min(sds), "not the tighter read it is "
                        "printed as -- the direction below is backwards")
        self.assertGreater(float(alt), float(basis))

    def test_the_draw_it_prints_is_the_one_it_climbed(self):
        """The half a seed cannot meet before the final is the whole reason
        `mu_opp` is a survivor rather than the field's mean, and this line is
        where a reader checks which half he is in. Printed off anything but
        the ladders the rounds were climbed on, the audit passes on a bracket
        nobody was priced in"""
        halves = re.search(r"draw is seeds (\S+) \| (\S+), each half climbed",
                           one_line(render("playoffs")))
        self.assertIsNotNone(halves)
        self.assertEqual([[int(s) for s in h.split("-")]
                          for h in halves.groups()],
                         [list(l) for l in sim.LADDERS])

    def test_a_counterparty_is_banded_on_his_own_weeks(self):
        """`--roster` has to reach the `P(title)` block and not only the rows.
        A band is the LOADED roster placed at a seed, so a run that prices his
        players and then publishes our title odds under his name reads as a
        rebuilding team a coin flip from a title. He projects outside the
        field entirely here, and every band says so"""
        out = render("playoffs", THEIR_ROSTER)
        marked, = [l for l in out.splitlines() if "<- loaded" in l]
        self.assertIn(THEIR_ROSTER, marked)
        ours = {r[0]: float(r[1]) for r in self.BAND.findall(render("playoffs"))}
        theirs = {r[0]: float(r[1]) for r in self.BAND.findall(out)}
        self.assertEqual(sorted(theirs), sorted(ours))
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertLess(theirs[band.label], ours[band.label])

    def test_the_cli_serves_it_for_a_counterparty(self):
        status, out = cli("--roster", THEIR_ROSTER, "playoffs")
        self.assertEqual(status, 0, out)
        self.assertIn(THEIR_ROSTER, out)
        self.assertNotIn("playoffs", sim.OURS_ONLY)
        for name in {p["n"] for p in sim.our_roster(THEIR_ROSTER)}:
            self.assertIn(name, out)


if __name__ == "__main__":
    unittest.main()
