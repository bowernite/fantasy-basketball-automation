"""The whole season end to end: regular periods -> standings -> seeds -> the
bracket -> a title, unconditional (the seed is simulated, not fixed)."""
import collections, os, random, statistics

from fetch_data import SEASON_TAG
from . import bracket, shard
from .bracket import (
    BANDS, BRACKET_TEAMS, LADDERS, WITHIN_CV, field_mean, loaded, measure,
    team_levels)
from .data import BRACKET, FULL_FIELD, PERIODS, REGULAR, _load
from .roster import PAD_NAMES, slot_group, swap
from .stats import block_stats
from .value import group_body, group_replacement


Odds = collections.namedtuple("Odds",
                              "wins pf seeds crowns bands bracket title")


SEASON_TRIALS = 20000


def _trials(trials):
    return SEASON_TRIALS if trials is None else trials


SEED0 = 4001  # distinct from bracket.SEED0 (that one seeds engine trials)


def _pairings():
    out = []
    for i in REGULAR:
        games = tuple((a, h) for a, _, h, _ in PERIODS[i]["games"])
        teams = {t for g in games for t in g}
        assert len(games) == FULL_FIELD and len(teams) == 2 * FULL_FIELD, (
            "period %d pairs %d teams into %d games, not the full field of %d"
            % (PERIODS[i]["ordinal"], len(teams), len(games), FULL_FIELD))
        out.append(games)
    return tuple(out)


PAIRINGS = _pairings()


def _seats(teams):
    names = _load("teams-%s.json" % SEASON_TAG)
    by_name = {}
    for k, t in enumerate(teams):
        tid = os.path.basename(t.path).split("-")[1]
        if tid not in names:
            raise KeyError("team %s is not in teams-%s.json -- re-run `./run "
                           "fetch_data.py roster` to rewrite both"
                           % (tid, SEASON_TAG))
        by_name[names[tid]] = k
    missing = sorted({n for per in PAIRINGS for g in per for n in g}
                     - set(by_name))
    if missing:
        raise KeyError("%s play in the schedule with no roster "
                       "file among the %d loaded -- `./run fetch_data.py "
                       "roster` writes all of them"
                       % (", ".join(missing), len(teams)))
    return tuple(tuple((by_name[a], by_name[h]) for a, h in per)
                 for per in PAIRINGS)


def _play(seeded, scores):
    finalists = []
    for ladder in LADDERS:
        cur = seeded[ladder[0] - 1]
        for r, s in enumerate(ladder[1:]):
            nxt = seeded[s - 1]
            cur = cur if scores[r][cur] > scores[r][nxt] else nxt
        finalists.append(cur)
    a, b = finalists
    last = scores[len(BRACKET) - 1]
    return a if last[a] > last[b] else b


def standings(wins, pf):
    # the league's own tie-break -- NOT recordOverall.rank (the draft's rule)
    return sorted(range(len(wins)), key=lambda k: (-wins[k], -pf[k]))


def _shock_z(rng, n):
    return [rng.gauss(0, 1) for _ in range(n)]


def _scores(level, mus, z):
    sd = WITHIN_CV * level
    return [mu + zi * sd for mu, zi in zip(mus, z)]


Tally = collections.namedtuple("Tally", "wins pf seeds crowns spread")


def _levels(teams):
    return ([statistics.mean(t.regs[p] for t in teams)
             for p in range(len(PAIRINGS))],
            [field_mean(w) for w in range(len(BRACKET))])


def _champ_from_draws(seat, period_z, bracket_z, teams, seats, reg_lvl,
                      brk_lvl, pinned):
    n = len(teams)
    w, p = [0] * n, [0.0] * n
    for i, games in enumerate(seats):
        sc = _scores(reg_lvl[i], [t.regs[i] for t in teams], period_z[i])
        for k, x in enumerate(sc):
            p[k] += x
        for a, h in games:
            x, y = seat[a], seat[h]
            w[x if sc[x] > sc[y] else y] += 1
    order = list(pinned) if pinned is not None else standings(w, p)
    return _play(order[:len(BRACKET_TEAMS)],
                 [_scores(brk_lvl[r], [t.mus[r] for t in teams], bracket_z[r])
                  for r in range(len(BRACKET))])


