import unittest
from tests.harness import *

class OptimalLineup(unittest.TestCase):
    """"Lineups are set optimally every night" is the premise under every PF
    figure here, and what lets the README call absolute PF an UPPER bound.
    Greedy placement with Kuhn augmentation is only exact because capacities
    are 1 and players are added in descending value, and a matching that misses
    a swap loses points on exactly the crowded nights the study is about"""

    def best_possible(self, avail):
        """The optimum by dynamic programming over subsets of the 9 slots, a
        different algorithm from the augmenting placement `lineup` uses"""
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
        """On real nights, not toy ones. The bodies and eligibilities are drawn
        from the 38-man roster, at the sizes `nights` says the cap actually
        bites on"""
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
        """The positional half of the 9-slot cap. A pure center reaches C and
        the two ANY slots and no further, so the 4th-best center on the roster
        scores nothing however good he is"""
        centers = [(float(40 - i), {"C"}, i) for i in range(12)]
        total, filled, who = sim.lineup(centers)
        self.assertEqual(filled, sim.group_slots(("C",)))
        self.assertEqual(sorted(who), [0, 1, 2])
        self.assertEqual(total, 40 + 39 + 38)

class CommonRandomNumbers(unittest.TestCase):
    def test_swapping_a_player_for_his_own_clone_changes_nothing(self):
        """A scenario must perturb only what it changes. Appending the incoming
        player rather than replacing in place shifts every later player's
        availability draw, which buries sub-0.1-win deltas in Monte-Carlo noise
        """
        full = sim.our_roster() + sim.EXPANSION
        clone = dict(full[0])
        same = sim.swap(full, [clone["n"]], [clone])
        self.assertEqual(sim.run(same, trials=8)["pf"], sim.run(full, trials=8)["pf"])

    def test_a_three_for_three_of_clones_changes_nothing_either(self):
        """A different path, and the one a real offer is priced on. With three
        bodies leaving and three arriving, a `swap` that appended the arrivals
        instead of seating them in the vacated slots re-orders everything below
        them and shifts every later draw, worth several tenths of a win against
        a joint-vs-summed gap of about one"""
        full = sim.basis()
        clones = [dict(p) for p in full[:3]]
        same = sim.swap(full, [p["n"] for p in clones], clones)
        self.assertEqual(sim.run(same, trials=8)["pf"], sim.run(full, trials=8)["pf"])

class ParallelTrials(unittest.TestCase):
    """`run` shards trials across processes. `wk` is a stride over the
    concatenated weeks, and `by_night` accumulates floats, so any reassembly
    order other than the sequential trial order reprints every published
    figure. The two paths have to be the same dict, not merely close"""

    def test_a_sharded_run_matches_the_sequential_one_digit_for_digit(self):
        full = sim.basis()
        seq = sim.run(full, trials=25, workers=1)
        par = sim.run(full, trials=25, workers=3)
        self.assertEqual(seq, par)

    def test_the_default_shard_matches_the_sequential_run_at_full_trials(self):
        """The path every published figure actually takes. `workers=3` above is
        a shard this file chose; the reports pass no `workers` at all and get
        `TRIALS` cut into as many chunks as the machine has cores, and none of
        those chunkings may print a different number"""
        full = sim.basis()
        self.assertEqual(sim.run(full, workers=1), sim.run(full))

    @unittest.skipIf((os.cpu_count() or 1) < 2, "one core shards into one chunk")
    def test_the_default_run_actually_puts_more_than_one_process_to_work(self):
        """Every other test here asserts the sharded answer EQUALS the
        sequential one, and sequential-everywhere satisfies all of them while the
        reports go back to taking three minutes. Somebody has to check the work
        was spread at all"""
        shard.retire()      # so the run has to build its own rather than inherit
        before = {c.pid for c in multiprocessing.active_children()}
        sim.run(sim.basis())
        started = {c.pid for c in multiprocessing.active_children()} - before
        self.assertGreater(len(started), 1, "the trials never left this process")

    def test_a_worker_dying_costs_speed_and_not_the_answer(self):
        """The pool is cached across calls, so a worker killed under it -- the
        OOM killer is the realistic one, at one process per core -- would break
        not just the call it died on but EVERY later `run` in the process, and a
        report is hundreds of runs long. Sequential accumulation cannot fail this
        way, and sharding it is not allowed to introduce a way"""
        full = sim.basis()
        seq = sim.run(full, trials=60, workers=1)
        self.assertEqual(sim.run(full, trials=60, workers=4), seq)
        os.kill(next(iter(shard._POOL._processes)), signal.SIGKILL)
        self.assertEqual(sim.run(full, trials=60, workers=4), seq)
        self.assertEqual(sim.run(full, trials=60, workers=4), seq)

