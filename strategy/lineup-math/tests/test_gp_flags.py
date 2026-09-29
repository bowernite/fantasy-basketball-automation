import unittest
from tests.harness import *

class NoPoolHistory(unittest.TestCase):
    ROOKIE = "Thomas Sorber"

    def test_a_player_the_pool_has_never_seen_still_prices_as_a_body(self):
        raw, = [q for q in sim._load(ROOKIE_ROSTER) if q["n"] == self.ROOKIE]
        p = rostered(self.ROOKIE, ROOKIE_ROSTER)

        self.assertEqual((raw["avg"], raw["gp"]), (0.0, 0))
        self.assertEqual(sim.evidence_flags(self.ROOKIE), ["nopool"])
        self.assertAlmostEqual(p["avg"], sim.projected_rate(self.ROOKIE))
        self.assertGreater(p["gp"], 20)
        self.assertEqual(p["gp"], round(sim.project_gp(
            self.ROOKIE, gp=0, rate=sim.projected_rate(self.ROOKIE))))

    def test_a_body_with_neither_a_pool_season_nor_a_projection_still_prices(self):
        path = roster_file({"n": "Unknown Rookie", "tm": "LAC", "avg": 0.0,
                            "tot": 0.0, "gp": 0, "posLabel": "F",
                            "elig": ["SF", "PF"]})
        self.assertIsNone(sim.projected_rate("Unknown Rookie"))
        p, = sim.our_roster(path)
        self.assertEqual(p["gp"], round(sim.project_gp("Unknown Rookie",
                                                       gp=0, rate=0.0)))

class RateEvidence(unittest.TestCase):
    def test_it_reports_the_games_the_gp_projection_rests_on(self):
        self.assertEqual(sim.rate_evidence("Kevin Porter")["gp"], 38)
        self.assertEqual(sim.rate_evidence("Precious Achiuwa")["gp"], 73)

    def test_it_reports_a_whole_season_missing_from_the_pool(self):
        self.assertTrue(sim.rate_evidence("Kevin Porter")["missed"])
        self.assertFalse(sim.rate_evidence("Precious Achiuwa")["missed"])

    def test_a_missed_most_recent_season_counts_too(self):
        self.assertTrue(sim.rate_evidence("Kyrie Irving")["missed"])
        self.assertTrue(sim.rate_evidence("Fred VanVleet")["missed"])

    def test_a_late_arrival_is_not_a_missed_season(self):
        self.assertFalse(sim.rate_evidence("Stephon Castle")["missed"])

    def test_it_counts_the_rotation_seasons_the_role_rests_on(self):
        self.assertEqual(sim.rate_evidence("Kevin Porter")["rotation"], 4)
        self.assertEqual(sim.rate_evidence("Ty Jerome")["rotation"], 2)

    def test_it_names_every_flag_code_an_eval_has_to_carry(self):
        self.assertEqual(sim.evidence_flags("Ty Jerome"), ["frag", "rot2"])
        self.assertEqual(sim.evidence_flags("Kevin Porter"), ["miss"])
        self.assertEqual(sim.evidence_flags("Precious Achiuwa"), [])
        self.assertEqual(sim.evidence_flags("Nobody At All"), ["nopool"])

    def test_a_season_below_the_fragment_band_still_flags(self):
        self.assertEqual(sim.evidence_flags("Walker Kessler"), ["frag"])

class EvidenceFlagsInThePlayersTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {}
        ours = sim.our_roster()
        for line in render("players").splitlines():
            for p in ours:
                if line.strip().startswith(p["n"] + " ") and p["n"] not in cls.rows:
                    cls.rows[p["n"]] = line

    def test_a_season_missing_from_the_pool_reaches_the_row_it_belongs_to(self):
        self.assertIn("miss", self.rows["Kyrie Irving"])
        self.assertIn("miss", self.rows["Fred VanVleet"])

    def test_every_row_prints_the_flags_its_evidence_implies_and_no_others(self):
        for name, line in self.rows.items():
            with self.subTest(player=name):
                self.assertEqual(
                    re.findall(r"frag|miss|nopool|rot\d", line),
                    sim.evidence_flags(name), line)

    def test_the_table_has_a_row_for_every_player_on_the_roster(self):
        self.assertEqual(sorted(self.rows),
                         sorted(p["n"] for p in sim.our_roster()))
