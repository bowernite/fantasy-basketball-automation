"""What a body is worth: replacement level, `Delta w` in both directions, and the
break-even rate an N-for-1 needs."""
import collections
from . import engine
from .data import DELTA_W_CAL
from .engine import TRIALS
from .roster import GROUPS, PAD_NAMES, slot_group, star, swap
from .schedule import SIM_TM
from .stats import block_stats, false_position, slope
from .wins import wins


def value_key(roster, R=None):
    """`p -> (rate - R) * gp` on `roster`'s OWN replacement level.

    R is the x-intercept of value in rate, so it moves with the body count by
    construction; deriving it is the only way it cannot go stale.
    """
    R = replacement(roster)[0] if R is None else R
    return lambda p: (p["avg"] - R) * p["gp"]


def thin(roster, n, R=None):
    """Best `n` bodies by `value_key`, IN THE ORIGINAL ORDER.

    Returning them sorted would be a different measurement of the same roster:
    order drives the per-season rng draw order, so `thin(r, len(r))` would not
    reproduce `r`.
    """
    v = value_key(roster, R)
    keep = set(sorted(range(len(roster)), key=lambda i: -v(roster[i]))[:n])
    return [p for i, p in enumerate(roster) if i in keep]


def bottom(roster, n, R=None):
    """The `n` bodies `roster` prices lowest by `value_key`, cheapest first.

    Pads are out. An invented slot (`pad`) is not a body anybody can ship, and
    pads are graded at the bottom of the auction, so they fill the cheapest seats
    on any padded roster and a caller would trade nobody.

    The order is not a ranking: `replacement`'s line goes negative below R while
    the truth does not, so which of the cheapest is worse than which is not a
    claim this makes.
    """
    v = value_key(roster, R)
    return sorted((p for p in roster if p["n"] not in PAD_NAMES), key=v)[:n]


class OutOfBracket(ValueError):
    """`breakeven` refusing to invent an answer, carrying `mark` -- which end of
    its own bracket the deal fell off, as a table cell would print it."""

    def __init__(self, msg, mark):
        ValueError.__init__(self, msg)
        self.mark = mark


def breakeven_value(*a, **kw):
    """`breakeven` as a VALUE: the rate as a float, or the `OutOfBracket` `.mark`
    ("<20", ">90") as a string. Out of bracket is a real answer about that deal,
    so callers that want the number get it without re-deriving it from a formatted
    cell."""
    try:
        return breakeven(*a, **kw)
    except OutOfBracket as e:
        return e.mark


def breakeven_fmt(v):
    """One `breakeven_value` as a table cell, %7s wide."""
    return "%7.1f" % v if isinstance(v, float) else "%7s" % v


def breakeven_cell(*a, **kw):
    """`breakeven_value` as ONE table cell, %7s wide: the rate, or the bracket end
    it fell off. Out of bracket is a real answer about that cell, not a dead
    row."""
    return breakeven_fmt(breakeven_value(*a, **kw))


def breakeven(roster, out_names, gp=68, elig=("SF", "PF"), tm=SIM_TM,
              lo=20.0, hi=90.0, tol=0.15, dead=None, base=None):
    """Incoming rate at which trading `out_names` away is PF-neutral.

    GP and eligibility are ARGUMENTS, not incidentals: the break-even for a
    65-GP center is several points above the one for a 68-GP forward, and a
    reader who compares a real player's rate to the wrong row gets the sign of
    the deal wrong. `dead` is the backfill grade -- see swap().

    `base` is `roster`'s own PF, measured here when omitted so the single-cell
    import path stays one call. A caller pricing SEVERAL cells against one roster
    should measure it once and pass it, or pay for the same run per cell.
    """
    base = engine.run(roster)["pf"] if base is None else base

    def d(rate):
        return engine.run(swap(roster, out_names,
                        [star(rate, gp, elig, tm)], dead))["pf"] - base
    # BRACKET FIRST. A search with no sign check converges on whichever END of
    # its own bracket is nearer and returns it looking measured -- and `lo` sits
    # right in the middle of the rates we trade at, so nothing about the number
    # gives it away. Out of bracket is a real answer -- say it.
    dlo = d(lo)
    if dlo >= 0:
        raise OutOfBracket("%s is already PF-neutral below %g: the deal does not "
                           "need an incoming rate, it needs a body"
                           % ("+".join(out_names), lo), "<%g" % lo)
    dhi = d(hi)
    if dhi < 0:
        raise OutOfBracket("%s does not break even by %g -- no such player "
                           "exists, so the deal is unbuyable at any price"
                           % ("+".join(out_names), hi), ">%g" % hi)
    # `d` meets `false_position`'s convexity precondition: a night's points are
    # the max of a matching over lineups affine in the incoming rate, so `d` is
    # convex in it and piecewise affine -- one piece per start count, and ONE
    # piece all the way to `hi` above the rate at which the body starts every
    # night he is available.
    return false_position(d, lo, hi, dlo, dhi, tol)