def _trial_draws(rng, n):
    seat = list(range(n))
    period_z = [_shock_z(rng, n) for _ in range(len(PAIRINGS))]
    bracket_z = [_shock_z(rng, n) for _ in range(len(BRACKET))]
    return seat, period_z, bracket_z


def _accumulate_trial(tally, teams, seats, reg_lvl, brk_lvl, pinned, seat,
                      period_z, bracket_z):
    n = len(teams)
    w, p = [0] * n, [0.0] * n
    for i, games in enumerate(seats):
        sc = _scores(reg_lvl[i], [t.regs[i] for t in teams], period_z[i])
        for k, x in enumerate(sc):
            p[k] += x
        for a, h in games:
            x, y = seat[a], seat[h]
            w[x if sc[x] > sc[y] else y] += 1
    order = list(pinned) if pinned is not None else standings(w, p)
    at = [0] * n
    wins, pf, seeds, crowns, spread = tally
    for k in range(n):
        wins[k] += w[k]
        pf[k] += p[k]
        at[order[k]] = k
        seeds[order[k]][k] += 1
    spread.append(statistics.stdev(w))
    champ = _play(order[:len(BRACKET_TEAMS)],
                  [_scores(brk_lvl[r], [t.mus[r] for t in teams], bracket_z[r])
                   for r in range(len(BRACKET))])
    crowns[champ][at[champ]] += 1


def _empty_tally(n):
    return ([0] * n, [0.0] * n, [[0] * n for _ in range(n)],
            [[0] * n for _ in range(n)], [])


def _merge_tallies(parts):
    n = len(parts[0].wins)
    wins = [sum(p.wins[k] for p in parts) for k in range(n)]
    pf = [sum(p.pf[k] for p in parts) for k in range(n)]
    seeds = [[sum(p.seeds[i][j] for p in parts) for j in range(n)]
             for i in range(n)]
    crowns = [[sum(p.crowns[i][j] for p in parts) for j in range(n)]
              for i in range(n)]
    spread = [s for p in parts for s in p.spread]
    return Tally(wins, pf, seeds, crowns, spread)


def _tally_chunk(job):
    start, count, seed0, teams, pinned, seats, reg_lvl, brk_lvl = job
    n = len(teams)
    parts = _empty_tally(n)
    for trial in range(start, start + count):
        rng = random.Random(seed0 + trial)
        seat, period_z, bracket_z = _trial_draws(rng, n)
        _accumulate_trial(parts, teams, seats, reg_lvl, brk_lvl, pinned, seat,
                          period_z, bracket_z)
    return Tally(*parts)


def _tally(teams, trials, seed0, pinned, workers=None):
    n = len(teams)
    seats = _seats(teams)
    reg_lvl, brk_lvl = _levels(teams)
    nw = shard.n_workers(workers, trials)
    if nw == 1:
        return _tally_chunk((0, trials, seed0, teams, pinned, seats, reg_lvl,
                             brk_lvl))
    jobs = [(start, count, seed0, teams, pinned, seats, reg_lvl, brk_lvl)
            for start, count in shard.chunks(trials, nw)]
    return _merge_tallies(shard.mapped(_tally_chunk, jobs, nw))


def _paired_chunk(job):
    start, count, seed0, teams, after, before, at, pinned, seats = job
    teams_a = list(teams)
    teams_a[at] = after
    teams_b = list(teams)
    teams_b[at] = before
    ta, tb = tuple(teams_a), tuple(teams_b)
    reg_a, brk_a = _levels(ta)
    reg_b, brk_b = _levels(tb)
    ca = cb = 0
    for trial in range(start, start + count):
        rng = random.Random(seed0 + trial)
        seat, period_z, bracket_z = _trial_draws(rng, n=len(teams))
        if _champ_from_draws(seat, period_z, bracket_z, ta, seats, reg_a, brk_a,
                             pinned) == at:
            ca += 1
        if _champ_from_draws(seat, period_z, bracket_z, tb, seats, reg_b, brk_b,
                             pinned) == at:
            cb += 1
    return ca, cb


