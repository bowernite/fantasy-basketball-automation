import unittest
from tests.harness import *

class TitleReport(unittest.TestCase):
    """The report a roster's actual odds are read off. `playoffs` answers what
    a seed is worth; this one answers what the odds of getting it are"""

    ROW = re.compile(r"^  (roster-\S+ \(.*?\)) +([\d.]+) +([\d.]+)"
                     + r" +([\d.]+)" * 3 + r" +([\d.]+) +\+-([\d.]+)$", re.M)
    SEED = re.compile(r"^ +(\d+|out) +([\d.]+) +([\d.]+|-) +([\d.]+)"
                      r"(?: +([\d.]+))?$", re.M)
    PINNED = re.compile(r"^  (roster-\S+ \(.*?\)) +([\d.]+) +([\d.]+)"
                        r" +([-+][\d.]+) *(.*)$", re.M)

    def title_run(self, seasons):
        """The report's stdout and the projected field it was printed against,
        off ONE draw of the twelve levels -- the field is read inside the block
        so the top eight are the eight the table itself seeded"""
        with cheap_monte_carlo(4, seasons=seasons):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["title"]()
            return buf.getvalue(), [t.path for t in sim.field()]

    def test_every_team_gets_a_row_and_they_sum_to_one_title(self):
        out = render("title")
        rows = {m[0]: m[1:] for m in self.ROW.findall(out)}
        self.assertEqual(len(rows), len(bracket.team_levels()), out)
        self.assertAlmostEqual(sum(float(r[-2]) for r in rows.values()), 1.0,
                               places=2)

    def test_the_band_columns_are_that_row_s_bracket_odds_split_by_seed(self):
        """The footnote under the table: the bands are P(seeded in that range),
        so they sum to `bracket`. A band that is not a partition of the field
        still prints as three probabilities under a total nobody can check --
        and `1-2` is the column a title case is argued off"""
        out = render("title")
        rows = self.ROW.findall(out)
        self.assertEqual(len(rows), len(bracket.team_levels()), out)
        header, = [l for l in out[:out.index("Seeding, priced.")].splitlines()
                   if l.lstrip().startswith("team ")]
        self.assertEqual(re.findall(r"\d+-\d+", header),
                         [b.label for b in sim.BANDS], header)
        for label, wins, made, low, mid, high, title, sd in rows:
            with self.subTest(team=label):
                self.assertAlmostEqual(float(low) + float(mid) + float(high),
                                       float(made), delta=0.002)

    def test_the_seed_decomposition_multiplies_out_to_the_p_title_above_it(self):
        """Its own footnote -- contribution sums to `P(title)` -- and the only
        place the two halves of this report meet: P(seed) comes off the
        standings, P(title | seed) off the bracket, and the headline is their
        product summed. A decomposition that does not recombine says the seed
        channel and the bracket were measured on different seasons"""
        out, _ = self.title_run(400)
        block = out[out.index("seed   P(seed)"):out.index("contribution sums")]
        rows = self.SEED.findall(block)
        self.assertEqual([r[0] for r in rows],
                         [str(s) for s in sorted(
                             s for b in sim.BANDS for s in b.slots)] + ["out"],
                         block)
        self.assertAlmostEqual(sum(float(r[1]) for r in rows), 1.0, delta=0.005)
        for seed, p, conditional, contribution, _ in rows:
            if conditional == "-":
                continue
            with self.subTest(seed=seed):
                self.assertAlmostEqual(float(contribution),
                                       float(p) * float(conditional),
                                       delta=0.003)
        headline, = [m[6] for m in self.ROW.findall(out)
                     if m[0] == roster_mod.label(roster_mod.ROSTER)]
        self.assertAlmostEqual(sum(float(r[3]) for r in rows), float(headline),
                               delta=0.005)

    def test_a_seed_too_few_seasons_reached_prints_no_conditional_at_all(self):
        """P(title | seed 8) off the three seasons this roster was seeded there
        is a number that moves on one bracket, and it prints beside one the
        whole run measured. The threshold and the season count are both on the
        page, so which cells are blank is checkable against the rule -- at 400
        seasons the top seed clears it and the seeds below it do not"""
        seasons = 400
        out, _ = self.title_run(seasons)
        block = out[out.index("seed   P(seed)"):out.index("contribution sums")]
        floor, = re.findall(r"reached fewer than (\d+) times", one_line(out))
        rows = [r for r in self.SEED.findall(block) if r[0] != "out"]
        for seed, p, conditional, _, _ in rows:
            with self.subTest(seed=seed):
                self.assertEqual(conditional == "-",
                                 float(p) * seasons < int(floor))
        self.assertEqual(len({r[2] == "-" for r in rows}), 2,
                         "every seed fell on one side of the threshold, so "
                         "this cannot see the rule -- move the season count")

    def test_the_seeding_table_is_the_gap_between_the_two_runs_it_names(self):
        """`pinned` hands out the projected seeds and `simulated` earns them:
        two models of one season whose whole product is the third column. A
        `delta` that is not their difference, or a `<- loaded` against the wrong
        row, prices the cost of earning a seed for a team nobody asked about"""
        out, _ = self.title_run(400)
        table = out[out.index("Seeding, priced."):]
        rows = self.PINNED.findall(table)
        headline = {m[0]: m[6] for m in self.ROW.findall(out)}
        self.assertEqual(len(rows), len(bracket.team_levels()), table)
        for label, pinned, simulated, delta, _ in rows:
            with self.subTest(team=label):
                self.assertAlmostEqual(float(delta),
                                       float(simulated) - float(pinned),
                                       delta=0.0015)
                self.assertEqual(simulated, headline[label],
                                 "`simulated` is not the P(title) printed for "
                                 "this team in the table above")
        self.assertEqual([r[0] for r in rows if "loaded" in r[4]],
                         [roster_mod.label(roster_mod.ROSTER)], table)

    def test_the_teams_the_projection_leaves_outside_the_field_say_so(self):
        """A 0.000 `pinned` is two different facts: a team seeded 8th that
        never wins the bracket, and a team the projection has 9th, which is not
        in the pinned run at all. Its delta is the whole value of getting in,
        and read as the other it is a rebuild that gains nothing from a season
        that goes right"""
        out, field = self.title_run(400)
        table = out[out.index("Seeding, priced."):]
        rows = self.PINNED.findall(table)
        self.assertEqual(
            {r[0] for r in rows if "outside the field" in r[4]},
            {roster_mod.label(t.path) for t in bracket.team_levels()
             if t.path not in field}, table)

    def test_the_legend_names_probabilities_rather_than_wins(self):
        """`Delta w`'s units are the other reports' and are not this table's:
        every column but one is a probability, and a legend defining wins over
        a table of probabilities is worse than none"""
        legend = one_line("\n".join(render("title").splitlines()[:2]))
        self.assertTrue(legend.startswith("units:"), legend)
        self.assertIn("PROBABILITY", legend)

    def test_it_answers_about_a_counterparty(self):
        """Every team in the league has an unconditional `P(title)` here, so
        `--roster` picks which one the seed decomposition is printed for -- and
        the decomposition is the half of the report that is about one team. Left
        on ours under his name it reads as his seeding, priced"""
        out = render("title", THEIR_ROSTER)
        label = roster_mod.label(THEIR_ROSTER)
        self.assertIn(label, out)
        self.assertIn("%s: P(title)" % label, out)
        table = out[out.index("Seeding, priced."):]
        self.assertEqual([r[0] for r in self.PINNED.findall(table)
                          if "loaded" in r[4]], [label], table)

    def test_a_roster_that_is_not_one_of_the_twelve_is_refused(self):
        """Last season's file, or a hand-built one: the league is the twelve
        files on disk, and a roster outside it has no seed in the draw. Given
        one, the decomposition can only be printed against some other team's
        seed -- under the name of the file that was passed"""
        path = roster_file(*[
            {"n": "Body %d" % i, "tm": "LAC", "avg": 20.0, "tot": 0.0,
             "gp": 60, "posLabel": "F", "elig": ["SF", "PF"]} for i in range(4)])
        with self.assertRaises(KeyError) as e:
            render("title", path)
        self.assertIn(os.path.basename(path), str(e.exception))
        self.assertIn("fetch_data.py roster", str(e.exception))

    def test_the_bar_on_every_row_is_binomial_on_the_seasons_it_printed(self):
        """The docstring above says the bars are binomial on that count and on
        nothing else, and this is the half of it a reader cannot check by
        eye. Nothing in this report re-draws the twelve rosters, so a row's
        spread is its own probability over its own season count -- a bar from
        anywhere else is a precision claim the run did not make"""
        seasons = 400
        out, _ = self.title_run(seasons)
        self.assertIn("%d seasons" % seasons, one_line(out))
        for label, wins, made, low, mid, high, title, sd in self.ROW.findall(out):
            p = float(title)
            with self.subTest(team=label):
                self.assertAlmostEqual(float(sd),
                                       math.sqrt(p * (1 - p) / seasons),
                                       delta=0.001)

    def test_it_prints_the_season_count_its_own_error_bars_are_from(self):
        """The bars on the table are binomial on that count and on nothing
        else, so a count the reader cannot see is a bar he cannot check"""
        with cheap_monte_carlo(4, seasons=137):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["title"]()
        self.assertIn("137 seasons", one_line(buf.getvalue()))

