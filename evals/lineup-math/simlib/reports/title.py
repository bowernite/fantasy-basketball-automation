import math, statistics
from .. import roster, title
from ..bracket import (
    BANDS, BRACKET_TEAMS, FIELD_LEVEL_CV, LADDERS, WITHIN_CV, loaded,
    seed_title, sigma, team_levels)
from ..data import BRACKET, PERIODS, REGULAR, SCORED
from ..title import bracket_odds, season_run, win_spread


def _wide():
    """Width of the team column, off the names it has to hold. Cut to a
    constant instead, the two longest team names lose their closing bracket and
    the row reads as a different franchise."""
    return max(len(roster.label(t.path)) for t in team_levels())


def _se(p, n):
    """Sampling error on a probability measured over `n` seasons. Binomial:
    every season is one independent draw of the whole league, so this is the
    only bar on the table that is not inherited from the basis below it."""
    return math.sqrt(max(p * (1 - p), 0.0) / n)


def _preamble(trials):
    print("The season simulated end to end: %d head-to-head periods on the"
          % len(REGULAR))
    print("league's own schedule shape, standings by record then points-for,")
    print("then the %d-of-%d bracket over periods %s -- byes and all."
          % (len(BRACKET_TEAMS), len(PERIODS[REGULAR[0]]["games"]) * 2,
             "-".join(str(PERIODS[i]["ordinal"])
                      for i in (BRACKET[0], BRACKET[-1]))))
    print("%d seasons. The draw is seeds %s | %s, each half"
          % (trials, *("-".join(str(s) for s in l) for l in LADDERS)))
    print("climbed worst seed first, so seeds %s enter in the last round they"
          % ", ".join(str(s) for s in BANDS[0].slots))
    print("can and everyone else has to climb to them.")
    print()
    print("THE DIFFERENCE FROM `playoffs`: there the seed is an assumption and")
    print("every figure is conditional on a band. Here it is simulated, so")
    print("P(title) is unconditional, every team has one and the twelve sum to")
    print("1. It is a THIRD quantity beside `Delta w` and banded")
    print("`Delta P(title)` and replaces neither: it carries the seeding")
    print("channel those two are defined to keep apart (`Bracket value.md`).")
    print()
    print("Levels are `team_levels()`'s -- every team's own roster file,")
    print("projected, padded to 38, one engine -- so injuries reach this as")
    print("each roster's own projected-GP haircut, per period and per bracket")
    print("round. The week-to-week spread around a level is drawn at %.4f of"
          % WITHIN_CV)
    print("the period's level, which is `sigma`'s own decomposition and NOT")
    print("the engine's own draws: availability is all that moves in the")
    print("engine, and a league scored off it alone runs 2.5x too predictable.")


def _table(odds, trials):
    w = _wide()
    print("  %-*s %4s %7s %s %8s %7s"
          % (w, "team", "wins", "bracket",
             " ".join("%6s" % b.label for b in BANDS), "P(title)", "+-"))
    for path, o in sorted(odds.items(), key=lambda kv: -kv[1].title):
        print("  %-*s %4.1f %7.3f %s %8.3f %7s"
              % (w, roster.label(path), o.wins, o.bracket,
                 " ".join("%6.3f" % o.bands[b.label] for b in BANDS),
                 o.title, "+-%.3f" % _se(o.title, trials)))
    print("  `wins` is matchups won of the %d; the band columns are P(seeded in"
          % len(REGULAR))
    print("  that range), so they sum to `bracket`. No PF column: seeding")
    print("  breaks its ties on points-for over these %d periods, which is not"
          % len(REGULAR))
    print("  the %d-period season PF `playoffs` seeds its field on."
          % len(SCORED))
    print("  P(title) sums to %.3f over the league -- somebody wins it."
          % sum(o.title for o in odds.values()))


# Seasons a conditional needs behind it before it is printed. At 200 a 0.5
# reads +-0.035, which is already the loosest thing on the page. Below it a
# seed prints a number that looks measured and is one season either way.
MIN_SEASONS = 200


