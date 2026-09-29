import unittest
from tests.harness import *
from simlib.reports import progression as rep


class Report(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = render("progression")

    def test_every_player_in_every_roster_file_gets_one_row_under_his_owner(self):
        owners = rep.owner_names()
        expected = []
        for path in glob.glob(os.path.join(sim.HERE, "rosters", "roster-*.json")):
            with open(path) as f:
                expected += [(r["n"], owners[path.split("roster-")[1].split("-")[0]])
                             for r in json.load(f)]
        got = [(name, line[28:35].strip()) for name, line in table_rows(self.out)]
        self.assertEqual(sorted(expected), sorted(got))

    def test_a_drafted_rookie_with_no_nba_season_is_a_draftee_at_his_nba_pick(self):
        rows = {pl["name"]: pl for _, pl, _ in rep.rostered()[0]}
        self.assertEqual(("D", 45), (rows["Emanuel Sharp"]["stage"], rows["Emanuel Sharp"]["pick"]))
        self.assertEqual(("D", 15), (rows["Thomas Sorber"]["stage"], rows["Thomas Sorber"]["pick"]))

    def test_a_tenth_pick_the_rookie_tab_writes_as_1_1_is_pick_ten(self):
        self.assertEqual(10, rep.newcomers()[rep._key("Brayden Burries")]["pick"])
        self.assertEqual(20, rep.newcomers()[rep._key("Jayden Quaintance")]["pick"])

    def test_a_pool_player_the_bbref_file_lacks_is_flagged_not_taken_for_a_draftee(self):
        bb = os.path.join(tempfile.mkdtemp(), "bbref.json")
        with open(os.path.join(sim.HERE, "data", rep.BBREF)) as f:
            rows = json.load(f)
        del rows["Naz Reid"]
        with open(bb, "w") as f:
            json.dump(rows, f)
        with mock.patch.object(rep, "BBREF", bb):
            owner, pl, flags = next(r for r in rep.rostered()[0] if r[1]["name"] == "Naz Reid")
        self.assertEqual("V", pl["stage"])
        self.assertIn("noBBRef", flags)

    def test_a_major_injury_in_the_file_marks_him_and_cuts_his_later_seasons_only(self):
        path = os.path.join(tempfile.mkdtemp(), "injury.json")
        with open(path, "w") as f:
            json.dump({"players": {"Cade Cunningham": {"rate_mult": 0.8,
                                                       "reason": "torn Achilles"}}}, f)
        before = cade_row(self.out)
        with mock.patch.object(rep, "INJURY", path):
            after = cade_row(render("progression"))
        self.assertIn("inj x0.80", after)
        self.assertEqual(before.split()[5:8], after.split()[5:8])   # year 1 as projected
        self.assertLess(float(after.split()[8]), float(before.split()[8]) * 0.9)

    def test_the_legend_states_the_weighting_the_twenty_year_value_uses(self):
        self.assertIn("0.95", self.out)
        self.assertIn("WRV", self.out)


class BoardResidual(unittest.TestCase):
    def test_the_twenty_best_producers_are_not_read_as_board_loved_just_for_being_the_best(self):
        players = [pl for _, pl, _ in rep.rostered()[0] if pl.get("bres") is not None]
        top = sorted(players, key=lambda pl: -pl["rate1"])[:20]
        self.assertLess(abs(sum(pl["bres"] for pl in top) / len(top)), 0.2)


    def test_a_players_board_residual_does_not_move_when_another_team_leaves_the_league(self):
        before = {pl["name"]: pl["bres"] for o, pl, _ in rep.rostered()[0] if o == "Brett"}
        rosters = os.path.join(tempfile.mkdtemp(), "rosters")
        shutil.copytree(os.path.join(sim.HERE, "rosters"), rosters)
        for path in glob.glob(os.path.join(rosters, "roster-*.json")):
            if roster_mod.OURS not in path:
                os.remove(path)
        with mock.patch.object(rep, "ROSTER_DIR", rosters):
            after = {pl["name"]: pl["bres"] for o, pl, _ in rep.rostered()[0]}
        self.assertEqual(before, after)


class NoBirthday(unittest.TestCase):
    def test_a_rostered_player_with_no_birthday_anywhere_keeps_a_flagged_row_with_no_projection(self):
        rosters = os.path.join(tempfile.mkdtemp(), "rosters")
        shutil.copytree(os.path.join(sim.HERE, "rosters"), rosters)
        ours = os.path.join(rosters, roster_mod.OURS)
        with open(ours) as f:
            rows = json.load(f) + [{"n": "Nobody Known", "tm": "SAC", "avg": 0.0, "tot": 0.0,
                                    "gp": 0, "posLabel": "G", "elig": ["PG"]}]
        with open(ours, "w") as f:
            json.dump(rows, f)
        with mock.patch.object(rep, "ROSTER_DIR", rosters):
            out = dict(table_rows(render("progression")))
        self.assertEqual(len(rows), len([line for line in out.values() if "Brett" in line]))
        self.assertEqual(["Nobody", "Known", "Brett", "-", "noDOB"], out["Nobody Known"].split())


def table_rows(out):
    """(player, line) per table row, in print order"""
    head = out.splitlines().index(next(line for line in out.splitlines()
                                       if line.startswith("  player ")))
    return [(line[2:].split("  ")[0].strip(), line) for line in out.splitlines()[head + 1:]
            if line.startswith("  ")]


def cade_row(out):
    return next(line for line in out.splitlines() if line.startswith("  Cade Cunningham "))


class Freeze(unittest.TestCase):
    def test_a_preseason_is_archived_once_with_its_inputs_and_every_players_path(self):
        root = tempfile.mkdtemp()
        with mock.patch.object(rep, "ARCHIVE", root), mock.patch.object(rep, "PATHS", 200), \
                contextlib.redirect_stdout(io.StringIO()):
            rep.freeze()
            with self.assertRaises(SystemExit):
                rep.freeze()
        dest = os.path.join(root, "%s-preseason" % fetch_data.LIVE_TAG)
        self.assertIn("sleeper-%d.json" % fetch_data.LIVE_SEASON, os.listdir(dest))
        with open(os.path.join(dest, "progression.json")) as f:
            frozen = {r["player"]["name"]: r for r in json.load(f)}
        self.assertEqual(len(frozen["Cade Cunningham"]["years"]), rep.YEARS)
