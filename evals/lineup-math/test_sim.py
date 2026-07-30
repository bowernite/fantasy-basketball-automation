"""python3 -m unittest test_sim -v"""
import collections
import json
import os
import random
import re
import statistics
import subprocess
import sys
import tempfile
import unittest

import fetch_data
import sim

# A committed counterparty file, so the `--roster` path is exercised on a real
# team rather than only on ours (team 161020, `team-info`).
THEIR_ROSTER = "roster-161020-2025-26.json"


def roster_payload(**over):
    """One `FetchRoster?season=` row, trimmed to the keys the transform reads.

    Fleaflicker omits zero/default fields entirely, so the shape that bites is a
    row with NO `seasonAverage` / `seasonTotal` / `rankFantasy` at all.
    """
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
    """`--roster their.json` is advertised for any counterparty but nothing built
    the file, so `REPL theirs` was not reproducible. The schema is what makes it
    reproducible, so it is asserted rather than described."""

    def test_a_played_season_becomes_a_priceable_roster_row(self):
        self.assertEqual(fetch_data.roster_rows(roster_payload()),
                         [{"n": "Darius Garland", "tm": "LAC",
                           "avg": 31.894444, "tot": 1435.25, "gp": 45,
                           "posLabel": "G", "elig": ["PG", "SG"]}])

    def test_a_player_who_missed_the_whole_season_still_carries_his_positions(self):
        """A 0-GP row has no `seasonAverage`, so it also has no `rankFantasy` --
        which is how Kyrie and VanVleet reached the roster file with `elig: []`
        and had to be guessed at as guards in `our_roster`. `positionEligibility`
        is on the row whether or not he played."""
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


