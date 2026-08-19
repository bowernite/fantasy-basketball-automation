import unittest
from tests.harness import *

class BracketWindow(unittest.TestCase):
    """Which periods the bracket is played over. Fleaflicker cannot label R1,
    so it arrives marked `regular` and a window taken off `kinds` is three
    rounds starting a week late. What separates a bracket period from a
    regular one on the wire is that not every team plays"""

    def test_the_wire_flags_fewer_rounds_than_are_actually_played(self):
        """The flags are a floor on the window, never the window. Some periods
        do arrive flagged, so the field reads as usable -- and taking the count
        from it drops R1 and prices a 3-round bracket starting a week late"""
        flagged = {i for i, p in enumerate(sim.PERIODS)
                   if "playoff" in p["kinds"]}
        self.assertTrue(flagged)
        self.assertLess(len(flagged), len(sim.BRACKET))

    def test_it_matches_the_window_league_info_states(self):
        """`league-info` is the verified owner of the bracket's shape and every
        skill reasons from it. A derivation that drifts from the page leaves
        both green and the two disagreeing about which weeks bind"""
        text = one_line(read_text(skills_path("league-info", "SKILL.md")))
        m = re.search(r"Bracket: (\d+) of (\d+) teams, (\d+) rounds, "
                      r"periods (\d+)\W(\d+)\*\*", text)
        self.assertIsNotNone(m, "the skill stopped stating the bracket")
        _, teams, rounds, first, last = (int(g) for g in m.groups())
        self.assertEqual(rounds, len(sim.BRACKET))
        self.assertEqual([first, last],
                         [sim.PERIODS[sim.BRACKET[0]]["ordinal"],
                          sim.PERIODS[sim.BRACKET[-1]]["ordinal"]])
        self.assertEqual(teams, 2 * sim.FULL_FIELD)

class BracketGames(unittest.TestCase):
    """`W20`-`W23` are a rate times a GAME COUNT, so the count is the whole
    column. Four a week for everybody is the assumption these exist to refuse"""

    def test_every_team_game_in_the_window_is_counted_once(self):
        for w, nights in enumerate(sim.BRACKET_NIGHTS):
            with self.subTest(week=w):
                self.assertEqual(
                    sum(sim.bracket_games(t)[w] for t in sim.NBA_TEAMS),
                    sum(len(sim.NIGHTS[n][1]) for n in nights))

    def test_the_weeks_are_not_flat_across_teams(self):
        """The spread is 2-5 in a week, and the last two periods -- the pair
        every seed band plays -- run 6 to 8 games across the 30 teams. A body
        priced at the mean is priced a third of a week wrong at either end"""
        per = {t: sim.bracket_games(t) for t in sim.NBA_TEAMS}
        self.assertEqual((min(min(c) for c in per.values()),
                          max(max(c) for c in per.values())), (2, 5))
        pair = [sum(c[-2:]) for c in per.values()]
        self.assertEqual((min(pair), max(pair)), (6, 8))

    def test_the_nba_schedule_covers_the_whole_window(self):
        """The bracket sits in March and the fantasy season ends before the
        NBA's, so a schedule file cut short leaves a bracket week with no
        nights at all and every W column in it reads 0"""
        for i, nights in zip(sim.BRACKET, sim.BRACKET_NIGHTS):
            with self.subTest(period=sim.PERIODS[i]["ordinal"]):
                self.assertTrue(nights)
                self.assertEqual(sim.NIGHTS[nights[0]][0],
                                 sim.PERIODS[i]["start"])
                self.assertEqual(sim.NIGHTS[nights[-1]][0],
                                 sim.PERIODS[i]["end"])

