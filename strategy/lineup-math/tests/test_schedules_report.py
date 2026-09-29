import unittest
from tests.harness import *

class SchedulesReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = len(sim.auction_slots(sim.basis()))
        cls.out = render("schedules")

    def headline(self):
        m = re.search(r"best %d, all %d teams on offer\s*:\s*([-+][\d.]+)"
                      % (self.n, len(sim.NBA_TEAMS)), self.out)
        self.assertIsNotNone(m, self.out)
        return float(m.group(1))

    def ladder(self):
        rungs = re.search(r"cumulative \+wins(.*)", self.out).group(1).split()
        self.assertEqual(len(rungs), self.n, self.out)
        return [float(x) for x in rungs]

    def test_the_ladder_total_is_the_same_number_as_the_headline(self):
        self.assertEqual(self.ladder()[-1], self.headline(), self.out)

    def test_the_stacked_slate_row_is_the_slate_times_the_deepest_schedule(self):
        summed, covered = re.search(
            r"all %d on \w+\s*:\s*(\d+) body-nights summed, (\d+) distinct"
            % self.n, self.out).groups()
        deepest = max(light_nights_per_team().values())
        self.assertEqual(int(summed), self.n * deepest)
        self.assertEqual(int(covered), deepest)
        got = float(re.search(r"distinct, ([-+][\d.]+) wins", self.out).group(1))
        self.assertIn("lands %s not caring" % ("BELOW" if got < 0 else "above"),
                      self.out)

    def per_team_counts(self):
        listed = {}
        for n, tms in re.findall(r"^ +(\d+) +((?:[A-Z]{2,4} ?)+)$", self.out, re.M):
            for tm in tms.split():
                listed[tm] = int(n)
        return listed

    def test_every_team_is_listed_under_its_own_light_night_count(self):
        self.assertEqual(self.per_team_counts(), light_nights_per_team())

    def per_body_rows(self):
        rows = [tuple(map(float, m)) for m in re.findall(
            r"^ +(\d+) +(\d+) +([\d.]+) +([\d.]+) +([\d.]+) +([\d.]+)$",
            self.out, re.M)]
        self.assertTrue(rows, self.out)
        return rows

    def test_the_schedule_swing_converts_through_the_one_pf_to_wins(self):
        for rate, _, sdpf, sdwins, _, _ in self.per_body_rows():
            with self.subTest(rate=rate):
                self.assertAlmostEqual(sdwins, sim.pf_wins(sdpf), delta=0.001)

    def test_the_schedule_spread_shrinks_as_the_body_gets_better(self):
        rows = self.per_body_rows()
        self.assertEqual([r[1] for r in rows], sorted(r[1] for r in rows))
        self.assertGreater(rows[0][4], rows[-1][4] * 1.5)

    def test_the_growth_line_comes_off_its_own_table(self):
        rows = self.per_body_rows()
        m = re.search(r"body ([\d.]+)x from rate (\d+) to (\d+), schedule sd "
                      r"([\d.]+)x: ([\d.]+) rate points at (\d+), ([\d.]+) "
                      r"at (\d+)", self.out)
        self.assertIsNotNone(m, self.out)
        body, lo, hi, swing, rlo, at_lo, rhi, at_hi = m.groups()
        self.assertEqual((int(lo), int(hi)), (rows[0][0], rows[-1][0]))
        self.assertEqual((int(at_lo), int(at_hi)), (rows[0][0], rows[-1][0]))
        self.assertAlmostEqual(float(body), rows[-1][1] / rows[0][1], delta=0.6)
        self.assertAlmostEqual(float(swing), rows[-1][2] / rows[0][2], delta=0.5)
        self.assertAlmostEqual(float(rlo), rows[0][4], delta=0.01)
        self.assertAlmostEqual(float(rhi), rows[-1][4], delta=0.01)

    def test_the_threshold_it_prints_comes_off_the_row_we_actually_bid_at(self):
        rows = self.per_body_rows()
        thresh = re.search(r"threshold ~([\d.]+) rate points", self.out)
        self.assertIsNotNone(thresh, self.out)
        self.assertAlmostEqual(float(thresh.group(1)), rows[0][4], delta=0.01)
        self.assertLessEqual(rows[0][0], 8)

    def test_the_spread_row_uses_the_same_picks_as_the_headline(self):
        covered, wins = re.search(
            r"spread best %d\s*:\s*\d+ body-nights summed, (\d+) distinct, "
            r"([-+][\d.]+) wins" % self.n, self.out).groups()
        self.assertEqual(float(wins), self.headline(), self.out)
        self.assertEqual(int(covered),
                         sim.coverage(sim.coverage_picks(self.n)))

    def test_the_last_pick_prints_the_increment_its_own_ladder_ends_on(self):
        inc, se = re.search(r"buys ([-+][\d.]+) against a paired \+-([\d.]+)",
                            self.out).groups()
        cum = self.ladder()
        self.assertAlmostEqual(float(inc), cum[-1] - cum[-2], delta=0.001)
        self.assertGreater(float(se), 0.0)

    def test_the_picks_it_prints_are_the_ones_the_rule_actually_makes(self):
        picks = re.search(r"picks: (.+)", self.out).group(1).split()
        self.assertEqual(picks, list(sim.coverage_picks(self.n)), self.out)
        cover = re.search(r"steered picks cover(.*)", self.out).group(1).split()
        self.assertEqual([int(c) for c in cover],
                         [sim.coverage(picks[:k])
                          for k in range(1, self.n + 1)])

    def test_the_percentages_it_quotes_match_its_own_ladder(self):
        cum = self.ladder()
        peak = max(cum)
        got = re.search(
            r"(\d+) picks? buys? ([-+]?\d+)% of the peak, (\d+) buy ([-+]?\d+)%",
            self.out)
        self.assertIsNotNone(got, self.out)
        a, sa, b, sb = (int(x) for x in got.groups())
        self.assertEqual(sa, round(100 * cum[a - 1] / peak))
        self.assertEqual(sb, round(100 * cum[b - 1] / peak))

    def test_a_15_team_offer_is_worth_less_than_having_all_30(self):
        real = float(re.search(r"random 15-team offer\s*:\s*([-+][\d.]+)",
                               self.out).group(1))
        full = self.headline()
        worst = float(re.search(r"worst %d .*:\s*([-+][\d.]+)" % self.n,
                                self.out).group(1))
        self.assertLess(real, full, self.out)
        self.assertLess(worst, real, self.out)
        self.assertGreater(full - worst, 2 * (full - real))

    def test_the_coverage_call_comes_off_the_two_r2s_it_prints(self):
        cov = float(re.search(r"nights COVERED.*R2 ([\d.]+)", self.out).group(1))
        summed = float(re.search(r"nights SUMMED.*R2 ([\d.]+)", self.out).group(1))
        self.assertIn("Coverage %s that comparison"
                      % ("wins" if cov > summed else "LOSES"), self.out)

