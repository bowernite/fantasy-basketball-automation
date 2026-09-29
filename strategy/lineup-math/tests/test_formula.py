import unittest
from tests.harness import *


class FormulaWins(unittest.TestCase):
    def test_a_14_rate_body_is_worth_the_measured_light_night_pf(self):
        self.assertAlmostEqual(
            sim.formula_player_wins(sim.star(14.0, 60)),
            sim.pf_wins(61))

    def test_a_48_rate_body_is_worth_the_measured_star_pf(self):
        self.assertAlmostEqual(
            sim.formula_player_wins(sim.star(48.0, 60)),
            sim.pf_wins(1304))

    def test_formula_wins_scale_with_gp(self):
        at_60 = sim.formula_player_wins(sim.star(14.0, 60))
        at_78 = sim.formula_player_wins(sim.star(14.0, 78))
        self.assertAlmostEqual(at_78 / at_60, 78 / 60)

    def test_a_season_lost_to_injury_prices_at_his_track_record_gp(self):
        row = {"n": "Joel Embiid", "tm": "PHI", "avg": 40.0, "tot": 760.0,
               "gp": 19, "posLabel": "C", "elig": ["C"]}
        with gp_snapshot(None):
            on_track_record, = sim.our_roster(roster_file(row))
        with gp_snapshot([("Joel Embiid", 5)], fanscout=[("Joel Embiid", 5)]):
            hurt, = sim.our_roster(roster_file(row))
        self.assertEqual(hurt["gp"], 5)
        self.assertAlmostEqual(sim.formula_player_wins(hurt),
                               sim.formula_player_wins(on_track_record),
                               delta=0.02)

    def test_feeds_above_his_track_record_price_at_the_feed_gp(self):
        row = {"n": "Joel Embiid", "tm": "PHI", "avg": 40.0, "tot": 760.0,
               "gp": 19, "posLabel": "C", "elig": ["C"]}
        with gp_snapshot([("Joel Embiid", 78)], fanscout=[("Joel Embiid", 78)]):
            healthy, = sim.our_roster(roster_file(row))
        self.assertAlmostEqual(
            sim.formula_player_wins(healthy),
            sim.formula_player_wins(sim.star(healthy["avg"], 78)))

    def test_a_deal_is_incoming_minus_outgoing_formula_wins(self):
        incoming = [p for p in sim.our_roster(THEIR_ROSTER)
                    if p["n"] == "Deni Avdija"]
        outgoing = [p for p in sim.our_roster() if p["n"] == "Jalen Suggs"]
        self.assertEqual(len(incoming), 1)
        self.assertAlmostEqual(
            sim.deal_formula_wins(incoming, outgoing),
            (sim.formula_player_wins(incoming[0])
             - sim.formula_player_wins(outgoing[0])))


class FormulaReport(unittest.TestCase):
    ROW = re.compile(r"^  (\S.*?) +[\d.]+ +\d+ +[-+][\d.]+ +([-+][\d.]+)", re.M)

    def test_the_formula_column_matches_formula_player_wins(self):
        buf = io.StringIO()
        with cheap_monte_carlo(8):
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["formula"]()
        printed = dict(self.ROW.findall(buf.getvalue()))
        by_name = {p["n"]: p for p in sim.our_roster()}
        name = next(n for n in printed if n in by_name)
        self.assertAlmostEqual(
            float(printed[name]), sim.formula_player_wins(by_name[name]),
            delta=0.01)
