import unittest
from tests.harness import *

class BracketWindow(unittest.TestCase):
    def test_the_wire_flags_fewer_rounds_than_are_actually_played(self):
        flagged = {i for i, p in enumerate(sim.PERIODS)
                   if "playoff" in p["kinds"]}
        self.assertLess(len(flagged), len(sim.BRACKET))
        self.assertTrue(flagged <= set(sim.BRACKET))

    def test_it_matches_the_window_league_info_states(self):
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
    def test_every_team_game_in_the_window_is_counted_once(self):
        for w, nights in enumerate(sim.BRACKET_NIGHTS):
            with self.subTest(week=w):
                self.assertEqual(
                    sum(sim.bracket_games(t)[w] for t in sim.NBA_TEAMS),
                    sum(len(sim.NIGHTS[n][1]) for n in nights))

    def test_the_weeks_are_not_flat_across_teams(self):
        per = {t: sim.bracket_games(t) for t in sim.NBA_TEAMS}
        self.assertEqual((min(min(c) for c in per.values()),
                          max(max(c) for c in per.values())), (2, 4))
        pair = [sum(c[-2:]) for c in per.values()]
        self.assertEqual((min(pair), max(pair)), (5, 8))

    def test_the_nba_schedule_covers_the_whole_window(self):
        for i, nights in zip(sim.BRACKET, sim.BRACKET_NIGHTS):
            with self.subTest(period=sim.PERIODS[i]["ordinal"]):
                self.assertTrue(nights)
                self.assertEqual(sim.NIGHTS[nights[0]][0],
                                 sim.PERIODS[i]["start"])
                self.assertEqual(sim.NIGHTS[nights[-1]][0],
                                 sim.PERIODS[i]["end"])

class SeedBands(unittest.TestCase):
    def test_a_consolation_half_in_r1_is_named_where_it_is_read(self):
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
        first = sim.PERIODS[sim.BRACKET[0]]["ordinal"]
        played = {t for t, s in sim.SCORES.items() if first in s}
        self.assertTrue(played <= set(sim.BRACKET_TEAMS))
        self.assertEqual(played, set(sim.BANDS[-1].seeds))

    def test_every_bracket_round_ends_in_the_final(self):
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertEqual(list(band.periods),
                                 [i for i in sim.BRACKET if i >= band.periods[0]])
                self.assertEqual(band.periods[-1], sim.BRACKET[-1])
        self.assertEqual([len(b.periods) for b in sim.BANDS],
                         sorted(len(b.periods) for b in sim.BANDS))

class TheDraw(unittest.TestCase):
    def test_the_ladders_are_the_pairings_the_league_actually_played(self):
        order, held = bracket._seeded(), []
        for ladder in sim.LADDERS:
            cur = order[ladder[0] - 1]
            for r, i in enumerate(sim.BRACKET[:-1]):
                nxt, o = order[ladder[r + 1] - 1], sim.PERIODS[i]["ordinal"]
                with self.subTest(period=o, seeds=(ladder[r + 1], ladder[:r + 1])):
                    self.assertIn({cur, nxt}, [{a, h} for a, _, h, _
                                               in sim.HIST_PERIODS[i]["games"]])
                cur = max((cur, nxt), key=lambda t: sim.SCORES[t][o])
            held.append(cur)
        self.assertIn(set(held),
                      [{a, h} for a, _, h, _
                       in sim.HIST_PERIODS[sim.BRACKET[-1]]["games"]])

    def test_every_seed_climbs_in_from_the_round_its_band_enters(self):
        entry = {s: sim.BRACKET.index(b.periods[0])
                 for b in sim.BANDS for s in b.slots}
        self.assertEqual(sorted(s for l in sim.LADDERS for s in l),
                         sorted(entry))
        for ladder in sim.LADDERS:
            for k, s in enumerate(ladder):
                with self.subTest(seed=s):
                    self.assertEqual(entry[s], max(0, k - 1))

    def test_the_half_a_seed_cannot_meet_early_is_the_half_it_meets_in_the_final(self):
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
        with cheap_monte_carlo(8):
            last = len(sim.BRACKET) - 1
            for b in sim.BANDS:
                for s in b.slots:
                    with self.subTest(seed=s):
                        self.assertGreater(sim.opp_mean(last, s),
                                           sim.opp_mean(last))
                        self.assertAlmostEqual(
                            sum(sim.opp_dist(s, last).values()), 1.0)
