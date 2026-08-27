import unittest
from tests.harness import *

class MissedSeasonRate(unittest.TestCase):
    def test_a_missed_season_is_priced_off_the_projection(self):
        p, = sim.our_roster(roster_file(
            {"n": "Tyrese Haliburton", "tm": "IND", "avg": 0.0, "tot": 0.0,
             "gp": 0, "posLabel": "G", "elig": ["PG", "SG"]}))
        self.assertGreater(p["avg"], 20)
        self.assertLess(p["avg"], 35)
        self.assertGreater(p["gp"], 45)

class PoolJoinByName(unittest.TestCase):
    def test_an_ascii_spelling_finds_the_same_pool_season(self):
        self.assertAlmostEqual(sim.project_gp("Luka Doncic"),
                               sim.project_gp("Luka Dončić"), places=6)

    def test_a_name_in_neither_the_pool_nor_the_call_fails_loudly(self):
        with self.assertRaises(KeyError):
            sim.project_gp("Nobody At All")

class SymmetricProjection(unittest.TestCase):
    def test_every_player_regresses_toward_the_pool_not_just_a_named_few(self):
        proj = {p["n"]: p["gp"] for p in sim.our_roster()}
        raw = {p["n"]: p["gp"] for p in sim.our_roster(projected=False)}
        self.assertEqual(raw["Desmond Bane"], 82)
        self.assertLess(proj["Desmond Bane"], raw["Desmond Bane"])
        self.assertEqual(raw["Jalen Suggs"], 57)
        self.assertGreater(proj["Jalen Suggs"], raw["Jalen Suggs"])

    def test_a_pooled_players_games_come_off_his_pool_rate(self):
        for p in sim.our_roster():
            if sim.pool_seasons(p["n"]):
                with self.subTest(player=p["n"]):
                    self.assertEqual(p["gp"], round(sim.project_gp(p["n"])))

    def test_the_rate_applies_by_name_not_by_owner(self):
        def maluach_priced_off(avg):
            p, = sim.our_roster(roster_file(
                {"n": "Khaman Maluach", "tm": "PHX", "avg": avg, "tot": 377.0,
                 "gp": 46, "posLabel": "C", "elig": ["C"]}))
            return p["avg"]

        low, high = maluach_priced_off(8.2), maluach_priced_off(40.0)
        self.assertEqual(low, high)
        self.assertNotIn(low, (8.2, 40.0))

    def test_the_calibration_basis_is_the_season_that_actually_happened(self):
        raw = sim._load(sim.ROSTER)
        self.assertEqual([(p["n"], p["avg"], p["gp"])
                          for p in sim.our_roster(projected=False)],
                         [(p["n"], p["avg"], p["gp"]) for p in raw])

class GPRunsOnTheActualRate(unittest.TestCase):
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
        ours = rostered(self.OURS)
        theirs, = sim.our_roster(roster_file(
            {"n": self.OURS, "tm": "BKN", "avg": 3.1, "tot": 37.0,
             "gp": 12, "posLabel": "G", "elig": ["PG", "SG"]}))

        self.assertEqual(theirs["gp"], ours["gp"])
        actual, _ = sim.pool_seasons(self.OURS)["2025"]
        self.assertEqual(theirs["gp"], round(sim.project_gp(self.OURS,
                                                            rate=actual)))

    def test_a_whole_missed_season_reaches_back_to_the_last_one_that_happened(self):
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
        name = "Vasilije Micić"
        self.assertEqual(sim.evidence_flags(name), ["nopool"])
        self.assertLess(sim.projected_rate(name), 15)

        p, = sim.our_roster(roster_file(
            {"n": name, "tm": "PHX", "avg": 21.5, "tot": 946.0,
             "gp": 44, "posLabel": "G", "elig": ["PG", "SG"]}))

        self.assertEqual(p["gp"], round(sim.project_gp(name, gp=44, rate=21.5)))

    def test_no_row_on_any_roster_is_fitted_on_the_forecast(self):
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
                    continue
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
        table = render("players")
        for name in ("Fred VanVleet", "Cade Cunningham"):
            raw = rostered(name, projected=False)
            p = rostered(name)
            self.assertNotEqual(raw["gp"], p["gp"])
            row, = [l for l in table.splitlines() if l.startswith("  " + name)]
            printed, = re.findall(r"[\d.]+ +(\d+) +\S+ +[-+][\d.]+", row)
            self.assertEqual(int(printed), p["gp"], row)
