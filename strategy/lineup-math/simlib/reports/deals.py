from .. import engine
from ..data import DELTA_W_CAL, DELTA_W_MATCHUPS
from ..roster import DEAD, basis, our_roster, star, swap
from ..schedule import SIM_TM, SIM_TMS
from ..value import bottom, breakeven_cell, breakeven_fmt, breakeven_value
from ..wins import PF_PER_WIN, wins


# held fixed so the only variable down a ladder is body count -- not a bucket
# or a recommendation (those live in `evals/teams/my-team/Ours.team.md`); shared
# by both reports below so they price the same trade
FILLER = ["Jalen Suggs", "Coby White", "Myles Turner", "Jakob Poeltl",
          "Naz Reid"]

# shared by both reports below, same reason as FILLER; NOT the `bottom-up`
# row's three, which `bottom` derives off board prices the sim doesn't carry
DREGS = ["De'Anthony Melton", "Anfernee Simons", "Keon Ellis"]

# generous end of the backfill bracket -- one constant `scenarios` cites and
# `breakevens` labels a row with, so both stay in agreement
GENEROUS = {"tm": "MIA", "avg": 14.0, "gp": 55, "elig": ["PG", "SG"]}


def grade(body):
    return "%.0f/%d" % (body["avg"], body["gp"])


def report_scenarios():
    full = basis()
    have = {p["n"] for p in full}
    left = [n for n in FILLER + DREGS if n not in have]
    if left:
        raise KeyError("%s: not on the roster as loaded. FILLER and DREGS are "
                       "typed by hand in `simlib/reports/deals.py` -- retype "
                       "the ladder around the trade you are pricing now (the "
                       "bottom-up row derives its own three)."
                       % ", ".join(left))
    base = engine.run(full, cal=DELTA_W_CAL)
    # priced on SIM_TM like every other incoming body, NOT on DEN -- his real
    # schedule is 1.0 sd below the 30-team mean, which would charge him ~76 PF
    # of handicap that the ladder would then read as body count
    JOKIC = dict(rate=65.2, gp=65, elig=("C",), tm=SIM_TM)
    BOTTOM = [p["n"] for p in bottom(full, 3)]
    SC = [
        # GP and position held fixed too, so the ONLY variable down this
        # ladder is how many bodies you pay
        ("Jokic 1-for-1  (Suggs)", FILLER[:1], [star(**JOKIC)]),
        ("Jokic 2-for-1  (+Coby White)", FILLER[:2], [star(**JOKIC)]),
        ("Jokic 3-for-1  (+Turner)", FILLER[:3], [star(**JOKIC)]),
        ("Jokic 4-for-1  (+Poeltl)", FILLER[:4], [star(**JOKIC)]),
        ("Jokic 5-for-1  (+Naz Reid)", FILLER[:5], [star(**JOKIC)]),
        ("1-for-1  Suggs -> 50", FILLER[:1], [star(50)]),
        ("1-for-1  Suggs -> 45", FILLER[:1], [star(45)]),
        ("1-for-1  Suggs -> 40 @78gp", FILLER[:1], [star(40, 78)]),
        ("2-for-1  -> 50", FILLER[:2], [star(50)]),
        ("3-for-1  -> 50", FILLER[:3], [star(50)]),
        ("3-for-1  dregs -> 45", DREGS, [star(45)]),
        ("3-for-1  -> fragile 55 @40gp", FILLER[:3], [star(55, 40)]),
        # spread over SIM_TMS so neither a schedule nor a stacking effect is
        # booked as body count, which is the one thing this ladder measures
        ("three separate 1-for-1s -> 42s", FILLER[:3],
         [star(42, 68, ("SF", "PF"), SIM_TMS[0], "S1"),
          star(42, 68, ("PG", "SG"), SIM_TMS[1], "S2"),
          star(42, 68, ("C",), SIM_TMS[2], "S3")]),
        ("two separate 1-for-1s -> 42s", FILLER[:2],
         [star(42, 68, ("SF", "PF"), SIM_TMS[0], "S1"),
          star(42, 68, ("PG", "SG"), SIM_TMS[1], "S2")]),
        ("bottom-up  3 lowest -> 3x 26", BOTTOM,
         [star(26, 76, ("SF", "PF"), SIM_TMS[0], "V1"),
          star(26, 76, ("PG", "SG"), SIM_TMS[1], "V2"),
          star(26, 76, ("C",), SIM_TMS[2], "V3")]),
    ]
    print("%d-man baseline: PF %.0f over the %d `Delta w` periods, weekly CV "
          "%.1f%%.\n1 win = %.0f PF."
          % (len(full), base["pf"], DELTA_W_MATCHUPS, 100 * base["cv"],
             PF_PER_WIN))
    print("incoming on %s (multi-body rows spread over %s)."
          % (SIM_TM, "/".join(SIM_TMS)))
    print("backfill: outgoing bodies 2..N refunded at %.0f FPts / %d GP, the "
          "post-auction\nopen-FA grade; `breakevens` reports the bracket to a "
          "%s refund." % (DEAD["avg"], DEAD["gp"], grade(GENEROUS)))
    # `n=` passed since `star`'s default name burns a counter value otherwise
    dflt = star(0, n="-")
    multi = sorted({b["gp"] for _, _, adds in SC if len(adds) > 1 for b in adds})
    print("shapes: %d-GP %s unless the label says otherwise; Jokic rows %d-GP "
          "%s;\nmulti-body rows one per slot group at %s GP."
          % (dflt["gp"], "/".join(dflt["elig"]), JOKIC["gp"],
             "/".join(JOKIC["elig"]),
             " and ".join("%d" % g for g in multi)))
    print("bottom-up row ships whoever the roster prices lowest as loaded: %s."
          % ", ".join(BOTTOM))
    print("%-30s %9s %7s %8s" % ("scenario", "dPF", "CV", "wins"))
    for label, out, adds in SC:
        r = engine.run(swap(full, out, adds), cal=DELTA_W_CAL)
        print("%-30s %+9.0f %6.1f%% %+8.2f"
              % (label, r["pf"] - base["pf"], 100 * r["cv"], wins(r, base)))


