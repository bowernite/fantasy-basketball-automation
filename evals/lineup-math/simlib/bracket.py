"""The bracket: seeds and rounds, the opponent level a round is played against,
and `Delta P(title)` per player. `Eval Definitions §ΔP(title)` owns the
definition and the currency rule; this module is the derivation."""
import collections, contextlib, functools, glob, math, os, statistics
from fetch_data import SEASON_TAG
from . import engine, roster as roster_mod
from .data import (
    BRACKET, BRACKET_CAL, HERE, PERIODS, REGULAR, SCORED, SCORES)
from .engine import TRIALS
from .roster import basis, slot_group, swap
from .schedule import bracket_games, team_nights
from .stats import block_stats, cdf, phi
from .value import _sampling, group_body, seed_blocks


# A seed band: its label, the SEED NUMBERS it covers, the teams that finished
# on them last season, and the bracket periods a team entering there has to win.
# `slots` is what the model runs on -- `seeds` names last season's finishers and
# is there so the band can be audited against the wire.
Band = collections.namedtuple("Band", "label slots seeds periods")


# One league team on the study's own basis: the roster file it was measured
# from, its projected season PF, its `mu` in one REGULAR period, and its `mu` in
# each bracket round.
Team = collections.namedtuple("Team", "path pf reg mus")


def _record(i):
    """{team: (wins, PF)} over the periods `i` indexes."""
    w, pf = collections.Counter(), collections.Counter()
    for p in (PERIODS[k] for k in i):
        for away, away_pf, home, home_pf in p["games"]:
            pf[away] += away_pf
            pf[home] += home_pf
            if away_pf > home_pf:
                w[away] += 1
            elif home_pf > away_pf:
                w[home] += 1
    return {t: (w[t], pf[t]) for t in pf}


def _seeded():
    """Every league team, best seed first: record, then points-for -- the
    league's own tie-break (`league-info`)."""
    rec = _record(REGULAR)
    return sorted(rec, key=lambda t: (-rec[t][0], -rec[t][1]))


def _bands():
    """Seed bands, each carrying the bracket periods it must win for the title.

    Sized off `BRACKET`'s own round count and R1's field (`league-info`
    §Matchup periods), never a literal. R1's field is the entering size for
    seeds 5-8; every other round but the final byes one pair beside its two
    survivors, so a band's size is 2 for every round but the last, which takes
    R1's field. A band's `periods` run from its entry round to the final, and
    `title_prob` is a product over them.
    """
    rounds = len(BRACKET)
    assert rounds >= 2, (
        "%d bracket round(s) in league-%s: a final and a bye is the smallest "
        "bracket this can band" % (rounds, PERIODS[BRACKET[0]]["ordinal"]))
    sizes = [2] * (rounds - 2) + [2 * len(PERIODS[BRACKET[0]]["games"])]
    # Two seeds enter every round but R1 and the final, which forces R1's own
    # field at four: two of them meet the pair entering the round above, and
    # that pair meets the next. The wire is the CHECK on it rather than the
    # source -- a period 20 carrying a consolation half beside the bracket
    # reads here as a wider entering band, and the size assert below passes on
    # it.
    assert sizes[-1] == 4, (
        "%d teams in period %d, where a ladder of %d rounds entered two at a "
        "time takes 4: the period is carrying games beside the bracket -- a "
        "consolation half is how it happens"
        % (sizes[-1], PERIODS[BRACKET[0]]["ordinal"], rounds))
    order, out, seed = _seeded(), [], 0
    for k, n in enumerate(sizes):     # k=0 is the latest-entering band
        band = order[seed:seed + n]
        assert len(band) == n, (
            "%d seeds for a %d-team band: the bracket does not fit the league"
            % (len(band), n))
        out.append(Band("%d-%d" % (seed + 1, seed + n),
                        tuple(range(seed + 1, seed + n + 1)), tuple(band),
                        tuple(BRACKET[rounds - 2 - k:])))
        seed += n
    return tuple(out)


