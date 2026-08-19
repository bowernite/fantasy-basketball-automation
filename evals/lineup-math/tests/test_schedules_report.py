import unittest
from tests.harness import *

class SchedulesReport(unittest.TestCase):
    """Every win figure README `Light-night coverage` quotes comes off this
    report, and the same choice gets printed three times, ladder, headline and
    coverage row, so the hazard is the three disagreeing.

    Rendered once for the class, since `schedules` sweeps 30 schedules at 11
    rates and is the priciest report here even at four trials"""

    @classmethod
    def setUpClass(cls):
        # The FA slots `pad` invents on the LOADED roster, which is what the
        # auction actually bids for: seven at 28 live bodies, three at 32
        cls.n = len(sim.auction_slots(sim.basis()))
        cls.out = render("schedules")

    def headline(self):
        """The best-slate win figure, the one number README quotes and the one
        three separate places on this page have to agree on"""
        m = re.search(r"best %d, all %d teams on offer\s*:\s*([-+][\d.]+)"
                      % (self.n, len(sim.NBA_TEAMS)), self.out)
        self.assertIsNotNone(m, self.out)
        return float(m.group(1))

    def ladder(self):
        """The cumulative +wins row, rung by rung"""
        rungs = re.search(r"cumulative \+wins(.*)", self.out).group(1).split()
        self.assertEqual(len(rungs), self.n, self.out)
        return [float(x) for x in rungs]

    def test_the_ladder_total_is_the_same_number_as_the_headline(self):
        """The ladder total and the best-slate headline are the same choice, so
        a reader given two figures has no way to tell which one to act on"""
        self.assertEqual(self.ladder()[-1], self.headline(), self.out)

    def test_the_stacked_slate_row_is_the_slate_times_the_deepest_schedule(self):
        """The whole slate on one NBA team cannot sum past that many times the
        deepest light-night schedule. The report prints the sum and the
        coverage side by side, so the gap between them has to be the finding
        rather than an arithmetic error"""
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
        """The printed light-nights-per-team table, as {team: count}"""
        listed = {}
        for n, tms in re.findall(r"^ +(\d+) +((?:[A-Z]{2,4} ?)+)$", self.out, re.M):
            for tm in tms.split():
                listed[tm] = int(n)
        return listed

    def test_every_team_is_listed_under_its_own_light_night_count(self):
        """The one table here a reader ACTS on, "prefer a body from these
        teams", and the one README republishes verbatim. A team dropped from
        it, or filed under a neighbouring count, sends the auction after the
        wrong schedule and no win figure above would look any different"""
        self.assertEqual(self.per_team_counts(), light_nights_per_team())

    def per_body_rows(self):
        """The 30-schedule sweep, one row per body grade (rate, meanPF, sdPF,
        sd wins, sdRate, spanRate)"""
        rows = [tuple(map(float, m)) for m in re.findall(
            r"^ +(\d+) +(\d+) +([\d.]+) +([\d.]+) +([\d.]+) +([\d.]+)$",
            self.out, re.M)]
        self.assertTrue(rows, self.out)
        return rows

    def test_the_schedule_swing_converts_through_the_one_pf_to_wins(self):
        """The only place the file converts a PF spread into the rate points a
        board prices in, and the whole tiebreak is denominated by it. A second
        PF to wins conversion living here would quote the threshold in a
        currency no other number on the page uses, and every row would still
        look plausible"""
        for rate, _, sdpf, sdwins, _, _ in self.per_body_rows():
            with self.subTest(rate=rate):
                self.assertAlmostEqual(sdwins, sim.pf_wins(sdpf), delta=0.001)

    def test_the_schedule_spread_shrinks_as_the_body_gets_better(self):
        """The shape the section is sold on. The body's own value climbs far
        faster than the schedule spread under it, so the schedule matters most
        exactly where the body matters least, the auction tier"""
        rows = self.per_body_rows()
        self.assertEqual([r[1] for r in rows], sorted(r[1] for r in rows))
        self.assertGreater(rows[0][4], rows[-1][4] * 1.5)

    def test_the_sub_proportional_line_comes_off_its_own_table(self):
        """The line under the table quotes four of its numbers. If a re-cut
        ever makes the schedule spread grow WITH the body, this stops being
        sub-proportional and the whole "cheap tiebreak, never a price" framing
        goes with it"""
        rows = self.per_body_rows()
        body = rows[-1][1] / rows[0][1]
        swing = rows[-1][2] / rows[0][2]
        if body > swing:
            self.assertIn("SUB-PROPORTIONAL", self.out)
        else:
            self.assertNotIn("SUB-PROPORTIONAL", self.out)
        self.assertIn("the body grows %dx from rate %d to %d while the"
                      % (round(body), rows[0][0], rows[-1][0]), self.out)
        self.assertIn("schedule sd under it grows only %dx" % round(swing),
                      self.out)
        self.assertIn("%.1f rate points at %d and %.1f at %d"
                      % (rows[0][4], rows[0][0], rows[-1][4], rows[-1][0]),
                      self.out)

    def test_the_threshold_it_prints_comes_off_the_row_we_actually_bid_at(self):
        """The rule is spent at 8-14 FPts and nowhere else, and the exchange
        rate halves by rate 40, so a threshold quoted off the wrong row is ~2x
        wrong in the direction that overpays. It is the one number from this
        report that gets carried into a live acquisition"""
        rows = self.per_body_rows()
        thresh = re.search(r"so ~([\d.]+) rate points is the threshold",
                           self.out)
        self.assertIsNotNone(thresh, self.out)
        self.assertEqual(float(thresh.group(1)), round(rows[0][4], 1))
        self.assertLessEqual(rows[0][0], 8)

    def test_the_spread_row_uses_the_same_picks_as_the_headline(self):
        """Third place the same choice gets printed, and the one sitting in a
        table beside a stack it is supposed to beat. A coverage row scoring its
        own private best slate splits the headline in two again"""
        covered, wins = re.search(
            r"spread best %d\s*:\s*\d+ body-nights summed, (\d+) distinct, "
            r"([-+][\d.]+) wins" % self.n, self.out).groups()
        self.assertEqual(float(wins), self.headline(), self.out)
        self.assertEqual(int(covered),
                         sim.coverage(sim.coverage_picks(self.n)))

    def test_the_last_picks_verdict_matches_the_sigma_it_prints(self):
        """The figure a reader acts on, "stop steering after k". On a
        counterparty file the ladder can peak at seven, so whether the last
        pick bought anything is a comparison against its own paired sigma
        rather than a fixed sentence"""
        inc, se = re.search(r"buys ([-+][\d.]+) against a paired \+-([\d.]+)",
                            self.out).groups()
        self.assertIn("which is %s" % ("nothing measurable"
                                       if abs(float(inc)) < 2 * float(se)
                                       else "a REAL increment"), self.out)

    def test_the_picks_it_prints_are_the_ones_the_rule_actually_makes(self):
        """The rungs are only comparable because every one of them is the same
        greedy-on-coverage rule taken k deep (`CoveragePicks`), and README
        quotes the picks and the nights they reach as fact. A ladder on any
        other rule reads as a measurement of steering and is a measurement of
        something else"""
        picks = re.search(r"picks: (.+)", self.out).group(1).split()
        self.assertEqual(picks, list(sim.coverage_picks(self.n)), self.out)
        cover = re.search(r"steered picks cover(.*)", self.out).group(1).split()
        self.assertEqual([int(c) for c in cover],
                         [sim.coverage(picks[:k])
                          for k in range(1, self.n + 1)])

    def test_the_percentages_it_quotes_match_its_own_ladder(self):
        """The only sentence here telling a reader where to stop paying
        attention, and it is a ratio of two numbers on the row above it. The
        ladder is re-cut every season and the sentence has to move with it"""
        cum = self.ladder()
        peak = max(cum)
        got = re.search(
            r"(\d+) picks? buys? (\d+)% of the peak and (\d+) buy (\d+)%",
            self.out)
        self.assertIsNotNone(got, self.out)
        a, sa, b, sb = (int(x) for x in got.groups())
        self.assertEqual(sa, round(100 * cum[a - 1] / peak))
        self.assertEqual(sb, round(100 * cum[b - 1] / peak))

    def test_a_15_team_offer_is_worth_less_than_having_all_30(self):
        """Fewer teams on the block is strictly less to choose from. Printing
        the two the other way round, or reading the wrong one into an eval,
        doubles the case for a rule already sitting at the 0.1-win floor"""
        real = float(re.search(r"random 15-team offer\s*:\s*([-+][\d.]+)",
                               self.out).group(1))
        full = self.headline()
        worst = float(re.search(r"worst %d .*:\s*([-+][\d.]+)" % self.n,
                                self.out).group(1))
        self.assertLess(real, full, self.out)
        self.assertLess(worst, real, self.out)
        self.assertGreater(full - worst, 4 * (full - real))

    def test_the_coverage_call_comes_off_the_two_r2s_it_prints(self):
        """"Coverage, not a summed night count" is the section's central claim
        and this report is the only thing that measures it, so the verdict is
        DERIVED from the two R2s and a re-cut that flips them flips the
        sentence too"""
        cov = float(re.search(r"nights COVERED.*R2 ([\d.]+)", self.out).group(1))
        summed = float(re.search(r"nights SUMMED.*R2 ([\d.]+)", self.out).group(1))
        self.assertIn("Coverage %s that comparison"
                      % ("wins" if cov > summed else "LOSES"), self.out)

