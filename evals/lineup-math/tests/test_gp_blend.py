import unittest
from tests.harness import *


class ProjectedSeasonGP(unittest.TestCase):
    ROW = {"n": "Joel Embiid", "tm": "PHI", "avg": 40.0, "tot": 760.0,
           "gp": 19, "posLabel": "C", "elig": ["C"]}

    def test_the_gp_is_the_mean_of_the_feeds_when_both_hit(self):
        with gp_snapshot(None):
            mapped = sim.project_gp("Joel Embiid")
        with gp_snapshot([("Joel Embiid", 40)], fanscout=[("Joel Embiid", 60)]):
            p, = sim.our_roster(roster_file(self.ROW))
            self.assertEqual(p["gp"], round((40 + 60) / 2))
            self.assertNotEqual(p["gp"], round(mapped))

    def test_an_ascii_overlay_name_matches_the_accented_pool_name(self):
        with gp_snapshot([("Nikola Jokic", 80)]):
            self.assertEqual(round(sim.project_gp("Nikola Jokić")), 80)

    def test_a_player_neither_feed_hits_stays_on_the_map(self):
        with gp_snapshot(None):
            mapped = round(sim.project_gp("Joel Embiid"))
        with gp_snapshot([("Nikola Jokić", 72)]):
            p, = sim.our_roster(roster_file(self.ROW))
            self.assertEqual(p["gp"], mapped)