def _paired_titles(after_team, before_team, teams, at, trials, seed0, pinned,
                   workers=None):
    seats = _seats(teams)
    nw = shard.n_workers(workers, trials)
    if nw == 1:
        ca, cb = _paired_chunk((0, trials, seed0, teams, after_team, before_team,
                                at, pinned, seats))
    else:
        jobs = [(start, count, seed0, teams, after_team, before_team, at, pinned,
                 seats)
                for start, count in shard.chunks(trials, nw)]
        parts = shard.mapped(_paired_chunk, jobs, nw)
        ca, cb = sum(p[0] for p in parts), sum(p[1] for p in parts)
    return ca / trials, cb / trials


def season_run(teams=None, trials=None, seed0=SEED0, pinned=None, workers=None):
    """`pinned`: seed order fixed as given team indices -- the bracket alone,
    no seeding uncertainty"""
    teams = team_levels() if teams is None else teams
    trials = _trials(trials)
    t = _tally(teams, trials, seed0, pinned, workers)
    out = {}
    for k, team in enumerate(teams):
        share = tuple(c / trials for c in t.seeds[k])
        crowns = tuple(c / trials for c in t.crowns[k])
        out[team.path] = Odds(
            wins=t.wins[k] / trials, pf=t.pf[k] / trials, seeds=share,
            crowns=crowns,
            bands={b.label: sum(share[s - 1] for s in b.slots) for b in BANDS},
            bracket=sum(share[:len(BRACKET_TEAMS)]), title=sum(crowns))
    return out, statistics.mean(t.spread)


def full_season(teams=None, trials=None, seed0=SEED0, pinned=None,
                workers=None):
    return season_run(teams, trials, seed0, pinned, workers)[0]


def win_spread(teams=None, trials=None, seed0=SEED0, spread=None):
    wire = bracket._record(REGULAR)
    if spread is None:
        spread = season_run(teams, trials, seed0)[1]
    return (spread, statistics.stdev([w for w, _ in wire.values()]))


def bracket_odds(order=None, teams=None, trials=None, seed0=SEED0):
    teams = team_levels() if teams is None else teams
    # sorted here rather than the tuple's own order, since `swap_odds` builds
    # a tuple by seat rather than by projected PF
    order = (sorted(range(len(teams)), key=lambda k: -teams[k].pf)
             if order is None else order)
    return {p: o.title for p, o in
            full_season(teams, trials, seed0, pinned=order).items()}


def swap_odds(after, before, path=None, trials=None, seed0=SEED0):
    """ARG ORDER IS THE SIGN, as `wins(deal, base)`"""
    who, teams, at = _seat(path)
    out = []
    for r in (after, before):
        swapped = list(teams)
        swapped[at] = measure(r, who)
        out.append(full_season(tuple(swapped), trials, seed0)[who])
    return tuple(out)


def deal_field(after_us, after_them, their_path):
    who_us, teams, at_us = _seat(None)
    who_them, _, at_them = _seat(their_path)
    swapped = list(teams)
    swapped[at_us] = measure(after_us, who_us)
    swapped[at_them] = measure(after_them, who_them)
    return tuple(swapped), who_us, who_them


def deal_odds(after_us, after_them, their_path, trials=None, seed0=SEED0,
              before=None):
    field, who_us, who_them = deal_field(after_us, after_them, their_path)
    if before is None:
        before = full_season(trials=trials, seed0=seed0)
    after = full_season(field, trials, seed0)
    return after[who_us], before[who_us], after[who_them], before[who_them]


ODDS_BLOCKS = 3


def _blocks(blocks):
    return ODDS_BLOCKS if blocks is None else blocks


def _seat(path):
    who = loaded(path)
    teams = team_levels()
    at = [k for k, t in enumerate(teams) if t.path == who]
    if not at:
        raise KeyError("%s is not among the %d roster files this league was "
                       "built from -- `./run fetch_data.py roster` writes "
                       "them" % (who, len(teams)))
    return who, teams, at[0]