class CLI(unittest.TestCase):
    def test_a_misspelled_report_name_fails_instead_of_printing_another_one(self):
        """`trades` and `team-eval` both mandate a sim run before recommending a
        deal. A silent fallback to `calibration` means `sim.py breakeven`
        (singular) exits 0 having printed a table the reader did not ask for,
        and he books it as the break-evens he thinks he just ran."""
        p = subprocess.run([sys.executable, "sim.py", "breakeven"],
                           cwd=os.path.dirname(os.path.abspath(sim.__file__)),
                           capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("CALIBRATION", p.stdout)


class Schedule(unittest.TestCase):
    """Every conclusion is a count of slot-nights, so a phantom game is a
    phantom night of value."""

    def test_every_team_plays_82_games(self):
        played = collections.Counter()
        for _, tms in sim.NIGHTS:
            for t in tms:
                played[t] += 1
        # The NBA Cup final is a 83rd game for its two participants: it produces
        # real box scores but does not count toward the 82-game schedule.
        self.assertEqual(sorted(collections.Counter(played.values()).items()),
                         [(82, 28), (83, 2)])


class FantasyCalendar(unittest.TestCase):
    """Weekly scores are the unit a matchup is won in, so how nights bucket into
    periods is not cosmetic."""

    def test_games_per_period_matches_the_real_spread(self):
        """Real periods carry 28-56 NBA games. An even split of nights across
        periods implies ~49-56 and erases most of the weekly variance the sim
        exists to explain."""
        games = collections.Counter()
        for (_, tms), w in zip(sim.NIGHTS, sim.WEEK_OF):
            if w is not None:
                games[w] += len(tms) // 2
        self.assertEqual((min(games.values()), max(games.values())), (28, 56))


class CommonRandomNumbers(unittest.TestCase):
    def test_swapping_a_player_for_his_own_clone_changes_nothing(self):
        """A scenario must perturb only what it changes. Appending the incoming
        player rather than replacing in place shifts every later player's
        availability draw, which buries sub-0.1-win deltas in Monte-Carlo noise."""
        full = sim.our_roster() + sim.EXPANSION
        clone = dict(next(p for p in full if p["n"] == "Naz Reid"))
        same = sim.swap(full, ["Naz Reid"], [clone])
        self.assertEqual(sim.run(same, trials=8)["pf"], sim.run(full, trials=8)["pf"])


class AbsenceBlocks(unittest.TestCase):
    """`_availability` places IL blocks CIRCULARLY, on purpose. So the onset scan
    has to be circular too -- ~26% of player-seasons come out with both their
    first and last team-game night absent, and a left-to-right scan splits that
    one block in two, letting a single injury surprise you twice and inflating
    every lock-in figure ~9%."""

    def test_a_block_that_wraps_the_end_of_the_season_is_one_block(self):
        # his own team-game nights; absent for 50, then 10 and 20 -- ONE block.
        self.assertEqual(sim._onsets([10, 20, 30, 40, 50], {30, 40}), [50])

    def test_the_block_statistics_are_measured_on_the_roster_you_pass(self):
        """The lock-in correction is worth exactly the ratio of absence NIGHTS to
        absence BLOCKS, and the README filed "711 nights in ~103 blocks of ~6.9"
        under a heading naming the 38-man roster when neither roster produces it.
        Measuring it live per roster is the fix."""
        small = sim.absence_blocks(sim.our_roster(), seeds=6)
        big = sim.absence_blocks(sim.our_roster() + sim.EXPANSION, seeds=6)
        self.assertGreater(big["nights"], small["nights"] + 100)
        # the factor the whole correction rests on
        self.assertGreater(small["mean_block"], 7.0)

    def test_a_player_who_never_suits_up_can_still_be_surprised_once(self):
        """The other side of the circular fix: with nothing played there is no
        'night before that he played', but opening night is still a surprise."""
        self.assertEqual(sim._onsets([10, 20, 30], set()), [10])


class SurpriseScratches(unittest.TestCase):
    """A scratch can only surprise a lineup-setter on the FIRST night of an
    absence block; after that he is on the public injury report. Drawing the
    surprise from every absence night instead is what made the lock-in penalty
    ~10x too large."""

    def test_a_season_long_absence_can_only_surprise_you_once(self):
        glass = [dict(sim.star(45, 0, ("SF", "PF"), "LAL", "GLASS"), surprise=1.0)]
        _, starts, _, _ = sim.season(glass, seed=101, bursty=True)
        self.assertLessEqual(starts["GLASS"], 1)

    def test_a_lone_scattered_absence_is_still_a_surprise(self):
        """Guard on the other side: a rest day IS the first night of its own
        block, so the correction must not suppress it. A high-GP veteran resting
        scattered single games is the shape the lock-in costs the most."""
        # LAL play 82; he misses exactly one, which is its own onset. ~79% of
        # NBA nights fall inside the scored periods, so over 20 seeds that lone
        # absence lands in-window ~16 times.
        rester = [dict(sim.star(45, 81, ("SF", "PF"), "LAL", "REST"), surprise=1.0)]
        wasted = 0
        for seed in range(101, 121):
            _, starts, pts, _ = sim.season(rester, seed=seed, bursty=True)
            wasted += starts["REST"] - round(pts["REST"] / 45)  # ghosts score 0
        self.assertGreaterEqual(wasted, 10)

    def test_a_small_surprise_rate_still_costs_something(self):
        """Each block must be an INDEPENDENT draw. Taking `round(q x blocks)`
        instead truncates to zero for every player with fewer than ~5 absence
        blocks -- which is most of a roster -- so a 10% rate silently became 0%
        and the corrected penalty read as exactly nothing."""
        full = sim.our_roster() + sim.EXPANSION
        base = sim.run(full, trials=40, bursty=True)["pf"]
        risky = sim.run(full, trials=40, bursty=True, surprise=0.10)["pf"]
        self.assertLess(risky, base - 20)


class PerPlayerWins(unittest.TestCase):
    """The top of `sim.py players` was decided by ONE 200-trial block, and the
    README then asserted a rank change off it. Those rows sit ~0.01 wins apart
    while a single block moves several times that between seeds, so the value has
    to be an average over blocks and it has to carry the sd a reader can test a
    gap against before calling one player better than another."""

    def test_two_independent_runs_agree_within_the_uncertainty_they_report(self):
        full = sim.our_roster() + sim.EXPANSION
        who = ["Desmond Bane", "Jalen Suggs"]
        a = sim.player_wins(full, who, blocks=3, trials=40, seed0=101)
        b = sim.player_wins(full, who, blocks=3, trials=40, seed0=9001)
        for n in who:
            self.assertGreater(a[n][1], 0.0, "%s reports no uncertainty" % n)
            self.assertLess(abs(a[n][0] - b[n][0]), 3 * (a[n][1] + b[n][1]),
                            "%s: %s vs %s" % (n, a[n], b[n]))


class Thin(unittest.TestCase):
    def test_thinning_to_the_roster_you_already_have_measures_the_same_thing(self):
        """Roster ORDER drives the rng draw order, so a thin() that sorted made
        `thin(full, 38)` a different measurement from `full` itself -- which is
        how three values of replacement level came to circulate (16.8 / 16.9 /
        17) for one roster."""
        full = sim.our_roster() + sim.EXPANSION
        self.assertEqual(sim.replacement(sim.thin(full, len(full)))[0],
                         sim.replacement(full)[0])


class Pad(unittest.TestCase):
    """R and WINS compare across teams only at a COMMON body count, and no two
    live rosters have one (26 here against our 28, 38 everywhere from Sept '26).
    Measured on live bodies a counterparty's R lands near 23 against ours at
    16 -- so every player on his roster reads as cheaper than one of ours."""

    def test_the_real_bodies_survive_padding_in_their_own_order(self):
        their = sim.our_roster(THEIR_ROSTER)
        padded = sim.pad(their, 38)
        self.assertEqual(len(padded), 38)
        self.assertEqual([p["n"] for p in padded[:len(their)]],
                         [p["n"] for p in their])
        self.assertEqual(len({p["n"] for p in padded}), 38)  # names index the rng

    def test_every_report_measures_a_counterparty_at_the_common_count(self):
        """`+ EXPANSION` is 10 BODIES, not a body count. Every report built its
        38-man baseline that way, so `--roster their.json` -- advertised for any
        team -- silently measured a 26-man roster at 36 and reported his R,
        break-evens and per-player wins off that."""
        self.assertEqual(len(sim.basis(THEIR_ROSTER)), 38)
        self.assertEqual(len(sim.basis()), 38)

    def test_padding_our_28_is_the_38_man_basis_every_table_is_measured_on(self):
        """Pinning test, not a cycle: every 38-man figure in the README was
        measured on `our_roster() + EXPANSION`, and the counterparty recipe now
        says `pad`. If those two stop being the same measurement, one of the two
        bases is wrong and the README's cross-team comparisons go with it."""
        self.assertEqual(
            sim.run(sim.pad(sim.our_roster(), 38), trials=8)["pf"],
            sim.run(sim.our_roster() + sim.EXPANSION, trials=8)["pf"])

    def test_padding_to_the_count_you_already_have_measures_the_same_roster(self):
        """Same reason `thin` preserves order: roster order drives the rng draw
        order, so a pad that reordered would make the padded and unpadded
        measurements incomparable -- which is the thing it exists to fix."""
        their = sim.our_roster(THEIR_ROSTER)
        self.assertEqual(sim.run(sim.pad(their, len(their)), trials=8)["pf"],
                         sim.run(their, trials=8)["pf"])


class Backfill(unittest.TestCase):
    def test_a_richer_backfill_grade_lowers_the_breakeven(self):
        """What the outgoing bodies 2..N are refunded at is an ASSUMPTION, not a
        fact, and every break-even in this study rides on it. It has to be an
        argument so the bracket can be reported."""
        full = sim.our_roster() + sim.EXPANSION
        out = ["Jalen Suggs", "Coby White", "Myles Turner"]
        thin_pool = sim.breakeven(full, out, dead={"tm": "MIA", "avg": 6.0,
                                                  "gp": 40, "elig": ["PG", "SG"]})
        deep_pool = sim.breakeven(full, out, dead={"tm": "MIA", "avg": 14.0,
                                                  "gp": 55, "elig": ["PG", "SG"]})
        self.assertLess(deep_pool, thin_pool)


class SwapNames(unittest.TestCase):
    def test_trading_away_someone_who_is_not_on_the_roster_fails(self):
        """`swap` matched on name and skipped what it did not find, so a typo --
        or our own player name against a counterparty's file -- returned a roster
        with the incoming star ADDED and nobody removed. Every scenario built that
        way still prints, several hundred PF too high, with no sign of it."""
        full = sim.basis()
        with self.assertRaises(KeyError):
            sim.swap(full, ["Jalen Sugs"], [sim.star(45)])


class SlotGroups(unittest.TestCase):
    """`replacement` explains its per-group `R` by the crowding behind it, and the
    crowded group is whichever the table says -- so bodies and slots have to be
    countable for ANY group, not just guards."""

    def test_a_group_counts_every_slot_it_can_fill(self):
        """The two ANY slots are what a hand count misses: a pure centre chases 3
        of the 9, not the 1 the template labels C."""
        self.assertEqual(sim.group_slots(("C",)), 3)
        self.assertEqual(sim.group_slots(("PG", "SG")), 5)
        self.assertEqual(sim.group_slots(("SF", "PF")), 5)

    def test_only_a_body_that_cannot_leave_the_group_crowds_it(self):
        """A dual-eligible body relieves the crowding rather than adding to it, so
        it counts toward neither group."""
        roster = [sim.star(20, 60, ("PG", "SG")), sim.star(20, 60, ("SG", "SF")),
                  sim.star(20, 60, ("C",))]
        self.assertEqual(sim.pure_bodies(roster, ("PG", "SG")), 1)
        self.assertEqual(sim.pure_bodies(roster, ("SF", "PF")), 0)
        self.assertEqual(sim.pure_bodies(roster, ("C",)), 1)


class RosterScopedReports(unittest.TestCase):
    """Half the reports are built on OUR player names (`scenarios` trades Suggs,
    `durability` re-shapes him). Pointed at another team's file those names match
    nobody, so the report used to print a full table of numbers that answered
    nothing. `--roster` is advertised for any team, so the ones it cannot serve
    have to say so instead."""

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "sim.py"] + list(args),
                              cwd=os.path.dirname(os.path.abspath(sim.__file__)),
                              capture_output=True, text=True)

    def test_an_our_roster_report_refuses_a_counterparty_file(self):
        p = self.run_cli("--roster", THEIR_ROSTER, "scenarios")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("players", p.stdout + p.stderr)   # names one that does work

    def test_a_roster_agnostic_report_still_runs_on_a_counterparty_file(self):
        p = self.run_cli("--roster", THEIR_ROSTER, "positions")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("rate", p.stdout)

    def test_the_positions_premium_is_explained_by_the_loaded_roster(self):
        """Second home of the same literal: `positions` headed a table of
        forward/centre premiums with 'our 12 pure PG/SG chase at most 5
        guard-eligible slots' whatever roster produced the table."""
        p = self.run_cli("--roster", THEIR_ROSTER, "positions")
        self.assertEqual(p.returncode, 0, p.stderr)
        pure_g = sum(1 for q in sim.our_roster(THEIR_ROSTER)
                     if set(q["elig"]) <= {"PG", "SG"})
        self.assertIn("%d pure PG/SG" % pure_g, p.stdout)

    def test_the_group_R_note_agrees_with_the_table_it_explains(self):
        """A report served for any team cannot explain its numbers with OUR
        roster's shape. `replacement` printed 'guards and centres sit X points
        above forwards because our 12 pure PG/SG glut...' for every roster --
        against a counterparty whose guard R is BELOW his forward R, and whose
        pure-guard count is not 12.

        The deltas were then signed and per-roster but the CAUSE was still the
        fixed guard sentence, so on this file it printed a NEGATIVE guard delta
        and 'N pure PG/SG chase the 5 guard-eligible slots -- crowding a group
        lifts its R' underneath it: a body count offered as proof of the opposite
        of what the numbers say. Whichever group the table puts highest is the
        crowded one, and its own count is the one to print."""
        p = self.run_cli("--roster", THEIR_ROSTER, "replacement")
        self.assertEqual(p.returncode, 0, p.stderr)
        R = {lab: float(re.search(r"^ +%s +([\d.]+)" % lab, p.stdout,
                                  re.M).group(1))
             for lab in ("guard", "forward", "centre")}
        note = re.search(r"guard ([-+]\d+\.\d), centre ([-+]\d+\.\d)", p.stdout)
        self.assertIsNotNone(note, p.stdout)
        self.assertAlmostEqual(float(note.group(1)),
                               R["guard"] - R["forward"], delta=0.1)
        self.assertAlmostEqual(float(note.group(2)),
                               R["centre"] - R["forward"], delta=0.1)
        cause = re.search(r"[Tt]ightest group is (\w+): (\d+) bodies", p.stdout)
        self.assertIsNotNone(cause, p.stdout)
        self.assertEqual(cause.group(1), max(R, key=R.get), p.stdout)
        elig = {"guard": ("PG", "SG"), "forward": ("SF", "PF"),
                "centre": ("C",)}[cause.group(1)]
        self.assertEqual(int(cause.group(2)),
                         sum(1 for q in sim.our_roster(THEIR_ROSTER)
                             if set(q["elig"]) <= set(elig)))


