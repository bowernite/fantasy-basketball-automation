import unittest
from tests.harness import *

class OneSchedule(unittest.TestCase):
    """Which NBA team a synthetic body sits on moves its added PF by ~220
    across the 30 schedules, several rate points rather than a rounding effect,
    so the study declares ONE schedule and puts every body on it"""

    def test_the_schedule_moves_a_body_more_than_the_tie_band_does(self):
        full = sim.basis()
        base = sim.run(full, trials=40)["pf"]

        def added(tm):
            body = sim.star(45, 68, ("SF", "PF"), tm, "ADD")
            return sim.run(full + [body], trials=40)["pf"] - base
        self.assertGreater(abs(added("OKC") - added("DET")), 100)

    def test_separate_one_for_ones_beat_a_consolidation_on_one_schedule(self):
        """Priced on the declared schedule the comparison is about bodies
        alone, which is the claim worth keeping. Spread the incoming bodies
        over different NBA teams and an unknown part of the gap is a schedule
        handicap booked as body count"""
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
    """The search under `breakeven`, on the shape a break-even actually has: a
    night's points are the max of a matching over lineups affine in the
    incoming rate, so PF is convex and piecewise affine in it -- one piece per
    start count, and one piece from below the break-even out past the top of
    the bracket, once the body starts every night he is available.

    Pinned here rather than only through `breakeven` because every probe there
    is a Monte Carlo season over 38 bodies, so the cell can only afford to ask
    the question once, of one deal"""

    # Kink at 40 and root at 50, so `LO` sits a piece below the root and the
    # search has to cross the kink to get there
    PIECES = ((1.0, -90.0), (5.0, -250.0))
    LO, HI, TOL = 20.0, 90.0, 0.15

    def search(self):
        """(what it returned, every x it was asked about). The end values go in
        unrecorded: they are the two probes the CALLER has already paid for"""
        seen = []

        def curve(x):
            return max(a * x + b for a, b in self.PIECES)

        def f(x):
            seen.append(x)
            return curve(x)
        return stats.false_position(f, self.LO, self.HI, curve(self.LO),
                                    curve(self.HI), self.TOL), seen

    def test_the_search_lands_on_the_root_rather_than_narrowing_onto_it(self):
        """Halving returns the midpoint of whatever bracket it has left, so it
        is out by up to tol/2 however smooth the function is. Interpolating two
        points of a LINE hits that line's root exactly, so once the search is
        inside the piece the root sits in there is no error left to halve"""
        got, _ = self.search()
        self.assertAlmostEqual(got, 50.0, places=9)

    def test_the_search_costs_a_fraction_of_what_halving_the_bracket_would(self):
        """Halving spends log2(width / tol) probes whatever the function is,
        because it never looks at the VALUES it paid for, only their signs"""
        _, seen = self.search()
        halving = math.log2((self.HI - self.LO) / self.TOL)
        self.assertLess(len(seen), halving / 2,
                        "%d probes: %s" % (len(seen), seen))

