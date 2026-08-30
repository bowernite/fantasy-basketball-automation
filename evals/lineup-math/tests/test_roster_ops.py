import unittest
from tests.harness import *

class Pad(unittest.TestCase):
    def test_pad_does_not_invent_rookies_beyond_held_picks(self):
        ours = sim.our_roster()
        added = [p["n"] for p in sim.basis()[len(ours):]]
        with open(os.path.join(sim.DATA_DIR, "draft-2026.json")) as f:
            picks = json.load(f)["161025"]
        self.assertEqual(len(picks), 1)
        self.assertEqual(added[0], "RK0")
        self.assertTrue(all(n.startswith("FA") for n in added[1:]), added)
        self.assertEqual(len(added), 38 - len(ours))

    def test_a_team_with_more_picks_gets_more_rookie_pad_bodies(self):
        with open(os.path.join(sim.DATA_DIR, "draft-2026.json")) as f:
            board = json.load(f)
        us = sum(1 for p in sim.basis() if p["n"].startswith("RK"))
        them = sum(1 for p in sim.basis(ROOKIE_ROSTER) if p["n"].startswith("RK"))
        self.assertEqual(us, len(board["161025"]))
        self.assertEqual(them, len(board["160941"]))
        self.assertGreater(them, us)

    def test_the_real_bodies_survive_padding_in_their_own_order(self):
        their = sim.our_roster(THEIR_ROSTER)
        padded = sim.pad(their, 38)
        self.assertEqual(len(padded), 38)
        self.assertEqual([p["n"] for p in padded[:len(their)]],
                         [p["n"] for p in their])
        self.assertEqual(len({p["n"] for p in padded}), 38)

    def test_every_report_measures_a_counterparty_at_the_common_count(self):
        self.assertEqual(len(sim.basis(THEIR_ROSTER)), 38)
        self.assertEqual(len(sim.basis()), 38)

    def test_padding_stops_at_38_bodies_rather_than_at_the_end_of_the_fill(self):
        ours = sim.our_roster()
        padded = sim.basis()
        self.assertEqual(len(padded), 38)
        self.assertEqual(sim.run(padded, trials=8)["pf"],
                         sim.run(sim.pad(ours, 38, path=sim.ROSTER),
                                 trials=8)["pf"])

    def test_padding_to_the_count_you_already_have_measures_the_same_roster(self):
        their = sim.our_roster(THEIR_ROSTER)
        self.assertEqual(sim.run(sim.pad(their, len(their)), trials=8)["pf"],
                         sim.run(their, trials=8)["pf"])

    def test_a_held_pick_sits_at_its_projected_rate(self):
        rk = next(p for p in sim.basis() if p["n"] == "RK0")
        self.assertAlmostEqual(rk["avg"], sim.projected_rate("Karim Lopez"))
        self.assertEqual(rk["gp"], 60)

    def test_a_better_pick_sits_above_a_worse_one(self):
        ours = next(p for p in sim.basis() if p["n"] == "RK0")
        todd = next(p for p in sim.basis("roster-161022-2025-26.json")
                    if p["n"] == "RK0")
        self.assertAlmostEqual(todd["avg"], sim.projected_rate("Cameron Boozer"))
        self.assertGreater(todd["avg"], ours["avg"] + 15)

    def test_a_held_pick_brings_its_own_team_and_eligibility(self):
        rk = next(p for p in sim.basis() if p["n"] == "RK0")
        self.assertEqual(rk["tm"], "MEM")
        self.assertEqual(rk["elig"], ["SF", "PF"])

    def test_a_pick_the_feed_misses_stays_a_late_pick_body(self):
        with open(os.path.join(sim.DATA_DIR, "draft-2026.json")) as f:
            picks = json.load(f)["161020"]
        self.assertEqual(picks[-1]["name"], "Ryan Conwell")
        self.assertIsNone(sim.projected_rate("Ryan Conwell"))
        rk = next(p for p in sim.basis(THEIR_ROSTER)
                  if p["n"] == "RK%d" % (len(picks) - 1))
        self.assertEqual(rk["avg"], 10.0)
        self.assertEqual(rk["gp"], 60)