def group_fits(roster, gp=68):
    """{group: (R, c)} on `roster` -- the `replacement` fit per slot group.

    R is position-dependent by roughly 2-3 rate points on any real roster
    (`report_replacement` calls that a third of the formula's error), so ONE R is
    a different counterfactual for a center than for a forward. `c` comes back
    with it because the reports price with both, and a second comprehension over
    GROUPS is the same fit measured twice.
    """
    return {g: replacement(roster, gp, e) for g, e in GROUPS.items()}


def group_replacement(roster, gp=68):
    """{group: R} on `roster` -- the R column of `group_fits`."""
    return {g: R for g, (R, _) in group_fits(roster, gp).items()}


def group_body(g, rate, n=None):
    """A replacement 68-GP body of slot group `g` at `rate` -- the counterfactual
    `player_wins`, `incoming_wins` and `report_formula` all price against. One
    helper so the GP, the eligibility and the team cannot drift apart between
    them and make their columns incomparable."""
    return star(rate, 68, GROUPS[g], SIM_TM, n)


def seed_blocks(blocks, trials, seed0):
    """The seed of each independent block, spaced by `trials` so no two blocks
    draw the same numbers -- and identical across rows, because the paired
    differences depend on the blocks being SHARED."""
    return [seed0 + b * trials for b in range(blocks)]


# Independent seed blocks behind every per-player row. +-0.02 on a delta is fine
# for a scenario and far too coarse for an ORDERING -- see `player_wins`.
PLAYER_BLOCKS = 3


def _sampling(roster, blocks, trials, seed0, R):
    """The `(seeds, R)` every per-player column runs on, resolved the one way.

    Shared so they cannot drift: both `Delta w` columns and `bracket`'s
    `Delta P(title)` are read against each other, and a column sampled on
    different seeds or fitted on a different R is not the comparison the reports
    print it as.

    `PLAYER_BLOCKS` is resolved HERE at call time, never bound as a default:
    `players` prints the block count as a caveat on the table, and a default
    snapshotted at import lets that caveat describe a measurement this path did
    not make.
    """
    R = group_replacement(roster) if R is None else R
    return seed_blocks(PLAYER_BLOCKS if blocks is None else blocks,
                       trials, seed0), R


def player_wins(roster, names, blocks=None, trials=TRIALS, seed0=101, R=None):
    """name -> (mean wins lost if swapped for a replacement 68-GP body OF HIS OWN
    SLOT GROUP, sd across `blocks` independent seed blocks, the per-block values).

    Own group, not a forward every time: R runs several rate points apart across
    groups, so pricing a center against a forward's alternative is the single-R
    error `report_replacement` calls a third of the formula's, applied to the
    table the framework actually decides on. `R` is a {group: rate} mapping; it is
    fitted on `roster` if omitted.

    The sd is not decoration. Common random numbers make ONE block's delta stable
    to ~0.02 wins, which is fine for a scenario but not for an ORDERING: the top
    rows here sit ~0.01 wins apart, so a single block picks the winner of the top
    pair essentially at random -- and picking one and publishing "X moved 4th to
    1st" is how a seed became a finding. The per-block values are returned as
    well, because the blocks are SHARED across rows: two rows differ by far less
    than either varies on its own, and only the paired differences see that.
    """
    seeds, R = _sampling(roster, blocks, trials, seed0, R)
    base = [engine.run(roster, trials=trials, seed0=s, cal=DELTA_W_CAL)
            for s in seeds]
    by_name = {p["n"]: p for p in roster}
    # Refused HERE, not left to `swap` inside the loop: the slot-group lookup
    # reads `by_name` first, so a mistyped name dies on a bare KeyError carrying
    # nothing but the name -- and this is the documented import path (`trades`
    # step 5), where the name is typed by hand.
    missing = [n for n in names if n not in by_name]
    if missing:
        raise KeyError("not on this roster: %s" % ", ".join(missing))
    out = {}
    for n in names:
        g = slot_group(by_name[n]["elig"])
        w = [wins(base[i], engine.run(swap(roster, [n], [group_body(g, R[g])]),
                               trials=trials, seed0=s, cal=DELTA_W_CAL))
             for i, s in enumerate(seeds)]
        out[n] = block_stats(w)
    return out


