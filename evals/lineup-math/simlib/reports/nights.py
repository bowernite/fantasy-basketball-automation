from .. import engine
from ..data import SCORING_NIGHTS
from ..engine import unfilled_slots
from ..lineups import SLOTS
from ..roster import basis


def report_nights():
    """Where the starting-slot cap actually bites. The deliverable is the SHARES.

    Deliberately no headline "season loss = N PF". That number is just your
    assumed price for an empty slot times a slot count, and there is no defensible
    price: R is a fitted x-intercept, and `replacement()` says in its own docstring
    that it is NOT the rate at which a body is worth zero. Pricing the same slots
    at 10 rather than at 20 halves the headline, so the figure reports the
    assumption. The share columns below are invariant to that price, which is why
    they are the only thing here worth quoting.
    """
    full = basis()
    r = engine.run(full)
    print("fill rate by night size, %d-man roster, %d scored nights."
          % (len(full), len(SCORING_NIGHTS)))
    print("Columns, per night of that size: `nights` how many there are,"
          " `avail` mean\nbodies with an NBA game, `filled/%d` mean starting "
          "slots filled of the %d,\n`slotsLost` the slot-nights that went empty,"
          " `cum` the share of the season's\nWHOLE unfilled-slot count sitting "
          "on nights this small or smaller.\n`cum` is price-free, hence quotable."
          % (len(SLOTS), len(SLOTS)))
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
    print("  %.0f unfilled slot-nights of %d (%.1f%%). Pricing them needs a rate"
          % (tot, slot_nights, 100 * tot / slot_nights))
    print("  an empty slot forgoes; this report refuses to pick one.")
    print("\nWhy a slot goes empty -- no body at all, or bodies with no legal slot:")
    posn = sum((min(len(SLOTS), na) - f) * n
               for na, f, _, n in r["by_night"].values())
    bod = sum(max(0.0, len(SLOTS) - na) * n
              for na, _, _, n in r["by_night"].values())
    print("  slot-nights lost to no legal slot : %5.1f (%.1f%% of all slot-nights)"
          % (posn, 100 * posn / slot_nights))
    print("  slot-nights lost to no body       : %5.1f (%.1f%%)"
          % (bod, 100 * bod / slot_nights))
    print("  ^ both take min(%d,.) of a BUCKET MEAN, so by Jensen the positional"
          % len(SLOTS))
    print("    figure is an UPPER BOUND, not an estimate. It runs with the")
    print("    conclusion that positions rarely bind -- say so when quoting it.")
