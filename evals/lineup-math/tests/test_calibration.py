import unittest
from tests.harness import *

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
