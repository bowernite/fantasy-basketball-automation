import unittest
from tests.harness import *

class OptimalLineup(unittest.TestCase):
    def best_possible(self, avail):
        dp = {0: 0.0}
        for val, elig, _ in avail:
            nxt = dict(dp)
            for mask, total in dp.items():
                for si, (_, slot) in enumerate(sim.SLOTS):
                    bit = 1 << si
                    if mask & bit or not elig & slot:
                        continue
                    if total + val > nxt.get(mask | bit, -1.0):
                        nxt[mask | bit] = total + val
            dp = nxt
        return max(dp.values())

    def test_no_other_legal_lineup_scores_more(self):
        roster = sim.basis()
        rng = random.Random(3)
        for case in range(30):
            up = rng.sample(roster, rng.randint(4, 18))
            avail = [(p["avg"], set(p["elig"]), i) for i, p in enumerate(up)]
            with self.subTest(case=case, n=len(up)):
                total, filled, who = sim.lineup(avail)
                self.assertEqual(len(who), len(set(who)))
                self.assertEqual(filled, len(who))
                self.assertLessEqual(filled, len(sim.SLOTS))
                self.assertAlmostEqual(total, self.best_possible(avail), places=6)

    def test_a_body_with_no_legal_slot_left_does_not_start(self):
        centers = [(float(40 - i), {"C"}, i) for i in range(12)]
        total, filled, who = sim.lineup(centers)
        self.assertEqual(filled, sim.group_slots(("C",)))
        self.assertEqual(sorted(who), [0, 1, 2])
        self.assertEqual(total, 40 + 39 + 38)

class CommonRandomNumbers(unittest.TestCase):
    def test_swapping_a_player_for_his_own_clone_changes_nothing(self):
        full = sim.our_roster() + sim.EXPANSION
        clone = dict(full[0])
        same = sim.swap(full, [clone["n"]], [clone])
        self.assertEqual(sim.run(same, trials=8)["pf"], sim.run(full, trials=8)["pf"])

    def test_a_three_for_three_of_clones_changes_nothing_either(self):
        full = sim.basis()
        clones = [dict(p) for p in full[:3]]
        same = sim.swap(full, [p["n"] for p in clones], clones)
        self.assertEqual(sim.run(same, trials=8)["pf"], sim.run(full, trials=8)["pf"])

class ParallelTrials(unittest.TestCase):
    def test_a_sharded_run_matches_the_sequential_one_digit_for_digit(self):
        full = sim.basis()
        seq = sim.run(full, trials=25, workers=1)
        par = sim.run(full, trials=25, workers=3)
        self.assertEqual(seq, par)

    def test_the_default_shard_matches_the_sequential_run_at_full_trials(self):
        full = sim.basis()
        self.assertEqual(sim.run(full, workers=1), sim.run(full))

    @unittest.skipIf((os.cpu_count() or 1) < 2, "one core shards into one chunk")
    def test_the_default_run_actually_puts_more_than_one_process_to_work(self):
        shard.retire()
        before = {c.pid for c in multiprocessing.active_children()}
        sim.run(sim.basis())
        started = {c.pid for c in multiprocessing.active_children()} - before
        self.assertGreater(len(started), 1, "the trials never left this process")

    def test_a_worker_dying_costs_speed_and_not_the_answer(self):
        full = sim.basis()
        seq = sim.run(full, trials=60, workers=1)
        self.assertEqual(sim.run(full, trials=60, workers=4), seq)
        os.kill(next(iter(shard._POOL._processes)), signal.SIGKILL)
        self.assertEqual(sim.run(full, trials=60, workers=4), seq)
        self.assertEqual(sim.run(full, trials=60, workers=4), seq)

class BatchedRosters(unittest.TestCase):
    def test_a_batch_of_one_matches_a_direct_run(self):
        full = sim.basis()
        self.assertEqual(engine.run_many([full], trials=25, workers=1),
                         [sim.run(full, trials=25, workers=1)])

    def test_sharding_by_roster_matches_sequential_by_roster_digit_for_digit(
            self):
        full = sim.basis()
        swapped = sim.swap(full, [full[0]["n"]], [dict(full[0], avg=99.0)])
        rosters = [full, swapped, full, swapped]
        seq = engine.run_many(rosters, trials=25, workers=1)
        par = engine.run_many(rosters, trials=25, workers=2)
        self.assertEqual(seq, par)
        self.assertEqual(seq, [sim.run(r, trials=25, workers=1)
                               for r in rosters])

    @unittest.skipIf((os.cpu_count() or 1) < 2, "one core shards into one chunk")
    def test_the_default_batch_actually_puts_more_than_one_process_to_work(
            self):
        shard.retire()
        before = {c.pid for c in multiprocessing.active_children()}
        engine.run_many([sim.basis()] * 60, trials=2)
        started = {c.pid for c in multiprocessing.active_children()} - before
        self.assertGreater(len(started), 1, "the batch never left this process")

class ShardedReports(unittest.TestCase):
    def table(self, report, workers, trials=4):
        real_run, real_many, was_blocks = (engine.run, engine.run_many,
                                          value.PLAYER_BLOCKS)
        engine.run = lambda roster, **kw: real_run(
            roster, **dict(kw, trials=trials, workers=workers))
        engine.run_many = lambda rosters, **kw: real_many(
            rosters, **dict(kw, trials=trials, workers=workers))
        value.PLAYER_BLOCKS = 1
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                sim.REPORTS[report]()
        finally:
            engine.run, engine.run_many, value.PLAYER_BLOCKS = (
                real_run, real_many, was_blocks)
        return buf.getvalue()

    def test_the_breakevens_table_is_the_same_table_sharded(self):
        self.assertEqual(self.table("breakevens", 1),
                         self.table("breakevens", 4))

    def test_the_schedules_table_is_the_same_table_sharded(self):
        self.assertEqual(self.table("schedules", 1), self.table("schedules", 4))

    def test_a_report_run_from_the_shell_finishes_and_says_nothing_on_stderr(self):
        p = sim_process("formula")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stderr, "")
        self.assertIn("FORMULA", p.stdout)

class ScriptsThatImportSim(unittest.TestCase):
    def script(self, body):
        path = os.path.join(tempfile.mkdtemp(), "price_it.py")
        with open(path, "w") as f:
            f.write(body)
        return subprocess.run(
            [sys.executable, path], cwd=sim.HERE, capture_output=True,
            text=True, env=dict(os.environ, PYTHONPATH=sim.HERE))

    def test_a_script_that_prices_a_roster_prints_its_table_once(self):
        p = self.script("import sim\n"
                        "print('MY TABLE')\n"
                        "print('pf', sim.run(sim.basis())['pf'])\n")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.count("MY TABLE"), 1, p.stdout)
        self.assertNotIn("Traceback", p.stderr)
