import unittest
from tests.harness import *

class CLI(unittest.TestCase):
    def test_naming_no_report_runs_the_one_the_usage_says_it_will(self):
        _, usage = cli("--help")
        promised, = re.findall(r"With no report named, runs `(\w+)`",
                               one_line(usage))
        status, out = cli()
        self.assertEqual(status, 0, out)
        self.assertIn(promised.upper(), out)

    def test_a_misspelled_report_name_fails_instead_of_printing_another_one(self):
        p = sim_process("breakeven")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("CALIBRATION", p.stdout)
        for name in sim.REPORTS:
            self.assertIn(name, p.stdout + p.stderr)

    def test_the_roster_flag_reaches_the_report_it_precedes(self):
        status, out = cli("--roster", THEIR_ROSTER, "players")
        self.assertEqual(status, 0, out)
        self.assertIn(THEIR_ROSTER, out, "the run has to name the file it priced")
        theirs = {p["n"] for p in sim.our_roster(THEIR_ROSTER)}
        for name in sorted(theirs):
            self.assertIn(name, out)
        for name in sorted({p["n"] for p in sim.our_roster()} - theirs):
            self.assertNotIn(name, out)

    def test_a_bad_name_beside_a_good_one_runs_neither(self):
        status, out = cli("players", "bogus")
        self.assertNotEqual(status, 0)
        self.assertNotIn("PLAYERS", out)

    def test_a_file_that_is_not_a_roster_is_refused_before_any_table_prints(self):
        path = os.path.join(tempfile.mkdtemp(), "notaroster.json")
        with open(path, "w") as f:
            f.write("# notes\n")
        p = sim_process("--roster", path, "players")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertNotIn("PLAYERS", p.stdout)
        self.assertIn(path, p.stdout + p.stderr)

    def test_a_report_that_refuses_says_so_without_a_traceback(self):
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
        name = sorted(sim.ROSTER_FREE)[0]
        was = reports.REPORTS[name]
        reports.REPORTS[name] = lambda: statistics.mean([])
        try:
            with self.assertRaises(statistics.StatisticsError):
                cli(name)
        finally:
            reports.REPORTS[name] = was

    def test_help_describes_every_report_without_running_one(self):
        p = sim_process("--help")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertNotIn("=" * 72, p.stdout, "--help ran a report")
        for name in sim.REPORTS:
            self.assertIn(name, p.stdout)
            self.assertIn(sim.BLURB[name], p.stdout)

    def test_help_says_which_reports_refuse_a_counterparty_roster(self):
        p = sim_process("--help")
        for name in sim.OURS_ONLY:
            self.assertRegex(p.stdout, r"%s.*\(ours only\)" % name)

    def test_a_slow_report_names_itself_before_it_finishes(self):
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
        status, out = cli("--roster", THEIR_ROSTER, "players", "positions")
        self.assertEqual(status, 0, out)
        heads = [l for l in out.splitlines()
                 if l.startswith(("PLAYERS", "POSITIONS"))]
        self.assertEqual(len(heads), 2, out)
        for head in heads:
            self.assertIn(THEIR_ROSTER, head)

    def test_a_report_that_reads_no_roster_does_not_claim_one(self):
        status, out = cli("--roster", THEIR_ROSTER, "market")
        self.assertEqual(status, 0, out)
        self.assertNotIn(THEIR_ROSTER, out.splitlines()[1])

    def test_the_header_names_the_team_not_just_its_id(self):
        teams = json.loads(read_text(
            os.path.join(sim.DATA_DIR, "teams-%s.json" % fetch_data.SEASON_TAG)))
        status, out = cli("--roster", THEIR_ROSTER, "positions")
        self.assertEqual(status, 0, out)
        self.assertIn(teams[THEIR_ROSTER.split("-")[1]], out.splitlines()[1])

    def test_every_report_named_in_one_run_prints(self):
        status, out = cli("nights", "formula")
        self.assertEqual(status, 0, out)
        self.assertIn("NIGHTS", out)
        self.assertIn("FORMULA", out)

    def test_the_directory_runner_says_how_to_invoke_each_thing_in_here(self):
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
        p = subprocess.run(["./run", "sim.py", "--help"], cwd=sim.HERE,
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(sorted(re.findall(r"^  (\w[\w-]*) ", p.stdout, re.M)),
                         sorted(sim.REPORTS))

class EveryReportRunsEndToEnd(unittest.TestCase):
    def test_every_report_runs_on_our_roster(self):
        for name in sorted(sim.REPORTS):
            with self.subTest(report=name):
                self.assertTrue(render(name).strip(), "printed nothing")

    def test_every_report_not_scoped_to_us_runs_on_a_counterparty_roster(self):
        for name in sorted(set(sim.REPORTS) - sim.OURS_ONLY):
            with self.subTest(report=name):
                self.assertTrue(render(name, THEIR_ROSTER).strip(),
                                "printed nothing")
