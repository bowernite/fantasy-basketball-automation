import unittest
from tests.harness import *

class WeekPoints(unittest.TestCase):
    """`W20`-`W23` as `Eval Definitions` defines them: a rate times the games
    that player's NBA team plays inside the period, times the share of the
    season he is projected available for"""

    def test_an_ever_present_body_totals_his_rate_times_his_games_in_it(self):
        body = sim.star(30.0, len(sim.team_nights("MEM")), ("C",), "MEM")
        self.assertEqual(len(sim.week_points(body)), len(sim.BRACKET))
        self.assertAlmostEqual(sum(sim.week_points(body)),
                               30.0 * sum(sim.bracket_games("MEM")))

    def test_a_body_projected_for_half_a_season_scores_half_the_window(self):
        """The column is an EXPECTATION, so the share of the season he is
        projected available is in it: same rate, same NBA schedule, half the
        games and he is worth half the week"""
        tg = len(sim.team_nights("MEM"))
        iron = sim.star(30.0, tg, ("C",), "MEM")
        half = sim.star(30.0, tg // 2, ("C",), "MEM")
        self.assertAlmostEqual(
            sum(sim.week_points(half)) / sum(sim.week_points(iron)),
            (tg // 2) / tg)

    def test_a_gp_above_his_teams_own_game_count_is_capped_at_every_night(self):
        """`season` suits a body up for `min(gp, team games)` nights, so this
        column agrees with the sim only if it caps the same way: a GP over his
        team's game count is a body who plays every night, not one worth more
        than his rate"""
        tg = len(sim.team_nights("MEM"))
        self.assertEqual(sim.week_points(sim.star(30.0, tg + 12, ("C",), "MEM")),
                         sim.week_points(sim.star(30.0, tg, ("C",), "MEM")))

    def test_two_identical_rates_split_on_their_nba_schedules(self):
        """The whole reason the column exists. Same rate, same slot, 8 games in
        the last two rounds against 6, and nothing in a season rate says so"""
        pair = {t: sum(sim.bracket_games(t)[-2:]) for t in sim.NBA_TEAMS}
        deep, thin = max(pair, key=pair.get), min(pair, key=pair.get)
        self.assertGreater(sum(sim.week_points(sim.star(30.0, 68, ("C",), deep))[-2:]),
                           sum(sim.week_points(sim.star(30.0, 68, ("C",), thin))[-2:]))

class MarginSpread(unittest.TestCase):
    """`sigma` is a margin between two weekly scores, and which spreads belong
    inside it depends on what the model has already priced. An opponent the
    draw NAMES carries only its own week-to-week deviation, because its level
    is in `mus`; an opponent drawn unidentified out of the field carries the
    field's level spread on top"""

    def test_a_named_opponent_is_narrower_than_a_drawn_one_by_the_fields_spread(self):
        self.assertLess(sim.MARGIN_CV, sim.FIELD_MARGIN_CV)
        self.assertAlmostEqual(sim.FIELD_MARGIN_CV ** 2 - sim.MARGIN_CV ** 2,
                               sim.FIELD_LEVEL_CV ** 2)

    def test_the_drawn_opponent_carries_the_spread_of_the_field_it_comes_from(self):
        """`reg_mean` draws that opponent from all 11 other teams and the
        bracket's 8 are the top of the league by construction, so their levels
        are a truncated sample of it: last season the whole league's spread was
        twice the seeds'. A regular matchup priced on the seeds' spread is
        priced against a field it is not drawn from"""
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
        """Put both sides' level spread and both sides' weekly spread back
        together and it has to land ON the pair margins the eight seeds
        actually scored -- a margin is a difference, so the period mean each
        score was divided by cancels out of it and nothing about the split
        survives into the total. A split that lands short is a split that has
        eaten variance the margin needs, and every `sigma` here is that total"""
        pooled = statistics.stdev(
            [(x - y) / statistics.mean(pf)
             for pf in ([sim.SCORES[t][sim.PERIODS[i]["ordinal"]]
                         for t in sim.BRACKET_TEAMS] for i in sim.REGULAR)
             for x, y in itertools.permutations(pf, 2)])
        both = math.sqrt(2 * (sim.WITHIN_CV ** 2 + sim.LEVEL_CV ** 2))
        self.assertLess(abs(both - pooled) / pooled, 0.01)

class RoundProbability(unittest.TestCase):
    """One bracket round is one week's PF against the opponents that round can
    produce, so the model is a normal CDF on a margin mixed over the draw. What
    it is fitted to is the argument"""

    def test_a_better_week_wins_more_often(self):
        p = [sim.round_pwin(mu, 0, sim.BANDS[-1].slots[0])
             for mu in (1000.0, 1400.0, 1600.0, 2200.0)]
        self.assertEqual(p, sorted(p))
        self.assertTrue(all(0.0 < x < 1.0 for x in p), p)

    def test_a_week_at_the_opponents_level_is_a_coin_flip(self):
        """R1 is the one round nobody has survived into, so its opponent is a
        named team rather than a mixture and the margin is readable straight
        off `mus`. Every later round mixes, and a week at the mixture's mean
        is not a coin flip -- the mixture is what makes it not one"""
        seed = sim.BANDS[-1].slots[0]
        opp, = sim.opp_dist(seed, 0)
        self.assertAlmostEqual(sim.round_pwin(opp.mus[0], 0, seed), 0.5)

    def test_the_opponent_level_is_measured_for_the_week_it_is_played_in(self):
        """Periods run 28-56 NBA games and the bracket's four are all at the
        dense end, so an opponent quoted at the season mean is quoted for a
        week nobody plays. Which of the four is heaviest is the FIELD's own
        schedules, not the league-wide game count -- the two disagree here"""
        with cheap_monte_carlo(8):
            levels = [sim.opp_mean(w) for w in range(len(sim.BRACKET))]
            self.assertGreater(min(levels), sim.reg_mean())
        self.assertEqual(len(set(levels)), len(levels))

    def test_the_opponent_is_a_seed_rather_than_an_average_team(self):
        """A playoff opponent is one of the eight. Priced off all 12 the bar
        carries a team nobody can meet in the bracket, which lowers it in
        every round"""
        with cheap_monte_carlo(8):
            for w, i in enumerate(sim.BRACKET):
                whole = statistics.mean(t.mus[w] for t in sim.team_levels())
                with self.subTest(period=sim.PERIODS[i]["ordinal"]):
                    self.assertGreater(sim.opp_mean(w), whole)

    def test_sigma_scales_with_the_level_it_is_measured_against(self):
        """A margin sd is a dispersion around a weekly level, so a denser week
        carries a proportionally wider one. Held flat, the densest bracket week
        reads as the most certain"""
        cv = [sim.sigma(w) / sim.field_mean(w) for w in range(len(sim.BRACKET))]
        for c in cv:
            self.assertAlmostEqual(c, cv[0])
        self.assertGreater(sim.sigma(max(range(len(sim.BRACKET)),
                                         key=sim.field_mean)),
                           sim.sigma(min(range(len(sim.BRACKET)),
                                         key=sim.field_mean)))

    def test_sigma_is_the_same_for_every_team_in_the_draw(self):
        """Every game in the bracket is priced with it, including the ones
        deciding who a later opponent is. Scaled off the field LESS the loaded
        roster, the eight seeds would each be running a bracket of their own"""
        was = roster_mod.ROSTER
        try:
            with cheap_monte_carlo(8):
                mine = [sim.sigma(w) for w in range(len(sim.BRACKET))]
                roster_mod.ROSTER = THEIR_ROSTER
                self.assertEqual([sim.sigma(w) for w in range(len(sim.BRACKET))],
                                 mine)
        finally:
            roster_mod.ROSTER = was
