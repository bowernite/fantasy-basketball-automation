"""Counterparty eval player-table sim columns. Always priced in our seat."""
import sim
from fetch_data import season_dw_tag
from simlib.bracket import week_points
from simlib.data import BRACKET, PERIODS
from simlib.projections import projected_rate
from simlib.roster import OURS
from simlib.schedule import unsigned
from simlib.value import group_replacement


def _weeks(p):
    if unsigned(p["tm"]) or projected_rate(p["n"]) is None:
        return ["–"] * len(BRACKET)
    pts = week_points(p)
    return ["%.0f" % pts[w] for w in range(len(BRACKET))]


def print_eval_columns(their_path, names=None):
    ours = sim.basis(OURS)
    bodies = sim.our_roster(their_path)
    if names:
        by = {p["n"]: p for p in bodies}
        missing = [n for n in names if n not in by]
        if missing:
            raise KeyError("missing on roster: %s" % ", ".join(missing))
        bodies = [by[n] for n in names]
    their_full = sim.basis(their_path)
    ins = sim.incoming_wins(ours, bodies)
    title = sim.incoming_title(ours, bodies, path=OURS)
    theirs = sim.player_wins(their_full, [p["n"] for p in bodies])
    tag = season_dw_tag()
    w_hdr = "\t".join("W%d" % PERIODS[i]["ordinal"] for i in BRACKET)
    print("player\tΔw\tΔw %s ours\tΔw %s theirs\tΔP(title) ours\t%s"
          % (tag, tag, w_hdr))
    for p in sorted(bodies, key=lambda q: -ins[q["n"]][0]):
        n = p["n"]
        print("%s\t%+.2f\t%+.2f\t%+.2f\t%.1f%%\t%s" % (
            n, sim.formula_player_wins(p), ins[n][0], theirs[n][0],
            title[n][0] * 100, "\t".join(_weeks(p))))
    R_ours = group_replacement(ours)
    R_theirs = group_replacement(their_full)
    print("REPL ours %s; theirs %s" % (
        " ".join("%s %.1f" % (g, R_ours[g]) for g in sorted(R_ours)),
        " ".join("%s %.1f" % (g, R_theirs[g]) for g in sorted(R_theirs))))
