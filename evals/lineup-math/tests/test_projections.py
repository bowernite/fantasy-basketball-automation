import unittest
from tests.harness import *

class UnprojectedRates(unittest.TestCase):
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
        p, = sim.our_roster(roster_file(self.UNPROJECTED))
        self.assertEqual(p["avg"], self.UNPROJECTED["avg"])

class ProjectionSnapshot(unittest.TestCase):
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
        ours = sim.our_roster()
        missing = [p["n"] for p in ours if sim.projected_rate(p["n"]) is None]
        self.assertGreater(len(ours), 20)
        self.assertGreaterEqual(1 - len(missing) / len(ours), 0.93, missing)

class UnusableSnapshot(unittest.TestCase):
    def test_a_missing_snapshot_is_refused_rather_than_repricing_everybody(self):
        with projection_snapshot(None):
            with self.assertRaises(RuntimeError) as e:
                sim.our_roster()
        self.assertIn("sleeper-2026.json", str(e.exception))

    def test_a_snapshot_carrying_nobody_is_refused_too(self):
        with projection_snapshot(sleeper_rows()):
            with self.assertRaises(RuntimeError):
                sim.our_roster()

    def test_a_feed_that_simply_misses_a_player_still_prices_everyone_else(self):
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
