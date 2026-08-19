from .. import engine
from ..data import DELTA_W_CAL, DELTA_W_MATCHUPS
from ..roster import DEAD, basis, our_roster, star, swap
from ..schedule import SIM_TM, SIM_TMS
from ..value import bottom, breakeven_cell, breakeven_fmt, breakeven_value
from ..wins import PF_PER_WIN, wins


# A scenario's FILLER, not a bucket, a surplus list or a recommendation: held
# fixed so the only variable down a ladder is body count. Two of these price as
# Core, where shipping one is a walk-away trigger (`trades`). Buckets live in
# `evals/teams/my-team/My Team.md`; this list is not one and must not be read as one.
#
# ONE list, because the two reports below are read against each other: a second
# copy asserting in prose that it is "the same filler" is a comparison that can
# drift into two different trades without either table saying so.
FILLER = ["Jalen Suggs", "Coby White", "Myles Turner", "Jakob Poeltl",
          "Naz Reid"]

# The bottom-of-roster row both reports run, for the same reason FILLER is one
# list: `scenarios` prices the 3-for-1 and `breakevens` prints what it would have
# to bring back, and they are only the same trade while they are the same three
# names. The prose below is derived off it too -- a hand-typed "(Melton, Simons,
# Ellis)" beside a list is a caption that can stop describing its own table.
#
# NOT the `bottom-up` row's three, which `bottom` derives: these are a trade-VALUE
# judgment off board prices the sim does not carry, and a body the board prices at
# nothing is not the body the sim prices lowest.
DREGS = ["De'Anthony Melton", "Anfernee Simons", "Keon Ellis"]

# The generous end of the backfill bracket, once. `scenarios` cites it as the
# grade `breakevens` reports out to and `breakevens` labels a band row with it,
# so it is one cross-table claim rather than three prints that have to agree.
GENEROUS = {"tm": "MIA", "avg": 14.0, "gp": 55, "elig": ["PG", "SG"]}


def grade(body):
    """A backfill body's rate/GP label, the way every row names one."""
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
    # Jokic priced on SIM_TM like every other incoming body, NOT on DEN. His real
    # schedule is 1.0 sd BELOW the 30-team mean, which charged him ~76 PF of
    # handicap that the ladder then read as body count.
    #
    # The rate rides in the same dict as the rest of his shape: five rungs is
    # five chances for one of them to price a different center.
    JOKIC = dict(rate=65.2, gp=65, elig=("C",), tm=SIM_TM)
    BOTTOM = [p["n"] for p in bottom(full, 3)]
    SC = [
        # Body count held fixed at 1 incoming, GP and position held fixed too,
        # so the ONLY variable down this ladder is how many bodies you pay.
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
        # Same 68 GP as every other row: three separate swaps, not one. Spread
        # over SIM_TMS so neither a schedule nor a stacking effect is booked as
        # body count, which is the one thing this ladder measures.
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
    print("Every incoming body is on %s (multi-body rows spread over %s) -- one"
          % (SIM_TM, "/".join(SIM_TMS)))
    print("schedule, because which NBA team a body sits on is worth up to 3.7")
    print("rate points and is not a fact about the trade.")
    print("BACKFILL ASSUMPTION, stated here rather than in a footnote: outgoing")
    print("bodies 2..N come back at %.0f FPts / %d GP. That is the post-auction"
          % (DEAD["avg"], DEAD["gp"]))
    print("open-FA grade. `breakevens` reports the bracket to a %s refund."
          % grade(GENEROUS))
    # STATED, because `breakevens` ten lines down states it -- "GP and position
    # are STATED because they move the answer several points" -- and a row here
    # labelled bare is the row a reader compares a real 50-rate center against.
    # Every shape read off the bodies actually priced: the exceptions are the
    # rows a label has no room for, so a hand-typed sentence describes them until
    # one of them changes.
    #
    # `n=` on the shape read, because `star`'s default name identifies a body:
    # calling it for its defaults alone burns one and leaves a gap in the run.
    dflt = star(0, n="-")
    multi = sorted({b["gp"] for _, _, adds in SC if len(adds) > 1 for b in adds})
    print("Incoming is a %d-GP %s where the label says nothing else. The Jokic"
          % (dflt["gp"], "/".join(dflt["elig"])))
    print("rows are a %d-GP %s, and the multi-body rows put each body in a"
          % (JOKIC["gp"], "/".join(JOKIC["elig"])))
    print("different slot group, at %s GP."
          % " and ".join("%d" % g for g in multi))
    print("The bottom-up row is not a typed trio: it ships whoever the roster")
    print("prices lowest as loaded -- today %s." % ", ".join(BOTTOM))
    print("`dPF` is season PF against the baseline above, `CV` the WEEKLY "
          "coefficient\nof variation of PF after the swap (the baseline's is on "
          "line 1), `wins` the\ndPF converted at the PF-per-win above.")
    print("%-30s %9s %7s %8s" % ("scenario", "dPF", "CV", "wins"))
    for label, out, adds in SC:
        r = engine.run(swap(full, out, adds), cal=DELTA_W_CAL)
        print("%-30s %+9.0f %6.1f%% %+8.2f"
              % (label, r["pf"] - base["pf"], 100 * r["cv"], wins(r, base)))


def report_breakevens():
    print("break-even incoming rate for an N-for-1, by roster size. GP and")
    print("position are STATED because they move the answer several points:")
    print("compare a real player against the row that matches him.")
    full, ours = basis(), our_roster()
    print("Two counts: padded to %d (the common basis, and ours from Sept '26)"
          % len(full))
    print("and the file as it stands. Every incoming body is on %s." % SIM_TM)
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

    print("\nBACKFILL GRADE. Every row above refunds outgoing bodies 2..N at some")
    print("rate/GP. Honest bracket: %s is post-auction open FA (all 10 fixed"
          % grade(DEAD))
    print("auction+rookie slots already spent); %s is generous -- a body must"
          % grade(GENEROUS))
    # MEASURED off the roster in hand: a typed range describes whoever the file
    # carried the day it was typed, and `our_roster` re-projects on every feed.
    print("be FIELDED at 456 owned, and our own worst KEPT body rates %.1f."
          % min(p["avg"] for p in ours))
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
    # `strict`/`generous`, not `lo`/`hi`: the STRICTER refund is the one that
    # demands the HIGHER incoming rate, so the DEAD column holds the bigger
    # numbers and a `lo`/`hi` pair would name them the wrong way round.
    strict, generous = band[grade(DEAD)], band[grade(GENEROUS)]

    def spread(a, b):
        """The gap between two grades, or `-` where either cell is out of
        bracket: a difference of two bounds is not a rate-point spread.

        On the VALUES, not the printed cells -- recovering a measurement by
        `float()`-ing a column back out of its own %7s formatting makes the
        display width load-bearing arithmetic.
        """
        both = isinstance(a, float) and isinstance(b, float)
        return "%.1f" % (a - b) if both else "-"
    print("  band across the honest bracket: %s rate points at 2..5-for-1."
          % "/".join(spread(a, b) for a, b in zip(strict, generous)))
    print("  Cap-at-3-for-1 survives every grade. A modifier, not a sign flip.")
