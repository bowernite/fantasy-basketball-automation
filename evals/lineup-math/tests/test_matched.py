import unittest
from tests.harness import *

class MatchedBasis(unittest.TestCase):
    def test_inflating_every_teams_rates_leaves_every_band_where_it_was(self):
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
        with cheap_monte_carlo(8):
            levels, field = sim.team_levels(), sim.field()
        self.assertEqual(len(field), len(sim.BRACKET_TEAMS))
        self.assertEqual(list(field), list(levels)[:len(field)])
        self.assertGreater(min(t.pf for t in field),
                           max(t.pf for t in levels[len(field):]))

    def test_a_team_is_never_its_own_opponent(self):
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
        stale = os.path.join(sim.ROSTER_DIR, "roster-161025-2020-21.json")
        with open(stale, "w") as f:
            f.write(read_text(os.path.join(sim.ROSTER_DIR, roster_mod.ROSTER)))
        try:
            with cheap_monte_carlo(4):
                teams = json.loads(read_text(os.path.join(
                    sim.DATA_DIR, "teams-%s.json" % fetch_data.SEASON_TAG)))
                self.assertEqual(len(sim.team_levels()), len(teams))
        finally:
            os.remove(stale)

    def test_a_roster_priced_by_path_is_left_out_of_its_own_field(self):
        with cheap_monte_carlo(8):
            for t in sim.field():
                with self.subTest(team=t.path):
                    self.assertNotIn(t.path,
                                     [o.path for o in sim.opponents(t.path)])

    def test_a_stronger_roster_wins_more_rounds_than_a_weaker_one(self):
        seed = sim.BANDS[-1].slots[0]
        with cheap_monte_carlo(8):
            best, worst = sim.team_levels()[0], sim.team_levels()[-1]
            for w in range(len(sim.BRACKET)):
                with self.subTest(round=w):
                    self.assertGreater(sim.round_pwin(best.mus[w], w, seed),
                                       sim.round_pwin(worst.mus[w], w, seed))

class BracketWeeks(unittest.TestCase):
    def test_a_week_scores_that_weeks_nights_and_no_others(self):
        body = sim.star(30.0, 82, ("C",), "MEM", "IRON")
        self.assertEqual([round(x, 6) for x in sim.bracket_weeks([body], trials=2)],
                         [30.0 * g for g in sim.bracket_games("MEM")])

    def test_the_last_three_rounds_score_nothing_toward_the_standings(self):
        for i in sim.BRACKET[1:]:
            for n in sim.period_nights(i):
                with self.subTest(night=sim.NIGHTS[n][0]):
                    self.assertIsNone(sim.WEEK_OF[n])
                    self.assertIsNotNone(sim.BRACKET_CAL.week_of[n])

    def test_swapping_a_body_for_its_own_twin_moves_nothing(self):
        full = sim.basis()
        p = sim.our_roster()[0]
        twin = sim.star(p["avg"], p["gp"], p["elig"], p["tm"], "TWIN")
        self.assertEqual(sim.bracket_weeks(full, trials=8),
                         sim.bracket_weeks(sim.swap(full, [p["n"]], [twin]),
                                           trials=8))
