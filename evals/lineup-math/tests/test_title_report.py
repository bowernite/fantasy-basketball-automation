import unittest
from tests.harness import *

class TitleReport(unittest.TestCase):
    ROW = re.compile(r"^  (roster-\S+ \(.*?\)) +([\d.]+) +([\d.]+)"
                     + r" +([\d.]+)" * 3 + r" +([\d.]+) +\+-([\d.]+)$", re.M)
    SEED = re.compile(r"^ +(\d+|out) +([\d.]+) +([\d.]+|-) +([\d.]+)"
                      r"(?: +([\d.]+))?$", re.M)
    PINNED = re.compile(r"^  (roster-\S+ \(.*?\)) +([\d.]+) +([\d.]+)"
                        r" +([-+][\d.]+) *(.*)$", re.M)

    def title_run(self, seasons):
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
        out, field = self.title_run(400)
        table = out[out.index("Seeding, priced."):]
        rows = self.PINNED.findall(table)
        self.assertEqual(
            {r[0] for r in rows if "outside the field" in r[4]},
            {roster_mod.label(t.path) for t in bracket.team_levels()
             if t.path not in field}, table)

    def test_the_checks_block_prints_the_wire_spread_it_compares_against(self):
        out, _ = self.title_run(400)
        m = re.search(r"standings spread: sim sd ([\d.]+), wire ([\d.]+)", out)
        self.assertIsNotNone(m, out)
        self.assertAlmostEqual(float(m.group(2)),
                               title.win_spread(spread=0.0)[1], places=2)

    def test_it_answers_about_a_counterparty(self):
        out = render("title", THEIR_ROSTER)
        label = roster_mod.label(THEIR_ROSTER)
        self.assertIn(label, out)
        self.assertIn("%s: P(title)" % label, out)
        table = out[out.index("Seeding, priced."):]
        self.assertEqual([r[0] for r in self.PINNED.findall(table)
                          if "loaded" in r[4]], [label], table)

    def test_a_roster_that_is_not_one_of_the_twelve_is_refused(self):
        path = roster_file(*[
            {"n": "Body %d" % i, "tm": "LAC", "avg": 20.0, "tot": 0.0,
             "gp": 60, "posLabel": "F", "elig": ["SF", "PF"]} for i in range(4)])
        with self.assertRaises(KeyError) as e:
            render("title", path)
        self.assertIn(os.path.basename(path), str(e.exception))
        self.assertIn("fetch_data.py roster", str(e.exception))

    def test_the_bar_on_every_row_is_binomial_on_the_seasons_it_printed(self):
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
        with cheap_monte_carlo(4, seasons=137):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["title"]()
        self.assertIn("137 seasons", one_line(buf.getvalue()))

class WeeksReport(unittest.TestCase):
    ROW = re.compile(r"^  (\S.*?)" + r" +(\d+/\d+|-)" * 4 + r" *(.*)$", re.M)

    def test_it_prices_a_bracket_week_without_running_the_monte_carlo(self):
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
