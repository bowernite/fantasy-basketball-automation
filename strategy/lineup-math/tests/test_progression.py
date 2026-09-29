import unittest
from tests.harness import *
from simlib import progression as prog


def vet(**kw):
    p = dict(rate1=30.0, gp1=65.0, age1=27.0, stage="V", cy1=6, bpm=1.0,
             gp_last=65.0)
    p.update(kw)
    return p


class YearOne(unittest.TestCase):
    def test_year_one_is_the_projection_with_no_spread(self):
        y1 = prog.project(vet(rate1=41.3, gp1=68.0), years=3, n=300)[0]
        self.assertEqual((y1.rate_p10, y1.rate_p50, y1.rate_p90), (41.3, 41.3, 41.3))
        self.assertEqual(y1.gp_mean, 68.0)


class QualityDependentAging(unittest.TestCase):
    def test_at_thirty_a_star_stays_useful_for_years_and_a_role_player_does_not(self):
        star = prog.project(vet(rate1=46.0, age1=30.0, bpm=6.0, cy1=9), years=6, n=1500)
        role = prog.project(vet(rate1=26.0, age1=30.0, bpm=0.0, cy1=9), years=6, n=1500)
        self.assertGreater(star[5].p_usable, 0.5)
        self.assertLess(role[5].p_usable, 0.2)
        self.assertGreater(star[5].rate_p50 / 46.0, role[5].rate_p50 / 26.0)
        self.assertGreater(star[5].p_active, role[5].p_active)


class Draftees(unittest.TestCase):
    def test_a_top_pick_grows_more_and_washes_out_less_than_a_late_one(self):
        top = prog.project(dict(rate1=12.0, gp1=60.0, age1=20.0, stage="D", cy1=1,
                                pick=2, age_rookie=20.0), years=5, n=1500)
        late = prog.project(dict(rate1=12.0, gp1=60.0, age1=20.0, stage="D", cy1=1,
                                 pick=20, age_rookie=20.0), years=5, n=1500)
        self.assertGreater(top[2].rate_p50, 15.0)
        self.assertGreater(top[2].rate_p50, late[2].rate_p50)
        self.assertGreater(top[4].p_active, late[4].p_active + 0.05)


class WhatMovesAPath(unittest.TestCase):
    def test_spread_widens_with_the_horizon(self):
        ys = prog.project(vet(age1=26.0), years=8, n=2000)
        widths = [math.log(ys[t].rate_p90 / ys[t].rate_p10) for t in (1, 4, 7)]
        self.assertLess(widths[0], widths[1])
        self.assertLess(widths[1], widths[2])

    def test_impact_beyond_the_box_score_slows_the_decline(self):
        hi = prog.project(vet(rate1=38.0, age1=29.0, bpm=7.0), years=6, n=1500)
        lo = prog.project(vet(rate1=38.0, age1=29.0, bpm=-1.0), years=6, n=1500)
        self.assertEqual(hi[0], lo[0])
        self.assertGreater(hi[5].rate_p50, lo[5].rate_p50 * 1.05)

    def test_a_box_score_outlier_at_the_ceiling_does_not_grow_past_thirty(self):
        ys = prog.project(vet(rate1=64.0, age1=32.0, bpm=13.5, cy1=12), years=4, n=4000)
        self.assertLess(ys[1].rate_p50, 64.0 * 1.02)     # holding, at most
        self.assertLess(ys[3].rate_p50, 64.0)

    def test_a_young_superstar_is_less_likely_than_not_to_be_playing_at_forty(self):
        # of 40 players at 45+ FP/G at 26-28 since 1980, 14 played 20+ games at 38 and 6 were 25+ at
        # 40; the bounds leave room for being the best of them
        ys = prog.project(vet(rate1=53.0, age1=23.0, bpm=9.0, cy1=4), years=18, n=2000)
        self.assertLess(ys[15].p_active, 0.6)      # age 38
        self.assertLess(ys[17].p_usable, 0.3)      # age 40

    def test_the_best_player_at_thirty_two_is_more_likely_than_not_done_starting_by_forty(self):
        # of 27 players at 45+ FP/G at 30-32, 4 were 25+ at 40
        ys = prog.project(vet(rate1=64.0, age1=32.0, bpm=13.5, cy1=12), years=9, n=2000)
        self.assertLess(ys[8].p_usable, 0.4)

    def test_a_board_that_ranks_him_below_his_inputs_pulls_him_down_from_year_two(self):
        base = prog.project(vet(), years=6, n=1500)
        doubted = prog.project(vet(bres=1.0), years=6, n=1500)
        self.assertEqual(base[0], doubted[0])
        self.assertLess(doubted[4].rate_p50, base[4].rate_p50 * 0.97)

    def test_an_injury_override_lowers_every_year_after_the_first(self):
        base = prog.project(vet(), years=4, n=1500)
        hurt = prog.project(vet(rate_mult=0.85), years=4, n=1500)
        self.assertEqual(base[0], hurt[0])
        for t in (1, 2, 3):
            self.assertLess(hurt[t].rate_p50, base[t].rate_p50 * 0.92)

    def test_a_deep_bench_body_plays_fewer_games_than_a_starter_with_the_same_history(self):
        bench = prog.project(vet(rate1=12.0, age1=26.0, bpm=-2.0, gp1=70.0), years=3, n=3000)
        starter = prog.project(vet(rate1=30.0, age1=26.0, bpm=1.0, gp1=70.0), years=3, n=3000)
        self.assertLess(bench[1].gp_mean / bench[1].p_active,
                        starter[1].gp_mean / starter[1].p_active - 3)

    def test_a_season_lost_to_injury_is_not_read_as_a_retirement(self):
        healthy = prog.project(vet(age1=26.0, gp1=65.0), years=3, n=6000)
        hurt = prog.project(vet(age1=26.0, gp1=0.0), years=3, n=6000)
        self.assertGreater(hurt[2].p_active, healthy[2].p_active - 0.03)

    def test_a_sophomore_grows_through_the_rookie_stage_where_a_vet_the_same_age_would_not(self):
        soph = prog.project(dict(rate1=15.0, gp1=65.0, age1=21.0, stage="S", cy1=2, pick=10,
                                 age_rookie=20.0, bpm=None, gp_last=60.0), years=3, n=2000)
        as_vet = prog.project(dict(rate1=15.0, gp1=65.0, age1=21.0, stage="V", cy1=2, pick=10,
                                   age_rookie=20.0, bpm=None, gp_last=60.0), years=3, n=2000)
        self.assertGreater(soph[1].rate_p50, as_vet[1].rate_p50)

    def test_two_runs_of_one_player_are_identical(self):
        self.assertEqual(prog.project(vet(), years=5, n=300),
                         prog.project(vet(), years=5, n=300))


class Weighting(unittest.TestCase):
    def test_years_one_to_seven_count_in_full_and_later_ones_fade_five_percent_a_year(self):
        one = prog.Year(*([None] * 9 + [100.0]))
        self.assertEqual(prog.wrv([one] * 7), 700.0)
        self.assertAlmostEqual(prog.wrv([one] * 9), 700.0 + 95.0 + 90.25)
