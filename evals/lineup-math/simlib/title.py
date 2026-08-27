"""The whole season, end to end: the regular periods played head to head ->
standings -> seeds -> the bracket with its byes -> a title. Every count comes
off the period data, as everywhere else here (`league-info`).

`bracket` prices a round GIVEN a seed, and every figure it publishes is
conditional on one. This closes the loop: the seed is simulated rather than
assumed, so `P(title)` here is unconditional, every team in the league has one,
and the twelve sum to 1.

WHERE THE NOISE COMES FROM, and it is NOT the engine's own draws. A team's
level in a period is `engine.run`'s mean over 200 seasons; the week-to-week
deviation around it is drawn at `bracket.WITHIN_CV`, which is the same
decomposition `bracket.sigma` prices a bracket round with. Scoring off single
engine seasons instead would run at 0.040 of relative weekly spread against the
wire's 0.1005: availability is the only thing that moves in this engine, and a
matchup is not decided on availability alone. Understated by 2.5x, the favourite
wins nearly every week, the standings barely shuffle and the top seed's title
odds read several times what they are. Pin the seed order here and the same
draws reproduce `seed_title` to Monte Carlo error -- `tests/` holds them
together, and that is what says these are two views of one model rather than
two models.

INJURIES reach it through that level and nowhere else: 200 draws of every
player's projected GP over his own NBA schedule, per regular period and per
bracket round, so a fragile roster is haircut in both. What this does NOT carry
is one injury persisting out of March into the bracket. The engine's own
regular-to-bracket correlation is -0.40 -- a GP budget spent early, not a
durable absence -- so resampling whole engine seasons would import that artifact
in place of the signal it looks like.
"""
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


# One team's season over the whole Monte Carlo. `wins` and `pf` are means; the
# rest are probabilities. `seeds` is indexed from 0, so `seeds[0]` is the top
# seed and everything from `len(BRACKET_TEAMS)` on missed the bracket.
#
# `crowns` is JOINT -- P(title AND seeded there) -- so it sums to `title` and
# needs no guard where a seed never happened. P(title | seed) is the ratio to
# `seeds`, which is the decomposition the report prints and the only place a
# seed's worth is separable from the odds of getting it.
Odds = collections.namedtuple("Odds",
                              "wins pf seeds crowns bands bracket title")


# Seasons per run. The sampling error on a probability is sqrt(p(1-p)/n), so
# this is +-0.3pp at p=0.2 -- inside the width of every other bar on the page
# and about a second of compute.
#
# Every entry point below takes `trials=None` and resolves it HERE, at call
# time, rather than binding it as a default: the report prints the count as the
# caveat on its own error bars, and a default snapshotted at import lets that
# caveat describe a run nobody made.
SEASON_TRIALS = 20000


def _trials(trials):
    return SEASON_TRIALS if trials is None else trials


# The draw every published figure here is on. Distinct from `bracket.SEED0`,
# which seeds ENGINE trials: these are schedule and weekly-shock draws on top of
# an engine result, and two streams sharing a base is a coincidence waiting to
# be read as a check.
SEED0 = 4001


def _pairings():
    """The league's own 19-period pairing skeleton, as team names off last
    season's wire.

    Next season's schedule does not exist in August and its SHAPE is what the
    standings are made of: 6 games a period, every team in exactly one of them,
    every pair meeting at least once and 8 of the 11 twice. `full_season`
    deals the twelve franchises onto these slots afresh every trial, so who
    draws the three single meetings is not last season's answer carried forward
    as though it were next season's.
    """
    out = []
    for i in REGULAR:
        games = tuple((a, h) for a, _, h, _ in PERIODS[i]["games"])
        teams = {t for g in games for t in g}
        assert len(games) == FULL_FIELD and len(teams) == 2 * FULL_FIELD, (
            "period %d pairs %d teams into %d games, not the full field of %d: "
            "a regular period the whole league does not play in is a bracket "
            "period this took for a regular one"
            % (PERIODS[i]["ordinal"], len(teams), len(games), FULL_FIELD))
        out.append(games)
    return tuple(out)


PAIRINGS = _pairings()


