import unittest
from tests.harness import *

class OutputIsSelfDescribing(unittest.TestCase):
    def test_no_report_spends_its_first_line_on_a_units_legend(self):
        for name in sorted(sim.REPORTS):
            with self.subTest(report=name):
                first = render(name).strip().splitlines()[0]
                self.assertNotRegex(first, r"^units:")

    def test_the_positional_slot_loss_is_flagged_as_the_bound_it_is(self):
        row, = [l for l in render("nights").splitlines() if "no legal slot" in l]
        self.assertIn("upper bound", row)

    def test_the_consolidation_ladder_converts_at_the_rate_it_prints(self):
        out = render("scenarios")
        pf_per_win = float(re.search(r"1 win = (\d+) PF", out).group(1))
        rows = re.findall(r"([-+]\d+) +\d+\.\d% +([-+]\d+\.\d\d)$", out, re.M)
        self.assertGreater(len(rows), 10, out)
        for dpf, wins in rows:
            self.assertAlmostEqual(float(wins), float(dpf) / pf_per_win,
                                   delta=0.01, msg=out)

    def test_every_table_converts_pf_to_wins_on_the_basis_its_legend_names(self):
        h = 1e-4
        per_pf = (sim.margin_pwin(h) - sim.margin_pwin(-h)) / (2 * h)

        def over_19(season_pf):
            return sim.DELTA_W_MATCHUPS * per_pf * (season_pf / sim.WEEKS)

        for name in ("extras", "durability"):
            for pf, w in re.findall(r"([-+]\d+) PF = ([-+]\d+\.\d+) wins",
                                    render(name)):
                with self.subTest(report=name, pf=pf):
                    self.assertAlmostEqual(float(w), over_19(float(pf)),
                                           delta=0.006)

    def test_the_row_labelled_wins_is_what_wins_actually_returns(self):
        out = render("calibration")
        rows = {}
        for label in ("+PF", "curve", "wins()"):
            line, = [l for l in out.splitlines()
                     if l.split()[:1] == [label]]
            rows[label] = [float(x) for x in line.split()[1:]]
        self.assertGreaterEqual(len(rows["+PF"]), 4)
        for pf, curve, line in zip(rows["+PF"], rows["curve"], rows["wins()"]):
            with self.subTest(pf=pf):
                self.assertAlmostEqual(line, sim.pf_wins(pf), delta=0.005)
                self.assertAlmostEqual(
                    curve,
                    sim.DELTA_W_MATCHUPS * (sim.margin_pwin(pf / sim.WEEKS)
                                            - sim.margin_pwin()),
                    delta=0.005)

    def test_the_shorthands_own_constant_buys_a_win_at_the_legends_price(self):
        h = 1e-4
        per_pf = (sim.margin_pwin(h) - sim.margin_pwin(-h)) / (2 * h)
        rows = re.findall(r"^ +\S+ +\d+\.\d +(\d+\.\d{3}) +(\d+)$",
                          render("replacement"), re.M)
        self.assertGreaterEqual(len(rows), 5)
        for c, K in rows:
            with self.subTest(c=c, K=K):
                self.assertAlmostEqual(
                    float(c) * float(K),
                    sim.WEEKS / (sim.DELTA_W_MATCHUPS * per_pf), delta=6)

    def test_the_formula_error_column_is_signed_against_the_sim_column(self):
        out = render("formula")
        rows = re.findall(r"([-+]\d+\.\d\d) +([-+]\d+\.\d\d) +([-+]\d+)%$",
                          out, re.M)
        self.assertGreaterEqual(len(rows), 10, out)
        for sim_w, one_r, err in rows:
            self.assertEqual(float(err) > 0, float(one_r) > float(sim_w),
                             "%s vs %s reads as err %s%%" % (one_r, sim_w, err))

    def test_a_counterparty_players_report_is_labelled_theirs_not_the_ours_column(self):
        out = render("players", THEIR_ROSTER)
        self.assertRegex(out, r"THEIRS")
        self.assertRegex(out, r"not the eval .+ours")

    def test_playoffs_says_it_is_not_the_eval_column(self):
        out = render("playoffs")
        self.assertRegex(out, r"not the eval")

    def test_the_per_player_table_states_the_seed_blocks_behind_its_sd(self):
        out = render("players")
        m = re.search(r"blocks: (\d+) x (\d+) trials", out)
        self.assertIsNotNone(m, out)
        self.assertEqual(int(m.group(2)), engine.TRIALS)

    def test_the_per_player_table_names_its_columns(self):
        out = render("players")
        head, = [l for l in out.splitlines() if l.strip().startswith("player")]
        for col in ("rate", "gp", "elig", "wins", "sd", "next", "flags"):
            self.assertIn(col, head)

    def test_the_per_player_header_sits_over_the_numbers_it_names(self):
        lines = render("players").splitlines()
        head, = [l for l in lines if l.strip().startswith("player")]
        row = lines[lines.index(head) + 1]
        at = 0
        for col, pattern in (("wins", r"[-+]\d+\.\d{2}"),
                             ("sd", r"\+-\d+\.\d{3}"),
                             ("next", r"inf|\d+\.\d")):
            with self.subTest(column=col):
                at = re.compile(pattern).search(row, at).end()
                self.assertEqual(re.search(r"%s\b" % col, head).end(), at,
                                 "`%s` does not end over its own column:\n%s\n%s"
                                 % (col, head, row))
