import unittest
from tests.harness import *

class MissedSeasonRate(unittest.TestCase):
    """A roster file's rate is `seasonAverage`, which Fleaflicker omits for a
    player who missed the whole season, so his row reads 0.0. The projection is
    the only thing giving him a rate at all, and it has to reach ANY team's
    file, or a team holding Haliburton prices out at his value minus all of it
    """

    def test_a_missed_season_is_priced_off_the_projection(self):
        p, = sim.our_roster(roster_file(
            {"n": "Tyrese Haliburton", "tm": "IND", "avg": 0.0, "tot": 0.0,
             "gp": 0, "posLabel": "G", "elig": ["PG", "SG"]}))
        self.assertGreater(p["avg"], 20)
        self.assertLess(p["avg"], 35)
        self.assertGreater(p["gp"], 45)

class PoolJoinByName(unittest.TestCase):
    """The pool is joined on a NAME, and the board-join rule already says that
    is where accents and punctuation silently drop rows. An ASCII-spelled
    roster file that loses the pool season prices the man off his file row, so
    a whole missed season reads as 0 GP at 0.0 FPts"""

    def test_an_ascii_spelling_finds_the_same_pool_season(self):
        self.assertAlmostEqual(sim.project_gp("Luka Doncic"),
                               sim.project_gp("Luka Dončić"), places=6)

    def test_a_name_in_neither_the_pool_nor_the_call_fails_loudly(self):
        """Returning None, which `our_roster` then rounds, surfaces the failure
        as a TypeError inside `round()` several frames away, if at all"""
        with self.assertRaises(KeyError):
            sim.project_gp("Nobody At All")

class SymmetricProjection(unittest.TestCase):
    """The documented failure mode is projecting our own injured players
    forward while pricing theirs at their worst season. `our_roster` prices ANY
    team's file, so applying the fit there, to every player and with no hand-
    typed GP, is the only thing making that impossible rather than merely
    discouraged"""

    def test_every_player_regresses_toward_the_pool_not_just_a_named_few(self):
        proj = {p["n"]: p["gp"] for p in sim.our_roster()}
        raw = {p["n"]: p["gp"] for p in sim.our_roster(projected=False)}
        self.assertEqual(raw["Desmond Bane"], 82)
        self.assertLess(proj["Desmond Bane"], raw["Desmond Bane"])
        self.assertEqual(raw["Jalen Suggs"], 57)
        self.assertGreater(proj["Jalen Suggs"], raw["Jalen Suggs"])

    def test_a_pooled_players_games_come_off_his_pool_rate(self):
        """The GP fit was fitted on last season's ACTUAL rate, which is what
        the pool carries, so feeding it the projected rate would recalibrate
        every GP figure in the study silently"""
        for p in sim.our_roster():
            if sim.pool_seasons(p["n"]):
                with self.subTest(player=p["n"]):
                    self.assertEqual(p["gp"], round(sim.project_gp(p["n"])))

    def test_the_rate_applies_by_name_not_by_owner(self):
        """A projection keys on the player, so it has to survive him being
        traded. A counterparty's file re-reading last season's average
        regresses his team on a DIFFERENT rule from ours, the asymmetry
        `our_roster` exists to make structurally impossible"""
        def maluach_priced_off(avg):
            p, = sim.our_roster(roster_file(
                {"n": "Khaman Maluach", "tm": "PHX", "avg": avg, "tot": 377.0,
                 "gp": 46, "posLabel": "C", "elig": ["C"]}))
            return p["avg"]

        low, high = maluach_priced_off(8.2), maluach_priced_off(40.0)
        self.assertEqual(low, high)
        self.assertNotIn(low, (8.2, 40.0))

    def test_the_calibration_basis_is_the_season_that_actually_happened(self):
        """`projected=False` stays raw, rate and GP alike, zeros and all. The
        calibration compares the sim against real '25-26 PF at the rates and
        the GP that really occurred, so projecting either there would
        recalibrate the whole study against itself"""
        raw = sim._load(sim.ROSTER)
        self.assertEqual([(p["n"], p["avg"], p["gp"])
                          for p in sim.our_roster(projected=False)],
                         [(p["n"], p["avg"], p["gp"]) for p in raw])

