import unittest
from tests.harness import *

class PerPositionReplacement(unittest.TestCase):
    """`replacement` prints an `R` per slot group and the README calls the
    single-R error "a third of the formula's error". Pricing a center against a
    forward's 17.1 when his own group's is 20.5 is worth 0.07-0.09 wins cross-
    position, so the counterfactual has to be a body of the outgoing player's
    OWN group"""

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
        """The counterfactual is the whole meaning of the number (`Eval
        Definitions §Δw`), so a header naming one rate for a table priced on
        three is worse than no header, and naming three rates the rows were not
        priced against is worse still. The rates are deterministic given the
        seeds, so the header is checked against a re-fit rather than inspected
        for the words"""
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
    """`formula` grades both formulas against a `sim` column, so that column
    has to use the same per-slot-group counterfactual `players` does. Measured
    against one 68-GP forward for every player, the per-position-R error it
    publishes is a residual against the wrong number, and the fix it recommends
    is scored against the bug it fixes"""

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
    """The top of `sim.py players` decides a rank the README then asserts off
    it. Those rows sit ~0.01 wins apart while a single block moves several
    times that between seeds, so the value has to be an average over blocks and
    it has to carry the sd a reader can test a gap against"""

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
            # An absolute bound on purpose. `3 x (sd_a + sd_b)` widens with the
            # instability it is meant to catch, and 0.06 sits well inside the
            # ~0.1 wins §sigma calls the smallest tradeable gap
            self.assertLess(abs(a[n][0] - b[n][0]), 0.06,
                            "%s: %s vs %s" % (n, a[n], b[n]))

class AdjacentRowSigma(unittest.TestCase):
    """`Eval Definitions §sigma` reads the ORDER of two adjacent rows off this
    column and states none below ~2. Every row is measured on the SAME seed
    blocks, which is what `swap`'s common random numbers buy, so the gap
    between two rows is a within-block quantity and combining the two sds as if
    independent runs up to 3x out in BOTH directions, which is the difference
    between an ordered pair and a tie"""

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
        # Which pairs the two formulas happen to agree on is a fact about this
        # roster's spacing, so the discrimination is asked of the table rather
        # than of the top pair -- where it held until the rows re-sorted
        self.assertGreater(max(gaps), 0.5,
                           "no pair on this table tells the paired formula "
                           "from the independent one, so nothing here can")
