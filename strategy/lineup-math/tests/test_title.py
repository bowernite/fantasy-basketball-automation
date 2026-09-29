import unittest
from tests.harness import *

class TitleProbability(unittest.TestCase):
    def test_exactly_one_of_the_eight_seeds_wins_the_title(self):
        with cheap_monte_carlo(8):
            total = sum(sim.seed_title(t.mus, k + 1, path=t.path)
                        for k, t in enumerate(sim.field()))
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_a_starter_is_worth_more_than_the_body_that_replaces_him(self):
        full = sim.basis()
        with cheap_monte_carlo(20):
            got, = bracket.player_title(full, ["Jalen Suggs"], blocks=2).values()
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                mean, sd, blocks = got[band.label]
                self.assertGreater(mean, 0.0)
                self.assertLess(mean, 1.0)
                self.assertEqual(len(blocks), 2)
                self.assertGreater(sd, 0.0)

    def test_he_is_priced_against_a_replacement_of_his_own_slot_group(self):
        full = sim.basis()
        with cheap_monte_carlo(20):
            R = sim.group_replacement(full)
            base = sim.bracket_weeks(full)
            own = sim.bracket_weeks(sim.swap(
                full, ["Jakob Poeltl"], [sim.group_body("center", R["center"])]))
            forward = sim.bracket_weeks(sim.swap(
                full, ["Jakob Poeltl"], [sim.group_body("forward", R["forward"])]))
            got, = bracket.player_title(full, ["Jakob Poeltl"], blocks=1,
                                        R=R).values()
            want = {b.label: sim.title_prob(base, b) - sim.title_prob(own, b)
                    for b in sim.BANDS}
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertAlmostEqual(got[band.label][0], want[band.label],
                                       places=9)
        self.assertNotEqual(own, forward, "this roster cannot tell the two "
                            "counterfactuals apart -- pick another player")

    def test_incoming_title_takes_the_same_one(self):
        body = sim.star(40.0, 68, ("C",), n="INCOMING")
        with cheap_monte_carlo(20):
            got, = bracket.incoming_title(sim.basis(), [body], blocks=2).values()
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                mean, sd, blocks = got[band.label]
                self.assertGreater(mean, 0.0)
                self.assertEqual(len(blocks), 2)
                self.assertGreater(sd, 0.0)

    def test_a_roster_with_nothing_padded_refuses_incoming_title(self):
        full = [p if p["n"] not in roster_mod.PAD_NAMES
                else dict(p, n="Real %d" % i)
                for i, p in enumerate(sim.basis())]
        with self.assertRaises(ValueError) as ctx:
            bracket.incoming_title(full, [sim.star(40.0, 68, ("C",), n="IN")],
                                   blocks=1, trials=2, R=flat_R())
        self.assertIn("padded", str(ctx.exception))

    def test_a_side_of_a_deal_is_priced_in_one_joint_run(self):
        with cheap_monte_carlo(8):
            full, R = sim.basis(), flat_R()
            name = sim.our_roster()[0]["n"]
            body, = [p for p in full if p["n"] == name]
            without = sim.swap(full, [name],
                               [sim.group_body(sim.slot_group(body["elig"]),
                                               R[sim.slot_group(body["elig"])])])
            row, = bracket.player_title(full, [name], blocks=2, R=R).values()
            joint = bracket.roster_title(full, without, blocks=2)
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertEqual(joint[band.label], row[band.label])

    def test_the_import_path_prices_a_counterparty_as_the_cli_does(self):
        theirs = "roster-161018-2025-26.json"
        with cheap_monte_carlo(8):
            full = sim.basis(theirs)
            name = sim.our_roster(theirs)[0]["n"]
            got, = bracket.player_title(full, [name], blocks=1, R=flat_R(),
                                        path=theirs).values()
            was = roster_mod.ROSTER
            try:
                roster_mod.ROSTER = theirs
                cli_side, = bracket.player_title(full, [name], blocks=1,
                                                 R=flat_R()).values()
            finally:
                roster_mod.ROSTER = was
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertEqual(got[band.label], cli_side[band.label])

    def test_a_counterparty_roster_without_path_is_refused_rather_than_seated_as_us(self):
        full = sim.basis(THEIR_ROSTER)
        name = sim.our_roster(THEIR_ROSTER)[0]["n"]
        with self.assertRaises(ValueError) as ctx:
            bracket.player_title(full, [name], blocks=1, R=flat_R())
        self.assertIn("path=", str(ctx.exception))

    def test_incoming_title_on_a_counterparty_roster_without_path_is_refused(self):
        body = sim.star(40.0, 68, ("C",), n="INCOMING")
        with self.assertRaises(ValueError) as ctx:
            bracket.incoming_title(sim.basis(THEIR_ROSTER), [body],
                                   blocks=1, R=flat_R())
        self.assertIn("path=", str(ctx.exception))

    def test_roster_title_on_a_counterparty_roster_without_path_is_refused(self):
        full = sim.basis(THEIR_ROSTER)
        name = sim.our_roster(THEIR_ROSTER)[0]["n"]
        without = sim.swap(full, [name], [sim.star(10, 68, ("C",), n="DEAD")])
        with self.assertRaises(ValueError) as ctx:
            bracket.roster_title(full, without, blocks=1)
        self.assertIn("path=", str(ctx.exception))

    def test_a_name_not_on_the_roster_is_refused(self):
        with cheap_monte_carlo(4, blocks=1):
            with self.assertRaises(KeyError):
                bracket.player_title(sim.basis(), ["Nobody At All"], blocks=1,
                                     R=flat_R())


