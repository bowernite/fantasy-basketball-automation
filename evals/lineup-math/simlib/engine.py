"""The simulator: who is available on a night, what a season scores, and the
Monte Carlo `run` every figure in the study comes out of."""
import collections, random, statistics
from .data import NIGHTS, SCORING_NIGHTS, WEEKS, WEEK_OF
from .lineups import SLOTS, lineup
from .schedule import games_on, team_nights


# One scoring night as `season` books it, and the same night averaged over trials
# as `run` reports it. Separate types because slot 0 is not the same quantity:
# `season` carries the night SIZE, which `run` has already spent as the key it
# groups on. Named rather than positional because `by_night` is read in three
# other modules, where `v[1]` and `v[3]` carry no clue which is which.
Night = collections.namedtuple("Night", "size avail filled pf")
NightAvg = collections.namedtuple("NightAvg", "avail filled pf nights")


def _availability(p, rng, bursty):
    """Night indices this player actually suits up for."""
    idxs = team_nights(p["tm"])
    tg = len(idxs)
    play = min(p["gp"], tg)
    if not bursty:
        return set(rng.sample(idxs, play))
    miss, out = tg - play, set()                        # contiguous IL blocks
    while miss > 0 and len(out) < tg:
        # gauss(9, 6) goes <=0 about 7% of the time and is TRUNCATED to 1 here,
        # so the realised block length is not 9: it is a right-shifted normal
        # with a spike of 1-game blocks. Deliberate -- a 1-night absence is real
        # and a negative one is not -- and it is why `mean_block` is MEASURED off
        # this same draw (`absence_blocks`) rather than quoted as 9.
        blk = max(1, min(int(rng.gauss(9, 6)), miss))
        # place CIRCULARLY. Constraining starts to [0, tg-blk] makes mid-season
        # games ~blk x likelier to be covered than edge games, which inflates
        # October/April availability ~15pts and spuriously synchronises
        # absences across players.
        s = rng.randrange(0, tg)
        out.update((s + j) % tg for j in range(blk))
        miss = (tg - play) - len(out)
    return {idxs[j] for j in range(tg) if j not in out}


def _onsets(idxs, played):
    """Absence nights that BEGIN a contiguous absence run, from `idxs`.

    The only nights a scratch can surprise you on. `idxs` is the player's own
    team-game nights in order; from the second night of a block on he is on the
    public injury report and you simply do not start him. Sampling every absence
    night instead scales the lock-in by the mean block length -- `absence_blocks`
    measures that factor on the roster in hand.

    CIRCULAR, because `_availability` places blocks circularly: a block that wraps
    the end of the season is one block. `idxs[j - 1]` at j=0 is the last night by
    construction. Scanning strictly left-to-right split those in two -- ~26% of
    player-seasons -- and over-counted onsets ~9%.
    """
    if not played:
        # never suits up: one block, and opening night is it. Listed, because
        # `idxs` is a tuple and the other branch is a comprehension
        return list(idxs[:1])
    return [i for j, i in enumerate(idxs)
            if i not in played and idxs[j - 1] in played]


def absence_blocks(roster, seeds=40, seed0=101):
    """-> {nights, blocks, mean_block}: how absences ARRIVE on this roster.

    `mean_block` is the whole of the lock-in correction: drawing the surprise from
    every absence night rather than each block's first night over-states the
    penalty by exactly this factor. It is a property of the roster's projected GP,
    so it has to be measured on the roster in hand -- hard-coding it is how a
    stale triple survived three revisions under a heading naming a roster that
    never produced it. Uses the same `_availability`/`_onsets` pair `season()`
    does, so the factor cannot drift from the model that applies it.
    """
    nights = blocks = 0
    for s in range(seeds):
        rng = random.Random(seed0 + s)
        for p in roster:
            played = _availability(p, rng, True)
            idxs = team_nights(p["tm"])
            nights += len(idxs) - len(played)
            blocks += len(_onsets(idxs, played))
    return {"nights": nights / seeds, "blocks": blocks / seeds,
            "mean_block": nights / blocks if blocks else 0.0}


