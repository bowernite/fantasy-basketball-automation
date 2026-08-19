import unittest
from tests.harness import *

class TitleProbability(unittest.TestCase):
    """`Delta P(title)`: the same counterfactual `Delta w` uses, priced in the
    only currency the bracket pays in (`Eval Definitions`). Reported under
    every seed band, because which rounds bind is what the answer turns on"""

    def test_exactly_one_of_the_eight_seeds_wins_the_title(self):
        """The whole draw at once: each projected seed priced from its own
        slot, against the survivors of the parts of the bracket it is not in.
        Those eight are one bracket's outcomes and have to sum to 1. Priced
        against the field's MEAN instead, each seed is measured in a bracket of
        its own and the eight sum to whatever they sum to"""
        with cheap_monte_carlo(8):
            total = sum(sim.seed_title(t.mus, k + 1, path=t.path)
                        for k, t in enumerate(sim.field()))
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_a_starter_is_worth_more_than_the_body_that_replaces_him(self):
        full = sim.basis()
        with cheap_monte_carlo(20):
            got, = sim.player_title(full, ["Jalen Suggs"], blocks=2).values()
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                mean, sd, blocks = got[band.label]
                self.assertGreater(mean, 0.0)
                self.assertLess(mean, 1.0)
                self.assertEqual(len(blocks), 2)
                self.assertGreater(sd, 0.0)

    def test_he_is_priced_against_a_replacement_of_his_own_slot_group(self):
        """The counterfactual is the whole meaning of the number (`Eval
        Definitions §Δw`). A center priced against a forward's R is the
        single-R error, applied to the column a bracket-week call reads"""
        full = sim.basis()
        with cheap_monte_carlo(20):
            R = sim.group_replacement(full)
            base = sim.bracket_weeks(full)
            own = sim.bracket_weeks(sim.swap(
                full, ["Jakob Poeltl"], [sim.group_body("center", R["center"])]))
            forward = sim.bracket_weeks(sim.swap(
                full, ["Jakob Poeltl"], [sim.group_body("forward", R["forward"])]))
            got, = sim.player_title(full, ["Jakob Poeltl"], blocks=1,
                                    R=R).values()
            # Priced inside the block: `title_prob` reads the league's own sim
            # for the opponent level, so it is a measurement at these trials
            want = {b.label: sim.title_prob(base, b) - sim.title_prob(own, b)
                    for b in sim.BANDS}
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertAlmostEqual(got[band.label][0], want[band.label],
                                       places=9)
        self.assertNotEqual(own, forward, "this roster cannot tell the two "
                            "counterfactuals apart -- pick another player")

    def test_incoming_title_takes_the_same_one(self):
        body = sim.star(40.0, 68, ("C",), n="INCOMING")
        with cheap_monte_carlo(20):
            got, = sim.incoming_title(sim.basis(), [body], blocks=2).values()
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                mean, sd, blocks = got[band.label]
                self.assertGreater(mean, 0.0)
                self.assertEqual(len(blocks), 2)
                self.assertGreater(sd, 0.0)

    def test_a_roster_with_nothing_padded_refuses_incoming_title(self):
        full = [dict(p, n="Real %d" % i) for i, p in enumerate(sim.basis())]
        with self.assertRaises(ValueError):
            sim.incoming_title(full, [sim.star(40.0, 68, ("C",), n="IN")],
                               blocks=1, trials=2, R=flat_R())

    def test_a_side_of_a_deal_is_priced_in_one_joint_run(self):
        """`Eval Definitions §ΔP(title)` gives a multi-piece side one joint
        run and forbids added rows, and `Delta w` has `incoming_wins` for
        exactly that. Where the two paths overlap -- a change of ONE body --
        they are the same measurement on the same blocks and have to agree to
        the digit, which is what makes the joint number readable against the
        per-player column above it"""
        with cheap_monte_carlo(8):
            full, R = sim.basis(), flat_R()
            name = sim.our_roster()[0]["n"]
            body, = [p for p in full if p["n"] == name]
            without = sim.swap(full, [name],
                               [sim.group_body(sim.slot_group(body["elig"]),
                                               R[sim.slot_group(body["elig"])])])
            row, = sim.player_title(full, [name], blocks=2, R=R).values()
            joint = sim.roster_title(full, without, blocks=2)
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertEqual(joint[band.label], row[band.label])

    def test_the_import_path_prices_a_counterparty_as_the_cli_does(self):
        """The two documented ways to price a counterparty's bracket week --
        `--roster their.json playoffs` and `sim.player_title(sim.basis(
        "their.json"), names)` (`sim.py` module docstring, `trades` step 5) --
        are about the same team and have to answer the same. Left to read the
        module global the import path seeds a projected 2-seed against a
        bracket that still contains it, drops the one seed it could not avoid,
        and prints that under the counterparty's name"""
        theirs = "roster-161018-2025-26.json"
        with cheap_monte_carlo(8):
            full = sim.basis(theirs)
            name = sim.our_roster(theirs)[0]["n"]
            got, = sim.player_title(full, [name], blocks=1, R=flat_R(),
                                    path=theirs).values()
            was = roster_mod.ROSTER
            try:
                roster_mod.ROSTER = theirs
                cli_side, = sim.player_title(full, [name], blocks=1,
                                             R=flat_R()).values()
            finally:
                roster_mod.ROSTER = was
            ours_loaded, = sim.player_title(full, [name], blocks=1,
                                            R=flat_R()).values()
        for band in sim.BANDS:
            with self.subTest(band=band.label):
                self.assertEqual(got[band.label], cli_side[band.label])
        self.assertNotEqual(got, ours_loaded, "this counterparty is priced the "
                            "same either way -- pick one inside the field")

    def test_a_name_not_on_the_roster_is_refused(self):
        with cheap_monte_carlo(4, blocks=1):
            with self.assertRaises(KeyError):
                sim.player_title(sim.basis(), ["Nobody At All"], blocks=1,
                                 R=flat_R())

