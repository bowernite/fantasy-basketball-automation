"""python3 -m unittest test_sim -v"""
import collections
import contextlib
import glob
import importlib
import io
import json
import math
import os
import random
import re
import runpy
import statistics
import subprocess
import sys
import tempfile
import unittest

import fetch_data
import sim
from simlib import engine, gp, roster as roster_mod, value
from simlib.reports import durability

THEIR_ROSTER = "roster-161020-2025-26.json"
ROOKIE_ROSTER = "roster-160941-2025-26.json"
THREE_OUT = ["Jalen Suggs", "Coby White", "Myles Turner"]
SNAPSHOT = os.path.join(sim.HERE, os.pardir, "board-snapshots", "projections",
                        "sleeper-2026.json")


@contextlib.contextmanager
def cheap_monte_carlo(trials=4, blocks=1):
    """A trial count that answers whether a report runs, not what it says

    These three bind their sample size as a default at import, so lowering
    `TRIALS` alone changes nothing. Patched on the module that defines each
    one, since `sim` forwards them both ways
    """
    real_run, real_wins, real_boot = (engine.run, value.player_wins,
                                      gp.gp_bootstrap)
    was_blocks = value.PLAYER_BLOCKS
    engine.run = lambda roster, **kw: real_run(roster, **dict(kw, trials=trials))
    value.player_wins = lambda roster, names, **kw: real_wins(
        roster, names, **dict(kw, trials=trials))
    gp.gp_bootstrap = lambda rows, **kw: real_boot(rows, **dict(kw, n=50))
    value.PLAYER_BLOCKS = blocks
    try:
        yield
    finally:
        engine.run, value.player_wins, gp.gp_bootstrap = (real_run, real_wins,
                                                          real_boot)
        value.PLAYER_BLOCKS = was_blocks


@contextlib.contextmanager
def recorded_rosters(trials=2):
    """Every roster `engine.run` is handed while the block runs, by name. Which
    bodies a column was priced on is not visible in the number it returns,
    since two bottom-grade rooms are under the noise apart"""
    seen, real = [], engine.run
    engine.run = lambda roster, **kw: (
        seen.append([p["n"] for p in roster]),
        real(roster, **dict(kw, trials=trials)))[1]
    try:
        yield seen
    finally:
        engine.run = real


@contextlib.contextmanager
def projection_snapshot(text):
    """Points `projections` at a snapshot file we wrote and lets the sim read
    it through its own loader, scorer and name join, so the file on disk is the
    only thing stubbed. `text=None` points it at a path with nothing on it"""
    sleeper = skill_module("projections", "sleeper")
    path = os.path.join(tempfile.mkdtemp(), "sleeper-2026.json")
    if text is not None:
        with open(path, "w") as f:
            f.write(text)
    was, sleeper.SNAPSHOT = sleeper.SNAPSHOT, path
    sim._projections.cache_clear()
    try:
        yield
    finally:
        sleeper.SNAPSHOT = was
        sim._projections.cache_clear()


def sleeper_rows(*lines):
    """A snapshot payload, in the feed's own shape"""
    return json.dumps({"season": "2026", "source": "test", "updated": 0,
                       "depth": len(lines),
                       "rows": [{"name": n, "updated": 0, "stats": s}
                                for n, s in lines]})


def roster_file(*rows):
    """A one-off roster file in the shape `fetch_data.py roster` writes, the
    only way to hand `our_roster` a row no committed file carries"""
    path = os.path.join(tempfile.mkdtemp(), "theirs.json")
    with open(path, "w") as f:
        json.dump(list(rows), f)
    return path


def committed_rosters():
    """Every roster file in the tree. The league is 12 and they are re-cut with
    `fetch_data.py roster <id>`, so the set is the directory's to state"""
    return sorted(glob.glob(os.path.join(sim.HERE, "roster-*.json")))


def rostered(name, path=None, projected=True):
    """His row on a loaded roster, exactly one or the unpacking says so"""
    p, = [q for q in sim.our_roster(path, projected=projected)
          if q["n"] == name]
    return p


def season_value(p):
    """Rate x games, the whole season of production a body supplies"""
    return p["avg"] * p["gp"]


def flat_R(rate=15.0):
    """One replacement level for all three slot groups, for a test whose
    subject is not which group a body lands in"""
    return dict.fromkeys(sim.GROUPS, rate)


def skills_path(*parts):
    return os.path.join(sim.HERE, os.pardir, os.pardir, ".claude", "skills",
                        *parts)


def skill_module(skill, name):
    path = skills_path(skill)
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module(name)


def read_text(path):
    with open(path) as f:
        return f.read()


def one_line(text):
    """Single-spaced, so a sentence can be matched across the wraps it is
    printed or written in"""
    return " ".join(text.split())


def render(report, roster=None):
    """The stdout of one report, driven the way `__main__` drives it.
    `roster_mod` is where `basis` reads the default path from, so this sets it
    there"""
    was = roster_mod.ROSTER
    if roster:
        roster_mod.ROSTER = roster
    buf = io.StringIO()
    try:
        with cheap_monte_carlo(), contextlib.redirect_stdout(buf):
            sim.REPORTS[report]()
    finally:
        roster_mod.ROSTER = was
    return buf.getvalue()


def cli(*args):
    """One `python3 sim.py ...`, argv parsing and all, without the process

    Returns (exit status, everything the run said). `sim.py` exits with its
    explanation as the status, so that text is folded into the output too
    """
    was_argv, was_roster = sys.argv, roster_mod.ROSTER
    sys.argv = ["sim.py"] + list(args)
    buf, status = io.StringIO(), 0
    try:
        with cheap_monte_carlo(), contextlib.redirect_stdout(buf):
            runpy.run_path(sim.__file__, run_name="__main__")
    except SystemExit as e:
        status = e.code
    finally:
        sys.argv, roster_mod.ROSTER = was_argv, was_roster
    return status, buf.getvalue() + (status if isinstance(status, str) else "")


def sim_process(*args):
    """One real `python3 sim.py ...`, real interpreter, real argv, real exit
    status, at the published trial counts. The paths worth this are the ones
    `cli` cannot reach, how the command behaves as it is actually typed"""
    return subprocess.run([sys.executable, "sim.py"] + list(args),
                          cwd=sim.HERE, capture_output=True, text=True)


def roster_payload(**over):
    """One `FetchRoster?season=` row, trimmed to the keys the transform reads.
    Fleaflicker omits zero and default fields entirely, so the shape that bites
    is a row with no `seasonAverage`, `seasonTotal` or `rankFantasy` at all"""
    row = {"proPlayer": {"nameFull": "Darius Garland", "position": "G",
                         "proTeamAbbreviation": "LAC",
                         "positionEligibility": ["PG", "SG"]},
           "seasonAverage": {"value": 31.894444},
           "seasonTotal": {"value": 1435.25},
           "rankFantasy": {"positions": [
               {"position": {"eligibility": ["PG"]}},
               {"position": {"eligibility": ["SG"]}}]}}
    row.update(over)
    return {"groups": [{"slots": [{}, {"leaguePlayer": row}]}]}


class FetchRosterTransform(unittest.TestCase):
    """`--roster their.json` is advertised for any counterparty, so the row
    shape `fetch_data` writes is what makes `REPL theirs` reproducible.
    Asserted rather than described"""

    def test_a_played_season_becomes_a_priceable_roster_row(self):
        self.assertEqual(fetch_data.roster_rows(roster_payload()),
                         [{"n": "Darius Garland", "tm": "LAC",
                           "avg": 31.894444, "tot": 1435.25, "gp": 45,
                           "posLabel": "G", "elig": ["PG", "SG"]}])

    def test_a_player_who_missed_the_whole_season_still_carries_his_positions(self):
        """A 0-GP row has no `seasonAverage`, so it has no `rankFantasy`
        either, which is how a player reaches the roster file with `elig: []`
        and gets guessed at as a guard. `positionEligibility` is on the row
        whether or not he played"""
        p = roster_payload(proPlayer={"nameFull": "Kyrie Irving", "position": "G",
                                      "proTeamAbbreviation": "DAL",
                                      "positionEligibility": ["PG", "SG"]})
        del p["groups"][0]["slots"][1]["leaguePlayer"]["seasonAverage"]
        del p["groups"][0]["slots"][1]["leaguePlayer"]["seasonTotal"]
        del p["groups"][0]["slots"][1]["leaguePlayer"]["rankFantasy"]
        self.assertEqual(fetch_data.roster_rows(p),
                         [{"n": "Kyrie Irving", "tm": "DAL", "avg": 0.0,
                           "tot": 0.0, "gp": 0, "posLabel": "G",
                           "elig": ["PG", "SG"]}])


class CommittedRosterFiles(unittest.TestCase):
    """The twelve files are the counterparty flow's input and get re-cut with
    `fetch_data.py roster <id>` after every trade. A re-fetch that drops a
    team's positions prices that whole roster on guesses, and no report
    refuses, it fills slots with what it was given"""

    def test_every_committed_file_carries_the_eligibility_it_is_priced_on(self):
        """Asserted on the file rather than on the loaded row, because
        `our_roster` FILLS an empty `elig` from the one-letter `posLabel`, so a
        dropped "SF" comes back as PG/SG and every table still prints. The loss
        is only visible before the guess"""
        slots = {pos for elig in sim.GROUPS.values() for pos in elig}
        files = committed_rosters()
        self.assertGreaterEqual(len(files), 12, "a league of 12 has 12 rosters")
        for path in files:
            rows = json.loads(read_text(path))
            with self.subTest(roster=os.path.basename(path)):
                self.assertGreaterEqual(len(rows), 20, "a fragment, not a team")
                for r in rows:
                    self.assertTrue(r["elig"], "%s has no slot to fill" % r["n"])
                    self.assertLessEqual(set(r["elig"]), slots, r["n"])

    def test_every_committed_file_loads_into_bodies_that_price(self):
        """The other half. A body carrying neither a rate nor a games count
        plays 82 nights at nothing and drags the roster's own R down with it"""
        for path in committed_rosters():
            rows = sim.our_roster(os.path.basename(path))
            with self.subTest(roster=os.path.basename(path)):
                for p in rows:
                    self.assertGreater(p["avg"], 0, "%s prices as nothing" % p["n"])
                    self.assertTrue(0 < p["gp"] <= 82, "%s: %s gp" % (p["n"], p["gp"]))


class EmptyRosterFile(unittest.TestCase):
    """A fetch that reached nobody writes `[]`, and `basis` PADS that to 38
    auction-grade bodies. Every figure below it, replacement level above all,
    then comes out measured on pure filler under the file's name. The only
    thing that shows it is the table's own row count, and a reader looking at R
    is not counting rows"""

    def test_a_file_with_nobody_on_it_is_refused_instead_of_padded_into_a_team(self):
        p = sim_process("--roster", roster_file(), "players")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("wins lost if swapped", p.stdout)

    def test_the_refusal_names_the_file_that_carried_nobody(self):
        """The import path (`trades` step 5) reaches the same padding with no
        banner above it at all, and the file it was handed is the only thing
        telling the caller which of the twelve to re-fetch"""
        path = roster_file()
        with self.assertRaises(ValueError) as e:
            sim.basis(path)
        self.assertIn(path, str(e.exception))


class CLI(unittest.TestCase):
    def test_a_misspelled_report_name_fails_instead_of_printing_another_one(self):
        """`trades` and `eval-team` both mandate a sim run before recommending
        a deal. A silent fallback to `calibration` means `sim.py breakeven`
        exits 0 having printed a table the reader did not ask for, and he books
        it as the break-evens he thinks he just ran"""
        p = sim_process("breakeven")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("CALIBRATION", p.stdout)
        for name in sim.REPORTS:
            self.assertIn(name, p.stdout + p.stderr)

    def test_the_roster_flag_reaches_the_report_it_precedes(self):
        """`render` puts the path on `roster_mod` itself, so nothing it covers
        touches the flag parsing that is supposed to put a counterparty's file
        there. A `--roster` that quietly kept OUR file prints our players under
        his team's name, and `Δw theirs` is the one number the counterparty
        workflow exists to produce"""
        status, out = cli("--roster", THEIR_ROSTER, "players")
        self.assertEqual(status, 0, out)
        self.assertIn(THEIR_ROSTER, out, "the run has to name the file it priced")
        theirs = {p["n"] for p in sim.our_roster(THEIR_ROSTER)}
        for name in sorted(theirs):
            self.assertIn(name, out)
        for name in sorted({p["n"] for p in sim.our_roster()} - theirs):
            self.assertNotIn(name, out)

    def test_a_bad_name_beside_a_good_one_runs_neither(self):
        """Same booking hazard as a lone misspelling, one step later. `sim.py
        players breakeven` printing PLAYERS and then dying leaves a table on
        screen from a command that exited 1, and the reader quotes it as the
        run he asked for"""
        status, out = cli("players", "bogus")
        self.assertNotEqual(status, 0)
        self.assertNotIn("PLAYERS", out)

    def test_every_report_named_in_one_run_prints(self):
        """The README advertises the reports on one line, so a run that takes
        the first name and drops the rest answers half of what was asked with
        no sign that it did"""
        status, out = cli("nights", "formula")
        self.assertEqual(status, 0, out)
        self.assertIn("NIGHTS", out)
        self.assertIn("FORMULA", out)


class EveryReportRunsEndToEnd(unittest.TestCase):
    """A report that names the players it trades as literals breaks the moment
    the roster file is re-cut, and every unit underneath it stays green. The
    file is re-cut after every trade, so that is a standing hazard for any
    report holding a name, which is what makes all twelve worth paying for"""

    def test_every_report_runs_on_our_roster(self):
        for name in sorted(sim.REPORTS):
            with self.subTest(report=name):
                self.assertTrue(render(name).strip(), "printed nothing")

    def test_every_report_not_scoped_to_us_runs_on_a_counterparty_roster(self):
        """The other half of the same hazard. A counterparty's file is a
        DIFFERENT shape, 26 bodies not 28, unsigned players, whole seasons
        missing, none of our names, and `--roster` is advertised for any of
        them"""
        for name in sorted(set(sim.REPORTS) - sim.OURS_ONLY):
            with self.subTest(report=name):
                self.assertTrue(render(name, THEIR_ROSTER).strip(),
                                "printed nothing")


