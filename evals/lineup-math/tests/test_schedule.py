import unittest
from tests.harness import *

class Schedule(unittest.TestCase):
    """Every conclusion is a count of slot-nights, so a phantom game is a
    phantom night of value"""

    def test_every_team_plays_82_games(self):
        played = collections.Counter()
        for _, tms in sim.NIGHTS:
            for t in tms:
                played[t] += 1
        # the NBA Cup final is an 83rd game for its two participants
        self.assertEqual(sorted(collections.Counter(played.values()).items()),
                         [(82, 28), (83, 2)])

class FantasyCalendar(unittest.TestCase):
    """Weekly scores are the unit a matchup is won in, so how nights bucket
    into periods is not cosmetic"""

    def test_games_per_period_matches_the_real_spread(self):
        """Real periods carry 28-56 NBA games. An even split of nights across
        periods implies ~49-56 and erases most of the weekly variance the sim
        exists to explain"""
        games = collections.Counter()
        for (_, tms), w in zip(sim.NIGHTS, sim.WEEK_OF):
            if w is not None:
                games[w] += len(tms) // 2
        self.assertEqual((min(games.values()), max(games.values())), (28, 56))

class NightToPeriodMapping(unittest.TestCase):
    """A night reaches a period two independent ways: the points column buckets
    it through the scoring calendar's `WEEK_OF`, and the games count comes off
    `period_nights`, a date-range test against the period. Let those drift and
    the two columns of the same row describe different weeks"""

    def test_the_scoring_nights_are_exactly_the_scored_periods_nights_in_order(self):
        """Same nights AND same order, since position `w` in the points column
        is the `w`th scored period. A scoring calendar that carried an extra
        night, or ran them in another order, would still total the same season
        """
        self.assertEqual([n for i in sim.SCORED for n in sim.period_nights(i)],
                         list(sim.SCORING_NIGHTS))

    def test_every_night_buckets_into_the_period_it_falls_inside(self):
        """The off-by-one guard. A shift of one leaves the season total alone
        and moves nearly every entry of the column"""
        for w, i in enumerate(sim.SCORED):
            for n in sim.period_nights(i):
                with self.subTest(period=sim.PERIODS[i]["ordinal"],
                                  night=sim.NIGHTS[n][0]):
                    self.assertEqual(sim.WEEK_OF[n], w)

    def test_no_night_falls_inside_two_periods_at_once(self):
        """Periods are read off start/end dates, so an inclusive end meeting an
        inclusive start double-counts that night's games in both"""
        seen = collections.Counter(n for i in range(len(sim.PERIODS))
                                   for n in sim.period_nights(i))
        self.assertTrue(seen)
        self.assertEqual(max(seen.values()), 1,
                         sorted(n for n, c in seen.items() if c > 1))

    def test_bracket_round_one_is_the_only_night_the_two_calendars_share(self):
        """Period 20 is both the last scored period and R1, so the standings
        basis and the bracket basis overlap there and NOWHERE else. An overlap
        that grew would score playoff-only nights into the standings; one that
        vanished would leave R1 out of the basis its own seeding is cut from"""
        self.assertEqual(set(sim.SCORED_CAL.nights) & set(sim.BRACKET_CAL.nights),
                         set(sim.BRACKET_NIGHTS[0]))

class DeltaWBasis(unittest.TestCase):
    """`Delta w` is regular-season wins only. W20 is bracket R1 on the wire and
    in the standings PF column, but it is not a regular-season matchup."""

    def test_delta_w_excludes_the_first_bracket_week(self):
        r1 = sim.BRACKET[0]
        r1_nights = set(sim.period_nights(r1))
        self.assertIn(r1, sim.SCORED)
        self.assertTrue(r1_nights <= set(sim.SCORED_CAL.nights))
        self.assertFalse(r1_nights & set(sim.DELTA_W_CAL.nights))
        self.assertEqual(sim.DELTA_W_MATCHUPS, len(sim.SCORED) - 1)

    def test_a_delta_w_run_spends_its_pf_over_the_periods_it_measured(self):
        """A `DELTA_W_CAL` run's PF total is 19 periods already. Divided by a
        SEASON PF-per-win and then cut to 19 matchups on top, the same gain
        buys 19/20 of the wins it bought -- every published `Delta w` ~5% low,
        with nothing on the page to show it"""
        full = sim.basis()
        worst = min(sim.our_roster(), key=season_value)
        base = sim.run(full, trials=20, cal=sim.DELTA_W_CAL)
        better = sim.run(sim.swap(full, [worst["n"]],
                                  [sim.star(55, 75, tuple(worst["elig"]),
                                            n="UP")]),
                         trials=20, cal=sim.DELTA_W_CAL)
        # Wins per matchup per PF of weekly edge, off the real margin
        # distribution itself -- the slope `wins()` linearises at
        h = 1e-4
        per_pf = (sim.margin_pwin(h) - sim.margin_pwin(-h)) / (2 * h)
        edge = (better["pf"] - base["pf"]) / sim.DELTA_W_MATCHUPS
        self.assertAlmostEqual(sim.wins(better, base),
                               sim.DELTA_W_MATCHUPS * per_pf * edge, places=6)

    def test_two_runs_on_different_calendars_are_refused_rather_than_differenced(
            self):
        """The W20 gap between the two calendars is ~5% of a season's PF, which
        is several wins -- larger than any trade this package prices. Left to
        subtract, the answer is the calendar, and it reads as the deal"""
        full = sim.basis()
        with self.assertRaises(ValueError):
            sim.wins(sim.run(full, trials=2, cal=sim.DELTA_W_CAL),
                     sim.run(full, trials=2))