class OneSchedule(unittest.TestCase):
    """Which NBA team a synthetic body sits on moves its added PF by ~190 across
    the 30 schedules -- several rate points, not a rounding effect. So the study
    has to declare ONE schedule and put every body on it."""

    def test_the_schedule_moves_a_body_more_than_the_tie_band_does(self):
        full = sim.our_roster() + sim.EXPANSION
        base = sim.run(full)["pf"]

        def added(tm):
            body = sim.star(45, 68, ("SF", "PF"), tm, "ADD")
            return sim.run(full + [body])["pf"] - base
        self.assertGreater(abs(added("OKC") - added("DET")), 100)

    def test_separate_one_for_ones_beat_a_consolidation_on_one_schedule(self):
        """The published "~2.7x" put the three incoming bodies on MIN/OKC/BOS and
        the consolidated star on DEN, so an unknown part of it was a schedule
        handicap booked as body count. Priced on the declared schedule the
        comparison is about bodies alone -- and that is the claim worth keeping."""
        full = sim.our_roster() + sim.EXPANSION
        out = ["Jalen Suggs", "Coby White", "Myles Turner"]
        base = sim.run(full)
        sep = sim.wins(sim.run(sim.swap(full, out, [
            sim.star(42, 68, ("SF", "PF"), sim.SIM_TM, "S%d" % i)
            for i in range(3)])), base)
        con = sim.wins(sim.run(sim.swap(full, out, [
            sim.star(65.2, 65, ("C",), sim.SIM_TM)])), base)
        self.assertGreater(sep, con)


