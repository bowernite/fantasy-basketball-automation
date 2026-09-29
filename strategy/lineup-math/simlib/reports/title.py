import math, statistics
from .. import roster, title
from ..bracket import (
    BANDS, BRACKET_TEAMS, FIELD_LEVEL_CV, LADDERS, WITHIN_CV, loaded,
    seed_title, sigma, team_levels)
from ..data import BRACKET, PERIODS, REGULAR
from ..title import bracket_odds, season_run, win_spread


def _wide():
    # off actual name lengths -- a hardcoded width truncates longer team names
    return max(len(roster.label(t.path)) for t in team_levels())


def _se(p, n):
    return math.sqrt(max(p * (1 - p), 0.0) / n)


def _preamble(trials):
    print("%d head-to-head periods on the league's own schedule shape, standings"
          % len(REGULAR))
    print("by record then points-for, then the %d-of-%d bracket over periods %s."
          % (len(BRACKET_TEAMS), len(PERIODS[REGULAR[0]]["games"]) * 2,
             "-".join(str(PERIODS[i]["ordinal"])
                      for i in (BRACKET[0], BRACKET[-1]))))
    print("%d seasons. draw: seeds %s | %s, each half climbed worst seed first,"
          % (trials, *("-".join(str(s) for s in l) for l in LADDERS)))
    print("so seeds %s enter in the last round they can."
          % ", ".join(str(s) for s in BANDS[0].slots))
    print("week-to-week spread around a level: %.4f of the period's level."
          % WITHIN_CV)


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
    print("  `wins` is matchups won of the %d; the band columns sum to `bracket`."
          % len(REGULAR))
    print("  P(title) sums to %.3f over the league."
          % sum(o.title for o in odds.values()))


# below 200 seasons behind it, a conditional's +- is wider than every other
# bar on the table
MIN_SEASONS = 200


def _ours(odds, who, trials):
    if who not in odds:
        raise KeyError(
            "%s is not among the %d roster files this league was built from, "
            "so it has no seed in the draw to decompose -- `./run "
            "fetch_data.py roster` writes them (`team-info`)"
            % (who, len(odds)))
    o = odds[who]
    mine, = [t for t in team_levels() if t.path == who]
    print("\n%s: P(title) %.3f, by seed."
          % (roster.label(who), o.title))
    print("  %4s %9s %14s %13s %12s"
          % ("seed", "P(seed)", "P(title|seed)", "contribution", "closed form"))
    for s in range(1, len(BRACKET_TEAMS) + 1):
        p, joint = o.seeds[s - 1], o.crowns[s - 1]
        print("  %4d %9.3f %14s %13.3f %12.3f"
              % (s, p, "%.3f" % (joint / p)
                 if p * trials >= MIN_SEASONS else "-", joint,
                 seed_title(mine.mus, s, path=who)))
    print("  %4s %9.3f %14s %13.3f" % ("out", 1 - o.bracket, "0.000", 0.0))
    print("  contribution sums to P(title); a seed reached fewer than %d times"
          % MIN_SEASONS)
    print("  prints `-`. `closed form` is `seed_title` against the PROJECTED")
    print("  field in its projected order.")


def _cost_of_the_seed(odds, who, trials):
    pinned = bracket_odds(trials=trials)
    print("\nSeeding, priced. `pinned` hands every team the seed its projected")
    print("PF says it gets and plays only the bracket; `simulated` is the table")
    print("above.")
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
    sim, wire = win_spread(trials=trials, spread=spread)
    lvl = [t.pf for t in team_levels()]
    print("\nChecks.")
    print("  standings spread: sim sd %.2f, wire %.2f over %d periods"
          % (sim, wire, len(REGULAR)))
    print("  level spread: projected season PF cv %.4f, wire %.4f"
          % (statistics.stdev(lvl) / statistics.mean(lvl), FIELD_LEVEL_CV))
    print("  bracket agreement: seeds pinned, sigma %.0f-%.0f by round"
          % (min(sigma(w) for w in range(len(BRACKET))),
             max(sigma(w) for w in range(len(BRACKET)))))


def report_title():
    # read at call time, not bound as a default -- else a snapshot taken at
    # import time would describe a run that didn't happen
    trials = title.SEASON_TRIALS
    who = loaded()
    _preamble(trials)
    print()
    # one run, both answers -- `_checks`' standings spread is the same seasons
    # as the table, not a second run of them
    odds, spread = season_run(trials=trials)
    _table(odds, trials)
    _ours(odds, who, trials)
    _cost_of_the_seed(odds, who, trials)
    _checks(trials, spread)
