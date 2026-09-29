import unittest
from tests.harness import *
from simlib import progression_eval as ev


class Scoring(unittest.TestCase):
    def test_a_forecast_drawn_from_the_truth_covers_its_bands_at_their_nominal_rates(self):
        rng = random.Random(3)
        pits = [ev.pit([rng.gauss(0, 1) for _ in range(200)], rng.gauss(0, 1), rng)
                for _ in range(3000)]
        c = ev.coverage(pits)
        self.assertAlmostEqual(c["b80"], 0.80, delta=0.03)
        self.assertAlmostEqual(c["b50"], 0.50, delta=0.03)

    def test_zeros_the_forecast_expects_are_not_all_counted_as_covered(self):
        rng = random.Random(3)
        samples = [0.0] * 60 + [float(i) for i in range(1, 141)]
        pits = [ev.pit(samples, 0.0, rng) for _ in range(2000)]
        self.assertLess(ev.coverage(pits)["b80"], 0.9)
        self.assertGreater(ev.coverage(pits)["lo10"], 0.1)

    def test_a_sharper_forecast_of_the_same_truth_scores_a_lower_crps(self):
        rng = random.Random(3)
        sharp = [rng.gauss(10, 1) for _ in range(400)]
        vague = [rng.gauss(10, 5) for _ in range(400)]
        self.assertLess(ev.crps(sharp, 10.3), ev.crps(vague, 10.3))

    def test_calibration_error_is_the_gap_between_what_was_said_and_what_happened(self):
        self.assertAlmostEqual(ev.ece([0.9] * 10, [1] * 5 + [0] * 5), 0.4)
        self.assertAlmostEqual(ev.ece([0.5] * 10, [1] * 5 + [0] * 5), 0.0)