def _seats(teams):
    """Schedule slot -> index into `teams`, by way of the wire's team names.

    The skeleton above arrives as names and everything else here is keyed by
    roster file; `teams-<season>.json` is the join, written by the same
    `fetch_data.py roster` run as the files themselves. A name it cannot resolve
    is refused rather than dropped: a team quietly missing from the schedule
    plays no games, finishes 0-19 and hands eleven other teams a seed.
    """
    names = _load("teams-%s.json" % SEASON_TAG)
    by_name = {}
    for k, t in enumerate(teams):
        tid = os.path.basename(t.path).split("-")[1]
        if tid not in names:
            raise KeyError(
                "team %s is not in teams-%s.json, so %s cannot be placed on the"
                " schedule -- re-run `./run fetch_data.py roster` to rewrite "
                "both (`team-info`)" % (tid, SEASON_TAG, t.path))
        by_name[names[tid]] = k
    missing = sorted({n for per in PAIRINGS for g in per for n in g}
                     - set(by_name))
    if missing:
        raise KeyError(
            "%s play in last season's schedule and have no roster file among "
            "the %d loaded: the skeleton cannot be dealt to a short league. "
            "`./run fetch_data.py roster` writes all of them (`team-info`)"
            % (", ".join(missing), len(teams)))
    return tuple(tuple((by_name[a], by_name[h]) for a, h in per)
                 for per in PAIRINGS)


def _play(seeded, scores):
    """The champion's team index. Each half of the draw is climbed worst seed
    first and the two survivors meet in the final (`bracket.LADDERS`), so a
    seed's byes are the rungs below its own entry point and it simply is not in
    those games.

    `seeded[s - 1]` is the team holding seed `s`; `scores[r][k]` is team `k`'s
    score in bracket round `r`.
    """
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
    """Team indices, best seed first: record, then points-for.

    The league's own seeding rule (`league-info`), and the same one
    `bracket._seeded` reads last season's finish with -- NOT
    `recordOverall.rank`, which is the draft's rule and splits ties differently.
    """
    return sorted(range(len(wins)), key=lambda k: (-wins[k], -pf[k]))


def _shock_z(rng, n):
    """Standard normal draws for one period, shared when two rosters differ in
    only one team's level and the same trial must stay paired."""
    return [rng.gauss(0, 1) for _ in range(n)]


def _scores(level, mus, z):
    """One period's scores from pre-drawn `z` and this roster's levels."""
    sd = WITHIN_CV * level
    return [mu + zi * sd for mu, zi in zip(mus, z)]


# What one Monte Carlo run counts. `spread` is per TRIAL, not per team: the sd
# of the twelve win totals inside one simulated season, which is the shape of a
# finished standings table and the one thing here last season's wire can be read
# against directly (`win_spread`).
Tally = collections.namedtuple("Tally", "wins pf seeds crowns spread")


def _levels(teams):
    """Regular and bracket period means for this twelve."""
    return ([statistics.mean(t.regs[p] for t in teams)
             for p in range(len(PAIRINGS))],
            [field_mean(w) for w in range(len(BRACKET))])


def _champ_from_draws(seat, period_z, bracket_z, teams, seats, reg_lvl,
                      brk_lvl, pinned):
    """Who wins the title on one trial's pre-drawn shocks."""
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
    """Seat shuffle and shock draws for one paired trial."""
    seat = list(range(n))
    rng.shuffle(seat)
    period_z = [_shock_z(rng, n) for _ in range(len(PAIRINGS))]
    bracket_z = [_shock_z(rng, n) for _ in range(len(BRACKET))]
    return seat, period_z, bracket_z


def _accumulate_trial(tally, teams, seats, reg_lvl, brk_lvl, pinned, seat,
                      period_z, bracket_z):
    """Book one simulated season into a partial `Tally`."""
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
    """Sum partial counts; spreads concatenate for the mean at the end."""
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
    """Crown counts for one team index on paired after/before rosters."""
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
    """Mean title probability for `at` with and without the roster change, same
    draws within each trial."""
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
    """({roster file: `Odds`}, mean standings spread) over `trials` seasons.

    ONE run, both answers. `full_season` and `win_spread` are views on this
    rather than two calls: they take the same arguments and would run the same
    seasons twice, and the report wants both.

    `teams` defaults to `team_levels()`; `swap_odds` passes a modified tuple
    to price a roster change. The DRAW ORDER does not depend on any team's
    level, so two runs at one `seed0` are paired -- same schedule, same weekly
    luck, same bracket luck -- and the difference is the roster change.

    `pinned` replaces the simulated standings with a seed order given as team
    indices: the bracket alone, with the regular season played and then thrown
    away (`bracket_odds`).
    """
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
    """{roster file: `Odds`} over `trials` simulated seasons."""
    return season_run(teams, trials, seed0, pinned, workers)[0]


