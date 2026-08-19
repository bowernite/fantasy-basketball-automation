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
from . import bracket
from .bracket import (
    BANDS, BRACKET_TEAMS, LADDERS, WITHIN_CV, field_mean, loaded, measure,
    team_levels)
from .data import BRACKET, FULL_FIELD, PERIODS, REGULAR, _load


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


def _shocks(rng, level, mus):
    """One period's scores: each team's level plus its own weekly deviation.

    The deviation is `WITHIN_CV` of the PERIOD's level, not of the team's own --
    `bracket._spread` measures it against the period mean, which is where the
    calendar's density already sits. Drawn for all twelve whether they play or
    not, so the stream position does not move when the field does and two runs
    at one seed stay paired.
    """
    sd = WITHIN_CV * level
    return [mu + rng.gauss(0, sd) for mu in mus]


# What one Monte Carlo run counts. `spread` is per TRIAL, not per team: the sd
# of the twelve win totals inside one simulated season, which is the shape of a
# finished standings table and the one thing here last season's wire can be read
# against directly (`win_spread`).
Tally = collections.namedtuple("Tally", "wins pf seeds crowns spread")


def _tally(teams, trials, seed0, pinned):
    n = len(teams)
    seats = _seats(teams)
    # The two levels a shock is a share of, and they are drawn from different
    # sets ON PURPOSE. A regular period is played by everybody, so its level is
    # these teams' own mean -- which is what `bracket._spread` normalised by
    # when it measured `WITHIN_CV` in the first place. A bracket round is
    # `field_mean`, the projected top 8, because that is what `bracket.sigma`
    # is: matched to the digit, a pinned run here reproduces `seed_title`, and
    # off any other set it would not.
    reg_lvl = [statistics.mean(t.regs[p] for t in teams)
               for p in range(len(PAIRINGS))]
    brk_lvl = [field_mean(w) for w in range(len(BRACKET))]
    wins, pf = [0] * n, [0.0] * n
    seeds = [[0] * n for _ in range(n)]
    crowns = [[0] * n for _ in range(n)]
    spread = []
    for trial in range(trials):
        rng = random.Random(seed0 + trial)
        seat = list(range(n))
        rng.shuffle(seat)
        w, p = [0] * n, [0.0] * n
        for i, games in enumerate(seats):
            sc = _shocks(rng, reg_lvl[i], [t.regs[i] for t in teams])
            for k, x in enumerate(sc):
                p[k] += x
            for a, h in games:
                x, y = seat[a], seat[h]
                w[x if sc[x] > sc[y] else y] += 1
        order = list(pinned) if pinned is not None else standings(w, p)
        at = [0] * n
        for k in range(n):
            wins[k] += w[k]
            pf[k] += p[k]
            at[order[k]] = k
            seeds[order[k]][k] += 1
        spread.append(statistics.stdev(w))
        champ = _play(order[:len(BRACKET_TEAMS)],
                      [_shocks(rng, brk_lvl[r], [t.mus[r] for t in teams])
                       for r in range(len(BRACKET))])
        crowns[champ][at[champ]] += 1
    return Tally(wins, pf, seeds, crowns, spread)


def season_run(teams=None, trials=None, seed0=SEED0, pinned=None):
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
    t = _tally(teams, trials, seed0, pinned)
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


def full_season(teams=None, trials=None, seed0=SEED0, pinned=None):
    """{roster file: `Odds`} over `trials` simulated seasons."""
    return season_run(teams, trials, seed0, pinned)[0]


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
    `team_levels()`'s, so the field is the same field and the bracket the same
    bracket. The result
    is an UNCONDITIONAL `Delta P(title)`, which is a third quantity beside
    `Delta w` and the seed-banded `Delta P(title)` and is not either of them:
    it carries the seeding channel a regular-season win pays through, which is
    exactly what those two are defined to keep apart (`Bracket value.md`).
    """
    who = loaded(path)
    teams = team_levels()
    at = [k for k, t in enumerate(teams) if t.path == who]
    if not at:
        raise KeyError(
            "%s is not among the %d roster files this league was built from, so"
            " there is no seat in the draw to put the deal in -- `./run "
            "fetch_data.py roster` writes them (`team-info`)"
            % (who, len(teams)))
    out = []
    for r in (after, before):
        swapped = list(teams)
        swapped[at[0]] = measure(r, who)
        out.append(full_season(tuple(swapped), trials, seed0)[who])
    return tuple(out)
