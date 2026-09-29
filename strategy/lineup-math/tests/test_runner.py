import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from unittest import mock

import sim
from fetch_data import TEAM
from simlib import cuts, runner
from simlib.runner import (
    TEAM_SLUG, _simmed_date, check_config, deal_delta_age, deal_delta_base, enrich_config,
    parse_config, resolve_roster, run_config, sim_tmp_path)
from tests.harness import cheap_monte_carlo

EXAMPLES = os.path.join(sim.HERE, "sims", "examples")


def full_counterparty():
    """A league seat other than ours at the wire cap"""
    for tid in TEAM_SLUG:
        rows = sim.our_roster(resolve_roster(tid))
        if tid != TEAM and len(rows) == sim.MAX_WIRE:
            return tid
    raise unittest.SkipTest("no counterparty at the wire cap")


def by_value(rows):
    return sorted(rows, key=lambda p: -p["avg"] * p["gp"])


class ResolveRoster(unittest.TestCase):
    def test_team_id_resolves_to_roster_file(self):
        self.assertTrue(resolve_roster(161024).startswith("roster-161024-"))
        self.assertEqual(resolve_roster("161024"), resolve_roster(161024))

    def test_bare_filename_gets_json_suffix(self):
        self.assertTrue(resolve_roster("roster-161024-2025-26").endswith(".json"))


def write_team_md(root, slug, filename, rows):
    folder = os.path.join(root, "teams", slug)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, filename), "w") as f:
        f.write("# X · 38 bodies\n\n## Players\n"
                "player | AGE POS | BASE | FPts/G GP | Δw | flags\n"
                "%s\nσ: none\n\n## Picks\npick | origin | rookie | VALUE\n"
                "2nd | own 2.09 | template | 645\n" % "\n".join(rows))


def fake_teams_root():
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "lineup-math"))
    return root