class BreakEven(unittest.TestCase):
    def test_the_rate_it_returns_is_pf_neutral(self):
        full = sim.our_roster() + sim.EXPANSION
        out = ["Jalen Suggs", "Coby White"]
        rate = sim.breakeven(full, out, gp=68, elig=("SF", "PF"))
        got = sim.run(sim.swap(full, out, [sim.star(rate, 68)]))["pf"]
        self.assertAlmostEqual(got, sim.run(full)["pf"], delta=40)


class BoardSnapshot(unittest.TestCase):
    """`dizzle-dynasty` snapshots are month-stamped and the month moves; the Skill
    says never hardcode one. `board_rates` is the study's only rank -> rate
    bridge, so a hardcoded month reads a stale board silently -- and keeps
    reading it after the new snapshot lands beside it."""

    def test_the_newest_snapshot_is_the_one_read(self):
        d = tempfile.mkdtemp()
        for n in ("july-2026-dynasty-ranks-points.csv",
                  "december-2026-dynasty-ranks-points.csv",
                  "january-2027-dynasty-ranks-points.csv",   # newest: year wins
                  "january-2027-dynasty-ranks-9cat.csv"):    # wrong scoring
            open(os.path.join(d, n), "w").close()
        self.assertEqual(os.path.basename(sim.newest_board(d)),
                         "january-2027-dynasty-ranks-points.csv")

    def test_a_directory_with_no_snapshot_says_what_it_looked_for(self):
        with self.assertRaises(FileNotFoundError) as e:
            sim.newest_board(tempfile.mkdtemp())
        self.assertIn("dynasty-ranks-points.csv", str(e.exception))


