import unittest
from tests.harness import *

class Durability(unittest.TestCase):
    def test_value_is_proportional_to_games_played(self):
        full = sim.our_roster() + sim.EXPANSION
        trials = 200

        def pf(gp):
            roster = [sim.star(45, gp) if p["n"] == "Jalen Suggs" else p for p in full]
            return sim.run(roster, trials=trials)["pf"]

        absent, healthy = pf(0), pf(82)
        for gp in (41, 62):
            retained = (pf(gp) - absent) / (healthy - absent)
            self.assertAlmostEqual(retained, gp / 82, delta=0.02)

class BackfillGrade(unittest.TestCase):
    def test_the_grade_scenarios_cites_is_a_row_breakevens_actually_reports(self):
        cited, = re.findall(r"bracket to a (\S+) refund", render("scenarios"))
        rows = [l.split()[0] for l in render("breakevens").splitlines() if l.split()]
        self.assertIn(cited, rows)

    def test_the_refund_bracket_names_both_grades_and_our_worst_kept_body(self):
        line, = [l for l in render("breakevens").splitlines()
                 if l.startswith("BACKFILL GRADE")]
        self.assertIn(deals.grade(deals.DEAD), line)
        self.assertIn(deals.grade(deals.GENEROUS), line)
        self.assertIn("%.1f" % min(p["avg"] for p in sim.our_roster()), line)

class ScenarioShapes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.head = render("scenarios").split("scenario ")[0]

    def test_the_center_rows_are_not_described_as_the_default_forward(self):
        self.assertRegex(self.head, r"Jokic[\s\S]*?65-GP C\b")

    def test_the_multi_body_rows_say_they_are_not_all_the_default_either(self):
        self.assertIn("76", self.head)

class BottomOfRoster(unittest.TestCase):
    def priced(self):
        buf = io.StringIO()
        with recorded_rosters() as seen, contextlib.redirect_stdout(buf):
            sim.REPORTS["scenarios"]()
        padded = {p["n"] for p in sim.basis()}
        return (buf.getvalue().split("scenario ")[0],
                [padded - set(r) for r in seen])

    def test_every_row_ships_bodies_the_loaded_roster_carries(self):
        _, gone = self.priced()
        ours = {p["n"] for p in sim.our_roster()}
        self.assertIn(3, [len(g) for g in gone])
        for g in gone:
            self.assertEqual(g - ours, set())

    def test_the_header_names_the_three_bodies_the_row_priced(self):
        head, gone = self.priced()
        named = {p["n"] for p in sim.our_roster() if p["n"] in one_line(head)}
        self.assertEqual(len(named), 3, head)
        self.assertIn(named, [g for g in gone if len(g) == 3])

    def test_a_typed_ladder_name_that_left_says_which_list_to_retype(self):
        self.addCleanup(setattr, deals, "FILLER", deals.FILLER)
        deals.FILLER = deals.FILLER[:2] + ["Traded Away"]
        with self.assertRaises(KeyError) as e, \
                contextlib.redirect_stdout(io.StringIO()):
            sim.REPORTS["scenarios"]()
        self.assertEqual(
            e.exception.args[0],
            "Traded Away: not on the roster as loaded. FILLER and DREGS are "
            "typed by hand in `simlib/reports/deals.py` -- retype the ladder "
            "around the trade you are pricing now (the bottom-up row derives "
            "its own three).")

class LockIn(unittest.TestCase):
    def test_the_bound_is_the_worst_share_the_table_above_it_prints(self):
        out = render("durability")
        rows = [l for l in out.splitlines()
                if re.match(r"^ +\d+ +[-+][\d.]+ +[-+][\d.]+ +\d+%", l)]
        self.assertTrue(rows, out)
        worst = max(int(p) for l in rows for p in re.findall(r"(\d+)%", l))
        bound = float(re.search(r"bound: <=([\d.]+)% of value", out).group(1))
        self.assertAlmostEqual(bound, worst, delta=1.0)

class DurabilityHeader(unittest.TestCase):
    def test_the_gp_row_quotes_the_subject_as_the_roster_carries_him(self):
        sub, = [p for p in sim.basis() if p["n"] == durability.SUBJECT]
        self.assertIn("%s (%.1f @ %d)"
                      % (durability.SUBJECT, sub["avg"], sub["gp"]),
                      render("durability"))

class UnsignedPlayer(unittest.TestCase):
    def test_an_unsigned_body_scores_what_he_would_on_the_assumed_schedule(self):
        base = sim.basis()
        free = {"n": "FREE", "tm": "FA", "avg": 30.0, "tot": 0.0, "gp": 70,
                "posLabel": "F", "elig": ["SF", "PF"]}
        unsigned = sim.run(base + [free], trials=8)["pf"]
        self.assertEqual(unsigned, sim.run(base + [dict(free, tm=sim.SIM_TM)],
                                           trials=8)["pf"])
        self.assertGreater(unsigned,
                           sim.run(base, trials=8)["pf"] + 300)

    def test_a_team_the_schedule_has_never_heard_of_fails(self):
        base = sim.basis()
        renamed = {"n": "RENAMED", "tm": "PHO", "avg": 30.0, "tot": 0.0,
                   "gp": 70, "posLabel": "F", "elig": ["SF", "PF"]}
        with self.assertRaises(KeyError) as e:
            sim.run(base + [renamed], trials=1)
        self.assertIn("PHO", str(e.exception))

    def test_the_players_table_says_the_schedule_is_assumed(self):
        path = roster_file({"n": "Bradley Beal", "tm": "FA", "avg": 24.0,
                            "tot": 1000.0, "gp": 42, "posLabel": "G",
                            "elig": ["PG", "SG"]},
                           {"n": "Desmond Bane", "tm": "MEM", "avg": 33.0,
                            "tot": 2706.0, "gp": 82, "posLabel": "G",
                            "elig": ["PG", "SG"]})
        out = render("players", path)
        beal, = [l for l in out.splitlines() if "Bradley Beal" in l]
        bane, = [l for l in out.splitlines() if "Desmond Bane" in l]
        self.assertIn("fa", beal.split())
        self.assertNotIn("fa", bane.split())
