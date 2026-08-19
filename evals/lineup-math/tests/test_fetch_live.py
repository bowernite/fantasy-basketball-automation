import unittest
from tests.harness import *
from tests.fetch_stub import *

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