class WeeksReport(unittest.TestCase):
    """`W20`-`W23` alone, for any roster. A rate times NBA games times a GP
    share is arithmetic off the roster file and the schedule, so the columns
    every team eval carries must not cost a bracket Monte Carlo to print"""

    ROW = re.compile(r"^  (\S.*?)" + r" +(\d+/\d+|-)" * 4 + r" *(.*)$", re.M)

    def test_it_prices_a_bracket_week_without_running_the_monte_carlo(self):
        """The whole reason it is a separate report. `playoffs` costs ~350
        simulated seasons for the same four columns, and eleven of twelve evals
        want only the columns"""
        with mock.patch.object(sim.engine, "run",
                               side_effect=AssertionError("ran the sim")):
            out = render("weeks")
        self.assertIn("W20", out)

    def test_every_rostered_player_gets_a_cell_per_bracket_round(self):
        out = render("weeks")
        rows = {m[0]: m[1:] for m in self.ROW.findall(out)}
        ours = sim.our_roster()
        self.assertEqual(set(rows), {p["n"] for p in ours}, out)
        for p in ours:
            if sim.unsigned(p["tm"]) or sim.projected_rate(p["n"]) is None:
                continue
            with self.subTest(player=p["n"]):
                for w, pts in enumerate(sim.week_points(p)):
                    self.assertEqual(rows[p["n"]][w], "%.0f/%d"
                                     % (pts, sim.bracket_games(p["tm"])[w]))

    def test_it_answers_about_a_counterparty(self):
        out = render("weeks", ROOKIE_ROSTER)
        self.assertEqual(
            {m[0] for m in self.ROW.findall(out)},
            {p["n"] for p in sim.our_roster(ROOKIE_ROSTER)}, out)