class OneDraw(unittest.TestCase):
    """`P(title)`, `by seed` and the multiplier are single UNPAIRED draws of
    twelve rosters. Nothing in them cancels the way the `Delta P` column's
    paired blocks do, so measuring their spread means re-drawing the whole
    basis -- ours and the field's -- on one seed at a time"""

    def test_the_draw_the_report_publishes_is_the_one_its_own_seed_gives(self):
        """The published figures come off `bracket.SEED0` and the error bar off
        re-draws of the same thing. A re-draw that lands somewhere else on that
        seed is measuring the spread of a bracket nobody published"""
        pinned = {t.path: t.mus for t in bracket.team_levels()}
        with bracket.draw(bracket.SEED0):
            self.assertEqual({t.path: t.mus for t in bracket.team_levels()}, pinned)

    def test_a_re_draw_moves_the_field_and_not_only_the_loaded_roster(self):
        """`sigma`, `field_mean` and every opponent level are the field's own
        weeks. Re-drawing ours against a pinned field prices each round against
        a draw it was not scored on, and books the loaded roster's noise as the
        whole error"""
        pinned = {t.path: t.mus for t in bracket.team_levels()}
        with bracket.draw(bracket.SEED0 + engine.TRIALS):
            moved = {t.path: t.mus for t in bracket.team_levels()}
        self.assertEqual(set(moved), set(pinned))
        for path in sorted(pinned):
            with self.subTest(team=path):
                self.assertNotEqual(moved[path], pinned[path])

    def test_the_field_is_back_on_its_own_draw_afterwards(self):
        """Every other report in the run reads `team_levels()` too"""
        pinned = {t.path: t.mus for t in bracket.team_levels()}
        with bracket.draw(bracket.SEED0 + engine.TRIALS):
            pass
        self.assertEqual({t.path: t.mus for t in bracket.team_levels()}, pinned)
