import unittest
from tests.harness import *

class AbsenceBlocks(unittest.TestCase):
    """`_availability` places IL blocks CIRCULARLY, so the onset scan has to be
    circular too. ~26% of player-seasons come out with both their first and
    last team-game night absent, and a left-to-right scan splits that one block
    in two, letting a single injury surprise you twice"""

    def test_a_block_that_wraps_the_end_of_the_season_is_one_block(self):
        # his team-game nights, absent for 50 then 10 and 20, so ONE block
        self.assertEqual(sim._onsets([10, 20, 30, 40, 50], {30, 40}), [50])

    def test_the_block_statistics_are_measured_on_the_roster_you_pass(self):
        """The lock-in correction is worth exactly the ratio of absence NIGHTS
        to absence BLOCKS, and no fixed pair of numbers describes both rosters,
        so it is measured live per roster"""
        small = sim.absence_blocks(sim.our_roster(), seeds=6)
        big = sim.absence_blocks(sim.our_roster() + sim.EXPANSION, seeds=6)
        self.assertGreater(big["nights"], small["nights"] + 100)
        self.assertGreater(small["mean_block"], 7.0)

class SurpriseScratches(unittest.TestCase):
    """A scratch can only surprise a lineup-setter on the FIRST night of an
    absence block, since after that he is on the public injury report. Drawing
    the surprise from every absence night instead makes the lock-in penalty
    ~10x too large"""

    def test_a_season_long_absence_can_only_surprise_you_once(self):
        """EXACTLY once, both ways. More than one is the whole season sampled
        as surprises, and none at all is the other half of the circular fix,
        since with nothing played there is no night before that he played and a
        scan needing one drops the opening night that IS the surprise"""
        glass = [dict(sim.star(45, 0, ("SF", "PF"), "LAL", "GLASS"), surprise=1.0)]
        for seed in (101, 202, 303):
            _, starts, pts, _ = sim.season(glass, seed=seed, bursty=True)
            self.assertEqual(starts["GLASS"], 1)
            self.assertEqual(pts["GLASS"], 0.0)      # started, scores nothing

    def test_a_lone_scattered_absence_is_still_a_surprise(self):
        # his one missed night is its own onset, and ~79% of NBA nights fall in
        # the scored periods, so over 20 seeds it lands in window ~16 times
        """Guard on the other side. A rest day IS the first night of its own
        block, so the correction must not suppress it, and a high-GP veteran
        resting scattered single games is the shape the lock-in costs the most
        """
        rester = [dict(sim.star(45, 81, ("SF", "PF"), "LAL", "REST"), surprise=1.0)]
        wasted = 0
        for seed in range(101, 121):
            _, starts, pts, _ = sim.season(rester, seed=seed, bursty=True)
            wasted += starts["REST"] - round(pts["REST"] / 45)
        self.assertGreaterEqual(wasted, 10)

    def test_a_small_surprise_rate_still_costs_something(self):
        """Each block has to be an INDEPENDENT draw. `round(q x blocks)`
        truncates to zero for every player with fewer than ~5 absence blocks,
        which is most of a roster, so a 10% rate silently becomes 0% and the
        corrected penalty reads as exactly nothing"""
        full = sim.our_roster() + sim.EXPANSION
        base = sim.run(full, trials=40, bursty=True)["pf"]
        risky = sim.run(full, trials=40, bursty=True, surprise=0.10)["pf"]
        self.assertLess(risky, base - 20)

    def test_a_scratch_you_started_costs_the_bench_body_who_would_have_played(self):
        """Lineups lock before tip, so the slot is spent, not freed. Ten bodies
        all on one NBA team and all eligible everywhere, so every night has one
        more body than the nine slots: starting the scratched man benches the
        10th, and what the season loses is HIS rate, not the scratched man's"""
        every = ("PG", "SG", "SF", "PF", "C")
        def deep(spare):
            return ([sim.star(50.0, 41, every, "MEM", "OUT")]
                    + [sim.star(40.0 - i, 82, every, "MEM", "B%d" % i)
                       for i in range(1, 9)]
                    + [sim.star(spare, 82, every, "MEM", "SPARE")])
        cost = {}
        for spare in (31.0, 10.0):
            r = deep(spare)
            cost[spare] = (sim.run(r, trials=3)["pf"]
                           - sim.run(r, trials=3, surprise=1.0)["pf"])
        self.assertGreater(cost[31.0], 0)
        self.assertAlmostEqual(cost[31.0] / 31.0, cost[10.0] / 10.0, places=6)

    def test_a_scratch_costs_nothing_when_there_is_nobody_to_bench(self):
        """The other half of the same claim, and the one that says the cost is
        the FOREGONE body rather than the scratched man's own points. Nine
        bodies for nine slots: whether he is started or known out, the same
        eight teammates play and the night scores the same"""
        every = ("PG", "SG", "SF", "PF", "C")
        thin = ([sim.star(50.0, 41, every, "MEM", "OUT")]
                + [sim.star(40.0 - i, 82, every, "MEM", "B%d" % i)
                   for i in range(1, 9)])
        self.assertEqual(sim.run(thin, trials=3, surprise=1.0)["pf"],
                         sim.run(thin, trials=3)["pf"])

