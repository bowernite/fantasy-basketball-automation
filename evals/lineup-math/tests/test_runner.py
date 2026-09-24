import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest

import sim
from simlib.runner import (
    _simmed_date, check_config, deal_delta_base, enrich_config, parse_config,
    resolve_roster, run_config, sim_tmp_path, team_sims_path, team_sim_path,
    team_trade_shapes_path)
from tests.harness import cheap_monte_carlo

EXAMPLES = os.path.join(sim.HERE, "sims", "examples")


class ResolveRoster(unittest.TestCase):
    def test_team_id_resolves_to_roster_file(self):
        self.assertTrue(resolve_roster(161024).startswith("roster-161024-"))
        self.assertEqual(resolve_roster("161024"), resolve_roster(161024))

    def test_bare_filename_gets_json_suffix(self):
        self.assertTrue(resolve_roster("roster-161024-2025-26").endswith(".json"))


class DealDeltaBase(unittest.TestCase):
    def test_an_unknown_counterparty_is_refused_rather_than_priced_off_another_team(self):
        with self.assertRaises(ValueError) as ctx:
            deal_delta_base({
                "out_us": ["Jalen Suggs"],
                "in_from_them": ["Deni Avdija"],
            }, 999999)
        self.assertIn("999999", str(ctx.exception))