class OptimalLineup(unittest.TestCase):
    """"Lineups are set optimally every night" is the premise under every PF
    figure here, and what lets the README call absolute PF an UPPER bound.
    Greedy placement with Kuhn augmentation is only exact because capacities
    are 1 and players are added in descending value, and a matching that misses
    a swap loses points on exactly the crowded nights the study is about"""

    def best_possible(self, avail):
        """The optimum by dynamic programming over subsets of the 9 slots, a
        different algorithm from the augmenting placement `lineup` uses"""
        dp = {0: 0.0}
        for val, elig, _ in avail:
            nxt = dict(dp)
            for mask, total in dp.items():
                for si, (_, slot) in enumerate(sim.SLOTS):
                    bit = 1 << si
                    if mask & bit or not elig & slot:
                        continue
                    if total + val > nxt.get(mask | bit, -1.0):
                        nxt[mask | bit] = total + val
            dp = nxt
        return max(dp.values())

    def test_no_other_legal_lineup_scores_more(self):
        """On real nights, not toy ones. The bodies and eligibilities are drawn
        from the 38-man roster, at the sizes `nights` says the cap actually
        bites on"""
        roster = sim.basis()
        rng = random.Random(3)
        for case in range(30):
            up = rng.sample(roster, rng.randint(4, 18))
            avail = [(p["avg"], set(p["elig"]), i) for i, p in enumerate(up)]
            with self.subTest(case=case, n=len(up)):
                total, filled, who = sim.lineup(avail)
                self.assertEqual(len(who), len(set(who)))
                self.assertEqual(filled, len(who))
                self.assertLessEqual(filled, len(sim.SLOTS))
                self.assertAlmostEqual(total, self.best_possible(avail), places=6)

    def test_a_body_with_no_legal_slot_left_does_not_start(self):
        """The positional half of the 9-slot cap. A pure centre reaches C and
        the two ANY slots and no further, so the 4th-best centre on the roster
        scores nothing however good he is"""
        centres = [(float(40 - i), {"C"}, i) for i in range(12)]
        total, filled, who = sim.lineup(centres)
        self.assertEqual(filled, sim.group_slots(("C",)))
        self.assertEqual(sorted(who), [0, 1, 2])
        self.assertEqual(total, 40 + 39 + 38)


class Schedule(unittest.TestCase):
    """Every conclusion is a count of slot-nights, so a phantom game is a
    phantom night of value"""

    def test_every_team_plays_82_games(self):
        played = collections.Counter()
        for _, tms in sim.NIGHTS:
            for t in tms:
                played[t] += 1
        # the NBA Cup final is an 83rd game for its two participants
        self.assertEqual(sorted(collections.Counter(played.values()).items()),
                         [(82, 28), (83, 2)])


class FantasyCalendar(unittest.TestCase):
    """Weekly scores are the unit a matchup is won in, so how nights bucket
    into periods is not cosmetic"""

    def test_games_per_period_matches_the_real_spread(self):
        """Real periods carry 28-56 NBA games. An even split of nights across
        periods implies ~49-56 and erases most of the weekly variance the sim
        exists to explain"""
        games = collections.Counter()
        for (_, tms), w in zip(sim.NIGHTS, sim.WEEK_OF):
            if w is not None:
                games[w] += len(tms) // 2
        self.assertEqual((min(games.values()), max(games.values())), (28, 56))


def light_nights_per_team():
    """{team: the light nights it plays}, the table `schedules` prints and the
    quantity every coverage bound is read off. Derived rather than a literal,
    since the deepest and emptiest schedules move with the calendar every
    season"""
    return {t: len(sim.team_light_nights(t)) for t in sim.NBA_TEAMS}