BANDS = _bands()


BRACKET_TEAMS = tuple(t for band in BANDS for t in band.seeds)


def _ladders():
    """The draw, as two seed ladders climbed worst seed first.

    Seeds go into halves on the standard snake -- 1 and 4, 5 and 8 one side; 2
    and 3, 6 and 7 the other -- and each half is then one ladder: the two worst
    seeds meet in R1, the winner meets the next seed up, and so on until the
    half's best seed, whose survivor plays the other half's in the final. That
    puts a seed's entry round at its position in its own ladder, which is what
    `_bands` derived independently and what the assert below holds them to.

    STRUCTURE, not an average: a 1-seed's penultimate opponent comes out of {4,
    5, 8} and can never be the 2 or the 3. `test_sim.py` walks every game of
    last season's bracket through this.
    """
    half = ([], [])
    for s in range(1, len(BRACKET_TEAMS) + 1):
        half[(s // 2) % 2].append(s)
    out = tuple(tuple(sorted(h, reverse=True)) for h in half)
    entry = {s: BRACKET.index(b.periods[0]) for b in BANDS for s in b.slots}
    assert all(entry[s] == max(0, k - 1)
               for l in out for k, s in enumerate(l)), (
        "the snake draw %s does not enter its seeds where the bands do (%s): "
        "one of the two is not this league's bracket" % (out, entry))
    return out


LADDERS = _ladders()


def week_points(p):
    """`W20`-`W23` for one body: his rate times his NBA team's games in each
    bracket period, times the share of the season he is projected available for
    (`Eval Definitions §Columns`).

    The share is `season`'s own -- `min(gp, team games)` over that team's games
    -- so this column and the `mu_us` behind `Delta P(title)` haircut a body by
    the same figure. Capped because a projected GP above his team's game count
    is a body who plays every night, not one worth more than his rate.
    """
    tg = len(team_nights(p["tm"]))
    share = min(p["gp"], tg) / tg
    return tuple(p["avg"] * g * share for g in bracket_games(p["tm"]))


def _spread(teams):
    """(within-team weekly cv, between-team level cv) over `teams` and the
    REGULAR periods.

    Each score is divided by its own period's mean PF across `teams`, so the
    period's own density drops out and what is left splits in two: a team's
    LEVEL, and its week-to-week deviation from that level. The one quantity
    here still taken off last season's wire, and SCALE-FREE by construction, so
    it carries onto this study's basis without carrying that season's level
    with it.

    Both steps that isolate the deviation also shrink it, and the two are
    corrected together: dividing by the mean of the same T teams leaves the
    period's T deviations summing to zero, which costs a factor `1 - 1/T`, and
    each team's deviations are taken from its own measured level rather than
    its true one, which costs a degree of freedom per team against the `T*n -
    1` `stdev` divides by. Uncorrected the estimate lands ~9% low and every
    `sigma` below carries it -- `test_sim.py` holds the recombined split to the
    pair margins it was taken from, which is the check that sees it.

    A team's measured level is a mean of `len(REGULAR)` weeks and so carries
    `within^2 / len(REGULAR)` of its own weekly noise; subtracted, because what
    the level term has to price is the spread of the levels themselves.
    """
    rel = {t: [SCORES[t][PERIODS[i]["ordinal"]]
               / statistics.mean(SCORES[u][PERIODS[i]["ordinal"]] for u in teams)
               for i in REGULAR]
           for t in teams}
    level = {t: statistics.mean(v) for t, v in rel.items()}
    within = statistics.stdev([x - level[t] for t, v in rel.items() for x in v])
    n = len(REGULAR)
    within *= math.sqrt((len(teams) * n - 1.0) / ((len(teams) - 1) * (n - 1)))
    return within, math.sqrt(max(0.0, statistics.variance(level.values())
                                 - within ** 2 / len(REGULAR)))


WITHIN_CV, LEVEL_CV = _spread(BRACKET_TEAMS)


# The level spread of the WHOLE league, which is the field a regular-season
# opponent is drawn from (`reg_mean`). The bracket's seeds are the top of that
# league by construction, so their own spread is a truncated sample of it and
# roughly half as wide.
FIELD_LEVEL_CV = _spread(tuple(sorted(SCORES)))[1]


# A margin between two teams whose weekly LEVELS the model already prices --
# every bracket round, where `opp_dist` names the opponent and `mus` carries
# both sides. Only the two sides' own week-to-week deviation is left in it.
MARGIN_CV = math.sqrt(2) * WITHIN_CV


# A margin against an opponent DRAWN from the field rather than named -- one
# regular-season matchup, priced against `reg_mean`. That side's level is
# unknown, so the field's own level spread rides in the margin as well.
FIELD_MARGIN_CV = math.sqrt(2 * WITHIN_CV ** 2 + FIELD_LEVEL_CV ** 2)


# One SEASON's roster files. `fetch_data.py roster` never deletes the season it
# is replacing, so a season-blind glob reads the roll as a second league: 24
# teams, one franchise seated twice in the draw, and a short field is the only
# shape anything below guards against.
ROSTERS = "roster-*-%s.json" % SEASON_TAG


def ladder_games():
    """(title-ladder margins, every other score in the bracket periods) off
    last season's wire.

    A ladder game is a seed pairing neither side has already lost out of, which
    is `len(BRACKET_TEAMS) - 1` games under single elimination. "Both sides
    seeded" is not that filter: R1's losers drop into the consolation ladder in
    the same periods and third place is played after both sides are out, so a
    draw pairing two eliminated seeds reads as a title game.
    """
    seeds, beaten, played, aside = set(BRACKET_TEAMS), set(), [], []
    for i in BRACKET:
        for away, away_pf, home, home_pf in PERIODS[i]["games"]:
            if {away, home} <= seeds and not {away, home} & beaten:
                played.append(away_pf - home_pf)
                beaten.add(home if away_pf > home_pf else away)
            else:
                aside += [away_pf, home_pf]
    return played, aside


def reg_week(wk):
    """Mean PF over the REGULAR periods, off a `SCORED`-basis weekly list.

    The two bases overlap at R1, which is inside `SCORED` and is also the
    bracket's first round -- and it scores well above a regular week. Averaged
    over `SCORED`, a "regular period" carries it; the games and the per-PF
    denominator beside it are counted over `REGULAR`, so the row would be three
    quantities on two bases.
    """
    keep = set(REGULAR)
    return statistics.mean(x for i, x in zip(SCORED, wk) if i in keep)


# The Monte Carlo draw every published figure here is on, and the one
# `bracket_weeks` and `player_title` seed from.
SEED0 = 101


@functools.lru_cache(maxsize=1)
def _pinned():
    """Every team in the league on ONE basis -- its own roster file, projected
    rates, padded to 38, this engine -- best projected season PF first.

    THE reason `mu_us` and `mu_opp` are comparable: `opp_mean` below is these
    same numbers, so our week and an opponent's differ by roster quality and by
    nothing else. An opponent level taken off last season's scores instead
    differs by the body count, the projections and the sim as well, and all
    three land in `P(round)` as an edge nobody has.

    One file per team (`team-info`); 12 sims, so it is computed once per
    process. A team whose file is missing is simply not in the league here --
    re-cut it with `fetch_data.py roster <id>`.
    """
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, ROSTERS))):
        r = basis(path)
        res = engine.run(r)
        out.append(Team(os.path.basename(path), res["pf"], reg_week(res["wk"]),
                        bracket_weeks(r)))
    return tuple(sorted(out, key=lambda t: -t.pf))


