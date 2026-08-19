import unittest
from tests.harness import *

class PlayoffsReport(unittest.TestCase):
    """The report `Eval Definitions §ΔP(title)`, `eval-team` and `trades` all
    send a reader to. It answers about any team -- the opponent distribution is
    the league's, not our weekly scores -- so `--roster` has to serve it"""

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

    def test_the_legend_above_it_states_the_unit_of_its_own_table(self):
        """One legend prints above every report and it is the first thing a
        reader meets. Wins, scored-period PF and a per-game rate are the other
        thirteen tables' units and none of the three is a column here -- so the
        one report whose standing rule is that its number is never read in wins
        opened by defining wins, and never named percentage points of a title
        at all"""
        legend = one_line("\n".join(render("playoffs").splitlines()[:2]))
        self.assertTrue(legend.startswith("units:"), legend)
        self.assertNotIn("wins", legend)
        self.assertIn("percentage points of title probability", legend)

    def test_the_projected_field_names_its_teams(self):
        """The one table here that ranks the whole league listed twelve file
        names. Which of them is the counterparty under discussion, and which is
        us, was a question only the `team-info` skill could answer"""
        out = render("playoffs")
        teams = json.loads(read_text(
            os.path.join(sim.HERE, "teams-%s.json" % fetch_data.SEASON_TAG)))
        for name in teams.values():
            self.assertIn(name, out)

    def test_a_body_with_no_nba_schedule_prints_no_week_columns(self):
        """`fa` runs on the sim's synthetic schedule so its `Delta w` exists,
        but `W20`-`W23` are that player's own games and he has none (`Eval
        Definitions §Columns`). Printing LAC's is a fact about the fetch date
        published as a fact about the player"""
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
        """Every body on the roster is priced for `Delta P(title)`, including
        one with no NBA team, so a row can print four blank W columns beside a
        percentage point of a title -- which reads as a player worth that while
        playing no bracket games. `players` answers it with the same `fa` and
        `noproj` (`Eval Template §Flags`), and the blanks are unreadable without
        them"""
        path = roster_file(
            {"n": "Nobody Signed", "tm": sim.UNSIGNED, "avg": 30.0, "tot": 0.0,
             "gp": 60, "posLabel": "C", "elig": ["C"]},
            {"n": "Victor Wembanyama", "tm": "SAS", "avg": 50.0, "tot": 0.0,
             "gp": 60, "posLabel": "C", "elig": ["C"]})
        rows = dict((m[0], m[1:]) for m in self.ROW.findall(render("playoffs", path)))
        self.assertIn("fa", rows["Nobody Signed"][-1].split())
        self.assertEqual(rows["Victor Wembanyama"][-1], "")

    def test_the_sigma_bound_is_taken_off_the_title_ladder_alone(self):
        """Single elimination: 8 seeds play 7 games for the title, and the 8th
        seeded pairing in those periods is two ELIMINATED seeds playing for
        third. Both-sides-seeded separated last season's tanked games only
        because every one of those happened to draw a non-seed, and a draw that
        pairs two eliminated seeds puts a game neither is trying to win inside
        the margin sd this bound is printed from"""
        out = render("playoffs")
        n, = re.findall(r"The (\d+) bracket games actually played", out)
        self.assertEqual(int(n), len(sim.BRACKET_TEAMS) - 1)

    ROUND = re.compile(
        r"^ +(\d+-\d+) +(W\d+) +(\d+) +(\d+) +(\d+) +(\d+) +(\d+) +([\d.]+)$",
        re.M)

    def test_the_basis_footer_states_what_the_probabilities_were_built_on(self):
        """A `P(round)` is only readable against the opponent level and the
        margin sd behind it, so every round of every band prints all three and
        the printed probability is the one they imply -- a footer describing
        some other run is worse than none.

        Not to the last digit: `P(round)` mixes `Phi` over the opponents the
        draw can produce and `mu_opp` is that mixture's MEAN, so the two differ
        by the curvature of `Phi` across it. That gap is what the tolerance
        here bounds"""
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
        """`mu_opp` is 11 other roster files run through this same sim, and
        which teams those are is the whole basis. A level with no field under
        it is unauditable -- and the reader has to see the loaded team excluded
        from the bar it is measured against"""
        out = render("playoffs")
        for path in committed_rosters():
            with self.subTest(team=os.path.basename(path)):
                self.assertIn(os.path.basename(path), out)
        marked, = [l for l in out.splitlines() if "<- loaded" in l]
        self.assertIn(os.path.basename(roster_mod.ROSTER), marked)

    def test_each_band_carries_its_own_error_bar(self):
        """One `+-` per row cannot serve three bands. All three are transforms
        of ONE simulated week, so they move together: the widest band's noise
        is not the middle one's, and a reader comparing two bands is reading
        the number he was given against a spread nothing measured"""
        with cheap_monte_carlo():
            out = render("playoffs")
            name = sim.our_roster()[0]["n"]
            full = sim.basis()
            got, = sim.player_title(full, [name],
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
        """An sd on 2 dof carries ~50% of itself as error -- published, it
        reads as a measurement of a spread nobody measured. The row's own
        blocks are what it is computed from, so the count printed above the
        table is the count that ran"""
        out = render("playoffs")
        self.assertGreaterEqual(bracket.TITLE_BLOCKS - 1, 5)
        self.assertIn("averaged over %d shared" % bracket.TITLE_BLOCKS, out)
        with cheap_monte_carlo(4):
            full = sim.basis()
            got, = sim.player_title(full, [sim.our_roster()[0]["n"]],
                                    R=flat_R()).values()
        self.assertEqual(len(got[sim.BANDS[0].label][2]), bracket.TITLE_BLOCKS)

    SUMMARY = re.compile(r"^ +(\d+-\d+) +([\d.]+) +\+-([\d.]+)"
                         r" +([\d.]+)-([\d.]+) +\+-([\d.]+)"
                         r" +(\d+) +([\d.]+) \+-([\d.]+) \(", re.M)

    def test_the_unpaired_band_figures_carry_an_error_bar_too(self):
        """These three sit directly under a table whose every `Delta P` row
        carries a `+-`, and they are the ones that need it most: a `Delta P` is
        a paired difference at matched seeds and the opponent noise cancels out
        of it, while `P(title)` is one unpaired draw of twelve rosters. Bolded
        into `findings.md` bare, they read as the tighter of the two"""
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
        """The bar is measured by re-drawing the whole basis, and the figure
        beside it stays the draw the `mu_us` and `sigma` rows above were printed
        from -- a block mean there would describe a bracket no row on the page
        was built on"""
        out = render("playoffs")
        with cheap_monte_carlo():
            mus = sim.bracket_weeks(sim.basis(), seed0=bracket.SEED0)
            want = [sim.title_prob(mus, b) for b in sim.BANDS]
        for row, band, p in zip(self.SUMMARY.findall(out), sim.BANDS, want):
            with self.subTest(band=band.label):
                self.assertAlmostEqual(float(row[1]), p, places=3)

    def test_the_week_headers_sit_over_the_columns_they_name(self):
        """The four rounds are not interchangeable -- a 1-2 seed never plays
        W20 at all -- so a header shifted or reordered off its own data prints
        one period's points under another's name, and the reader books a
        bracket week the player does not have"""
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
        """28 rows is a list a reader reads the top of. The three bands
        disagree about the order -- which of two bodies matters more depends on
        how many rounds you have to win -- so an order taken off one band and
        announced as another's is a ranking of a question nobody asked"""
        out = render("playoffs")
        self.assertIn("Sorted on the %s band." % sim.BANDS[0].label,
                      one_line(out))
        col = [float(m[5]) for m in self.ROW.findall(out)]
        self.assertEqual(col, sorted(col, reverse=True))

    REG = re.compile(r"^ +reg +([\d.]+) +(\d+) +(\d+) +(\d+) +(\d+) +([\d.]+)"
                     r"  <- one regular period$", re.M)

    def test_the_sigma_column_is_the_level_times_the_spread_the_prose_names(self):
        """Two different opponents are priced on this table. A bracket round
        NAMES both teams, so their levels are in `mu_us` and `mu_opp` already
        and only the week-to-week deviation is left; the `reg` row -- the
        denominator the multiplier beside it divides by -- draws its opponent
        unidentified out of the league and carries that field's level spread on
        top. One spread for both prices a regular season's uncertainty into a
        bracket game, and the multiplier moves with it"""
        out = render("playoffs")
        self.assertIn("%.4f of the level" % sim.MARGIN_CV, out)
        self.assertIn("%.4f. Both off last season's wire" % sim.FIELD_MARGIN_CV,
                      out)
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
        """A band is a SEED RANGE and the figure is the mean over it, so both
        headlines are quoted with the spread they were averaged from and have
        to sit inside it. A headline outside its own range is averaging a
        different set of seeds or rounds from the one the range describes --
        and the range is the column a decision that turns on WHICH seed is
        told to read instead"""
        rows = self.BAND.findall(render("playoffs"))
        self.assertEqual([r[0] for r in rows], [b.label for b in sim.BANDS])
        for row, band in zip(rows, sim.BANDS):
            p, lo, hi, rounds, mult, mlo, mhi = (float(x) for x in row[1:])
            with self.subTest(band=band.label):
                self.assertEqual(rounds, len(band.periods))
                self.assertLessEqual(lo, hi)
                self.assertLessEqual(mlo, mhi)
                # Each end is printed to the headline's own precision, so a
                # tie sits within one rounded step of it.
                self.assertTrue(lo - 0.0005 <= p <= hi + 0.0005,
                                "P(title) %.3f is outside its own %.3f-%.3f"
                                % (p, lo, hi))
                self.assertTrue(mlo - 0.05 <= mult <= mhi + 0.05,
                                "the multiplier %.1f is outside its own "
                                "%.1f-%.1f by round" % (mult, mlo, mhi))

    SENSITIVITY = re.compile(
        r"sigma sensitivity\. The \d+ bracket games actually played give a "
        r"margin sd of (\d+) against the (\d+)-(\d+) above; at that sigma the "
        r"(\S+) band reads ([\d.]+) rather than ([\d.]+)\.")

    def test_the_sigma_sensitivity_reads_against_the_table_it_sits_under(self):
        """The one paragraph on the page that quotes a `P(title)` this run did
        not publish, and it is only readable as a distance from the one it did:
        both the sd it is compared against and the figure it displaces are
        columns printed above it. Sourced anywhere else the reader is handed a
        bound on a run he cannot see, in the direction he cannot check"""
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
        """The half a seed cannot meet before the final is the whole reason
        `mu_opp` is a survivor rather than the field's mean, and this line is
        where a reader checks which half he is in. Printed off anything but
        the ladders the rounds were climbed on, the audit passes on a bracket
        nobody was priced in"""
        halves = re.search(r"draw is seeds (\S+) \| (\S+), each half climbed",
                           one_line(render("playoffs")))
        self.assertIsNotNone(halves)
        self.assertEqual([[int(s) for s in h.split("-")]
                          for h in halves.groups()],
                         [list(l) for l in sim.LADDERS])

    def test_a_counterparty_is_banded_on_his_own_weeks(self):
        """`--roster` has to reach the `P(title)` block and not only the rows.
        A band is the LOADED roster placed at a seed, so a run that prices his
        players and then publishes our title odds under his name reads as a
        rebuilding team a coin flip from a title. He projects outside the
        field entirely here, and every band says so"""
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