class LightNights(unittest.TestCase):
    """The nights the 9-slot cap binds on, and the only nights a schedule
    choice can pay on. The fantasy season ENDS before the NBA's, so a team
    whose light nights sit in April has none that count"""

    def test_light_nights_outside_the_scored_periods_are_dropped(self):
        whole = [i for i, (_, tms) in enumerate(sim.NIGHTS)
                 if len(tms) // 2 <= sim.LIGHT_GAMES]
        self.assertLess(len(sim.light_nights()), len(whole))
        self.assertTrue(set(sim.light_nights()) <= set(sim.SCORING_NIGHTS))

    def test_every_team_spelling_in_the_feed_finds_a_real_schedule(self):
        """The roster feed and the NBA schedule spell teams differently,
        SAS/NYK/UTA against SA/NY/UTAH, so all 30 resolve only through
        `FF2ESPN` and a rename on either side breaks the join. Driven off the
        committed roster files rather than a hand list, because the vocabulary
        is the feed's to change"""
        feed = set()
        for path in committed_rosters():
            feed |= {r["tm"] for r in json.loads(read_text(path))}
        feed -= {sim.UNSIGNED}          # no schedule to resolve
        self.assertEqual(len(feed), 30, sorted(feed))
        self.assertEqual({sim.team_light_nights(t) for t in feed},
                         {sim.team_light_nights(t) for t in sim.NBA_TEAMS})

    def test_a_team_is_counted_on_the_nights_it_actually_plays(self):
        for tm in ("LAC", "CLE", "BKN"):
            with self.subTest(tm=tm):
                self.assertEqual(
                    sim.team_light_nights(tm),
                    frozenset(i for i in sim.light_nights()
                              if tm in sim.NIGHTS[i][1]))


class Coverage(unittest.TestCase):
    """`Eval Definitions §Where our format pulls off consensus` 5. What pays is
    the count of DISTINCT light nights the roster reaches, never a body's own
    night count, and the two diverge by 7x on a stack"""

    def test_seven_bodies_on_one_team_only_get_you_that_teams_nights(self):
        deepest = max(light_nights_per_team().values())
        self.assertEqual(deepest, 12)
        self.assertEqual(sim.coverage(["LAC"] * 7), 12)

    def test_spreading_the_same_seven_out_covers_way_more_nights(self):
        spread = sim.coverage(["OKC", "LAC", "UTAH", "SA", "NY", "MIN", "BOS"])
        self.assertGreater(spread, 2 * sim.coverage(["LAC"] * 7))
        self.assertLessEqual(spread, len(sim.light_nights()))


class CoveragePicks(unittest.TestCase):
    """The selection rule every steering figure is cut on, stated once so the
    ladder and the headline cannot be two different rules. A greedy ladder ENDS
    at its own best-7 by construction, since rung k is the best-k"""

    def test_the_first_k_picks_are_always_the_best_k(self):
        picks = sim.coverage_picks(7)
        for k in range(1, 8):
            with self.subTest(k=k):
                self.assertEqual(sim.coverage_picks(k), picks[:k])

    def test_coverage_saturates_after_about_three_picks(self):
        """The section's whole point. Three picks buy most of it and the last
        buy nothing, and if the rule did not saturate the ladder would be a
        straight line and "steer the first few" would be wrong advice"""
        cov = [sim.coverage(sim.coverage_picks(k)) for k in range(1, 8)]
        self.assertEqual(cov, sorted(cov))
        self.assertEqual(cov[-1], cov[-2], "the 7th pick still bought a night")
        self.assertGreater(cov[2], 0.8 * cov[-1])

    def test_the_worst_seven_all_pile_onto_the_emptiest_schedule(self):
        worst = sim.coverage_picks(7, best=False)
        self.assertEqual(len(set(worst)), 1)
        self.assertEqual(sim.coverage(worst),
                         min(light_nights_per_team().values()))

    def test_only_the_teams_actually_on_offer_can_be_picked(self):
        """An auction shows you a slice of the league, not all 30, so the
        realistic figure is the best 7 of what is on the block and a rule that
        quietly reaches outside it prices a draft nobody ran"""
        offer = ("BKN", "CHI", "POR", "ATL", "DET")
        self.assertTrue(set(sim.coverage_picks(7, teams=offer)) <= set(offer))


class SchedulesReport(unittest.TestCase):
    """Every win figure README `Light-night coverage` quotes comes off this
    report, and the same choice gets printed three times, ladder, headline and
    coverage row, so the hazard is the three disagreeing.

    Rendered once for the class, since `schedules` sweeps 30 schedules at 11
    rates and is the priciest report here even at four trials"""

    @classmethod
    def setUpClass(cls):
        cls.out = render("schedules")

    def headline(self):
        """The best-7 win figure, the one number README quotes and the one
        three separate places on this page have to agree on"""
        m = re.search(r"best 7, all 30 teams on offer\s*:\s*([-+][\d.]+)",
                      self.out)
        self.assertIsNotNone(m, self.out)
        return float(m.group(1))

    def ladder(self):
        """The cumulative +wins row, rung by rung"""
        rungs = re.search(r"cumulative \+wins(.*)", self.out).group(1).split()
        self.assertEqual(len(rungs), 7, self.out)
        return [float(x) for x in rungs]

    def test_the_ladder_total_is_the_same_number_as_the_headline(self):
        """The ladder total and the best-7 headline are the same choice, so a
        reader given two figures has no way to tell which one to act on"""
        self.assertEqual(self.ladder()[-1], self.headline(), self.out)

    def test_the_stacked_seven_row_is_seven_times_the_deepest_schedule(self):
        """Seven bodies on one NBA team cannot sum past 7x the deepest light-
        night schedule. The report prints the sum and the coverage side by
        side, so the gap between them has to be the finding rather than an
        arithmetic error"""
        summed, covered = re.search(
            r"seven on \w+\s*:\s*(\d+) body-nights summed, (\d+) distinct",
            self.out).groups()
        deepest = max(light_nights_per_team().values())
        self.assertEqual(int(summed), 7 * deepest)
        self.assertEqual(int(covered), deepest)
        got = float(re.search(r"distinct, ([-+][\d.]+) wins", self.out).group(1))
        self.assertIn("lands %s not caring" % ("BELOW" if got < 0 else "above"),
                      self.out)

    def per_team_counts(self):
        """The printed light-nights-per-team table, as {team: count}"""
        listed = {}
        for n, tms in re.findall(r"^ +(\d+) +((?:[A-Z]{2,4} ?)+)$", self.out, re.M):
            for tm in tms.split():
                listed[tm] = int(n)
        return listed

    def test_every_team_is_listed_under_its_own_light_night_count(self):
        """The one table here a reader ACTS on, "prefer a body from these
        teams", and the one README republishes verbatim. A team dropped from
        it, or filed under a neighbouring count, sends the auction after the
        wrong schedule and no win figure above would look any different"""
        self.assertEqual(self.per_team_counts(), light_nights_per_team())

    def per_body_rows(self):
        """The 30-schedule sweep, one row per body grade (rate, meanPF, sdPF,
        sd wins, sdRate, spanRate)"""
        rows = [tuple(map(float, m)) for m in re.findall(
            r"^ +(\d+) +(\d+) +([\d.]+) +([\d.]+) +([\d.]+) +([\d.]+)$",
            self.out, re.M)]
        self.assertTrue(rows, self.out)
        return rows

    def test_the_schedule_swing_converts_through_the_one_pf_per_win(self):
        """The only place the file converts a PF spread into the rate points a
        board prices in, and the whole tiebreak is denominated by it. A second
        PF to wins constant living here would quote the threshold in a currency
        no other number on the page uses, and every row would still look
        plausible"""
        for rate, _, sdpf, sdwins, _, _ in self.per_body_rows():
            with self.subTest(rate=rate):
                self.assertAlmostEqual(sdwins, sdpf / sim.PF_PER_WIN, delta=0.001)

    def test_the_schedule_spread_shrinks_as_the_body_gets_better(self):
        """The shape the section is sold on. The body's own value climbs far
        faster than the schedule spread under it, so the schedule matters most
        exactly where the body matters least, the auction tier"""
        rows = self.per_body_rows()
        self.assertEqual([r[1] for r in rows], sorted(r[1] for r in rows))
        self.assertGreater(rows[0][4], rows[-1][4] * 1.5)

    def test_the_sub_proportional_line_comes_off_its_own_table(self):
        """The line under the table quotes four of its numbers. If a re-cut
        ever makes the schedule spread grow WITH the body, this stops being
        sub-proportional and the whole "cheap tiebreak, never a price" framing
        goes with it"""
        rows = self.per_body_rows()
        body = rows[-1][1] / rows[0][1]
        swing = rows[-1][2] / rows[0][2]
        if body > swing:
            self.assertIn("SUB-PROPORTIONAL", self.out)
        else:
            self.assertNotIn("SUB-PROPORTIONAL", self.out)
        self.assertIn("the body grows %dx from rate %d to %d while the"
                      % (round(body), rows[0][0], rows[-1][0]), self.out)
        self.assertIn("schedule sd under it grows only %dx" % round(swing),
                      self.out)
        self.assertIn("%.1f rate points at %d and %.1f at %d"
                      % (rows[0][4], rows[0][0], rows[-1][4], rows[-1][0]),
                      self.out)

    def test_the_threshold_it_prints_comes_off_the_row_we_actually_bid_at(self):
        """The rule is spent at 8-14 FPts and nowhere else, and the exchange
        rate halves by rate 40, so a threshold quoted off the wrong row is ~2x
        wrong in the direction that overpays. It is the one number from this
        report that gets carried into a live acquisition"""
        rows = self.per_body_rows()
        thresh = re.search(r"so ~([\d.]+) rate points is the threshold",
                           self.out)
        self.assertIsNotNone(thresh, self.out)
        self.assertEqual(float(thresh.group(1)), round(rows[0][4], 1))
        self.assertLessEqual(rows[0][0], 8)

    def test_the_spread_seven_row_uses_the_same_seven_as_the_headline(self):
        """Third place the same choice gets printed, and the one sitting in a
        table beside a stack it is supposed to beat. A coverage row scoring its
        own private best-7 splits the headline in two again"""
        covered, wins = re.search(
            r"spread best 7\s*:\s*\d+ body-nights summed, (\d+) distinct, "
            r"([-+][\d.]+) wins", self.out).groups()
        self.assertEqual(float(wins), self.headline(), self.out)
        self.assertEqual(int(covered), sim.coverage(sim.coverage_picks(7)))

    def test_the_last_picks_verdict_matches_the_sigma_it_prints(self):
        """The figure a reader acts on, "stop steering after k". On a
        counterparty file the ladder can peak at seven, so whether the last
        pick bought anything is a comparison against its own paired sigma
        rather than a fixed sentence"""
        inc, se = re.search(r"buys ([-+][\d.]+) against a paired \+-([\d.]+)",
                            self.out).groups()
        self.assertIn("which is %s" % ("nothing measurable"
                                       if abs(float(inc)) < 2 * float(se)
                                       else "a REAL increment"), self.out)

    def test_the_picks_it_prints_are_the_ones_the_rule_actually_makes(self):
        """The rungs are only comparable because every one of them is the same
        greedy-on-coverage rule taken k deep (`CoveragePicks`), and README
        quotes the picks and the nights they reach as fact. A ladder on any
        other rule reads as a measurement of steering and is a measurement of
        something else"""
        picks = re.search(r"picks: (.+)", self.out).group(1).split()
        self.assertEqual(picks, list(sim.coverage_picks(7)), self.out)
        cover = re.search(r"steered picks cover(.*)", self.out).group(1).split()
        self.assertEqual([int(c) for c in cover],
                         [sim.coverage(picks[:k]) for k in range(1, 8)])

    def test_the_percentages_it_quotes_match_its_own_ladder(self):
        """The only sentence here telling a reader where to stop paying
        attention, and it is a ratio of two numbers on the row above it. The
        ladder is re-cut every season and the sentence has to move with it"""
        cum = self.ladder()
        peak = max(cum)
        got = re.search(r"(\d+) picks buy (\d+)% of the peak and (\d+) buy (\d+)%",
                        self.out)
        self.assertIsNotNone(got, self.out)
        a, sa, b, sb = (int(x) for x in got.groups())
        self.assertEqual(sa, round(100 * cum[a - 1] / peak))
        self.assertEqual(sb, round(100 * cum[b - 1] / peak))

    def test_a_15_team_offer_is_worth_less_than_having_all_30(self):
        """Fewer teams on the block is strictly less to choose from. Printing
        the two the other way round, or reading the wrong one into an eval,
        doubles the case for a rule already sitting at the 0.1-win floor"""
        real = float(re.search(r"random 15-team offer\s*:\s*([-+][\d.]+)",
                               self.out).group(1))
        full = self.headline()
        worst = float(re.search(r"worst 7 .*:\s*([-+][\d.]+)",
                                self.out).group(1))
        self.assertLess(real, full, self.out)
        self.assertLess(worst, real, self.out)
        self.assertGreater(full - worst, 4 * (full - real))

    def test_the_coverage_call_comes_off_the_two_r2s_it_prints(self):
        """"Coverage, not a summed night count" is the section's central claim
        and this report is the only thing that measures it, so the verdict is
        DERIVED from the two R2s and a re-cut that flips them flips the
        sentence too"""
        cov = float(re.search(r"nights COVERED.*R2 ([\d.]+)", self.out).group(1))
        summed = float(re.search(r"nights SUMMED.*R2 ([\d.]+)", self.out).group(1))
        self.assertIn("Coverage %s that comparison"
                      % ("wins" if cov > summed else "LOSES"), self.out)


class AuctionSteering(unittest.TestCase):
    """Sept '26 fills 10 slots, 3 rookie picks and a 7-man FA auction (`league-
    info`). Only the auction seven are a schedule we CHOOSE, so a steering
    figure that quietly re-points any of the other 31 prices a choice nobody
    has"""

    def test_steering_moves_the_auction_seven_and_nobody_else(self):
        """Two targets, so a body that already sat on the target team cannot
        pass for one that stayed put. The rookie grades carry a schedule too,
        so a rule reaching one body further would price a pick we do not get to
        aim, and would still print seven steered bodies"""
        full = sim.basis()
        a, b = sim.steer(full, ["BKN"] * 7), sim.steer(full, ["CHI"] * 7)
        moved = [p["n"] for p, x, y in zip(full, a, b)
                 if not p["tm"] == x["tm"] == y["tm"]]
        self.assertEqual(len(moved), 7)
        owned = {p["n"] for p in sim.our_roster()}
        self.assertFalse(owned & set(moved), "steered a player we already own")
        auction = [p["n"] for p in sim.EXPANSION if p["n"].startswith("FA")]
        self.assertEqual(moved, auction, "steered something we do not bid on")

    def test_a_steered_body_is_the_same_body_on_a_different_schedule(self):
        """The whole comparison is schedule against schedule at matched grade,
        so a steered body that also picked up a rate or a slot group would book
        those as the schedule's doing"""
        full = sim.basis()
        for a, b in zip(full, sim.steer(full, ["BKN"] * 7)):
            self.assertEqual((a["n"], a["avg"], a["gp"], a["elig"]),
                             (b["n"], b["avg"], b["gp"], b["elig"]))

    def test_a_target_list_that_is_not_seven_teams_fails(self):
        """Seven is a league fact, not a loop bound. Silently steering the
        first three of a seven-team list answers a different question and still
        prints a win figure"""
        full = sim.basis()
        with self.assertRaises(ValueError):
            sim.steer(full, ["BKN", "LAC", "OKC"])

    def test_an_unsigned_body_covers_the_same_nights_the_sim_gives_him(self):
        """`team_nights` puts an unsigned body on SIM_TM rather than inventing
        him a calendar, and coverage cannot quietly disagree with it and call
        him a body that covers nothing"""
        self.assertEqual(sim.coverage([sim.UNSIGNED]),
                         sim.coverage([sim.SIM_TM]))


class CommonRandomNumbers(unittest.TestCase):
    def test_swapping_a_player_for_his_own_clone_changes_nothing(self):
        """A scenario must perturb only what it changes. Appending the incoming
        player rather than replacing in place shifts every later player's
        availability draw, which buries sub-0.1-win deltas in Monte-Carlo noise
        """
        full = sim.our_roster() + sim.EXPANSION
        clone = dict(full[0])
        same = sim.swap(full, [clone["n"]], [clone])
        self.assertEqual(sim.run(same, trials=8)["pf"], sim.run(full, trials=8)["pf"])

    def test_a_three_for_three_of_clones_changes_nothing_either(self):
        """A different path, and the one a real offer is priced on. With three
        bodies leaving and three arriving, a `swap` that appended the arrivals
        instead of seating them in the vacated slots re-orders everything below
        them and shifts every later draw, worth several tenths of a win against
        a joint-vs-summed gap of about one"""
        full = sim.basis()
        clones = [dict(p) for p in full[:3]]
        same = sim.swap(full, [p["n"] for p in clones], clones)
        self.assertEqual(sim.run(same, trials=8)["pf"], sim.run(full, trials=8)["pf"])


class AbsenceBlocks(unittest.TestCase):
    """`_availability` places IL blocks CIRCULARLY, so the onset scan has to be
    circular too. ~26% of player-seasons come out with both their first and
    last team-game night absent, and a left-to-right scan splits that one block
    in two, letting a single injury surprise you twice"""

    def test_a_block_that_wraps_the_end_of_the_season_is_one_block(self):
        # his team-game nights, absent for 50 then 10 and 20, so ONE block
        self.assertEqual(sim._onsets([10, 20, 30, 40, 50], {30, 40}), [50])

    def test_the_block_statistics_are_measured_on_the_roster_you_pass(self):
        """The lock-in correction is worth exactly the ratio of absence NIGHTS
        to absence BLOCKS, and no fixed pair of numbers describes both rosters,
        so it is measured live per roster"""
        small = sim.absence_blocks(sim.our_roster(), seeds=6)
        big = sim.absence_blocks(sim.our_roster() + sim.EXPANSION, seeds=6)
        self.assertGreater(big["nights"], small["nights"] + 100)
        self.assertGreater(small["mean_block"], 7.0)


class SurpriseScratches(unittest.TestCase):
    """A scratch can only surprise a lineup-setter on the FIRST night of an
    absence block, since after that he is on the public injury report. Drawing
    the surprise from every absence night instead makes the lock-in penalty
    ~10x too large"""

    def test_a_season_long_absence_can_only_surprise_you_once(self):
        """EXACTLY once, both ways. More than one is the whole season sampled
        as surprises, and none at all is the other half of the circular fix,
        since with nothing played there is no night before that he played and a
        scan needing one drops the opening night that IS the surprise"""
        glass = [dict(sim.star(45, 0, ("SF", "PF"), "LAL", "GLASS"), surprise=1.0)]
        for seed in (101, 202, 303):
            _, starts, pts, _ = sim.season(glass, seed=seed, bursty=True)
            self.assertEqual(starts["GLASS"], 1)
            self.assertEqual(pts["GLASS"], 0.0)      # started, scores nothing

    def test_a_lone_scattered_absence_is_still_a_surprise(self):
        # his one missed night is its own onset, and ~79% of NBA nights fall in
        # the scored periods, so over 20 seeds it lands in window ~16 times
        """Guard on the other side. A rest day IS the first night of its own
        block, so the correction must not suppress it, and a high-GP veteran
        resting scattered single games is the shape the lock-in costs the most
        """
        rester = [dict(sim.star(45, 81, ("SF", "PF"), "LAL", "REST"), surprise=1.0)]
        wasted = 0
        for seed in range(101, 121):
            _, starts, pts, _ = sim.season(rester, seed=seed, bursty=True)
            wasted += starts["REST"] - round(pts["REST"] / 45)
        self.assertGreaterEqual(wasted, 10)

    def test_a_small_surprise_rate_still_costs_something(self):
        """Each block has to be an INDEPENDENT draw. `round(q x blocks)`
        truncates to zero for every player with fewer than ~5 absence blocks,
        which is most of a roster, so a 10% rate silently becomes 0% and the
        corrected penalty reads as exactly nothing"""
        full = sim.our_roster() + sim.EXPANSION
        base = sim.run(full, trials=40, bursty=True)["pf"]
        risky = sim.run(full, trials=40, bursty=True, surprise=0.10)["pf"]
        self.assertLess(risky, base - 20)


class DuplicateNames(unittest.TestCase):
    """`season` scores a night off a `{name: points}` built from the players
    available, so two bodies sharing a name collapse into one entry and the
    night's total counts whichever one the dict kept, twice. `star()` names
    every synthetic body the same by default, and the league also rosters two
    real Jaylin Williamses"""

    def test_two_bodies_sharing_a_name_score_as_two_bodies(self):
        roster = [sim.star(40, 82, ("SF", "PF"), "LAC", "TWIN"),
                  sim.star(10, 82, ("PG", "SG"), "LAC", "TWIN")]
        distinct = [dict(roster[0], n="A"), dict(roster[1], n="B")]
        self.assertAlmostEqual(sim.run(roster, trials=4)["pf"],
                               sim.run(distinct, trials=4)["pf"], places=6)

    def test_two_unnamed_bodies_in_one_deal_stay_two_distinct_bodies(self):
        """The documented multi-piece path, `swap(full, [a, b], [star(),
        star()])`, names neither incoming body. PF survives that, since it is
        keyed on the roster index, but everything a reader does with the deal
        afterwards does not, the two collapse into one `season` points row and
        moving either of them on reads as ambiguous"""
        full = sim.basis()
        deal = sim.swap(full, ["Jalen Suggs", "Coby White"],
                        [sim.star(45, 68, ("PG", "SG")), sim.star(12, 68, ("C",))])
        incoming = [p["n"] for p in deal if p["n"] not in {q["n"] for q in full}]
        self.assertEqual(len(set(incoming)), 2, incoming)
        pts = sim.season(deal, seed=101)[2]
        self.assertGreater(pts[incoming[0]], pts[incoming[1]])
        sim.swap(deal, [incoming[0]], [sim.star(30)])

    def test_trading_away_an_ambiguous_name_fails_instead_of_guessing(self):
        """Which of the two Jaylin Williamses left is not a question `swap` can
        answer, and the roster it returns is a different trade either way"""
        roster = [sim.star(40, 82, ("SF", "PF"), "LAC", "Jaylin Williams"),
                  sim.star(20, 82, ("C",), "OKC", "Jaylin Williams"),
                  sim.star(30, 82, ("PG", "SG"), "LAC", "Someone Else")]
        with self.assertRaises(KeyError):
            sim.swap(roster, ["Jaylin Williams"], [sim.star(45)])
        self.assertGreater(sim.run(roster, trials=2)["pf"], 0)


class PerPositionReplacement(unittest.TestCase):
    """`replacement` prints an `R` per slot group and the README calls the
    single-R error "a third of the formula's error". Pricing a centre against a
    forward's 17.1 when his own group's is 20.5 is worth 0.07-0.09 wins cross-
    position, so the counterfactual has to be a body of the outgoing player's
    OWN group"""

    def test_a_player_is_priced_against_a_replacement_of_his_own_slot_group(self):
        full = sim.basis()
        with cheap_monte_carlo(40):
            groups = {g: sim.replacement(full, 68, e)[0]
                      for g, e in sim.GROUPS.items()}
            self.assertGreater(groups["centre"], groups["forward"] + 1.0,
                               "this roster's centre group is not the tight one")
            base = sim.run(full, seed0=101)

            def against(R, elig):
                return sim.wins(base, sim.run(
                    sim.swap(full, ["Jakob Poeltl"], [sim.star(R, 68, elig)]),
                    seed0=101))
            own = against(groups["centre"], ("C",))
            forward = against(groups["forward"], ("SF", "PF"))
            got, = sim.player_wins(full, ["Jakob Poeltl"], blocks=1).values()
        self.assertAlmostEqual(got[0], own, delta=0.02)
        self.assertGreater(forward, own + 0.02, "the two counterfactuals agree, "
                           "so this roster cannot tell them apart")

    def test_the_table_states_the_replacement_rate_it_used_for_each_group(self):
        """The counterfactual is the whole meaning of the number (`Eval
        Definitions §Δw`), so a header naming one rate for a table priced on
        three is worse than no header, and naming three rates the rows were not
        priced against is worse still. The rates are deterministic given the
        seeds, so the header is checked against a re-fit rather than inspected
        for the words"""
        buf = io.StringIO()
        with cheap_monte_carlo(8):
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["players"]()
            fitted = sim.group_replacement(sim.basis())
        header = buf.getvalue()
        for g, R in fitted.items():
            with self.subTest(group=g):
                stated = re.search(r"%s (\d+\.\d)" % g, header)
                self.assertIsNotNone(stated, header)
                self.assertAlmostEqual(float(stated.group(1)), R, delta=0.05)


class FormulaCounterfactual(unittest.TestCase):
    """`formula` grades both formulas against a `sim` column, so that column
    has to use the same per-slot-group counterfactual `players` does. Measured
    against one 68-GP forward for every player, the per-position-R error it
    publishes is a residual against the wrong number, and the fix it recommends
    is scored against the bug it fixes"""

    ROW = re.compile(r"^  (\S.*?) +[\d.]+ +\d+ +([-+][\d.]+)", re.M)

    def test_the_sim_column_uses_the_same_counterfactual_the_players_report_does(self):
        full = sim.basis()
        buf = io.StringIO()
        with cheap_monte_carlo(8):
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["formula"]()
            rows = dict(self.ROW.findall(buf.getvalue()))
            elig = {p["n"]: p["elig"] for p in sim.our_roster()}
            name = next(n for n in rows
                        if sim.slot_group(elig[n]) != "forward")
            got, = sim.player_wins(full, [name], blocks=1,
                                   R=sim.group_replacement(full)).values()
        self.assertAlmostEqual(float(rows[name]), got[0], delta=0.01)


class PerPlayerWins(unittest.TestCase):
    """The top of `sim.py players` decides a rank the README then asserts off
    it. Those rows sit ~0.01 wins apart while a single block moves several
    times that between seeds, so the value has to be an average over blocks and
    it has to carry the sd a reader can test a gap against"""

    def test_two_independent_runs_land_far_inside_the_smallest_tradeable_gap(self):
        full = sim.basis()
        who = [p["n"] for p in sorted(sim.our_roster(),
                                      key=lambda p: -p["avg"])[:2]]
        with cheap_monte_carlo(40):
            R = sim.group_replacement(full)
        a = sim.player_wins(full, who, blocks=3, trials=40, seed0=101, R=R)
        b = sim.player_wins(full, who, blocks=3, trials=40, seed0=9001, R=R)
        for n in who:
            self.assertGreater(a[n][1], 0.0, "%s reports no uncertainty" % n)
            # An absolute bound on purpose. `3 x (sd_a + sd_b)` widens with the
            # instability it is meant to catch, and 0.06 sits well inside the
            # ~0.1 wins §sigma calls the smallest tradeable gap
            self.assertLess(abs(a[n][0] - b[n][0]), 0.06,
                            "%s: %s vs %s" % (n, a[n], b[n]))


class AdjacentRowSigma(unittest.TestCase):
    """`Eval Definitions §sigma` reads the ORDER of two adjacent rows off this
    column and states none below ~2. Every row is measured on the SAME seed
    blocks, which is what `swap`'s common random numbers buy, so the gap
    between two rows is a within-block quantity and combining the two sds as if
    independent runs up to 3x out in BOTH directions, which is the difference
    between an ordered pair and a tie"""

    ROW = re.compile(r"^ +(?P<n>\S.*?) +[\d.]+ rate +\d+ gp +\S+ "
                     r"+(?P<w>[-+][\d.]+) +\+-[\d.]+ +(?P<next>[-\d.]+|inf)?",
                     re.M)

    def test_the_gap_is_measured_on_the_blocks_the_two_rows_share(self):
        full = sim.basis()
        blocks = 3
        ours = sim.our_roster()
        with cheap_monte_carlo(8, blocks=blocks):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                sim.REPORTS["players"]()
            w = sim.player_wins(full, [p["n"] for p in ours], blocks=blocks,
                                R=sim.group_replacement(full))
        rows = self.ROW.findall(buf.getvalue())
        self.assertEqual(len(rows), len(ours), rows)
        top, second = rows[0][0], rows[1][0]
        printed = float(rows[0][2])
        d = [a - b for a, b in zip(w[top][2], w[second][2])]
        paired = statistics.mean(d) / (statistics.stdev(d) / math.sqrt(len(d)))
        independent = (w[top][0] - w[second][0]) / math.sqrt(
            (w[top][1] ** 2 + w[second][1] ** 2) / blocks)
        self.assertAlmostEqual(printed, paired, delta=0.15)
        self.assertGreater(abs(printed - independent), 0.5,
                           "the two formulas agree on this pair, so it cannot "
                           "tell them apart -- pick another")


class IncomingWins(unittest.TestCase):
    """`Eval Definitions §Columns` wants a `Δw ours` for every player on a
    counterparty's roster. `--roster their.json players` prices them on THEIR
    roster, which is `Δw theirs`, a different column the same file forbids
    sorting on, so without this the counterparty half of every eval is 28 hand-
    typed `swap` calls with the counterfactual retyped each time"""

    def test_acquiring_a_player_is_worth_what_losing_him_costs(self):
        """The mirror, and the reason this belongs beside `player_wins` rather
        than beside a hand-written swap. Same counterfactual, a replacement
        body of his own slot group, so the two columns are comparable.

        Both sides padded back to the SAME 38, since the mirror only holds at a
        common body count (§Δw), and a gain priced one body deeper than the
        loss it mirrors is the depth mismatch this pair exists to catch"""
        full = sim.basis()
        n = "Cade Cunningham"
        row = next(p for p in sim.our_roster() if p["n"] == n)
        without = sim.pad([p for p in full if p["n"] != n], len(full))
        with cheap_monte_carlo(60):
            R = sim.group_replacement(full)
            lost, = sim.player_wins(full, [n], blocks=1, R=R).values()
            gained, = sim.incoming_wins(without, [row], blocks=1, R=R).values()
        self.assertEqual(len(without), len(full))
        self.assertGreater(lost[0], 1.0, "pick a player worth something")
        self.assertAlmostEqual(gained[0], lost[0], delta=0.15)

    def test_an_arrival_is_priced_at_the_same_38_bodies_a_departure_is(self):
        """`Eval Definitions §Δw` compares rosters only at a COMMON body count.
        `player_wins` prices a departure at 38, `swap` replacing in place and
        refusing a 39th body outright, so pricing an arrival AS the 39th costs
        the marginal body.

        The count is the assertion because the win difference is ~0.01 here,
        under the noise. What is wrong is the basis, not the digit"""
        full = sim.basis()
        row = max(sim.our_roster(THEIR_ROSTER), key=season_value)
        with cheap_monte_carlo(4):
            R = sim.group_replacement(full)
            with recorded_rosters(trials=4) as seen:
                sim.incoming_wins(full, [row], blocks=1, R=R)
        self.assertEqual({len(names) for names in seen}, {len(full)})

    def test_the_roster_an_arrival_joins_is_the_one_the_recipe_re_pads(self):
        """§Columns' recipe is "add him to our roster file, re-run", and at 38
        that costs a PADDED slot, our real bodies re-padded one shallower and
        him on the end. Nothing else names a body it is defensible to drop, so
        any other room prices him against a team we could not field.

        The room is the assertion because the win difference between two
        bottom-grade rooms is under the noise. What is wrong when this breaks
        is which team the column describes, not the digit.

        `R` is passed a couple of points apart across groups because that is
        the shape every real fit has (`group_fits`), and a flat one hides this.
        Rank the pads by `(rate - R) * gp` and the group spread alone decides
        which of three near-identical bottom bodies loses its slot"""
        full = sim.basis()
        recipe = [p["n"] for p in sim.pad(sim.our_roster(), len(full) - 1)]
        R = {"guard": 18.0, "forward": 17.0, "centre": 20.0}
        with recorded_rosters() as seen:
            sim.incoming_wins(full, [sim.star(40.0, 68, ("SF", "PF"), n="IN")],
                              blocks=1, trials=2, R=R)
        priced = [ns for ns in seen if {"IN", "REPL"} & set(ns)]
        self.assertTrue(priced)
        for names in priced:
            self.assertEqual([n for n in names if n not in ("IN", "REPL")],
                             recipe)

    def test_a_real_body_keeps_his_slot_however_cheap_he_scores(self):
        """The slot spent is an INVENTED one, so no roster file loses a player
        to it. Ranking every body by `(rate - R) * gp` and evicting the minimum
        instead reads the line below `R`, where `replacement` says it is not an
        ordering at all, and on five of the twelve league files the body it
        picks is a real player"""
        full = sim.basis()
        roster = [dict(p) for p in full[:-1]]
        roster.insert(3, sim.star(1.0, 82, ("PG", "SG"), n="SCRUB"))
        with recorded_rosters() as seen:
            sim.incoming_wins(roster, [sim.star(40.0, 68, ("SF", "PF"), n="IN")],
                              blocks=1, trials=2, R=flat_R())
        priced = [set(ns) for ns in seen if {"IN", "REPL"} & set(ns)]
        self.assertTrue(priced)
        for names in priced:
            self.assertEqual(len(names), len(roster))
            self.assertIn("SCRUB", names,
                          "a body off the roster file paid for the arrival")
            self.assertLess(len(names & roster_mod.PAD_NAMES),
                            len(set(p["n"] for p in roster)
                                & roster_mod.PAD_NAMES))

    def test_a_roster_with_nothing_padded_is_refused_rather_than_thinned(self):
        """From Sept '26 the 38 are all real and the recipe runs out of
        anything to spend, so somebody we field has to go. Which one is the
        caller's call, the same as `swap` says for that decision on the way
        out, and the alternatives sit a rate point apart on a line
        `replacement` says does not rank, so a default here is a coin flip that
        prints as a measurement"""
        full = [dict(p, n="Real %d" % i) for i, p in enumerate(sim.basis())]
        with self.assertRaises(ValueError) as e:
            sim.incoming_wins(full, [sim.star(40.0, 68, ("C",), n="IN")],
                              blocks=1, trials=2,
                              R=flat_R())
        self.assertIn("38", str(e.exception))

    def test_every_player_on_a_counterparty_file_is_priced_at_once(self):
        """"Never a shortlist, either side" (`Eval Definitions §Δw`), since a
        blank reads as zero. One call, one row per body on the file"""
        theirs = sim.our_roster(THEIR_ROSTER)
        with cheap_monte_carlo(20):
            w = sim.incoming_wins(sim.basis(), theirs, blocks=1)
        self.assertEqual(sorted(w), sorted(p["n"] for p in theirs))
        best = max(theirs, key=season_value)
        self.assertGreater(w[best["n"]][0], 0.3, best["n"])

    def test_a_name_our_own_roster_already_carries_is_still_priced_as_himself(self):
        """`Δw ours` seats the arrival on OUR roster, so a name we already hold
        is a collision this column cannot avoid, and the committed files
        collide today. The result is keyed by name either way, so a collision
        never shows up as a missing row, it shows up as a number belonging to
        the wrong body, under the right name, on the column a buy decision
        reads"""
        full = sim.basis()
        theirs = max(sim.our_roster(THEIR_ROSTER), key=season_value)
        ours = full[0]["n"]
        R = flat_R()
        namesake = sim.incoming_wins(full, [dict(theirs, n=ours)], blocks=1,
                                     trials=30, R=R)
        alone = sim.incoming_wins(full, [dict(theirs, n="A NAME NOBODY HOLDS")],
                                  blocks=1, trials=30, R=R)
        self.assertGreater(alone["A NAME NOBODY HOLDS"][0], 0.3, theirs["n"])
        self.assertAlmostEqual(namesake[ours][0], alone["A NAME NOBODY HOLDS"][0],
                               places=9)

    def test_two_arrivals_of_one_name_are_refused_rather_than_priced_as_one(self):
        """The league rosters two Jaylin Williamses, so one trade puts both on
        a file this column is asked to price. Keyed by NAME, the second row
        overwrites the first, which is worse than the blank §Δw forbids, since
        a blank reads as zero and this reads as measured. `swap` refuses
        exactly this ambiguity on the way out"""
        both = [sim.star(45.0, 70, ("C",), n="Jaylin Williams"),
                sim.star(12.0, 40, ("PG", "SG"), n="Jaylin Williams")]
        with self.assertRaises(ValueError) as e:
            sim.incoming_wins(sim.basis(), both, blocks=1, trials=2)
        self.assertIn("Jaylin Williams", str(e.exception))


class Thin(unittest.TestCase):
    def test_thinning_to_the_roster_you_already_have_measures_the_same_thing(self):
        """Roster ORDER drives the rng draw order, so a `thin` that sorted
        makes `thin(full, 38)` a different measurement from `full` itself,
        which is how three values of replacement level come to circulate for
        one roster"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            self.assertEqual(sim.replacement(sim.thin(full, len(full)))[0],
                             sim.replacement(full)[0])

    def test_thinning_uses_the_rosters_own_r_not_a_stale_constant(self):
        """`R` is the x-intercept of value in rate, so it moves with the body
        COUNT by construction, 17.1 on our padded 38 against ~11 on a live
        26-man file. Ranking that file at a hard-coded 17 is 6 rate points out,
        and it does not merely relabel the order, it prefers rate to games
        where this roster's own level prefers games"""
        theirs = sim.our_roster(THEIR_ROSTER)
        with cheap_monte_carlo(20):
            fitted = sim.replacement(theirs)[0]
            self.assertLess(fitted, 14.0, "this file's R is not far enough from "
                            "17 to tell the two rankings apart")
            kept = sim.thin(theirs, 22)
            stale = sim.thin(theirs, 22, R=17.0)
            self.assertNotEqual({p["n"] for p in kept}, {p["n"] for p in stale})
        self.assertGreater(sim.run(kept, trials=40)["pf"],
                           sim.run(stale, trials=40)["pf"] + 40)


class Pad(unittest.TestCase):
    """R and WINS compare across teams only at a COMMON body count, and no two
    live rosters have one. Measured on live bodies a counterparty's R lands
    near 23 against ours at 16, so every player on his roster reads as cheaper
    than one of ours"""

    def test_the_real_bodies_survive_padding_in_their_own_order(self):
        their = sim.our_roster(THEIR_ROSTER)
        padded = sim.pad(their, 38)
        self.assertEqual(len(padded), 38)
        self.assertEqual([p["n"] for p in padded[:len(their)]],
                         [p["n"] for p in their])
        self.assertEqual(len({p["n"] for p in padded}), 38)  # names index the rng

    def test_every_report_measures_a_counterparty_at_the_common_count(self):
        """`+ EXPANSION` is 10 BODIES, not a body count, so a 38-man baseline
        built that way measures a 26-man roster at 36 and reports his R, break-
        evens and per-player wins off that"""
        self.assertEqual(len(sim.basis(THEIR_ROSTER)), 38)
        self.assertEqual(len(sim.basis()), 38)

    def test_padding_our_28_is_the_38_man_basis_every_table_is_measured_on(self):
        """Pinning test, not a cycle. Every 38-man figure in the README is
        measured on `our_roster() + EXPANSION` and the counterparty recipe says
        `pad`, so if those two stop being the same measurement one of the two
        bases is wrong and the README's cross-team comparisons go with it"""
        self.assertEqual(
            sim.run(sim.pad(sim.our_roster(), 38), trials=8)["pf"],
            sim.run(sim.our_roster() + sim.EXPANSION, trials=8)["pf"])

    def test_padding_to_the_count_you_already_have_measures_the_same_roster(self):
        """Same reason `thin` preserves order. Roster order drives the rng draw
        order, so a pad that reordered would make the padded and unpadded
        measurements incomparable, which is the thing it exists to fix"""
        their = sim.our_roster(THEIR_ROSTER)
        self.assertEqual(sim.run(sim.pad(their, len(their)), trials=8)["pf"],
                         sim.run(their, trials=8)["pf"])


class Backfill(unittest.TestCase):
    def test_a_richer_backfill_grade_lowers_the_breakeven(self):
        """What the outgoing bodies 2..N are refunded at is an ASSUMPTION, not
        a fact, and every break-even in this study rides on it, so it has to be
        an argument for the bracket to be reportable"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            thin_pool = sim.breakeven(full, THREE_OUT,
                                      dead={"tm": "MIA", "avg": 6.0, "gp": 40,
                                            "elig": ["PG", "SG"]})
            deep_pool = sim.breakeven(full, THREE_OUT,
                                      dead={"tm": "MIA", "avg": 14.0, "gp": 55,
                                            "elig": ["PG", "SG"]})
        self.assertLess(deep_pool, thin_pool)


class SwapNames(unittest.TestCase):
    def test_taking_back_more_bodies_than_you_send_fails(self):
        """A 38-man roster has no room, and a silently returned 39-man one
        prices the deal with a free extra body, so the ladder that exists to
        charge for body count reads the wrong count. Attaching the drops is the
        caller's job and there is no defensible default for it"""
        full = sim.basis()
        with self.assertRaises(ValueError):
            sim.swap(full, ["Jalen Suggs"], [sim.star(45), sim.star(30)])
        self.assertEqual(len(sim.swap(full, ["Jalen Suggs", "Coby White"],
                                      [sim.star(45), sim.star(30)])), len(full))

    def test_naming_one_body_twice_on_the_send_side_fails(self):
        """One body cannot leave twice, or `len(out_names)` stops being the
        count of bodies going out and a hand-typed 3-for-1 prices as the
        1-for-1 nobody offered, on the ladder that exists to charge for body
        count"""
        full = sim.basis()
        with self.assertRaises(ValueError):
            sim.swap(full, ["Jalen Suggs", "Jalen Suggs"],
                     [sim.star(45), sim.star(30)])

    def test_trading_away_someone_who_is_not_on_the_roster_fails(self):
        """Matching on name and skipping what it does not find returns a roster
        with the incoming star ADDED and nobody removed. Every scenario built
        that way still prints, several hundred PF too high, with no sign of it
        """
        full = sim.basis()
        with self.assertRaises(KeyError):
            sim.swap(full, ["Jalen Sugs"], [sim.star(45)])


class WinsArgumentOrder(unittest.TestCase):
    """`sim.wins(after, before)`, where the argument order is the sign.
    Reversed it reads "wins lost", which is a legitimate call `report_formula`
    makes, so nothing in the code can guard it and both orders return a
    plausible-looking number. A convention that drifted would invert the
    verdict on every deal in every eval and leave the magnitudes untouched"""

    def test_an_upgrade_reads_positive_and_the_reversed_call_reads_the_loss(self):
        """Measured on the roster's own weakest body so the direction is not in
        question. The reversal is exact rather than approximate, the same pair
        of runs read the other way round, which is what makes "wins lost" a
        call a report can make rather than a second measurement"""
        full = sim.basis()
        worst = min(sim.our_roster(), key=season_value)
        base = sim.run(full, trials=20)
        better = sim.run(sim.swap(full, [worst["n"]],
                                  [sim.star(55, 75, tuple(worst["elig"]), n="UP")]),
                         trials=20)
        gained = sim.wins(better, base)
        self.assertGreater(gained, 1.0, "%s -> a 55/75 body is not an upgrade"
                           % worst["n"])
        self.assertAlmostEqual(sim.wins(base, better), -gained, places=9)


class MultiPieceDeal(unittest.TestCase):
    """`Eval Definitions §Δw` says price a multi-piece side with one joint
    `sim.run(sim.swap(...))`, never by adding rows. The rows are floats and
    nothing in the code can stop a caller adding them, so the rule is only
    worth what the gap between the two ways measures, and the published table
    is one column of addable numbers sitting next to a three-for-three offer"""

    def priced_both_ways(self, eligs):
        """The same three-for-three, priced as one deal and as three deals"""
        full = sim.basis()
        base = sim.run(full, trials=30, seed0=101)
        adds = [sim.star(46, 70, e, n="IN%d" % i) for i, e in enumerate(eligs)]
        joint = sim.wins(
            sim.run(sim.swap(full, THREE_OUT, adds), trials=30, seed0=101), base)
        summed = sum(
            sim.wins(sim.run(sim.swap(full, [o], [a]), trials=30, seed0=101), base)
            for o, a in zip(THREE_OUT, adds))
        return joint, summed

    def test_adding_the_rows_up_overstates_a_three_piece_package(self):
        """Three 46-rate centres for Suggs/White/Turner run +3.0 wins priced as
        one deal and +4.0 as three rows added. A third of the package is an
        arrival the nine slots have no room to start, and the sum cannot see
        it, which is a whole win on a deal whose verdict turns on tenths"""
        joint, summed = self.priced_both_ways([("C",)] * 3)
        self.assertGreater(summed - joint, 0.5,
                           "joint %.3f vs summed %.3f" % (joint, summed))

    def test_the_overstatement_is_worst_when_the_pieces_share_a_slot_group(self):
        """The mechanism, and the reason the rule is not a haircut a caller
        could apply from the sum alone. The same three bodies spread over
        guard/forward/centre lose ~0.2 wins to the cap instead of ~1.0, so a
        package's sub-additivity is a fact about its shape against OUR roster's
        shape and has to be simulated"""
        stacked = self.priced_both_ways([("C",)] * 3)
        spread = self.priced_both_ways([("C",), ("PG", "SG"), ("SF", "PF")])
        self.assertGreater(stacked[1] - stacked[0],
                           (spread[1] - spread[0]) + 0.4,
                           "stacked %s spread %s" % (stacked, spread))


class SlotFillCurve(unittest.TestCase):
    """The whole point of the 9-slot cap. It binds on LIGHT nights and nowhere
    else, which is why breadth pays at all and why the surplus is the middle of
    the roster rather than its tail"""

    @classmethod
    def setUpClass(cls):
        cls.by_night = sim.run(sim.basis(), trials=40)["by_night"]

    def test_most_of_the_lost_slots_sit_on_the_lightest_nights(self):
        lost = {g: (9 - v[1]) * v[3] for g, v in self.by_night.items()}
        tot = sum(lost.values())
        share = lambda upto: sum(v for g, v in lost.items() if g <= upto) / tot
        self.assertAlmostEqual(share(3), 0.68, delta=0.03)
        self.assertAlmostEqual(share(5), 0.89, delta=0.03)
        self.assertAlmostEqual(tot / (9 * len(sim.SCORING_NIGHTS)), 0.091,
                               delta=0.005)

    def test_far_more_slots_go_empty_for_want_of_a_body_than_a_position(self):
        """"Positions rarely bind" is what licenses treating the positional
        premium as a tiebreak rather than a constraint to build around"""
        vals = self.by_night.values()
        no_slot = sum((min(9, v[0]) - v[1]) * v[3] for v in vals)
        no_body = sum(max(0.0, 9 - v[0]) * v[3] for v in vals)
        self.assertGreater(no_body, 3 * no_slot)


class SlotGroups(unittest.TestCase):
    """`replacement` explains its per-group `R` by the crowding behind it, and
    the crowded group is whichever the table says, so bodies and slots have to
    be countable for ANY group rather than just guards"""

    def test_a_body_takes_the_group_of_the_slots_he_is_confined_to(self):
        """`player_wins` prices every player against his own group's R, and the
        three run 3.4 rate points apart here, so where a PF/C lands is worth
        0.07-0.09 wins on his row. Only a body confined to {C} takes the centre
        counterfactual"""
        self.assertEqual(sim.slot_group(["C"]), "centre")
        self.assertEqual(sim.slot_group(["PF", "C"]), "forward")
        self.assertEqual(sim.slot_group(["PG", "SG"]), "guard")
        self.assertEqual(sim.slot_group(["SG", "SF"]), "forward")

    def test_a_group_counts_every_slot_it_can_fill(self):
        """The two ANY slots are what a hand count misses. A pure centre chases
        3 of the 9, not the 1 the template labels C"""
        self.assertEqual(sim.group_slots(("C",)), 3)
        self.assertEqual(sim.group_slots(("PG", "SG")), 5)
        self.assertEqual(sim.group_slots(("SF", "PF")), 5)

    def test_only_a_body_that_cannot_leave_the_group_crowds_it(self):
        """A dual-eligible body relieves the crowding rather than adding to it,
        so it counts toward neither group"""
        roster = [sim.star(20, 60, ("PG", "SG")), sim.star(20, 60, ("SG", "SF")),
                  sim.star(20, 60, ("C",))]
        self.assertEqual(sim.pure_bodies(roster, ("PG", "SG")), 1)
        self.assertEqual(sim.pure_bodies(roster, ("SF", "PF")), 0)
        self.assertEqual(sim.pure_bodies(roster, ("C",)), 1)


class RosterScopedReports(unittest.TestCase):
    """Half the reports are built on OUR player names, `scenarios` trading
    Suggs and `durability` re-shaping him. Pointed at another team's file those
    names match nobody, so the report prints a full table of numbers answering
    nothing, and `--roster` is advertised for any team"""

    def test_an_our_roster_report_refuses_a_counterparty_file(self):
        """It has to name the ones it DOES serve. A bare refusal on the report
        a Skill just told you to run reads as "--roster is broken", and the 9
        that work are the whole counterparty workflow"""
        for name in sorted(sim.OURS_ONLY):
            with self.subTest(report=name):
                p = sim_process("--roster", THEIR_ROSTER, name)
                self.assertNotEqual(p.returncode, 0)
                for served in set(sim.REPORTS) - sim.OURS_ONLY:
                    self.assertIn(served, p.stdout + p.stderr)

    def test_naming_no_report_at_all_refuses_the_one_it_falls_back_to(self):
        """`calibration` is the default, so a default applied AFTER the refusal
        hands you the exact report the refusal names, their simulated PF over
        OUR real standings PF, exit 0, under a header naming their file"""
        p = sim_process("--roster", THEIR_ROSTER)
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("CALIBRATION", p.stdout)
        self.assertIn("calibration", p.stdout + p.stderr)

    def test_a_served_report_runs_on_a_counterparty_from_the_shell(self):
        """Every other run of a SERVED report is in-process with the sample
        size shrunk, so this is the only thing showing the command as it is
        actually typed, real interpreter, real argv, exit 0, a table. The
        refusals all exit before loading anything"""
        p = sim_process("--roster", THEIR_ROSTER, "nights")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(THEIR_ROSTER, p.stdout)
        self.assertIn("NIGHTS", p.stdout)

    def test_the_flag_joined_to_its_file_by_an_equals_sign_still_loads_it(self):
        """`--roster=theirs.json` is the other half of how the flag gets typed.
        A parse matching only the bare word sends the whole token through to
        the report check, which comes back complaining about a report name, on
        a flag spelled correctly"""
        p = sim_process("--roster=%s" % THEIR_ROSTER, "nights")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(THEIR_ROSTER, p.stdout)
        self.assertIn("NIGHTS", p.stdout)

    def test_the_flag_with_nothing_after_the_equals_sign_says_what_it_wanted(self):
        """`--roster=` is one keystroke from `--roster=theirs.json`, and an
        arity guard that only counts argv is satisfied by the empty half, then
        loads the DIRECTORY the files sit in under a header saying it had a
        roster"""
        p = sim_process("--roster=", "nights")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("--roster", p.stdout + p.stderr)

    def test_a_roster_file_that_is_not_there_is_refused_before_any_table(self):
        """The commonest way to mistype this flag is a wrong path, and left as
        a traceback it comes after the roster banner and the report's own
        header, so the run reads as started. `_load` also joins against the
        DATA directory rather than the shell's cwd, so a path that exists where
        you typed it still has to be named back to you"""
        p = sim_process("--roster", "no-such-team.json", "players")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertNotIn("wins lost if swapped", p.stdout)
        self.assertIn("no-such-team.json", p.stdout + p.stderr)

    def test_the_readme_names_the_reports_the_flag_actually_refuses(self):
        """The counterparty workflow is followed out of the README, not out of
        `REPORTS`, and the refusal message above is only checked against
        whatever `OURS_ONLY` happens to hold. Move a report between the two
        sets and both stay green while the page sends the reader to run
        something that exits 1"""
        text = one_line(read_text(os.path.join(sim.HERE, "README.md")))
        refused = re.search(r"exits non-zero on ((?:`\w+`[ ,])+)", text)
        self.assertIsNotNone(refused, "the README stopped naming them")
        self.assertEqual(set(re.findall(r"\w+", refused.group(1))), sim.OURS_ONLY)
        served = re.search(r"serves \*\*(\d+) of the (\d+) reports\*\*", text)
        self.assertIsNotNone(served, "the README stopped counting them")
        self.assertEqual(
            (int(served.group(1)), int(served.group(2))),
            (len(set(sim.REPORTS) - sim.OURS_ONLY), len(sim.REPORTS)))

    def test_the_module_docstring_names_the_reports_the_flag_refuses(self):
        """`sim.py`'s own docstring is the first thing anyone opening the file
        reads. A reader who believes it serves every report runs one of the
        four it refuses, gets exit 1, and reads the flag as broken rather than
        the sentence"""
        text = one_line(sim.__doc__)
        served = re.search(r"serves (\d+) of the (\d+) reports", text)
        self.assertIsNotNone(served, "the docstring stopped counting them")
        self.assertEqual((int(served.group(1)), int(served.group(2))),
                         (len(set(sim.REPORTS) - sim.OURS_ONLY), len(sim.REPORTS)))
        refused = re.search(r"refuse it: ([^.]+)\.", text)
        self.assertIsNotNone(refused, "the docstring stopped naming them")
        self.assertEqual(set(re.findall(r"\w+", refused.group(1))), sim.OURS_ONLY)

    def test_the_trades_skill_counts_the_served_reports_the_same_way(self):
        """Step 6 of `trades` is where the count is actually READ, since that
        skill and not this README is what gets loaded before a deal is priced.
        Whoever follows it skips a report the flag serves, or is sent to run
        one it refuses and reads the refusal as the flag being broken"""
        text = one_line(read_text(skills_path("trades", "SKILL.md")))
        served = len(set(sim.REPORTS) - sim.OURS_ONLY)
        counted = re.search(r"on \*\*(\d+) of the (\d+) reports\*\*", text)
        self.assertIsNotNone(counted, "the skill stopped counting them")
        self.assertEqual((int(counted.group(1)), int(counted.group(2))),
                         (served, len(sim.REPORTS)))
        naming = re.search(r"naming the (\d+)", text)
        self.assertIsNotNone(naming, "the skill stopped saying what it names")
        self.assertEqual(int(naming.group(1)), served)

    def test_roster_with_no_file_after_it_says_what_it_wanted(self):
        """Every other CLI error here exits with a written explanation. A
        traceback on the flag a Skill was just told to pass reads as a broken
        flag rather than as a command missing its argument"""
        p = sim_process("--roster")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("--roster", p.stdout + p.stderr)

    def test_the_positions_premium_is_explained_by_the_loaded_roster(self):
        """A pure-guard count typed into the `positions` header describes
        whatever roster produced the table. It has to come off the roster the
        bodies were ADDED to, the padded 38, not the live file, which is 4
        guards short of it here"""
        out = render("positions", THEIR_ROSTER)
        pure_g = sum(1 for q in sim.basis(THEIR_ROSTER)
                     if set(q["elig"]) <= {"PG", "SG"})
        self.assertIn("%d pure PG/SG" % pure_g, out)

    def test_the_light_night_premise_is_the_loaded_rosters_own(self):
        """What steering the auction buys is entirely a function of which light
        nights the OTHER 31 bodies already reach. Ours reach 31 of the 32,
        which is why the headline sits at the 0.1-win floor at all, so a report
        quoting our spread while pricing his auction hands a counterparty our
        ceiling and every table under it still prints"""
        flat = one_line(render("schedules", THEIR_ROSTER))
        full = sim.basis(THEIR_ROSTER)
        moved_a, moved_b = sim.steer(full, ["BKN"] * 7), sim.steer(full, ["CHI"] * 7)
        kept = [p["tm"] for p, x, y in zip(full, moved_a, moved_b)
                if p["tm"] == x["tm"] == y["tm"]]
        self.assertIn("the other %d stay where they are, and %d of the %d "
                      "light nights are already reached"
                      % (len(kept), sim.coverage(kept), len(sim.light_nights())),
                      flat)
        self.assertIn("spread of %d NBA teams"
                      % sum(1 for t in set(kept) if not sim.unsigned(t)), flat)

    def test_the_group_r_note_agrees_with_the_table_it_explains(self):
        """A report served for any team cannot explain its numbers with OUR
        roster's shape. Against a counterparty whose guard R is BELOW his
        forward R, a fixed guard sentence offers a body count as proof of the
        opposite of what the numbers say.

        Two things have to hold. The counts come off the roster R was FITTED
        on, the padded 38 rather than the live file, which is a different shape
        and 4-8 bodies short per group. And crowding is offered as an
        explanation only where it actually orders the three R's, since on our
        own padded roster guards and centres are equally crowded while centre R
        is the higher"""
        out = render("replacement", THEIR_ROSTER)
        R = {lab: float(re.search(r"^ +%s +([\d.]+)" % lab, out, re.M).group(1))
             for lab in ("guard", "forward", "centre")}
        note = re.search(r"guard ([-+]\d+\.\d), centre ([-+]\d+\.\d)", out)
        self.assertIsNotNone(note, out)
        self.assertAlmostEqual(float(note.group(1)),
                               R["guard"] - R["forward"], delta=0.1)
        self.assertAlmostEqual(float(note.group(2)),
                               R["centre"] - R["forward"], delta=0.1)
        padded = sim.basis(THEIR_ROSTER)
        for g, elig in sim.GROUPS.items():
            with self.subTest(group=g):
                self.assertIn("%s %d/%d" % (g, sim.pure_bodies(padded, elig),
                                            sim.group_slots(elig)), out)
        top = re.search(r"[Hh]ighest R is (\w+)", out)
        self.assertIsNotNone(top, out)
        self.assertEqual(top.group(1), max(R, key=R.get), out)
        crowd = {g: sim.pure_bodies(padded, e) / sim.group_slots(e)
                 for g, e in sim.GROUPS.items()}
        byR = sorted(R, key=lambda g: -R[g])
        orders = all(crowd[a] > crowd[b] for a, b in zip(byR, byR[1:]))
        self.assertIn("rowding %s the three here"
                      % ("orders" if orders else "does NOT order"), out)


class OneSchedule(unittest.TestCase):
    """Which NBA team a synthetic body sits on moves its added PF by ~220
    across the 30 schedules, several rate points rather than a rounding effect,
    so the study declares ONE schedule and puts every body on it"""

    def test_the_schedule_moves_a_body_more_than_the_tie_band_does(self):
        full = sim.basis()
        base = sim.run(full, trials=40)["pf"]

        def added(tm):
            body = sim.star(45, 68, ("SF", "PF"), tm, "ADD")
            return sim.run(full + [body], trials=40)["pf"] - base
        self.assertGreater(abs(added("OKC") - added("DET")), 100)

    def test_separate_one_for_ones_beat_a_consolidation_on_one_schedule(self):
        """Priced on the declared schedule the comparison is about bodies
        alone, which is the claim worth keeping. Spread the incoming bodies
        over different NBA teams and an unknown part of the gap is a schedule
        handicap booked as body count"""
        full = sim.basis()
        base = sim.run(full, trials=40)
        sep = sim.wins(sim.run(sim.swap(full, THREE_OUT, [
            sim.star(42, 68, ("SF", "PF"), sim.SIM_TM, "S%d" % i)
            for i in range(3)]), trials=40), base)
        con = sim.wins(sim.run(sim.swap(full, THREE_OUT, [
            sim.star(65.2, 65, ("C",), sim.SIM_TM)]), trials=40), base)
        self.assertGreater(sep, con)


class BreakEven(unittest.TestCase):
    def test_a_breakeven_outside_the_bracket_raises_rather_than_returning_an_end(self):
        """Bisection with no sign check converges on the nearer END of its own
        bracket and returns it as an answer, a number that looks measured, sits
        in the middle of the rates we trade at, and is really just `lo`. Both
        ends do it"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            with self.assertRaises(ValueError) as low:
                sim.breakeven(full, ["Jalen Suggs"], lo=60.0, hi=90.0)
            self.assertIn("60", str(low.exception))
            with self.assertRaises(ValueError) as high:
                sim.breakeven(full, THREE_OUT, lo=20.0, hi=30.0)
            self.assertIn("30", str(high.exception))

    def test_one_uncomputable_cell_does_not_take_the_table_with_it(self):
        """Every row of the break-evens table is a comprehension over
        2..N-for-1s, so the ValueError `breakeven` correctly raises for one
        cell kills the whole report. Out of bracket is a real answer ABOUT THAT
        CELL, "no such player exists, so the deal is unbuyable", so the cell
        says which end it fell off"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            self.assertIn(">30", sim.breakeven_cell(full, THREE_OUT,
                                                    lo=20.0, hi=30.0))
            self.assertIn("<60", sim.breakeven_cell(full, THREE_OUT[:1],
                                                    lo=60.0, hi=90.0))
            self.assertRegex(sim.breakeven_cell(full, THREE_OUT[:2]),
                             r"\d\d\.\d")

    def test_the_rate_it_returns_is_pf_neutral(self):
        """What a break-even IS. Seat a body at that rate in the slots the
        outgoing players vacated and the season's PF comes back where it
        started.

        Both sides are 20-trial figures on the same estimator the search
        bisected on, so what this pins is that the search converged, not that
        the published rate survives a re-measure at the published trial count
        """
        full = sim.basis()
        out = ["Jalen Suggs", "Coby White"]
        with cheap_monte_carlo(20):
            rate = sim.breakeven(full, out, gp=68, elig=("SF", "PF"))
            got = sim.run(sim.swap(full, out, [sim.star(rate, 68)]))["pf"]
            self.assertAlmostEqual(got, sim.run(full)["pf"], delta=40)

    def test_the_breakeven_moves_with_the_incoming_gp_and_slot(self):
        """"Read the row matching his shape." The same 3-for-1 needs several
        more rate points from a 65-GP centre than from a 68-GP forward and
        fewer from a 78-GP one, which is how Jokic reads as a hair positive
        against his own row and a 6-point win against the forward row. A break-
        even quoted without its GP and slot is the wrong number, not a rounded
        one"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            forward = sim.breakeven(full, THREE_OUT, 68, ("SF", "PF"))
            centre = sim.breakeven(full, THREE_OUT, 65, ("C",))
            durable = sim.breakeven(full, THREE_OUT, 78, ("SF", "PF"))
        self.assertGreater(centre, forward + 3.0)
        self.assertLess(durable, forward - 1.5)


class BoardSnapshot(unittest.TestCase):
    """`dizzle-dynasty` snapshots are month-stamped and the month moves, and
    the Skill says never hardcode one. `board_rates` is the study's only rank
    to rate bridge, so a hardcoded month reads a stale board silently, and
    keeps reading it after the new snapshot lands beside it"""

    def test_the_newest_snapshot_is_the_one_read(self):
        d = tempfile.mkdtemp()
        for n in ("july-2026-dynasty-ranks-points.csv",
                  "december-2026-dynasty-ranks-points.csv",
                  "january-2027-dynasty-ranks-points.csv",   # newest, year wins
                  "january-2027-dynasty-ranks-9cat.csv"):    # wrong scoring
            open(os.path.join(d, n), "w").close()
        self.assertEqual(os.path.basename(sim.newest_board(d)),
                         "january-2027-dynasty-ranks-points.csv")

    def test_a_directory_with_no_snapshot_says_what_it_looked_for(self):
        with self.assertRaises(FileNotFoundError) as e:
            sim.newest_board(tempfile.mkdtemp())
        self.assertIn("dynasty-ranks-points.csv", str(e.exception))

    def test_the_report_names_the_snapshot_it_priced_off(self):
        """The month moves and the old file stays put, so a rank table that
        does not name its board cannot be checked against one, and the reader
        has no way to tell a re-snapshot from a re-rank"""
        self.assertIn(os.path.basename(sim.newest_board()), render("market"))


class BoardBridge(unittest.TestCase):
    """The framework converts board rank to wins through one constant, so a
    rank to FPts/G join that silently matches nothing would make every scenario
    look purchasable"""

    def test_the_top_of_the_board_joins_to_scoring_rates(self):
        pairs = sim.board_rates()
        top50 = [r for r, _ in pairs if r <= 50]
        self.assertGreater(len(top50), 40)

    def test_rate_falls_as_board_rank_rises(self):
        pairs = sim.board_rates()
        top = statistics.mean([v for r, v in pairs if r <= 30])
        deep = statistics.mean([v for r, v in pairs if 150 <= r <= 250])
        self.assertGreater(top, deep + 10)

    def test_the_rates_a_four_and_five_for_one_demands_barely_exist(self):
        """The case for the 3-for-1 cap that does NOT go through the win table.
        The 4-for-1 break-even at 45.1 and the 5-for-1 at 58.8 ask for rates
        almost nobody supplies, so those deals are unavailable at any price
        rather than merely expensive. If the pool ever gets deep in 45s that
        argument is gone"""
        pairs = sim.board_rates()
        self.assertEqual(len(pairs), 359)
        self.assertEqual(sum(1 for _, r in pairs if r >= 45), 8)
        self.assertEqual(sum(1 for _, r in pairs if r >= 50), 3)
        self.assertEqual(sum(1 for _, r in pairs if r >= 60), 1)

    def test_a_fragment_season_does_not_set_the_rate_a_rank_band_supplies(self):
        """The report prints the DEEPEST rank that has ever supplied a rate,
        how far down you might have to look, so one 5-game hot streak deep on
        the board moves the answer to a question about where 30-FPts players
        live. `min_gp` is what stops it"""
        deepest = lambda pairs: max(k for k, r in pairs if r >= 30)
        self.assertLess(deepest(sim.board_rates()),
                        deepest(sim.board_rates(min_gp=0)) - 50)
        self.assertEqual(sim.pool_seasons("Walker Kessler")["2025"][1], 5)


class PFPerWinBand(unittest.TestCase):
    """Every trade verdict is priced through this one constant and `eval-team`
    quotes a band for it, so the band has to be re-derivable rather than a
    number in prose.

    The CLUSTERING is the whole content. The 11 margins in a period all share
    our score for that period, so they are not 212 independent draws, and
    resampling them individually gives an interval several times too narrow"""

    def test_the_band_brackets_the_point_estimate_and_stays_wide(self):
        lo, hi = sim.pf_per_win_band(n=400)
        self.assertLess(lo, sim.PF_PER_WIN)
        self.assertGreater(hi, sim.PF_PER_WIN)
        self.assertGreater((hi - lo) / sim.PF_PER_WIN, 0.15)

    def test_one_win_is_about_600_pf(self):
        """"1 win ~ 600 PF" is the headline the whole framework converts
        through, and every +wins figure in the README divides by it. It is a
        measurement off the real margin distribution, so it moves when the
        score matrix or the scoring basis does and every table above it goes
        stale silently"""
        self.assertAlmostEqual(sim.PF_PER_WIN, 597, delta=10)


class StandingsBasis(unittest.TestCase):
    """ONE basis for every PF figure here, the periods that count toward the
    standings. Periods 21-23 are the playoff and consolation bracket and the
    standings PF column excludes them, so a 23-period total is a different
    season, and it is the number the API hands you first"""

    def test_the_scored_periods_are_the_ones_the_standings_count(self):
        self.assertEqual(sim.WEEKS, 20)
        self.assertEqual(len(sim.OURS), 20)
        self.assertEqual(round(sum(sim.OURS)), 27229)   # our standings PF column
        for i in sim.SCORED:
            self.assertNotIn("playoff", sim.PERIODS[i]["kinds"])

    def test_including_the_bracket_periods_inflates_the_total(self):
        """Not a rounding difference. Including them inflates the total 18.5%,
        which is several wins wherever it lands"""
        every = list(sim.SCORES[sim.US].values())
        self.assertEqual(len(every), 23)
        self.assertGreater(sum(every) / sum(sim.OURS), 1.15)


class Calibration(unittest.TestCase):
    """The one end-to-end check that the machinery, schedule, periods, the
    9-slot matching and the availability draw, reproduces a season that
    actually happened. §Method calls absolute PF good to ~5% and quotes it as a
    SANITY BOUND rather than a scale factor, so what is worth guarding is the
    order of magnitude"""

    def test_the_season_that_happened_simulates_to_roughly_what_it_scored(self):
        got = sim.run(sim.our_roster(projected=False), trials=40)["pf"]
        real = sim.REAL_WK_MEAN * sim.WEEKS
        self.assertAlmostEqual(got / real, 1.0, delta=0.2)


class CalibrationRatio(unittest.TestCase):
    """The ratio divides the CURRENT roster's simulated season by what the PRE-
    trade roster actually scored, since 27,229 is a standings column and the
    file is re-cut after every trade. Printed bare it reads as a 5.2% model
    error, which is the one number a reader would use to rescale the study"""

    def test_the_printed_ratio_says_it_is_measured_against_the_pre_trade_roster(self):
        out = render("calibration")
        self.assertIn("ratio", out)
        self.assertIn("pre-trade", out[out.index("ratio"):].lower())


class CalibrationUsesTheScoredPeriods(unittest.TestCase):
    """`SCORED`, the 20 periods that count toward the standings, is the ONE
    basis for every PF figure here. Setting MARGIN_SD over 20 periods against a
    pooled opponent sd taken over all 23 compares two different seasons"""

    def test_the_independence_check_is_on_the_same_periods_as_the_margins(self):
        out = render("calibration")
        rho = float(re.search(r"correlation rho = (\d+\.\d+)", out).group(1))

        def rho_over(ordinals):
            ind = math.sqrt(sim.REAL_WK_SD ** 2 + statistics.stdev(
                [v for t, s in sim.SCORES.items() if t != sim.US
                 for p, v in s.items() if p in ordinals]) ** 2)
            return 1 - sim.MARGIN_SD ** 2 / ind ** 2

        scored = {sim.PERIODS[i]["ordinal"] for i in sim.SCORED}
        self.assertAlmostEqual(rho, rho_over(scored), delta=0.006)
        self.assertGreater(abs(rho - rho_over(set(sim.SCORES[sim.US]))), 0.006,
                           "the two bases agree, so this cannot tell them apart")


class SeasonAge(unittest.TestCase):
    def test_age_is_taken_at_the_february_of_the_season_it_describes(self):
        # born 1995-02-19, and Fleaflicker's 2025 season hits Feb 1 2026
        """Season age has to be a fixed point inside that season. Reading
        `detail.age` instead dates every historical row to whenever the file
        was scraped, so a 5-season fit runs on drifting labels"""
        self.assertAlmostEqual(sim.age_at("1995-02-19", 2025), 30.95, places=1)
        self.assertAlmostEqual(sim.age_at("1995-02-19", 2021), 26.95, places=1)


class GPModelSelection(unittest.TestCase):
    """The comparison exists to REJECT models, so it has to be out of sample.
    An in-sample table always ranks the richest model first and would have us
    adopt per-player projections that predict nothing"""

    def test_nothing_beats_the_pool_mean_when_games_played_is_pure_noise(self):
        """The floor the bake-off is read against. On rows where GP is pure
        noise nothing may beat the flat prior, or the table is ranking overfit
        """
        rng = random.Random(7)
        rows = [{"name": "P%d" % i, "age": rng.uniform(20, 36),
                 "hist": [rng.gauss(58, 17) for _ in range(5)],
                 "rate": rng.uniform(20, 50), "y": rng.gauss(58, 17)}
                for i in range(500)]
        err = sim.gp_models(rows)
        self.assertIn("mean", err)
        for name, rmse in err.items():
            self.assertGreater(rmse, err["mean"] - 0.5,
                               "%s beat the mean on noise" % name)

    def test_age_wins_when_the_games_really_are_age_driven(self):
        """Guard the other way. A harness that always prefers the constant is
        just as useless, so make GP genuinely age-driven and age has to win"""
        rng = random.Random(7)
        rows = []
        for i in range(500):
            age = rng.uniform(20, 36)
            rows.append({"name": "P%d" % i, "age": age,
                         "hist": [rng.gauss(58, 17) for _ in range(5)],
                         "rate": rng.uniform(20, 50),
                         "y": 110 - 2.0 * age + rng.gauss(0, 6)})
        err = sim.gp_models(rows)
        self.assertLess(err["age"], err["mean"] - 5)


class GPFoldThatCannotBeFitted(unittest.TestCase):
    """Every model in the bake-off has to be scored on the SAME rows, or the
    RMSE column is not a comparison. A fold whose design comes back singular
    leaves that model's rows as NaN, and `_rmse` drops NaNs, so it ends up
    scored on 4/5 of the rows while its competitors get 5/5 and nothing prints
    """

    def test_a_model_that_loses_a_fold_is_refused_rather_than_scored_on_the_rest(self):
        rows = [{"name": "P%d" % i, "y": 60.0 + i, "hist": [60], "rate": 30.0,
                 "age": 25.0} for i in range(10)]
        self.addCleanup(gp.GP_MODELS.pop, "flat", None)
        # collinear with the intercept the fit always carries, so no fold of it
        # can be solved
        gp.GP_MODELS["flat"] = lambda r: (1.0,)
        with self.assertRaises(ValueError) as e:
            gp.gp_sq_errors(rows, models=("flat",))
        self.assertIn("flat", str(e.exception))


class GPUncertainty(unittest.TestCase):
    """The uncertainty a gap is judged against has to be resampled over
    PLAYERS. The sd across FOLD SHUFFLES is which player landed in which fold,
    not sampling uncertainty over the ~286 players, and it understates the real
    spread more than tenfold"""

    def test_the_reported_uncertainty_covers_the_gap_it_is_used_to_judge(self):
        b = sim.gp_bootstrap(sim.gp_rows(), models=("gp1", "gp5", "mean"), n=400)
        self.assertGreater(b["gp5"]["delta"], 0.0)
        self.assertLess(b["gp5"]["lo"], 0.0)
        self.assertGreater(b["mean"]["lo"], 0.0)


class GPRows(unittest.TestCase):
    def test_history_is_strictly_earlier_than_the_season_being_predicted(self):
        """A row whose `hist` contains its own target season makes every model
        look clairvoyant and would justify per-player projections outright"""
        rows = sim.gp_rows()
        self.assertGreater(len(rows), 300)
        for r in rows:
            self.assertTrue(r["seasons"], r)
            self.assertLess(max(r["seasons"]), r["season"], r)

    def test_history_is_most_recent_first(self):
        """`gp1` reads `hist[0]`, so the order carries meaning rather than
        being cosmetic"""
        for r in sim.gp_rows():
            self.assertEqual(r["seasons"], sorted(r["seasons"], reverse=True), r)


class GPProjection(unittest.TestCase):
    """GP is the input this study calls dominant, ~10x any format effect, and
    taking one injury season literally is the biggest error available here, so
    a projection has to regress toward the pool"""

    def test_the_gp_fit_coefficients_are_the_ones_the_readme_publishes(self):
        """The formula is quoted as one an eval author can apply by hand, and
        it is a FIT, so a re-scrape moves it silently while every GP in every
        table stays as printed. Pinned so a refit has to be a deliberate re-
        publish"""
        intercept, per_gp, per_rate = sim.gp_model()
        self.assertAlmostEqual(intercept, 25.7, delta=0.05)
        self.assertAlmostEqual(per_gp, 0.368, delta=0.005)
        self.assertAlmostEqual(per_rate, 0.432, delta=0.005)

    def test_an_outlier_injury_season_regresses_upward(self):
        self.assertGreater(sim.project_gp("Joel Embiid"), 45)

    def test_an_iron_man_season_regresses_downward(self):
        """Regression pulls the top down too, since 82 GP is not a projection
        """
        self.assertLess(sim.project_gp("Desmond Bane"), 75)

    def test_the_durable_player_still_projects_above_the_fragile_one(self):
        """Compressed, not erased, so the ordering has to survive"""
        self.assertGreater(sim.project_gp("Nikola Jokić"),
                           sim.project_gp("Joel Embiid"))

    def test_a_superstar_rate_does_not_buy_more_games_than_an_all_star_rate(self):
        """Empirical next-season GP by last-season rate is concave and turns
        DOWN, 57.6 at rate 20-25, peaking 63.2 at 30-35, then 59.6 above 45. A
        rate term that keeps adding past the peak over-projects exactly the
        star-rate players every headline table is built on"""
        self.assertLessEqual(sim.project_gp("nobody", gp=65, rate=65.0),
                             sim.project_gp("nobody", gp=65, rate=35.0) + 0.5)

    def test_a_fringe_player_projects_fewer_games_than_a_starter_at_the_same_gp(self):
        """Expected GP falls off hard below rotation quality, ~40 GP at rate
        <10 against ~63 at rate 30-40, so a fit gated to rotation players
        projects the whole bench ~10 games too high. Scoring rate is the
        feature that fixes it, and `sim.py gp` shows age does not"""
        self.assertGreater(sim.project_gp("Desmond Bane"),
                           sim.project_gp("Sion James") + 4)


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
        for name in ("Fred VanVleet", "Amen Thompson"):
            raw = rostered(name, projected=False)
            p = rostered(name)
            self.assertNotEqual(raw["gp"], p["gp"])
            row, = [l for l in table.splitlines() if l.startswith("  " + name)]
            printed, = re.findall(r"[\d.]+ rate +(\d+) gp", row)
            self.assertEqual(int(printed), p["gp"], row)


class NoPoolHistory(unittest.TestCase):
    """`our_roster` feeds the GP fit the POOL's rate, and a player the pool has
    never seen has none to give it, so he is the one row where that branch goes
    the other way. A TRUE rookie's file row is a 0-GP, 0.0-rate shell with no
    actual rate anywhere on it, so without the projection he prices as a hole
    on a roster that really holds a body"""

    ROOKIE = "Thomas Sorber"

    def test_a_player_the_pool_has_never_seen_still_prices_as_a_body(self):
        raw, = [q for q in sim._load(ROOKIE_ROSTER) if q["n"] == self.ROOKIE]
        p = rostered(self.ROOKIE, ROOKIE_ROSTER)

        self.assertEqual((raw["avg"], raw["gp"]), (0.0, 0))
        self.assertEqual(sim.evidence_flags(self.ROOKIE), ["nopool"])
        self.assertAlmostEqual(p["avg"], sim.projected_rate(self.ROOKIE))
        self.assertGreater(p["gp"], 20)
        self.assertEqual(p["gp"], round(sim.project_gp(
            self.ROOKIE, gp=0, rate=sim.projected_rate(self.ROOKIE))))

    def test_a_body_with_neither_a_pool_season_nor_a_projection_still_prices(self):
        """Both fallbacks gone, an undrafted body the pool never saw and the
        feed does not carry. `project_gp` RAISES on a name with no rate at all
        (`PoolJoinByName`), and a roster that will not load prices no trade at
        all, so the last fallback has to be the row's own 0.0 rather than None
        """
        path = roster_file({"n": "Unknown Rookie", "tm": "LAC", "avg": 0.0,
                            "tot": 0.0, "gp": 0, "posLabel": "F",
                            "elig": ["SF", "PF"]})
        self.assertIsNone(sim.projected_rate("Unknown Rookie"))
        p, = sim.our_roster(path)
        self.assertEqual(p["gp"], round(sim.project_gp("Unknown Rookie",
                                                       gp=0, rate=0.0)))


class RateEvidence(unittest.TestCase):
    """A rate posted over a fragment season no longer carries the whole `Δw`,
    the projection replaces it. That same fragment is still the GP fit's main
    input and GP is the dominant one, so how many games the pool saw is what
    says whether the `Δw` is a measurement or an upper bound (`Eval Definitions
    §Δw`)"""

    def test_it_reports_the_games_the_gp_projection_rests_on(self):
        self.assertEqual(sim.rate_evidence("Kevin Porter")["gp"], 38)
        self.assertEqual(sim.rate_evidence("Precious Achiuwa")["gp"], 73)

    def test_it_reports_a_whole_season_missing_from_the_pool(self):
        """A missed season is ABSENT from the pool rather than a zero, so the
        GP fit cannot see it at all and expected GP is conditional on him
        playing"""
        self.assertTrue(sim.rate_evidence("Kevin Porter")["missed"])
        self.assertFalse(sim.rate_evidence("Precious Achiuwa")["missed"])

    def test_a_missed_most_recent_season_counts_too(self):
        """A trailing absence is the same censoring as an interior one and the
        one the GP fit is blindest to, so it cannot read as a full season"""
        self.assertTrue(sim.rate_evidence("Kyrie Irving")["missed"])
        self.assertTrue(sim.rate_evidence("Fred VanVleet")["missed"])

    def test_a_late_arrival_is_not_a_missed_season(self):
        """Seasons before a player entered the pool are not absences. Only a
        gap INSIDE his history is one, or every rookie reads as injured"""
        self.assertFalse(sim.rate_evidence("Stephon Castle")["missed"])

    def test_it_counts_the_rotation_seasons_the_role_rests_on(self):
        """Rate >= 15 is where GP starts measuring health rather than role
        (`Eval Definitions §LATE`), so it is also the bar a season clears to be
        evidence the role is real"""
        self.assertEqual(sim.rate_evidence("Kevin Porter")["rotation"], 4)
        self.assertEqual(sim.rate_evidence("Ty Jerome")["rotation"], 2)

    def test_it_names_every_flag_code_an_eval_has_to_carry(self):
        """`Eval Definitions §Output` fixes the vocabulary and §Durability
        fixes the fragment band at 10-25 games. An eval author reads these off
        here rather than eyeballing five seasons of pool rows per player, so
        the PUBLIC function has to name all four codes, or a caller gets two of
        the four with no sign the others exist"""
        self.assertEqual(sim.evidence_flags("Ty Jerome"), ["frag", "rot2"])
        self.assertEqual(sim.evidence_flags("Kevin Porter"), ["miss"])
        self.assertEqual(sim.evidence_flags("Precious Achiuwa"), [])
        self.assertEqual(sim.evidence_flags("Nobody At All"), ["nopool"])

    def test_a_season_below_the_fragment_band_still_flags(self):
        """§Durability writes the band as 10-25 to separate a fragment from a
        whole missed season, but a 5-game season is PRESENT in the pool rather
        than absent, so a lower bound silently passes the thinnest rows of all
        """
        self.assertEqual(sim.evidence_flags("Walker Kessler"), ["frag"])


class EvidenceFlagsInThePlayersTable(unittest.TestCase):
    """`rate_evidence` and `evidence_flags` are pinned against the pool by
    `RateEvidence`, but the reader never calls them, he reads `sim.py players`.
    The flag is the only thing on that row saying whether the `Δw` beside it is
    a measurement or an upper bound, and an unflagged row reads as a clean one,
    so a flag computed and not printed, or printed against the wrong row, is
    worse than no flag column at all"""

    @classmethod
    def setUpClass(cls):
        cls.rows = {}
        ours = sim.our_roster()
        for line in render("players").splitlines():
            for p in ours:
                if line.strip().startswith(p["n"] + " ") and p["n"] not in cls.rows:
                    cls.rows[p["n"]] = line

    def test_a_season_missing_from_the_pool_reaches_the_row_it_belongs_to(self):
        """Kyrie and VanVleet are the two on our roster with a whole season
        gone, and exactly the rows whose rate is an upper bound"""
        self.assertIn("miss", self.rows["Kyrie Irving"])
        self.assertIn("miss", self.rows["Fred VanVleet"])

    def test_every_row_prints_the_flags_its_evidence_implies_and_no_others(self):
        """Both ways. Whatever `evidence_flags` names is what his row carries,
        and a row carries nothing it did not earn, so a flag printed against
        the wrong row clears the first half and fails here.

        `rotN` carries the count rather than just a mark, the bar being 3
        seasons at rate >= 15 (`Eval Definitions §LATE`). Below it the rate is
        a role that has not held up yet, at or above it the reader may read the
        row clean"""
        for name, line in self.rows.items():
            with self.subTest(player=name):
                self.assertEqual(
                    re.findall(r"frag|miss|nopool|rot\d", line),
                    sim.evidence_flags(name), line)

    def test_the_table_has_a_row_for_every_player_on_the_roster(self):
        """The agreement above is vacuous for any player the scan missed"""
        self.assertEqual(sorted(self.rows),
                         sorted(p["n"] for p in sim.our_roster()))


class DefinitionsVocabulary(unittest.TestCase):
    """`Eval Definitions` is cited by section instead of restated and it owns
    the canonical flag table. Both halves only work if the citations resolve,
    since a `§Delta w` that names no section sends the reader looking for a
    definition that is not there, and a flag code printed on a row but absent
    from the table is a vocabulary the rest of the repo cannot carry"""

    DEFS = os.path.join(sim.HERE, os.pardir, "Eval Definitions.md")

    @classmethod
    def setUpClass(cls):
        cls.text = read_text(cls.DEFS)
        cls.sections = set()
        for h in re.findall(r"^#+ +(.*)$", cls.text, re.M):
            head = h.replace("`", "").replace("*", "")
            cls.sections.add(re.split(r" +[-—] +", head)[0].strip())
        cls.source = read_text(sim.__file__)

    def test_every_section_sim_cites_is_a_section_that_exists(self):
        """A citation runs to the closing backtick rather than to the first
        space, since the definitions carry multi-word headings, and stopping at
        the space checks a section name nobody wrote. Every citation has to be
        inside the backticks for that to hold, so the two counts are compared
        rather than assumed"""
        cited = set(re.findall(r"`Eval Definitions §([^`]+)`", self.source))
        self.assertTrue(cited, "nothing cites the definitions any more")
        self.assertEqual(len(re.findall(r"`Eval Definitions §", self.source)),
                         len(re.findall(r"Eval Definitions §", self.source)),
                         "a citation outside backticks is not being checked")
        for name in cited:
            with self.subTest(section=name.rstrip(".,:")):
                self.assertIn(name.rstrip(".,:"), self.sections)

    def test_the_flag_legend_and_the_canonical_table_are_the_same_vocabulary(self):
        """Both directions. A code the table prints and §Output does not define
        cannot be carried into an eval, and a code §Output sources FROM `sim.py
        players` that this table never prints is a row the eval author is told
        to read off a report that does not emit it"""
        canon = dict(re.findall(r"^\| `(\w+)` *\|([^|]*)\|", self.text, re.M))
        out = render("players")
        legend = set(re.findall(r"`([a-z]\w*)`", out[out.index("flag column"):]))
        self.assertLessEqual(legend, set(canon), legend - set(canon))
        for code, desc in canon.items():
            if "sim.py players" in desc:
                with self.subTest(flag=code):
                    self.assertIn(code, legend)


class UnprojectedRates(unittest.TestCase):
    """`Eval Definitions §Output` says a player the projection feed does not
    carry keeps LAST SEASON's average, which is a different kind of number from
    every other row in the column. Nothing in the rate itself says so, so the
    row has to carry `noproj` or a stale average reads as a projection"""

    UNPROJECTED = {"n": "Chaney Johnson", "tm": "BKN", "avg": 19.1,
                   "tot": 343.0, "gp": 18, "posLabel": "SG/SF",
                   "elig": ["SF", "SG"]}

    def test_a_player_with_no_projection_is_flagged_on_his_row(self):
        path = roster_file(self.UNPROJECTED)
        self.assertIsNone(sim.projected_rate("Chaney Johnson"))
        row, = [l for l in render("players", path).splitlines()
                if "Chaney Johnson" in l]
        self.assertIn("noproj", row)

    def test_a_projected_player_is_not_flagged(self):
        row, = [l for l in render("players").splitlines() if "Josh Giddey" in l]
        self.assertNotIn("noproj", row)

    def test_an_unprojected_rate_is_last_seasons_average_untouched(self):
        """The flag says the rate is last season's, nothing says it still IS. A
        fallback that regressed or part-projected him would be a third kind of
        number in the column with only two labels for it"""
        p, = sim.our_roster(roster_file(self.UNPROJECTED))
        self.assertEqual(p["avg"], self.UNPROJECTED["avg"])


class ProjectionSnapshot(unittest.TestCase):
    """The rate every `Δw` runs on is assembled across two directories and a
    file on disk. `projections` writes a snapshot of someone else's stat lines
    and `sim` joins it by name and scores it under our rules (`Eval Definitions
    §Δw`). Every other test here checks only whether a row was projected AT
    ALL, so the number itself could arrive halved, stale, hand-set or scored as
    one night's line and nothing would print differently"""

    def test_the_rate_on_a_roster_row_is_the_committed_snapshots_line_scored(self):
        stats = {r["name"]: r["stats"]
                 for r in json.loads(read_text(SNAPSHOT))["rows"]}
        scoring = skill_module("projections", "scoring")
        giddey = scoring.rate(scoring.line_from_sleeper(stats["Josh Giddey"]))

        self.assertGreater(giddey, 25)
        self.assertLess(giddey, 60)
        self.assertAlmostEqual(sim.projected_rate("Josh Giddey"), giddey, places=9)
        p = rostered("Josh Giddey")
        self.assertAlmostEqual(p["avg"], giddey, places=6)

    def test_the_join_reaches_essentially_the_whole_roster(self):
        """A join that rots, a normalisation change or a feed re-cut or a moved
        snapshot, puts last season's average back under every row it drops.
        `noproj` makes that visible one row at a time, and only a count makes
        it visible when it happens wholesale"""
        ours = sim.our_roster()
        missing = [p["n"] for p in ours if sim.projected_rate(p["n"]) is None]
        self.assertGreater(len(ours), 20)
        self.assertGreaterEqual(1 - len(missing) / len(ours), 0.93, missing)


