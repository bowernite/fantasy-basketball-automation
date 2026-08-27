import statistics
from .. import engine
from ..data import DELTA_W_CAL, DELTA_W_MATCHUPS
from ..roster import (
    GROUPS, basis, group_slots, our_roster, pure_bodies, slot_group, star, swap)
from ..schedule import SIM_TM
from ..stats import slope
from ..value import group_body, group_fits, replacement, thin
from ..wins import pf_wins, wins


def report_replacement():
    full = basis()
    print("value of an added 68-GP forward, fitted as c*(rate-R)*GP over rates")
    print("30/40/50/65, on the %d-matchup basis." % DELTA_W_MATCHUPS)
    print("  %6s %10s %8s %8s" % ("thin to", "R", "c", "K"))
    for n in (38, 28):        # the only two roster sizes that exist
        R, c = replacement(thin(full, n))
        print("  %6d %10.1f %8.3f %8.0f" % (n, R, c, 1.0 / pf_wins(c)))

    print("\nR by slot group")
    print("  %8s %8s %8s %8s" % ("group", "R", "c", "K"))
    fits = group_fits(full)
    Rs = {}
    for lab, (R, c) in fits.items():
        Rs[lab] = R
        print("  %8s %8.1f %8.3f %8.0f" % (lab, R, c, 1.0 / pf_wins(c)))
    # derived off the LOADED roster, not hardcoded -- `--roster` serves every
    # team, and counts off `full` (the same padded bodies R was fitted on),
    # not the live file, which is short by an uneven number of bodies per group
    print("  R against forwards: guard %+.1f, center %+.1f."
          % (Rs["guard"] - Rs["forward"], Rs["center"] - Rs["forward"]))
    byR = sorted(Rs, key=lambda g: -Rs[g])
    counts = {g: (pure_bodies(full, e), group_slots(e)) for g, e in GROUPS.items()}
    crowd = {g: b / s for g, (b, s) in counts.items()}
    print("  pure bodies / slots on those same %d: %s"
          % (len(full), ", ".join("%s %d/%d" % ((g,) + counts[g]) for g in byR)))
    print("  highest R %s, crowding %s the three"
          % (byR[0], "orders" if all(crowd[a] > crowd[b]
                                     for a, b in zip(byR, byR[1:]))
             else "does NOT order"))

    print("\nadded PF by rate")
    base = engine.run(full)["pf"]
    rates = list(range(20, 70, 5))
    v = [engine.run(full + [star(r, 68, ("SF", "PF"), SIM_TM, "ADD")])["pf"] - base
         for r in rates]
    print("  %6s %9s %11s" % ("rate", "addedPF", "increment"))
    for i, (r, y) in enumerate(zip(rates, v)):
        print("  %6d %9.0f %11s"
              % (r, y, "%.0f" % (y - v[i - 1]) if i else "-"))
    hi = [(r, y) for r, y in zip(rates, v) if r >= 30]
    mx, my, a = slope([r for r, _ in hi], [y for _, y in hi])
    print("  fit over rate>=30: %.1f PF per rate point, x-intercept %.1f."
          % (a, mx - my / a))


def report_positions():
    full = basis()
    base = engine.run(full)["pf"]
    print("value of an ADDED body of each eligibility, vs a guard at the same "
          "rate.")
    # counted on `full`, the roster the body is added to, not the live file
    print("%d-man roster: %d pure PG/SG chase at most %d guard-eligible slots; "
          "%d pure centers chase %d."
          % (len(full), pure_bodies(full, GROUPS["guard"]),
             group_slots(GROUPS["guard"]),
             pure_bodies(full, GROUPS["center"]), group_slots(GROUPS["center"])))
    print("  %6s %10s %10s %10s" % ("rate", "guard PF", "forward", "center"))
    for rate in (25, 35, 45):
        v = {}
        for lab, elig in GROUPS.items():
            body = star(rate, 68, elig, SIM_TM, "ADD")
            v[lab] = engine.run(full + [body])["pf"] - base
        print("  %6d %10.0f %+9.0f%% %+9.0f%%"
              % (rate, v["guard"], 100 * (v["forward"] / v["guard"] - 1),
                 100 * (v["center"] / v["guard"] - 1)))


def report_formula():
    full = basis()
    base = engine.run(full, cal=DELTA_W_CAL)
    R, c = replacement(full)
    # through `pf_wins`, not `PF_PER_WIN / c` -- `replacement` fits `c` on the
    # standings calendar, and `sim` below is measured on `DELTA_W_CAL`; skipping
    # the basis conversion would grade the formula ~5% off and read as its error
    K = 1.0 / pf_wins(c)
    print("formula: (rate - %.1f) x GP / %.0f = wins, tested as 1-for-1s against"
          % (R, K))
    # same swap `players` prices -- both reports must grade one counterfactual,
    # or posR is scored against a `sim` column with its own error baked in
    print("a replacement 68-GP body OF HIS OWN SLOT GROUP.\n")
    grp = group_fits(full)
    print("  %-22s %5s %4s %8s %8s %7s %7s" %
          ("player", "rate", "gp", "sim", "1R", "err", "posR err"))
    rows = []
    for p in sorted(our_roster(), key=lambda q: -(q["avg"] - R) * q["gp"])[:12]:
        g = slot_group(p["elig"])
        r = engine.run(swap(full, [p["n"]], [group_body(g, grp[g][0])]),
                       cal=DELTA_W_CAL)
        sim_w = wins(base, r)
        pred = (p["avg"] - R) * p["gp"] / K
        Rp, cp = grp[g]
        predp = (p["avg"] - Rp) * p["gp"] * pf_wins(cp)
        rows.append((p["n"], sim_w, pred, predp))
        print("  %-22s %5.1f %4d %+8.2f %+8.2f %+6.0f%% %+6.0f%%"
              % (p["n"], p["avg"], p["gp"], sim_w, pred,
                 100 * (pred / sim_w - 1) if sim_w else 0,
                 100 * (predp / sim_w - 1) if sim_w else 0))
    err = [abs(pr / s - 1) for _, s, pr, _ in rows if s > 0.1]
    errp = [abs(pp / s - 1) for _, s, _, pp in rows if s > 0.1]
    print("\n  |error| median %.0f%%, worst %.0f%%"
          % (100 * statistics.median(err), 100 * max(err)))
    print("  with per-position R: median %.0f%%, worst %.0f%%"
          % (100 * statistics.median(errp), 100 * max(errp)))
    by_sim = [n for n, _, _, _ in sorted(rows, key=lambda r: -r[1])][:5]
    by_f = [n for n, _, _, _ in sorted(rows, key=lambda r: -r[2])][:5]
    by_fp = [n for n, _, _, _ in sorted(rows, key=lambda r: -r[3])][:5]
    print("  top 5 by sim         : %s" % ", ".join(by_sim))
    print("  top 5 by formula     : %s" % ", ".join(by_f))
    print("  top 5 by formula+posR: %s" % ", ".join(by_fp))
    # derived, not hardcoded -- a comparison of the three lists above
    print("  posR %s the top-5 order, and it %s the sim's."
          % ("leaves" if by_f == by_fp else "changes",
             "matches" if by_fp == by_sim else "still differs from"))
