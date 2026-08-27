import unittest
from tests.harness import *

class ParallelPlayerWins(unittest.TestCase):
    def test_a_sharded_batch_matches_the_sequential_one(self):
        full = sim.basis()
        names = [p["n"] for p in sim.our_roster()]
        R = flat_R()
        seq = sim.player_wins(full, names, blocks=1, trials=10, R=R, workers=1)
        par = sim.player_wins(full, names, blocks=1, trials=10, R=R, workers=3)
        self.assertEqual(seq, par)

    def test_a_short_call_never_leaves_this_process(self):
        shard.retire()
        full = sim.basis()
        before = {c.pid for c in multiprocessing.active_children()}
        sim.player_wins(full, [full[0]["n"]], blocks=1, trials=10, R=flat_R())
        self.assertEqual(
            {c.pid for c in multiprocessing.active_children()} - before, set())

    @unittest.skipIf((os.cpu_count() or 1) < 2, "one core shards into one job")
    def test_a_full_roster_call_actually_puts_more_than_one_process_to_work(self):
        shard.retire()
        full = sim.basis()
        names = [p["n"] for p in sim.our_roster()]
        before = {c.pid for c in multiprocessing.active_children()}
        sim.player_wins(full, names, blocks=1, trials=10, R=flat_R())
        started = {c.pid for c in multiprocessing.active_children()} - before
        self.assertGreater(len(started), 1, "the roster never left this process")


class ParallelIncomingWins(unittest.TestCase):
    def test_a_sharded_batch_matches_the_sequential_one(self):
        full = sim.basis()
        players = sim.our_roster(THEIR_ROSTER)
        R = flat_R()
        seq = sim.incoming_wins(full, players, blocks=1, trials=10, R=R,
                                workers=1)
        par = sim.incoming_wins(full, players, blocks=1, trials=10, R=R,
                                workers=3)
        self.assertEqual(seq, par)

    def test_a_short_call_never_leaves_this_process(self):
        shard.retire()
        full = sim.basis()
        players = sim.our_roster(THEIR_ROSTER)[:1]
        before = {c.pid for c in multiprocessing.active_children()}
        sim.incoming_wins(full, players, blocks=1, trials=10, R=flat_R())
        self.assertEqual(
            {c.pid for c in multiprocessing.active_children()} - before, set())