def win_spread(teams=None, trials=None, seed0=SEED0, spread=None):
    """(what a simulated standings table spreads, what last season's did) --
    both the sd of one season's twelve win totals.

    THE calibration of this model, and the only one available: the levels come
    off projected rosters and the weekly spread off last season's scores, but
    whether the two together produce a league that finishes as spread out as a
    real one is a separate question, and a table nobody could win 15 games in
    would put every figure above it out by more than its own error bar. Read as
    a bound rather than a fit -- it is one league-season of standings, and a
    team that quit mid-season sits in it.

    `spread` is the second half of a `season_run` a caller has already made;
    without it this runs its own.
    """
    wire = bracket._record(REGULAR)
    if spread is None:
        spread = season_run(teams, trials, seed0)[1]
    return (spread, statistics.stdev([w for w, _ in wire.values()]))


def bracket_odds(order=None, teams=None, trials=None, seed0=SEED0):
    """{roster file: P(title)} with the seed order PINNED -- the bracket alone,
    no seeding uncertainty.

    `order` defaults to the projected field's own order (`team_levels()`,
    sorted on projected season PF), so this is `bracket.seed_title` as a Monte
    Carlo: the same closed form, the same draw, the same sigma. Holding the two
    together is what says the seeded model and the end-to-end one are one model
    (`tests/`), and the gap between this and `full_season` is the whole
    cost of not knowing the seed.
    """
    teams = team_levels() if teams is None else teams
    # SORTED here rather than taken as the tuple's own order. `_pinned` hands
    # its twelve out on projected PF already, so the two coincide there and
    # nothing says they must: `swap_odds` builds a tuple by seat, which keeps
    # a re-measured team where it was and not where its new PF puts it.
    order = (sorted(range(len(teams)), key=lambda k: -teams[k].pf)
             if order is None else order)
    return {p: o.title for p, o in
            full_season(teams, trials, seed0, pinned=order).items()}


def swap_odds(after, before, path=None, trials=None, seed0=SEED0):
    """(`Odds` after, `Odds` before) for ONE joint roster change, both on the
    same draws. ARG ORDER IS THE SIGN, as `wins(deal, base)` -- reversed it
    reads "title probability given up".

    Only the loaded team is re-measured; the other eleven stay
    `team_levels()`'s. The result is unconditional `Delta P(title)` -- seed
    earned, not assumed (`Eval Definitions §ΔP(title)`). `roster_title` is the
    same change as a (mean, sd, per-block) delta.
    """
    who, teams, at = _seat(path)
    out = []
    for r in (after, before):
        swapped = list(teams)
        swapped[at] = measure(r, who)
        out.append(full_season(tuple(swapped), trials, seed0)[who])
    return tuple(out)


# Independent season-blocks behind a per-player `Delta P(title)`. Resolved at
# call time so a report that prints the count is printing the count that ran.
ODDS_BLOCKS = 3


def _blocks(blocks):
    return ODDS_BLOCKS if blocks is None else blocks


def _seat(path):
    """(loaded roster file, the twelve, its index). Refuse a file that is not
    one of the twelve: it has no seed in the draw."""
    who = loaded(path)
    teams = team_levels()
    at = [k for k, t in enumerate(teams) if t.path == who]
    if not at:
        raise KeyError(
            "%s is not among the %d roster files this league was built from, so"
            " there is no seat in the draw to put the deal in -- `./run "
            "fetch_data.py roster` writes them (`team-info`)"
            % (who, len(teams)))
    return who, teams, at[0]


