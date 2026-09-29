import unittest
from tests.harness import *
from simlib import future, progression as prog


TEAMS = ["T%02d" % i for i in range(1, 13)]


class DraftOrder(unittest.TestCase):
    def test_the_top_four_by_record_pick_last_in_reverse(self):
        order = future.draft_order(TEAMS, random.Random(1))
        self.assertEqual(order[8:], ["T04", "T03", "T02", "T01"])

    def test_only_the_top_pick_is_drawn_among_the_worst_four_at_50_25_15_10(self):
        n, wins = 8000, collections.Counter()
        for s in range(n):
            order = future.draft_order(TEAMS, random.Random(s))
            wins[order[0]] += 1
            self.assertEqual(order[4:8], ["T08", "T07", "T06", "T05"])
            self.assertEqual([t for t in order[:4] if t != order[0]],
                             [t for t in ["T12", "T11", "T10", "T09"] if t != order[0]])
        for team, odds in zip(["T12", "T11", "T10", "T09"], (0.50, 0.25, 0.15, 0.10)):
            self.assertAlmostEqual(wins[team] / n, odds, delta=0.02)
        self.assertEqual(sum(wins.values()), n)


def vet(name, rate=20.0, base=500, rates=None):
    return {"n": name, "tm": "BOS", "elig": ["SF", "PF"], "base": base,
            "rates": rates or [rate, rate, rate], "gps": [60.0, 60.0, 60.0]}


def draft_class():
    """48 rookies, best first, shaped like a real class: FP/G falls with the ordinal"""
    return [{"n": "Rookie %d" % k, "name": "Rookie %d" % k, "tm": "SAC", "elig": ["PG", "SG"],
             "base": 3000 - 60 * k, "rate1": 30.0 - 0.5 * k, "gp1": 60.0, "age1": 20.0,
             "age_rookie": 20.0, "stage": "D", "cy1": 1, "pick": k, "bpm": None,
             "gp_last": None} for k in range(1, 49)]


def small_league(size=20):
    return {t: [vet("%s vet %d" % (t, i)) for i in range(size)] for t in TEAMS}


def rookies(roster, rnd):
    """{slot: year-2 FP/G} of the round-`rnd` rookies on a roster"""
    out = {}
    for p in roster:
        m = re.match(r"'27 %d\.(\d\d)$" % rnd, p["n"])
        if m:
            out[int(m.group(1))] = p["rates"][1]
    return out


class PicksLand(unittest.TestCase):
    LEDGER = {(2027, 1, "T12"): "T06"}

    def test_a_held_first_lands_where_its_original_team_finished(self):
        worst, _ = future.offseason(small_league(), 0, TEAMS, self.LEDGER, draft_class(), "t", years=3)
        best, _ = future.offseason(small_league(), 0, ["T12"] + TEAMS[:11], self.LEDGER,
                                   draft_class(), "t", years=3)
        when_worst, when_best = rookies(worst["T06"], 1), rookies(best["T06"], 1)
        self.assertEqual(len(when_worst), 2)
        self.assertIn(7, when_worst)
        tail_pick = min(when_worst)
        self.assertLessEqual(tail_pick, 4)
        self.assertEqual(sorted(when_best), [6, 12])
        self.assertGreater(when_worst[tail_pick], when_best[12])

    def test_a_pick_traded_away_adds_no_body_to_its_original_team(self):
        after, _ = future.offseason(small_league(), 0, TEAMS, self.LEDGER, draft_class(), "t", years=3)
        self.assertEqual(rookies(after["T12"], 1), {})
        self.assertEqual(len(after["T12"]), 20 + 3)
        self.assertEqual(len(after["T06"]), 20 + 5)
        self.assertEqual(sum(len(r) for r in after.values()), 12 * 20 + 48)


class FullRosters(unittest.TestCase):
    def test_a_full_roster_cuts_its_lowest_score_bodies_and_exits_leave_first(self):
        league = small_league()
        league["T06"] = ([vet("regular %d" % i) for i in range(34)]
                         + [vet("retiring", rates=[20.0, None, None])]
                         + [vet("fodder %d" % i, rate=12.0, base=0) for i in range(3)])
        after, flow = future.offseason(league, 0, TEAMS, {}, draft_class(), "t", years=3)
        names = {p["n"] for p in after["T06"]}
        self.assertEqual(len(after["T06"]), future.MAX_BODIES)
        self.assertFalse(names & {"retiring", "fodder 0", "fodder 1", "fodder 2"})
        self.assertEqual(len([n for n in names if n.startswith("'27")]), 4)
        self.assertEqual((flow["T06"]["exits"], flow["T06"]["rookies"], flow["T06"]["cuts"]), (1, 4, 3))
        self.assertEqual(flow["T01"]["cuts"], 0)


class SampledSeason(unittest.TestCase):
    def test_one_sampled_season_ranks_every_team_once_and_better_teams_finish_higher(self):
        with cheap_monte_carlo():
            teams = bracket.team_levels()
            best, worst = teams[0].path, teams[-1].path
            firsts, lasts = collections.Counter(), collections.Counter()
            for seed in range(300):
                order = title.sampled_standings(teams, seed)
                self.assertEqual(sorted(order), sorted(t.path for t in teams))
                firsts[order[0]] += 1
                lasts[order[-1]] += 1
        self.assertEqual(firsts.most_common(1)[0][0], best)
        self.assertEqual(lasts.most_common(1)[0][0], worst)