class Backfill(unittest.TestCase):
    def test_a_richer_backfill_grade_lowers_the_breakeven(self):
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
        full = sim.basis()
        with self.assertRaises(ValueError):
            sim.swap(full, ["Jalen Suggs"], [sim.star(45), sim.star(30)])
        self.assertEqual(len(sim.swap(full, ["Jalen Suggs", "Coby White"],
                                      [sim.star(45), sim.star(30)])), len(full))

    def test_naming_one_body_twice_on_the_send_side_fails(self):
        full = sim.basis()
        with self.assertRaises(ValueError):
            sim.swap(full, ["Jalen Suggs", "Jalen Suggs"],
                     [sim.star(45), sim.star(30)])

    def test_trading_away_someone_who_is_not_on_the_roster_fails(self):
        full = sim.basis()
        with self.assertRaises(KeyError):
            sim.swap(full, ["Jalen Sugs"], [sim.star(45)])

class WinsArgumentOrder(unittest.TestCase):
    def test_an_upgrade_reads_positive_and_the_reversed_call_reads_the_loss(self):
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
    def priced_both_ways(self, eligs):
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
        joint, summed = self.priced_both_ways([("C",)] * 3)
        self.assertGreater(summed - joint, 0.5,
                           "joint %.3f vs summed %.3f" % (joint, summed))

    def test_the_overstatement_is_worst_when_the_pieces_share_a_slot_group(self):
        stacked = self.priced_both_ways([("C",)] * 3)
        spread = self.priced_both_ways([("C",), ("PG", "SG"), ("SF", "PF")])
        self.assertGreater(stacked[1] - stacked[0],
                           (spread[1] - spread[0]) + 0.4,
                           "stacked %s spread %s" % (stacked, spread))

class SlotFillCurve(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.by_night = sim.run(sim.basis(), trials=40)["by_night"]

    def test_most_of_the_lost_slots_sit_on_the_lightest_nights(self):
        lost = {g: (9 - v[1]) * v[3] for g, v in self.by_night.items()}
        tot = sum(lost.values())
        share = lambda upto: sum(v for g, v in lost.items() if g <= upto) / tot
        self.assertAlmostEqual(share(3), 0.54, delta=0.03)
        self.assertAlmostEqual(share(5), 0.89, delta=0.05)
        self.assertAlmostEqual(tot / (9 * len(sim.SCORING_NIGHTS)), 0.061,
                               delta=0.01)

    def test_far_more_slots_go_empty_for_want_of_a_body_than_a_position(self):
        vals = self.by_night.values()
        no_slot = sum((min(9, v[0]) - v[1]) * v[3] for v in vals)
        no_body = sum(max(0.0, 9 - v[0]) * v[3] for v in vals)
        self.assertGreater(no_body, 3 * no_slot)

class SlotGroups(unittest.TestCase):
    def test_a_body_takes_the_group_of_the_slots_he_is_confined_to(self):
        self.assertEqual(sim.slot_group(["C"]), "center")
        self.assertEqual(sim.slot_group(["PF", "C"]), "forward")
        self.assertEqual(sim.slot_group(["PG", "SG"]), "guard")
        self.assertEqual(sim.slot_group(["SG", "SF"]), "forward")

    def test_a_group_counts_every_slot_it_can_fill(self):
        self.assertEqual(sim.group_slots(("C",)), 3)
        self.assertEqual(sim.group_slots(("PG", "SG")), 5)
        self.assertEqual(sim.group_slots(("SF", "PF")), 5)

    def test_only_a_body_that_cannot_leave_the_group_crowds_it(self):
        roster = [sim.star(20, 60, ("PG", "SG")), sim.star(20, 60, ("SG", "SF")),
                  sim.star(20, 60, ("C",))]
        self.assertEqual(sim.pure_bodies(roster, ("PG", "SG")), 1)
        self.assertEqual(sim.pure_bodies(roster, ("SF", "PF")), 0)
        self.assertEqual(sim.pure_bodies(roster, ("C",)), 1)
