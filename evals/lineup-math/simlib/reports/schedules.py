import collections, random, statistics, sys
from fetch_data import SEASON_TAG
from .. import engine
from ..auction import auction_slots, coverage_picks, steer
from ..data import NIGHTS, SCORING_NIGHTS
from ..engine import unfilled_slots
from ..lineups import SLOTS
from ..roster import basis, star
from ..schedule import (
    LIGHT_GAMES, NBA_TEAMS, coverage, is_light, light_nights, team_light_nights,
    unsigned)
from ..stats import ols, se_mean
from ..wins import pf_wins


SWEEP_RATES = (8, 12, 20, 40)   # auction grades, and two references above them


SWEEP_H = 2                     # central-difference step for PF per rate point


STEER_DRAWS = 20                # random full-slate draws behind "not caring"


OFFER_N = 15                    # teams a September auction actually puts up


TIGHT_GAMES = 3                 # reported only, to show how thin a light night gets


def report_schedules():
    # sized off the LOADED roster, not `AUCTION_N` -- `pad` invents an FA slot
    # only after held picks, so leftover auction slots shrink with live count
    full = basis()
    base = engine.run(full)
    # read off `pad`, not retyped -- a grade change in EXPANSION must move this
    # table
    slots = set(auction_slots(full))
    fa = [p for i, p in enumerate(full) if i in slots]
    held = [p for i, p in enumerate(full) if i not in slots]
    held_tms = {p["tm"] for p in held}
    if not fa:
        # raised, not `sys.exit`, since an exit here would kill every later
        # report in the same run with no sign any were skipped
        raise ValueError(
            "this roster is already full at %d bodies; the September auction "
            "fills nothing" % len(full))
    # every count below is `n` -- ladder, draws, stack, offer
    n = len(fa)
    gp = max(p["gp"] for p in fa)
    light, tight = light_nights(), light_nights(TIGHT_GAMES)
    per_team = {t: len(team_light_nights(t)) for t in NBA_TEAMS}
    scored = collections.Counter(t for i in SCORING_NIGHTS for t in NIGHTS[i][1])
    lost = unfilled_slots(base)
    print("light night = a scored night of <=%d NBA games on the %s calendar, "
          "where\nthe %d-slot cap binds: `nights` puts %d%% of the season's "
          "unfilled slots on them."
          % (LIGHT_GAMES, SEASON_TAG, len(SLOTS),
             round(100 * sum(v for g, v in lost.items() if g <= LIGHT_GAMES)
                   / sum(lost.values()))))
    print("\nSCORED PERIODS ONLY -- %d of %d nights, %d of %d games."
          % (len(SCORING_NIGHTS), len(NIGHTS), sum(scored.values()) // 2,
             sum(len(t) for _, t in NIGHTS) // 2))
    calendar = [tms for _, tms in NIGHTS if is_light(tms)]
    whole = collections.Counter(t for tms in calendar for t in tms)
    shift = max(whole[t] - per_team[t] for t in NBA_TEAMS)
    print("whole calendar instead: %d light nights, not %d, and up to %d per "
          "team (%s)."
          % (len(calendar), len(light), shift,
             ", ".join("%s %d->%d" % (t, whole[t], per_team[t])
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
    print("  scored-period GAMES per team: %d-%d"
          % (min(scored.values()), max(scored.values())))

    print("\nPER BODY. One added %d-GP forward-eligible body, swept across all %d"
          % (gp, len(NBA_TEAMS)))
    print("schedules on the %d-man roster. `sdRate` = that PF sd over the MEASURED"
          % len(full))
    print("PF-per-rate-point slope of the same %d-schedule MEAN (central "
          "difference, +-%d)." % (len(NBA_TEAMS), SWEEP_H))
    grid = sorted({r + d for r in SWEEP_RATES for d in (-SWEEP_H, 0, SWEEP_H)})
    swept = engine.run_many([full + [star(r, gp, ("SF", "PF"), t, "ADD")]
                             for r in grid for t in NBA_TEAMS])
    pf_iter = iter(res["pf"] - base["pf"] for res in swept)
    sweep = {r: [next(pf_iter) for _ in NBA_TEAMS] for r in grid}
    print("  %6s %9s %8s %9s %9s %9s"
          % ("rate", "meanPF", "sdPF", "sd wins", "sdRate", "spanRate"))
    ratepts = {}
    for r in SWEEP_RATES:
        v, sd = sweep[r], statistics.stdev(sweep[r])
        # central difference of the schedule MEAN, not `stats.slope`'s
        # least-squares fit -- same word, different quantity
        pf_per_rate = (statistics.mean(sweep[r + SWEEP_H])
                       - statistics.mean(sweep[r - SWEEP_H])) / (2.0 * SWEEP_H)
        ratepts[r] = sd / pf_per_rate
        print("  %6d %9.0f %8.1f %9.3f %9.2f %9.2f"
              % (r, statistics.mean(v), sd, pf_wins(sd), sd / pf_per_rate,
                 (max(v) - min(v)) / pf_per_rate))
    lo, hi = SWEEP_RATES[0], SWEEP_RATES[-1]
    print("  body %.1fx from rate %d to %d, schedule sd %.1fx: %.2f rate points"
          " at %d, %.2f at %d"
          % (statistics.mean(sweep[hi]) / statistics.mean(sweep[lo]), lo, hi,
             statistics.stdev(sweep[hi]) / statistics.stdev(sweep[lo]),
             ratepts[lo], lo, ratepts[hi], hi))
    print("  auction grades %.0f-%.0f FPts; threshold ~%.2f rate points"
          % (min(p["avg"] for p in fa), max(p["avg"] for p in fa), ratepts[lo]))

    print("\nSTEERING THE AUCTION. %d bodies (`pad`'s FA grades at %d GP); the"
          % (len(fa), gp))
    print("other %d stay where they are on %d NBA teams, and %d of the %d light"
          % (len(held), sum(1 for t in held_tms if not unsigned(t)),
             coverage(held_tms), len(light)))
    print("nights are already reached by them. Selection rule: greedy on")
    print("`coverage`. Baseline NOT CARING = mean of %d random %d-team draws."
          % (STEER_DRAWS, n))

    rng = random.Random(13)
    draws = [[rng.choice(NBA_TEAMS) for _ in range(n)]
             for _ in range(STEER_DRAWS)]
    offers = [rng.sample(NBA_TEAMS, OFFER_N) for _ in range(STEER_DRAWS)]
    best = coverage_picks(n)
    worst = coverage_picks(n, best=False)
    deep = max(NBA_TEAMS, key=lambda t: per_team[t])
    stack = [deep] * n
    # one sharded batch for every roster measured here -- best/worst/stack,
    # the ladder's paired rungs, the random offers -- not one reshard each
    offer_picks = [coverage_picks(n, teams=o) for o in offers]
    tms_list = ([best, worst, stack]
               + [best[:k] + d[k:] for d in draws for k in range(n)]
               + offer_picks)
    pf_vals = [res["pf"] for res in
              engine.run_many([steer(full, tms) for tms in tms_list])]
    top, worst_pf, stack_pf = pf_vals[:3]
    ladder_pf, got = (pf_vals[3:3 + STEER_DRAWS * n],
                      pf_vals[3 + STEER_DRAWS * n:])
    # paired down the ladder: rung k and rung k-1 share the draw AND the seeds,
    # so the increment is a within-draw quantity, sd 3-5x smaller than either
    # rung's own spread
    rows = [[ladder_pf[i * n + k] for k in range(n)] + [top]
            for i in range(STEER_DRAWS)]
    idle = statistics.mean(r[0] for r in rows)
    lottery = [r[0] for r in rows]
    cum = [[r[k] - r[0] for r in rows] for k in range(1, n + 1)]

    def vs_idle(total):
        return pf_wins(total - idle)

    def se_wins(xs):
        return pf_wins(se_mean(xs))

    w = [pf_wins(statistics.mean(c)) for c in cum]
    print("  %-22s %s" % ("schedule-aware picks",
                          " ".join("%7d" % k for k in range(1, n + 1))))
    print("  %-22s %s" % ("cumulative +wins",
                          " ".join("%+7.3f" % x for x in w)))
    print("  %-22s %s" % ("  paired +-",
                          " ".join("%7.3f" % se_wins(c) for c in cum)))
    print("  %-22s %s" % ("steered picks cover", " ".join(
        "%7d" % coverage(best[:k]) for k in range(1, n + 1))))
    print("  %-22s %s" % ("all %d cover, mean" % n, " ".join(
        "%7.1f" % statistics.mean(coverage(best[:k] + d[k:]) for d in draws)
        for k in range(1, n + 1))))
    peak = max(range(n), key=lambda i: w[i])
    print("  picks: %s" % " ".join(best))
    print("  best %d, all %d teams on offer : %+.3f wins"
          % (n, len(NBA_TEAMS), w[-1]))
    print("  worst %d (greedy-min: a stack) : %+.3f wins"
          % (n, vs_idle(worst_pf)))
    last = w[-1] - w[-2]
    se = se_wins([a - b for a, b in zip(cum[-1], cum[-2])])
    sat = next(k for k in range(1, n + 1)
               if coverage(best[:k]) == coverage(best))
    print("  peaks at %d of %d picks (%+.3f); coverage saturates at %d (%d of "
          "%d nights)" % (peak + 1, n, w[peak], sat, coverage(best), len(light)))
    print("  %dth pick is %s again, and buys %+.3f against a paired +-%.3f"
          % (n, best[-1], last, se))
    early = max(1, (peak + 1) // 2)
    shown = [float("%+.3f" % x) for x in w]
    print("  %d pick%s buy%s %d%% of the peak, %d buy %d%%"
          % (early, "" if early == 1 else "s", "s" if early == 1 else "",
             round(100 * shown[early - 1] / shown[peak]), early + 1,
             round(100 * shown[early] / shown[peak])))
    print("  %d random draws land %+.2f to %+.2f wins against the best %d, "
          "sd %.3f"
          % (STEER_DRAWS, pf_wins(min(lottery) - top),
             pf_wins(max(lottery) - top), n,
             pf_wins(statistics.stdev(lottery))))
    print("  best %d of a random %d-team offer  : %+.3f +- %.3f wins"
          % (n, OFFER_N, vs_idle(statistics.mean(got)), se_wins(got)))

    print("\nCOVERAGE, NOT A SUMMED NIGHT COUNT.")
    print("  all %d on %s : %d body-nights summed, %d distinct, %+.3f wins"
          % (n, deep, n * per_team[deep], coverage(stack), vs_idle(stack_pf)))
    print("  spread best %d : %d body-nights summed, %d distinct, %+.3f wins"
          % (n, sum(per_team[t] for t in best), coverage(best), w[-1]))
    print("  %dx%d is the CEILING on that sum, and the shape that reaches it"
          % (n, per_team[deep]))
    print("  lands %s not caring." % ("BELOW" if stack_pf < idle else "above"))

    # one row per configuration, not per `run` -- the ladder alone is n rungs x
    # STEER_DRAWS near-identical rosters, which would make the fit a statement
    # about the ladder rather than about coverage
    configs = ([(d, r[0]) for d, r in zip(draws, rows)] + list(zip(offers, got))
               + [(best, top), (worst, worst_pf), (stack, stack_pf)])

    def fit(metric):
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
    print("  Coverage %s that comparison. A random %d covers %.0f of %d."
          % ("wins" if cr2 > sr2 else "LOSES", n,
             statistics.mean(coverage(d) for d in draws), len(light)))
