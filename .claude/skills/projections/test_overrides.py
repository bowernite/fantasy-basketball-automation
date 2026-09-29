"""Offline guard for projection overrides."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import overrides


class Overrides(unittest.TestCase):
    def setUp(self):
        overrides.index.cache_clear()

    def test_missing_file_is_a_no_op(self):
        real = overrides.OVERRIDES
        try:
            overrides.OVERRIDES = os.path.join(tempfile.gettempdir(),
                                               "no-overrides-here.json")
            overrides.index.cache_clear()
            self.assertIsNone(overrides.lookup_gp("Shaedon Sharpe"))
            self.assertIsNone(overrides.lookup_rate("Shaedon Sharpe"))
        finally:
            overrides.OVERRIDES = real
            overrides.index.cache_clear()

    def test_gp_override_wins_over_feed_keys(self):
        real = overrides.OVERRIDES
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            with open(path, "w") as f:
                json.dump({"players": {"Shaedon Sharpe": {"gp": 0,
                                                           "reason": "test"}}},
                          f)
            overrides.OVERRIDES = path
            overrides.index.cache_clear()
            self.assertEqual(overrides.lookup_gp("Shaedon Sharpe"), 0.0)
            self.assertIsNone(overrides.lookup_rate("Shaedon Sharpe"))
        finally:
            os.unlink(path)
            overrides.OVERRIDES = real
            overrides.index.cache_clear()

    def test_rate_override_is_optional(self):
        real = overrides.OVERRIDES
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            with open(path, "w") as f:
                json.dump({"players": {"Nikola Jokic": {"rate": 0.0}}}, f)
            overrides.OVERRIDES = path
            overrides.index.cache_clear()
            self.assertAlmostEqual(overrides.lookup_rate("Nikola Jokić"), 0.0)
        finally:
            os.unlink(path)
            overrides.OVERRIDES = real
            overrides.index.cache_clear()


if __name__ == "__main__":
    unittest.main()
