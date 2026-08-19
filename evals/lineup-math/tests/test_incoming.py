import unittest
from tests.harness import *

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
        R = {"guard": 18.0, "forward": 17.0, "center": 20.0}
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

    def test_a_live_counterparty_file_is_nowhere_near_our_padded_r(self):
        """`R` is the x-intercept of value in rate, so it moves with the body
        COUNT by construction: ~17 on our padded 38 against ~11 on a live
        27-man file. That gap is why `thin` takes the roster's own"""
        with cheap_monte_carlo(20):
            self.assertLess(sim.replacement(sim.our_roster(THEIR_ROSTER))[0],
                            14.0)

    def test_thinning_at_a_stale_r_keeps_a_different_set_of_bodies(self):
        """Six rate points out does not merely relabel the order -- it prefers
        rate to games where the roster's own level prefers games, and keeps
        other bodies.

        BUILT, not read off a roster file. Whether two R's happen to order one
        real 27-man file differently is a fact about that week's transactions,
        and this test went green on a trade"""
        grinders = [sim.star(15.0, gp=82, elig=("SF", "PF"), n="GRIND%d" % i)
                    for i in range(3)]
        scorers = [sim.star(30.0, gp=30, elig=("SF", "PF"), n="SCORE%d" % i)
                   for i in range(3)]
        roster = [p for pair in zip(grinders, scorers) for p in pair]
        # (15-5)*82 = 820 against (30-5)*30 = 750, and at R=12 it is 246
        # against 540 -- the same six bodies, ranked the other way up
        self.assertEqual({p["n"] for p in sim.thin(roster, 3, R=5.0)},
                         {"GRIND0", "GRIND1", "GRIND2"})
        self.assertEqual({p["n"] for p in sim.thin(roster, 3, R=12.0)},
                         {"SCORE0", "SCORE1", "SCORE2"})
