import unittest
from tests.harness import *

class WeekPoints(unittest.TestCase):
    def test_an_ever_present_body_totals_his_rate_times_his_games_in_it(self):
        body = sim.star(30.0, len(sim.team_nights("MEM")), ("C",), "MEM")
        self.assertEqual(len(sim.week_points(body)), len(sim.BRACKET))
        self.assertAlmostEqual(sum(sim.week_points(body)),
                               30.0 * sum(sim.bracket_games("MEM")))

    def test_a_body_projected_for_half_a_season_scores_half_the_window(self):
        tg = len(sim.team_nights("MEM"))
        iron = sim.star(30.0, tg, ("C",), "MEM")
        half = sim.star(30.0, tg // 2, ("C",), "MEM")
        self.assertAlmostEqual(
            sum(sim.week_points(half)) / sum(sim.week_points(iron)),
            (tg // 2) / tg)

    def test_a_gp_above_his_teams_own_game_count_is_capped_at_every_night(self):
        tg = len(sim.team_nights("MEM"))
        self.assertEqual(sim.week_points(sim.star(30.0, tg + 12, ("C",), "MEM")),
                         sim.week_points(sim.star(30.0, tg, ("C",), "MEM")))

    def test_two_identical_rates_split_on_their_nba_schedules(self):
        pair = {t: sum(sim.bracket_games(t)[-2:]) for t in sim.NBA_TEAMS}
        deep, thin = max(pair, key=pair.get), min(pair, key=pair.get)
        self.assertGreater(sum(sim.week_points(sim.star(30.0, 68, ("C",), deep))[-2:]),
                           sum(sim.week_points(sim.star(30.0, 68, ("C",), thin))[-2:]))

class MarginSpread(unittest.TestCase):
    def test_a_named_opponent_is_narrower_than_a_drawn_one_by_the_fields_spread(self):
        self.assertLess(sim.MARGIN_CV, sim.FIELD_MARGIN_CV)
        self.assertAlmostEqual(sim.FIELD_MARGIN_CV ** 2 - sim.MARGIN_CV ** 2,
                               sim.FIELD_LEVEL_CV ** 2)

    def test_the_drawn_opponent_carries_the_spread_of_the_field_it_comes_from(self):
        def level_sd(teams):
            rel = [[sim.SCORES[t][sim.PERIODS[i]["ordinal"]]
                    / statistics.mean(sim.SCORES[u][sim.PERIODS[i]["ordinal"]]
                                      for u in teams)
                    for i in sim.REGULAR] for t in teams]
            return statistics.stdev([statistics.mean(v) for v in rel])
        self.assertGreater(level_sd(sorted(sim.SCORES)),
                           level_sd(sim.BRACKET_TEAMS))
        self.assertGreater(sim.FIELD_LEVEL_CV, sim.LEVEL_CV)
        self.assertLess(sim.FIELD_LEVEL_CV, level_sd(sorted(sim.SCORES)))

    def test_the_split_recombines_onto_the_margins_it_was_taken_from(self):
        pooled = statistics.stdev(
            [(x - y) / statistics.mean(pf)
             for pf in ([sim.SCORES[t][sim.PERIODS[i]["ordinal"]]
                         for t in sim.BRACKET_TEAMS] for i in sim.REGULAR)
             for x, y in itertools.permutations(pf, 2)])
        both = math.sqrt(2 * (sim.WITHIN_CV ** 2 + sim.LEVEL_CV ** 2))
        self.assertLess(abs(both - pooled) / pooled, 0.01)

class RoundProbability(unittest.TestCase):
    def test_a_better_week_wins_more_often(self):
        p = [sim.round_pwin(mu, 0, sim.BANDS[-1].slots[0])
             for mu in (1000.0, 1400.0, 1600.0, 2200.0)]
        self.assertEqual(p, sorted(p))
        self.assertTrue(all(0.0 < x < 1.0 for x in p), p)

    def test_a_week_at_the_opponents_level_is_a_coin_flip(self):
        seed = sim.BANDS[-1].slots[0]
        opp, = sim.opp_dist(seed, 0)
        self.assertAlmostEqual(sim.round_pwin(opp.mus[0], 0, seed), 0.5)

    def test_the_opponent_level_is_measured_for_the_week_it_is_played_in(self):
        with cheap_monte_carlo(8):
            levels = [sim.opp_mean(w) for w in range(len(sim.BRACKET))]
            self.assertGreater(min(levels), sim.reg_mean())
        self.assertEqual(len(set(levels)), len(levels))

    def test_the_opponent_is_a_seed_rather_than_an_average_team(self):
        with cheap_monte_carlo(8):
            for w, i in enumerate(sim.BRACKET):
                whole = statistics.mean(t.mus[w] for t in sim.team_levels())
                with self.subTest(period=sim.PERIODS[i]["ordinal"]):
                    self.assertGreater(sim.opp_mean(w), whole)

    def test_sigma_scales_with_the_level_it_is_measured_against(self):
        cv = [sim.sigma(w) / sim.field_mean(w) for w in range(len(sim.BRACKET))]
        for c in cv:
            self.assertAlmostEqual(c, cv[0])
        self.assertGreater(sim.sigma(max(range(len(sim.BRACKET)),
                                         key=sim.field_mean)),
                           sim.sigma(min(range(len(sim.BRACKET)),
                                         key=sim.field_mean)))

    def test_sigma_is_the_same_for_every_team_in_the_draw(self):
        was = roster_mod.ROSTER
        try:
            with cheap_monte_carlo(8):
                mine = [sim.sigma(w) for w in range(len(sim.BRACKET))]
                roster_mod.ROSTER = THEIR_ROSTER
                self.assertEqual([sim.sigma(w) for w in range(len(sim.BRACKET))],
                                 mine)
        finally:
            roster_mod.ROSTER = was
