import unittest
from tests.harness import *

class PFPerWinBand(unittest.TestCase):
    def test_the_band_brackets_the_point_estimate_and_stays_wide(self):
        lo, hi = sim.pf_per_win_band(n=400)
        self.assertLess(lo, sim.PF_PER_WIN)
        self.assertGreater(hi, sim.PF_PER_WIN)
        self.assertGreater((hi - lo) / sim.PF_PER_WIN, 0.15)

    def test_one_win_is_about_600_pf(self):
        self.assertAlmostEqual(sim.PF_PER_WIN, 597, delta=10)

class StandingsBasis(unittest.TestCase):
    def test_the_scored_periods_are_the_ones_the_standings_count(self):
        self.assertEqual(sim.WEEKS, 20)
        self.assertEqual(len(sim.OURS), 20)
        self.assertEqual(round(sum(sim.OURS)), 27229)
        for i in sim.SCORED:
            self.assertNotIn("playoff", sim.PERIODS[i]["kinds"])

    def test_including_the_bracket_periods_inflates_the_total(self):
        every = list(sim.SCORES[sim.US].values())
        self.assertEqual(len(every), 23)
        self.assertGreater(sum(every) / sum(sim.OURS), 1.15)

class Calibration(unittest.TestCase):
    def test_the_season_that_happened_simulates_to_roughly_what_it_scored(self):
        got = sim.run(sim.our_roster(projected=False), trials=40)["pf"]
        real = sim.REAL_WK_MEAN * sim.WEEKS
        self.assertAlmostEqual(got / real, 1.0, delta=0.2)

class CalibrationRatio(unittest.TestCase):
    def test_the_ratio_row_is_the_two_totals_printed_above_it(self):
        out = render("calibration")
        got = float(re.search(r"simulated season PF +: +(\d+)", out).group(1))
        real = float(re.search(r"real standings PF +: +(\d+)", out).group(1))
        ratio = float(re.search(r"ratio +: +([\d.]+)", out).group(1))
        self.assertAlmostEqual(ratio, got / real, places=2)

    def test_the_cv_gap_prints_as_a_number_rather_than_a_verdict(self):
        out = render("calibration")
        cv = float(re.search(r"weekly CV +: +([\d.]+)%", out).group(1))
        real = 100 * sim.REAL_WK_SD / sim.REAL_WK_MEAN
        gap = float(re.search(r"sim/real CV - 1 +: +([-+][\d.]+)%",
                              out).group(1))
        self.assertAlmostEqual(gap, 100 * (cv / real - 1), delta=1.0)

class CalibrationUsesTheScoredPeriods(unittest.TestCase):
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
