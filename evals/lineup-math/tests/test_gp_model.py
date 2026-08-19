import unittest
from tests.harness import *

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
