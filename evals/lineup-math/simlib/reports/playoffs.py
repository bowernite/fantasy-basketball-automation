import statistics
from .. import bracket, engine
from ..bracket import (
    BANDS, BRACKET_TEAMS, LADDERS, FIELD_MARGIN_CV, MARGIN_CV, bracket_weeks,
    field_mean, ladder_games, loaded, opp_mean, reg_mean, reg_week, team_levels,
    round_pwin, seed_title, sigma, title_prob, title_slope, week_points)
from ..data import BRACKET, PERIODS, REGULAR
from ..engine import TRIALS
from ..projections import projected_rate
from .. import roster
from ..roster import basis, our_roster
from ..schedule import bracket_games, period_games, unsigned
from ..stats import cdf, phi, se_mean
from ..value import group_replacement, seed_blocks


def _label(i):
    return "W%d" % PERIODS[i]["ordinal"]


def _flags(p):
    return " ".join(code for code, on in
                    (("fa", unsigned(p["tm"])),
                     ("noproj", projected_rate(p["n"]) is None)) if on)


def _cell(p, w):
    if _flags(p):
        return "-"
    return "%.0f/%d" % (week_points(p)[w], bracket_games(p["tm"])[w])


def report_weeks():
    ours = our_roster()
    print("Bracket: %d rounds, periods %s (%s to %s)."
          % (len(BRACKET), "-".join(str(PERIODS[i]["ordinal"])
                                    for i in (BRACKET[0], BRACKET[-1])),
             PERIODS[BRACKET[0]]["start"], PERIODS[BRACKET[-1]]["end"]))
    print("  %-24s %s  %s"
          % ("player", " ".join("%6s" % _label(i) for i in BRACKET), "flags"))
    for p in ours:
        print("  %-24s %s  %s"
              % (p["n"],
                 " ".join("%6s" % _cell(p, w) for w in range(len(BRACKET))),
                 _flags(p)))


def _z(pwin):
    lo, hi = -8.0, 8.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cdf(mid) < pwin else (lo, mid)
    return (lo + hi) / 2


def _per_pf(pwin, sd):
    # d P(win that game) / d PF, at a margin whose win probability is `pwin`
    return phi(_z(pwin)) / sd


def _one_draw(full, seed0):
    # `bracket.draw` moves the field too, so `sigma`/`opp_mean`/`field_mean`
    # move with it -- re-drawing only the loaded roster would mismatch the
    # spread and book it as error
    with bracket.draw(seed0):
        mus = bracket_weeks(full, seed0=seed0)
        reg_opp = reg_mean()
        # this matchup's opponent isn't named, so its margin also carries the
        # field's level spread (`bracket.FIELD_MARGIN_CV`, not `MARGIN_CV`)
        reg_sd = FIELD_MARGIN_CV * reg_opp
        reg_mu = reg_week(engine.run(full, seed0=seed0)["wk"])
        reg_p = cdf((reg_mu - reg_opp) / reg_sd)
        reg_pf = _per_pf(reg_p, reg_sd) / len(REGULAR)
        return {"mus": mus, "reg": (reg_mu, reg_opp, reg_sd, reg_p),
                "band": {b.label: (title_prob(mus, b),
                                   [seed_title(mus, s) for s in b.slots],
                                   [title_slope(mus, b, BRACKET.index(i))
                                    / reg_pf for i in b.periods])
                         for b in BANDS}}


def _spread(xs):
    # sd of one draw, NOT the standard error of their mean -- the figure
    # printed beside it is a single draw, not an average of these
    return statistics.stdev(list(xs))


def report_playoffs():
    full = basis()
    ours = our_roster()
    R = group_replacement(full)
    # draw 0 is `bracket.SEED0`, the one every other figure below is printed
    # from, so the basis rows and the summary describe one bracket; the rest
    # only measure what a single draw of it is worth
    draws = [_one_draw(full, s) for s in
             seed_blocks(bracket.TITLE_BLOCKS, TRIALS, bracket.SEED0)]
    mus = draws[0]["mus"]
    reg_mu, reg_opp, reg_sd, reg_p = draws[0]["reg"]
    reg_games = statistics.mean(period_games(i) for i in REGULAR)

    print("Delta P(title|seed) per player, against a replacement 68-GP body OF")
    print("HIS OWN SLOT GROUP -- seed HELD.")
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
    print("Delta P in PERCENTAGE POINTS, averaged over %d shared %d-trial seed"
          % (bracket.TITLE_BLOCKS, TRIALS))
    print("blocks; each +- is the standard error of the figure beside it.")
    print("Sorted on the %s band." % BANDS[0].label)

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

    print("\nBasis.")
    print("Projected field -- the league on season PF, cut at the bracket's %d:"
          % len(BRACKET_TEAMS))
    for k, t in enumerate(team_levels()):
        print("  %2d %-58s %7.0f  %s"
              % (k + 1, roster.label(t.path), t.pf,
                 "<- loaded" if t.path == loaded() else
                 "" if k < len(BRACKET_TEAMS) else "(outside the field)"))
    print("draw: seeds %s | %s, climbed worst seed first."
          % tuple("-".join(str(s) for s in l) for l in LADDERS))
    print("mu_opp is that field's SURVIVOR for the round, not its mean.")
    print("sigma: %.4f x the round's level, reg %.4f x the field's"
          % (MARGIN_CV, FIELD_MARGIN_CV))
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
    print("  every +- here is the sd of ONE draw over %d re-draws of the basis."
          % bracket.TITLE_BLOCKS)

    played, aside = ladder_games()
    tight = statistics.stdev(played + [-m for m in played])
    print("\n  sigma sensitivity: %d ladder games give margin sd %.0f vs the"
          % (len(played), tight))
    print("  %.0f-%.0f above; %s band reads %.3f vs %.3f -- a bound, not the basis."
          % (min(sigma(w) for w in range(len(BRACKET))),
             max(sigma(w) for w in range(len(BRACKET))), BANDS[0].label,
             title_prob(mus, BANDS[0], tight), title_prob(mus, BANDS[0])))
    print("  %d other scores in periods %s run %.0f-%.0f, excluded here."
          % (len(aside), "-".join(str(PERIODS[i]["ordinal"])
                                  for i in (BRACKET[0], BRACKET[-1])),
             min(aside), max(aside)))
