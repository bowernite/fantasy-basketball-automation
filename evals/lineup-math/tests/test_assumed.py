import unittest
from tests.harness import *
from tests.fetch_stub import *

class AssumedTradesOverlay(unittest.TestCase):
    """Pending / handshake deals are treated as done on the roster files.
    A re-fetch that skipped this would price Amen on us and Hunter on Henry."""

    def test_moves_and_the_drop_and_a_second_pass_is_a_noop(self):
        import assumed_trades as at
        hunter = {"n": "De'Andre Hunter", "tm": "SAC"}
        holmes = {"n": "DaRon Holmes", "tm": "DEN"}
        amen = {"n": "Amen Thompson", "tm": "HOU"}
        murray = {"n": "Keegan Murray", "tm": "SAC"}
        nnaji = {"n": "Zeke Nnaji", "tm": "DEN"}
        cade = {"n": "Cade Cunningham", "tm": "DET"}
        wemby = {"n": "Victor Wembanyama", "tm": "SAS"}
        rest = [{"n": n, "tm": "FA"} for n in (
            "Shaedon Sharpe", "Tari Eason", "Devin Vassell", "Jonathan Kuminga")]
        rosters = {
            at.US: [cade, amen, holmes],
            at.HENRY: [hunter, nnaji],
            at.MATTHEW: [wemby, murray] + rest,
        }
        self.assertEqual(at.apply_all(rosters), 3)
        us = {r["n"] for r in rosters[at.US]}
        self.assertEqual(us, {"Cade Cunningham", "De'Andre Hunter",
                              "Keegan Murray", "Shaedon Sharpe", "Tari Eason",
                              "Devin Vassell", "Jonathan Kuminga"})
        self.assertEqual({r["n"] for r in rosters[at.HENRY]}, {"DaRon Holmes"})
        self.assertEqual({r["n"] for r in rosters[at.MATTHEW]},
                         {"Victor Wembanyama", "Amen Thompson"})
        self.assertEqual(at.apply_all(rosters), 0)

    def test_a_team_outside_the_deals_does_not_pull_the_other_sides(self):
        import assumed_trades as at
        self.assertEqual(at.expand_ids([161016]), [161016])
        self.assertEqual(set(at.expand_ids([at.US])), at.INVOLVED)

    def test_a_drop_only_empties_the_roster_it_was_dropped_from(self):
        """A drop is one team releasing one body, and the row says which team.
        Applied league-wide it matches on NAME alone -- and this league has
        carried two Jaylin Williamses, so the other team loses a player it
        still owns and the overlay is the only thing that could say so"""
        import assumed_trades as at
        name, src = at.DROPS[0]
        other = min(t for t in at.INVOLVED if t != src)
        rosters = {src: [{"n": name, "tm": "DEN"}],
                   other: [{"n": name, "tm": "PHX"}]}
        at.apply_all(rosters)
        self.assertEqual(rosters[src], [])
        self.assertEqual([r["tm"] for r in rosters[other]], ["PHX"])

    def test_a_moved_body_a_third_team_still_holds_is_refused(self):
        """`expand_ids` re-cuts every side so the files cannot double-own a
        body, and this is the only place that can keep that promise: an
        incoming name is resolved across the whole league, so a deal whose
        source no longer holds him copies the row off whoever does -- and that
        team keeps him. Two files then own one body and the sim reads his level
        twice, in a league whose PF is supposed to sum to itself"""
        import assumed_trades as at
        name, src, dst = at.MOVES[0]
        third = min(t for t in at.INVOLVED if t not in (src, dst))
        rosters = {src: [], dst: [], third: [{"n": name, "tm": "DEN"}]}
        with self.assertRaises(ValueError) as e:
            at.apply_all(rosters)
        for bit in (name, str(src), str(third)):
            self.assertIn(bit, str(e.exception))
        self.assertEqual([r["n"] for r in rosters[third]], [name])

class AssumedTradesReachTheFilesTheSimPrices(unittest.TestCase):
    """The overlay's only caller is `fetch_data.py roster`, and the files it
    lands are what every counterparty table is then priced off. `apply_all` over
    a dict it was handed cannot see the fetch pick which teams to re-cut, nor
    what reaches disk -- and a deal that is applied to a roster nobody writes is
    a trade the reader was told is already done"""

    def setUp(self):
        import assumed_trades as at
        self.at = at
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        for name in ("fetch_data.py", "assumed_trades.py"):
            shutil.copy(os.path.join(sim.HERE, name), self.dir)
        with open(os.path.join(self.dir, "stub_fleaflicker.py"), "w") as f:
            f.write(STUB_FLEAFLICKER)
        held = collections.defaultdict(list)
        for name, src, _ in at.MOVES:
            held[src].append(name)
        for name, src in at.DROPS:
            held[src].append(name)
        self.ids = sorted(at.INVOLVED) + [
            161101 + i for i in range(12 - len(at.INVOLVED))]
        self.bodies = {
            t: [pro_player(n, 7000 + 50 * i + k) for k, n in
                enumerate(held[t] + ["Keeper %d" % t])]
            for i, t in enumerate(self.ids)}
        with open(os.path.join(self.dir, "feed.json"), "w") as f:
            json.dump({"league": league_payload(*sorted(self.bodies.items())),
                       "snapshots": {
                           str(t): snapshot_payload(*[(p, 20.0, 800.0)
                                                      for p in self.bodies[t]])
                           for t in self.ids}}, f)

    def fetch(self, *args):
        p = subprocess.run([sys.executable, "stub_fleaflicker.py"] + list(args),
                           cwd=self.dir, capture_output=True, text=True,
                           timeout=120)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p

    def names(self, team):
        with open(os.path.join(self.dir, "roster-%d-%s.json"
                               % (team, fetch_data.SEASON_TAG))) as f:
            return [r["n"] for r in json.load(f)]

    def test_naming_one_side_of_a_deal_re_cuts_every_team_it_touches(self):
        """The one side asked for, cut alone, is the side that gains a body --
        and the file it came off still carries him. Two files own one body and
        the league's PF stops summing to itself"""
        self.fetch("roster", str(self.at.MOVES[0][1]))
        self.assertEqual(
            sorted(f for f in os.listdir(self.dir) if f.startswith("roster-")),
            sorted("roster-%d-%s.json" % (t, fetch_data.SEASON_TAG)
                   for t in self.at.INVOLVED))

    def test_every_moved_body_lands_on_the_file_of_the_team_that_traded_for_him(
            self):
        """The whole point of the overlay, read off disk rather than off the
        dict it was applied to: the wire lags a handshake deal, so the row the
        sim prices has to be the post-deal one on both sides at once"""
        self.fetch("roster")
        for name, src, dst in self.at.MOVES:
            with self.subTest(player=name):
                self.assertIn(name, self.names(dst))
                self.assertNotIn(name, self.names(src))

    def test_a_dropped_body_is_on_no_file_the_fetch_writes(self):
        """A drop is not a move, so nobody gains him -- and left on the file he
        is priced as an asset that no longer exists in the league"""
        self.fetch("roster")
        for name, src in self.at.DROPS:
            with self.subTest(player=name):
                self.assertEqual([t for t in self.ids
                                  if name in self.names(t)], [])
