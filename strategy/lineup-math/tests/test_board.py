import unittest
from tests.harness import *

class BoardSnapshot(unittest.TestCase):
    def test_the_newest_snapshot_is_the_one_read(self):
        d = tempfile.mkdtemp()
        for n in ("july-2026-dynasty-ranks-points.csv",
                  "december-2026-dynasty-ranks-points.csv",
                  "january-2027-dynasty-ranks-points.csv",
                  "january-2027-dynasty-ranks-9cat.csv"):
            open(os.path.join(d, n), "w").close()
        self.assertEqual(os.path.basename(sim.newest_board(d)),
                         "january-2027-dynasty-ranks-points.csv")

    def test_a_directory_with_no_snapshot_says_what_it_looked_for(self):
        with self.assertRaises(FileNotFoundError) as e:
            sim.newest_board(tempfile.mkdtemp())
        self.assertIn("dynasty-ranks-points.csv", str(e.exception))

    def test_the_report_names_the_snapshot_it_priced_off(self):
        self.assertIn(os.path.basename(sim.newest_board()), render("market"))

    def test_the_rank_to_rate_bridge_accounts_for_every_ranked_player(self):
        out = render("market")
        matched, total = (int(x) for x in re.search(
            r"(\d+) of the board's (\d+) ranked players", out).groups())
        unmatched, = re.findall(r"unmatched (\d+)", out)
        self.assertEqual(int(unmatched), total - matched)

class BoardBridge(unittest.TestCase):
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
        pairs = sim.board_rates()
        self.assertEqual(len(pairs), 359)
        self.assertEqual(sum(1 for _, r in pairs if r >= 45), 8)
        self.assertEqual(sum(1 for _, r in pairs if r >= 50), 3)
        self.assertEqual(sum(1 for _, r in pairs if r >= 60), 1)

    def test_a_fragment_season_does_not_set_the_rate_a_rank_band_supplies(self):
        deepest = lambda pairs: max(k for k, r in pairs if r >= 30)
        self.assertLess(deepest(sim.board_rates()),
                        deepest(sim.board_rates(min_gp=0)) - 50)
        self.assertEqual(sim.pool_seasons("Walker Kessler")["2025"][1], 5)