def _delta(after_team, before_team, teams, who, at, trials, seed0, blocks,
           workers=None):
    """(mean, sd, per-block) of after.title - before.title, paired draws."""
    n, n_blocks = _trials(trials), _blocks(blocks)
    per = max(1, n // n_blocks)
    nw = shard.n_workers(workers, per)
    if nw > 1:
        shard.retire()  # `measure` runs `engine.run` on the shared pool first
    xs = []
    for b in range(n_blocks):
        s = seed0 + b * per
        after_p, before_p = _paired_titles(after_team, before_team, teams, at,
                                           per, s, None, workers)
        xs.append(after_p - before_p)
    return block_stats(xs)


# Below this many players, forking costs more than the ~1s of single-core
# work one player already is on its own -- a far lower bar than
# `shard.SHARD_FLOOR`'s, which is calibrated for a unit the size of one
# trial, not a whole measure-and-delta.
PLAYER_SHARD_FLOOR = 4


def _without_job(job):
    """One `player_title` row: `after` is fixed (the roster as given), so
    only `before` -- this name's own replacement -- needs measuring, done
    in-process with `workers` forced to 1 by `_run_jobs` when this runs
    inside a per-player worker."""
    after, before_roster, teams, who, at, trials, seed0, blocks, workers = job
    before = measure(before_roster, who, workers=workers)
    return _delta(after, before, teams, who, at, trials, seed0, blocks,
                 workers)


def _with_job(job):
    """One `incoming_title` row: mirror of `_without_job` -- `before` (the
    slot group's replacement level) is fixed and shared, so only `after`
    needs measuring."""
    after_roster, before, teams, who, at, trials, seed0, blocks, workers = job
    after = measure(after_roster, who, workers=workers)
    return _delta(after, before, teams, who, at, trials, seed0, blocks,
                 workers)


def _run_jobs(fn, jobs, workers):
    """One `fn(job)` per row, sharded ACROSS players rather than across one
    row's own trials. Below `PLAYER_SHARD_FLOOR` this stays in this process
    at whatever `workers` a single row's own trials would use. At or above
    it, `fn` runs in a forked worker, so `workers` collapses to 1 inside it
    -- a worker opening its own pool after the shared one has already served
    a different job shape hangs (`_delta`) -- and the fork itself is where
    this call's parallelism comes from instead.
    """
    nw = shard.n_workers(workers, len(jobs), floor=PLAYER_SHARD_FLOOR)
    inner = 1 if nw > 1 else workers
    if nw > 1:
        shard.retire()
    return shard.mapped(fn, [job + (inner,) for job in jobs], nw)


def player_title(roster, names, blocks=None, trials=None, seed0=SEED0,
                 R=None, path=None, workers=None):
    """name -> (mean `Delta P(title)`, sd across blocks, per-block).

    Same counterfactual as `player_wins`: he leaves, a replacement 68-GP body
    of his own slot group sits in. Seed is simulated, not held (`Eval
    Definitions §ΔP(title)`). ONE NAME AT A TIME -- a multi-piece side is
    `roster_title`.
    """
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
    """name -> (mean `Delta P(title)`, sd, per-block) for acquiring each player
    onto `roster` (typically `basis()`).

    THE `Delta P(title) ours` read -- mirror `incoming_wins` (`Bracket
    value.md`). Same pad slot, same slot-group replacement. Never sum rows;
    multi-piece sides use `roster_title`.
    """
    dupes = collections.Counter(p["n"] for p in players)
    twice = sorted(n for n, c in dupes.items() if c > 1)
    if twice:
        raise ValueError("%s: two bodies of one name -- the column is keyed by "
                         "name, so one row would silently replace the other. "
                         "Rename the row you mean." % ", ".join(twice))
    who, teams, at = _seat(path)
    R = group_replacement(roster) if R is None else R
    pads = [i for i, p in enumerate(roster) if p["n"] in PAD_NAMES]
    if not pads:
        raise ValueError("%d bodies and none of them padded: 'add him and "
                         "re-pad' has no invented slot to spend, and which of "
                         "ours is dropped is a decision, not a default. Pass "
                         "the 37 you would field -- or `basis()`, if this was "
                         "meant to be padded at all." % len(roster))
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
    """(mean `Delta P(title)`, sd across blocks, per-block) for ONE joint
    roster change: `after` against `before`.

    ARG ORDER IS THE SIGN, as `wins(deal, base)`. THE multi-piece path (`Eval
    Definitions §ΔP(title)`: one joint run, never added rows).
    """
    who, teams, at = _seat(path)
    return _delta(measure(after, who), measure(before, who),
                  teams, who, at, trials, seed0, blocks, workers)