class AuctionSteering(unittest.TestCase):
    def auction_bodies(self):
        full = sim.basis()
        return full, [full[i]["n"] for i in sim.auction_slots(full)]

    def test_steering_moves_the_auction_bodies_and_nobody_else(self):
        full, bodies = self.auction_bodies()
        a = sim.steer(full, ["BKN"] * len(bodies))
        b = sim.steer(full, ["CHI"] * len(bodies))
        moved = [p["n"] for p, x, y in zip(full, a, b)
                 if not p["tm"] == x["tm"] == y["tm"]]
        self.assertEqual(moved, bodies)
        owned = {p["n"] for p in sim.our_roster()}
        self.assertFalse(owned & set(moved), "steered a player we already own")
        auction = {p["n"] for p in sim.EXPANSION if p["n"].startswith("FA")}
        self.assertTrue(set(moved) <= auction,
                        "steered something we do not bid on")

    def test_a_steered_body_is_the_same_body_on_a_different_schedule(self):
        full, bodies = self.auction_bodies()
        for a, b in zip(full, sim.steer(full, ["BKN"] * len(bodies))):
            self.assertEqual((a["n"], a["avg"], a["gp"], a["elig"]),
                             (b["n"], b["avg"], b["gp"], b["elig"]))

    def test_a_target_list_that_is_not_one_team_per_slot_fails(self):
        full, bodies = self.auction_bodies()
        with self.assertRaises(ValueError):
            sim.steer(full, ["BKN"] * (len(bodies) + 1))
        with self.assertRaises(ValueError):
            sim.steer(full, ["BKN"] * (len(bodies) - 1))

    def test_an_unsigned_body_covers_the_same_nights_the_sim_gives_him(self):
        self.assertEqual(sim.coverage([sim.UNSIGNED]),
                         sim.coverage([sim.SIM_TM]))