class UnusableSnapshot(unittest.TestCase):
    """A snapshot that cannot be read is indistinguishable, row by row, from a
    feed that carries nobody. Every rate falls back to last season's average
    and every row flags `noproj`, which is the whole study re-cut onto the
    basis `projections` exists to replace, and eleven of the twelve reports
    print no flag column at all"""

    def test_a_missing_snapshot_is_refused_rather_than_repricing_everybody(self):
        with projection_snapshot(None):
            with self.assertRaises(RuntimeError) as e:
                sim.our_roster()
        self.assertIn("sleeper-2026.json", str(e.exception))

    def test_a_snapshot_carrying_nobody_is_refused_too(self):
        """It parses, so nothing upstream complains, and a feed re-cut that
        breaks `projected_rows` writes exactly this file. Zero rows is not a
        thin feed, it is no feed"""
        with projection_snapshot(sleeper_rows()):
            with self.assertRaises(RuntimeError):
                sim.our_roster()

    def test_a_feed_that_simply_misses_a_player_still_prices_everyone_else(self):
        """The refusal is about the SNAPSHOT and must not swallow the one case
        that is a fact about a player, a usable feed that does not carry him.
        He keeps last season's average, everybody in the feed is priced off it,
        and only his row says so"""
        with projection_snapshot(sleeper_rows(
                ("Josh Giddey", {"pts": 30.0, "reb": 10.0, "dreb": 7.0,
                                 "ast": 10.0, "stl": 1.0, "blk": 0.5, "to": 3.0,
                                 "fgm": 11.0, "fga": 22.0, "ftm": 5.0,
                                 "fta": 6.0, "tpm": 3.0, "min": 35.0}))):
            priced = {p["n"]: p["avg"] for p in sim.our_roster()}
            self.assertIsNone(sim.projected_rate("Desmond Bane"))
        raw = {p["n"]: p["avg"] for p in sim.our_roster(projected=False)}

        self.assertNotEqual(priced["Josh Giddey"], raw["Josh Giddey"])
        self.assertEqual(priced["Desmond Bane"], raw["Desmond Bane"])