class TeamTradeShapesPath(unittest.TestCase):
    def test_slug_resolves_to_name_trade_shapes_md(self):
        path = team_trade_shapes_path("josh")
        self.assertTrue(path.endswith(os.path.join("josh", "Josh Trade Shapes.md")))

    def test_team_id_resolves_to_name_trade_shapes_md(self):
        path = team_trade_shapes_path(161021)
        self.assertTrue(path.endswith(os.path.join("hlina", "Hlina Trade Shapes.md")))

    def test_team_sims_path_alias(self):
        self.assertEqual(team_sims_path("josh"), team_trade_shapes_path("josh"))

    def test_team_sim_path_alias(self):
        self.assertEqual(team_sim_path("josh"), team_trade_shapes_path("josh"))

    def test_sim_tmp_path_under_tmpdir(self):
        path = sim_tmp_path("josh-kawhi")
        self.assertTrue(path.startswith(tempfile.gettempdir()))
        self.assertTrue(path.endswith("ff-sim-josh-kawhi.json"))


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

    def test_eval_columns_needs_their_roster(self):
        with self.assertRaises(ValueError) as ctx:
            check_config({"kind": "eval-columns"})
        self.assertIn("their_roster", str(ctx.exception))

    def test_eval_columns_section_has_no_roster_key(self):
        from simlib.runner import eval_columns_section
        sec = eval_columns_section(161014)
        check_config(sec)
        self.assertEqual(sec["kind"], "eval-columns")
        self.assertEqual(sec["their_roster"], 161014)
        self.assertNotIn("roster", sec)

    def test_eval_columns_refuses_our_roster(self):
        with self.assertRaises(ValueError) as ctx:
            check_config({"kind": "eval-columns", "their_roster": 161025})
        self.assertIn("counterparty", str(ctx.exception))

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

    def test_trade_screen_includes_formula_and_season_delta_w(self):
        deal = {
            "label": "probe",
            "out_us": ["Jalen Suggs"],
            "in_from_them": ["Deni Avdija"],
            "out_them": ["Deni Avdija"],
            "in_from_us": ["Jalen Suggs"],
        }
        their = "roster-161020-2025-26.json"
        in_us = [p for p in sim.our_roster(their) if p["n"] == "Deni Avdija"]
        out_us = [p for p in sim.our_roster() if p["n"] == "Jalen Suggs"]
        expect_fdw = sim.deal_formula_wins(in_us, out_us)
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161020,
            "their_label": "Mitch",
            "deals": [deal],
        }
        with cheap_monte_carlo():
            out = enrich_config(cfg)
        got = out["deals"][0]["results"]
        self.assertEqual(got["fdw_us"], round(expect_fdw, 2))
        self.assertIn("fdw_them", got)

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

    def test_trade_screen_results_include_simmed_date(self):
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
        self.assertEqual(out["deals"][0]["results"]["simmed"], _simmed_date())
        self.assertEqual(out["meta"]["simmed"], _simmed_date())

    def test_trade_screen_picks_move_by_slot(self):
        deal = {
            "label": "probe",
            "out_us": [],
            "in_from_them": [],
            "out_them": [],
            "in_from_us": [],
            "out_us_picks": ["2.09"],
            "in_from_them_picks": ["1.03"],
        }
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161020,
            "their_label": "Mitch",
            "deals": [deal],
        }
        their = "roster-161020-2025-26.json"
        with cheap_monte_carlo():
            after_ours = sim.basis_after_trade(
                None, [], [], out_picks=["2.09"],
                in_picks=sim.resolve_picks(their, ["1.03"]))
            after_theirs = sim.basis_after_trade(their, [], [])
            after_us, before_us, after_them, before_them = sim.deal_odds(
                after_ours, after_theirs, their)
            out = enrich_config(cfg)
        got = out["deals"][0]["results"]
        self.assertNotIn("error", got)
        self.assertEqual(got["dw_us"], round(after_us.wins - before_us.wins, 2))
        self.assertEqual(got["dw_them"],
                         round(after_them.wins - before_them.wins, 2))

    def test_trade_screen_formula_delta_w_counts_the_mock_rookie_of_a_moved_pick(self):
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161020,
            "their_label": "Mitch",
            "deals": [{
                "label": "probe",
                "out_us": [],
                "in_from_them": [],
                "out_them": [],
                "in_from_us": [],
                "out_them_picks": ["1.03"],
                "in_from_them_picks": ["1.03"],
            }],
        }
        with cheap_monte_carlo():
            out = enrich_config(cfg)
        got = out["deals"][0]["results"]
        self.assertGreater(got["fdw_us"], 0)
        self.assertEqual(got["fdw_them"], -got["fdw_us"])

    def test_trade_screen_pick_not_held_by_sender_refuses(self):
        deal = {
            "label": "probe",
            "out_us": [],
            "in_from_them": [],
            "out_them": [],
            "in_from_us": [],
            "out_us_picks": ["1.03"],
        }
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161020,
            "their_label": "Mitch",
            "deals": [deal],
        }
        with cheap_monte_carlo():
            out = enrich_config(cfg)
        self.assertIn("error", out["deals"][0]["results"])

    def test_trade_screen_section_meta_has_simmed_date(self):
        cfg = {
            "sections": [{
                "label": "probe",
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
            }],
        }
        with cheap_monte_carlo():
            out = enrich_config(cfg)
        self.assertEqual(out["sections"][0]["meta"]["simmed"], _simmed_date())

    def test_run_config_writes_results_back_to_file(self):
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
        path = os.path.join(tempfile.mkdtemp(), "probe.json")
        with open(path, "w") as f:
            json.dump(cfg, f)
        with cheap_monte_carlo():
            run_config(path)
        with open(path) as f:
            saved = json.load(f)
        self.assertIn("meta", saved)
        self.assertIn("simmed", saved["meta"])
        self.assertIn("results", saved["deals"][0])
        self.assertIn("dw_us", saved["deals"][0]["results"])

    def test_reports_only_config_does_not_write_back(self):
        cfg = {"kind": "reports", "names": ["market"]}
        path = os.path.join(tempfile.mkdtemp(), "reports.json")
        with open(path, "w") as f:
            json.dump(cfg, f)
        with open(path) as f:
            before = f.read()
        with cheap_monte_carlo():
            run_config(path)
        with open(path) as f:
            self.assertEqual(f.read(), before)

    def test_cached_deals_are_skipped(self):
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161020,
            "their_label": "Mitch",
            "deals": [
                {
                    "label": "done",
                    "out_us": ["Jalen Suggs"],
                    "in_from_them": ["Deni Avdija"],
                    "out_them": ["Deni Avdija"],
                    "in_from_us": ["Jalen Suggs"],
                    "results": {"dw_us": 1.0, "dp_title_us": 1.0,
                                "dw_them": -1.0, "dp_title_them": -1.0},
                },
                {
                    "label": "new",
                    "out_us": ["Jalen Suggs"],
                    "in_from_them": ["Deni Avdija"],
                    "out_them": ["Deni Avdija"],
                    "in_from_us": ["Jalen Suggs"],
                },
            ],
        }
        with cheap_monte_carlo():
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                run_config(cfg)
            text = out.getvalue()
        self.assertNotIn("done", text)
        self.assertIn("new", text)

    def test_cli_check_accepts_valid_config(self):
        path = os.path.join(EXAMPLES, "eval-columns.json")
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

    def test_cli_eval_refuses_our_team(self):
        p = subprocess.run(["python3", "sim_run.py", "--eval", "161025"],
                           cwd=sim.HERE, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("counterparty", p.stderr + p.stdout)

    def test_eval_columns_prices_incoming_on_us_without_moving_roster(self):
        was = sim.ROSTER
        cfg = {
            "kind": "eval-columns",
            "their_roster": 161020,
            "names": ["Deni Avdija"],
        }
        with cheap_monte_carlo():
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                run_config(cfg)
        text = buf.getvalue()
        self.assertEqual(sim.ROSTER, was)
        self.assertIn("Deni Avdija", text)
        self.assertIn("ours", text)
        self.assertIn("theirs", text)
        row = next(l for l in text.splitlines() if "Deni Avdija" in l)
        parts = row.split("\t")
        self.assertGreaterEqual(len(parts), 5)
        self.assertNotEqual(parts[2], parts[3], text)

    def test_player_effects_refuses_a_name_missing_on_the_source_roster(self):
        cfg = {
            "kind": "player-effects",
            "their_roster": 161020,
            "groups": [{
                "label": "probe",
                "source": "their",
                "names": ["Nobody McFake"],
            }],
        }
        with cheap_monte_carlo():
            with self.assertRaises(KeyError) as ctx:
                run_config(cfg)
        self.assertIn("Nobody McFake", str(ctx.exception))

    def test_eval_columns_stays_on_us_when_roster_global_is_theirs(self):
        was = sim.ROSTER
        cfg = {
            "kind": "eval-columns",
            "their_roster": 161020,
            "names": ["Deni Avdija"],
        }
        try:
            sim.ROSTER = "roster-161020-2025-26.json"
            with cheap_monte_carlo():
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    run_config(cfg)
            text = buf.getvalue()
        finally:
            sim.ROSTER = was
        self.assertIn("Deni Avdija", text)
        self.assertNotIn("already on this roster", text)


class RunHelp(unittest.TestCase):
    def test_directory_runner_lists_sim_run(self):
        p = subprocess.run(["./run", "-h"], cwd=sim.HERE,
                           capture_output=True, text=True)
        self.assertIn("sim_run.py", p.stdout + p.stderr)


class EvalCli(unittest.TestCase):
    def test_sim_run_help_lists_eval(self):
        p = subprocess.run(["python3", "sim_run.py", "-h"], cwd=sim.HERE,
                           capture_output=True, text=True)
        self.assertIn("--eval", p.stdout)