class UnconditionalTitle(unittest.TestCase):
    def test_a_starter_is_worth_more_than_the_body_that_replaces_him(self):
        full = sim.basis()
        with cheap_monte_carlo(8, seasons=200):
            mean, sd, blocks = sim.player_title(
                full, ["Jalen Suggs"], blocks=2).popitem()[1]
        self.assertGreater(mean, 0.0)
        self.assertLess(mean, 1.0)
        self.assertEqual(len(blocks), 2)
        self.assertGreater(sd, 0.0)

    def test_incoming_title_is_positive_for_a_star(self):
        body = sim.star(40.0, 68, ("C",), n="INCOMING")
        with cheap_monte_carlo(8, seasons=200):
            mean, sd, blocks = sim.incoming_title(
                sim.basis(), [body], blocks=2).popitem()[1]
        self.assertGreater(mean, 0.0)
        self.assertEqual(len(blocks), 2)
        self.assertGreater(sd, 0.0)

    def test_a_roster_with_nothing_padded_refuses_incoming_title(self):
        full = [p if p["n"] not in roster_mod.PAD_NAMES
                else dict(p, n="Real %d" % i)
                for i, p in enumerate(sim.basis())]
        with self.assertRaises(ValueError) as ctx:
            sim.incoming_title(full, [sim.star(40.0, 68, ("C",), n="IN")],
                               blocks=1, trials=20)
        self.assertIn("padded", str(ctx.exception))

    def test_a_body_already_on_the_roster_is_refused_rather_than_added_again(self):
        theirs = sim.our_roster(THEIR_ROSTER)
        with self.assertRaises(ValueError) as e:
            sim.incoming_title(sim.basis(THEIR_ROSTER), theirs, blocks=1,
                               trials=20)
        self.assertIn(theirs[0]["n"], str(e.exception))
        self.assertIn("already on this roster", str(e.exception))

    def test_a_side_of_a_deal_is_priced_in_one_joint_run(self):
        with cheap_monte_carlo(8, seasons=200):
            full, R = sim.basis(), flat_R()
            name = sim.our_roster()[0]["n"]
            body, = [p for p in full if p["n"] == name]
            without = sim.swap(full, [name],
                               [sim.group_body(sim.slot_group(body["elig"]),
                                               R[sim.slot_group(body["elig"])])])
            row, = sim.player_title(full, [name], blocks=2, R=R).values()
            joint = sim.roster_title(full, without, blocks=2)
        self.assertEqual(joint, row)

    def test_path_selects_the_seat_in_the_draw(self):
        theirs = "roster-161018-2025-26.json"
        with cheap_monte_carlo(8, seasons=80):
            full = sim.basis(theirs)
            name = sim.our_roster(theirs)[0]["n"]
            got, = sim.player_title(full, [name], blocks=1, R=flat_R(),
                                    path=theirs).values()
            was = roster_mod.ROSTER
            try:
                roster_mod.ROSTER = theirs
                cli_side, = sim.player_title(full, [name], blocks=1,
                                             R=flat_R()).values()
            finally:
                roster_mod.ROSTER = was
        self.assertEqual(got, cli_side)

    def test_a_counterparty_roster_without_path_is_refused_rather_than_seated_as_us(self):
        full = sim.basis(THEIR_ROSTER)
        name = sim.our_roster(THEIR_ROSTER)[0]["n"]
        with cheap_monte_carlo(4, seasons=20):
            with self.assertRaises(ValueError) as ctx:
                sim.player_title(full, [name], blocks=1)
        self.assertIn("path=", str(ctx.exception))

    def test_incoming_title_on_a_counterparty_roster_without_path_is_refused(self):
        body = sim.star(40.0, 68, ("C",), n="INCOMING")
        with cheap_monte_carlo(4, seasons=20):
            with self.assertRaises(ValueError) as ctx:
                sim.incoming_title(sim.basis(THEIR_ROSTER), [body], blocks=1)
        self.assertIn("path=", str(ctx.exception))

    def test_roster_title_on_a_counterparty_roster_without_path_is_refused(self):
        full = sim.basis(THEIR_ROSTER)
        name = sim.our_roster(THEIR_ROSTER)[0]["n"]
        without = sim.swap(full, [name], [sim.star(10, 68, ("C",), n="DEAD")])
        with cheap_monte_carlo(4, seasons=20):
            with self.assertRaises(ValueError) as ctx:
                sim.roster_title(full, without, blocks=1)
        self.assertIn("path=", str(ctx.exception))

    def test_swap_odds_on_a_counterparty_roster_without_path_is_refused(self):
        full = sim.basis(THEIR_ROSTER)
        name = sim.our_roster(THEIR_ROSTER)[0]["n"]
        after = sim.swap(full, [name], [sim.star(40, 68, ("C",), n="IN")])
        with cheap_monte_carlo(4, seasons=20):
            with self.assertRaises(ValueError) as ctx:
                sim.swap_odds(after, full)
        self.assertIn("path=", str(ctx.exception))

    def test_a_name_not_on_the_roster_is_refused(self):
        with cheap_monte_carlo(4, seasons=20):
            with self.assertRaises(KeyError):
                sim.player_title(sim.basis(), ["Nobody At All"], blocks=1)