class BreakEven(unittest.TestCase):
    def test_a_breakeven_outside_the_bracket_raises_rather_than_returning_an_end(self):
        """Bisection with no sign check converges on the nearer END of its own
        bracket and returns it as an answer, a number that looks measured, sits
        in the middle of the rates we trade at, and is really just `lo`. Both
        ends do it"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            with self.assertRaises(ValueError) as low:
                sim.breakeven(full, ["Jalen Suggs"], lo=60.0, hi=90.0)
            self.assertIn("60", str(low.exception))
            with self.assertRaises(ValueError) as high:
                sim.breakeven(full, THREE_OUT, lo=20.0, hi=30.0)
            self.assertIn("30", str(high.exception))

    def test_one_uncomputable_cell_does_not_take_the_table_with_it(self):
        """Every row of the break-evens table is a comprehension over
        2..N-for-1s, so the ValueError `breakeven` correctly raises for one
        cell kills the whole report. Out of bracket is a real answer ABOUT THAT
        CELL, "no such player exists, so the deal is unbuyable", so the cell
        says which end it fell off.

        One of them through `base=`, which is how the table calls every cell it
        prints: a search handed a baseline still has to sign-check its own
        bracket, or an unbuyable deal comes back as a number that looks
        measured"""
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
        """What a break-even IS. Seat a body at that rate in the slots the
        outgoing players vacated and the season's PF comes back where it
        started.

        Both sides are 20-trial figures on the same estimator the search ran
        on, so what this pins is that the search converged, not that the
        published rate survives a re-measure at the published trial count.

        5 PF is `tol`'s own accuracy claim priced in PF rather than a round
        number: PF runs ~52 per rate point through here, so the 0.15-wide
        bracket the search promises is worth ~3.9 PF. Anything looser is slack
        a search that stops short of the root can still read as converged in"""
        full = sim.basis()
        out = THREE_OUT[:2]
        with cheap_monte_carlo(20):
            rate = sim.breakeven(full, out, gp=68, elig=("SF", "PF"))
            got = sim.run(sim.swap(full, out, [sim.star(rate, 68)]))["pf"]
            self.assertAlmostEqual(got, sim.run(full)["pf"], delta=5)

    def test_the_breakeven_moves_with_the_incoming_gp_and_slot(self):
        """"Read the row matching his shape." The same 3-for-1 needs several
        more rate points from a 65-GP center than from a 68-GP forward and
        fewer from a 78-GP one, which is how Jokic reads as a hair positive
        against his own row and a 6-point win against the forward row. A break-
        even quoted without its GP and slot is the wrong number, not a rounded
        one"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            forward = sim.breakeven(full, THREE_OUT, 68, ("SF", "PF"))
            center = sim.breakeven(full, THREE_OUT, 65, ("C",))
            durable = sim.breakeven(full, THREE_OUT, 78, ("SF", "PF"))
        # A bound above 2.5 sits over the gap the report publishes, so it would
        # bound the search's rounding error and not the gap this test is about
        self.assertGreater(center, forward + 2.5)
        self.assertLess(durable, forward - 1.5)

    def test_the_baseline_you_hand_in_is_the_one_the_search_prices_against(self):
        """The table prices 25 cells against ONE roster, so the baseline goes
        in once rather than as 25 identical runs of the same 38 bodies. It has
        to be the number the search actually subtracts, or the answer is priced
        against a roster the caller never handed in"""
        full = sim.basis()
        out = THREE_OUT[:2]
        with recorded_rosters(20) as seen:
            base = sim.run(full)["pf"]
            handed = sim.breakeven(full, out, base=base)
            measured = sim.breakeven(full, out)
        self.assertEqual(handed, measured)
        # the explicit run above and `measured`'s own -- never `handed`'s
        self.assertEqual(seen.count([p["n"] for p in full]), 2)

    def test_a_cell_costs_a_handful_of_probes_and_not_a_whole_bisection(self):
        """Halving a 70-point bracket down to 0.15 is 9 probes on top of the two
        the sign check spends, and each one is a full Monte Carlo over 38
        bodies. `FalsePosition` pins the count against a synthetic convex `f`;
        this is the same claim against the real PF curve, whose affine pieces
        are the incoming body's start counts"""
        full = sim.basis()
        with recorded_rosters(20) as seen:
            base = sim.run(full)["pf"]
            sim.breakeven(full, THREE_OUT[:2], base=base)
        probes = len(seen) - 1
        self.assertLessEqual(probes, 5, "%d probes for one cell" % probes)

    def test_the_table_measures_each_rosters_baseline_once(self):
        """Every cell of it is priced against one of two rosters, and the
        baseline is the SAME run of the same bodies for all 25 cells the padded
        one carries -- the single largest piece of what this report spends.

        The rest is the searches, 37 cells at a handful of Monte Carlo seasons
        each. Bounded over the WHOLE table because per-cell probe counts are a
        property of the deal: a root that lands in a shallow piece of PF costs
        more probes than halving would and stops further from the root than
        this table prints, and only a cell that does it shows up here"""
        with recorded_rosters(20) as seen, \
                contextlib.redirect_stdout(io.StringIO()):
            deals.report_breakevens()
        for label, roster in (("padded", sim.basis()),
                              ("as loaded", sim.our_roster())):
            with self.subTest(roster=label):
                self.assertEqual(seen.count([p["n"] for p in roster]), 1)
        self.assertLess(len(seen), 250, "%d seasons for the table" % len(seen))
