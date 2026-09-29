import unittest
from tests.harness import *

def flat_league(levels):
    return tuple(t._replace(regs=(lvl,) * len(sim.PAIRINGS),
                            mus=(lvl,) * len(sim.BRACKET))
                 for t, lvl in zip(bracket.team_levels(), levels))

def rounds_that_decide(seed):
    n, rounds = len(sim.BRACKET_TEAMS), len(sim.BRACKET)
    out = []
    for r in range(rounds):
        scores = [[1.0] * n for _ in range(rounds)]
        for each in range(rounds):
            scores[each][seed - 1] = 2.0
        scores[r][seed - 1] = 0.0
        if title._play(list(range(n)), scores) != seed - 1:
            out.append(r)
    return out

class HeadToHeadSchedule(unittest.TestCase):
    def test_every_team_plays_exactly_once_in_every_period(self):
        for k, per in enumerate(sim.PAIRINGS):
            with self.subTest(period=k):
                teams = [t for g in per for t in g]
                self.assertEqual(len(teams), len(set(teams)))
                self.assertEqual(len(set(teams)), len(bracket.team_levels()))

    def test_it_is_the_regular_season_and_not_the_bracket(self):
        self.assertEqual(len(sim.PAIRINGS), len(sim.REGULAR))
        self.assertEqual(sum(len(p) for p in sim.PAIRINGS),
                         len(sim.REGULAR) * sim.FULL_FIELD)

    def test_every_pair_meets_and_most_of_them_twice(self):
        met = collections.Counter(frozenset(g) for p in sim.PAIRINGS for g in p)
        n = len(bracket.team_levels())
        self.assertEqual(len(met), n * (n - 1) // 2)
        self.assertEqual(min(met.values()), 1)
        self.assertEqual(max(met.values()), 2)

    def test_meeting_the_best_team_twice_costs_wins(self):
        names = sim._load("teams-%s.json" % fetch_data.SEASON_TAG)
        teams = flat_league([1000.0] * len(bracket.team_levels()))
        at = {names[os.path.basename(t.path).split("-")[1]]: k
              for k, t in enumerate(teams)}
        stacked = "Yao Ming Dynasty"
        met = collections.Counter()
        for per in sim.PAIRINGS:
            for a, h in per:
                if stacked in (a, h):
                    met[h if a == stacked else a] += 1
        twice = at[next(n for n, c in met.items() if c == 2)]
        once = at[next(n for n, c in met.items() if c == 1)]
        boosted = list(teams)
        t = boosted[at[stacked]]
        boosted[at[stacked]] = t._replace(
            regs=tuple(x + 400 for x in t.regs), pf=t.pf + 400 * len(t.regs))
        with cheap_monte_carlo(4, seasons=2500):
            odds = sim.full_season(tuple(boosted), trials=2500)
        self.assertLess(odds[teams[twice].path].wins,
                        odds[teams[once].path].wins)

    def test_a_league_short_a_roster_file_is_refused(self):
        with cheap_monte_carlo(4, seasons=20):
            with self.assertRaises(KeyError):
                sim.full_season(bracket.team_levels()[:-1], trials=5)

class SeedingRule(unittest.TestCase):
    def test_record_comes_first(self):
        self.assertEqual(title.standings([5, 9, 7], [900.0, 100.0, 500.0]),
                         [1, 2, 0])

    def test_points_for_breaks_a_tie(self):
        self.assertEqual(title.standings([9, 9, 9], [100.0, 300.0, 200.0]),
                         [1, 2, 0])

class BracketByes(unittest.TestCase):
    def test_a_seed_plays_exactly_the_rounds_its_band_names(self):
        for band in sim.BANDS:
            want = sorted(sim.BRACKET.index(i) for i in band.periods)
            for seed in band.slots:
                with self.subTest(seed=seed):
                    self.assertEqual(rounds_that_decide(seed), want)

    def test_the_top_seed_cannot_lose_a_round_it_is_not_in(self):
        n, rounds = len(sim.BRACKET_TEAMS), len(sim.BRACKET)
        byes = rounds - len(sim.BANDS[0].periods)
        scores = [[1.0] * n for _ in range(rounds)]
        for r in range(rounds):
            scores[r][0] = -1e9 if r < byes else 1e9
        self.assertEqual(title._play(list(range(n)), scores), 0)

    def test_the_worst_seed_plays_every_round(self):
        n, rounds = len(sim.BRACKET_TEAMS), len(sim.BRACKET)
        scores = [[1.0] * n for _ in range(rounds)]
        for r in range(rounds):
            scores[r][n - 1] = 1e9
        scores[0][n - 1] = -1e9
        self.assertNotEqual(title._play(list(range(n)), scores), n - 1)

class FullSeason(unittest.TestCase):
    def test_fixing_the_seeds_reproduces_the_closed_form(self):
        seasons = 6000
        with cheap_monte_carlo(8, seasons=seasons):
            teams = bracket.team_levels()
            got = sim.bracket_odds()
            for k, t in enumerate(teams[:len(sim.BRACKET_TEAMS)]):
                with self.subTest(seed=k + 1):
                    self.assertAlmostEqual(
                        got[t.path], sim.seed_title(t.mus, k + 1, path=t.path),
                        delta=4 * math.sqrt(0.25 / seasons))

    def test_somebody_wins_the_title(self):
        with cheap_monte_carlo(4, seasons=400):
            odds = sim.full_season()
        self.assertAlmostEqual(sum(o.title for o in odds.values()), 1.0)
        for path, o in odds.items():
            with self.subTest(team=path):
                self.assertAlmostEqual(sum(o.seeds), 1.0)
                self.assertAlmostEqual(sum(o.crowns), o.title)

    def test_the_twelve_records_add_up_to_the_matchups_played(self):
        with cheap_monte_carlo(4, seasons=200):
            odds = sim.full_season()
        self.assertAlmostEqual(sum(o.wins for o in odds.values()),
                               sum(len(p) for p in sim.PAIRINGS), places=6)

    def test_a_matchup_is_decided_on_the_wires_spread_not_the_engines(self):
        edge, base, seasons = 100.0, 1000.0, 4000
        with cheap_monte_carlo(4, seasons=seasons):
            teams = flat_league([base + edge]
                                + [base] * (len(bracket.team_levels()) - 1))
            got = sim.full_season(teams, trials=seasons)[teams[0].path]
        level = statistics.mean(t.regs[0] for t in teams)
        want = len(sim.PAIRINGS) * bracket.cdf(
            edge / (math.sqrt(2) * sim.WITHIN_CV * level))
        self.assertAlmostEqual(got.wins, want, delta=0.15)

    def test_an_equal_league_seeds_at_random(self):
        with cheap_monte_carlo(4, seasons=3000):
            teams = flat_league([1000.0] * len(bracket.team_levels()))
            odds = sim.full_season(teams, trials=3000)
        for path, o in odds.items():
            with self.subTest(team=path):
                self.assertAlmostEqual(o.title, 1.0 / len(teams), delta=0.02)
                self.assertAlmostEqual(o.seeds[0], 1.0 / len(teams), delta=0.03)

    def test_one_roster_priced_twice_moves_by_exactly_nothing(self):
        with cheap_monte_carlo(4, seasons=300):
            full = sim.basis()
            after, before = sim.swap_odds(full, full)
        self.assertEqual(after, before)

    def test_a_better_roster_takes_more_titles(self):
        with cheap_monte_carlo(8, seasons=2000):
            full = sim.basis()
            after, before = sim.swap_odds(
                sim.swap(full, [full[-1]["n"]], [sim.star(70, 82, ("C",))]),
                full)
        self.assertGreater(after.wins, before.wins)
        self.assertGreater(after.title, before.title)

    def test_the_fixed_order_is_read_off_projected_pf_not_off_the_tuple(self):
        with cheap_monte_carlo(4, seasons=800):
            teams = bracket.team_levels()
            best, worst = teams[0], teams[-1]
            got = sim.bracket_odds(teams=tuple(reversed(teams)), trials=800)
        self.assertGreater(got[best.path], got[worst.path])

    def test_the_seed_is_worth_something_it_is_not_handed(self):
        with cheap_monte_carlo(8, seasons=3000):
            pinned = sim.bracket_odds()
            odds = sim.full_season()
            best, worst = bracket.team_levels()[0], bracket.team_levels()[-1]
        self.assertLess(odds[best.path].title, pinned[best.path])
        self.assertGreaterEqual(odds[worst.path].title, pinned[worst.path])
