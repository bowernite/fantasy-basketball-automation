import statistics
from .. import bracket, engine
from ..bracket import (
    BANDS, BRACKET_TEAMS, LADDERS, FIELD_MARGIN_CV, MARGIN_CV, bracket_weeks,
    field_mean, ladder_games, loaded, opp_mean, reg_mean, reg_week, team_levels,
    round_pwin, seed_title, sigma, title_prob, title_slope, week_points)
from ..data import BRACKET, DELTA_W_MATCHUPS, PERIODS, REGULAR
from ..engine import TRIALS
from ..projections import projected_rate
from .. import roster
from ..roster import basis, our_roster
from ..schedule import SIM_TM, bracket_games, period_games, unsigned
from ..stats import cdf, phi, se_mean
from ..value import group_replacement, seed_blocks


def _label(i):
    return "W%d" % PERIODS[i]["ordinal"]


def _flags(p):
    """Why this row's `W` columns are blank, in `players`' own vocabulary
    (`Eval Template §Flags`)."""
    return " ".join(code for code, on in
                    (("fa", unsigned(p["tm"])),
                     ("noproj", projected_rate(p["n"]) is None)) if on)


def _cell(p, w):
    """One `W` cell: points/games, or `-` for no NBA team or no projection
    (`Eval Definitions §Columns`)."""
    if _flags(p):
        return "-"
    return "%.0f/%d" % (week_points(p)[w], bracket_games(p["tm"])[w])


def _week_legend():
    """What a `W` cell is, above every table that carries one."""
    print("W columns are FPts/Gp x that player's NBA games in the period x his")
    print("projected share of the season (GPp / his NBA team's games) -- the")
    print("same haircut the sim draws behind Delta P, so never add the two:")
    print("that counts availability twice AND mixes currencies. Points, so")
    print("never read against the 0.1-win floor -- that floor is wins over a")
    print("%d-matchup regular season (`method.md`)." % DELTA_W_MATCHUPS)


def _week_flag_legend():
    """Why a row's `W` columns are blank."""
    print("`fa` unsigned in the NBA, so he has no bracket games of his own and")
    print("the sim runs him on %s's schedule; `noproj` no projection, so his"
          % SIM_TM)
    print("rate is LAST SEASON's (`Eval Template §Flags`).")


def report_weeks():
    """`W20`-`W23` per player and nothing else -- no bracket Monte Carlo.

    A `W` cell is a rate times NBA games times a GP share, all three off the
    roster file and the schedule, so the columns every team eval carries are
    arithmetic. `playoffs` prices the title beside them and costs ~350
    simulated seasons to do it; the eleven evals that want only the columns run
    this instead.
    """
    ours = our_roster()
    print("Bracket: %d rounds, periods %s (%s to %s)."
          % (len(BRACKET), "-".join(str(PERIODS[i]["ordinal"])
                                    for i in (BRACKET[0], BRACKET[-1])),
             PERIODS[BRACKET[0]]["start"], PERIODS[BRACKET[-1]]["end"]))
    _week_legend()
    print("Which of these rounds a team plays depends on its seed, and what a")
    print("body is worth across them is `playoffs` -- not derivable here.")
    print("  %-24s %s  %s"
          % ("player", " ".join("%6s" % _label(i) for i in BRACKET), "flags"))
    for p in ours:
        print("  %-24s %s  %s"
              % (p["n"],
                 " ".join("%6s" % _cell(p, w) for w in range(len(BRACKET))),
                 _flags(p)))
    _week_flag_legend()


def _z(pwin):
    """The standard normal quantile at `pwin`, by bisection."""
    lo, hi = -8.0, 8.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cdf(mid) < pwin else (lo, mid)
    return (lo + hi) / 2


def _per_pf(pwin, sd):
    """d P(win that game) / d PF, at a margin whose win probability is `pwin`."""
    return phi(_z(pwin)) / sd


def _one_draw(full, seed0):
    """Every figure the two tables below are read off, on ONE Monte Carlo draw
    of the whole basis -- our bracket weeks and the field's, seeded together.

    `bracket.draw` moves the field too, so `sigma`, `opp_mean` and `field_mean`
    move with it and a round is priced against the draw it is scored on. Only
    the loaded roster re-drawn would leave a mismatch in the spread and book it
    as error.
    """
    with bracket.draw(seed0):
        mus = bracket_weeks(full, seed0=seed0)
        reg_opp = reg_mean()
        # The one matchup here whose opponent is not named, so its margin
        # carries the field's level spread as well (`bracket.FIELD_MARGIN_CV`).
        reg_sd = FIELD_MARGIN_CV * reg_opp
        reg_mu = reg_week(engine.run(full, seed0=seed0)["wk"])
        reg_p = cdf((reg_mu - reg_opp) / reg_sd)
        # d P(win a regular matchup) / d PF, per matchup: the per-round
        # multiplier's denominator.
        reg_pf = _per_pf(reg_p, reg_sd) / len(REGULAR)
        return {"mus": mus, "reg": (reg_mu, reg_opp, reg_sd, reg_p),
                "band": {b.label: (title_prob(mus, b),
                                   [seed_title(mus, s) for s in b.slots],
                                   [title_slope(mus, b, BRACKET.index(i))
                                    / reg_pf for i in b.periods])
                         for b in BANDS}}