def _ours(odds, who, trials):
    """Where our own title odds come from: the seed we get, and what it is
    worth once we have it."""
    if who not in odds:
        raise KeyError(
            "%s is not among the %d roster files this league was built from, "
            "so it has no seed in the draw to decompose -- `./run "
            "fetch_data.py roster` writes them (`team-info`)"
            % (who, len(odds)))
    o = odds[who]
    mine, = [t for t in team_levels() if t.path == who]
    print("\n%s: P(title) %.3f, and where it comes from."
          % (roster.label(who), o.title))
    print("  P(title | seed) is measured INSIDE this run, so its opponents are")
    print("  whoever else finished there -- not the projected order. That is")
    print("  the number `playoffs` cannot produce: it seeds the field by")
    print("  projected PF and asks what a seed is worth against that one draw.")
    print("  %4s %9s %14s %13s %12s"
          % ("seed", "P(seed)", "P(title|seed)", "contribution", "closed form"))
    for s in range(1, len(BRACKET_TEAMS) + 1):
        p, joint = o.seeds[s - 1], o.crowns[s - 1]
        print("  %4d %9.3f %14s %13.3f %12.3f"
              % (s, p, "%.3f" % (joint / p)
                 if p * trials >= MIN_SEASONS else "-", joint,
                 seed_title(mine.mus, s, path=who)))
    print("  %4s %9.3f %14s %13.3f" % ("out", 1 - o.bracket, "0.000", 0.0))
    print("  contribution sums to P(title). A seed reached fewer than %d times"
          % MIN_SEASONS)
    print("  prints `-` rather than a conditional one season could move.")
    print("  `closed form` is `seed_title` -- the same seed against the")
    print("  PROJECTED field in its projected order, which is what `playoffs`")
    print("  prices, and it is priced at every seed whether this roster can")
    print("  reach it or not. The two columns differ wherever the simulated")
    print("  field is not that field.")


def _cost_of_the_seed(odds, who, trials):
    """What not knowing the seed is worth, as against being handed the
    projected one."""
    pinned = bracket_odds(trials=trials)
    print("\nSeeding, priced. `pinned` hands every team the seed its projected")
    print("PF says it gets and plays only the bracket; `simulated` is the")
    print("table above. The gap is the whole cost of having to earn the seed --")
    print("and for a team the projection already has outside the field, the")
    print("whole value of not being stuck outside it.")
    w = _wide()
    print("  %-*s %7s %10s %7s"
          % (w, "team", "pinned", "simulated", "delta"))
    for k, t in enumerate(team_levels()):
        p, s = pinned[t.path], odds[t.path].title
        print("  %-*s %7.3f %10.3f %+7.3f  %s"
              % (w, roster.label(t.path), p, s, s - p,
                 "<- loaded" if t.path == who else
                 "" if k < len(BRACKET_TEAMS) else "(outside the field)"))


def _checks(trials, spread):
    """The three ways this run can be wrong that are measurable from here."""
    sim, wire = win_spread(trials=trials, spread=spread)
    lvl = [t.pf for t in team_levels()]
    print("\nChecks.")
    print("  Standings spread. One simulated season's %d win totals have an sd"
          % len(team_levels()))
    print("  of %.2f; last season's actual %d periods gave %.2f. Realised, so"
          % (sim, len(REGULAR), wire))
    print("  both carry matchup luck. One league-season is a bound and not a")
    print("  fit -- and a team that stopped setting lineups is inside it.")
    print("  Level spread. The projected league's season PF has a cv of %.4f"
          % (statistics.stdev(lvl) / statistics.mean(lvl)))
    print("  against %.4f for last season's actual weekly levels. Wider means"
          % FIELD_LEVEL_CV)
    print("  the projections separate these teams more than the wire did, and")
    print("  every P(title) here is more concentrated than it should be.")
    print("  Bracket agreement. With the seeds pinned this is `seed_title` as a")
    print("  Monte Carlo -- same sigma (%.0f-%.0f by round), same draw. The two"
          % (min(sigma(w) for w in range(len(BRACKET))),
             max(sigma(w) for w in range(len(BRACKET)))))
    print("  are held to each other in `tests/`; a gap there is one model")
    print("  having drifted from the other, not a finding.")
    print("  What none of this measures: the field is PROJECTED. Rosters move")
    print("  all season, the opponent basis is one snapshot, and `method.md`")
    print("  owns that error bar -- it is wider than every bar printed here.")


def report_title():
    """P(title) with the seed simulated rather than assumed, for all 12 teams.

    The end-to-end run: regular season, standings, seeds, bracket. `playoffs`
    is the same bracket priced one seed band at a time and is the report a
    per-player column comes off; this one answers what the roster's odds
    actually are.
    """
    # Read off the module at call time, never bound as a default: the table
    # prints its own season count and its own error bars, and a count
    # snapshotted at import lets those describe a run that did not happen.
    trials = title.SEASON_TRIALS
    who = loaded()
    _preamble(trials)
    print()
    # One run, both answers: the standings spread `_checks` prints is the
    # same 20,000 seasons the table is, and asking for it separately runs
    # them again.
    odds, spread = season_run(trials=trials)
    _table(odds, trials)
    _ours(odds, who, trials)
    _cost_of_the_seed(odds, who, trials)
    _checks(trials, spread)