# The re-draw `draw` is inside, or None for the pinned one.
_DRAWN = None


def league():
    """The twelve teams every figure here is measured against."""
    return _pinned() if _DRAWN is None else _DRAWN


# `league` is the name every caller holds, so the cache control belongs on it.
league.cache_clear = _pinned.cache_clear


@contextlib.contextmanager
def draw(seed0):
    """Every team's bracket `mus` re-drawn on `seed0`, ours and the field's
    together -- one Monte Carlo draw of the whole basis.

    `sigma`, `field_mean` and every `opp_mean` are the field's own weeks, so
    inside this block a round is priced against the draw it is scored on and
    what is left in the spread is sampling error rather than a mismatch. THE
    error bar on `P(title)`, `by seed` and the multiplier, which are single
    unpaired figures no differencing cancels anything out of.

    The seeding ORDER does not move with it: `pf` and `reg` stay `_pinned`'s.
    Which 8 teams seed, and in what order, is a projection whose own error bar
    `method.md` states separately -- rolled in here it would be counted twice.
    """
    global _DRAWN
    was = _DRAWN
    _DRAWN = tuple(
        t._replace(mus=bracket_weeks(basis(os.path.join(HERE, t.path)),
                                     seed0=seed0))
        for t in _pinned())
    try:
        yield
    finally:
        _DRAWN = was


