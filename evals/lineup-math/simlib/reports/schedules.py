import collections, random, statistics, sys
from fetch_data import SEASON_TAG
from .. import engine
from ..auction import AUCTION_N, auction_slots, coverage_picks, steer
from ..data import NIGHTS, SCORING_NIGHTS
from ..engine import unfilled_slots
from ..lineups import SLOTS
from ..roster import basis, star
from ..schedule import (
    LIGHT_GAMES, NBA_TEAMS, coverage, is_light, light_nights, team_light_nights,
    unsigned)
from ..stats import ols, se_mean
from ..wins import PF_PER_WIN


SWEEP_RATES = (8, 12, 20, 40)   # auction grades, and two references above them


SWEEP_H = 2                     # central-difference step for PF per rate point


STEER_DRAWS = 20                # random 7-team draws behind "not caring"


OFFER_N = 15                    # teams a September auction actually puts up


TIGHT_GAMES = 3                 # reported only, to show how thin a light night gets


def report_schedules():
    """What steering the seven-body Sept '26 auction on the NBA calendar buys.

    ONE baseline and ONE selection rule for every win figure here. The baseline
    is NOT CARING -- the mean over `STEER_DRAWS` random 7-team draws -- and the
    rule is `coverage_picks`, which is prefix-consistent, so the saturation
    ladder's last rung IS the best-7 headline rather than a second cut of the
    same choice. Two cuts and the ladder can total above the best-7 it ends at.

    Not in OURS_ONLY: no player of ours is named. Every win figure here still
    divides by PF_PER_WIN, which is derived entirely from OUR margins -- that is
    true of every win figure in the package, including the ones `--roster` is
    for, so it is not what sets these four apart. What the answer DOES depend on
    is the loaded roster's spread of NBA teams -- which light nights are already
    reached -- so `--roster` gives that team's answer, and neither team's is
    transferable to the other.
    """
    full = basis()
    base = engine.run(full)
    # The swept body is the body the auction actually hands you, read off `pad`
    # rather than retyped: a grade change in EXPANSION has to move this table,
    # because the whole table is about what THOSE seven slots are worth.
    slots = set(auction_slots(full))
    fa = [p for i, p in enumerate(full) if i in slots]
    held = [p for i, p in enumerate(full) if i not in slots]
    held_tms = {p["tm"] for p in held}
    if not fa:
        # RAISED, not `sys.exit`: from inside a report that killed every later
        # report in the same run with no sign that any were skipped, and it is
        # reachable from the import path too, where an exit is not an answer.
        raise ValueError(
            "this roster is already full at %d bodies, so the September auction "
            "fills nothing. This report is about what THAT auction's schedules "
            "buy -- there is nothing to steer." % len(full))
    gp = max(p["gp"] for p in fa)
    light, tight = light_nights(), light_nights(TIGHT_GAMES)
    per_team = {t: len(team_light_nights(t)) for t in NBA_TEAMS}
    scored = collections.Counter(t for i in SCORING_NIGHTS for t in NIGHTS[i][1])
    print("light night = a scored night of <=%d NBA games, where the %d-slot cap"
          % (LIGHT_GAMES, len(SLOTS)))
    lost = unfilled_slots(base)
    print("binds: `nights` puts %d%% of the season's unfilled slots on them."
          % round(100 * sum(v for g, v in lost.items() if g <= LIGHT_GAMES)
                  / sum(lost.values())))
    print("\nSCORED PERIODS ONLY -- %d of %d nights, %d of %d games. The fantasy"
          % (len(SCORING_NIGHTS), len(NIGHTS), sum(scored.values()) // 2,
             sum(len(t) for _, t in NIGHTS) // 2))
    calendar = [tms for _, tms in NIGHTS if is_light(tms)]
    whole = collections.Counter(t for tms in calendar for t in tms)
    shift = max(whole[t] - per_team[t] for t in NBA_TEAMS)
    print("season ends before the NBA's, so light nights in April are worth 0:")
    print("counting the whole calendar finds %d light nights, not %d, and moves a"
          % (len(calendar), len(light)))
    print("team by up to %d (%s)."
          % (shift, ", ".join("%s %d->%d" % (t, whole[t], per_team[t])
                              for t in NBA_TEAMS
                              if whole[t] - per_team[t] == shift)))
    print("  %d of the %d scored nights are light; %d carry <=%d games."
          % (len(light), len(SCORING_NIGHTS), len(tight), TIGHT_GAMES))
    print("  light nights per team: mean %.2f, sd %.2f, %d to %d."
          % (statistics.mean(per_team.values()),
             statistics.stdev(per_team.values()),
             min(per_team.values()), max(per_team.values())))
    for c in sorted(set(per_team.values()), reverse=True):
        print("  %5d  %s" % (c, " ".join(t for t in NBA_TEAMS
                                         if per_team[t] == c)))
    print("  scored-period GAMES per team run %d-%d, so the choice buys light"
          % (min(scored.values()), max(scored.values())))
    print("  nights, not games -- do not read this table as a strength of schedule.")

    print("\nPER BODY. One added %d-GP forward-eligible body, swept across all %d"
          % (gp, len(NBA_TEAMS)))
    print("schedules on the %d-man roster. `sdRate` converts that PF sd at the"
          % len(full))
    print("MEASURED PF-per-rate-point slope of the same %d-schedule MEAN (central"
          % len(NBA_TEAMS))
    print("difference, +-%d): the schedule in the units a board prices in. The"
          % SWEEP_H)
    print("slope is a property of the schedule too -- it runs 2.5 (BKN) to 8.0")
    print("(OKC) at rate %d -- so the mean's slope is the only honest denominator."
          % SWEEP_RATES[0])
    grid = sorted({r + d for r in SWEEP_RATES for d in (-SWEEP_H, 0, SWEEP_H)})
    sweep = {r: [engine.run(full + [star(r, gp, ("SF", "PF"), t, "ADD")])["pf"]
                 - base["pf"] for t in NBA_TEAMS] for r in grid}
    print("  %6s %9s %8s %9s %9s %9s"
          % ("rate", "meanPF", "sdPF", "sd wins", "sdRate", "spanRate"))
    ratepts = {}
    for r in SWEEP_RATES:
        v, sd = sweep[r], statistics.stdev(sweep[r])
        # A central difference of the schedule MEAN, not `stats.slope`'s
        # least-squares fit: same word, different quantity.
        pf_per_rate = (statistics.mean(sweep[r + SWEEP_H])
                       - statistics.mean(sweep[r - SWEEP_H])) / (2.0 * SWEEP_H)
        ratepts[r] = sd / pf_per_rate
        print("  %6d %9.0f %8.1f %9.3f %9.2f %9.2f"
              % (r, statistics.mean(v), sd, sd / PF_PER_WIN, sd / pf_per_rate,
                 (max(v) - min(v)) / pf_per_rate))
    lo, hi = SWEEP_RATES[0], SWEEP_RATES[-1]
    print("  SUB-PROPORTIONAL: the body grows %.0fx from rate %d to %d while the"
          % (statistics.mean(sweep[hi]) / statistics.mean(sweep[lo]), lo, hi))
    print("  schedule sd under it grows only %.0fx, so the schedule is worth"
          % (statistics.stdev(sweep[hi]) / statistics.stdev(sweep[lo])))
    print("  %.1f rate points at %d and %.1f at %d." % (ratepts[lo], lo,
                                                        ratepts[hi], hi))
    # The threshold that MATTERS is the one at the grade it is applied at -- the
    # auction fills at 8-14 -- so quoting the rate-40 figure as "the" threshold
    # under-prices the only case the rule is ever spent in
    print("  Quote the row that matches the body: the auction grades are %.0f-%.0f"
          % (min(p["avg"] for p in fa), max(p["avg"] for p in fa)))
    print("  FPts, so ~%.1f rate points is the threshold this rule is spent at."
          % ratepts[lo])

    print("\nSTEERING THE AUCTION. %d bodies (`pad`'s FA grades at %d GP); the"
          % (len(fa), gp))
    print("other %d stay where they are, and %d of the %d light nights are already"
          % (len(held), coverage(held_tms), len(light)))
    print("reached by them. Selection rule: greedy on `coverage`. ONE baseline --")
    print("NOT CARING, the mean of %d random 7-team draws -- so the ladder below"
          % STEER_DRAWS)
    print("ends exactly on the best-7 headline instead of contradicting it.")

    def pf(tms):
        return engine.run(steer(full, tms))["pf"]

    rng = random.Random(13)
    draws = [[rng.choice(NBA_TEAMS) for _ in range(AUCTION_N)]
             for _ in range(STEER_DRAWS)]
    best = coverage_picks(AUCTION_N)
    worst = coverage_picks(AUCTION_N, best=False)
    top = pf(best)
    # PAIRED down the ladder: rung k and rung k-1 share the draw AND the seeds, so
    # the increment is a within-draw quantity with an sd 3-5x smaller than either
    # rung's -- the rungs' own spread buries increments under the lottery
    rows = [[pf(best[:k] + d[k:]) for k in range(AUCTION_N)] + [top]
            for d in draws]
    idle = statistics.mean(r[0] for r in rows)   # THE baseline for every row
    lottery = [r[0] for r in rows]
    cum = [[r[k] - r[0] for r in rows] for k in range(1, AUCTION_N + 1)]

    def vs_idle(total):
        """A configuration's PF as wins over NOT CARING. Every win figure below
        goes through here, so the ONE baseline this report promises is structural
        rather than retyped."""
        return (total - idle) / PF_PER_WIN

    def se_wins(xs):
        """Standard error of the mean of `xs` PF, in wins."""
        return se_mean(xs) / PF_PER_WIN

    w = [statistics.mean(c) / PF_PER_WIN for c in cum]
    print("  %-22s %s" % ("schedule-aware picks",
                          " ".join("%7d" % k
                                   for k in range(1, AUCTION_N + 1))))
    print("  %-22s %s" % ("cumulative +wins",
                          " ".join("%+7.3f" % x for x in w)))
    print("  %-22s %s" % ("  paired +-",
                          " ".join("%7.3f" % se_wins(c) for c in cum)))
    print("  %-22s %s" % ("steered picks cover", " ".join(
        "%7d" % coverage(best[:k]) for k in range(1, AUCTION_N + 1))))
    print("  %-22s %s" % ("all %d cover, mean" % AUCTION_N, " ".join(
        "%7.1f" % statistics.mean(coverage(best[:k] + d[k:]) for d in draws)
        for k in range(1, AUCTION_N + 1))))
    peak = max(range(AUCTION_N), key=lambda i: w[i])
    print("  picks: %s" % " ".join(best))
    worst_pf = pf(worst)
    print("  best %d, all %d teams on offer : %+.3f wins"
          % (AUCTION_N, len(NBA_TEAMS), w[-1]))
    print("  worst %d (greedy-min: a stack) : %+.3f wins"
          % (AUCTION_N, vs_idle(worst_pf)))
    # DERIVED. "The last pick buys nothing" is where a reader stops steering, and
    # the ladder peaks wherever it peaks -- on a counterparty file the peak can be
    # the last rung
    last = w[-1] - w[-2]
    se = se_wins([a - b for a, b in zip(cum[-1], cum[-2])])
    sat = next(k for k in range(1, AUCTION_N + 1)
               if coverage(best[:k]) == coverage(best))
    print("  It PEAKS at %d of %d picks (%+.3f), and coverage saturates at %d"
          % (peak + 1, AUCTION_N, w[peak], sat))
    print("  (%d of %d nights). Past that the rule can only REPEAT itself -- its"
          % (coverage(best), len(light)))
    print("  %dth pick is %s again. That pick buys %+.3f against a paired +-%.3f,"
          % (AUCTION_N, best[-1], last, se))
    print("  which is %s." % ("nothing measurable" if abs(last) < 2 * se else
                              "a REAL increment -- the rule pays past "
                              "saturation here, so re-read this ladder"))
    print("  %d picks buy %.0f%% of the peak and %d buy %.0f%%."
          % (3, 100 * w[2] / w[peak], 4, 100 * w[3] / w[peak]))
    sd = statistics.stdev(lottery) / PF_PER_WIN
    print("  NOT CARING IS ITSELF A LOTTERY, not a neutral draw: the %d draws land"
          % STEER_DRAWS)
    print("  %+.2f to %+.2f wins against the best %d (sd %.3f), so what ignoring"
          % ((min(lottery) - top) / PF_PER_WIN,
             (max(lottery) - top) / PF_PER_WIN, AUCTION_N, sd))
    print("  schedule costs swings by +-%.2f wins on its own." % sd)
    offers = [rng.sample(NBA_TEAMS, OFFER_N) for _ in range(STEER_DRAWS)]
    got = [pf(coverage_picks(AUCTION_N, teams=o)) for o in offers]
    print("  best %d of a random %d-team offer  : %+.3f +- %.3f wins -- the"
          % (AUCTION_N, OFFER_N, vs_idle(statistics.mean(got)), se_wins(got)))
    print("  realistic figure, since no auction puts all %d up." % len(NBA_TEAMS))

    print("\nCOVERAGE, NOT A SUMMED NIGHT COUNT. A second body on a night already")
    print("covered chases the slot the first one took, so the two quantities")
    print("disagree hardest on the one shape that matters -- a stack:")
    deep = max(NBA_TEAMS, key=lambda t: per_team[t])
    stack = [deep] * AUCTION_N
    stack_pf = pf(stack)
    print("  seven on %s : %d body-nights summed, %d distinct, %+.3f wins"
          % (deep, AUCTION_N * per_team[deep], coverage(stack),
             vs_idle(stack_pf)))
    print("  spread best %d : %d body-nights summed, %d distinct, %+.3f wins"
          % (AUCTION_N, sum(per_team[t] for t in best), coverage(best), w[-1]))
    print("  %dx%d is the CEILING on that sum, and the shape that reaches it"
          % (AUCTION_N, per_team[deep]))
    print("  lands %s not caring. Diversification is not a separate principle:"
          % ("BELOW" if stack_pf < idle else "above"))
    print("  it is a proxy for coverage.")

    # ONE row per configuration, not one per `run`: the ladder alone is 7 rungs x
    # STEER_DRAWS near-identical rosters, and letting those in makes the fit a
    # statement about the ladder rather than about coverage
    configs = ([(d, r[0]) for d, r in zip(draws, rows)] + list(zip(offers, got))
               + [(best, top), (worst, worst_pf), (stack, stack_pf)])

    def fit(metric):
        """(slope, R2) of PF on `metric` over every configuration measured above.

        Through `stats.ols` rather than a second hand-rolled normal equation:
        the same solver the GP models are fitted with, so there is one place a
        regression in this package can be wrong.
        """
        xs, ys = [metric(t) for t, _ in configs], [y for _, y in configs]
        a, b = ols(xs, lambda v: (v,), ys)
        my = statistics.mean(ys)
        return b, 1 - (sum((c - a - b * v) ** 2 for v, c in zip(xs, ys))
                       / sum((c - my) ** 2 for c in ys))

    cb, cr2 = fit(coverage)
    sb, sr2 = fit(lambda t: sum(per_team[q] for q in t))
    covs = [coverage(t) for t, _ in configs]
    print("  Over the %d configurations measured above (covering %d-%d nights):"
          % (len(configs), min(covs), max(covs)))
    print("    on nights COVERED  : %5.1f PF/night, R2 %.2f" % (cb, cr2))
    print("    on nights SUMMED   : %5.1f PF/night, R2 %.2f" % (sb, sr2))
    print("  Coverage %s that comparison, which is the whole of the claim. It is"
          % ("wins" if cr2 > sr2 else "LOSES"))
    print("  still only a PROXY -- neither explains the spread inside the realistic")
    print("  band (a random 7 covers %.0f of %d), where the %d-slot mechanics on the"
          % (statistics.mean(coverage(d) for d in draws), len(light), len(SLOTS)))
    print("  nights you do cover carry the rest. Steer on it; do not model with it.")
    print("\nRE-CUT EVERY SEASON. Measured on the %s calendar at %d bodies against"
          % (SEASON_TAG, len(full)))
    print("this roster's spread of %d NBA teams; which nights are already covered"
          % sum(1 for t in held_tms if not unsigned(t)))
    print("sets every figure above. Never carry one forward.")
