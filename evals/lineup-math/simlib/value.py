"""What a body is worth: replacement level, `Delta w` in both directions, and
the break-even rate an N-for-1 needs."""
import collections, os
from . import engine, shard
from .data import DELTA_W_CAL
from .engine import TRIALS
from .roster import GROUPS, PAD_NAMES, refuse_already_rostered, slot_group, star, swap
from .schedule import SIM_TM
from .stats import block_stats, false_position, slope
from .league_curve import league_pf
from .wins import pf_wins, wins


def value_key(roster, R=None):
    R = replacement(roster)[0] if R is None else R
    return lambda p: (p["avg"] - R) * p["gp"]


def thin(roster, n, R=None):
    """Best `n` bodies by `value_key`, in ORIGINAL order -- order drives the
    per-season rng draw order, so sorting would change what `roster` means"""
    v = value_key(roster, R)
    keep = set(sorted(range(len(roster)), key=lambda i: -v(roster[i]))[:n])
    return [p for i, p in enumerate(roster) if i in keep]


def bottom(roster, n, R=None):
    v = value_key(roster, R)
    return sorted((p for p in roster if p["n"] not in PAD_NAMES), key=v)[:n]


class OutOfBracket(ValueError):
    """`mark` is which end of the bracket the deal fell off ("<20", ">90")"""

    def __init__(self, msg, mark):
        ValueError.__init__(self, msg)
        self.mark = mark


def breakeven_value(*a, **kw):
    try:
        return breakeven(*a, **kw)
    except OutOfBracket as e:
        return e.mark


def breakeven_fmt(v):
    return "%7.1f" % v if isinstance(v, float) else "%7s" % v


def breakeven_cell(*a, **kw):
    return breakeven_fmt(breakeven_value(*a, **kw))


def breakeven(roster, out_names, gp=68, elig=("SF", "PF"), tm=SIM_TM,
              lo=20.0, hi=90.0, tol=0.15, dead=None, base=None):
    base = engine.run(roster)["pf"] if base is None else base

    def d(rate):
        return engine.run(swap(roster, out_names,
                        [star(rate, gp, elig, tm)], dead))["pf"] - base
    dlo = d(lo)
    if dlo >= 0:
        raise OutOfBracket("%s is already PF-neutral below %g"
                           % ("+".join(out_names), lo), "<%g" % lo)
    dhi = d(hi)
    if dhi < 0:
        raise OutOfBracket("%s does not break even by %g"
                           % ("+".join(out_names), hi), ">%g" % hi)
    return false_position(d, lo, hi, dlo, dhi, tol)


def group_fits(roster, gp=68):
    return {g: replacement(roster, gp, e) for g, e in GROUPS.items()}


def group_replacement(roster, gp=68):
    return {g: R for g, (R, _) in group_fits(roster, gp).items()}


def group_body(g, rate, n=None):
    return star(rate, 68, GROUPS[g], SIM_TM, n)


def seed_blocks(blocks, trials, seed0):
    return [seed0 + b * trials for b in range(blocks)]  # spaced so blocks don't overlap


PLAYER_BLOCKS = 3


def _sampling(roster, blocks, trials, seed0, R):
    # shared so both `Delta w` columns are drawn and fitted the same way
    R = group_replacement(roster) if R is None else R
    return seed_blocks(PLAYER_BLOCKS if blocks is None else blocks,
                       trials, seed0), R


JOB_FLOOR = 8


def _run_jobs(specs, workers):
    nw = 1
    if len(specs) >= JOB_FLOOR:
        nw = shard.n_workers(
            workers if workers is not None else (os.cpu_count() or 1), len(specs))
    if nw == 1:
        return [engine.run(r, trials=t, seed0=s, cal=c, workers=workers)
               for r, t, s, c in specs]
    shard.retire()
    chunks = [specs[s:s + c] for s, c in shard.chunks(len(specs), nw)]
    return [r for chunk in shard.mapped(_run_chunk, chunks, nw) for r in chunk]