def field():
    """The projected bracket field: the league on projected season PF, cut at
    the bracket's own size.

    Which teams actually seed next season is not knowable in August, so the
    league's own seeding rule (PF, `league-info`) is run forward on the same
    basis as everything else rather than last season's finish being reused.
    """
    teams = league()
    assert len(teams) >= len(BRACKET_TEAMS), (
        "%d roster files beside sim.py for a %d-team bracket: a short field is "
        "a lower opponent level, not a smaller league. `./run fetch_data.py "
        "roster` writes all of them (`team-info`)"
        % (len(teams), len(BRACKET_TEAMS)))
    return teams[:len(BRACKET_TEAMS)]


def loaded(path=None):
    """Whose roster is being priced: `path`, or the file `roster` has loaded --
    ours, or a counterparty's under `--roster`.

    THE argument every function below threads. `basis(path)` reads a file
    without moving that global, so an import-path caller who has one has to
    hand it over: left to the global, a counterparty is priced against a
    bracket holding a clone of himself and never meets the seed he cannot
    avoid, and nothing about the number says so.
    """
    return os.path.basename(path or roster_mod.ROSTER)


def opponents(path=None):
    """The seeds the loaded roster could meet: `field()` less itself. Left in,
    a team is measured against a bar that includes it."""
    return tuple(t for t in field() if t.path != loaded(path))


def _draw(seed, path=None):
    """Seed number -> the `Team` holding it when the loaded roster takes `seed`
    (which holds `None`): `opponents()`, best projected first, into the rest.

    Seeding by projected PF is `field()`'s own rule run one step further. A
    roster outside the projected field displaces the weakest seed rather than
    enlarging the bracket.
    """
    rest = list(opponents(path))[:len(BRACKET_TEAMS) - 1]
    return {s: None if s == seed else rest.pop(0)
            for s in range(1, len(BRACKET_TEAMS) + 1)}


def _climb(teams, rounds, sd=None):
    """{`Team`: P(it is the one left standing)} after `rounds` rounds of a
    ladder: `teams[0]` v `teams[1]` in round 0, that winner v `teams[r+1]` in
    round `r`."""
    dist = {teams[0]: 1.0}
    for r in range(rounds):
        chal, out = teams[r + 1], collections.Counter()
        for t, p in dist.items():
            q = cdf((t.mus[r] - chal.mus[r]) / (sigma(r) if sd is None else sd))
            out[t] += p * q
            out[chal] += p * (1 - q)
        dist = out
    return dist


