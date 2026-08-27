from .. import engine
from ..engine import TRIALS, absence_blocks
from ..roster import EXPANSION, basis, star
from ..value import replacement, value_key
from ..wins import pf_wins


# named once -- the GP curve, lock-in column and replacement reference all
# measure this SAME body
SUBJECT = "Jalen Suggs"
# quoted in prose in findings.md
PROBE = 48.9
# one tuple each so a header can't drift from the row it labels
PROBE_GP = (36, 45, 55, 65)
LOCK_INS = (0.15, 0.30)


def report_durability():
    full = basis()
    base = engine.run(full)
    bbase = engine.run(full, bursty=True)["pf"]      # lock-in is a block phenomenon
    R = replacement(full)[0]
    print("%d-man baseline PF %.0f (trials=%d)"
          % (len(full), base["pf"], TRIALS))

    def reshaped(body):
        # in place, so untouched bodies keep their index and their rng draws
        return [body if p["n"] == SUBJECT else p for p in full]

    def pf(rate, gp):
        return engine.run(reshaped(star(rate, gp)))["pf"]

    # off the roster in hand, not typed -- `our_roster` re-projects on every feed
    sub, = [p for p in full if p["n"] == SUBJECT]
    print("\nGP swept 1-for-1 for %s (%.1f @ %d), incoming a %.1f-rate forward:"
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

    print("\nTHE LOCK-IN. BLOCK absences, surprise on a block's FIRST night only.")
    ab = absence_blocks(full)
    print("on this roster: %.0f absence nights in %.0f blocks of %.2f."
          % (ab["nights"], ab["blocks"], ab["mean_block"]))
    print("  whole %d-man roster:" % len(full))
    for s in (0.10, 0.25, 0.40):
        d = engine.run(full, bursty=True, surprise=s)["pf"] - bbase
        print("    %2d%% surprised: %+6.0f PF = %+.2f wins"
              % (100 * s, d, pf_wins(d)))
    print("  ONE 45-rate player, as a share of his own value 1-for-1 against a")
    print("  %.1f-rate body:" % R)
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
    # derived, not hardcoded -- this bound is what "do not levy a fragility
    # discount" rests on
    print("  bound: <=%.1f%% of value at any input, %s in GP"
          % (100 * max(worst), "FLAT" if worst[-1] <= worst[0] else "RISING"))

    print("\ndead-slot cost, marginal last bodies:")
    for p in EXPANSION[-4:]:
        d = engine.run([q for q in full if q["n"] != p["n"]])["pf"] - base["pf"]
        print("  drop %s (%.0f FPts/%d GP): %+5.0f PF = %+.3f wins"
              % (p["n"], p["avg"], p["gp"], d, pf_wins(d)))

    print("\nfragility at CONSTANT (rate-%.1f)xGP, top 6 / top 12:" % R)
    v = value_key(full, R)
    for k in (6, 12):
        names = {p["n"] for p in sorted(full, key=lambda p: -v(p))[:k]}
        for gp in (78, 45):
            r = engine.run(
                [dict(p, gp=gp, avg=R + (p["avg"] - R) * p["gp"] / gp)
                 if p["n"] in names else p for p in full])
            print("  top %-2d all at %d GP: PF %+6.0f  weekly sd %5.0f (base %.0f)"
                  % (k, gp, r["pf"] - base["pf"], r["wk_sd"], base["wk_sd"]))
