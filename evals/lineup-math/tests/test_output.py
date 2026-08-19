import unittest
from tests.harness import *

class OutputIsSelfDescribing(unittest.TestCase):
    """A caller reads these tables in a terminal, not next to findings.md. A
    figure whose units live in another file is a figure he has to go and look
    up -- and the commonest way that ends is that he does not"""

    def test_every_report_opens_with_the_units_its_numbers_are_in(self):
        """`+2.01` is per 19-matchup regular season. Nothing on stdout said so,
        so it read equally well as per week, per matchup or per game -- and a
        legend that arrives BELOW the table it explains is one a reader who
        scrolled to his row never sees"""
        for name in sorted(sim.REPORTS):
            with self.subTest(report=name):
                raw = render(name)
                legend = reports.OWN_UNITS.get(name, reports.UNITS)
                self.assertTrue(raw.startswith(legend),
                                "%s opens with:\n%s" % (name, raw[:200]))
                if "win" not in one_line(raw).lower():
                    continue
                self.assertRegex(one_line(raw), r"%d-matchup regular season"
                                 % sim.DELTA_W_MATCHUPS)

    def test_the_consolidation_ladder_converts_at_the_rate_it_prints(self):
        """`wins` is `dPF` through the PF-per-win on line 1, and the note above
        the table says so. It is the one place these tables cross from points
        into wins, and every scenario in `trades` is quoted out of this column"""
        out = render("scenarios")
        pf_per_win = float(re.search(r"1 win = (\d+) PF", out).group(1))
        rows = re.findall(r"([-+]\d+) +\d+\.\d% +([-+]\d+\.\d\d)$", out, re.M)
        self.assertGreater(len(rows), 10, out)
        for dpf, wins in rows:
            self.assertAlmostEqual(float(wins), float(dpf) / pf_per_win,
                                   delta=0.01, msg=out)

    def test_every_table_converts_pf_to_wins_on_the_basis_its_legend_names(self):
        """The legend promises wins over a 19-matchup regular season. A report
        that divides a 20-period season PF by the season constant alone is
        quoting wins over 20 -- 5% high, in the same column, under a legend
        saying otherwise, and nothing in the row gives it away"""
        # Wins per matchup per PF of weekly edge, off the real margin
        # distribution rather than off the constant the reports divide by
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
        """`calibration` prints the linearisation beside the curve under "the
        straight line `wins()` actually divides by", which is where a reader
        goes to check a `Delta w` against the constant. Quoted over 20 matchups
        both rows are 5% above the legend's basis -- in the one table whose job
        is to BE the conversion every other table's column went through"""
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
        """`replacement` prints `c` (PF per rate-point-GP) and `K` (rate-point-
        GP per win) side by side, and a reader multiplies them back out to a
        PF-per-win. On a 20-matchup K that product is 5% off the one every
        `Delta w` in the package is quoted at, and both numbers look right"""
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

    def test_the_formula_error_is_signed_the_way_its_own_note_says(self):
        """`+ means the formula pays him more than the sim does`. The direction
        is what a reader books -- reversed, the bodies the shorthand overpays
        read as the ones it underpays, and he sorts on it backwards"""
        out = render("formula")
        rows = re.findall(r"([-+]\d+\.\d\d) +([-+]\d+\.\d\d) +([-+]\d+)% +"
                          r"([-+]\d+)%$", out, re.M)
        self.assertGreaterEqual(len(rows), 10, out)
        for sim_w, one_r, err, _ in rows:
            self.assertEqual(float(err) > 0, float(one_r) > float(sim_w),
                             "%s vs %s reads as err %s%%" % (one_r, sim_w, err))

    def test_the_per_player_table_names_its_columns(self):
        """Seven columns, no header row: `+-0.001` and a trailing `48.5` next to
        a name reads as two more scores"""
        out = render("players")
        head, = [l for l in out.splitlines() if l.strip().startswith("player")]
        for col in ("rate", "gp", "elig", "wins", "sd", "next", "flags"):
            self.assertIn(col, head)

    def test_the_per_player_header_sits_over_the_numbers_it_names(self):
        """Naming the columns is only half of it -- a header shifted off its own
        data reads `sd` over the wins figure, and the reader books the wrong
        column"""
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
