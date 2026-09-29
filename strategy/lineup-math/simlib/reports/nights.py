from .. import engine
from ..data import SCORING_NIGHTS
from ..engine import unfilled_slots
from ..lineups import SLOTS
from ..roster import basis


def report_nights():
    full = basis()
    r = engine.run(full)
    print("fill rate by night size, %d-man roster, %d scored nights."
          % (len(full), len(SCORING_NIGHTS)))
    print("  %5s %7s %8s %9s %10s %6s" %
          ("games", "nights", "avail", "filled/%d" % len(SLOTS), "slotsLost",
           "cum"))
    lost = unfilled_slots(r)
    tot, cum = sum(lost.values()), 0.0
    for g in sorted(r["by_night"]):
        na, f, _, n = r["by_night"][g]
        cum += lost[g]
        print("  %5d %7.1f %8.1f %9.2f %10.1f %5.0f%%"
              % (g, n, na, f, lost[g], 100 * cum / tot))
    slot_nights = len(SLOTS) * len(SCORING_NIGHTS)
    print("  %.0f unfilled slot-nights of %d (%.1f%%)."
          % (tot, slot_nights, 100 * tot / slot_nights))
    posn = sum((min(len(SLOTS), na) - f) * n
               for na, f, _, n in r["by_night"].values())
    bod = sum(max(0.0, len(SLOTS) - na) * n
              for na, _, _, n in r["by_night"].values())
    print("\n  slot-nights lost to no legal slot : %5.1f (%.1f%%)  upper bound"
          % (posn, 100 * posn / slot_nights))
    print("  slot-nights lost to no body       : %5.1f (%.1f%%)"
          % (bod, 100 * bod / slot_nights))