class BoardBridge(unittest.TestCase):
    """The framework converts board rank to wins through one constant, so a rank
    -> FPts/G join that silently matches nothing would make every scenario look
    purchasable. Assert it actually joins."""

    def test_the_top_of_the_board_joins_to_scoring_rates(self):
        pairs = sim.board_rates()
        top50 = [r for r, _ in pairs if r <= 50]
        self.assertGreater(len(top50), 40)

    def test_rate_falls_as_board_rank_rises(self):
        pairs = sim.board_rates()
        top = statistics.mean([v for r, v in pairs if r <= 30])
        deep = statistics.mean([v for r, v in pairs if 150 <= r <= 250])
        self.assertGreater(top, deep + 10)


class PFPerWinBand(unittest.TestCase):
    """Every trade verdict is priced through this one constant and `team-eval`
    quotes a band for it, but `calibration` printed only the point estimate, so
    the band was a number in prose that nothing could re-derive.

    The CLUSTERING is the whole content: the 11 margins in a period all share our
    score for that period, so they are not 212 independent draws. Resampling them
    individually gives an interval several times too narrow -- the same mistake
    the GP table made with fold shuffles."""

    def test_the_band_brackets_the_point_estimate_and_stays_wide(self):
        lo, hi = sim.pf_per_win_band(n=400)
        self.assertLess(lo, sim.PF_PER_WIN)
        self.assertGreater(hi, sim.PF_PER_WIN)
        # ~27% wide clustered on period; resampling margins individually halves it
        self.assertGreater((hi - lo) / sim.PF_PER_WIN, 0.15)


