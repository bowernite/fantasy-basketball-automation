from .. import engine, value
from ..engine import TRIALS
from ..gp import evidence_flags
from ..projections import projected_rate
from ..roster import basis, our_roster
from ..schedule import unsigned
from ..stats import se_mean
from ..value import group_replacement
from ..wins import pf_wins


def report_extras():
    full = basis()
    base = engine.run(full)
    d = base["pf"] - engine.run(our_roster())["pf"]
    print("\nSept '26 expansion: %d -> %d bodies (`pad`'s EXPANSION grades)"
          % (len(our_roster()), len(full)))
    print("  %+5.0f PF = %+.2f wins" % (d, pf_wins(d)))


def report_players():
    full = basis()
    R = group_replacement(full)
    ours = our_roster()
    print("wins lost if swapped for a replacement-level 68-GP body OF HIS OWN")
    print("SLOT GROUP, %d-man roster: %s." % (len(full), ", ".join(
        "%s %.1f" % (g, R[g]) for g in sorted(R))))
    print("blocks: %d x %d trials" % (value.PLAYER_BLOCKS, TRIALS))
    print("  %-24s %5s %5s  %-6s %5s  %7s  %5s  %s"
          % ("player", "rate", "gp", "elig", "wins", "sd", "next", "flags"))
    w = value.player_wins(full, [p["n"] for p in ours], R=R)
    order = sorted(ours, key=lambda q: -w[q["n"]][0])
    for i, p in enumerate(order):
        m, sd, blk = w[p["n"]]
        nxt = ""
        if i + 1 < len(order):
            m2, _, blk2 = w[order[i + 1]["n"]]
            # paired -- both rows run on the SAME seed blocks, so the two sds
            # aren't independent
            se = se_mean([a - b for a, b in zip(blk, blk2)])
            nxt = "%5.1f" % ((m - m2) / se) if se else "  inf"
        row_flags = [code for code, on in (("fa", unsigned(p["tm"])),
                                           ("noproj", projected_rate(p["n"]) is None))
                     if on]
        flag = " ".join(evidence_flags(p["n"]) + row_flags)
        print("  %-24s %5.1f %5d  %-6s %+5.2f  +-%.3f  %5s  %s"
              % (p["n"], p["avg"], p["gp"], "/".join(p["elig"]), m, sd, nxt, flag))