class Report(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from simlib.reports import future as rep
        cls.last = os.path.join(tempfile.mkdtemp(), "last.json")
        cls.out = []
        with cheap_monte_carlo(), mock.patch.object(rep, "LAST", cls.last):
            for _ in range(2):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rep.report_future()
                cls.out.append(buf.getvalue())
        with open(cls.last) as f:
            cls.saved = json.load(f)

    def test_every_season_crowns_exactly_one_champion(self):
        teams = self.saved["teams"].values()
        for y in range(len(self.saved["years"])):
            self.assertAlmostEqual(sum(t["title"][y] for t in teams), 1.0, places=9)

    def test_every_draft_hands_out_all_48_picks(self):
        for y in range(len(self.saved["drafts"])):
            self.assertEqual(sum(sum(t["picks"][y]) for t in self.saved["teams"].values()), 48)

    def test_every_draft_slots_each_original_teams_pick_exactly_once_per_path(self):
        teams = self.saved["teams"].values()
        for y in range(len(self.saved["drafts"])):
            for t in teams:
                self.assertEqual(sum(t["own_slots"][y]), self.saved["paths"])
            for slot in range(12):
                self.assertEqual(sum(t["own_slots"][y][slot] for t in teams), self.saved["paths"])

    def test_each_original_teams_printed_slot_band_is_its_drawn_slots_less_the_tails(self):
        from simlib.reports import future as rep
        section = self.out[0].split("\nOwn-pick slot band")[1].split("\n\n")[0]
        lines = section.splitlines()
        header = next(i for i, line in enumerate(lines) if line.split()[:1] == ["team"])
        rows = {line.split()[0]: line.split()[1:] for line in lines[header + 1:]}
        self.assertEqual(sorted(rows), sorted(self.saved["teams"]))
        for owner, t in self.saved["teams"].items():
            for y, hist in enumerate(t["own_slots"]):
                self.assertEqual(rows[owner][2 * y], "1.%02d-1.%02d" % rep.slot_band(hist))

    def test_a_re_run_on_the_same_inputs_is_identical_and_says_so(self):
        table = lambda text: text.split("\nΔ")[0].split("ran in")[0].rstrip()
        self.assertEqual(table(self.out[0]), table(self.out[1]))
        self.assertIn("same as the last run", self.out[1])


class SlotBand(unittest.TestCase):
    def test_the_band_drops_up_to_a_tenth_of_paths_off_each_end(self):
        from simlib.reports import future as rep
        self.assertEqual(rep.slot_band([60, 0, 0, 0, 480, 0, 0, 0, 0, 0, 0, 60]), (5, 5))
        self.assertEqual(rep.slot_band([61, 0, 0, 0, 479, 0, 0, 0, 0, 0, 0, 60]), (1, 5))


def entry(name, gp, rate=35.0, age=26.0):
    row = {"n": name, "tm": "BOS", "avg": rate, "gp": gp, "elig": ["PG", "SG"]}
    pl = {"name": name, "rate1": rate, "gp1": float(gp), "age1": age, "stage": "V", "cy1": 5,
          "bpm": 2.0, "gp_last": 60.0, "pick": 10, "age_rookie": age - 4}
    return {"row": row, "pl": pl, "base": 2000}


class GamesPlayed(unittest.TestCase):
    def test_season_one_plays_the_games_the_model_expects_after_last_season_not_the_projections(self):
        sampler = prog.Sampler(prog.params())
        e = entry("durable", 72)
        q = future.player(e, sampler, "gp", 3)
        self.assertAlmostEqual(q["gps"][0], sampler.gp_expected(60.0, 25.0, 35.0))
        self.assertLess(q["gps"][0], 70)

    def test_a_season_projected_lost_to_injury_stays_lost(self):
        q = future.player(entry("hurt", 0), prog.Sampler(prog.params()), "gp", 3)
        self.assertEqual(q["gps"][0], 0)

    def test_a_player_the_model_cannot_place_plays_season_one_and_leaves(self):
        e = dict(entry("no birthday", 50), pl=None)
        q = future.player(e, prog.Sampler(prog.params()), "gp", 3)
        self.assertEqual(q["rates"], [35.0, None, None])

    def test_a_projection_after_a_season_lost_to_injury_stands(self):
        e = entry("back from injury", 70)
        e["pl"]["gp_last"] = 12.0
        self.assertEqual(future.player(e, prog.Sampler(prog.params()), "gp", 3)["gps"][0], 70)

    def test_a_projection_below_the_models_forecast_is_known_absence_and_stands(self):
        q = future.player(entry("out till January", 30), prog.Sampler(prog.params()), "gp", 3)
        self.assertEqual(q["gps"][0], 30)

    def test_a_drafted_rookie_plays_his_first_season_on_the_models_basis_too(self):
        sampler = prog.Sampler(prog.params())
        rookies_72 = [dict(r, gp1=72.0) for r in draft_class()]
        after, _ = future.offseason(small_league(), 0, TEAMS, {}, rookies_72, "t", years=3)
        first = next(p for p in after["T12"] if p["n"].startswith("'27 1."))
        slot = int(first["n"][-2:])
        tpl = rookies_72[slot - 1]
        self.assertAlmostEqual(first["gps"][1], sampler.gp_expected(sampler.gp_ref, tpl["age1"] - 1, tpl["rate1"]))