class GPRunsOnTheActualRate(unittest.TestCase):
    """`Eval Definitions §Durability` says **`GP` is projected off last
    season's ACTUAL rate, never the projected one**, since that is the input
    the fit was built on and a projected rate through it recalibrates every
    `GPp` in the study against a variable it never saw.

    Two rates sit on the same roster row, so the wrong one is one keystroke
    away and the substitution is silent, every GP in every table moving with no
    figure on the page saying which variable produced it. `SymmetricProjection`
    guards the CALLER but takes its expectation from `project_gp`'s own
    default, so both sides of that comparison move together. These read the two
    rates apart instead"""

    OURS = "De'Anthony Melton"

    def test_the_games_come_off_the_rate_that_happened_not_the_one_forecast(self):
        actual, _ = sim.pool_seasons(self.OURS)["2025"]
        forecast = sim.projected_rate(self.OURS)
        self.assertLess(forecast, actual - 5)
        p = rostered(self.OURS)

        self.assertEqual(p["gp"], round(sim.project_gp(self.OURS, rate=actual)))
        self.assertGreater(p["gp"],
                           round(sim.project_gp(self.OURS, rate=forecast)) + 2)

    def test_a_counterparty_gets_the_same_games_off_the_same_season(self):
        """§Durability again, regressed **identically on both sides of every
        deal**. A counterparty's file is the only place a row's OWN `avg`/`gp`
        could be read instead of the pool season the fit was built on, which is
        the documented failure exactly, our injured man projected forward while
        theirs is priced at his worst line"""
        ours = rostered(self.OURS)
        theirs, = sim.our_roster(roster_file(
            {"n": self.OURS, "tm": "BKN", "avg": 3.1, "tot": 37.0,
             "gp": 12, "posLabel": "G", "elig": ["PG", "SG"]}))

        self.assertEqual(theirs["gp"], ours["gp"])
        actual, _ = sim.pool_seasons(self.OURS)["2025"]
        self.assertEqual(theirs["gp"], round(sim.project_gp(self.OURS,
                                                            rate=actual)))

    def test_a_whole_missed_season_reaches_back_to_the_last_one_that_happened(self):
        """A missed season is ABSENT from the pool rather than a zero
        (`§Durability`), so the fit's "last season" is the last one that
        exists. His is the row most exposed to the substitution, since his file
        `avg` is 0.0 and the projection is the only rate on it, while the
        actual he has to be fitted on is two years back and nowhere on the page
        """
        name = "Fred VanVleet"
        self.assertIn("miss", sim.evidence_flags(name))
        self.assertNotIn("2025", sim.pool_seasons(name))
        raw = rostered(name, projected=False)
        self.assertEqual((raw["avg"], raw["gp"]), (0.0, 0))

        actual, _ = sim.pool_seasons(name)["2024"]
        forecast = sim.projected_rate(name)
        p = rostered(name)

        self.assertEqual(p["gp"], round(sim.project_gp(name, rate=actual)))
        self.assertGreater(p["gp"], round(sim.project_gp(name, rate=forecast)) + 4)

    def test_a_row_the_pool_never_saw_is_fitted_on_the_actual_line_it_carries(self):
        """`nopool` is not only rookies. The pool is a separate scrape from the
        roster fetch and the join is by NAME, so an established player lands
        here with last season's actual line sitting on his file row. The fit
        has its input right there, and reaching past it for the forecast is the
        substitution §Durability forbids, on rows already flagged as the
        thinnest evidence in the study.

        A true rookie is the only row with no actual rate anywhere, and only
        there is the projection a defensible fallback (`NoPoolHistory`)"""
        name = "Vasilije Micić"
        self.assertEqual(sim.evidence_flags(name), ["nopool"])
        self.assertLess(sim.projected_rate(name), 15)

        p, = sim.our_roster(roster_file(
            {"n": name, "tm": "PHX", "avg": 21.5, "tot": 946.0,
             "gp": 44, "posLabel": "G", "elig": ["PG", "SG"]}))

        self.assertEqual(p["gp"], round(sim.project_gp(name, gp=44, rate=21.5)))

    def test_no_row_on_any_roster_is_fitted_on_the_forecast(self):
        """The class the cases above are drawn from. Every kind of player a
        roster can hold, long history, thin, fragment, a missed year,
        unprojected, unsigned, none at all, goes through the one `our_roster`,
        on ours and on a counterparty's alike, so a sweep is the only thing
        that says the rule holds for the rows nobody thought to name"""
        moved = 0
        for path in (None, THEIR_ROSTER, ROOKIE_ROSTER):
            raw = sim.our_roster(path, projected=False)
            self.assertGreater(len(raw), 20)
            for before, after in zip(raw, sim.our_roster(path)):
                n = before["n"]
                seasons = sim.pool_seasons(n)
                if seasons:
                    actual = (seasons.get("2025") or seasons[max(seasons)])[0]
                    gp_from_file = {}
                else:
                    actual = before["avg"]
                    gp_from_file = {"gp": before["gp"]}
                if not actual:
                    continue                     # a rookie, no actual rate exists
                forecast = sim.projected_rate(n)
                with self.subTest(roster=path or "ours", player=n):
                    self.assertEqual(
                        after["gp"],
                        round(sim.project_gp(n, rate=actual, **gp_from_file)))
                if forecast is not None and round(sim.project_gp(
                        n, rate=forecast, **gp_from_file)) != after["gp"]:
                    moved += 1
        self.assertGreater(moved, 15)

    def test_the_games_on_the_printed_row_are_the_projected_ones(self):
        """`Eval Definitions §Columns` says the `gp` a `players` row prints is
        `GPp`, the projection `Δw` runs on, and an eval copies it into the
        published table beside last season's actual `GP`. Raw and projected are
        the same field name one call apart, so a table rendered off the file
        prints last season's under the projected heading, and for a man who
        missed the year that is a bare 0 next to a real `Δw`. Every other test
        here stops at the roster row, which is not what anybody reads"""
        table = render("players")
        for name in ("Fred VanVleet", "Cade Cunningham"):
            raw = rostered(name, projected=False)
            p = rostered(name)
            self.assertNotEqual(raw["gp"], p["gp"])
            row, = [l for l in table.splitlines() if l.startswith("  " + name)]
            printed, = re.findall(r"[\d.]+ +(\d+) +\S+ +[-+][\d.]+", row)
            self.assertEqual(int(printed), p["gp"], row)