class DealDeltaBase(unittest.TestCase):
    def test_base_comes_from_the_agent_team_md_not_the_human_file_beside_it(self):
        root = fake_teams_root()
        write_team_md(root, "my-team", "Ours.team.md",
                      ["Jalen Suggs | 25.2 PG/SG | 1200 | 30 60 | +0.50"])
        write_team_md(root, "mitch", "Mitch.team.md",
                      ["Deni Avdija | 25.7 SF | 2000 | 35 70 | +0.90 | rot2"])
        with open(os.path.join(root, "teams", "mitch", "Mitch's Team.md"), "w") as f:
            f.write("| # | Player | AGE | POS | Boards | BASE |\n"
                    "| 1 | Deni Avdija | 25.7 | SF | – | **9999** |\n")
        with mock.patch.object(runner, "HERE", os.path.join(root, "lineup-math")):
            got = deal_delta_base({
                "out_us": ["Jalen Suggs"],
                "in_from_them": ["Deni Avdija"],
            }, 161020)
        self.assertEqual(got, 800)

    def test_a_player_missing_from_the_team_md_blanks_base_age_and_score_and_says_who(self):
        mitch = 161020
        ours = by_value(sim.our_roster())[0]
        theirs = by_value(sim.our_roster(resolve_roster(mitch)))[0]
        root = fake_teams_root()
        write_team_md(root, "my-team", "Ours.team.md",
                      ["%s | 27.0 PG | 3000 | 40 70 | +1.00" % ours["n"]])
        write_team_md(root, "mitch", "Mitch.team.md",
                      ["Someone Else | 27.0 PG | 500 | 20 60 | +0.10"])
        cfg = {"kind": "trade-screen", "their_roster": mitch, "deals": [{
            "label": "swap", "out_us": [ours["n"]], "in_from_them": [theirs["n"]],
            "out_them": [theirs["n"]], "in_from_us": [ours["n"]]}]}
        out = io.StringIO()
        with mock.patch.object(runner, "HERE", os.path.join(root, "lineup-math")), \
                cheap_monte_carlo(), contextlib.redirect_stdout(out):
            res = run_config(cfg)[0]["deals"][0]["results"]
        self.assertEqual((res["delta_base_us"], res["dage_us"], res["score_us"]),
                         (None, None, None))
        self.assertIn("%s not in Mitch.team.md" % theirs["n"], res["eval_gap"])
        self.assertIn("%s not in Mitch.team.md" % theirs["n"], out.getvalue())

    def test_a_malformed_row_only_blanks_deals_that_name_that_player(self):
        root = fake_teams_root()
        write_team_md(root, "my-team", "Ours.team.md",
                      ["Jalen Suggs | 25.2 PG/SG | 1200 | 30 60 | +0.50",
                       "Tyus Jones | 29.0 PG | 1,24 | 12 50 | +0.01"])
        write_team_md(root, "mitch", "Mitch.team.md",
                      ["Deni Avdija | 25.7 SF | 2000 | 35 70 | +0.90",
                       "Blank Age |  | 50 | 10 40 | +0.01"])
        with mock.patch.object(runner, "HERE", os.path.join(root, "lineup-math")):
            clean = deal_delta_base({"out_us": ["Jalen Suggs"],
                                     "in_from_them": ["Deni Avdija"]}, 161020)
            with self.assertRaises(runner.EvalGap) as ctx:
                deal_delta_base({"out_us": ["Tyus Jones"],
                                 "in_from_them": ["Blank Age"]}, 161020)
        self.assertEqual(clean, 800)
        self.assertIn("Tyus Jones unreadable in Ours.team.md", str(ctx.exception))
        self.assertIn("Blank Age unreadable in Mitch.team.md", str(ctx.exception))

    def test_a_pick_in_the_label_without_its_base_field_is_a_gap_not_a_silent_zero(self):
        root = fake_teams_root()
        write_team_md(root, "my-team", "Ours.team.md",
                      ["Jalen Suggs | 25.2 PG/SG | 1200 | 30 60 | +0.50"])
        write_team_md(root, "mitch", "Mitch.team.md",
                      ["Deni Avdija | 25.7 SF | 2000 | 35 70 | +0.90"])
        deal = {"label": "Suggs+'27 1st > Avdija+Mitch '28 2nd",
                "out_us": ["Jalen Suggs"], "in_from_them": ["Deni Avdija"]}
        with mock.patch.object(runner, "HERE", os.path.join(root, "lineup-math")):
            with self.assertRaises(runner.EvalGap) as ctx:
                deal_delta_base(deal, 161020)
            priced = deal_delta_base(dict(deal, out_us_extra_base=1176,
                                          in_from_us_extra_base=541), 161020)
        self.assertIn("'27 1st", str(ctx.exception))
        self.assertIn("'28 2nd", str(ctx.exception))
        self.assertEqual(priced, 800 - 1176 + 541)

    def test_a_pick_named_by_slot_counts_like_one_named_by_round(self):
        root = fake_teams_root()
        write_team_md(root, "my-team", "Ours.team.md",
                      ["Rookie | 20.0 PG | 100 | 10 50 | +0.01"])
        write_team_md(root, "mitch", "Mitch.team.md",
                      ["Vet | 30.0 PG/SG | 900 | 30 70 | +0.50"])
        deal = {"label": "Rookie+'27 2.09 > Vet",
                "out_us": ["Rookie"], "in_from_them": ["Vet"]}
        with mock.patch.object(runner, "HERE", os.path.join(root, "lineup-math")):
            with self.assertRaises(runner.EvalGap) as ctx:
                deal_delta_base(deal, 161020)
            age = deal_delta_age(deal, 161020)
        self.assertIn("'27 2.09", str(ctx.exception))
        self.assertAlmostEqual(age, 30.0 - 19)

    def test_picks_in_a_label_without_a_side_split_are_a_gap(self):
        root = fake_teams_root()
        write_team_md(root, "my-team", "Ours.team.md",
                      ["Jalen Suggs | 25.2 PG/SG | 1200 | 30 60 | +0.50"])
        write_team_md(root, "mitch", "Mitch.team.md",
                      ["Deni Avdija | 25.7 SF | 2000 | 35 70 | +0.90"])
        deal = {"label": "Suggs and '27 1st for Avdija", "out_us_extra_base": 1176,
                "out_us": ["Jalen Suggs"], "in_from_them": ["Deni Avdija"]}
        with mock.patch.object(runner, "HERE", os.path.join(root, "lineup-math")):
            with self.assertRaises(runner.EvalGap) as ctx:
                deal_delta_age(deal, 161020)
        self.assertIn(" > ", str(ctx.exception))

    def test_an_unknown_counterparty_is_refused_rather_than_priced_off_another_team(self):
        with self.assertRaises(ValueError) as ctx:
            deal_delta_base({
                "out_us": ["Jalen Suggs"],
                "in_from_them": ["Deni Avdija"],
            }, 999999)
        self.assertIn("999999", str(ctx.exception))


