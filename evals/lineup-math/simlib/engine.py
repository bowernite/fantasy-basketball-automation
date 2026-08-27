"""The simulator: who is available on a night, what a season scores, and the
Monte Carlo `run` every figure in the study comes out of."""
import collections, random, statistics
from . import shard
from .data import NIGHTS, SCORED_CAL
from .lineups import SLOTS, lineup
from .schedule import games_on, team_nights


# `Night` is one scoring night as `season` books it; `NightAvg` is the same
# averaged over trials, after `size` has been spent as the key `run` groups on.
Night = collections.namedtuple("Night", "size avail filled pf")
NightAvg = collections.namedtuple("NightAvg", "avail filled pf nights")


def _availability(p, rng, bursty):
    idxs = team_nights(p["tm"])
    tg = len(idxs)
    play = min(p["gp"], tg)
    if not bursty:
        return set(rng.sample(idxs, play))
    miss, out = tg - play, set()                        # contiguous IL blocks
    while miss > 0 and len(out) < tg:
        # truncated to >=1: gauss(9, 6) goes negative ~7% of the time and a
        # negative absence block isn't real
        blk = max(1, min(int(rng.gauss(9, 6)), miss))
        # placed circularly so mid-season games aren't likelier to be covered
        # than edge games (`_onsets` assumes the same wraparound)
        s = rng.randrange(0, tg)
        out.update((s + j) % tg for j in range(blk))
        miss = (tg - play) - len(out)
    return {idxs[j] for j in range(tg) if j not in out}


def _onsets(idxs, played):
    """Absence nights that begin a contiguous absence run -- the only nights a
    scratch can surprise you on. Circular, matching `_availability`'s block
    placement"""
    if not played:
        return list(idxs[:1])       # never suits up: opening night is the block
    return [i for j, i in enumerate(idxs)
            if i not in played and idxs[j - 1] in played]


def absence_blocks(roster, seeds=40, seed0=101):
    """Measured off the same `_availability`/`_onsets` pair `season()` uses"""
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


def season(roster, seed, bursty=False, surprise=0.0, cal=SCORED_CAL):
    """Lineups lock before tip, so a late scratch does not free the slot -- a
    started player who is out scores 0 rather than being replaced"""
    rng = random.Random(seed)
    sched = [_availability(p, rng, bursty) for p in roster]
    ghosts = []
    for k, p in enumerate(roster):
        q = p.get("surprise", surprise)     # per-player override
        g = set()
        if q:                              # `durability` alone; skip the scan
            # independent per block, NOT round(q * blocks): most rosters have
            # 2-3 blocks/player, so a deterministic count floors to zero
            g = {i for i in _onsets(team_nights(p["tm"]), sched[k])
                 if rng.random() < q}
        ghosts.append(g)
        sched[k] |= g                      # started, but will score nothing
    eligs = [set(p["elig"]) for p in roster]
    avgs = [p["avg"] for p in roster]
    names = [p["n"] for p in roster]
    weeks = [0.0] * cal.weeks
    starts, pts = collections.Counter(), collections.Counter()
    by_night = []
    for i in cal.nights:
        tms = NIGHTS[i][1]
        # keyed on roster INDEX, never name -- two bodies can share a name
        av = [(avgs[k], eligs[k], k) for k, on in enumerate(sched) if i in on]
        if not av:
            by_night.append(Night(games_on(tms), 0, 0, 0.0))
            continue
        _, filled, who = lineup(av)
        # scored over the <=9 starters: a ghost is ranked on his real rate and
        # only scores nothing, so zeroing happens here and nowhere earlier
        scored = [0.0 if i in ghosts[w] else avgs[w] for w in who]
        total = sum(scored)
        weeks[cal.week_of[i]] += total
        for w, v in zip(who, scored):
            starts[names[w]] += 1
            pts[names[w]] += v
        by_night.append(Night(games_on(tms), len(av), filled, total))
    return weeks, starts, pts, by_night


TRIALS = 200  # deltas stable to +-0.02 wins from ~50 now that swap() shares rng


def run(roster, trials=TRIALS, bursty=False, seed0=101, surprise=0.0,
        cal=SCORED_CAL, workers=None):
    """-> dict(pf, wk_mean, wk_sd, cv, wk, by_night)

    `workers` shards trials across processes (`shard`); chunks come back in
    job order, so the result is digit-for-digit the sequential one."""
    n = shard.n_workers(workers, trials)
    jobs = [TrialJob(roster, seed0, start, count, bursty, surprise, cal)
            for start, count in shard.chunks(trials, n)]
    chunked = shard.mapped(_trial_chunk, jobs, n)
    return _collect([row for chunk in chunked for row in chunk], trials, cal)


TrialJob = collections.namedtuple(
    "TrialJob", "roster seed0 start count bursty surprise cal")


def _trial_chunk(job):
    out = []
    for t in range(job.start, job.start + job.count):
        weeks, _, _, bn = season(job.roster, job.seed0 + t, job.bursty,
                                 job.surprise, job.cal)
        out.append((weeks, bn))
    return out


def _collect(results, trials, cal):
    allweeks = []
    agg = collections.defaultdict(lambda: [0, 0, 0.0, 0])
    for weeks, bn in results:
        allweeks += weeks
        for n in bn:
            a = agg[n.size]
            a[0] += n.avail; a[1] += n.filled; a[2] += n.pf; a[3] += 1
    m, sd = statistics.mean(allweeks), statistics.stdev(allweeks)
    return {
        "pf": m * cal.weeks, "wk_mean": m, "wk_sd": sd, "cv": sd / m,
        "wk": tuple(statistics.mean(allweeks[w::cal.weeks])
                    for w in range(cal.weeks)),
        "by_night": {g: NightAvg(v[0] / v[3], v[1] / v[3], v[2] / v[3],
                                 v[3] / trials)
                     for g, v in agg.items()},
    }


def run_many(rosters, trials=TRIALS, bursty=False, seed0=101, surprise=0.0,
             cal=SCORED_CAL, workers=None):
    """[run(r, ...) for r in rosters], sharded by ROSTER rather than by trial
    -- digit-for-digit against calling `run` on each roster in turn"""
    n = shard.n_workers(workers, len(rosters))
    jobs = [(rosters[s:s + c], trials, bursty, seed0, surprise, cal)
            for s, c in shard.chunks(len(rosters), n)]
    chunked = shard.mapped(_run_many_chunk, jobs, n)
    return [r for chunk in chunked for r in chunk]


def _run_many_chunk(job):
    rosters, trials, bursty, seed0, surprise, cal = job
    return [_collect(_trial_chunk(TrialJob(r, seed0, 0, trials, bursty,
                                          surprise, cal)), trials, cal)
            for r in rosters]


def unfilled_slots(res):
    return {g: (len(SLOTS) - v.filled) * v.nights
            for g, v in res["by_night"].items()}
