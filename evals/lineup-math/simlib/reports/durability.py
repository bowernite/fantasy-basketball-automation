from .. import engine
from ..engine import TRIALS, absence_blocks
from ..roster import EXPANSION, basis, star
from ..value import replacement, value_key
from ..wins import pf_wins


# The one player every row here reshapes. Named once: the GP curve, the lock-in
# column and the replacement reference are all measured on the SAME body, and
# three literals is three chances for one of them to be about somebody else.
SUBJECT = "Jalen Suggs"
# The rate the GP row probes at; `findings.md` quotes it in prose.
PROBE = 48.9
# The GPs that row is measured at, and the surprise rates the lock-in column is
# measured at. One tuple each, for the same reason SUBJECT is one name: a header
# typed apart from its own row is a column labelled at what was not measured.
PROBE_GP = (36, 45, 55, 65)
LOCK_INS = (0.15, 0.30)


def report_durability():
    """Does OUR format penalise a missed game differently from a dynasty board?

    A board prices roughly expected production: any multiplicative model
    (rate x GP, or convex(rate) x GP) has GP-elasticity exactly 1 -- lose 30% of
    your games, lose 30% of your value. Measure ours against that.
    """
    full = basis()
    base = engine.run(full)
    bbase = engine.run(full, bursty=True)["pf"]      # lock-in is a block phenomenon
    R = replacement(full)[0]
    print("%d-man baseline PF %.0f (trials=%d)"
          % (len(full), base["pf"], TRIALS))

    def reshaped(body):
        """`full` with SUBJECT's row replaced by `body`, in place.

        The three rows below reshape the same player, and each typing its own
        comprehension is three chances for one of them to reshape somebody else
        -- the reason SUBJECT is a constant in the first place. In place, so the
        untouched bodies keep their order and their rng draws.
        """
        return [body if p["n"] == SUBJECT else p for p in full]

    def pf(rate, gp):
        return engine.run(reshaped(star(rate, gp)))["pf"]

    # Off the roster in hand, never typed: `our_roster` re-projects both the
    # rate and the GP whenever the feed moves, so a literal line here describes
    # whoever this roster carried the day it was typed while the row below is
    # measured on today's.
    sub, = [p for p in full if p["n"] == SUBJECT]
    print("\nGP is the input we are worst at. What one player's GP is worth,")
    print("1-for-1 for %s (%.1f @ %d), for a %.1f-rate forward:"
          % (SUBJECT, sub["avg"], sub["gp"], PROBE))
    print("  %5s %s" % ("gp", "  ".join("%8d" % g for g in PROBE_GP)))
    print("  %5s %s" % ("wins", "  ".join(
        "%+8.2f" % pf_wins(pf(PROBE, g) - base["pf"])
        for g in PROBE_GP)))

    print("\nfraction of a healthy(82 GP) season retained; a board implies gp/82:")
    print("  %5s %5s %9s %9s %8s" % ("rate", "gp", "board", "ours", "delta"))
    for rate in (26, 45, 60):
        absent, healthy = pf(rate, 0), pf(rate, 82)
        for gp in (41, 55, 70):
            ours = (pf(rate, gp) - absent) / (healthy - absent)
            print("  %5d %5d %9.3f %9.3f %+7.1f%%"
                  % (rate, gp, gp / 82, ours, 100 * (ours / (gp / 82) - 1)))

    print("\nTHE LOCK-IN. Measured on BLOCK absences with the surprise restricted")
    print("to a block's FIRST night, which is the only night it can be one -- from")
    print("night 2 he is on the public injury report and you do not start him.")
    print("`surprise` = share of a player's absence BLOCKS he is started into.")
    ab = absence_blocks(full)
    print("MEASURED on this roster, not quoted: absences arrive as %.0f nights in"
          % ab["nights"])
    print("%.0f blocks of %.2f. Drawing the surprise from every absence NIGHT"
          % (ab["blocks"], ab["mean_block"]))
    print("instead multiplies the penalty by that %.2f." % ab["mean_block"])
    print("  whole %d-man roster:" % len(full))
    for s in (0.10, 0.25, 0.40):
        d = engine.run(full, bursty=True, surprise=s)["pf"] - bbase
        print("    %2d%% surprised: %+6.0f PF = %+.2f wins"
              % (100 * s, d, pf_wins(d)))
    print("  carried by ONE 45-rate player as a share of HIS OWN value (measured")
    print("  1-for-1 against a %.1f-rate body). A board charges gp/82 and stops;" % R)
    print("  this column is what it does not charge:")
    print("    %5s %11s %s" % ("gp", "wins", "  ".join(
        "%14s" % ("lock-in @%d%%" % (100 * s)) for s in LOCK_INS)))

    def one(gp, s):
        return engine.run(reshaped(dict(star(45, gp), surprise=s)),
                          bursty=True)["pf"]
    repl = engine.run(reshaped(star(R, 68)), bursty=True)["pf"]
    worst = []          # the costliest lock-in share at each GP, for the bound
    for gp in (41, 55, 70, 82):
        clean = one(gp, 0.0)
        val = pf_wins(clean - repl)
        cells = [pf_wins(one(gp, s) - clean) for s in LOCK_INS]
        worst.append(max(abs(d) / val for d in cells))
        print("    %5d %+11.2f %s" % (gp, val, "  ".join(
            "%+8.2f %4.0f%%" % (d, 100 * abs(d) / val) for d in cells)))
    # DERIVED off the rows above, never asserted: this bound is what "do not levy
    # a fragility discount" rests on, so a table that moved past it has to say so.
    print("  <=%.1f%% of value at any plausible input, and %s in GP. The shape that"
          % (100 * max(worst), "FLAT" if worst[-1] <= worst[0] else "RISING"))
    print("  costs most is a high-GP veteran resting scattered single games, where")
    print("  every absence IS its own onset. Not a fragility discount; do not levy")
    print("  one. And the slate-wide-lock premise is unverified, which can only")
    print("  make this smaller.")

    print("\ndead-slot cost: at 38 with an empty pool a season-long absence also")
    print("burns a roster spot. Marginal last bodies:")
    for p in EXPANSION[-4:]:
        d = engine.run([q for q in full if q["n"] != p["n"]])["pf"] - base["pf"]
        print("  drop %s (%.0f FPts/%d GP): %+5.0f PF = %+.3f wins"
              % (p["n"], p["avg"], p["gp"], d, pf_wins(d)))

    print("\nfragility at CONSTANT (rate-%.1f)xGP, top 6 / top 12. Weekly sd raw:"
          % R)
    print("  independent absences do not synchronise, so concentrating glass")
    print("  jaws neither helps nor hurts materially.")
    v = value_key(full, R)
    for k in (6, 12):
        names = {p["n"] for p in sorted(full, key=lambda p: -v(p))[:k]}
        for gp in (78, 45):
            r = engine.run(
                [dict(p, gp=gp, avg=R + (p["avg"] - R) * p["gp"] / gp)
                 if p["n"] in names else p for p in full])
            print("  top %-2d all at %d GP: PF %+6.0f  weekly sd %5.0f (base %.0f)"
                  % (k, gp, r["pf"] - base["pf"], r["wk_sd"], base["wk_sd"]))