class ProjectedRateReachesTheWinFigure(unittest.TestCase):
    """The snapshot is joined, scored and stapled onto a roster row four files
    away from the thing that consumes it. Every other test here stops at the
    roster row, so a rate that never actually reached the nightly lineup, or a
    GP that moved when the projection did, would read as a clean pass"""

    def _snapshot_with(self, name, stats):
        snap = json.loads(read_text(SNAPSHOT))
        for r in snap["rows"]:
            if r["name"] == name:
                r["stats"] = stats
        return json.dumps(snap)

    def test_projecting_a_starter_up_pays_wins_without_buying_him_games(self):
        best = max(json.loads(read_text(SNAPSHOT))["rows"],
                   key=lambda r: sim.projected_rate(r["name"]) or 0)

        with projection_snapshot(self._snapshot_with("Josh Giddey",
                                                     best["stats"])):
            up = rostered("Josh Giddey")
            up_pf = sim.run(sim.basis(), trials=8)["pf"]
        base = rostered("Josh Giddey")
        base_pf = sim.run(sim.basis(), trials=8)["pf"]

        self.assertGreater(up["avg"], base["avg"] + 5)
        self.assertGreater(up_pf - base_pf, 500)
        self.assertEqual(up["gp"], base["gp"])

        with projection_snapshot(self._snapshot_with(
                "Josh Giddey", {"pts": 3.5, "reb": 1.4, "dreb": 1.0, "ast": 0.8,
                                "stl": 0.2, "blk": 0.1, "to": 0.7, "fgm": 1.4,
                                "fga": 3.8, "ftm": 0.6, "fta": 0.8, "tpm": 0.3,
                                "min": 9.0})):
            down = rostered("Josh Giddey")
        self.assertLess(down["avg"], 15)
        self.assertEqual(down["gp"], base["gp"])


