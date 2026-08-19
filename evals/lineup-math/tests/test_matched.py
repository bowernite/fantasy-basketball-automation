import unittest
from tests.harness import *

class MatchedBasis(unittest.TestCase):
    """`mu_us` and `mu_opp` are the SAME measurement of two rosters -- every
    team's file through this sim's own pipeline. Anything else prices a margin
    between two quantities that differ by more than the rosters do, and the
    difference lands in `P(round)` as an edge nobody has"""

    def test_inflating_every_teams_rates_leaves_every_band_where_it_was(self):
        """The property the matched basis IS. A league-wide 10% is a rescaling
        of the whole board, not an edge: our week grows and so does every
        opponent's, so no published figure may move. An opponent level taken
        off anything but this pipeline reads the inflation as an edge and books
        it.

        It does not cancel EXACTLY. `league_rates` reaches a rate through
        `projected_rate`, and the bodies `pad` tops each roster up to 38 with
        carry fixed grades no rate feed serves, so a team holding more real
        bodies rescales harder. Measured at 0.008 of a `P(title)`, which is
        what this tolerance sits just above: a bound on that leak, not slack.

        On BANDS rather than on single rounds, because a band averages over its
        four seeds. One round from one seed is one slot of the draw, and the
        7th and 8th projected seeds are 0.3% of a season apart -- they trade
        places under a re-run, which re-points that slot at a different team"""
        with cheap_monte_carlo(8):
            mus = sim.bracket_weeks(sim.basis())
            base = [sim.title_prob(mus, b) for b in sim.BANDS]
            with league_rates(1.10):
                mus = sim.bracket_weeks(sim.basis())
                got = [sim.title_prob(mus, b) for b in sim.BANDS]
        for b, was, now in zip(sim.BANDS, base, got):
            with self.subTest(band=b.label):
                self.assertAlmostEqual(was, now, delta=0.012)

    def test_the_field_is_the_top_eight_projected_teams(self):
        """Which teams seed next season is unknown, so the field is the rule
        stated in `method.md`: the league sorted on projected season PF, cut at
        the bracket's own size"""
        with cheap_monte_carlo(8):
            levels, field = sim.team_levels(), sim.field()
        self.assertEqual(len(field), len(sim.BRACKET_TEAMS))
        self.assertEqual(list(field), list(levels)[:len(field)])
        self.assertGreater(min(t.pf for t in field),
                           max(t.pf for t in levels[len(field):]))

    def test_a_team_is_never_its_own_opponent(self):
        """We are the strongest projected roster, so leaving ourselves in the
        field pulls the bar we are measured against up toward us and shrinks
        the edge by an eighth of it"""
        with cheap_monte_carlo(8):
            field = sim.field()
            ours = [t for t in field
                    if t.path == os.path.basename(roster_mod.ROSTER)]
            self.assertTrue(ours, "our own roster is not a projected seed")
            for w in range(len(sim.BRACKET)):
                with self.subTest(round=w):
                    self.assertAlmostEqual(
                        sim.opp_mean(w),
                        statistics.mean(t.mus[w] for t in field
                                        if t not in ours))

    def test_last_seasons_roster_files_are_not_a_second_league(self):
        """`fetch_data.py roster` writes `roster-<id>-<season>.json` and leaves
        the previous season's beside it, so the roll puts 24 files in the
        directory. Read season-blind the league is 24 teams, one franchise can
        take two seats in `field()`, and the bracket that comes out is a draw
        nobody plays -- with no short-field guard to trip"""
        stale = os.path.join(sim.HERE, "roster-161025-2020-21.json")
        with open(stale, "w") as f:
            f.write(read_text(os.path.join(sim.HERE, roster_mod.ROSTER)))
        try:
            with cheap_monte_carlo(4):
                teams = json.loads(read_text(os.path.join(
                    sim.HERE, "teams-%s.json" % fetch_data.SEASON_TAG)))
                self.assertEqual(len(sim.team_levels()), len(teams))
        finally:
            os.remove(stale)

    def test_a_roster_priced_by_path_is_left_out_of_its_own_field(self):
        """`basis(path)` reads a file without moving the module global, so the
        import path in `sim.py`'s module docstring hands a counterparty's
        roster to a bracket that still believes ours is loaded: the
        counterparty is seeded against a clone of itself and the one seed it
        could never avoid drops out of the draw. Whose roster it is comes in as
        an argument here, the way every other import entry point takes it"""
        with cheap_monte_carlo(8):
            for t in sim.field():
                with self.subTest(team=t.path):
                    self.assertNotIn(t.path,
                                     [o.path for o in sim.opponents(t.path)])

    def test_a_stronger_roster_wins_more_rounds_than_a_weaker_one(self):
        """End to end: the only thing left between two teams' `P(round)` is
        the rosters, which is what the whole model is for"""
        seed = sim.BANDS[-1].slots[0]
        with cheap_monte_carlo(8):
            best, worst = sim.team_levels()[0], sim.team_levels()[-1]
            for w in range(len(sim.BRACKET)):
                with self.subTest(round=w):
                    self.assertGreater(sim.round_pwin(best.mus[w], w, seed),
                                       sim.round_pwin(worst.mus[w], w, seed))

class BracketWeeks(unittest.TestCase):
    """`mu_us` for a round is one week of the same sim every other figure here
    comes out of -- optimal nightly lineups, projected GP -- scored over that
    week's NBA nights and no others"""

    def test_a_week_scores_that_weeks_nights_and_no_others(self):
        """An ironman on one NBA team scores his rate once per team game in
        the period. Anything else and the run is bucketing the wrong nights"""
        body = sim.star(30.0, 82, ("C",), "MEM", "IRON")
        self.assertEqual([round(x, 6) for x in sim.bracket_weeks([body], trials=2)],
                         [30.0 * g for g in sim.bracket_games("MEM")])

    def test_the_last_three_rounds_score_nothing_toward_the_standings(self):
        """Periods 21-23 are outside `SCORED`, so a run on the standings basis
        never reaches them at all"""
        for i in sim.BRACKET[1:]:
            for n in sim.period_nights(i):
                with self.subTest(night=sim.NIGHTS[n][0]):
                    self.assertIsNone(sim.WEEK_OF[n])
                    self.assertIsNotNone(sim.BRACKET_CAL.week_of[n])

    def test_swapping_a_body_for_its_own_twin_moves_nothing(self):
        """Common random numbers, in the bracket path too. Without them the
        two rosters draw different availability and a no-op swap prints a
        `Delta P(title)` several times what a real one is worth"""
        full = sim.basis()
        p = sim.our_roster()[0]
        twin = sim.star(p["avg"], p["gp"], p["elig"], p["tm"], "TWIN")
        self.assertEqual(sim.bracket_weeks(full, trials=8),
                         sim.bracket_weeks(sim.swap(full, [p["n"]], [twin]),
                                           trials=8))