class SeasonAge(unittest.TestCase):
    def test_age_is_taken_at_the_february_of_the_season_it_describes(self):
        """Season age must be a fixed point inside that season. Reading
        `detail.age` instead dates every historical row to whenever the file was
        scraped, so a 5-season fit would be fit on drifting labels."""
        # Born 1995-02-19; the '25-26 season (Fleaflicker 2025) hits Feb 1 2026.
        self.assertAlmostEqual(sim.age_at("1995-02-19", 2025), 30.95, places=1)
        self.assertAlmostEqual(sim.age_at("1995-02-19", 2021), 26.95, places=1)


class GPModelSelection(unittest.TestCase):
    """The comparison exists to REJECT models, so it has to be out-of-sample.
    An in-sample table always ranks the richest model first and would have us
    adopt per-player projections that predict nothing."""

    def test_nothing_beats_the_pool_mean_when_games_played_is_pure_noise(self):
        rng = random.Random(7)
        rows = [{"name": "P%d" % i, "age": rng.uniform(20, 36),
                 "hist": [rng.gauss(58, 17) for _ in range(5)],
                 "rate": rng.uniform(20, 50), "y": rng.gauss(58, 17)}
                for i in range(500)]
        err = sim.gp_models(rows)
        self.assertIn("mean", err)
        for name, rmse in err.items():
            self.assertGreater(rmse, err["mean"] - 0.5, "%s beat the mean on noise" % name)

    def test_a_real_signal_is_found(self):
        """Guard the other way: a harness that always prefers the constant is
        just as useless. Make GP genuinely age-driven and age must win."""
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


class GPUncertainty(unittest.TestCase):
    """The model table ranked candidates against a `noise` column that was the sd
    across FOLD SHUFFLES -- i.e. which player landed in which fold. That is not
    sampling uncertainty over the ~286 players, and it understated the real spread
    more than tenfold, which is what licensed "more seasons is WORSE" off a gap of
    0.15 against a quoted noise of 0.01. The uncertainty a gap is judged against
    has to be resampled over PLAYERS."""

    def test_the_reported_uncertainty_covers_the_gap_it_is_used_to_judge(self):
        b = sim.gp_bootstrap(sim.gp_rows(), models=("gp1", "gp5", "mean"), n=400)
        self.assertGreater(b["gp5"]["delta"], 0.0)   # gp5 does look worse than gp1
        self.assertLess(b["gp5"]["lo"], 0.0)         # ...but not measurably so
        self.assertGreater(b["mean"]["lo"], 0.0)     # the flat prior IS measurably


