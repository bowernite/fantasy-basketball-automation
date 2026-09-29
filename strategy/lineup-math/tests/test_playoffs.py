import unittest
from tests.harness import *

class PlayoffsReport(unittest.TestCase):
    ROW = re.compile(r"^  (\S.*?) +(\S+) +(\S+) +(\S+) +(\S+)"
                     + r" +([-+][\d.]+) +\+-([\d.]+)" * 3 + r" *(.*)$", re.M)

    def test_every_player_gets_a_week_column_per_round_and_a_band_per_seed(self):
        out = render("playoffs")
        rows = {m[0]: m[1:] for m in self.ROW.findall(out)}
        ours = sim.our_roster()
        self.assertEqual(set(rows), {p["n"] for p in ours}, out)
        for i in sim.BRACKET:
            self.assertIn("W%d" % sim.PERIODS[i]["ordinal"], out)
        for band in sim.BANDS:
            self.assertIn(band.label, out)
        for p in ours:
            if sim.unsigned(p["tm"]) or sim.projected_rate(p["n"]) is None:
                continue
            with self.subTest(player=p["n"]):
                for w, pts in enumerate(sim.week_points(p)):
                    cell = rows[p["n"]][w]
                    self.assertEqual(cell, "%.0f/%d"
                                     % (pts, sim.bracket_games(p["tm"])[w]))

    def test_the_projected_field_names_its_teams(self):
        out = render("playoffs")
        teams = json.loads(read_text(
            os.path.join(sim.DATA_DIR, "teams-%s.json" % fetch_data.SEASON_TAG)))
        for name in teams.values():
            self.assertIn(name, out)

    def test_a_body_with_no_nba_schedule_prints_no_week_columns(self):
        path = roster_file(
            {"n": "Nobody Signed", "tm": sim.UNSIGNED, "avg": 30.0, "tot": 0.0,
             "gp": 60, "posLabel": "C", "elig": ["C"]},
            {"n": "Victor Wembanyama", "tm": "SAS", "avg": 50.0, "tot": 0.0,
             "gp": 60, "posLabel": "C", "elig": ["C"]})
        rows = dict((m[0], m[1:]) for m in self.ROW.findall(render("playoffs", path)))
        self.assertEqual(list(rows["Nobody Signed"][:len(sim.BRACKET)]),
                         ["-"] * len(sim.BRACKET))
        self.assertNotIn("-", rows["Victor Wembanyama"][:len(sim.BRACKET)])

    def test_a_row_with_no_week_columns_carries_the_flag_that_explains_them(self):
        path = roster_file(
            {"n": "Nobody Signed", "tm": sim.UNSIGNED, "avg": 30.0, "tot": 0.0,
             "gp": 60, "posLabel": "C", "elig": ["C"]},
            {"n": "Victor Wembanyama", "tm": "SAS", "avg": 50.0, "tot": 0.0,
             "gp": 60, "posLabel": "C", "elig": ["C"]})
        rows = dict((m[0], m[1:]) for m in self.ROW.findall(render("playoffs", path)))
        self.assertIn("fa", rows["Nobody Signed"][-1].split())
        self.assertEqual(rows["Victor Wembanyama"][-1], "")

    def test_the_sigma_bound_is_taken_off_the_title_ladder_alone(self):
        out = render("playoffs")
        n, = re.findall(r"sigma sensitivity: (\d+) ladder games", out)
        self.assertEqual(int(n), len(sim.BRACKET_TEAMS) - 1)

    ROUND = re.compile(
        r"^ +(\d+-\d+) +(W\d+) +(\d+) +(\d+) +(\d+) +(\d+) +(\d+) +([\d.]+)$",
        re.M)

    def test_the_basis_footer_states_what_the_probabilities_were_built_on(self):
        out = render("playoffs")
        rows = self.ROUND.findall(out)
        self.assertEqual(
            [(r[0], r[1]) for r in rows],
            [(b.label, "W%d" % sim.PERIODS[i]["ordinal"])
             for b in sim.BANDS for i in b.periods], out)
        for band, label, _, mu_us, mu_opp, _, sd, p in rows:
            with self.subTest(band=band, round=label):
                z = (float(mu_us) - float(mu_opp)) / float(sd)
                self.assertAlmostEqual(float(p),
                                       0.5 * (1 + math.erf(z / math.sqrt(2))),
                                       delta=0.015)
        self.assertIn("x a regular-season game", out)

    def test_the_footer_names_every_team_the_opponent_level_is_measured_on(self):
        out = render("playoffs")
        for path in committed_rosters():
            with self.subTest(team=os.path.basename(path)):
                self.assertIn(os.path.basename(path), out)
        marked, = [l for l in out.splitlines() if "<- loaded" in l]
        self.assertIn(os.path.basename(roster_mod.ROSTER), marked)

    def test_each_band_carries_its_own_error_bar(self):
        with cheap_monte_carlo():
            out = render("playoffs")
            name = sim.our_roster()[0]["n"]
            full = sim.basis()
            got, = bracket.player_title(full, [name],
                                    R=sim.group_replacement(full)).values()
        row, = [m for m in self.ROW.findall(out) if m[0] == name]
        for k, band in enumerate(sim.BANDS):
            mean, sd, blocks = got[band.label]
            with self.subTest(band=band.label):
                self.assertAlmostEqual(float(row[5 + 2 * k]), 100 * mean,
                                       places=2)
                self.assertAlmostEqual(float(row[6 + 2 * k]),
                                       100 * sim.se_mean(blocks), places=2)

    def test_the_error_bar_it_publishes_is_measured_on_enough_blocks(self):
        out = render("playoffs")
        self.assertGreaterEqual(bracket.TITLE_BLOCKS - 1, 5)
        self.assertIn("averaged over %d shared" % bracket.TITLE_BLOCKS, out)
        with cheap_monte_carlo(4):
            full = sim.basis()
            got, = bracket.player_title(full, [sim.our_roster()[0]["n"]],
                                    R=flat_R()).values()
        self.assertEqual(len(got[sim.BANDS[0].label][2]), bracket.TITLE_BLOCKS)

    SUMMARY = re.compile(r"^ +(\d+-\d+) +([\d.]+) +\+-([\d.]+)"
                         r" +([\d.]+)-([\d.]+) +\+-([\d.]+)"
                         r" +(\d+) +([\d.]+) \+-([\d.]+) \(", re.M)

    def test_the_unpaired_band_figures_carry_an_error_bar_too(self):
        rows = self.SUMMARY.findall(render("playoffs"))
        self.assertEqual([r[0] for r in rows], [b.label for b in sim.BANDS])
        for row in rows:
            with self.subTest(band=row[0]):
                for k, what in ((2, "P(title)"), (5, "by seed"),
                                (8, "the multiplier")):
                    self.assertGreater(float(row[k]), 0,
                                       "%s printed a bar nothing measured"
                                       % what)

    def test_what_it_publishes_is_the_draw_the_basis_above_it_states(self):
        out = render("playoffs")
        with cheap_monte_carlo():
            mus = sim.bracket_weeks(sim.basis(), seed0=bracket.SEED0)
            want = [sim.title_prob(mus, b) for b in sim.BANDS]
        for row, band, p in zip(self.SUMMARY.findall(out), sim.BANDS, want):
            with self.subTest(band=band.label):
                self.assertAlmostEqual(float(row[1]), p, places=3)

    def test_the_week_headers_sit_over_the_columns_they_name(self):
        lines = render("playoffs").splitlines()
        head, = [l for l in lines if l.strip().startswith("player")]
        row = next(l for l in lines[lines.index(head) + 1:]
                   if len(re.findall(r"\d+/\d+", l)) == len(sim.BRACKET))
        at = 0
        for i in sim.BRACKET:
            col = "W%d" % sim.PERIODS[i]["ordinal"]
            with self.subTest(column=col):
                at = re.compile(r"\d+/\d+").search(row, at).end()
                self.assertEqual(re.search(r"\b%s\b" % col, head).end(), at,
                                 "`%s` does not end over its own column:\n%s\n%s"
                                 % (col, head, row))

    def test_the_rows_are_ordered_on_the_band_the_preamble_names(self):
        out = render("playoffs")
        self.assertIn("Sorted on the %s band." % sim.BANDS[0].label,
                      one_line(out))
        col = [float(m[5]) for m in self.ROW.findall(out)]
        self.assertEqual(col, sorted(col, reverse=True))

    REG = re.compile(r"^ +reg +([\d.]+) +(\d+) +(\d+) +(\d+) +(\d+) +([\d.]+)"
                     r"  <- one regular period$", re.M)

    def test_the_sigma_column_is_the_level_times_the_spread_it_prints(self):
        out = render("playoffs")
        self.assertIn("sigma: %.4f x the round's level, reg %.4f x the field's"
                      % (sim.MARGIN_CV, sim.FIELD_MARGIN_CV), out)
        for band, label, _, _, _, field, sd, _ in self.ROUND.findall(out):
            with self.subTest(band=band, round=label):
                self.assertAlmostEqual(float(sd),
                                       sim.MARGIN_CV * float(field), delta=1.0)
        reg, = self.REG.findall(out)
        _, mu_us, mu_opp, field, sd, p = (float(x) for x in reg)
        self.assertEqual(mu_opp, field, "the drawn opponent is the field's own "
                         "mean, not a survivor above it")
        self.assertAlmostEqual(sd, sim.FIELD_MARGIN_CV * field, delta=1.0)
        z = (mu_us - mu_opp) / sd
        self.assertAlmostEqual(p, 0.5 * (1 + math.erf(z / math.sqrt(2))),
                               delta=0.005)

    BAND = re.compile(r"^ +(\d+-\d+) +([\d.]+) +\+-[\d.]+"
                      r" +([\d.]+)-([\d.]+) +\+-[\d.]+ +(\d+)"
                      r" +([\d.]+) \+-[\d.]+ \(([\d.]+)-([\d.]+) by round\)$",
                      re.M)

    def test_each_band_figure_sits_inside_the_spread_printed_beside_it(self):
        rows = self.BAND.findall(render("playoffs"))
        self.assertEqual([r[0] for r in rows], [b.label for b in sim.BANDS])
        for row, band in zip(rows, sim.BANDS):
            p, lo, hi, rounds, mult, mlo, mhi = (float(x) for x in row[1:])
            with self.subTest(band=band.label):
                self.assertEqual(rounds, len(band.periods))
                self.assertLessEqual(lo, hi)
                self.assertLessEqual(mlo, mhi)
                self.assertTrue(lo - 0.0005 <= p <= hi + 0.0005,
                                "P(title) %.3f is outside its own %.3f-%.3f"
                                % (p, lo, hi))
                self.assertTrue(mlo - 0.05 <= mult <= mhi + 0.05,
                                "the multiplier %.1f is outside its own "
                                "%.1f-%.1f by round" % (mult, mlo, mhi))

    SENSITIVITY = re.compile(
        r"sigma sensitivity: \d+ ladder games give margin sd (\d+) vs the "
        r"(\d+)-(\d+) above; (\S+) band reads ([\d.]+) vs ([\d.]+)")

    def test_the_sigma_sensitivity_reads_against_the_table_it_sits_under(self):
        out = render("playoffs")
        m = self.SENSITIVITY.search(one_line(out))
        self.assertIsNotNone(m, out)
        tight, lo, hi, band, alt, basis = m.groups()
        sds = [float(r[6]) for r in self.ROUND.findall(out)]
        self.assertEqual((float(lo), float(hi)), (min(sds), max(sds)))
        published = {r[0]: float(r[1]) for r in self.BAND.findall(out)}
        self.assertEqual(float(basis), published[band])
        self.assertLess(float(tight), min(sds), "not the tighter read it is "
                        "printed as -- the direction below is backwards")
        self.assertGreater(float(alt), float(basis))

    def test_the_draw_it_prints_is_the_one_it_climbed(self):
        halves = re.search(r"draw: seeds (\S+) \| (\S+), climbed worst seed",
                           one_line(render("playoffs")))
        self.assertIsNotNone(halves)
        self.assertEqual([[int(s) for s in h.split("-")]
                          for h in halves.groups()],
                         [list(l) for l in sim.LADDERS])

    def test_a_counterparty_is_banded_on_his_own_weeks(self):
        out = render("playoffs", THEIR_ROSTER)
        marked, = [l for l in out.splitlines() if "<- loaded" in l]
        self.assertIn(THEIR_ROSTER, marked)
        ours = {r[0]: float(r[1]) for r in self.BAND.findall(render("playoffs"))}
        theirs = {r[0]: float(r[1]) for r in self.BAND.findall(out)}
        self.assertEqual(sorted(theirs), sorted(ours))
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertLess(theirs[band.label], ours[band.label])

    def test_the_cli_serves_it_for_a_counterparty(self):
        status, out = cli("--roster", THEIR_ROSTER, "playoffs")
        self.assertEqual(status, 0, out)
        self.assertIn(THEIR_ROSTER, out)
        self.assertNotIn("playoffs", sim.OURS_ONLY)
        for name in {p["n"] for p in sim.our_roster(THEIR_ROSTER)}:
            self.assertIn(name, out)
