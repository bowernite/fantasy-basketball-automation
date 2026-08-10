import statistics
from .. import engine
from ..roster import (
    GROUPS, basis, group_slots, our_roster, pure_bodies, slot_group, star, swap)
from ..schedule import SIM_TM
from ..stats import slope
from ..value import group_body, group_fits, replacement, thin
from ..wins import PF_PER_WIN, wins


def report_replacement():
    full = basis()
    print("value of an added 68-GP forward, fitted as c*(rate-R)*GP over rates")
    print("30/40/50/65. K = PF per win / c, so wins = (rate-R)*GP / K.")
    print("Rows are thin(basis(),n) -- the best n of the PADDED 38, so the 28 row")
    print("is not the live file's R. Measure a live roster with replacement() on it.")
    print("  %6s %10s %8s %8s" % ("thin to", "R", "c", "K"))
    for n in (38, 28):        # the only two roster sizes that exist
        R, c = replacement(thin(full, n))
        print("  %6d %10.1f %8.3f %8.0f" % (n, R, c, PF_PER_WIN / c))

    print("\nR IS POSITION-DEPENDENT, and this is a third of the formula's error.")
    print("  %8s %8s %8s %8s" % ("group", "R", "c", "K"))
    fits = group_fits(full)
    Rs = {}
    for lab, (R, c) in fits.items():
        Rs[lab] = R
        print("  %8s %8.1f %8.3f %8.0f" % (lab, R, c, PF_PER_WIN / c))
    # Numbers AND cause DERIVED off the LOADED roster, which `--roster` serves for
    # every team: a fixed sentence naming one group as the crowded one prints our
    # own roster's explanation over somebody else's deltas.
    #
    # Counts off `full` -- the SAME padded bodies R was fitted on. Off the live
    # file they are 4-8 bodies per group short of the roster being explained, and
    # padding does not add them evenly (4 guards, 3 forwards, 3 centers).
    print("  R against forwards: guard %+.1f, center %+.1f."
          % (Rs["guard"] - Rs["forward"], Rs["center"] - Rs["forward"]))
    byR = sorted(Rs, key=lambda g: -Rs[g])
    counts = {g: (pure_bodies(full, e), group_slots(e)) for g, e in GROUPS.items()}
    crowd = {g: b / s for g, (b, s) in counts.items()}
    print("  crowding on those same %d bodies -- pure bodies / slots: %s."
          % (len(full), ", ".join("%s %d/%d" % ((g,) + counts[g]) for g in byR)))
    print("  Highest R is %s. Crowding %s the three here, so read the R column"
          % (byR[0], "orders" if all(crowd[a] > crowd[b]
                                     for a, b in zip(byR, byR[1:]))
             else "does NOT order"))
    print("  itself -- a property of THIS roster's shape, re-measured when the")
    print("  shape moves, never inferred from a body count.")

    print("\nvalue in rate is LINEAR above ~30, not a power law.")
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
    print("  The x-intercept of THIS line is not R: R is fitted over 30/40/50/65")
    print("  and printed above, this one over 30..65 in fives. They differ, and")
    print("  quoting either as 'the' replacement level invites the mismatch.")
    print("  Constant increments => NO convexity above 30. The real convexity is")
    print("  confined to rate < 30, which is exactly what makes the linear")
    print("  formula unusable down there.")


def report_positions():
    full = basis()
    base = engine.run(full)["pf"]
    print("value of an ADDED body of each eligibility, vs the same rate as a")
    # Counted on `full`, the roster the body is ADDED to. The live file is a
    # different shape -- padding adds 4 guards, 3 forwards and 3 centers.
    print("guard. this %d-man roster's %d pure PG/SG chase at most %d"
          % (len(full), pure_bodies(full, GROUPS["guard"]),
             group_slots(GROUPS["guard"])))
    print("guard-eligible slots; %d pure centers chase %d."
          % (pure_bodies(full, GROUPS["center"]), group_slots(GROUPS["center"])))
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
    """Does (rate - R) x GP predict what the sim measures? For whom?"""
    full = basis()
    base = engine.run(full)
    R, c = replacement(full)
    K = PF_PER_WIN / c
    print("formula: (rate - %.1f) x GP / %.0f = wins, tested as 1-for-1s against"
          % (R, K))
    # The SAME swap `players` prices -- a 68-GP body of his own slot group. The two
    # reports must grade ONE counterfactual, or the posR column is scored against a
    # `sim` column with the very error it exists to fix baked into it.
    print("a replacement 68-GP body OF HIS OWN SLOT GROUP -- the counterfactual")
    print("`players` prices, so the two reports grade the same swap.")
    print("`sim` is what the sim measured; `1R` the formula on the ONE roster-wide")
    print("R printed above; `err` and `posR err` are (formula / sim - 1), the")
    print("second using the per-slot-group R from `replacement`. Signed: + means")
    print("the formula pays him more than the sim does.\n")
    grp = group_fits(full)
    print("  %-22s %5s %4s %8s %8s %7s %7s" %
          ("player", "rate", "gp", "sim", "1R", "err", "posR err"))
    rows = []
    for p in sorted(our_roster(), key=lambda q: -(q["avg"] - R) * q["gp"])[:12]:
        g = slot_group(p["elig"])
        r = engine.run(swap(full, [p["n"]], [group_body(g, grp[g][0])]))
        sim_w = wins(base, r)
        pred = (p["avg"] - R) * p["gp"] / K
        Rp, cp = grp[g]
        predp = (p["avg"] - Rp) * p["gp"] / (PF_PER_WIN / cp)
        rows.append((p["n"], sim_w, pred, predp))
        print("  %-22s %5.1f %4d %+8.2f %+8.2f %+6.0f%% %+6.0f%%"
              % (p["n"], p["avg"], p["gp"], sim_w, pred,
                 100 * (pred / sim_w - 1) if sim_w else 0,
                 100 * (predp / sim_w - 1) if sim_w else 0))
    err = [abs(pr / s - 1) for _, s, pr, _ in rows if s > 0.1]
    errp = [abs(pp / s - 1) for _, s, _, pp in rows if s > 0.1]
    print("\n  |error| median %.0f%%, worst %.0f%%. It is NOT a 1%% formula."
          % (100 * statistics.median(err), 100 * max(err)))
    print("  With a PER-POSITION R: median %.0f%%, worst %.0f%%. A third of the"
          % (100 * statistics.median(errp), 100 * max(errp)))
    print("  error is a fixable constant, not irreducible roster shape -- use the")
    print("  per-position R from `replacement` when you sort with this.")
    by_sim = [n for n, _, _, _ in sorted(rows, key=lambda r: -r[1])][:5]
    by_f = [n for n, _, _, _ in sorted(rows, key=lambda r: -r[2])][:5]
    by_fp = [n for n, _, _, _ in sorted(rows, key=lambda r: -r[3])][:5]
    print("  top 5 by sim         : %s" % ", ".join(by_sim))
    print("  top 5 by formula     : %s" % ", ".join(by_f))
    print("  top 5 by formula+posR: %s" % ", ".join(by_fp))
    # DERIVED, never asserted: every ordering claim here is a comparison of the
    # three lists above, so it cannot contradict them.
    print("  posR %s the top-5 order, and it %s the sim's."
          % ("leaves" if by_f == by_fp else "changes",
             "matches" if by_fp == by_sim else "still differs from"))
    print("  Judge any such difference against the per-block sd in `players`")
    print("  before reading it as a mis-ranking either R fixes.")