def incoming_wins(roster, players, blocks=None, trials=TRIALS, seed0=101, R=None):
    """name -> (mean wins ADDED to `roster` by acquiring him, sd, per-block).

    THE `Δw ours` column for a counterparty's roster (`Eval Definitions
    §Columns`: "not yet ours -> add him to our roster file, re-run"). Feed it
    `our_roster(their_file)` against `basis()`:

        sim.incoming_wins(sim.basis(), sim.our_roster("roster-160941-...json"))

    `--roster their.json players` is a different column -- that is `Δw theirs`,
    priced on THEIR roster -- and the gap between the two is most of why a deal
    is worth making.

    Exactly `player_wins`' counterfactual, mirrored: a replacement 68-GP body of
    his own slot group, in, out. So the two columns are comparable and their
    signs mean the same thing -- both positive for a player worth having. Never
    SUM these across a multi-piece deal (§Δw): price that with one joint
    `engine.run(swap(...))`.

    He arrives at `roster`'s OWN body count, taking a PADDED slot rather than a
    new one: the roster is capped, `player_wins` prices a departure at 38 and
    `swap` refuses a 39th body outright, so pricing an arrival at 39 compared two
    counts (§Δw). The slot is the LAST pad because `pad` appends, which makes the
    room he joins our real bodies re-padded one shallower -- exactly what "add
    him to our roster file and re-pad to 38" spends, and no body off a roster
    file is touched.

    At 38 real bodies (ours from Sept '26) there is no pad and this REFUSES.
    Somebody we field would have to go, the candidates sit a rate point apart on
    a line `replacement` says does not rank down there, and a column of coin
    flips still prints as measured.
    """
    dupes = collections.Counter(p["n"] for p in players)
    twice = sorted(n for n, c in dupes.items() if c > 1)
    if twice:
        # The rows are keyed by name, so a second body of one name overwrites the
        # first: one plausible number under a name two bodies answer to. A blank
        # would at least read as zero (§Δw); this reads as measured. Refuse, the
        # way `swap` refuses an ambiguous name on the way out.
        raise ValueError("%s: two bodies of one name -- the column is keyed by "
                         "name, so one row would silently replace the other. "
                         "Rename the row you mean." % ", ".join(twice))
    seeds, R = _sampling(roster, blocks, trials, seed0, R)
    # Taken in place rather than filtered out, so every body around it keeps its
    # order and therefore its rng draws.
    pads = [i for i, p in enumerate(roster) if p["n"] in PAD_NAMES]
    if not pads:
        # `swap` refuses the same decision on the way out, in the same words.
        raise ValueError("%d bodies and none of them padded: 'add him and "
                         "re-pad' has no invented slot to spend, and which of "
                         "ours is dropped is a decision, not a default. Pass "
                         "the 37 you would field -- or `basis()`, if this was "
                         "meant to be padded at all." % len(roster))
    room = roster[:pads[-1]] + roster[pads[-1] + 1:]
    ref, out = {}, {}
    for p in players:
        g = slot_group(p["elig"])
        if g not in ref:
            body = group_body(g, R[g], "REPL")
            ref[g] = [engine.run(room + [body], trials=trials, seed0=s,
                                 cal=DELTA_W_CAL) for s in seeds]
        w = [wins(engine.run(room + [p], trials=trials, seed0=s,
                             cal=DELTA_W_CAL), ref[g][i])
             for i, s in enumerate(seeds)]
        out[p["n"]] = block_stats(w)
    return out


def replacement(roster, gp=68, elig=("SF", "PF"), rates=(30, 40, 50, 65)):
    """-> (R, c): value of an added body is ~ c * (rate - R) * gp PF.

    R is the x-INTERCEPT of a line fitted over `rates`. It is not the rate at
    which a body is worth zero -- no such rate exists, because adding a body can
    never LOWER your PF. Value in rate is convex, so this line goes negative below
    R while the truth stays positive: that, not noise, is why the formula cannot
    be used on sub-25 players. Two different `rates` grids give two different
    x-intercepts; quote the one from the grid you fitted.
    """
    base = engine.run(roster)["pf"]
    v = [engine.run(roster + [star(r, gp, elig, SIM_TM, "ADD")])["pf"] - base
         for r in rates]
    mx, mv, a = slope(rates, v)
    return mx - mv / a, a / gp
