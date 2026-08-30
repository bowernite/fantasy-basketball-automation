import unittest

from simlib.roster import apply_trade, basis_after_trade, our_roster, pad


def _names(roster):
    return [p["n"] for p in roster]


class ApplyTrade(unittest.TestCase):
    def test_net_plus_one_without_cut(self):
        wire = [{"n": "A", "tm": "BOS", "avg": 30, "gp": 60, "elig": ["PG", "SG"]}]
        out = apply_trade(wire, ["A"], [
            {"n": "B", "tm": "NYK", "avg": 28, "gp": 60, "elig": ["PG", "SG"]},
            {"n": "C", "tm": "LAL", "avg": 27, "gp": 60, "elig": ["SF", "PF"]},
        ])
        self.assertEqual(_names(out), ["B", "C"])

    def test_net_minus_one_without_dead(self):
        wire = [
            {"n": "A", "tm": "BOS", "avg": 30, "gp": 60, "elig": ["PG", "SG"]},
            {"n": "B", "tm": "NYK", "avg": 28, "gp": 60, "elig": ["PG", "SG"]},
        ]
        out = apply_trade(wire, ["A", "B"], [
            {"n": "C", "tm": "LAL", "avg": 27, "gp": 60, "elig": ["SF", "PF"]},
        ])
        self.assertEqual(_names(out), ["C"])

    def test_refuses_when_over_cap_without_cuts(self):
        wire = [{"n": "P%d" % i, "tm": "BOS", "avg": 20, "gp": 60, "elig": ["PG", "SG"]}
                for i in range(38)]
        with self.assertRaises(ValueError) as ctx:
            apply_trade(wire, ["P0"], [
                {"n": "X", "tm": "NYK", "avg": 28, "gp": 60, "elig": ["PG", "SG"]},
                {"n": "Y", "tm": "LAL", "avg": 27, "gp": 60, "elig": ["SF", "PF"]},
            ])
        self.assertIn("name 1 cut", str(ctx.exception))

    def test_basis_after_trade_repads(self):
        path = "roster-161025-2025-26.json"
        n = len(our_roster(path))
        full = basis_after_trade(path, ["Kawhi Leonard"], [
            p for p in our_roster("roster-161024-2025-26.json")
            if p["n"] in ("Miles Bridges", "Aaron Gordon")
        ])
        self.assertEqual(len(full), 38)
        self.assertEqual(len([p for p in full if not p["n"].startswith(("RK", "FA", "PAD"))]),
                         n - 1 + 2)