class GPRows(unittest.TestCase):
    def test_history_is_strictly_earlier_than_the_season_being_predicted(self):
        """A row whose `hist` contains its own target season makes every model
        look clairvoyant and would justify per-player projections outright."""
        rows = sim.gp_rows()
        self.assertGreater(len(rows), 300)
        for r in rows:
            self.assertTrue(r["seasons"], r)
            self.assertLess(max(r["seasons"]), r["season"], r)

    def test_history_is_most_recent_first(self):
        """`gp1` reads `hist[0]`, so the order is load-bearing, not cosmetic."""
        for r in sim.gp_rows():
            self.assertEqual(r["seasons"], sorted(r["seasons"], reverse=True), r)


class GPProjection(unittest.TestCase):
    """GP is the input this study calls dominant -- ~10x any format effect -- and
    `PROJECTED` was 12 hand-typed pairs covering 43% of the roster. Taking one
    injury season literally is the biggest error available here, so a projection
    has to regress toward the pool."""

    def test_an_outlier_injury_season_regresses_upward(self):
        # Embiid: 39 / 19 / 38 GP over '23-'25. Nobody should project 38.
        self.assertGreater(sim.project_gp("Joel Embiid"), 45)

    def test_an_iron_man_season_regresses_downward(self):
        """Regression pulls the top down too: 82 GP is not a projection."""
        self.assertLess(sim.project_gp("Desmond Bane"), 75)   # 42 / 69 / 82

    def test_the_durable_player_still_projects_above_the_fragile_one(self):
        """Compressed, not erased -- the ordering has to survive."""
        self.assertGreater(sim.project_gp("Nikola Jokić"),      # 79 / 70 / 65
                           sim.project_gp("Joel Embiid"))

    def test_a_superstar_rate_does_not_buy_more_games_than_an_all_star_rate(self):
        """Empirical next-season GP by last-season rate is concave and turns DOWN:
        57.6 at rate 20-25, peaking 63.2 at 30-35, then 61.3 at 40-45 and 59.6
        above 45. A rate term that keeps adding past the peak over-projects
        exactly the star-rate players every headline table is built on -- the
        unknotted form ran +6.7 GP of bias on the rate>=45 rows."""
        self.assertLessEqual(sim.project_gp("nobody", gp=65, rate=65.0),
                             sim.project_gp("nobody", gp=65, rate=35.0) + 0.5)

    def test_a_fringe_player_projects_fewer_games_than_a_starter_at_the_same_gp(self):
        """Expected GP falls off hard below rotation quality -- ~40 GP at rate <10
        against ~63 at rate 30-40 -- so a fit gated to rotation players projects the
        whole bench ~10 games too high. Scoring rate is the feature that fixes it;
        `sim.py gp` shows age does not."""
        # Both played all 82 in '25-26; Bane at 33.0 FPts/G, James at 13.9.
        self.assertGreater(sim.project_gp("Desmond Bane"),
                           sim.project_gp("Sion James") + 4)


class MissedSeasonRate(unittest.TestCase):
    """A roster file's rate is `seasonAverage`, which Fleaflicker omits for a
    player who missed the whole season -- so his row reads 0.0. OURS are hand-typed
    back in (`PROJECTED_RATE`); a counterparty's are not, and `PROJECTED_RATE`
    only holds our names. So "both sides are regressed identically" held for GP
    and failed for rate: a team holding Haliburton priced out at his value minus
    all of it."""

    def test_a_missed_season_is_priced_off_his_last_real_one(self):
        path = os.path.join(tempfile.mkdtemp(), "their.json")
        with open(path, "w") as f:
            json.dump([{"n": "Tyrese Haliburton", "tm": "IND", "avg": 0.0,
                        "tot": 0.0, "gp": 0, "posLabel": "G",
                        "elig": ["PG", "SG"]}], f)
        self.assertNotIn("Tyrese Haliburton", sim.PROJECTED_RATE)
        p, = sim.our_roster(path)
        self.assertGreater(p["avg"], 35)     # 41.4 in '24-25
        self.assertGreater(p["gp"], 45)      # and projected as the starter he is

    def test_the_calibration_basis_still_reads_the_file_as_it_stands(self):
        """`projected=False` is the season that actually happened, zeros and all --
        the 1.006 calibration is measured against it."""
        self.assertEqual([p["avg"] for p in sim.our_roster(projected=False)],
                         [p["avg"] for p in sim._load(sim.ROSTER)])


