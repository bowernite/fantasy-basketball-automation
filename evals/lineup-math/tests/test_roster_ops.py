import unittest
from tests.harness import *

class Pad(unittest.TestCase):
    """R and WINS compare across teams only at a COMMON body count, and no two
    live rosters have one. Measured on live bodies a counterparty's R lands
    near 23 against ours at 16, so every player on his roster reads as cheaper
    than one of ours"""

    def test_the_real_bodies_survive_padding_in_their_own_order(self):
        their = sim.our_roster(THEIR_ROSTER)
        padded = sim.pad(their, 38)
        self.assertEqual(len(padded), 38)
        self.assertEqual([p["n"] for p in padded[:len(their)]],
                         [p["n"] for p in their])
        self.assertEqual(len({p["n"] for p in padded}), 38)  # names index the rng

    def test_every_report_measures_a_counterparty_at_the_common_count(self):
        """`+ EXPANSION` is 10 BODIES, not a body count, so a 38-man baseline
        built that way measures a 26-man roster at 36 and reports his R, break-
        evens and per-player wins off that"""
        self.assertEqual(len(sim.basis(THEIR_ROSTER)), 38)
        self.assertEqual(len(sim.basis()), 38)

    def test_padding_stops_at_38_bodies_rather_than_at_the_end_of_EXPANSION(self):
        """`+ EXPANSION` is 10 BODIES and `pad` is a COUNT, so the two are one
        measurement only at 28 live bodies. Assumed-through overlays put us at
        32, where `+ EXPANSION` builds a 42-man roster nobody can field and
        `pad` takes the first six grades -- three rookie slots and three FA"""
        ours = sim.our_roster()
        padded = sim.pad(ours, 38)
        short = 38 - len(ours)
        self.assertEqual(len(padded), 38)
        self.assertEqual([p["n"] for p in padded[len(ours):]],
                         [p["n"] for p in sim.EXPANSION[:short]])
        self.assertEqual(sim.run(padded, trials=8)["pf"],
                         sim.run(ours + sim.EXPANSION[:short], trials=8)["pf"])

    def test_padding_to_the_count_you_already_have_measures_the_same_roster(self):
        """Same reason `thin` preserves order. Roster order drives the rng draw
        order, so a pad that reordered would make the padded and unpadded
        measurements incomparable, which is the thing it exists to fix"""
        their = sim.our_roster(THEIR_ROSTER)
        self.assertEqual(sim.run(sim.pad(their, len(their)), trials=8)["pf"],
                         sim.run(their, trials=8)["pf"])

class Backfill(unittest.TestCase):
    def test_a_richer_backfill_grade_lowers_the_breakeven(self):
        """What the outgoing bodies 2..N are refunded at is an ASSUMPTION, not
        a fact, and every break-even in this study rides on it, so it has to be
        an argument for the bracket to be reportable"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            thin_pool = sim.breakeven(full, THREE_OUT,
                                      dead={"tm": "MIA", "avg": 6.0, "gp": 40,
                                            "elig": ["PG", "SG"]})
            deep_pool = sim.breakeven(full, THREE_OUT,
                                      dead={"tm": "MIA", "avg": 14.0, "gp": 55,
                                            "elig": ["PG", "SG"]})
        self.assertLess(deep_pool, thin_pool)

class SwapNames(unittest.TestCase):
    def test_taking_back_more_bodies_than_you_send_fails(self):
        """A 38-man roster has no room, and a silently returned 39-man one
        prices the deal with a free extra body, so the ladder that exists to
        charge for body count reads the wrong count. Attaching the drops is the
        caller's job and there is no defensible default for it"""
        full = sim.basis()
        with self.assertRaises(ValueError):
            sim.swap(full, ["Jalen Suggs"], [sim.star(45), sim.star(30)])
        self.assertEqual(len(sim.swap(full, ["Jalen Suggs", "Coby White"],
                                      [sim.star(45), sim.star(30)])), len(full))

    def test_naming_one_body_twice_on_the_send_side_fails(self):
        """One body cannot leave twice, or `len(out_names)` stops being the
        count of bodies going out and a hand-typed 3-for-1 prices as the
        1-for-1 nobody offered, on the ladder that exists to charge for body
        count"""
        full = sim.basis()
        with self.assertRaises(ValueError):
            sim.swap(full, ["Jalen Suggs", "Jalen Suggs"],
                     [sim.star(45), sim.star(30)])

    def test_trading_away_someone_who_is_not_on_the_roster_fails(self):
        """Matching on name and skipping what it does not find returns a roster
        with the incoming star ADDED and nobody removed. Every scenario built
        that way still prints, several hundred PF too high, with no sign of it
        """
        full = sim.basis()
        with self.assertRaises(KeyError):
            sim.swap(full, ["Jalen Sugs"], [sim.star(45)])