class OneDraw(unittest.TestCase):
    def test_the_draw_the_report_publishes_is_the_one_its_own_seed_gives(self):
        pinned = {t.path: t.mus for t in bracket.team_levels()}
        with bracket.draw(bracket.SEED0):
            self.assertEqual({t.path: t.mus for t in bracket.team_levels()}, pinned)

    def test_a_re_draw_moves_the_field_and_not_only_the_loaded_roster(self):
        pinned = {t.path: t.mus for t in bracket.team_levels()}
        with bracket.draw(bracket.SEED0 + engine.TRIALS):
            moved = {t.path: t.mus for t in bracket.team_levels()}
        self.assertEqual(set(moved), set(pinned))
        for path in sorted(pinned):
            with self.subTest(team=path):
                self.assertNotEqual(moved[path], pinned[path])

    def test_the_field_is_back_on_its_own_draw_afterwards(self):
        pinned = {t.path: t.mus for t in bracket.team_levels()}
        with bracket.draw(bracket.SEED0 + engine.TRIALS):
            pass
        self.assertEqual({t.path: t.mus for t in bracket.team_levels()}, pinned)


class ParallelTitle(unittest.TestCase):
    def test_a_sharded_season_matches_the_sequential_one(self):
        teams = bracket.team_levels()
        seq = title.full_season(teams, trials=120, workers=1)
        par = title.full_season(teams, trials=120, workers=4)
        for path in seq:
            with self.subTest(team=path):
                self.assertAlmostEqual(seq[path].title, par[path].title,
                                       places=9)
                self.assertAlmostEqual(seq[path].wins, par[path].wins, places=9)

    def test_paired_delta_matches_sequential_workers(self):
        body = sim.star(40.0, 68, ("C",), n="INCOMING")
        with cheap_monte_carlo(8, seasons=120):
            seq, = sim.incoming_title(sim.basis(), [body], blocks=2,
                                      workers=1).values()
            shard.retire()
            par, = sim.incoming_title(sim.basis(), [body], blocks=2).values()
        self.assertEqual(seq, par)

    @unittest.skipIf((os.cpu_count() or 1) < 2, "one core shards into one chunk")
    def test_incoming_title_survives_measure_then_shard(self):
        shard.retire()
        row, = sim.our_roster("roster-161018-2025-26.json")[:1]
        with cheap_monte_carlo(8, seasons=120):
            mean, _, _ = sim.incoming_title(sim.basis(), [row],
                                            blocks=1).popitem()[1]
        self.assertGreater(mean, 0.0)

    @unittest.skipIf((os.cpu_count() or 1) < 2, "one core shards into one chunk")
    def test_player_title_actually_puts_more_than_one_process_to_work(self):
        shard.retire()
        full = sim.basis()
        names = [p["n"] for p in sim.our_roster()][:6]
        with cheap_monte_carlo(8, seasons=40):
            before = {c.pid for c in multiprocessing.active_children()}
            sim.player_title(full, names, blocks=1)
            started = ({c.pid for c in multiprocessing.active_children()}
                      - before)
        self.assertGreater(len(started), 1,
                           "the per-player work never left this process")

    def test_player_title_cross_player_shard_matches_sequential_workers(self):
        full = sim.basis()
        names = [p["n"] for p in sim.our_roster()][:6]
        with cheap_monte_carlo(8, seasons=120):
            seq = sim.player_title(full, names, blocks=2, workers=1)
            shard.retire()
            par = sim.player_title(full, names, blocks=2)
        self.assertEqual(seq, par)

    def test_incoming_title_cross_player_shard_matches_sequential_workers(self):
        bodies = [sim.star(30.0 + i, 68, ("C",), n="IN%d" % i)
                 for i in range(6)]
        with cheap_monte_carlo(8, seasons=120):
            seq = sim.incoming_title(sim.basis(), bodies, blocks=2, workers=1)
            shard.retire()
            par = sim.incoming_title(sim.basis(), bodies, blocks=2)
        self.assertEqual(seq, par)


class DealOdds(unittest.TestCase):
    def test_unchanged_rosters_move_by_exactly_nothing(self):
        with cheap_monte_carlo(4, seasons=300):
            after_us, before_us, after_them, before_them = sim.deal_odds(
                sim.basis(), sim.basis(THEIR_ROSTER), THEIR_ROSTER)
        self.assertEqual(after_us, before_us)
        self.assertEqual(after_them, before_them)

    def test_field_seats_both_after_rosters(self):
        ours = sim.basis()
        theirs = sim.basis(THEIR_ROSTER)
        deni = rostered("Deni Avdija", THEIR_ROSTER)
        suggs = rostered("Jalen Suggs")
        after_us = sim.swap(ours, ["Jalen Suggs"], [deni])
        after_them = sim.swap(theirs, ["Deni Avdija"], [suggs])
        with cheap_monte_carlo():
            field, who_us, who_them = title.deal_field(
                after_us, after_them, THEIR_ROSTER)
            us = next(t for t in field if t.path == who_us)
            them = next(t for t in field if t.path == who_them)
            self.assertEqual(us, sim.measure(after_us, who_us))
            self.assertEqual(them, sim.measure(after_them, who_them))