class PoolJoinByName(unittest.TestCase):
    """The pool is joined on a NAME, and the board-join rule already says that is
    where accents and punctuation silently drop rows. `_key` normalises them for
    `board_rates` and the sim's own pool join went without it, so an ASCII-spelled
    roster file quietly lost the pool season and priced the man off his file row --
    a whole missed season reads as 0 GP at 0.0 FPts."""

    def test_an_ascii_spelling_finds_the_same_pool_season(self):
        self.assertAlmostEqual(sim.project_gp("Luka Doncic"),
                               sim.project_gp("Luka Dončić"), places=6)

    def test_a_name_in_neither_the_pool_nor_the_call_fails_loudly(self):
        """It returned None, and `our_roster` rounds it -- so the failure surfaced
        as a TypeError inside `round()` several frames away, if at all."""
        with self.assertRaises(KeyError):
            sim.project_gp("Nobody At All")


class SymmetricProjection(unittest.TestCase):
    """The documented failure mode is projecting our own injured players forward
    while pricing theirs at their worst season. `our_roster` prices ANY team's file,
    so applying the fit there -- to every player, with no hand-typed GP -- is the
    only thing that makes that impossible rather than merely discouraged."""

    def test_every_player_regresses_toward_the_pool_not_just_a_named_few(self):
        proj = {p["n"]: p["gp"] for p in sim.our_roster()}
        raw = {p["n"]: p["gp"] for p in sim.our_roster(projected=False)}
        self.assertEqual(raw["Desmond Bane"], 82)               # an iron-man season
        self.assertLess(proj["Desmond Bane"], raw["Desmond Bane"])
        self.assertEqual(raw["Jalen Suggs"], 57)                # an injured one
        self.assertGreater(proj["Jalen Suggs"], raw["Jalen Suggs"])

    def test_an_overridden_rate_reaches_the_games_played_projection(self):
        """`PROJECTED_RATE` exists for the players whose '25-26 average is
        unusable, and the rate term is the whole of what separates a bench body
        from a starter. Maluach is on it at 16.0 against a raw 8.2 rookie
        season, so a projection that re-reads 8.2 off the pool prices him as
        exactly the bench body the override exists to deny -- and makes the
        override dead code."""
        self.assertEqual(sim.PROJECTED_RATE["Khaman Maluach"], 16.0)
        overridden = {p["n"]: p["gp"] for p in sim.our_roster()}["Khaman Maluach"]
        self.assertGreater(overridden,
                           round(sim.project_gp("Khaman Maluach", rate=8.2)))

    def test_the_calibration_basis_is_the_season_that_actually_happened(self):
        """`projected=False` must stay raw. The 1.006 calibration compares the sim
        against real '25-26 PF at the GP that really occurred, so projecting there
        would silently recalibrate the whole study."""
        self.assertEqual([p["gp"] for p in sim.our_roster(projected=False)],
                         [p["gp"] for p in sim._load(sim.ROSTER)])


class Durability(unittest.TestCase):
    """Characterisation test, not a red->green cycle: it pins the conclusion the
    README's durability section rests on -- with foreknowledge of who plays,
    GP-elasticity is 1, so the ONLY format-derived injury adjustment is the
    lock-in. If this stops holding, that section must be rewritten."""

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


class UnsignedPlayer(unittest.TestCase):
    """A roster may hold a player unsigned in the NBA (`proTeamAbbreviation` "FA").
    He suits up for nothing; he must not crash the sim. `--roster their.json` is
    advertised for any counterparty, and real rosters carry FA players."""

    def test_unsigned_player_plays_no_games(self):
        p = {"n": "FREE", "tm": "FA", "avg": 20.0, "tot": 0.0, "gp": 40,
             "posLabel": "F", "elig": ["SF", "PF"]}
        self.assertEqual(sim._availability(p, random.Random(1), False), set())

    def test_unsigned_player_does_not_break_a_run(self):
        roster = sim.our_roster() + [
            {"n": "FREE", "tm": "FA", "avg": 20.0, "tot": 0.0, "gp": 40,
             "posLabel": "F", "elig": ["SF", "PF"]}]
        self.assertGreater(sim.run(roster, trials=2)["pf"], 0)