def _spread(xs):
    """The sd of one draw, NOT the standard error of their mean: the figure
    printed beside it is a single draw, not an average of these."""
    return statistics.stdev(list(xs))


def report_playoffs():
    """`W20`-`W23` and `Delta P(title)` per player, all three seed bands
    (`Eval Definitions §ΔP(title)`)."""
    full = basis()
    ours = our_roster()
    R = group_replacement(full)
    # Draw 0 is `bracket.SEED0` -- the one every figure below is PRINTED from,
    # so the basis rows and the summary describe one bracket. The rest measure
    # what a single draw of it is worth.
    draws = [_one_draw(full, s) for s in
             seed_blocks(bracket.TITLE_BLOCKS, TRIALS, bracket.SEED0)]
    mus = draws[0]["mus"]
    reg_mu, reg_opp, reg_sd, reg_p = draws[0]["reg"]
    reg_games = statistics.mean(period_games(i) for i in REGULAR)

    print("Delta P(title) per player, against a replacement 68-GP body OF HIS")
    print("OWN SLOT GROUP -- the counterfactual `players` prices (`Eval")
    print("Definitions §Delta w`), in the only currency a bracket week pays in.")
    print("NEVER summed with, netted against or converted into `Delta w`.")
    print("%d-man roster: %s." % (len(full), ", ".join(
        "%s %.1f" % (g, R[g]) for g in sorted(R))))
    print("Bracket: %d rounds, periods %s (%s to %s), %d of %d teams."
          % (len(BRACKET), "-".join(str(PERIODS[i]["ordinal"])
                                    for i in (BRACKET[0], BRACKET[-1])),
             PERIODS[BRACKET[0]]["start"], PERIODS[BRACKET[-1]]["end"],
             len(BRACKET_TEAMS), len(PERIODS[REGULAR[0]]["games"]) * 2))
    print("Seed bands and the rounds each has to win: %s."
          % ", ".join("%s %s" % (b.label, "/".join(_label(i) for i in b.periods))
                      for b in BANDS))
    _week_legend()
    print("Delta P is in PERCENTAGE POINTS, averaged over %d shared %d-trial"
          % (bracket.TITLE_BLOCKS, TRIALS))
    print("seed blocks. Each +- is the standard error of the figure BESIDE it,")
    print("across those blocks: the three bands are transforms of one simulated")
    print("week, so they move together and the widest band's noise is not the")
    print("others'. Two ROWS share the blocks too -- an ordering between them")
    print("is the paired difference, which no column here carries. Sorted on")
    print("the %s band." % BANDS[0].label)

    print("  %-24s %s %s  %s"
          % ("player", " ".join("%6s" % _label(i) for i in BRACKET),
             " ".join("%6s %6s" % (b.label, "+-") for b in BANDS), "flags"))
    d = bracket.player_title(full, [p["n"] for p in ours], R=R)
    for p in sorted(ours, key=lambda q: -d[q["n"]][BANDS[0].label][0]):
        row = d[p["n"]]
        print("  %-24s %s %s  %s"
              % (p["n"],
                 " ".join("%6s" % _cell(p, w) for w in range(len(BRACKET))),
                 " ".join("%+6.2f %6s"
                          % (100 * row[b.label][0],
                             "+-%.2f" % (100 * se_mean(row[b.label][2])))
                          for b in BANDS),
                 _flags(p)))
    print("Flags say why a row's W columns are blank while its Delta P is")
    print("priced anyway:")
    _week_flag_legend()

    print("\nBasis. mu_us and mu_opp are ONE measurement of two rosters: every")
    print("team's own file, projected, padded to %d, this engine -- so the two"
          % len(full))
    print("sides differ by roster quality and by nothing else, and a")
    print("league-wide level error cancels instead of booking as an edge.")
    print("A band is a SEED RANGE the loaded roster is placed at, one seed at a")
    print("time, with the field below filling the rest of the draw in its own")
    print("order: it is neither last season's finish nor the rank printed")
    print("beside us here, which is where a #1 projection can read band 5-8.")
    print("Projected field -- the league on season PF, cut at the bracket's %d:"
          % len(BRACKET_TEAMS))
    for k, t in enumerate(team_levels()):
        print("  %2d %-58s %7.0f  %s"
              % (k + 1, roster.label(t.path), t.pf,
                 "<- loaded" if t.path == loaded() else
                 "" if k < len(BRACKET_TEAMS) else "(outside the field)"))
    print("mu_opp is that field's SURVIVOR for the round, not its mean: the")
    print("draw is seeds %s | %s, each half climbed"
          % tuple("-".join(str(s) for s in l) for l in LADDERS))
    print("worst seed first, so who a seed can meet is structure. The field's")
    print("own mean is beside it and is nobody's opponent.")
    print("sigma_w is the week-to-week spread of two NAMED teams' scores, at")
    print("%.4f of the level the round is played at -- both levels are already"
          % MARGIN_CV)
    print("in mu_us and mu_opp, so only that spread is left. The reg row's")
    print("opponent is drawn rather than named, out of all %d others and not"
          % (len(team_levels()) - 1))
    print("the %d seeds, so it carries that whole field's level spread too, at"
          % len(BRACKET_TEAMS))
    print("%.4f. Both off last season's wire (`method.md`)." % FIELD_MARGIN_CV)
    print("  %5s %6s %7s %8s %8s %8s %8s %8s"
          % ("band", "round", "games", "mu_us", "mu_opp", "field", "sigma",
             "P(round)"))
    for b in BANDS:
        for i in b.periods:
            w = BRACKET.index(i)
            print("  %5s %6s %7d %8.0f %8.0f %8.0f %8.0f %8.3f"
                  % (b.label, _label(i), period_games(i), mus[w],
                     statistics.mean(opp_mean(w, s) for s in b.slots),
                     field_mean(w), sigma(w),
                     statistics.mean(round_pwin(mus[w], w, s)
                                     for s in b.slots)))
    print("  %5s %6s %7.1f %8.0f %8.0f %8.0f %8.0f %8.3f  <- one regular period"
          % ("", "reg", reg_games, reg_mu, reg_opp, reg_opp, reg_sd, reg_p))

    print("\n  %6s %9s %8s %13s %8s %7s  %s"
          % ("band", "P(title)", "+-", "by seed", "+-", "rounds",
             "x a regular-season game"))
    for b in BANDS:
        got = [d["band"][b.label] for d in draws]
        p, each, mult = got[0]
        print("  %6s %9.3f %8s %6.3f-%.3f %8s %7d  %.1f +-%.1f"
              " (%.1f-%.1f by round)"
              % (b.label, p, "+-%.3f" % _spread(x[0] for x in got),
                 min(each), max(each),
                 "+-%.3f" % max(_spread(min(x[1]) for x in got),
                                _spread(max(x[1]) for x in got)),
                 len(b.periods), statistics.mean(mult),
                 _spread(statistics.mean(x[2]) for x in got),
                 min(mult), max(mult)))
    print("  Every +- on THIS table is the spread of the figure beside it over")
    print("  %d re-draws of the whole basis, ours and the field's together --"
          % bracket.TITLE_BLOCKS)
    print("  the sd of ONE draw, which is what each figure is. Read it the")
    print("  other way from the `Delta P` column above: that one is a paired")
    print("  difference at matched seeds and the draw cancels out of it, so")
    print("  these bars are the wider pair by an order of magnitude. `by seed`")
    print("  carries the wider of its two ends. Nothing here is paired against")
    print("  anything, so a gap between two bands is not a measured ordering.")
    print("  P(title) is the band's OWN seeds averaged; `by seed` is the spread")
    print("  across them, which the draw makes real -- 6 and 7 sit on the")
    print("  2-seed's side and 5 and 8 on the 1-seed's.")
    print("  The same PF, one week later in the calendar. Both sides are a")
    print("  share of the whole prize that week is played for -- a title, or")
    print("  one of %d regular matchups -- and both are per PF, so the rate"
          % len(REGULAR))
    print("  cancels and 'one game' is the same game. `Eval Definitions")
    print("  §Delta P(title)` forbids converting either into the other's units.")

    played, aside = ladder_games()
    tight = statistics.stdev(played + [-m for m in played])
    print("\n  sigma sensitivity. The %d bracket games actually played give a"
          % len(played))
    print("  margin sd of %.0f against the %.0f-%.0f above; at that"
          % (tight, min(sigma(w) for w in range(len(BRACKET))),
             max(sigma(w) for w in range(len(BRACKET)))))
    print("  sigma the %s band reads %.3f rather than %.3f. %d games is not a"
          % (BANDS[0].label, title_prob(mus, BANDS[0], tight),
             title_prob(mus, BANDS[0]), len(played)))
    print("  distribution -- it is printed as a bound, not used as the basis.")
    print("  Those %d are the title ladder alone: a seed pairing neither side"
          % len(played))
    print("  had already lost out of. The %d other scores in periods %s --"
          % (len(aside), "-".join(str(PERIODS[i]["ordinal"])
                                  for i in (BRACKET[0], BRACKET[-1]))))
    print("  the consolation half, and third place once both sides are out --")
    print("  run %.0f-%.0f and are excluded from every figure here."
          % (min(aside), max(aside)))
    print("  Period %d is bracket R1. Standings PF still counts it; `Delta w`"
          % PERIODS[BRACKET[0]]["ordinal"])
    print("  does not, so `W20` is not priced twice beside `Delta P(title)`.")
