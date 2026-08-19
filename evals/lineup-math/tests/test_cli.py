import unittest
from tests.harness import *

class CLI(unittest.TestCase):
    def test_naming_no_report_runs_the_one_the_usage_says_it_will(self):
        """`./run sim.py` alone is the first thing anybody types, and the
        report it lands on is promised in `--help` rather than chosen there. The
        default is also the one path no `sim.py <report>` test covers, so it can
        break while every named report still runs"""
        _, usage = cli("--help")
        promised, = re.findall(r"With no report named, runs `(\w+)`",
                               one_line(usage))
        status, out = cli()
        self.assertEqual(status, 0, out)
        self.assertIn(promised.upper(), out)

    def test_a_misspelled_report_name_fails_instead_of_printing_another_one(self):
        """`trades` and `eval-team` both mandate a sim run before recommending
        a deal. A silent fallback to `calibration` means `sim.py breakeven`
        exits 0 having printed a table the reader did not ask for, and he books
        it as the break-evens he thinks he just ran"""
        p = sim_process("breakeven")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("CALIBRATION", p.stdout)
        for name in sim.REPORTS:
            self.assertIn(name, p.stdout + p.stderr)

    def test_the_roster_flag_reaches_the_report_it_precedes(self):
        """`render` puts the path on `roster_mod` itself, so nothing it covers
        touches the flag parsing that is supposed to put a counterparty's file
        there. A `--roster` that quietly kept OUR file prints our players under
        his team's name, and `Δw theirs` is the one number the counterparty
        workflow exists to produce"""
        status, out = cli("--roster", THEIR_ROSTER, "players")
        self.assertEqual(status, 0, out)
        self.assertIn(THEIR_ROSTER, out, "the run has to name the file it priced")
        theirs = {p["n"] for p in sim.our_roster(THEIR_ROSTER)}
        for name in sorted(theirs):
            self.assertIn(name, out)
        for name in sorted({p["n"] for p in sim.our_roster()} - theirs):
            self.assertNotIn(name, out)

    def test_a_bad_name_beside_a_good_one_runs_neither(self):
        """Same booking hazard as a lone misspelling, one step later. `sim.py
        players breakeven` printing PLAYERS and then dying leaves a table on
        screen from a command that exited 1, and the reader quotes it as the
        run he asked for"""
        status, out = cli("players", "bogus")
        self.assertNotEqual(status, 0)
        self.assertNotIn("PLAYERS", out)

    def test_a_file_that_is_not_a_roster_is_refused_before_any_table_prints(self):
        """The existence check passed and the run then died on a JSON decode
        error mid-report, under a header that reads as a started run -- exactly
        what the path check above it was written to prevent. `--roster
        findings.md` and a half-written fetch both land here"""
        path = os.path.join(tempfile.mkdtemp(), "notaroster.json")
        with open(path, "w") as f:
            f.write("# notes\n")
        p = sim_process("--roster", path, "players")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertNotIn("PLAYERS", p.stdout)
        self.assertIn(path, p.stdout + p.stderr)

    def test_a_report_that_refuses_says_so_without_a_traceback(self):
        """Half these refusals are written as prose -- `schedules` on a roster
        with no auction slots, a missing board snapshot, a name the pool has
        never seen. They arrived wrapped in a stack trace, which reads as the
        command being broken rather than as the answer it is"""
        full = roster_file(*[
            {"n": "Body %d" % i, "tm": "LAC", "avg": 20.0, "tot": 0.0, "gp": 60,
             "posLabel": "F", "elig": ["SF", "PF"]} for i in range(38)])
        p = sim_process("--roster", full, "schedules", "positions")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("auction", p.stdout + p.stderr)
        self.assertIn("positions", p.stdout + p.stderr,
                      "the run died without saying what it never ran")

    def test_a_report_that_breaks_is_not_dressed_up_as_one_that_refuses(self):
        """The refusals above are authored prose and are caught as
        `ValueError`. `statistics.StatisticsError` IS a `ValueError`, and
        `playoffs` alone makes ~20 `mean`/`stdev` calls -- caught with them, a
        broken run prints a tidy one-line explanation with no file, no line and
        no traceback, and reads exactly like an answer"""
        name = sorted(sim.ROSTER_FREE)[0]
        was = reports.REPORTS[name]
        reports.REPORTS[name] = lambda: statistics.mean([])
        try:
            with self.assertRaises(statistics.StatisticsError):
                cli(name)
        finally:
            reports.REPORTS[name] = was

    def test_help_describes_every_report_without_running_one(self):
        """The whole point of the flag: an agent handed this command learns the
        surface from the command, not from README.md. A `--help` treated as a
        report name exits 1 with a bare list of words, which reads as a failure
        and describes nothing"""
        p = sim_process("--help")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertNotIn("=" * 72, p.stdout, "--help ran a report")
        for name in sim.REPORTS:
            self.assertIn(name, p.stdout)
            self.assertIn(sim.BLURB[name], p.stdout)

    def test_help_says_which_reports_refuse_a_counterparty_roster(self):
        """`--roster` on one of the four is the commonest way to mistype this
        command, and the refusal is the only place that list appears"""
        p = sim_process("--help")
        for name in sim.OURS_ONLY:
            self.assertRegex(p.stdout, r"%s.*\(ours only\)" % name)

    def test_a_slow_report_names_itself_before_it_finishes(self):
        """Two of the fourteen run for minutes, and every caller captures this
        through a pipe, which Python block-buffers. A run cut short then hands
        back ZERO bytes -- no report name, nothing separating slow from hung
        from crashed"""
        p = subprocess.Popen([sys.executable, "sim.py", "schedules"],
                             cwd=sim.HERE, stdout=subprocess.PIPE, text=True)
        first = []
        reader = threading.Thread(target=lambda: first.append(p.stdout.readline()))
        reader.daemon = True
        reader.start()
        reader.join(20)
        p.kill()
        p.wait()
        p.stdout.close()
        self.assertTrue(first, "nothing reached the pipe in 20s")
        self.assertIn("=", first[0])

    def test_each_report_header_names_the_roster_that_report_priced(self):
        """One banner on line 1 of a multi-report run leaves thousands of lines
        between it and the tables, and a single table lifted out of the run --
        which is how these get quoted -- carries no team at all"""
        status, out = cli("--roster", THEIR_ROSTER, "players", "positions")
        self.assertEqual(status, 0, out)
        heads = [l for l in out.splitlines()
                 if l.startswith(("PLAYERS", "POSITIONS"))]
        self.assertEqual(len(heads), 2, out)
        for head in heads:
            self.assertIn(THEIR_ROSTER, head)

    def test_a_report_that_reads_no_roster_does_not_claim_one(self):
        """`market` is the board and the pool; its table is byte-identical
        whatever `--roster` says. A header naming a counterparty over it
        attributes to that team a measurement of nobody"""
        status, out = cli("--roster", THEIR_ROSTER, "market")
        self.assertEqual(status, 0, out)
        self.assertNotIn(THEIR_ROSTER, out.splitlines()[1])

    def test_the_header_names_the_team_not_just_its_id(self):
        """`roster-161020-2025-26.json` is a team only to a reader holding the
        `team-info` table. The command knows the name at fetch time, so the run
        it labels should not send its reader to a skill file to find out whose
        roster he is looking at"""
        teams = json.loads(read_text(
            os.path.join(sim.HERE, "teams-%s.json" % fetch_data.SEASON_TAG)))
        status, out = cli("--roster", THEIR_ROSTER, "positions")
        self.assertEqual(status, 0, out)
        self.assertIn(teams[THEIR_ROSTER.split("-")[1]], out.splitlines()[1])

    def test_every_report_named_in_one_run_prints(self):
        """The README advertises the reports on one line, so a run that takes
        the first name and drops the rest answers half of what was asked with
        no sign that it did"""
        status, out = cli("nights", "formula")
        self.assertEqual(status, 0, out)
        self.assertIn("NIGHTS", out)
        self.assertIn("FORMULA", out)

    def test_the_directory_runner_says_how_to_invoke_each_thing_in_here(self):
        """The first command a human or an agent types in this directory. With
        no arguments it has to name sim.py, fetch_data.py and how to run the
        tests, or the reader opens README.md to find the other two"""
        for argv in (["./run"], ["./run", "-h"], ["./run", "--help"]):
            with self.subTest(argv=argv):
                p = subprocess.run(argv, cwd=sim.HERE, capture_output=True,
                                   text=True)
                self.assertNotEqual(p.returncode, 0)
                out = p.stdout + p.stderr
                self.assertIn("sim.py", out)
                self.assertIn("fetch_data.py", out)
                self.assertIn("./run test", out)

    @unittest.skipUnless(shutil.which("pypy3.11"), "pypy3.11 not installed")
    def test_the_directory_runner_is_the_command_that_lists_the_reports(self):
        """`--help` is how an agent learns the surface. It has to come off
        `./run sim.py`, not a python3 invocation the README no longer leads with"""
        p = subprocess.run(["./run", "sim.py", "--help"], cwd=sim.HERE,
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(sorted(re.findall(r"^  (\w[\w-]*) ", p.stdout, re.M)),
                         sorted(sim.REPORTS))

class EveryReportRunsEndToEnd(unittest.TestCase):
    """A report that names the players it trades as literals breaks the moment
    the roster file is re-cut, and every unit underneath it stays green. The
    file is re-cut after every trade, so that is a standing hazard for any
    report holding a name, which is what makes every one worth paying for"""

    def test_every_report_runs_on_our_roster(self):
        for name in sorted(sim.REPORTS):
            with self.subTest(report=name):
                self.assertTrue(render(name).strip(), "printed nothing")

    def test_every_report_not_scoped_to_us_runs_on_a_counterparty_roster(self):
        """The other half of the same hazard. A counterparty's file is a
        DIFFERENT shape, 26 bodies not 28, unsigned players, whole seasons
        missing, none of our names, and `--roster` is advertised for any of
        them"""
        for name in sorted(set(sim.REPORTS) - sim.OURS_ONLY):
            with self.subTest(report=name):
                self.assertTrue(render(name, THEIR_ROSTER).strip(),
                                "printed nothing")