class WinsArgumentOrder(unittest.TestCase):
    """`sim.wins(after, before)`, where the argument order is the sign.
    Reversed it reads "wins lost", which is a legitimate call `report_formula`
    makes, so nothing in the code can guard it and both orders return a
    plausible-looking number. A convention that drifted would invert the
    verdict on every deal in every eval and leave the magnitudes untouched"""

    def test_an_upgrade_reads_positive_and_the_reversed_call_reads_the_loss(self):
        """Measured on the roster's own weakest body so the direction is not in
        question. The reversal is exact rather than approximate, the same pair
        of runs read the other way round, which is what makes "wins lost" a
        call a report can make rather than a second measurement"""
        full = sim.basis()
        worst = min(sim.our_roster(), key=season_value)
        base = sim.run(full, trials=20, cal=sim.DELTA_W_CAL)
        better = sim.run(sim.swap(full, [worst["n"]],
                                  [sim.star(55, 75, tuple(worst["elig"]), n="UP")]),
                         trials=20, cal=sim.DELTA_W_CAL)
        gained = sim.wins(better, base)
        self.assertGreater(gained, 1.0, "%s -> a 55/75 body is not an upgrade"
                           % worst["n"])
        self.assertAlmostEqual(sim.wins(base, better), -gained, places=9)

class MultiPieceDeal(unittest.TestCase):
    """`Eval Definitions §Δw` says price a multi-piece side with one joint
    `sim.run(sim.swap(...))`, never by adding rows. The rows are floats and
    nothing in the code can stop a caller adding them, so the rule is only
    worth what the gap between the two ways measures, and the published table
    is one column of addable numbers sitting next to a three-for-three offer"""

    def priced_both_ways(self, eligs):
        """The same three-for-three, priced as one deal and as three deals"""
        full = sim.basis()
        base = sim.run(full, trials=30, seed0=101, cal=sim.DELTA_W_CAL)
        adds = [sim.star(46, 70, e, n="IN%d" % i) for i, e in enumerate(eligs)]
        joint = sim.wins(
            sim.run(sim.swap(full, THREE_OUT, adds), trials=30, seed0=101,
                    cal=sim.DELTA_W_CAL), base)
        summed = sum(
            sim.wins(sim.run(sim.swap(full, [o], [a]), trials=30, seed0=101,
                             cal=sim.DELTA_W_CAL), base)
            for o, a in zip(THREE_OUT, adds))
        return joint, summed

    def test_adding_the_rows_up_overstates_a_three_piece_package(self):
        """Three 46-rate centers for Suggs/White/Turner run +3.0 wins priced as
        one deal and +4.0 as three rows added. A third of the package is an
        arrival the nine slots have no room to start, and the sum cannot see
        it, which is a whole win on a deal whose verdict turns on tenths"""
        joint, summed = self.priced_both_ways([("C",)] * 3)
        self.assertGreater(summed - joint, 0.5,
                           "joint %.3f vs summed %.3f" % (joint, summed))

    def test_the_overstatement_is_worst_when_the_pieces_share_a_slot_group(self):
        """The mechanism, and the reason the rule is not a haircut a caller
        could apply from the sum alone. The same three bodies spread over
        guard/forward/center lose ~0.2 wins to the cap instead of ~1.0, so a
        package's sub-additivity is a fact about its shape against OUR roster's
        shape and has to be simulated"""
        stacked = self.priced_both_ways([("C",)] * 3)
        spread = self.priced_both_ways([("C",), ("PG", "SG"), ("SF", "PF")])
        self.assertGreater(stacked[1] - stacked[0],
                           (spread[1] - spread[0]) + 0.4,
                           "stacked %s spread %s" % (stacked, spread))