class DealDeltaAge(unittest.TestCase):
    def test_a_body_with_no_age_and_no_weight_does_not_blank_the_change(self):
        root = fake_teams_root()
        write_team_md(root, "my-team", "Ours.team.md",
                      ["Rookie | – PG/SG | 100 | 10 50 | +0.01 | nopool"])
        write_team_md(root, "mitch", "Mitch.team.md",
                      ["Vet | 30.0 PG/SG | 900 | 30 70 | +0.50"])
        with mock.patch.object(runner, "HERE", os.path.join(root, "lineup-math")):
            got = deal_delta_age({
                "label": "Rookie+'28 1st > '27 1st",
                "out_us": ["Rookie"],
                "in_from_them": [],
            }, 161020)
        self.assertAlmostEqual(got, 1.0)


class SimTmpPath(unittest.TestCase):
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

    def test_a_deal_moving_a_pick_body_is_refused(self):
        deal = {"label": "probe", "out_us": [], "in_from_them": [],
                "out_them": [], "in_from_us": [], "out_us_picks": ["2.09"]}
        with self.assertRaises(ValueError) as ctx:
            check_config({"kind": "trade-screen", "their_roster": 161020,
                          "deals": [deal]})
        self.assertIn("out_us_picks", str(ctx.exception))

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

    def test_trade_screen_score_prices_the_published_numbers_net_of_extra_bodies(self):
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161022,
            "their_label": "Todd",
            "deals": [{
                "label": "probe",
                "out_us": ["Jalen Suggs", "Keon Ellis"],
                "in_from_them": ["Dean Wade"],
                "out_them": ["Dean Wade"],
                "in_from_us": ["Jalen Suggs", "Keon Ellis"],
            }],
        }
        with cheap_monte_carlo():
            out = enrich_config(cfg)
        got = out["deals"][0]["results"]
        # one body fewer on our side -> formula Δw credited 0.3
        expect = (got["delta_base_us"] + 300 * (got["fdw_us"] + 0.3)
                  + 250 * got["dw_us"] + 80 * got["dp_title_us"])
        self.assertEqual(got["score_us"], round(expect))

    def test_a_deal_that_overfills_our_roster_cuts_the_body_whose_named_cut_scores_best(self):
        ours = sim.our_roster()
        self.assertEqual(len(ours), sim.MAX_WIRE, "needs our roster full")
        their = next(tid for tid in TEAM_SLUG if tid != TEAM)
        star = by_value(ours)[0]["n"]
        pair = [p["n"] for p in by_value(sim.our_roster(resolve_roster(their)))[:2]]
        named = {"out_us": [star], "in_from_them": pair, "out_them": pair,
                 "in_from_us": [star]}
        candidates = [p["n"] for p in cuts.shortlist(
            [p for p in ours if p["n"] != star], 1)]
        cfg = {"kind": "trade-screen", "their_roster": their,
               "deals": [dict(named, label="auto")]
               + [dict(named, label=n, out_us=[star, n]) for n in candidates]}
        with cheap_monte_carlo():
            rows = {d["label"]: d["results"] for d in enrich_config(cfg)["deals"]}
        base = sim.board_base(ours)
        score = {n: -base[n] + 300 * rows[n]["fdw_us"] + 250 * rows[n]["dw_us"]
                 + 80 * rows[n]["dp_title_us"] for n in candidates}
        cut = max(score, key=score.get)
        auto = rows["auto"]
        self.assertEqual(auto["cut_us"], [cut])
        self.assertEqual(auto["cut_them"], [])
        for col in ("fdw_us", "dw_us", "dp_title_us"):
            self.assertEqual(auto[col], rows[cut][col], col)
        named_base = deal_delta_base(named, their)
        self.assertEqual(auto["delta_base_us"],
                         None if named_base is None else named_base - base[cut])
        self.assertEqual(auto["score_us"], None if named_base is None else round(
            auto["delta_base_us"] + 300 * auto["fdw_us"] + 250 * auto["dw_us"]
            + 80 * auto["dp_title_us"]))

    def test_a_deal_that_overfills_their_roster_cuts_the_body_whose_named_cut_scores_best_for_them(self):
        their = full_counterparty()
        theirs = sim.our_roster(resolve_roster(their))
        star = by_value(theirs)[0]["n"]
        pair = [p["n"] for p in by_value(sim.our_roster())[:2]]
        named = {"out_us": pair, "in_from_them": [star], "out_them": [star],
                 "in_from_us": pair}
        candidates = [p["n"] for p in cuts.shortlist(
            [p for p in theirs if p["n"] != star], 1)]
        cfg = {"kind": "trade-screen", "their_roster": their,
               "deals": [dict(named, label="auto")]
               + [dict(named, label=n, out_them=[star, n]) for n in candidates]}
        with cheap_monte_carlo():
            rows = {d["label"]: d["results"] for d in enrich_config(cfg)["deals"]}
        base = sim.board_base(theirs)
        score = {n: -base[n] + 300 * rows[n]["fdw_them"]
                 + 250 * rows[n]["dw_them"] + 80 * rows[n]["dp_title_them"]
                 for n in candidates}
        cut = max(score, key=score.get)
        auto = rows["auto"]
        self.assertEqual(auto["cut_them"], [cut])
        self.assertEqual(auto["cut_us"], [])
        for col in ("fdw_them", "dw_them", "dp_title_them", "dw_us"):
            self.assertEqual(auto[col], rows[cut][col], col)

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

    def test_trade_screen_age_change_reads_later_picks_from_the_label(self):
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161020,
            "their_label": "Mitch",
            "deals": [{
                "label": "'27 1st > '28 1st",
                "out_us": [],
                "in_from_them": [],
                "out_them": [],
                "in_from_us": [],
            }],
        }
        with cheap_monte_carlo():
            out = enrich_config(cfg)
        self.assertAlmostEqual(out["deals"][0]["results"]["dage_us"], -1.0)

    def test_trade_screen_age_change_weights_picks_by_round(self):
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161020,
            "their_label": "Mitch",
            "deals": [{
                "label": "'27 2nd+'28 1st > '27 1st",
                "out_us": [],
                "in_from_them": [],
                "out_them": [],
                "in_from_us": [],
            }],
        }
        with cheap_monte_carlo():
            out = enrich_config(cfg)
        # out (19 x 300 + 18 x 700) / 1000 = 18.3; in 19
        self.assertAlmostEqual(out["deals"][0]["results"]["dage_us"], 0.7)

    def test_trade_screen_age_change_counts_a_fourth_round_pick(self):
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161020,
            "their_label": "Mitch",
            "deals": [{
                "label": "'27 4th+'28 1st > '28 1st",
                "out_us": [],
                "in_from_them": [],
                "out_them": [],
                "in_from_us": [],
            }],
        }
        with cheap_monte_carlo():
            out = enrich_config(cfg)
        # out (19 x 50 + 18 x 700) / 750 = 18.07; in 18
        self.assertAlmostEqual(out["deals"][0]["results"]["dage_us"], -0.07)

    def test_trade_screen_age_change_reads_a_later_pick_named_by_owner(self):
        cfg = {
            "kind": "trade-screen",
            "their_roster": 161020,
            "their_label": "Mitch",
            "deals": [{
                "label": "'28 1st > '27 KC 2nd",
                "out_us": [],
                "in_from_them": [],
                "out_them": [],
                "in_from_us": [],
            }],
        }
        with cheap_monte_carlo():
            out = enrich_config(cfg)
        self.assertAlmostEqual(out["deals"][0]["results"]["dage_us"], 1.0)

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
