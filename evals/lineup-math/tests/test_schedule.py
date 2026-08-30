import unittest
from tests.harness import *

class Schedule(unittest.TestCase):
    def test_the_nba_calendar_is_this_season(self):
        self.assertGreaterEqual(sim.NIGHTS[0][0], "2026-10-01")
        self.assertLessEqual(sim.NIGHTS[-1][0], "2027-04-30")

    def test_every_team_plays_the_same_number_of_games(self):
        played = collections.Counter()
        for _, tms in sim.NIGHTS:
            for t in tms:
                played[t] += 1
        self.assertEqual(sorted(collections.Counter(played.values()).items()),
                         [(80, 30)])

class FantasyCalendar(unittest.TestCase):
    def test_scoring_nights_fall_on_this_seasons_nba_calendar(self):
        self.assertTrue(sim.SCORING_NIGHTS)
        self.assertGreaterEqual(sim.NIGHTS[sim.SCORING_NIGHTS[0]][0],
                                "2026-10-01")

    def test_games_per_period_matches_the_real_spread(self):
        games = collections.Counter()
        for (_, tms), w in zip(sim.NIGHTS, sim.WEEK_OF):
            if w is not None:
                games[w] += len(tms) // 2
        self.assertEqual((min(games.values()), max(games.values())), (14, 55))

class NightToPeriodMapping(unittest.TestCase):
    def test_the_scoring_nights_are_exactly_the_scored_periods_nights_in_order(self):
        self.assertEqual([n for i in sim.SCORED for n in sim.period_nights(i)],
                         list(sim.SCORING_NIGHTS))

    def test_every_night_buckets_into_the_period_it_falls_inside(self):
        for w, i in enumerate(sim.SCORED):
            for n in sim.period_nights(i):
                with self.subTest(period=sim.PERIODS[i]["ordinal"],
                                  night=sim.NIGHTS[n][0]):
                    self.assertEqual(sim.WEEK_OF[n], w)

    def test_no_night_falls_inside_two_periods_at_once(self):
        seen = collections.Counter(n for i in range(len(sim.PERIODS))
                                   for n in sim.period_nights(i))
        self.assertTrue(seen)
        self.assertEqual(max(seen.values()), 1,
                         sorted(n for n, c in seen.items() if c > 1))

    def test_bracket_round_one_is_the_only_night_the_two_calendars_share(self):
        self.assertEqual(set(sim.SCORED_CAL.nights) & set(sim.BRACKET_CAL.nights),
                         set(sim.BRACKET_NIGHTS[0]))

class DeltaWBasis(unittest.TestCase):
    def test_delta_w_excludes_the_first_bracket_week(self):
        r1 = sim.BRACKET[0]
        r1_nights = set(sim.period_nights(r1))
        self.assertIn(r1, sim.SCORED)
        self.assertTrue(r1_nights <= set(sim.SCORED_CAL.nights))
        self.assertFalse(r1_nights & set(sim.DELTA_W_CAL.nights))
        self.assertEqual(sim.DELTA_W_MATCHUPS, len(sim.SCORED) - 1)

    def test_a_delta_w_run_spends_its_pf_over_the_periods_it_measured(self):
        full = sim.basis()
        worst = min(sim.our_roster(), key=season_value)
        base = sim.run(full, trials=20, cal=sim.DELTA_W_CAL)
        better = sim.run(sim.swap(full, [worst["n"]],
                                  [sim.star(55, 75, tuple(worst["elig"]),
                                            n="UP")]),
                         trials=20, cal=sim.DELTA_W_CAL)
        h = 1e-4
        per_pf = (sim.margin_pwin(h) - sim.margin_pwin(-h)) / (2 * h)
        edge = (better["pf"] - base["pf"]) / sim.DELTA_W_MATCHUPS
        self.assertAlmostEqual(sim.wins(better, base),
                               sim.DELTA_W_MATCHUPS * per_pf * edge, places=6)

    def test_two_runs_on_different_calendars_are_refused_rather_than_differenced(
            self):
        full = sim.basis()
        with self.assertRaises(ValueError):
            sim.wins(sim.run(full, trials=2, cal=sim.DELTA_W_CAL),
                     sim.run(full, trials=2))

