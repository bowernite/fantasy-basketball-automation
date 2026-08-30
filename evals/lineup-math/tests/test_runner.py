import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest

import sim
from simlib.runner import (
    check_config, enrich_config, parse_config, resolve_roster, run_config)
from tests.harness import cheap_monte_carlo

EXAMPLES = os.path.join(sim.HERE, "sims", "examples")


class ResolveRoster(unittest.TestCase):
    def test_team_id_resolves_to_roster_file(self):
        self.assertTrue(resolve_roster(161024).startswith("roster-161024-"))
        self.assertEqual(resolve_roster("161024"), resolve_roster(161024))

    def test_bare_filename_gets_json_suffix(self):
        self.assertTrue(resolve_roster("roster-161024-2025-26").endswith(".json"))


class ConfigParse(unittest.TestCase):
    def test_single_kind_becomes_one_section(self):
        sec = parse_config({"kind": "reports", "names": ["market"]})
        self.assertEqual(len(sec), 1)
        self.assertEqual(sec[0]["kind"], "reports")

    def test_sections_passthrough(self):
        cfg = {"sections": [{"kind": "reports", "names": ["market"]}]}
        self.assertEqual(parse_config(cfg), cfg["sections"])


class ConfigValidate(unittest.TestCase):
    def test_unknown_kind_is_refused(self):
        with self.assertRaises(ValueError) as ctx:
            check_config({"kind": "nope", "names": []})
        self.assertIn("unknown kind", str(ctx.exception))

    def test_ours_only_report_with_counterparty_roster_is_refused(self):
        with self.assertRaises(ValueError) as ctx:
            check_config({"kind": "reports", "names": ["scenarios"],
                          "roster": 161024})
        self.assertIn("refuse", str(ctx.exception))

    def test_example_configs_validate(self):
        for name in os.listdir(EXAMPLES):
            if not name.endswith(".json"):
                continue
            with self.subTest(name=name):
                check_config(os.path.join(EXAMPLES, name))


class ConfigRun(unittest.TestCase):
    def test_trade_screen_runs_on_minimal_deal(self):
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161020,
            "their_label": "Mitch",
            "deals": [{
                "label": "probe",
                "out_us": ["Jalen Suggs"],
                "in_from_them": ["Deni Avdija"],
                "out_them": ["Deni Avdija"],
                "in_from_us": ["Jalen Suggs"],
            }],
        }
        with cheap_monte_carlo():
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                run_config(cfg)
            text = out.getvalue()
        self.assertIn("JOINT DEALS", text)
        self.assertIn("probe", text)
        self.assertNotIn("ERROR", text)

    def test_trade_screen_delta_w_is_the_field_season_delta(self):
        deal = {
            "label": "probe",
            "out_us": ["Jalen Suggs"],
            "in_from_them": ["Deni Avdija"],
            "out_them": ["Deni Avdija"],
            "in_from_us": ["Jalen Suggs"],
        }
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161020,
            "their_label": "Mitch",
            "deals": [deal],
        }
        their = "roster-161020-2025-26.json"
        with cheap_monte_carlo():
            after_us, before_us, after_them, before_them = sim.deal_odds(
                sim.basis_after_trade(
                    None, deal["out_us"],
                    [p for p in sim.our_roster(their) if p["n"] == "Deni Avdija"]),
                sim.basis_after_trade(
                    their, deal["out_them"],
                    [p for p in sim.our_roster() if p["n"] == "Jalen Suggs"]),
                their)
            out = enrich_config(cfg)
        got = out["deals"][0]["results"]
        self.assertEqual(got["dw_us"], round(after_us.wins - before_us.wins, 2))
        self.assertEqual(got["dw_them"],
                         round(after_them.wins - before_them.wins, 2))

    def test_trade_screen_title_note_is_both_rosters(self):
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161020,
            "their_label": "Mitch",
            "deals": [{
                "label": "probe",
                "out_us": ["Jalen Suggs"],
                "in_from_them": ["Deni Avdija"],
                "out_them": ["Deni Avdija"],
                "in_from_us": ["Jalen Suggs"],
            }],
        }
        with cheap_monte_carlo():
            out = enrich_config(cfg)
        self.assertIn("both rosters", out["meta"]["dp_title_note"])
        self.assertIn("both rosters", out["deals"][0]["results"]["dp_title_note"])

    def test_cli_check_accepts_valid_config(self):
        path = os.path.join(EXAMPLES, "brian-trade-screen.json")
        p = subprocess.run(["python3", "sim_run.py", "--check", path],
                           cwd=sim.HERE, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_cli_check_refuses_bad_kind(self):
        path = os.path.join(tempfile.mkdtemp(), "bad.json")
        with open(path, "w") as f:
            json.dump({"kind": "nope"}, f)
        p = subprocess.run(["python3", "sim_run.py", "--check", path],
                           cwd=sim.HERE, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("unknown kind", p.stderr + p.stdout)


class RunHelp(unittest.TestCase):
    def test_directory_runner_lists_sim_run(self):
        p = subprocess.run(["./run", "-h"], cwd=sim.HERE,
                           capture_output=True, text=True)
        self.assertIn("sim_run.py", p.stdout + p.stderr)
