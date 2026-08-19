import unittest
from tests.harness import *

class NoPoolHistory(unittest.TestCase):
    """`our_roster` feeds the GP fit the POOL's rate, and a player the pool has
    never seen has none to give it, so he is the one row where that branch goes
    the other way. A TRUE rookie's file row is a 0-GP, 0.0-rate shell with no
    actual rate anywhere on it, so without the projection he prices as a hole
    on a roster that really holds a body"""

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
        """Both fallbacks gone, an undrafted body the pool never saw and the
        feed does not carry. `project_gp` RAISES on a name with no rate at all
        (`PoolJoinByName`), and a roster that will not load prices no trade at
        all, so the last fallback has to be the row's own 0.0 rather than None
        """
        path = roster_file({"n": "Unknown Rookie", "tm": "LAC", "avg": 0.0,
                            "tot": 0.0, "gp": 0, "posLabel": "F",
                            "elig": ["SF", "PF"]})
        self.assertIsNone(sim.projected_rate("Unknown Rookie"))
        p, = sim.our_roster(path)
        self.assertEqual(p["gp"], round(sim.project_gp("Unknown Rookie",
                                                       gp=0, rate=0.0)))

class RateEvidence(unittest.TestCase):
    """A rate posted over a fragment season no longer carries the whole `Δw`,
    the projection replaces it. That same fragment is still the GP fit's main
    input and GP is the dominant one, so how many games the pool saw is what
    says whether the `Δw` is a measurement or an upper bound (`Eval Definitions
    §Δw`)"""

    def test_it_reports_the_games_the_gp_projection_rests_on(self):
        self.assertEqual(sim.rate_evidence("Kevin Porter")["gp"], 38)
        self.assertEqual(sim.rate_evidence("Precious Achiuwa")["gp"], 73)

    def test_it_reports_a_whole_season_missing_from_the_pool(self):
        """A missed season is ABSENT from the pool rather than a zero, so the
        GP fit cannot see it at all and expected GP is conditional on him
        playing"""
        self.assertTrue(sim.rate_evidence("Kevin Porter")["missed"])
        self.assertFalse(sim.rate_evidence("Precious Achiuwa")["missed"])

    def test_a_missed_most_recent_season_counts_too(self):
        """A trailing absence is the same censoring as an interior one and the
        one the GP fit is blindest to, so it cannot read as a full season"""
        self.assertTrue(sim.rate_evidence("Kyrie Irving")["missed"])
        self.assertTrue(sim.rate_evidence("Fred VanVleet")["missed"])

    def test_a_late_arrival_is_not_a_missed_season(self):
        """Seasons before a player entered the pool are not absences. Only a
        gap INSIDE his history is one, or every rookie reads as injured"""
        self.assertFalse(sim.rate_evidence("Stephon Castle")["missed"])

    def test_it_counts_the_rotation_seasons_the_role_rests_on(self):
        """Rate >= 15 is where GP starts measuring health rather than role
        (`Eval Definitions §Durability`), so it is also the bar a season clears
        to be evidence the role is real"""
        self.assertEqual(sim.rate_evidence("Kevin Porter")["rotation"], 4)
        self.assertEqual(sim.rate_evidence("Ty Jerome")["rotation"], 2)

    def test_it_names_every_flag_code_an_eval_has_to_carry(self):
        """`Eval Template.md` fixes the vocabulary and `Eval Definitions`
        §Durability
        fixes the fragment band at 10-25 games. An eval author reads these off
        here rather than eyeballing five seasons of pool rows per player, so
        the PUBLIC function has to name all four codes, or a caller gets two of
        the four with no sign the others exist"""
        self.assertEqual(sim.evidence_flags("Ty Jerome"), ["frag", "rot2"])
        self.assertEqual(sim.evidence_flags("Kevin Porter"), ["miss"])
        self.assertEqual(sim.evidence_flags("Precious Achiuwa"), [])
        self.assertEqual(sim.evidence_flags("Nobody At All"), ["nopool"])

    def test_a_season_below_the_fragment_band_still_flags(self):
        """§Durability writes the band as 10-25 to separate a fragment from a
        whole missed season, but a 5-game season is PRESENT in the pool rather
        than absent, so a lower bound silently passes the thinnest rows of all
        """
        self.assertEqual(sim.evidence_flags("Walker Kessler"), ["frag"])

class EvidenceFlagsInThePlayersTable(unittest.TestCase):
    """`rate_evidence` and `evidence_flags` are pinned against the pool by
    `RateEvidence`, but the reader never calls them, he reads `sim.py players`.
    The flag is the only thing on that row saying whether the `Δw` beside it is
    a measurement or an upper bound, and an unflagged row reads as a clean one,
    so a flag computed and not printed, or printed against the wrong row, is
    worse than no flag column at all"""

    @classmethod
    def setUpClass(cls):
        cls.rows = {}
        ours = sim.our_roster()
        for line in render("players").splitlines():
            for p in ours:
                if line.strip().startswith(p["n"] + " ") and p["n"] not in cls.rows:
                    cls.rows[p["n"]] = line

    def test_a_season_missing_from_the_pool_reaches_the_row_it_belongs_to(self):
        """Kyrie and VanVleet are the two on our roster with a whole season
        gone, and exactly the rows whose rate is an upper bound"""
        self.assertIn("miss", self.rows["Kyrie Irving"])
        self.assertIn("miss", self.rows["Fred VanVleet"])

    def test_every_row_prints_the_flags_its_evidence_implies_and_no_others(self):
        """Both ways. Whatever `evidence_flags` names is what his row carries,
        and a row carries nothing it did not earn, so a flag printed against
        the wrong row clears the first half and fails here.

        `rotN` carries the count rather than just a mark, the bar being 3
        seasons at rate >= 15 (`Eval Definitions §Durability`). Below it the
        rate is a role that has not held up yet, at or above it the reader may
        read the row clean"""
        for name, line in self.rows.items():
            with self.subTest(player=name):
                self.assertEqual(
                    re.findall(r"frag|miss|nopool|rot\d", line),
                    sim.evidence_flags(name), line)

    def test_the_table_has_a_row_for_every_player_on_the_roster(self):
        """The agreement above is vacuous for any player the scan missed"""
        self.assertEqual(sorted(self.rows),
                         sorted(p["n"] for p in sim.our_roster()))
