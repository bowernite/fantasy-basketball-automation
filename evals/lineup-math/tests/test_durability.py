import unittest
from tests.harness import *

class Durability(unittest.TestCase):
    """Characterisation test rather than a red to green cycle. It pins the
    conclusion the README's durability section rests on, that with
    foreknowledge of who plays GP-elasticity is 1, so the ONLY format-derived
    injury adjustment is the lock-in. If this stops holding, that section has
    to be rewritten"""

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
    """Regression pin rather than a red to green cycle. `scenarios` tells the
    reader that `breakevens` reports the bracket out to one named refund grade,
    which is a cross-table claim otherwise held together by two people typing
    the same pair of numbers into two files' worth of prints"""

    def test_the_grade_scenarios_cites_is_a_row_breakevens_actually_reports(self):
        cited, = re.findall(r"bracket to a (\S+) refund", render("scenarios"))
        rows = [l.split()[0] for l in render("breakevens").splitlines() if l.split()]
        self.assertIn(cited, rows)

class ScenarioShapes(unittest.TestCase):
    """`breakevens` states GP and position on every row "because they move the
    answer several points", and `scenarios` states them once above the table
    for the rows whose labels do not. So that sentence carries the whole
    table's worth of the warning, and a reader who takes a bare label at its
    word compares a real 65-GP center against a row priced as a 68-GP forward
    """

    @classmethod
    def setUpClass(cls):
        cls.head = render("scenarios").split("scenario ")[0]

    def test_the_center_rows_are_not_described_as_the_default_forward(self):
        self.assertRegex(self.head, r"Jokic[\s\S]*?65-GP C\b")

    def test_the_multi_body_rows_say_they_are_not_all_the_default_either(self):
        self.assertIn("76", self.head)

class BottomOfRoster(unittest.TestCase):
    """The ladder's bottom-up row is the one shape nobody can hand-type. Three
    names typed into the report go stale the day one of them is traded, and
    `swap` refuses a name the roster does not carry -- so a row about a body
    that left does not print a wrong number, it takes the whole report down
    with it (`KeyError: not on this roster: DaRon Holmes`)"""

    def priced(self):
        """(everything printed above the table, the bodies each row sent OUT).

        Off the rosters the sim was handed rather than off the labels: which
        bodies a row was priced on is not visible in the number it prints"""
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
        """A derived trio nothing prints is a row a reader cannot check, and
        the trio findings.md quotes beside it is then a caption on a table it
        has stopped describing"""
        head, gone = self.priced()
        named = {p["n"] for p in sim.our_roster() if p["n"] in one_line(head)}
        self.assertEqual(len(named), 3, head)
        self.assertIn(named, [g for g in gone if len(g) == 3])

    def test_a_typed_ladder_name_that_left_says_which_list_to_retype(self):
        """The other two ladders here cannot be derived -- `DREGS` is a
        trade-value judgment the sim holds no data for, and `FILLER` is named
        in the row labels -- so the next departure lands as `swap`'s bare name
        from inside the loop, which does not say that the fix is a retyped list
        in this file"""
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

class DurabilityHeader(unittest.TestCase):
    """The GP row's header names its subject and quotes his line. `our_roster`
    re-projects both the rate and the GP every time the feed moves, so a line
    typed into the header describes whoever the roster carried the day it was
    typed while the row underneath is measured on today's"""

    def test_the_gp_row_quotes_the_subject_as_the_roster_carries_him(self):
        sub, = [p for p in sim.basis() if p["n"] == durability.SUBJECT]
        self.assertIn("%s (%.1f @ %d)"
                      % (durability.SUBJECT, sub["avg"], sub["gp"]),
                      render("durability"))

class UnsignedPlayer(unittest.TestCase):
    """Most committed rosters hold a player unsigned in the NBA, purely because
    the snapshot is taken in July. Given no schedule at all he suits up for
    nothing and prices as most of a body of `Δw` short, a snapshot artifact
    reading as a finding about the player. He is a body with an unknown
    schedule, which is what `SIM_TM` is for"""

    def test_an_unsigned_body_scores_what_he_would_on_the_assumed_schedule(self):
        """The whole claim in the only terms that matter, a season's PF. A
        floor, "he beats an empty slot", passes on a quarter of a schedule, and
        an rng-draw assertion tests the mechanism rather than the season"""
        base = sim.basis()
        free = {"n": "FREE", "tm": "FA", "avg": 30.0, "tot": 0.0, "gp": 70,
                "posLabel": "F", "elig": ["SF", "PF"]}
        unsigned = sim.run(base + [free], trials=8)["pf"]
        self.assertEqual(unsigned, sim.run(base + [dict(free, tm=sim.SIM_TM)],
                                           trials=8)["pf"])
        self.assertGreater(unsigned,
                           sim.run(base, trials=8)["pf"] + 500)

    def test_a_team_the_schedule_has_never_heard_of_fails(self):
        """The other side of the same boundary. "FA" is a fact the feed states,
        "PHO" is the feed having renamed Phoenix out from under the join, and
        inheriting SIM_TM there prices the body on the DEEPEST light-night
        schedule of the 30 while nothing prints an error"""
        base = sim.basis()
        renamed = {"n": "RENAMED", "tm": "PHO", "avg": 30.0, "tot": 0.0,
                   "gp": 70, "posLabel": "F", "elig": ["SF", "PF"]}
        with self.assertRaises(KeyError) as e:
            sim.run(base + [renamed], trials=1)
        self.assertIn("PHO", str(e.exception))

    def test_the_players_table_says_the_schedule_is_assumed(self):
        """`Δw` on an assumed schedule is not the same claim as `Δw` on his
        own, and nothing else on the row distinguishes them"""
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