class AuctionSteering(unittest.TestCase):
    """Sept '26 fills 10 slots, 3 rookie picks and a 7-man FA auction (`league-
    info`), but only the FA slots `pad` actually invents on THIS roster are a
    schedule we CHOOSE -- a roster carrying 32 bodies has three of them, not
    seven. A steering figure that re-points any other body prices a choice
    nobody has"""

    def auction_bodies(self):
        """The padded roster and the FA grades on it a September auction fills.
        Counted live: the FA slots run out as the live roster grows, and seven
        typed against a roster that has three steers real players"""
        full = sim.basis()
        return full, [full[i]["n"] for i in sim.auction_slots(full)]

    def test_steering_moves_the_auction_bodies_and_nobody_else(self):
        """Two targets, so a body that already sat on the target team cannot
        pass for one that stayed put. The rookie grades carry a schedule too,
        so a rule reaching one body further would price a pick we do not get to
        aim, and would still print a full slate of steered bodies"""
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
        """The whole comparison is schedule against schedule at matched grade,
        so a steered body that also picked up a rate or a slot group would book
        those as the schedule's doing"""
        full, bodies = self.auction_bodies()
        for a, b in zip(full, sim.steer(full, ["BKN"] * len(bodies))):
            self.assertEqual((a["n"], a["avg"], a["gp"], a["elig"]),
                             (b["n"], b["avg"], b["gp"], b["elig"]))

    def test_a_target_list_that_is_not_one_team_per_slot_fails(self):
        """One team per slot THIS roster has, which is a fact about the loaded
        roster rather than a loop bound. Silently steering the first three of a
        seven-team list answers a different question and still prints a win
        figure"""
        full, bodies = self.auction_bodies()
        with self.assertRaises(ValueError):
            sim.steer(full, ["BKN"] * (len(bodies) + 1))
        with self.assertRaises(ValueError):
            sim.steer(full, ["BKN"] * (len(bodies) - 1))

    def test_an_unsigned_body_covers_the_same_nights_the_sim_gives_him(self):
        """`team_nights` puts an unsigned body on SIM_TM rather than inventing
        him a calendar, and coverage cannot quietly disagree with it and call
        him a body that covers nothing"""
        self.assertEqual(sim.coverage([sim.UNSIGNED]),
                         sim.coverage([sim.SIM_TM]))
