import unittest
from tests.harness import *
from simlib import progression as prog
from simlib.board import pool
from simlib.reports import progression as rep


OURS = ["Cade Cunningham", "Cooper Flagg", "Emanuel Sharp"]
THEIRS = ["Naz Reid", "Thomas Sorber"]


def league(extra=()):
    """A two-team league of roster files, so no test rides on live rosters"""
    d = os.path.join(tempfile.mkdtemp(), "rosters")
    os.makedirs(d)
    ours = int(roster_mod.OURS.split("-")[1])
    theirs = next(int(t) for t in rep.owner_names() if int(t) != ours)
    known = rep.newcomers()
    for tid, names in ((ours, OURS + list(extra)), (theirs, THEIRS)):
        rows = [{"n": n, "tm": (pool().get(n) or known.get(rep._key(n)) or {"tm": "SAC"})["tm"],
                 "avg": 0.0, "tot": 0.0, "gp": 0, "posLabel": "G", "elig": ["PG"]} for n in names]
        with open(os.path.join(d, "roster-%d-%s.json" % (tid, fetch_data.SEASON_TAG)), "w") as f:
            json.dump(rows, f)
    return d


def rendered(rosters):
    with mock.patch.object(rep, "ROSTER_DIR", rosters):
        return render("progression")


def placed(rosters):
    with mock.patch.object(rep, "ROSTER_DIR", rosters):
        return {pl["name"]: (owner, pl, flags) for owner, pl, flags in rep.rostered()[0]}


class Report(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rosters = league()
        cls.out = rendered(cls.rosters)
        cls.rows = placed(cls.rosters)

    def test_every_player_in_every_roster_file_gets_one_row_under_his_owner(self):
        owners = rep.owner_names()
        us = owners[roster_mod.OURS.split("-")[1]]
        got = {name: line.split() for name, line in table_rows(self.out)}
        self.assertEqual(sorted(OURS + THEIRS), sorted(got))
        for name in OURS:
            self.assertIn(us, got[name])

    def test_a_drafted_rookie_with_no_nba_season_is_a_draftee_at_his_nba_pick(self):
        self.assertEqual(("D", 45), (self.rows["Emanuel Sharp"][1]["stage"], self.rows["Emanuel Sharp"][1]["pick"]))
        self.assertEqual(("D", 15), (self.rows["Thomas Sorber"][1]["stage"], self.rows["Thomas Sorber"][1]["pick"]))

    def test_a_player_with_one_nba_season_done_is_in_his_second_career_year(self):
        pl = self.rows["Cooper Flagg"][1]
        self.assertEqual(("S", 2), (pl["stage"], pl["cy1"]))

    def test_a_top_five_pick_carries_the_flag_for_his_known_over_projection(self):
        self.assertIn("top5", self.rows["Cooper Flagg"][2])
        self.assertNotIn("top5", self.rows["Emanuel Sharp"][2])

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
            owner, pl, flags = placed(self.rosters)["Naz Reid"]
        self.assertEqual("V", pl["stage"])
        self.assertIn("noBBRef", flags)

    def test_a_major_injury_in_the_file_marks_him_and_cuts_his_later_seasons_only(self):
        path = os.path.join(tempfile.mkdtemp(), "injury.json")
        with open(path, "w") as f:
            json.dump({"players": {"Cade Cunningham": {"rate_mult": 0.8,
                                                       "reason": "torn Achilles"}}}, f)
        before = dict(table_rows(self.out))["Cade Cunningham"]
        with mock.patch.object(rep, "INJURY", path):
            after = dict(table_rows(rendered(self.rosters)))["Cade Cunningham"]
        self.assertIn("inj x0.80", after)
        self.assertEqual(before.split()[5:8], after.split()[5:8])   # year 1 as projected
        self.assertLess(float(after.split()[8]), float(before.split()[8]) * 0.9)

    def test_the_legend_states_the_weighting_the_twenty_year_value_uses(self):
        self.assertIn("0.95", self.out)
        self.assertIn("WRV", self.out)

    def test_one_players_view_carries_the_tables_limits(self):
        out = io.StringIO()
        with mock.patch.object(rep, "ROSTER_DIR", self.rosters), mock.patch.object(rep, "PATHS", 200), \
                contextlib.redirect_stdout(out):
            rep.detail(["Naz Reid"])
        self.assertIn(rep.LIMITS, out.getvalue())
        self.assertIn(rep.LIMITS, self.out)


class BoardResidual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        universe = rep.board_universe()
        cls.scored = [(pl, b) for pl, b in zip(universe, rep.board_residuals(universe)) if b is not None]

    def test_the_twenty_best_producers_are_not_read_as_board_loved_just_for_being_the_best(self):
        top = sorted(self.scored, key=lambda x: -x[0]["rate1"])[:20]
        self.assertLess(abs(sum(b for _, b in top) / len(top)), 0.2)

    def test_among_the_best_producers_the_residual_does_not_track_age(self):
        stars = [(pl["age1"], b) for pl, b in self.scored if pl["rate1"] >= 34]
        self.assertLess(abs(statistics.correlation(*zip(*stars))), 0.15)

    def test_the_residual_runs_on_the_scale_its_nudge_was_measured_on(self):
        sd = statistics.pstdev(b for _, b in self.scored)
        self.assertAlmostEqual(sd, prog.params()["board"]["sd"], delta=0.05)


    def test_a_players_board_residual_does_not_move_when_another_team_leaves_the_league(self):
        rosters = league()
        before = placed(rosters)["Cade Cunningham"][1]["bres"]
        os.remove(next(p for p in glob.glob(os.path.join(rosters, "*.json")) if roster_mod.OURS not in p))
        self.assertEqual(before, placed(rosters)["Cade Cunningham"][1]["bres"])


class NoBirthday(unittest.TestCase):
    def test_a_rostered_player_with_no_birthday_anywhere_keeps_a_flagged_row_with_no_projection(self):
        out = dict(table_rows(rendered(league(extra=["Nobody Known"]))))
        self.assertEqual(len(OURS + THEIRS) + 1, len(out))
        self.assertEqual("noDOB", out["Nobody Known"].split()[-1])


def table_rows(out):
    """(player, line) per table row, in print order"""
    head = out.splitlines().index(next(line for line in out.splitlines()
                                       if line.startswith("  player ")))
    return [(line[2:].split("  ")[0].strip(), line) for line in out.splitlines()[head + 1:]
            if line.startswith("  ")]


class Freeze(unittest.TestCase):
    def test_a_preseason_is_archived_once_with_its_inputs_and_every_players_path(self):
        root = tempfile.mkdtemp()
        with mock.patch.object(rep, "ARCHIVE", root), mock.patch.object(rep, "PATHS", 200), \
                mock.patch.object(rep, "ROSTER_DIR", league()), contextlib.redirect_stdout(io.StringIO()):
            rep.freeze()
            with self.assertRaises(SystemExit):
                rep.freeze()
        dest = os.path.join(root, "%s-preseason" % fetch_data.LIVE_TAG)
        self.assertIn("sleeper-%d.json" % fetch_data.LIVE_SEASON, os.listdir(dest))
        with open(os.path.join(dest, "progression.json")) as f:
            frozen = {r["player"]["name"]: r for r in json.load(f)}
        self.assertEqual(len(frozen["Cade Cunningham"]["years"]), rep.YEARS)