def opp_dist(seed, w, sd=None, path=None):
    """{`Team`: P(it is the round-`w` opponent)} for the loaded roster seeded
    `seed` -- the survivor distribution, not the field.

    The opponent reaches round `w` through a part of the draw the loaded roster
    is not in, so its survival cannot depend on the loaded roster's own results
    and the distribution enumerates in one pass: no fixed point.
    """
    ladder, other = ((LADDERS[0], LADDERS[1]) if seed in LADDERS[0]
                     else (LADDERS[1], LADDERS[0]))
    k, slots = ladder.index(seed), _draw(seed, path)
    if w < max(0, k - 1):
        raise ValueError("seed %d does not play bracket round %d -- it enters "
                         "in round %d" % (seed, w, max(0, k - 1)))
    if w == len(BRACKET) - 1:
        return _climb([slots[s] for s in other], len(other) - 1, sd)
    if k <= 1 and w == 0:                 # the two that open this ladder
        return {slots[ladder[1 - k]]: 1.0}
    if w == k - 1:                        # the survivor of the rungs below
        return _climb([slots[s] for s in ladder[:k]], k - 1, sd)
    return {slots[ladder[w + 1]]: 1.0}    # the seed climbing in this round


def opp_mean(w, seed=None, path=None):
    """Mean opponent `mu` in bracket round `w`, out of the same sim `mu_us`
    comes out of.

    With `seed`, the survivor distribution a roster seeded there actually
    faces. Without, the projected field's own mean for the week -- the level
    `sigma` is a share of, and no round's opponent.
    """
    if seed is None:
        return statistics.mean(t.mus[w] for t in opponents(path))
    return sum(p * t.mus[w] for t, p in opp_dist(seed, w, path=path).items())


def reg_mean(path=None):
    """`mu_opp` for one REGULAR matchup: the rest of the league's projected PF
    per regular period. All 11, not the 8 seeds -- the regular season is played
    against everybody."""
    return statistics.mean(t.reg for t in league() if t.path != loaded(path))


def field_mean(w):
    """What the projected field scores in bracket round `w` -- the level the
    round is played at, over the whole field and so the same whoever is loaded.
    No round's opponent: `opp_dist` is."""
    return statistics.mean(t.mus[w] for t in field())


def sigma(w):
    """`sigma_w` for bracket round `w`: `MARGIN_CV * field_mean(w)`. Both sides
    of a bracket margin are named, so it carries their weekly spread only.

    A property of the ROUND, not of the roster loaded -- every game in the draw
    is priced with it, including the ones deciding who the opponent is, and a
    sigma that moved with the loaded team would make the eight seeds' title
    probabilities eight different brackets.
    """
    return MARGIN_CV * field_mean(w)


def round_pwin(mu_us, w, seed, sd=None, path=None):
    """P(win bracket round `w`) scoring `mu_us` from `seed`: `Phi((mu_us -
    opponent) / sigma(w))`, mixed over `opp_dist`."""
    s = sigma(w) if sd is None else sd
    return sum(p * cdf((mu_us - t.mus[w]) / s)
               for t, p in opp_dist(seed, w, sd, path).items())


def _entry(seed):
    """The bracket round `seed` enters -- its rung on its own ladder."""
    ladder = LADDERS[0] if seed in LADDERS[0] else LADDERS[1]
    return max(0, ladder.index(seed) - 1)


def seed_title(mus, seed, sd=None, path=None):
    """P(title) scoring `mus` from `seed`: the product of `round_pwin` over
    every round that seed plays, each conditional on the one before."""
    out = 1.0
    for w in range(_entry(seed), len(BRACKET)):
        out *= round_pwin(mus[w], w, seed, sd, path)
    return out


def bracket_weeks(roster, trials=TRIALS, seed0=SEED0):
    """`mu_us` per bracket round: `engine.run` restricted to each round's own
    nights, one mean per round."""
    return engine.run(roster, trials=trials, seed0=seed0, cal=BRACKET_CAL)["wk"]


def title_prob(mus, band, sd=None, path=None):
    """P(title | seeded somewhere in `band`): `seed_title` averaged over the
    band's own seeds.

    A band names a seed RANGE, and the draw splits it: 6 and 7 sit on the
    2-seed's side and 5 and 8 on the 1-seed's, so the four rounds they each
    have to win are four different rounds. The band figure is the mean over the
    range; `seed_title` is the one seed.
    """
    return statistics.mean(seed_title(mus, s, sd, path) for s in band.slots)