class SlotFillCurve(unittest.TestCase):
    """The whole point of the 9-slot cap. It binds on LIGHT nights and nowhere
    else, which is why breadth pays at all and why the surplus is the middle of
    the roster rather than its tail"""

    @classmethod
    def setUpClass(cls):
        cls.by_night = sim.run(sim.basis(), trials=40)["by_night"]

    def test_most_of_the_lost_slots_sit_on_the_lightest_nights(self):
        lost = {g: (9 - v[1]) * v[3] for g, v in self.by_night.items()}
        tot = sum(lost.values())
        share = lambda upto: sum(v for g, v in lost.items() if g <= upto) / tot
        self.assertAlmostEqual(share(3), 0.68, delta=0.03)
        self.assertAlmostEqual(share(5), 0.89, delta=0.03)
        self.assertAlmostEqual(tot / (9 * len(sim.SCORING_NIGHTS)), 0.091,
                               delta=0.005)

    def test_far_more_slots_go_empty_for_want_of_a_body_than_a_position(self):
        """"Positions rarely bind" is what licenses treating the positional
        premium as a tiebreak rather than a constraint to build around"""
        vals = self.by_night.values()
        no_slot = sum((min(9, v[0]) - v[1]) * v[3] for v in vals)
        no_body = sum(max(0.0, 9 - v[0]) * v[3] for v in vals)
        self.assertGreater(no_body, 3 * no_slot)

class SlotGroups(unittest.TestCase):
    """`replacement` explains its per-group `R` by the crowding behind it, and
    the crowded group is whichever the table says, so bodies and slots have to
    be countable for ANY group rather than just guards"""

    def test_a_body_takes_the_group_of_the_slots_he_is_confined_to(self):
        """`player_wins` prices every player against his own group's R, and the
        three run 3.4 rate points apart here, so where a PF/C lands is worth
        0.07-0.09 wins on his row. Only a body confined to {C} takes the center
        counterfactual"""
        self.assertEqual(sim.slot_group(["C"]), "center")
        self.assertEqual(sim.slot_group(["PF", "C"]), "forward")
        self.assertEqual(sim.slot_group(["PG", "SG"]), "guard")
        self.assertEqual(sim.slot_group(["SG", "SF"]), "forward")

    def test_a_group_counts_every_slot_it_can_fill(self):
        """The two ANY slots are what a hand count misses. A pure center chases
        3 of the 9, not the 1 the template labels C"""
        self.assertEqual(sim.group_slots(("C",)), 3)
        self.assertEqual(sim.group_slots(("PG", "SG")), 5)
        self.assertEqual(sim.group_slots(("SF", "PF")), 5)

    def test_only_a_body_that_cannot_leave_the_group_crowds_it(self):
        """A dual-eligible body relieves the crowding rather than adding to it,
        so it counts toward neither group"""
        roster = [sim.star(20, 60, ("PG", "SG")), sim.star(20, 60, ("SG", "SF")),
                  sim.star(20, 60, ("C",))]
        self.assertEqual(sim.pure_bodies(roster, ("PG", "SG")), 1)
        self.assertEqual(sim.pure_bodies(roster, ("SF", "PF")), 0)
        self.assertEqual(sim.pure_bodies(roster, ("C",)), 1)