class ShardedReports(unittest.TestCase):
    """The two reports the sharding was built for, printed both ways.

    `ParallelTrials` prices ONE roster; a report is hundreds of runs, each
    feeding the next -- a break-even interpolates, so a last-digit disagreement
    moves the next point it probes and prints a different rate. Nothing else
    here runs a report sharded at all: every other report test goes through
    `cheap_monte_carlo`, which is under the floor and never touches a pool
    """

    def table(self, report, workers, trials=4):
        """One report's stdout with every `run` under it forced to `workers`.
        `trials` is a count these print SOMETHING at, not the published one --
        the two paths have to agree at any count. A printed table is rounded, so
        last-digit reassembly noise is `ParallelTrials`' to catch on the dict;
        what this reaches past that is a report driving the pool hundreds of
        times over and the answer arriving as a table rather than a traceback"""
        real, was_blocks = engine.run, value.PLAYER_BLOCKS
        engine.run = lambda roster, **kw: real(
            roster, **dict(kw, trials=trials, workers=workers))
        value.PLAYER_BLOCKS = 1
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                sim.REPORTS[report]()
        finally:
            engine.run, value.PLAYER_BLOCKS = real, was_blocks
        return buf.getvalue()

    def test_the_breakevens_table_is_the_same_table_sharded(self):
        self.assertEqual(self.table("breakevens", 1),
                         self.table("breakevens", 4))

    def test_the_schedules_table_is_the_same_table_sharded(self):
        self.assertEqual(self.table("schedules", 1), self.table("schedules", 4))

    def test_a_report_run_from_the_shell_finishes_and_says_nothing_on_stderr(self):
        """Everything above drives a report inside THIS interpreter, where the
        pool is already warm and `__main__` is the test runner. Typed at a
        prompt it is a fresh process building a pool of one per core, and the
        ways that goes wrong -- a worker that cannot start, a pool that never
        shuts down, a warning per fork -- all land on a stderr no in-process
        test reads. `formula` is the cheapest report at the published count, so
        it is the one that can afford to be a real process"""
        p = sim_process("formula")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stderr, "")
        self.assertIn("FORMULA", p.stdout)

class ScriptsThatImportSim(unittest.TestCase):
    """The other half of the surface the README advertises: `import sim` from a
    throwaway script. Most of the scripts beside this file run their body at
    module level, with no `if __name__ == "__main__"` guard"""

    def script(self, body):
        """One `python3 whatever.py` off the import surface, written the way the
        scripts in this directory are written -- module level, no guard"""
        path = os.path.join(tempfile.mkdtemp(), "price_it.py")
        with open(path, "w") as f:
            f.write(body)
        return subprocess.run(
            [sys.executable, path], cwd=sim.HERE, capture_output=True,
            text=True, env=dict(os.environ, PYTHONPATH=sim.HERE))

    def test_a_script_that_prices_a_roster_prints_its_table_once(self):
        """Under `spawn` -- the platform default here -- every worker re-imports
        the module it was started from, and for a caller like this one that is
        the script, body and all: its table prints once per worker, and the
        re-import trips `_check_not_importing_main` in each child and puts that
        traceback on stderr. The number survives it (the pool retires and the
        call finishes in-process), so nothing that compares two numbers can see
        this"""
        p = self.script("import sim\n"
                        "print('MY TABLE')\n"
                        "print('pf', sim.run(sim.basis())['pf'])\n")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.count("MY TABLE"), 1, p.stdout)
        self.assertNotIn("Traceback", p.stderr)
