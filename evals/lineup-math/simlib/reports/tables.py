from .. import engine, value
from ..engine import TRIALS
from ..gp import FRAGMENT_GP, ROTATION_RATE, evidence_flags
from ..projections import projected_rate
from ..roster import basis, our_roster
from ..schedule import SIM_TM, unsigned
from ..stats import se_mean
from ..value import group_replacement
from ..wins import PF_PER_WIN


def report_extras():
    full = basis()
    base = engine.run(full)
    d = base["pf"] - engine.run(our_roster())["pf"]
    print("\nSept '26 expansion: filling %d -> %d with auction-grade bodies"
          % (len(our_roster()), len(full)))
    print("  %+5.0f PF = %+.2f wins, free" % (d, d / PF_PER_WIN))


def report_players():
    """Per-player win value. STATE THE COUNTERFACTUAL: this is 'swapped for a
    replacement-level 68-GP forward', not 'if he vanished and the slot went
    empty'. Those differ by the whole value of the replacement."""
    full = basis()
    R = group_replacement(full)
    ours = our_roster()
    print("wins lost if swapped for a replacement-level 68-GP body OF HIS OWN")
    print("SLOT GROUP, %d-man roster: %s." % (len(full), ", ".join(
        "%s %.1f" % (g, R[g]) for g in sorted(R))))
    print("Own group, not one forward for everybody: R runs %.1f rate points"
          % (max(R.values()) - min(R.values())))
    print("apart between groups here, which is a different counterfactual, not a")
    print("rounding difference (`Eval Definitions §Δw`: state it).")
    print("R is fitted on THIS roster, so a short input file gives a low R and")
    print("inflates every row -- check the body count before quoting these.")
    print("Averaged over %d independent %d-trial seed blocks, with the sd across"
          % (value.PLAYER_BLOCKS, TRIALS))
    print("them. `next` is the gap to the row below in sigma, computed from the")
    print("PAIRED per-block differences: the blocks are shared, so two rows move")
    print("together and differencing them first is worth up to 3x either way.")
    print("Below ~2 sigma the two rows are not ordered. QUOTE NO ORDER THERE, and")
    print("note %d blocks is %d dof -- sigma itself is coarse."
          % (value.PLAYER_BLOCKS, value.PLAYER_BLOCKS - 1))
    w = value.player_wins(full, [p["n"] for p in ours], R=R)
    order = sorted(ours, key=lambda q: -w[q["n"]][0])
    for i, p in enumerate(order):
        m, sd, blk = w[p["n"]]
        nxt = ""
        if i + 1 < len(order):
            m2, _, blk2 = w[order[i + 1]["n"]]
            # PAIRED. Both rows run on the SAME seed blocks, so the gap is a
            # within-block quantity and the two sds are not independent.
            se = se_mean([a - b for a, b in zip(blk, blk2)])
            nxt = "%5.1f" % ((m - m2) / se) if se else "   inf"
        row_flags = [code for code, on in (("fa", unsigned(p["tm"])),
                                           ("noproj", projected_rate(p["n"]) is None))
                     if on]
        flag = " ".join(evidence_flags(p["n"]) + row_flags)
        print("  %-24s %5.1f rate %3d gp  %-6s %+.2f  +-%.3f  %5s  %s"
              % (p["n"], p["avg"], p["gp"], "/".join(p["elig"]), m, sd, nxt, flag))
    print("\nThe rate above is PROJECTED (`projections`); `gp` is projected off the")
    print("pool. The flag column is what the GP projection rests on (`Eval")
    print("Definitions §Output`): `frag` a <=%d game season, `miss` a whole season"
          % FRAGMENT_GP)
    print("gone from the pool, `rotN` fewer than 3 seasons at rate >= %g, `nopool`"
          % ROTATION_RATE)
    print("no pool history at all. `fa` unsigned in the NBA, so his `Delta w` is")
    print("priced on %s's schedule rather than his own; `noproj` no projection, so"
          % SIM_TM)
    print("the rate above is LAST SEASON's average, not a projected one.")
