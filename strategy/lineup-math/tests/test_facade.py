import unittest
from tests.harness import *

class Facade(unittest.TestCase):
    def test_setting_the_roster_on_the_facade_reaches_basis(self):
        self.addCleanup(setattr, roster_mod, "ROSTER", roster_mod.ROSTER)
        sim.ROSTER = THEIR_ROSTER
        self.assertEqual([p["n"] for p in sim.basis()],
                         [p["n"] for p in sim.basis(THEIR_ROSTER)])

    def test_setting_a_name_the_facade_only_re_exports_fails(self):
        was = sim.SLOTS
        with self.assertRaises(AttributeError) as e:
            sim.SLOTS = []
        self.assertIs(sim.SLOTS, was)
        self.assertIn("simlib", str(e.exception))

    def test_a_name_the_facade_never_exported_is_settable_more_than_once(self):
        sim.scratch = 1
        self.addCleanup(delattr, sim, "scratch")
        sim.scratch = 2
        self.assertEqual(sim.scratch, 2)

    def test_replacing_run_on_the_facade_reaches_simlib(self):
        real = engine.run
        self.addCleanup(setattr, engine, "run", real)
        seen = []
        sim.run = lambda roster, **kw: (seen.append(len(roster))
                                        or real(roster, **dict(kw, trials=2)))
        R = flat_R()
        sim.player_wins(sim.basis(), ["Jalen Suggs"], blocks=1, trials=2, R=R)
        self.assertTrue(seen)

    def test_a_star_import_carries_the_five_live_names_and_not_the_plumbing(self):
        ns = {}
        exec("from sim import *", ns)
        starred = set(ns) - {"__builtins__"}
        self.assertLessEqual({"run", "player_wins", "gp_bootstrap",
                              "PLAYER_BLOCKS", "ROSTER", "basis"}, starred)
        self.assertIs(ns["run"], engine.run)
        self.assertEqual(starred & {"sys", "types", "roster", "value"}, set())

    def test_no_name_is_re_exported_from_two_simlib_modules(self):
        seen = collections.defaultdict(list)
        tree = ast.parse(read_text(os.path.join(sim.HERE, "sim.py")))
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                for a in node.names:
                    seen[a.asname or a.name].append(node.module)
        self.assertEqual(
            {n: m for n, m in seen.items() if len(m) > 1}, {},
            "one name, two modules: rename one of them in `simlib`")

class PlayerBlocksIsOneConstant(unittest.TestCase):
    def test_player_wins_takes_its_block_count_from_the_constant(self):
        self.addCleanup(setattr, value, "PLAYER_BLOCKS", value.PLAYER_BLOCKS)
        value.PLAYER_BLOCKS = 2
        R = flat_R()
        w = sim.player_wins(sim.basis(), ["Jalen Suggs"], trials=2, R=R)
        self.assertEqual(len(w["Jalen Suggs"][2]), 2)

    def test_incoming_wins_takes_the_same_one(self):
        self.addCleanup(setattr, value, "PLAYER_BLOCKS", value.PLAYER_BLOCKS)
        value.PLAYER_BLOCKS = 2
        R = flat_R()
        body = sim.star(40.0, 68, ("C",), n="INCOMING")
        w = sim.incoming_wins(sim.basis(), [body], trials=2, R=R)
        self.assertEqual(len(w["INCOMING"][2]), 2)
