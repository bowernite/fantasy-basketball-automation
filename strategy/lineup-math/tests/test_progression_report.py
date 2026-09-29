import unittest
from tests.harness import *
from simlib.reports import progression as rep


class Report(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = render("progression")

    def test_every_rostered_player_and_held_draftee_gets_a_row_under_his_owner(self):
        ours = [p["n"] for p in sim.our_roster()]
        drafted = [p["name"] for p in roster_mod.held_picks(roster_mod.OURS)]
        rows = {line[2:].split("  ")[0].strip(): line for line in self.out.splitlines()
                if line.startswith("  ")}
        for name in ours + drafted:
            self.assertIn(name, rows)
            self.assertIn("Brett", rows[name])

    def test_the_legend_states_the_weighting_the_twenty_year_value_uses(self):
        self.assertIn("0.95", self.out)
        self.assertIn("WRV", self.out)


def cade_row(out):
    return next(line for line in out.splitlines() if line.startswith("  Cade Cunningham "))


class InjuryOverride(unittest.TestCase):
    def test_a_major_injury_in_the_file_marks_him_and_cuts_his_later_seasons_only(self):
        path = os.path.join(tempfile.mkdtemp(), "injury.json")
        with open(path, "w") as f:
            json.dump({"players": {"Cade Cunningham": {"rate_mult": 0.8,
                                                       "reason": "torn Achilles"}}}, f)
        before = cade_row(render("progression"))
        with mock.patch.object(rep, "INJURY", path):
            after = cade_row(render("progression"))
        self.assertIn("inj x0.80", after)
        self.assertEqual(before.split()[5:8], after.split()[5:8])   # year 1 as projected
        self.assertLess(float(after.split()[8]), float(before.split()[8]) * 0.9)


class Freeze(unittest.TestCase):
    def test_a_preseason_is_archived_once_with_its_inputs_and_every_players_path(self):
        root = tempfile.mkdtemp()
        with mock.patch.object(rep, "ARCHIVE", root), \
                contextlib.redirect_stdout(io.StringIO()):
            rep.freeze()
            with self.assertRaises(SystemExit):
                rep.freeze()
        dest = os.path.join(root, "%s-preseason" % fetch_data.LIVE_TAG)
        self.assertIn("sleeper-%d.json" % fetch_data.LIVE_SEASON, os.listdir(dest))
        with open(os.path.join(dest, "progression.json")) as f:
            frozen = {r["player"]["name"]: r for r in json.load(f)}
        self.assertEqual(len(frozen["Cade Cunningham"]["years"]), rep.YEARS)
