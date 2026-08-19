import unittest
from tests.harness import *

class BoardSnapshot(unittest.TestCase):
    """`dizzle-dynasty` snapshots are month-stamped and the month moves, and
    the Skill says never hardcode one. `board_rates` is the study's only rank
    to rate bridge, so a hardcoded month reads a stale board silently, and
    keeps reading it after the new snapshot lands beside it"""

    def test_the_newest_snapshot_is_the_one_read(self):
        d = tempfile.mkdtemp()
        for n in ("july-2026-dynasty-ranks-points.csv",
                  "december-2026-dynasty-ranks-points.csv",
                  "january-2027-dynasty-ranks-points.csv",   # newest, year wins
                  "january-2027-dynasty-ranks-9cat.csv"):    # wrong scoring
            open(os.path.join(d, n), "w").close()
        self.assertEqual(os.path.basename(sim.newest_board(d)),
                         "january-2027-dynasty-ranks-points.csv")

    def test_a_directory_with_no_snapshot_says_what_it_looked_for(self):
        with self.assertRaises(FileNotFoundError) as e:
            sim.newest_board(tempfile.mkdtemp())
        self.assertIn("dynasty-ranks-points.csv", str(e.exception))

    def test_the_report_names_the_snapshot_it_priced_off(self):
        """The month moves and the old file stays put, so a rank table that
        does not name its board cannot be checked against one, and the reader
        has no way to tell a re-snapshot from a re-rank"""
        self.assertIn(os.path.basename(sim.newest_board()), render("market"))

class BoardBridge(unittest.TestCase):
    """The framework converts board rank to wins through one constant, so a
    rank to FPts/G join that silently matches nothing would make every scenario
    look purchasable"""

    def test_the_top_of_the_board_joins_to_scoring_rates(self):
        pairs = sim.board_rates()
        top50 = [r for r, _ in pairs if r <= 50]
        self.assertGreater(len(top50), 40)

    def test_rate_falls_as_board_rank_rises(self):
        pairs = sim.board_rates()
        top = statistics.mean([v for r, v in pairs if r <= 30])
        deep = statistics.mean([v for r, v in pairs if 150 <= r <= 250])
        self.assertGreater(top, deep + 10)

    def test_the_rates_a_four_and_five_for_one_demands_barely_exist(self):
        """The case for the 3-for-1 cap that does NOT go through the win table.
        The 4-for-1 break-even at 45.1 and the 5-for-1 at 58.8 ask for rates
        almost nobody supplies, so those deals are unavailable at any price
        rather than merely expensive. If the pool ever gets deep in 45s that
        argument is gone"""
        pairs = sim.board_rates()
        self.assertEqual(len(pairs), 359)
        self.assertEqual(sum(1 for _, r in pairs if r >= 45), 8)
        self.assertEqual(sum(1 for _, r in pairs if r >= 50), 3)
        self.assertEqual(sum(1 for _, r in pairs if r >= 60), 1)

    def test_a_fragment_season_does_not_set_the_rate_a_rank_band_supplies(self):
        """The report prints the DEEPEST rank that has ever supplied a rate,
        how far down you might have to look, so one 5-game hot streak deep on
        the board moves the answer to a question about where 30-FPts players
        live. `min_gp` is what stops it"""
        deepest = lambda pairs: max(k for k, r in pairs if r >= 30)
        self.assertLess(deepest(sim.board_rates()),
                        deepest(sim.board_rates(min_gp=0)) - 50)
        self.assertEqual(sim.pool_seasons("Walker Kessler")["2025"][1], 5)