class GameCountsAgree(unittest.TestCase):
    """A bracket period's size is printed as the games on its nights and drives
    every per-player `W` column as that team's games in the round. The two are
    counted over separately built night lists, and a window that slipped a
    night on one side prices bodies off a schedule the printed table never
    showed"""

    def test_a_bracket_round_is_the_same_window_counted_per_night_and_per_team(self):
        for w, i in enumerate(sim.BRACKET):
            with self.subTest(period=sim.PERIODS[i]["ordinal"]):
                self.assertEqual(2 * sim.period_games(i),
                                 sum(sim.bracket_games(t)[w]
                                     for t in sim.NBA_TEAMS))



def light_nights_per_team():
    """{team: the light nights it plays}, the table `schedules` prints and the
    quantity every coverage bound is read off. Derived rather than a literal,
    since the deepest and emptiest schedules move with the calendar every
    season"""
    return {t: len(sim.team_light_nights(t)) for t in sim.NBA_TEAMS}


class LightNights(unittest.TestCase):
    """The nights the 9-slot cap binds on, and the only nights a schedule
    choice can pay on. The fantasy season ENDS before the NBA's, so a team
    whose light nights sit in April has none that count"""

    def test_light_nights_outside_the_scored_periods_are_dropped(self):
        whole = [i for i, (_, tms) in enumerate(sim.NIGHTS)
                 if len(tms) // 2 <= sim.LIGHT_GAMES]
        self.assertLess(len(sim.light_nights()), len(whole))
        self.assertTrue(set(sim.light_nights()) <= set(sim.SCORING_NIGHTS))

    def test_every_team_spelling_in_the_feed_finds_a_real_schedule(self):
        """The roster feed and the NBA schedule spell teams differently,
        SAS/NYK/UTA against SA/NY/UTAH, so all 30 resolve only through
        `FF2ESPN` and a rename on either side breaks the join. Driven off the
        committed roster files rather than a hand list, because the vocabulary
        is the feed's to change"""
        feed = set()
        for path in committed_rosters():
            feed |= {r["tm"] for r in json.loads(read_text(path))}
        feed -= {sim.UNSIGNED}          # no schedule to resolve
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
    """`Eval Definitions §Where our format pulls off consensus` 5. What pays is
    the count of DISTINCT light nights the roster reaches, never a body's own
    night count, and the two diverge by 7x on a stack"""

    def test_seven_bodies_on_one_team_only_get_you_that_teams_nights(self):
        deepest = max(light_nights_per_team().values())
        self.assertEqual(deepest, 12)
        self.assertEqual(sim.coverage(["LAC"] * 7), 12)

    def test_spreading_the_same_seven_out_covers_way_more_nights(self):
        spread = sim.coverage(["OKC", "LAC", "UTAH", "SA", "NY", "MIN", "BOS"])
        self.assertGreater(spread, 2 * sim.coverage(["LAC"] * 7))
        self.assertLessEqual(spread, len(sim.light_nights()))

class CoveragePicks(unittest.TestCase):
    """The selection rule every steering figure is cut on, stated once so the
    ladder and the headline cannot be two different rules. A greedy ladder ENDS
    at its own best-7 by construction, since rung k is the best-k"""

    def test_the_first_k_picks_are_always_the_best_k(self):
        picks = sim.coverage_picks(7)
        for k in range(1, 8):
            with self.subTest(k=k):
                self.assertEqual(sim.coverage_picks(k), picks[:k])

    def test_coverage_saturates_after_about_three_picks(self):
        """The section's whole point. Three picks buy most of it and the last
        buy nothing, and if the rule did not saturate the ladder would be a
        straight line and "steer the first few" would be wrong advice"""
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
        """An auction shows you a slice of the league, not all 30, so the
        realistic figure is the best 7 of what is on the block and a rule that
        quietly reaches outside it prices a draft nobody ran"""
        offer = ("BKN", "CHI", "POR", "ATL", "DET")
        self.assertTrue(set(sim.coverage_picks(7, teams=offer)) <= set(offer))
