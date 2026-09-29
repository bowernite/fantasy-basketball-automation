import unittest
from tests.harness import *
from tests.fetch_stub import *

class FetchRosterTransform(unittest.TestCase):
    def test_a_played_season_becomes_a_priceable_roster_row(self):
        self.assertEqual(fetch_data.roster_rows(roster_payload()),
                         [{"n": "Darius Garland", "tm": "LAC",
                           "avg": 31.894444, "tot": 1435.25, "gp": 45,
                           "posLabel": "G", "elig": ["PG", "SG"]}])

    def test_a_player_who_missed_the_whole_season_still_carries_his_positions(self):
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
    def test_a_body_added_after_the_snapshot_is_on_the_roster(self):
        league = league_payload((161014, [
            pro_player("Darius Garland", 1),
            pro_player("Steven Adams", 9, "HOU", "C", ("C",))]))
        rows = fetch_data.merged_rows(league, 161014, roster_payload(), {})
        self.assertEqual([r["n"] for r in rows],
                         ["Darius Garland", "Steven Adams"])

    def test_a_body_dropped_after_the_snapshot_is_off_the_roster(self):
        snapshot = snapshot_payload(
            (pro_player("Darius Garland", 1), 31.9, 1435.25),
            (pro_player("Nick Richards", 7, "PHX", "C", ("C",)), 20.0, 1000.0))
        league = league_payload((161014, [pro_player("Darius Garland", 1)]))
        rows = fetch_data.merged_rows(league, 161014, snapshot, {})
        self.assertEqual([r["n"] for r in rows], ["Darius Garland"])

    def test_a_body_the_snapshot_never_saw_takes_last_season_off_the_pool(self):
        league = league_payload((161014, [
            pro_player("Steven Adams", 9, "HOU", "C", ("C",))]))
        pool = {"Steven Adams": {"seasons": {"2024": [10.0, 5], "2025": [23.117, 32]}}}
        row, = fetch_data.merged_rows(league, 161014, snapshot_payload(), pool)
        self.assertEqual(row, {"n": "Steven Adams", "tm": "HOU", "avg": 23.117,
                               "tot": 739.744, "gp": 32, "posLabel": "C",
                               "elig": ["C"]})

    def test_the_bodies_keep_the_snapshot_order_and_the_new_ones_append(self):
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
        snapshot = snapshot_payload(
            (pro_player("Zach Edey", 3, "MEM", "C", ("C",)), 33.7, 371.0))
        league = league_payload((161014, [
            pro_player("Zach Edey", 3, "DAL", "F", ("PF", "C"))]))
        row, = fetch_data.merged_rows(league, 161014, snapshot, {})
        self.assertEqual(row, {"n": "Zach Edey", "tm": "DAL", "avg": 33.7,
                               "tot": 371.0, "gp": 11, "posLabel": "F",
                               "elig": ["C", "PF"]})

    def test_a_body_neither_feed_has_a_line_for_is_written_as_an_empty_one(self):
        league = league_payload((161014, [
            pro_player("Cooper Flagg", 11, "DAL", "F", ("SF", "PF"))]))
        row, = fetch_data.merged_rows(league, 161014, snapshot_payload(), {})
        self.assertEqual((row["avg"], row["tot"], row["gp"]), (0.0, 0.0, 0))

    def test_a_team_id_the_league_does_not_carry_refuses(self):
        league = league_payload((161014, [pro_player("Darius Garland", 1)]))
        with self.assertRaises(KeyError) as e:
            fetch_data.merged_rows(league, 161099, roster_payload(), {})
        self.assertIn("161099", str(e.exception))

class CommittedRosterFiles(unittest.TestCase):
    def test_every_committed_file_carries_the_eligibility_it_is_priced_on(self):
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
        for path in committed_rosters():
            rows = sim.our_roster(os.path.basename(path))
            with self.subTest(roster=os.path.basename(path)):
                for p in rows:
                    self.assertGreater(p["avg"], 0, "%s prices as nothing" % p["n"])
                    self.assertTrue(0 < p["gp"] <= 82, "%s: %s gp" % (p["n"], p["gp"]))

class EmptyRosterFile(unittest.TestCase):
    def test_a_file_with_nobody_on_it_is_refused_instead_of_padded_into_a_team(self):
        p = sim_process("--roster", roster_file(), "players")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("wins lost if swapped", p.stdout)

    def test_the_refusal_names_the_file_that_carried_nobody(self):
        path = roster_file()
        with self.assertRaises(ValueError) as e:
            sim.basis(path)
        self.assertIn(path, str(e.exception))
