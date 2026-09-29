import unittest
from tests.harness import *

class SeasonAge(unittest.TestCase):
    def test_age_is_taken_at_the_february_of_the_season_it_describes(self):
        self.assertAlmostEqual(sim.age_at("1995-02-19", 2025), 30.95, places=1)
        self.assertAlmostEqual(sim.age_at("1995-02-19", 2021), 26.95, places=1)

class GPModelSelection(unittest.TestCase):
    def test_nothing_beats_the_pool_mean_when_games_played_is_pure_noise(self):
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
    def test_a_model_that_loses_a_fold_is_refused_rather_than_scored_on_the_rest(self):
        rows = [{"name": "P%d" % i, "y": 60.0 + i, "hist": [60], "rate": 30.0,
                 "age": 25.0} for i in range(10)]
        self.addCleanup(gp.GP_MODELS.pop, "flat", None)
        gp.GP_MODELS["flat"] = lambda r: (1.0,)
        with self.assertRaises(ValueError) as e:
            gp.gp_sq_errors(rows, models=("flat",))
        self.assertIn("flat", str(e.exception))

class GPUncertainty(unittest.TestCase):
    def test_the_reported_uncertainty_covers_the_gap_it_is_used_to_judge(self):
        b = sim.gp_bootstrap(sim.gp_rows(), models=("gp1", "gp5", "mean"), n=400)
        self.assertGreater(b["gp5"]["delta"], 0.0)
        self.assertLess(b["gp5"]["lo"], 0.0)
        self.assertGreater(b["mean"]["lo"], 0.0)

class GPRows(unittest.TestCase):
    def test_history_is_strictly_earlier_than_the_season_being_predicted(self):
        rows = sim.gp_rows()
        self.assertGreater(len(rows), 300)
        for r in rows:
            self.assertTrue(r["seasons"], r)
            self.assertLess(max(r["seasons"]), r["season"], r)

    def test_history_is_most_recent_first(self):
        for r in sim.gp_rows():
            self.assertEqual(r["seasons"], sorted(r["seasons"], reverse=True), r)

class GPProjection(unittest.TestCase):
    def test_the_gp_fit_coefficients_are_the_ones_the_readme_publishes(self):
        intercept, per_gp, per_rate = sim.gp_model()
        self.assertAlmostEqual(intercept, 25.7, delta=0.05)
        self.assertAlmostEqual(per_gp, 0.368, delta=0.005)
        self.assertAlmostEqual(per_rate, 0.432, delta=0.005)

    def test_an_outlier_injury_season_regresses_upward(self):
        self.assertGreater(sim.mapped_gp("Joel Embiid"), 45)

    def test_an_iron_man_season_regresses_downward(self):
        self.assertLess(sim.mapped_gp("Desmond Bane"), 75)

    def test_the_durable_player_still_projects_above_the_fragile_one(self):
        self.assertGreater(sim.mapped_gp("Nikola Jokić"),
                           sim.mapped_gp("Joel Embiid"))

    def test_a_superstar_rate_does_not_buy_more_games_than_an_all_star_rate(self):
        self.assertLessEqual(sim.mapped_gp("nobody", gp=65, rate=65.0),
                             sim.mapped_gp("nobody", gp=65, rate=35.0) + 0.5)

    def test_a_fringe_player_projects_fewer_games_than_a_starter_at_the_same_gp(self):
        self.assertGreater(sim.mapped_gp("Desmond Bane"),
                           sim.mapped_gp("Sion James") + 4)