class Durability(unittest.TestCase):
    """Characterisation test rather than a red to green cycle. It pins the
    conclusion the README's durability section rests on, that with
    foreknowledge of who plays GP-elasticity is 1, so the ONLY format-derived
    injury adjustment is the lock-in. If this stops holding, that section has
    to be rewritten"""

    def test_value_is_proportional_to_games_played(self):
        full = sim.our_roster() + sim.EXPANSION
        trials = 200

        def pf(gp):
            roster = [sim.star(45, gp) if p["n"] == "Jalen Suggs" else p for p in full]
            return sim.run(roster, trials=trials)["pf"]

        absent, healthy = pf(0), pf(82)
        for gp in (41, 62):
            retained = (pf(gp) - absent) / (healthy - absent)
            self.assertAlmostEqual(retained, gp / 82, delta=0.02)


class BackfillGrade(unittest.TestCase):
    """Regression pin rather than a red to green cycle. `scenarios` tells the
    reader that `breakevens` reports the bracket out to one named refund grade,
    which is a cross-table claim otherwise held together by two people typing
    the same pair of numbers into two files' worth of prints"""

    def test_the_grade_scenarios_cites_is_a_row_breakevens_actually_reports(self):
        cited, = re.findall(r"bracket to a (\S+) refund", render("scenarios"))
        rows = [l.split()[0] for l in render("breakevens").splitlines() if l.split()]
        self.assertIn(cited, rows)


