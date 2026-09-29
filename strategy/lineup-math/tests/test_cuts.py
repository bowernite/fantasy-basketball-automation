import unittest
from tests.harness import *
from simlib import cuts


def guards(*rates):
    return [sim.star(r, 70, ("PG", "SG"), n="Body %d" % i)
            for i, r in enumerate(rates)]


def names(rows):
    return [p["n"] for p in rows]


class Shortlist(unittest.TestCase):
    def test_a_single_cut_shortlists_the_five_lowest_real_bodies_in_order(self):
        spread = guards(*[40 + 15 * i for i in range(20)])
        rows = sim.pad(list(reversed(spread)), 38)
        self.assertEqual(names(cuts.shortlist(rows, 1)), names(spread[:5]))

    def test_bodies_within_250_of_the_last_cut_join_the_shortlist(self):
        close = guards(40, 40.5, 41, 41.5, 42, 42.5, 43, 70, 85, 100)
        self.assertEqual(names(cuts.shortlist(close, 1)), names(close[:7]))

    def test_the_shortlist_stops_at_twelve_however_many_bodies_are_close(self):
        close = guards(*[40 + 0.1 * i for i in range(20)])
        self.assertEqual(names(cuts.shortlist(close, 1)), names(close[:12]))

    def test_two_cuts_measure_the_band_from_the_second_worst(self):
        rows = guards(40, 55, 56, 57, 58, 59, 60, 61, 90)
        self.assertEqual(names(cuts.shortlist(rows, 2)), names(rows[:8]))


class BestCut(unittest.TestCase):
    def test_the_cut_is_the_shortlisted_body_whose_loss_scores_best_not_the_lowest_partial(self):
        rows = guards(*[40 + 15 * i for i in range(20)])
        kept_worth = {"Body 2": -50}
        cut = cuts.best_cut(rows, 1, lambda c: kept_worth.get(c[0]["n"], -100))
        self.assertEqual(names(cut), ["Body 2"])

    def test_a_tie_goes_to_the_lower_partial(self):
        rows = guards(*[40 + 15 * i for i in range(20)])
        self.assertEqual(names(cuts.best_cut(rows, 1, lambda c: 0)), ["Body 0"])

    def test_two_cuts_are_chosen_as_a_pair_not_one_at_a_time(self):
        rows = guards(*[40 + 15 * i for i in range(20)])
        pair_score = {("Body 0", "Body 1"): -10, ("Body 2", "Body 3"): -5}
        alone = {"Body 0": -1}

        def score(c):
            key = tuple(sorted(names(c)))
            return pair_score.get(key, -20 + sum(alone.get(n, 0) for n in key))

        self.assertEqual(sorted(names(cuts.best_cut(rows, 2, score))),
                         ["Body 2", "Body 3"])

    def test_three_cuts_from_twelve_candidates_go_greedy_rather_than_try_every_trio(self):
        rows = guards(*[40 + 0.1 * i for i in range(20)])
        cost = {"Body 11": 1, "Body 7": 2, "Body 4": 3}
        tried = []

        def score(c):
            tried.append(names(c))
            return -sum(cost.get(n, 10) for n in names(c))

        cut = cuts.best_cut(rows, 3, score)
        self.assertEqual(sorted(names(cut)), ["Body 11", "Body 4", "Body 7"])
        self.assertLessEqual(len(tried), 120)


class ArrivalBasis(unittest.TestCase):
    def test_an_arrival_takes_the_slot_of_the_body_whose_cut_trade_screen_scores_best(self):
        from simlib.runner import enrich_config
        rows = sim.our_roster()
        self.assertEqual(len(rows), sim.MAX_WIRE, "needs our roster full")
        base = sim.board_base(rows)
        cfg = {"kind": "trade-screen", "their_roster": 161022,
               "their_label": "Todd",
               "deals": [{"label": n, "out_us": [n], "in_from_them": [],
                          "out_them": [], "in_from_us": []}
                         for n in names(cuts.shortlist(rows, 1))]}
        with cheap_monte_carlo():
            priced = enrich_config(cfg)["deals"]
            seat = sim.arrival_basis()
        score = {d["label"]: -base[d["label"]] + 300 * d["results"]["fdw_us"]
                 + 250 * d["results"]["dw_us"] + 80 * d["results"]["dp_title_us"]
                 for d in priced}
        best = max(score, key=score.get)
        self.assertEqual(names(seat[:-1]),
                         [n for n in names(rows) if n != best])
        self.assertIn(seat[-1]["n"], roster_mod.PAD_NAMES)

    def test_a_second_call_reuses_the_cut_without_simming_again(self):
        with cheap_monte_carlo():
            first = sim.arrival_basis()
            with recorded_rosters() as seen:
                second = sim.arrival_basis()
        self.assertEqual(names(second), names(first))
        self.assertEqual(seen, [])

    def test_a_full_roster_that_is_not_a_league_seat_is_refused(self):
        bodies = [dict(p, tot=0.0, posLabel="G")
                  for p in guards(*[15 + i for i in range(38)])]
        with self.assertRaises(KeyError):
            sim.arrival_basis(roster_file(*bodies))
