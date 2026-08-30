import unittest
from tests.harness import *

class OneSchedule(unittest.TestCase):
    def test_the_schedule_moves_a_body_more_than_the_tie_band_does(self):
        full = sim.basis()
        base = sim.run(full, trials=40)["pf"]

        def added(tm):
            body = sim.star(45, 68, ("SF", "PF"), tm, "ADD")
            return sim.run(full + [body], trials=40)["pf"] - base
        per = {t: len(sim.team_light_nights(t)) for t in sim.NBA_TEAMS}
        deep = max(per, key=per.get)
        thin = min(per, key=per.get)
        self.assertGreater(abs(added(deep) - added(thin)), 100)

    def test_separate_one_for_ones_beat_a_consolidation_on_one_schedule(self):
        full = sim.basis()
        base = sim.run(full, trials=40, cal=sim.DELTA_W_CAL)
        sep = sim.wins(sim.run(sim.swap(full, THREE_OUT, [
            sim.star(42, 68, ("SF", "PF"), sim.SIM_TM, "S%d" % i)
            for i in range(3)]), trials=40, cal=sim.DELTA_W_CAL), base)
        con = sim.wins(sim.run(sim.swap(full, THREE_OUT, [
            sim.star(65.2, 65, ("C",), sim.SIM_TM)]), trials=40,
                       cal=sim.DELTA_W_CAL), base)
        self.assertGreater(sep, con)

class FalsePosition(unittest.TestCase):
    PIECES = ((1.0, -90.0), (5.0, -250.0))
    LO, HI, TOL = 20.0, 90.0, 0.15

    def search(self):
        seen = []

        def curve(x):
            return max(a * x + b for a, b in self.PIECES)

        def f(x):
            seen.append(x)
            return curve(x)
        return stats.false_position(f, self.LO, self.HI, curve(self.LO),
                                    curve(self.HI), self.TOL), seen

    def test_the_search_lands_on_the_root_rather_than_narrowing_onto_it(self):
        got, _ = self.search()
        self.assertAlmostEqual(got, 50.0, places=9)

    def test_the_search_costs_a_fraction_of_what_halving_the_bracket_would(self):
        _, seen = self.search()
        halving = math.log2((self.HI - self.LO) / self.TOL)
        self.assertLess(len(seen), halving / 2,
                        "%d probes: %s" % (len(seen), seen))

class BreakEven(unittest.TestCase):
    def test_a_breakeven_outside_the_bracket_raises_rather_than_returning_an_end(self):
        full = sim.basis()
        with cheap_monte_carlo(20):
            with self.assertRaises(ValueError) as low:
                sim.breakeven(full, ["Jalen Suggs"], lo=60.0, hi=90.0)
            self.assertIn("60", str(low.exception))
            with self.assertRaises(ValueError) as high:
                sim.breakeven(full, THREE_OUT, lo=20.0, hi=30.0)
            self.assertIn("30", str(high.exception))

    def test_one_uncomputable_cell_does_not_take_the_table_with_it(self):
        full = sim.basis()
        with cheap_monte_carlo(20):
            self.assertIn(">30", sim.breakeven_cell(full, THREE_OUT, lo=20.0,
                                                    hi=30.0,
                                                    base=sim.run(full)["pf"]))
            self.assertIn("<60", sim.breakeven_cell(full, THREE_OUT[:1],
                                                    lo=60.0, hi=90.0))
            self.assertRegex(sim.breakeven_cell(full, THREE_OUT[:2]),
                             r"\d\d\.\d")

    def test_the_rate_it_returns_is_pf_neutral(self):
        full = sim.basis()
        out = THREE_OUT[:2]
        with cheap_monte_carlo(20):
            rate = sim.breakeven(full, out, gp=68, elig=("SF", "PF"))
            got = sim.run(sim.swap(full, out, [sim.star(rate, 68)]))["pf"]
            self.assertAlmostEqual(got, sim.run(full)["pf"], delta=5)

    def test_the_breakeven_moves_with_the_incoming_gp_and_slot(self):
        full = sim.basis()
        with cheap_monte_carlo(20):
            forward = sim.breakeven(full, THREE_OUT, 68, ("SF", "PF"))
            center = sim.breakeven(full, THREE_OUT, 65, ("C",))
            durable = sim.breakeven(full, THREE_OUT, 78, ("SF", "PF"))
        self.assertGreater(center, forward)
        self.assertLess(durable, forward)

    def test_the_baseline_you_hand_in_is_the_one_the_search_prices_against(self):
        full = sim.basis()
        out = THREE_OUT[:2]
        with recorded_rosters(20) as seen:
            base = sim.run(full)["pf"]
            handed = sim.breakeven(full, out, base=base)
            measured = sim.breakeven(full, out)
        self.assertEqual(handed, measured)
        self.assertEqual(seen.count([p["n"] for p in full]), 2)

    def test_a_cell_costs_a_handful_of_probes_and_not_a_whole_bisection(self):
        full = sim.basis()
        with recorded_rosters(20) as seen:
            base = sim.run(full)["pf"]
            sim.breakeven(full, THREE_OUT[:2], base=base)
        probes = len(seen) - 1
        self.assertLessEqual(probes, 5, "%d probes for one cell" % probes)

    def test_the_table_measures_each_rosters_baseline_once(self):
        with recorded_rosters(20) as seen, \
                contextlib.redirect_stdout(io.StringIO()):
            deals.report_breakevens()
        for label, roster in (("padded", sim.basis()),
                              ("as loaded", sim.our_roster())):
            with self.subTest(roster=label):
                self.assertEqual(seen.count([p["n"] for p in roster]), 1)
        self.assertLess(len(seen), 250, "%d seasons for the table" % len(seen))