def _delta(after_team, before_team, teams, who, at, trials, seed0, blocks,
           workers=None):
    n, n_blocks = _trials(trials), _blocks(blocks)
    per = max(1, n // n_blocks)
    nw = shard.n_workers(workers, per)
    if nw > 1:
        shard.retire()  # `measure` already ran engine.run on the shared pool
    xs = []
    for b in range(n_blocks):
        s = seed0 + b * per
        after_p, before_p = _paired_titles(after_team, before_team, teams, at,
                                           per, s, None, workers)
        xs.append(after_p - before_p)
    return block_stats(xs)


PLAYER_SHARD_FLOOR = 4


def _without_job(job):
    after, before_roster, teams, who, at, trials, seed0, blocks, workers = job
    before = measure(before_roster, who, workers=workers)
    return _delta(after, before, teams, who, at, trials, seed0, blocks,
                 workers)


def _with_job(job):
    after_roster, before, teams, who, at, trials, seed0, blocks, workers = job
    after = measure(after_roster, who, workers=workers)
    return _delta(after, before, teams, who, at, trials, seed0, blocks,
                 workers)


def _run_jobs(fn, jobs, workers):
    # at or above PLAYER_SHARD_FLOOR, `fn` runs in a forked worker with
    # `workers` forced to 1 -- opening a second pool after the shared one
    # served a different job shape hangs
    nw = shard.n_workers(workers, len(jobs), floor=PLAYER_SHARD_FLOOR)
    inner = 1 if nw > 1 else workers
    if nw > 1:
        shard.retire()
    return shard.mapped(fn, [job + (inner,) for job in jobs], nw)


def player_title(roster, names, blocks=None, trials=None, seed0=SEED0,
                 R=None, path=None, workers=None):
    """ONE NAME AT A TIME -- a multi-piece side is `roster_title`"""
    who, teams, at = _seat(path)
    R = group_replacement(roster) if R is None else R
    with_team = measure(roster, who)
    by_name = {p["n"]: p for p in roster}
    missing = [n for n in names if n not in by_name]
    if missing:
        raise KeyError("not on this roster: %s" % ", ".join(missing))
    jobs = []
    for n in names:
        g = slot_group(by_name[n]["elig"])
        without = swap(roster, [n], [group_body(g, R[g])])
        jobs.append((with_team, without, teams, who, at, trials, seed0,
                    blocks))
    return dict(zip(names, _run_jobs(_without_job, jobs, workers)))


def incoming_title(roster, players, blocks=None, trials=None, seed0=SEED0,
                   R=None, path=None, workers=None):
    """Never sum rows -- multi-piece sides use `roster_title`"""
    dupes = collections.Counter(p["n"] for p in players)
    twice = sorted(n for n, c in dupes.items() if c > 1)
    if twice:
        raise ValueError("%s: two bodies of one name -- rename the row you "
                         "mean" % ", ".join(twice))
    who, teams, at = _seat(path)
    R = group_replacement(roster) if R is None else R
    pads = [i for i, p in enumerate(roster) if p["n"] in PAD_NAMES]
    if not pads:
        raise ValueError("%d bodies and none of them padded -- pass the 37 "
                         "you would field, or `basis()`" % len(roster))
    room = roster[:pads[-1]] + roster[pads[-1] + 1:]
    groups = {slot_group(p["elig"]) for p in players}
    ref = {g: measure(room + [group_body(g, R[g], "REPL")], who)
           for g in groups}
    jobs = [(room + [p], ref[slot_group(p["elig"])], teams, who, at, trials,
             seed0, blocks)
            for p in players]
    return dict(zip((p["n"] for p in players),
                    _run_jobs(_with_job, jobs, workers)))


def roster_title(after, before, blocks=None, trials=None, seed0=SEED0,
                 path=None, workers=None):
    """ARG ORDER IS THE SIGN, as `wins(deal, base)`"""
    who, teams, at = _seat(path)
    return _delta(measure(after, who), measure(before, who),
                  teams, who, at, trials, seed0, blocks, workers)