def report_breakevens():
    print("break-even incoming rate for an N-for-1, by roster size.")
    full, ours = basis(), our_roster()
    print("two counts: padded to %d, and the file as it stands. incoming on %s."
          % (len(full), SIM_TM))
    shapes = [("68 GP forward", 68, ("SF", "PF")),
              ("65 GP center", 65, ("C",)),
              ("78 GP forward", 78, ("SF", "PF"))]
    full_base, ours_base = engine.run(full)["pf"], engine.run(ours)["pf"]
    for roster, base in ((full, full_base), (ours, ours_base)):
        avail = [n for n in FILLER if any(p["n"] == n for p in roster)]
        print("\n  %d-man roster. give up %s" % (len(roster), ", ".join(
            "%s(%.1f)" % (n, next(p["avg"] for p in roster if p["n"] == n))
            for n in avail)))
        print("    %-16s %s" % ("incoming shape", "  ".join(
            "%d-for-1" % k for k in range(2, len(avail) + 1))))
        for lab, gp, elig in shapes:
            row = [breakeven_cell(roster, avail[:k], gp, elig, base=base)
                   for k in range(2, len(avail) + 1)]
            print("    %-16s %s" % (lab, "  ".join(row)))
    print("\n  %d dregs (%s) at %d men, 68 GP forward: %s"
          % (len(DREGS), ", ".join(n.split()[-1] for n in DREGS), len(full),
             breakeven_cell(full, DREGS, base=full_base)))

    # measured off the roster in hand, not typed -- `our_roster` re-projects
    # on every feed
    print("\nBACKFILL GRADE. bracket: %s post-auction open FA, %s generous; our "
          "worst KEPT body rates %.1f."
          % (grade(DEAD), grade(GENEROUS), min(p["avg"] for p in ours)))
    print("    %-16s %s" % ("refund grade", "  ".join(
        "%d-for-1" % k for k in range(2, 6))))
    band = {}
    lean = {"tm": "MIA", "avg": 10.0, "gp": 48, "elig": ["PG", "SG"]}
    for d in (None, lean, GENEROUS):
        lab = grade(d or DEAD)
        band[lab] = [breakeven_value(full, FILLER[:k], 68, ("SF", "PF"), dead=d,
                                     base=full_base)
                     for k in range(2, 6)]
        print("    %-16s %s"
              % (lab, "  ".join(breakeven_fmt(v) for v in band[lab])))
    strict, generous = band[grade(DEAD)], band[grade(GENEROUS)]

    def spread(a, b):
        # `-` where either cell is out of bracket -- a difference of two
        # bounds is not a rate-point spread
        both = isinstance(a, float) and isinstance(b, float)
        return "%.1f" % (a - b) if both else "-"
    print("  band across that bracket: %s rate points at 2..5-for-1."
          % "/".join(spread(a, b) for a, b in zip(strict, generous)))