class WeeklyPointsColumn(unittest.TestCase):
    """`wk` is the per-period points column a bracket opponent's level is
    measured from. A run that buckets a night into the wrong period is
    invisible in the season total and wrong everywhere the column is read"""

    def test_a_period_totals_its_own_nights_and_no_others(self):
        """An ironman on one NBA team scores his rate once per team game in the
        period, so every one of the 20 entries is pinned. Shift the buckets by
        one and `pf` is untouched while most of the column moves"""
        body = sim.star(30.0, 82, ("C",), "MEM", "IRON")
        out = sim.run([body], trials=2)
        played = set(sim.team_nights("MEM"))
        self.assertEqual(
            [round(x, 6) for x in out["wk"]],
            [round(30.0 * len(played & set(sim.period_nights(i))), 6)
             for i in sim.SCORED])

class AvailabilityIsSeasonLong(unittest.TestCase):
    """GP/82 is a season-long rate, drawn over the WHOLE season even when only
    the bracket weeks are scored. Restrict the draw to the scored window and
    every bracket column comes out systematically wrong"""

    def test_a_41_gp_body_scores_about_half_the_bracket_an_ironman_does(self):
        """Not zero and not full: the four bracket rounds are a sample of a
        season-long absence pattern, so a half-season body loses about half of
        them. Zero means the draw ran out before the bracket, full means it
        never ran on the rounds being scored"""
        iron = sim.run([sim.star(30.0, 82, ("C",), "MEM", "IRON")],
                       trials=60, cal=sim.BRACKET_CAL)
        half = sim.run([sim.star(30.0, 41, ("C",), "MEM", "HALF")],
                       trials=60, cal=sim.BRACKET_CAL)
        self.assertEqual(
            [round(x, 6) for x in iron["wk"]],
            [round(30.0 * g, 6) for g in sim.bracket_games("MEM")])
        self.assertAlmostEqual(sum(half["wk"]) / sum(iron["wk"]), 0.5, delta=0.06)

class DuplicateNames(unittest.TestCase):
    """`season` scores a night off a `{name: points}` built from the players
    available, so two bodies sharing a name collapse into one entry and the
    night's total counts whichever one the dict kept, twice. `star()` names
    every synthetic body the same by default, and the league also rosters two
    real Jaylin Williamses"""

    def test_two_bodies_sharing_a_name_score_as_two_bodies(self):
        roster = [sim.star(40, 82, ("SF", "PF"), "LAC", "TWIN"),
                  sim.star(10, 82, ("PG", "SG"), "LAC", "TWIN")]
        distinct = [dict(roster[0], n="A"), dict(roster[1], n="B")]
        self.assertAlmostEqual(sim.run(roster, trials=4)["pf"],
                               sim.run(distinct, trials=4)["pf"], places=6)

    def test_two_unnamed_bodies_in_one_deal_stay_two_distinct_bodies(self):
        """The documented multi-piece path, `swap(full, [a, b], [star(),
        star()])`, names neither incoming body. PF survives that, since it is
        keyed on the roster index, but everything a reader does with the deal
        afterwards does not, the two collapse into one `season` points row and
        moving either of them on reads as ambiguous"""
        full = sim.basis()
        deal = sim.swap(full, ["Jalen Suggs", "Coby White"],
                        [sim.star(45, 68, ("PG", "SG")), sim.star(12, 68, ("C",))])
        incoming = [p["n"] for p in deal if p["n"] not in {q["n"] for q in full}]
        self.assertEqual(len(set(incoming)), 2, incoming)
        pts = sim.season(deal, seed=101)[2]
        self.assertGreater(pts[incoming[0]], pts[incoming[1]])
        sim.swap(deal, [incoming[0]], [sim.star(30)])

    def test_trading_away_an_ambiguous_name_fails_instead_of_guessing(self):
        """Which of the two Jaylin Williamses left is not a question `swap` can
        answer, and the roster it returns is a different trade either way"""
        roster = [sim.star(40, 82, ("SF", "PF"), "LAC", "Jaylin Williams"),
                  sim.star(20, 82, ("C",), "OKC", "Jaylin Williams"),
                  sim.star(30, 82, ("PG", "SG"), "LAC", "Someone Else")]
        with self.assertRaises(KeyError):
            sim.swap(roster, ["Jaylin Williams"], [sim.star(45)])
        self.assertGreater(sim.run(roster, trials=2)["pf"], 0)