class GameCountsAgree(unittest.TestCase):
    def test_a_bracket_round_is_the_same_window_counted_per_night_and_per_team(self):
        for w, i in enumerate(sim.BRACKET):
            with self.subTest(period=sim.PERIODS[i]["ordinal"]):
                self.assertEqual(2 * sim.period_games(i),
                                 sum(sim.bracket_games(t)[w]
                                     for t in sim.NBA_TEAMS))



def light_nights_per_team():
    return {t: len(sim.team_light_nights(t)) for t in sim.NBA_TEAMS}


class LightNights(unittest.TestCase):
    def test_light_nights_outside_the_scored_periods_are_dropped(self):
        whole = [i for i, (_, tms) in enumerate(sim.NIGHTS)
                 if len(tms) // 2 <= sim.LIGHT_GAMES]
        self.assertLess(len(sim.light_nights()), len(whole))
        self.assertTrue(set(sim.light_nights()) <= set(sim.SCORING_NIGHTS))

    def test_every_team_spelling_in_the_feed_finds_a_real_schedule(self):
        feed = set()
        for path in committed_rosters():
            feed |= {r["tm"] for r in json.loads(read_text(path))}
        feed -= {sim.UNSIGNED}
        self.assertEqual(len(feed), 30, sorted(feed))
        self.assertEqual({sim.team_light_nights(t) for t in feed},
                         {sim.team_light_nights(t) for t in sim.NBA_TEAMS})

    def test_a_team_is_counted_on_the_nights_it_actually_plays(self):
        for tm in ("LAC", "CLE", "BKN"):
            with self.subTest(tm=tm):
                self.assertEqual(
                    sim.team_light_nights(tm),
                    frozenset(i for i in sim.light_nights()
                              if tm in sim.NIGHTS[i][1]))

class Coverage(unittest.TestCase):
    def test_seven_bodies_on_one_team_only_get_you_that_teams_nights(self):
        per = light_nights_per_team()
        tm = max(per, key=per.get)
        self.assertEqual(sim.coverage([tm] * 7), per[tm])

    def test_spreading_the_same_seven_out_covers_way_more_nights(self):
        spread = sim.coverage(["OKC", "LAC", "UTAH", "SA", "NY", "MIN", "BOS"])
        self.assertGreater(spread, 2 * sim.coverage(["LAC"] * 7))
        self.assertLessEqual(spread, len(sim.light_nights()))

class CoveragePicks(unittest.TestCase):
    def test_the_first_k_picks_are_always_the_best_k(self):
        picks = sim.coverage_picks(7)
        for k in range(1, 8):
            with self.subTest(k=k):
                self.assertEqual(sim.coverage_picks(k), picks[:k])

    def test_coverage_saturates_after_about_three_picks(self):
        cov = [sim.coverage(sim.coverage_picks(k)) for k in range(1, 8)]
        self.assertEqual(cov, sorted(cov))
        self.assertEqual(cov[-1], cov[-2], "the 7th pick still bought a night")
        self.assertGreater(cov[2], 0.8 * cov[-1])

    def test_the_worst_seven_all_pile_onto_the_emptiest_schedule(self):
        worst = sim.coverage_picks(7, best=False)
        self.assertEqual(len(set(worst)), 1)
        self.assertEqual(sim.coverage(worst),
                         min(light_nights_per_team().values()))

    def test_only_the_teams_actually_on_offer_can_be_picked(self):
        offer = ("BKN", "CHI", "POR", "ATL", "DET")
        self.assertTrue(set(sim.coverage_picks(7, teams=offer)) <= set(offer))