def _run_chunk(chunk):
    # workers=1: a worker opening its own pool inside one already forked by
    # `_run_jobs` deadlocks on this machine
    return [engine.run(r, trials=t, seed0=s, cal=c, workers=1)
           for r, t, s, c in chunk]


def player_wins(roster, names, blocks=None, trials=TRIALS, seed0=101, R=None,
                workers=None):
    seeds, R = _sampling(roster, blocks, trials, seed0, R)
    by_name = {p["n"]: p for p in roster}
    missing = [n for n in names if n not in by_name]
    if missing:
        raise KeyError("not on this roster: %s" % ", ".join(missing))
    groups = {n: slot_group(by_name[n]["elig"]) for n in names}
    specs = [(roster, trials, s, DELTA_W_CAL) for s in seeds]
    specs += [(swap(roster, [n], [group_body(groups[n], R[groups[n]])]),
              trials, s, DELTA_W_CAL)
             for n in names for s in seeds]
    results = _run_jobs(specs, workers)
    base, rest = results[:len(seeds)], iter(results[len(seeds):])
    out = {}
    for n in names:
        w = [wins(base[i], next(rest)) for i in range(len(seeds))]
        out[n] = block_stats(w)
    return out


def incoming_wins(roster, players, blocks=None, trials=TRIALS, seed0=101, R=None,
                  workers=None):
    """Never sum rows across a multi-piece deal -- price with one joint
    `engine.run(swap(...))`. Takes the LAST padded slot, not an arbitrary
    one."""
    dupes = collections.Counter(p["n"] for p in players)
    twice = sorted(n for n, c in dupes.items() if c > 1)
    if twice:
        raise ValueError("%s: two bodies of one name -- rename the row you "
                         "mean" % ", ".join(twice))
    refuse_already_rostered(roster, players, "incoming_wins")
    seeds, R = _sampling(roster, blocks, trials, seed0, R)
    pads = [i for i, p in enumerate(roster) if p["n"] in PAD_NAMES]
    if not pads:
        raise ValueError("%d bodies and none of them padded -- pass the 37 "
                         "you would field, or `basis()`"  % len(roster))
    room = roster[:pads[-1]] + roster[pads[-1] + 1:]
    groups = []
    for p in players:
        g = slot_group(p["elig"])
        if g not in groups:
            groups.append(g)
    specs = [(room + [group_body(g, R[g], "REPL")], trials, s, DELTA_W_CAL)
             for g in groups for s in seeds]
    specs += [(room + [p], trials, s, DELTA_W_CAL)
             for p in players for s in seeds]
    results = _run_jobs(specs, workers)
    ref = {g: results[i * len(seeds):(i + 1) * len(seeds)]
          for i, g in enumerate(groups)}
    rest = iter(results[len(groups) * len(seeds):])
    out = {}
    for p in players:
        g = slot_group(p["elig"])
        w = [wins(next(rest), ref[g][i]) for i in range(len(seeds))]
        out[p["n"]] = block_stats(w)
    return out


def formula_player_wins(p):
    return pf_wins(league_pf(p["avg"], p["gp"]))


def deal_formula_wins(in_bodies, out_bodies):
    """Per-piece net formula Δw — sum of incoming minus outgoing bodies."""
    ins = sum(formula_player_wins(p) for p in in_bodies)
    outs = sum(formula_player_wins(p) for p in out_bodies)
    return ins - outs


def replacement(roster, gp=68, elig=("SF", "PF"), rates=(30, 40, 50, 65)):
    """R is the x-intercept of a line fit over `rates`, not the rate at which
    a body is worth zero -- value in rate is convex, so this cannot be used
    on sub-25 players."""
    base = engine.run(roster)["pf"]
    v = [engine.run(roster + [star(r, gp, elig, SIM_TM, "ADD")])["pf"] - base
         for r in rates]
    mx, mv, a = slope(rates, v)
    return mx - mv / a, a / gp
