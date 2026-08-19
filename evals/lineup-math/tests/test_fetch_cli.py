import unittest
from tests.harness import *
from tests.fetch_stub import *

class FetchDataCLI(unittest.TestCase):
    """The other half of the command surface. It WRITES the files every report
    reads, so its failure modes are quieter and cost more"""

    def fetch(self, *args):
        return subprocess.run([sys.executable, "fetch_data.py"] + list(args),
                              cwd=sim.HERE, capture_output=True, text=True,
                              timeout=30)

    def test_an_unrecognised_argument_refuses_instead_of_re_scraping(self):
        """`rosters` (plural), `players`, a bare team id -- each fell through to
        the default branch, spent 30 requests overwriting the schedule and the
        calendar, printed `wrote ...` and exited 0"""
        before = {p: os.path.getmtime(p)
                  for p in glob.glob(os.path.join(sim.HERE, "*.json"))}
        p = self.fetch("rosters")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("wrote", p.stdout)
        self.assertEqual({q: os.path.getmtime(q) for q in before}, before)

    def test_a_non_numeric_team_id_is_caught_before_any_request(self):
        """`int(t)` raised only after a league call had been made and a roster
        file already truncated"""
        p = self.fetch("roster", "brett")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("brett", p.stdout + p.stderr)

    def test_help_names_every_thing_it_can_be_asked_for(self):
        p = self.fetch("--help")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        for word in ("pool", "roster", "teams"):
            self.assertIn(word, p.stdout)

class DataFileWrites(unittest.TestCase):
    """One function lands every file `sim.py` reads, and none of them is
    re-fetchable at will: the pool is a 20-minute scrape and the season it
    describes is over"""

    def test_a_rebuild_that_dies_mid_scrape_leaves_the_good_file_alone(self):
        """Opening the path for writing AROUND the build truncated it first, so
        a transport error left a zero-byte `league-<season>.json` where the
        season was, and every `sim.py` run after it died on a JSON decode error
        naming nothing that had happened"""
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "league-x.json"), "w") as f:
            f.write('{"periods": [1, 2, 3]}')

        def transport_error():
            raise RuntimeError("connection reset by peer")

        was = fetch_data.HERE
        fetch_data.HERE = d
        try:
            with self.assertRaises(RuntimeError):
                fetch_data.write("league-x.json", transport_error)
        finally:
            fetch_data.HERE = was
        self.assertEqual(read_text(os.path.join(d, "league-x.json")),
                         '{"periods": [1, 2, 3]}')
        self.assertEqual(os.listdir(d), ["league-x.json"],
                         "a half-written file was left behind to be read next")

class FetchDataWritesWhatSimReads(unittest.TestCase):
    """`fetch_data.py roster` is the sole writer of the twelve files every
    counterparty table is priced off, and of the id -> name map that labels
    them. Driven against a canned league so the files it lands can be read
    back, which is the only thing that shows the fetch and the sim agree on a
    schema"""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        shutil.copy(fetch_data.__file__, self.dir)
        shutil.copy(os.path.join(os.path.dirname(fetch_data.__file__),
                                 "assumed_trades.py"), self.dir)
        with open(os.path.join(self.dir, "stub_fleaflicker.py"), "w") as f:
            f.write(STUB_FLEAFLICKER)
        self.ids = [161001 + i for i in range(12)]
        bodies = {t: [pro_player("Starter %d" % t, t * 10),
                      pro_player("Bench %d" % t, t * 10 + 1, "HOU", "C", ("C",))]
                  for t in self.ids}
        with open(os.path.join(self.dir, "feed.json"), "w") as f:
            json.dump({"league": league_payload(*sorted(bodies.items())),
                       "snapshots": {str(t): snapshot_payload(
                           (bodies[t][0], 30.0, 1500.0), (bodies[t][1], 10.0, 400.0))
                           for t in self.ids}}, f)

    def fetch(self, *args):
        return subprocess.run(
            [sys.executable, "stub_fleaflicker.py"] + list(args),
            cwd=self.dir, capture_output=True, text=True, timeout=60)

    def rosters(self):
        return sorted(f for f in os.listdir(self.dir) if f.startswith("roster-"))

    def test_naming_no_team_re_cuts_all_twelve(self):
        """They drift independently, so a team left un-recut is a team priced
        off whoever owned him in March -- which is how four went stale"""
        p = self.fetch("roster")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.rosters(),
                         sorted("roster-%d-%s.json" % (t, fetch_data.SEASON_TAG)
                                for t in self.ids))

    def test_the_rows_it_lands_are_the_rows_sim_prices(self):
        """The schema is this file's to state and `--roster` is the only reader
        of it, so a key renamed on either side shows up nowhere else"""
        self.assertEqual(self.fetch("roster", "161001").returncode, 0)
        rows = json.loads(read_text(os.path.join(
            self.dir, "roster-161001-%s.json" % fetch_data.SEASON_TAG)))
        self.assertEqual(rows, [
            {"n": "Starter 161001", "tm": "LAC", "avg": 30.0, "tot": 1500.0,
             "gp": 50, "posLabel": "G", "elig": ["PG", "SG"]},
            {"n": "Bench 161001", "tm": "HOU", "avg": 10.0, "tot": 400.0,
             "gp": 40, "posLabel": "C", "elig": ["C"]}])

    def test_asking_for_one_team_still_writes_all_twelve_labels(self):
        """The labels cost nothing extra, and a partial map makes the header of
        one report inconsistent with the next"""
        self.assertEqual(self.fetch("roster", "161001").returncode, 0)
        teams = json.loads(read_text(os.path.join(
            self.dir, "teams-%s.json" % fetch_data.SEASON_TAG)))
        self.assertEqual(teams, {str(t): "Team %d" % t for t in self.ids})

    def test_a_team_id_the_league_lacks_stops_the_run_before_any_roster(self):
        """Re-cutting eleven and dying on the twelfth leaves the directory half
        stale, and nothing downstream can tell which half"""
        p = self.fetch("roster", "161001", "999999")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("999999", p.stdout + p.stderr)
        self.assertEqual(self.rosters(), [])

    def test_the_file_it_says_it_wrote_is_the_file_it_wrote(self):
        """`wrote teams-2025-26.json` says nothing about where, and the answer
        is never the directory the caller is standing in"""
        p = self.fetch("teams")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        wrote = [os.path.realpath(l.split(None, 1)[1])
                 for l in p.stdout.splitlines() if l.startswith("wrote ")]
        self.assertEqual(wrote, [os.path.realpath(os.path.join(
            self.dir, "teams-%s.json" % fetch_data.SEASON_TAG))])
        self.assertTrue(os.path.exists(wrote[0]))
        self.assertEqual(self.rosters(), [], "`teams` re-cut a roster")
