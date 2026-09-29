import unittest
from tests.harness import *

class PerPositionReplacement(unittest.TestCase):
    def test_a_player_is_priced_against_a_replacement_of_his_own_slot_group(self):
        full = sim.basis()
        with cheap_monte_carlo(40):
            groups = {g: sim.replacement(full, 68, e)[0]
                      for g, e in sim.GROUPS.items()}
            self.assertGreater(groups["center"], groups["forward"] + 1.0,
                               "this roster's center group is not the tight one")
            base = sim.run(full, seed0=101, cal=sim.DELTA_W_CAL)

            def against(R, elig):
                return sim.wins(base, sim.run(
                    sim.swap(full, ["Jakob Poeltl"], [sim.star(R, 68, elig)]),
                    seed0=101, cal=sim.DELTA_W_CAL))
            own = against(groups["center"], ("C",))
            forward = against(groups["forward"], ("SF", "PF"))
            got, = sim.player_wins(full, ["Jakob Poeltl"], blocks=1).values()
        self.assertAlmostEqual(got[0], own, delta=0.02)
        self.assertGreater(forward, own + 0.02, "the two counterfactuals agree, "
                           "so this roster cannot tell them apart")

    def test_the_table_states_the_replacement_rate_it_used_for_each_group(self):
        buf = io.StringIO()
        with cheap_monte_carlo(8):
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["players"]()
            fitted = sim.group_replacement(sim.basis())
        header = buf.getvalue()
        for g, R in fitted.items():
            with self.subTest(group=g):
                stated = re.search(r"%s (\d+\.\d)" % g, header)
                self.assertIsNotNone(stated, header)
                self.assertAlmostEqual(float(stated.group(1)), R, delta=0.05)

class FormulaCounterfactual(unittest.TestCase):
    ROW = re.compile(r"^  (\S.*?) +[\d.]+ +\d+ +([-+][\d.]+)", re.M)

    def test_the_sim_column_uses_the_same_counterfactual_the_players_report_does(self):
        full = sim.basis()
        buf = io.StringIO()
        with cheap_monte_carlo(8):
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["formula"]()
            rows = dict(self.ROW.findall(buf.getvalue()))
            elig = {p["n"]: p["elig"] for p in sim.our_roster()}
            name = next(n for n in rows
                        if sim.slot_group(elig[n]) != "forward")
            got, = sim.player_wins(full, [name], blocks=1,
                                   R=sim.group_replacement(full)).values()
        self.assertAlmostEqual(float(rows[name]), got[0], delta=0.01)

class PerPlayerWins(unittest.TestCase):
    def test_two_independent_runs_land_far_inside_the_smallest_tradeable_gap(self):
        full = sim.basis()
        who = [p["n"] for p in sorted(sim.our_roster(),
                                      key=lambda p: -p["avg"])[:2]]
        with cheap_monte_carlo(40):
            R = sim.group_replacement(full)
        a = sim.player_wins(full, who, blocks=3, trials=40, seed0=101, R=R)
        b = sim.player_wins(full, who, blocks=3, trials=40, seed0=9001, R=R)
        for n in who:
            self.assertGreater(a[n][1], 0.0, "%s reports no uncertainty" % n)
            self.assertLess(abs(a[n][0] - b[n][0]), 0.08,
                            "%s: %s vs %s" % (n, a[n], b[n]))

class AdjacentRowSigma(unittest.TestCase):
    ROW = re.compile(r"^ +(?P<n>\S.*?) +[\d.]+ +\d+ +\S+ "
                     r"+(?P<w>[-+][\d.]+) +\+-[\d.]+ +(?P<next>[-\d.]+|inf)?",
                     re.M)

    def test_the_gap_is_measured_on_the_blocks_the_two_rows_share(self):
        full = sim.basis()
        blocks = 3
        ours = sim.our_roster()
        with cheap_monte_carlo(8, blocks=blocks):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["players"]()
            w = sim.player_wins(full, [p["n"] for p in ours], blocks=blocks,
                                R=sim.group_replacement(full))
        rows = self.ROW.findall(buf.getvalue())
        self.assertEqual(len(rows), len(ours), rows)
        gaps = []
        for (top, _, printed), (second, _, _) in zip(rows, rows[1:]):
            if printed in ("", "inf"):
                continue
            d = [a - b for a, b in zip(w[top][2], w[second][2])]
            paired = statistics.mean(d) / (statistics.stdev(d)
                                           / math.sqrt(len(d)))
            independent = (w[top][0] - w[second][0]) / math.sqrt(
                (w[top][1] ** 2 + w[second][1] ** 2) / blocks)
            with self.subTest(rows=(top, second)):
                self.assertAlmostEqual(float(printed), paired, delta=0.15)
            gaps.append(abs(float(printed) - independent))
        self.assertGreater(max(gaps), 0.5,
                           "no pair on this table tells the paired formula "
                           "from the independent one, so nothing here can")