def season(roster, seed, bursty=False, surprise=0.0):
    """`surprise`: share of a player's absence BLOCKS he is started into.

    Lineups lock before tip, so a late scratch does not free the slot -- you have
    started a player who scores 0 and cannot refill. Everything else here assumes
    perfect foreknowledge of who plays, which is the study's one structural
    over-statement of a fragile player's worth.

    Only meaningful with `bursty=True`: independent per-night absences are their
    own onsets, so the correction is a near no-op against a draw that is not how
    injuries arrive.
    """
    rng = random.Random(seed)
    sched = [_availability(p, rng, bursty) for p in roster]
    ghosts = []
    for k, p in enumerate(roster):
        q = p.get("surprise", surprise)     # per-player override
        g = set()
        if q:                              # `durability` alone; skip the scan
            # Independent per block, NOT round(q * blocks): a typical player has
            # 2-3 absence blocks, so the deterministic count floors to zero and a
            # 10% rate becomes 0% for most of the roster.
            g = {i for i in _onsets(team_nights(p["tm"]), sched[k])
                 if rng.random() < q}
        ghosts.append(g)
        sched[k] |= g                      # started, but will score nothing
    # Read once per roster, not once per player per night: rebuilding the
    # eligibility set on each of the ~131 scoring nights is the largest cost in
    # the loop below after the solver itself.
    eligs = [set(p["elig"]) for p in roster]
    avgs = [p["avg"] for p in roster]
    names = [p["n"] for p in roster]
    weeks = [0.0] * WEEKS
    starts, pts = collections.Counter(), collections.Counter()
    by_night = []
    for i in SCORING_NIGHTS:
        tms = NIGHTS[i][1]
        # Keyed on the ROSTER INDEX, never the name. Two bodies can share a name
        # -- two `star()`s in one deal, or the league's two Jaylin Williamses --
        # and the night has to score both.
        av = [(avgs[k], eligs[k], k) for k, on in enumerate(sched) if i in on]
        if not av:
            by_night.append(Night(games_on(tms), 0, 0, 0.0))
            continue
        _, filled, who = lineup(av)
        # Scored over the <=9 STARTERS, not over everyone available: a ghost is
        # ranked on his real rate (you started him believing he plays) and only
        # scores nothing, so the zeroing belongs here and nowhere earlier.
        #
        # Through `sum`, never a `+=` accumulator: builtin `sum` compensates its
        # float error and a hand-rolled loop does not, so the two disagree in the
        # last ulp on ~38% of nights -- which is enough to move a published Δw in
        # its 13th digit.
        scored = [0.0 if i in ghosts[w] else avgs[w] for w in who]
        total = sum(scored)
        weeks[WEEK_OF[i]] += total
        for w, v in zip(who, scored):
            starts[names[w]] += 1
            pts[names[w]] += v
        by_night.append(Night(games_on(tms), len(av), filled, total))
    return weeks, starts, pts, by_night


# Deltas are stable to +-0.02 wins from ~50 up now that swap() preserves common
# random numbers.
TRIALS = 200


def run(roster, trials=TRIALS, bursty=False, seed0=101, surprise=0.0):
    """-> dict(pf, wk_mean, wk_sd, cv, by_night)

    Per-player figures come off `season`, which returns `starts` and `pts` for a
    single season.
    """
    allweeks = []
    agg = collections.defaultdict(lambda: [0, 0, 0.0, 0])
    for t in range(trials):
        w, _, _, bn = season(roster, seed0 + t, bursty, surprise)
        allweeks += w
        for n in bn:
            a = agg[n.size]
            a[0] += n.avail; a[1] += n.filled; a[2] += n.pf; a[3] += 1
    m, sd = statistics.mean(allweeks), statistics.stdev(allweeks)
    return {
        "pf": m * WEEKS, "wk_mean": m, "wk_sd": sd, "cv": sd / m,
        "by_night": {g: NightAvg(v[0] / v[3], v[1] / v[3], v[2] / v[3],
                                 v[3] / trials)
                     for g, v in agg.items()},
    }


def unfilled_slots(res):
    """{night size: starting slot-nights left empty} off a `run` result.

    THE quantity both `nights` and `schedules` argue from -- the first to say
    where empty slots sit, the second to say that light nights are where they
    sit -- so the two cannot drift apart on how an empty slot is counted.
    """
    return {g: (len(SLOTS) - v.filled) * v.nights
            for g, v in res["by_night"].items()}
