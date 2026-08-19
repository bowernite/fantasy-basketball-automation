import unittest
from tests.harness import *

class Facade(unittest.TestCase):
    """`sim` re-exports, and five names are state a caller REPLACES. A module
    `__getattr__` fires only when normal lookup FAILS, so an assignment on the
    facade creates the very entry that stops it failing, and the write reads
    back fine while reaching nobody inside `simlib`. Reads fixed and writes not
    is the silent-wrong-number shape, pointed the other way"""

    def test_setting_the_roster_on_the_facade_reaches_basis(self):
        self.addCleanup(setattr, roster_mod, "ROSTER", roster_mod.ROSTER)
        sim.ROSTER = THEIR_ROSTER
        self.assertEqual([p["n"] for p in sim.basis()],
                         [p["n"] for p in sim.basis(THEIR_ROSTER)])

    def test_setting_a_name_the_facade_only_re_exports_fails(self):
        """Five names are live state, and the facade re-exports a hundred more,
        every one of them bound here as a reference. An assignment to one of
        those lands in the facade's own dict, reads back the caller's value and
        leaves every reader inside `simlib` on the real one"""
        was = sim.SLOTS
        with self.assertRaises(AttributeError) as e:
            sim.SLOTS = []
        self.assertIs(sim.SLOTS, was)
        self.assertIn("simlib", str(e.exception))

    def test_a_name_the_facade_never_exported_is_settable_more_than_once(self):
        """`ModuleType.__setattr__` writes into the same module dict the
        refusal above asks about, so a name `simlib` has never heard of is
        accepted once and the second assignment comes back "re-exported from
        simlib, not owned here" about it. A guard that mis-states what it is
        guarding sends the reader looking for a `simlib` name that does not
        exist"""
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
        """`from sim import *` is what a REPL and a saved snippet do. It copies
        the module DICT, and the five live names are in nobody's dict, they are
        served by `__getattr__`, so `run`, the first line of the documented
        import path, comes out of a star import as a NameError.

        The same dict is why the star can hand back `sys`, `types` and four
        `simlib` module handles, rebinding whatever the caller already had
        under those names"""
        ns = {}
        exec("from sim import *", ns)
        starred = set(ns) - {"__builtins__"}
        self.assertLessEqual({"run", "player_wins", "gp_bootstrap",
                              "PLAYER_BLOCKS", "ROSTER", "basis"}, starred)
        self.assertIs(ns["run"], engine.run)
        self.assertEqual(starred & {"sys", "types", "roster", "value"}, set())

    def test_no_name_is_re_exported_from_two_simlib_modules(self):
        """A hundred-odd names off a dozen modules land in one namespace, and
        the second import of a name silently wins. `SEASONS` arrived that way:
        `gp`'s list of GP seasons and a Monte Carlo trial count, so
        `sim.SEASONS` handed back an int to every caller expecting the list --
        and both modules kept reading their own, so nothing raised"""
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
    """`players` prints "averaged over N independent seed blocks" off the
    constant, while `player_wins`, the import path a deal is actually priced
    on, is what runs them. Move the constant and the printed caveat describes a
    measurement nobody ran, on the table `eval-team` quotes"""

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