class SeedBands(unittest.TestCase):
    """Which rounds a seed has to win is the whole of why `Delta P(title)` is
    reported three times. Seeds 1-2 are double-byed into two games; 5-8 play
    four, so a body's bracket weeks are worth twice as many rounds to them"""

    def test_a_consolation_half_in_r1_is_named_where_it_is_read(self):
        """R1's field is read off the period's game count, and two seeds enter
        every round after it, so a period 20 that ever carried a consolation
        half beside the bracket reads as a wider entering band. `_bands`' own
        size assert passes on it and the failure surfaces rounds later as the
        snake draw disagreeing with the bands -- a message about the draw for a
        fact about the wire"""
        was = bracket.PERIODS
        first = dict(was[sim.BRACKET[0]])
        first["games"] = first["games"] * 2
        bracket.PERIODS = was[:sim.BRACKET[0]] + [first]
        try:
            with self.assertRaises(AssertionError) as raised:
                bracket._bands()
        finally:
            bracket.PERIODS = was
        self.assertIn("consolation", str(raised.exception))

    def test_a_band_enters_the_bracket_in_the_period_it_is_seeded_into(self):
        """Checked against the wire: a byed team has no score at all in the
        rounds before its entry, and every team in the band has one in the
        round it enters"""
        for band in sim.BANDS:
            skipped = [sim.PERIODS[i]["ordinal"] for i in sim.BRACKET
                       if i < band.periods[0]]
            entered = sim.PERIODS[band.periods[0]]["ordinal"]
            for t in band.seeds:
                with self.subTest(band=band.label, team=t):
                    self.assertIn(entered, sim.SCORES[t])
                    for o in skipped:
                        self.assertNotIn(o, sim.SCORES[t])

    def test_the_bands_partition_the_field_league_info_states(self):
        text = one_line(read_text(skills_path("league-info", "SKILL.md")))
        field = int(re.search(r"Bracket: (\d+) of \d+ teams", text).group(1))
        seeds = [t for band in sim.BANDS for t in band.seeds]
        self.assertEqual(len(seeds), field)
        self.assertEqual(sorted(seeds), sorted(sim.BRACKET_TEAMS))
        self.assertEqual(len(set(seeds)), field)

    def test_no_team_outside_the_bracket_plays_the_first_round(self):
        """Periods 21-23 run a consolation bracket alongside the playoff one,
        so appearing in one proves nothing. R1 is the one period only bracket
        teams are in, and the four missing from it are the four that missed"""
        first = sim.PERIODS[sim.BRACKET[0]]["ordinal"]
        played = {t for t, s in sim.SCORES.items() if first in s}
        self.assertTrue(played <= set(sim.BRACKET_TEAMS))
        self.assertEqual(played, set(sim.BANDS[-1].seeds))

    def test_every_bracket_round_ends_in_the_final(self):
        """A band's periods are the tail of the window from its entry round.
        `P(title)` is a product over them, each factor conditional on winning
        the one before, so a band that stops short is one that cannot win"""
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertEqual(list(band.periods),
                                 [i for i in sim.BRACKET if i >= band.periods[0]])
                self.assertEqual(band.periods[-1], sim.BRACKET[-1])
        self.assertEqual([len(b.periods) for b in sim.BANDS],
                         sorted(len(b.periods) for b in sim.BANDS))

class TheDraw(unittest.TestCase):
    """Who a seed can meet in a round is structure, not an average. The draw
    splits into two halves and each is climbed worst seed first, so a 1-seed's
    penultimate opponent comes only from its own half and can never be the 2 or
    the 3. Every opponent level in the model is a distribution over that"""

    def test_the_ladders_are_the_pairings_the_league_actually_played(self):
        """Every playoff game of last season's bracket, walked in seed terms:
        each half's climb, the winner carried forward on the wire's own scores,
        and the two survivors meeting in the final. A shape taken from anywhere
        but this is an assumption about who a seed can draw"""
        order, held = bracket._seeded(), []
        for ladder in sim.LADDERS:
            cur = order[ladder[0] - 1]
            for r, i in enumerate(sim.BRACKET[:-1]):
                nxt, o = order[ladder[r + 1] - 1], sim.PERIODS[i]["ordinal"]
                with self.subTest(period=o, seeds=(ladder[r + 1], ladder[:r + 1])):
                    self.assertIn({cur, nxt}, [{a, h} for a, _, h, _
                                               in sim.PERIODS[i]["games"]])
                cur = max((cur, nxt), key=lambda t: sim.SCORES[t][o])
            held.append(cur)
        self.assertIn(set(held),
                      [{a, h} for a, _, h, _
                       in sim.PERIODS[sim.BRACKET[-1]]["games"]])

    def test_every_seed_climbs_in_from_the_round_its_band_enters(self):
        """The ladders and the bands are two readings of one bracket -- the
        seeds a band holds are the seeds that enter where the band does, and a
        ladder that disagrees prices a bye nobody has"""
        entry = {s: sim.BRACKET.index(b.periods[0])
                 for b in sim.BANDS for s in b.slots}
        self.assertEqual(sorted(s for l in sim.LADDERS for s in l),
                         sorted(entry))
        for ladder in sim.LADDERS:
            for k, s in enumerate(ladder):
                with self.subTest(seed=s):
                    self.assertEqual(entry[s], max(0, k - 1))

    def test_the_half_a_seed_cannot_meet_early_is_the_half_it_meets_in_the_final(self):
        """Half the draw is unreachable until the last round and the other half
        is unreachable in it. Priced at the field's mean, every round is played
        against a blend of both -- which is a team no bracket can produce"""
        with cheap_monte_carlo(8):
            last = len(sim.BRACKET) - 1
            for b in sim.BANDS:
                for s in b.slots:
                    early = set().union(*[
                        set(sim.opp_dist(s, w))
                        for w in range(sim.BRACKET.index(b.periods[0]), last)])
                    late = set(sim.opp_dist(s, last))
                    with self.subTest(seed=s):
                        self.assertFalse(early & late)
                        self.assertEqual(len(early | late),
                                         len(sim.BRACKET_TEAMS) - 1)

    def test_the_final_is_played_against_a_survivor_not_against_the_field(self):
        """Whoever you meet in the last round has already won its way through
        its own half, which selects it above the level the field's mean quotes
        -- a final priced at that mean is priced against a team the bracket
        cannot produce"""
        with cheap_monte_carlo(8):
            last = len(sim.BRACKET) - 1
            for b in sim.BANDS:
                for s in b.slots:
                    with self.subTest(seed=s):
                        self.assertGreater(sim.opp_mean(last, s),
                                           sim.opp_mean(last))
                        self.assertAlmostEqual(
                            sum(sim.opp_dist(s, last).values()), 1.0)
