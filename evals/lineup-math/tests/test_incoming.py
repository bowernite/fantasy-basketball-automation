import unittest
from tests.harness import *

class IncomingWins(unittest.TestCase):
    def test_acquiring_a_player_is_worth_what_losing_him_costs(self):
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
        full = sim.basis()
        row = max(sim.our_roster(THEIR_ROSTER), key=season_value)
        with cheap_monte_carlo(4):
            R = sim.group_replacement(full)
            with recorded_rosters(trials=4) as seen:
                sim.incoming_wins(full, [row], blocks=1, R=R)
        self.assertEqual({len(names) for names in seen}, {len(full)})

    def test_the_roster_an_arrival_joins_is_the_one_the_recipe_re_pads(self):
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
        full = [dict(p, n="Real %d" % i) for i, p in enumerate(sim.basis())]
        with self.assertRaises(ValueError) as e:
            sim.incoming_wins(full, [sim.star(40.0, 68, ("C",), n="IN")],
                              blocks=1, trials=2,
                              R=flat_R())
        self.assertIn("38", str(e.exception))

    def test_every_player_on_a_counterparty_file_is_priced_at_once(self):
        theirs = sim.our_roster(THEIR_ROSTER)
        with cheap_monte_carlo(20):
            w = sim.incoming_wins(sim.basis(), theirs, blocks=1)
        self.assertEqual(sorted(w), sorted(p["n"] for p in theirs))
        best = max(theirs, key=season_value)
        self.assertGreater(w[best["n"]][0], 0.3, best["n"])

    def test_a_name_our_own_roster_already_carries_is_still_priced_as_himself(self):
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
        both = [sim.star(45.0, 70, ("C",), n="Jaylin Williams"),
                sim.star(12.0, 40, ("PG", "SG"), n="Jaylin Williams")]
        with self.assertRaises(ValueError) as e:
            sim.incoming_wins(sim.basis(), both, blocks=1, trials=2)
        self.assertIn("Jaylin Williams", str(e.exception))

class Thin(unittest.TestCase):
    def test_thinning_to_the_roster_you_already_have_measures_the_same_thing(self):
        full = sim.basis()
        with cheap_monte_carlo(20):
            self.assertEqual(sim.replacement(sim.thin(full, len(full)))[0],
                             sim.replacement(full)[0])

    def test_a_live_counterparty_file_is_nowhere_near_our_padded_r(self):
        with cheap_monte_carlo(20):
            self.assertLess(sim.replacement(sim.our_roster(THEIR_ROSTER))[0],
                            14.0)

    def test_thinning_at_a_stale_r_keeps_a_different_set_of_bodies(self):
        grinders = [sim.star(15.0, gp=82, elig=("SF", "PF"), n="GRIND%d" % i)
                    for i in range(3)]
        scorers = [sim.star(30.0, gp=30, elig=("SF", "PF"), n="SCORE%d" % i)
                   for i in range(3)]
        roster = [p for pair in zip(grinders, scorers) for p in pair]
        self.assertEqual({p["n"] for p in sim.thin(roster, 3, R=5.0)},
                         {"GRIND0", "GRIND1", "GRIND2"})
        self.assertEqual({p["n"] for p in sim.thin(roster, 3, R=12.0)},
                         {"SCORE0", "SCORE1", "SCORE2"})
