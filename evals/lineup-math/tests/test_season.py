import unittest
from tests.harness import *

def flat_league(levels):
    """The league with every team's period and bracket levels replaced by one
    number of its own. `pf` is left alone: it seeds nothing here, since these
    teams are passed in rather than read off `team_levels`.

    Strips out the calendar and the rosters so a test can ask what the model
    does with a known gap -- which is the only way to check the SPREAD the
    matchups are decided on, since nothing prints it"""
    return tuple(t._replace(regs=(lvl,) * len(sim.PAIRINGS),
                            mus=(lvl,) * len(sim.BRACKET))
                 for t, lvl in zip(bracket.team_levels(), levels))

def rounds_that_decide(seed):
    """The bracket rounds `seed` cannot afford to lose, found by losing each
    one in turn against a field that never beats it. A round it can lose and
    still win the title is a round it was not in"""
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
    """The 19 head-to-head periods the standings are made of. Next season's
    schedule does not exist in August, so the SHAPE is taken off last season's
    and the franchises are dealt onto it afresh every trial"""

    def test_every_team_plays_exactly_once_in_every_period(self):
        """A team missing from a period plays 18 games, and one seated twice
        plays 20 -- either way its record is not the league's record, and the
        seeding sorts on it anyway"""
        for k, per in enumerate(sim.PAIRINGS):
            with self.subTest(period=k):
                teams = [t for g in per for t in g]
                self.assertEqual(len(teams), len(set(teams)))
                self.assertEqual(len(set(teams)), len(bracket.team_levels()))

    def test_it_is_the_regular_season_and_not_the_bracket(self):
        """The bracket periods are short-field by construction (`data`), so a
        skeleton read off every period would deal 6 teams into a 12-team
        schedule and forfeit the rest"""
        self.assertEqual(len(sim.PAIRINGS), len(sim.REGULAR))
        self.assertEqual(sum(len(p) for p in sim.PAIRINGS),
                         len(sim.REGULAR) * sim.FULL_FIELD)

    def test_every_pair_meets_and_most_of_them_twice(self):
        """What makes a 19-game record comparable across the league. A
        skeleton where some pairs never meet hands the teams that dodged each
        other a schedule nobody else played"""
        met = collections.Counter(frozenset(g) for p in sim.PAIRINGS for g in p)
        n = len(bracket.team_levels())
        self.assertEqual(len(met), n * (n - 1) // 2)
        self.assertEqual(min(met.values()), 1)
        self.assertEqual(max(met.values()), 2)

    def test_a_league_short_a_roster_file_is_refused(self):
        """A team with no file is not a team that loses -- it is a name the
        schedule still holds. Dropped instead of refused it forfeits 19 games
        and hands the other eleven a seed each"""
        with cheap_monte_carlo(4, seasons=20):
            with self.assertRaises(KeyError):
                sim.full_season(bracket.team_levels()[:-1], trials=5)

class SeedingRule(unittest.TestCase):
    """Seeds are record then points-for (`league-info`) -- NOT
    `recordOverall.rank`, which is the draft's rule and splits ties on
    something else"""

    def test_record_comes_first(self):
        self.assertEqual(title.standings([5, 9, 7], [900.0, 100.0, 500.0]),
                         [1, 2, 0])

    def test_points_for_breaks_a_tie(self):
        self.assertEqual(title.standings([9, 9, 9], [100.0, 300.0, 200.0]),
                         [1, 2, 0])

class BracketByes(unittest.TestCase):
    """Seeds 1-2 are double-byed and 3-4 byed once, so which rounds a seed
    plays is the whole reason `Delta P(title)` is banded. A bye that is not
    modelled is a game the top seed can lose"""

    def test_a_seed_plays_exactly_the_rounds_its_band_names(self):
        """`BANDS` says how many rounds each seed range has to win and the
        draw says which. This walks the draw itself and asks which rounds
        actually decide that seed's season"""
        for band in sim.BANDS:
            want = sorted(sim.BRACKET.index(i) for i in band.periods)
            for seed in band.slots:
                with self.subTest(seed=seed):
                    self.assertEqual(rounds_that_decide(seed), want)

    def test_the_top_seed_cannot_lose_a_round_it_is_not_in(self):
        """The property a bye IS, stated as the failure it prevents: a
        1-seed's score in bracket R1 is a number nobody plays against"""
        n, rounds = len(sim.BRACKET_TEAMS), len(sim.BRACKET)
        byes = rounds - len(sim.BANDS[0].periods)
        scores = [[1.0] * n for _ in range(rounds)]
        for r in range(rounds):
            scores[r][0] = -1e9 if r < byes else 1e9
        self.assertEqual(title._play(list(range(n)), scores), 0)

    def test_the_worst_seed_plays_every_round(self):
        """The other end of the same fact -- and the reason a bracket game is
        worth four times as much to seed 8 as to seed 1"""
        n, rounds = len(sim.BRACKET_TEAMS), len(sim.BRACKET)
        scores = [[1.0] * n for _ in range(rounds)]
        for r in range(rounds):
            scores[r][n - 1] = 1e9
        scores[0][n - 1] = -1e9
        self.assertNotEqual(title._play(list(range(n)), scores), n - 1)

class FullSeason(unittest.TestCase):
    """Regular season -> standings -> seeds -> bracket -> title, as one run.
    `bracket` prices a round GIVEN a seed; this earns the seed first, so the
    two have to agree wherever the seed is not in question"""

    def test_fixing_the_seeds_reproduces_the_closed_form(self):
        """THE check that these are two views of one model. Pinned at the
        projected order this is `seed_title` as a Monte Carlo -- same sigma,
        same draw, same opponents -- so a gap is one of them having drifted"""
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
        """Twelve unconditional probabilities of the same one prize. The
        banded figures cannot be summed this way and this one has to be"""
        with cheap_monte_carlo(4, seasons=400):
            odds = sim.full_season()
        self.assertAlmostEqual(sum(o.title for o in odds.values()), 1.0)
        for path, o in odds.items():
            with self.subTest(team=path):
                self.assertAlmostEqual(sum(o.seeds), 1.0)
                self.assertAlmostEqual(sum(o.crowns), o.title)

    def test_the_twelve_records_add_up_to_the_matchups_played(self):
        """Six games a period, one winner each, so the league's wins sum to the
        schedule itself. A tie booked to both sides, or a team seated twice in
        a period, inflates the records the seeding then sorts on -- and every
        row still prints as a plausible season with a plausible spread"""
        with cheap_monte_carlo(4, seasons=200):
            odds = sim.full_season()
        self.assertAlmostEqual(sum(o.wins for o in odds.values()),
                               sum(len(p) for p in sim.PAIRINGS), places=6)

    def test_a_matchup_is_decided_on_the_wires_spread_not_the_engines(self):
        """The single number this model turns on. Two named teams' margin is
        sqrt(2) x `WITHIN_CV` of the period's level, which is `sigma`'s own
        decomposition; the engine's own draws are 0.040 against that 0.1005,
        because availability is all that moves in it. Scored off those instead
        the favourite wins nearly every week and the standings never shuffle"""
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
        """With no edge anywhere, every team has to be as likely to take any
        seed as any other -- the check that the schedule deal and the shocks
        are not quietly favouring a slot in the skeleton"""
        with cheap_monte_carlo(4, seasons=3000):
            teams = flat_league([1000.0] * len(bracket.team_levels()))
            odds = sim.full_season(teams, trials=3000)
        for path, o in odds.items():
            with self.subTest(team=path):
                self.assertAlmostEqual(o.title, 1.0 / len(teams), delta=0.02)
                self.assertAlmostEqual(o.seeds[0], 1.0 / len(teams), delta=0.03)

    def test_one_roster_priced_twice_moves_by_exactly_nothing(self):
        """Common random numbers, which is what makes a `Delta P(title)` off
        two runs readable at all: the schedule, the weekly luck and the
        bracket luck are the same draws on both sides, so the same roster
        against itself is not merely close to zero"""
        with cheap_monte_carlo(4, seasons=300):
            full = sim.basis()
            after, before = sim.swap_odds(full, full)
        self.assertEqual(after, before)

    def test_a_better_roster_takes_more_titles(self):
        """End to end, through both channels at once -- it wins more matchups,
        so it seeds higher, and it scores more in the bracket once there"""
        with cheap_monte_carlo(8, seasons=2000):
            full = sim.basis()
            after, before = sim.swap_odds(
                sim.swap(full, [full[-1]["n"]], [sim.star(70, 82, ("C",))]),
                full)
        self.assertGreater(after.wins, before.wins)
        self.assertGreater(after.title, before.title)

    def test_the_fixed_order_is_read_off_projected_pf_not_off_the_tuple(self):
        """`bracket_odds` hands every team the seed its projected PF says it
        gets. Read off the tuple's own order instead, a caller who assembles
        the same twelve in another order -- `swap_odds` builds one, and it is
        the tuple this takes -- hands the 1 seed to whoever happens to sit
        first, and every row still prints as a bracket"""
        with cheap_monte_carlo(4, seasons=800):
            teams = bracket.team_levels()
            best, worst = teams[0], teams[-1]
            got = sim.bracket_odds(teams=tuple(reversed(teams)), trials=800)
        self.assertGreater(got[best.path], got[worst.path])

    def test_the_seed_is_worth_something_it_is_not_handed(self):
        """The whole point of simulating the standings. A team pinned at its
        projected seed never has to earn it, so the top projection can only be
        worse off once it does -- and a team the projection leaves outside the
        field can only be better off"""
        with cheap_monte_carlo(8, seasons=3000):
            pinned = sim.bracket_odds()
            odds = sim.full_season()
            best, worst = bracket.team_levels()[0], bracket.team_levels()[-1]
        self.assertLess(odds[best.path].title, pinned[best.path])
        self.assertGreaterEqual(odds[worst.path].title, pinned[worst.path])