class ScenarioShapes(unittest.TestCase):
    """`breakevens` states GP and position on every row "because they move the
    answer several points", and `scenarios` states them once above the table
    for the rows whose labels do not. So that sentence carries the whole
    table's worth of the warning, and a reader who takes a bare label at its
    word compares a real 65-GP centre against a row priced as a 68-GP forward
    """

    @classmethod
    def setUpClass(cls):
        cls.head = render("scenarios").split("scenario ")[0]

    def test_the_centre_rows_are_not_described_as_the_default_forward(self):
        self.assertRegex(self.head, r"Jokic[\s\S]*?65-GP C\b")

    def test_the_multi_body_rows_say_they_are_not_all_the_default_either(self):
        self.assertIn("76", self.head)


class DurabilityHeader(unittest.TestCase):
    """The GP row's header names its subject and quotes his line. `our_roster`
    re-projects both the rate and the GP every time the feed moves, so a line
    typed into the header describes whoever the roster carried the day it was
    typed while the row underneath is measured on today's"""

    def test_the_gp_row_quotes_the_subject_as_the_roster_carries_him(self):
        sub, = [p for p in sim.basis() if p["n"] == durability.SUBJECT]
        self.assertIn("%s (%.1f @ %d)"
                      % (durability.SUBJECT, sub["avg"], sub["gp"]),
                      render("durability"))