def title_slope(mus, band, w, path=None):
    """d `title_prob(mus, band)` / d `mus[w]` -- what one more PF in round `w`
    is worth to the whole title, in the same average over the band's seeds."""
    out = []
    for seed in band.slots:
        rest = 1.0
        for v in range(_entry(seed), len(BRACKET)):
            if v != w:
                rest *= round_pwin(mus[v], v, seed, path=path)
        out.append(rest * sum(p * phi((mus[w] - t.mus[w]) / sigma(w)) / sigma(w)
                              for t, p in opp_dist(seed, w, path=path).items()))
    return statistics.mean(out)


# Independent seed blocks behind a `Delta P(title)` row -- more than
# `PLAYER_BLOCKS`, because every band figure is published with an error bar of
# its own and 2 dof does not measure one: the sd then carries about half itself
# as error, and a band gap inside that still prints as measured. A block is one
# bracket run per player, so this is what the report costs.
TITLE_BLOCKS = 8


def _bands_delta(after, before, path):
    """{band label: (mean `Delta P(title)`, sd across blocks, per-block)} for
    two block-matched runs of the same roster change."""
    return {b.label: block_stats([title_prob(a, b, path=path)
                                  - title_prob(w, b, path=path)
                                  for a, w in zip(after, before)])
            for b in BANDS}


def player_title(roster, names, blocks=None, trials=TRIALS, seed0=SEED0,
                 R=None, path=None):
    """name -> {band label: (mean `Delta P(title)`, sd across blocks,
    per-block)}. Counterfactual and seeding as `value.player_wins`, priced in
    `title_prob` under every `BANDS` entry (`Eval Definitions §ΔP(title)`).

    `path` is whose roster this is (`loaded`) -- pass it whenever `roster` came
    from `basis(path)`. ONE NAME AT A TIME, and never added up: a multi-piece
    side is one joint run, which is `roster_title` (§ΔP(title)).

    Blocks are `TITLE_BLOCKS`, read at call time so the count a report prints
    as its caveat is the count that ran.
    """
    seeds, R = _sampling(roster, TITLE_BLOCKS if blocks is None else blocks,
                         trials, seed0, R)
    base = [bracket_weeks(roster, trials=trials, seed0=s) for s in seeds]
    by_name = {p["n"]: p for p in roster}
    missing = [n for n in names if n not in by_name]
    if missing:
        raise KeyError("not on this roster: %s" % ", ".join(missing))
    out = {}
    for n in names:
        g = slot_group(by_name[n]["elig"])
        without = [bracket_weeks(swap(roster, [n], [group_body(g, R[g])]),
                                 trials=trials, seed0=s)
                   for s in seeds]
        out[n] = _bands_delta(base, without, path)
    return out


def roster_title(after, before, blocks=None, trials=TRIALS, seed0=SEED0,
                 path=None):
    """{band label: (mean `Delta P(title)`, sd across blocks, per-block)} for
    ONE joint roster change: `after` against `before`, both whole rosters.

    ARG ORDER IS THE SIGN, as `wins(deal, base)` -- reversed it reads "title
    probability given up". THE multi-piece path (`Eval Definitions §ΔP(title)`:
    one joint run, never added rows). `player_title` prices each body against
    its own replacement, so two of its rows describe a roster holding two
    replacements, which is neither side of the deal.

    Same blocks as `player_title`, so a joint figure is read against the
    per-player column on one set of draws.
    """
    seeds = seed_blocks(TITLE_BLOCKS if blocks is None else blocks, trials,
                        seed0)
    return _bands_delta(
        [bracket_weeks(after, trials=trials, seed0=s) for s in seeds],
        [bracket_weeks(before, trials=trials, seed0=s) for s in seeds], path)