class UnsignedPlayer(unittest.TestCase):
    """Most committed rosters hold a player unsigned in the NBA, purely because
    the snapshot is taken in July. Given no schedule at all he suits up for
    nothing and prices as most of a body of `Δw` short, a snapshot artifact
    reading as a finding about the player. He is a body with an unknown
    schedule, which is what `SIM_TM` is for"""

    def test_an_unsigned_body_scores_what_he_would_on_the_assumed_schedule(self):
        """The whole claim in the only terms that matter, a season's PF. A
        floor, "he beats an empty slot", passes on a quarter of a schedule, and
        an rng-draw assertion tests the mechanism rather than the season"""
        base = sim.basis()
        free = {"n": "FREE", "tm": "FA", "avg": 30.0, "tot": 0.0, "gp": 70,
                "posLabel": "F", "elig": ["SF", "PF"]}
        unsigned = sim.run(base + [free], trials=8)["pf"]
        self.assertEqual(unsigned, sim.run(base + [dict(free, tm=sim.SIM_TM)],
                                           trials=8)["pf"])
        self.assertGreater(unsigned,
                           sim.run(base, trials=8)["pf"] + 500)

    def test_a_team_the_schedule_has_never_heard_of_fails(self):
        """The other side of the same boundary. "FA" is a fact the feed states,
        "PHO" is the feed having renamed Phoenix out from under the join, and
        inheriting SIM_TM there prices the body on the DEEPEST light-night
        schedule of the 30 while nothing prints an error"""
        base = sim.basis()
        renamed = {"n": "RENAMED", "tm": "PHO", "avg": 30.0, "tot": 0.0,
                   "gp": 70, "posLabel": "F", "elig": ["SF", "PF"]}
        with self.assertRaises(KeyError) as e:
            sim.run(base + [renamed], trials=1)
        self.assertIn("PHO", str(e.exception))

    def test_the_players_table_says_the_schedule_is_assumed(self):
        """`Δw` on an assumed schedule is not the same claim as `Δw` on his
        own, and nothing else on the row distinguishes them"""
        path = roster_file({"n": "Bradley Beal", "tm": "FA", "avg": 24.0,
                            "tot": 1000.0, "gp": 42, "posLabel": "G",
                            "elig": ["PG", "SG"]},
                           {"n": "Desmond Bane", "tm": "MEM", "avg": 33.0,
                            "tot": 2706.0, "gp": 82, "posLabel": "G",
                            "elig": ["PG", "SG"]})
        out = render("players", path)
        beal, = [l for l in out.splitlines() if "Bradley Beal" in l]
        bane, = [l for l in out.splitlines() if "Desmond Bane" in l]
        self.assertIn("fa", beal.split())
        self.assertNotIn("fa", bane.split())


class Facade(unittest.TestCase):
    """`sim` re-exports, and five names are state a caller REPLACES. A module
    `__getattr__` fires only when normal lookup FAILS, so an assignment on the
    facade creates the very entry that stops it failing, and the write reads
    back fine while reaching nobody inside `simlib`. Reads fixed and writes not
    is the silent-wrong-number shape, pointed the other way"""

    def test_setting_the_roster_on_the_facade_reaches_basis(self):
        self.addCleanup(setattr, roster_mod, "ROSTER", roster_mod.ROSTER)
        sim.ROSTER = THEIR_ROSTER
        self.assertEqual([p["n"] for p in sim.basis()],
                         [p["n"] for p in sim.basis(THEIR_ROSTER)])

    def test_setting_a_name_the_facade_only_re_exports_fails(self):
        """Five names are live state, and the facade re-exports a hundred more,
        every one of them bound here as a reference. An assignment to one of
        those lands in the facade's own dict, reads back the caller's value and
        leaves every reader inside `simlib` on the real one"""
        was = sim.SLOTS
        with self.assertRaises(AttributeError) as e:
            sim.SLOTS = []
        self.assertIs(sim.SLOTS, was)
        self.assertIn("simlib", str(e.exception))

    def test_a_name_the_facade_never_exported_is_settable_more_than_once(self):
        """`ModuleType.__setattr__` writes into the same module dict the
        refusal above asks about, so a name `simlib` has never heard of is
        accepted once and the second assignment comes back "re-exported from
        simlib, not owned here" about it. A guard that mis-states what it is
        guarding sends the reader looking for a `simlib` name that does not
        exist"""
        sim.scratch = 1
        self.addCleanup(delattr, sim, "scratch")
        sim.scratch = 2
        self.assertEqual(sim.scratch, 2)

    def test_replacing_run_on_the_facade_reaches_simlib(self):
        real = engine.run
        self.addCleanup(setattr, engine, "run", real)
        seen = []
        sim.run = lambda roster, **kw: (seen.append(len(roster))
                                        or real(roster, **dict(kw, trials=2)))
        R = flat_R()
        sim.player_wins(sim.basis(), ["Jalen Suggs"], blocks=1, trials=2, R=R)
        self.assertTrue(seen)

    def test_a_star_import_carries_the_five_live_names_and_not_the_plumbing(self):
        """`from sim import *` is what a REPL and a saved snippet do. It copies
        the module DICT, and the five live names are in nobody's dict, they are
        served by `__getattr__`, so `run`, the first line of the documented
        import path, comes out of a star import as a NameError.

        The same dict is why the star can hand back `sys`, `types` and four
        `simlib` module handles, rebinding whatever the caller already had
        under those names"""
        ns = {}
        exec("from sim import *", ns)
        starred = set(ns) - {"__builtins__"}
        self.assertLessEqual({"run", "player_wins", "gp_bootstrap",
                              "PLAYER_BLOCKS", "ROSTER", "basis"}, starred)
        self.assertIs(ns["run"], engine.run)
        self.assertEqual(starred & {"sys", "types", "roster", "value"}, set())


class PlayerBlocksIsOneConstant(unittest.TestCase):
    """`players` prints "averaged over N independent seed blocks" off the
    constant, while `player_wins`, the import path a deal is actually priced
    on, is what runs them. Move the constant and the printed caveat describes a
    measurement nobody ran, on the table `eval-team` quotes"""

    def test_player_wins_takes_its_block_count_from_the_constant(self):
        self.addCleanup(setattr, value, "PLAYER_BLOCKS", value.PLAYER_BLOCKS)
        value.PLAYER_BLOCKS = 2
        R = flat_R()
        w = sim.player_wins(sim.basis(), ["Jalen Suggs"], trials=2, R=R)
        self.assertEqual(len(w["Jalen Suggs"][2]), 2)

    def test_incoming_wins_takes_the_same_one(self):
        self.addCleanup(setattr, value, "PLAYER_BLOCKS", value.PLAYER_BLOCKS)
        value.PLAYER_BLOCKS = 2
        R = flat_R()
        body = sim.star(40.0, 68, ("C",), n="INCOMING")
        w = sim.incoming_wins(sim.basis(), [body], trials=2, R=R)
        self.assertEqual(len(w["INCOMING"][2]), 2)


if __name__ == "__main__":
    unittest.main()
