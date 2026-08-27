"""Bracket seeds and rounds: the opponent level a round is played against,
and P(title|seed) -- what a round is worth given a seed."""
import collections, contextlib, functools, glob, math, os, statistics
from fetch_data import SEASON_TAG
from . import engine, roster as roster_mod
from .data import (
    BRACKET, BRACKET_CAL, PERIODS, REGULAR, ROSTER_DIR, SCORED, SCORES)
from .engine import TRIALS
from .roster import PAD_NAMES, basis, slot_group, swap
from .schedule import bracket_games, team_nights
from .stats import block_stats, cdf, phi
from .value import _sampling, group_body, seed_blocks


Band = collections.namedtuple("Band", "label slots seeds periods")


Team = collections.namedtuple("Team", "path pf regs mus")


def _record(i):
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
    rec = _record(REGULAR)
    return sorted(rec, key=lambda t: (-rec[t][0], -rec[t][1]))


def _bands():
    """Sizes derived off BRACKET's own round count and R1's field -- never
    hardcode, the bracket shape isn't fixed"""
    rounds = len(BRACKET)
    assert rounds >= 2, (
        "%d bracket round(s) in league-%s: a final and a bye is the smallest "
        "bracket this can band" % (rounds, PERIODS[BRACKET[0]]["ordinal"]))
    sizes = [2] * (rounds - 2) + [2 * len(PERIODS[BRACKET[0]]["games"])]
    assert sizes[-1] == 4, (
        "%d teams in period %d -- expected 4 entering a %d-round ladder two "
        "at a time; a consolation half sharing the period is one way this "
        "happens" % (sizes[-1], PERIODS[BRACKET[0]]["ordinal"], rounds))
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
    """Two seed ladders, climbed worst seed first. STRUCTURE, not an
    average -- a 1-seed's penultimate opponent is fixed by this."""
    half = ([], [])
    for s in range(1, len(BRACKET_TEAMS) + 1):
        half[(s // 2) % 2].append(s)
    out = tuple(tuple(sorted(h, reverse=True)) for h in half)
    entry = {s: BRACKET.index(b.periods[0]) for b in BANDS for s in b.slots}
    assert all(entry[s] == max(0, k - 1)
               for l in out for k, s in enumerate(l)), (
        "the snake draw %s does not enter its seeds where the bands do (%s)"
        % (out, entry))
    return out


LADDERS = _ladders()


def week_points(p):
    tg = len(team_nights(p["tm"]))
    share = min(p["gp"], tg) / tg
    return tuple(p["avg"] * g * share for g in bracket_games(p["tm"]))


def _spread(teams):
    """(within-team weekly cv, between-team level cv). Both isolating steps
    shrink the deviation they measure (fewer degrees of freedom than a naive
    `stdev` assumes), so `within` is corrected back up before it's subtracted
    out of `level`'s own variance"""
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


FIELD_LEVEL_CV = _spread(tuple(sorted(SCORES)))[1]  # whole league, not just the bracket 8


MARGIN_CV = math.sqrt(2) * WITHIN_CV  # margin cv between two NAMED teams


FIELD_MARGIN_CV = math.sqrt(2 * WITHIN_CV ** 2 + FIELD_LEVEL_CV ** 2)  # vs a drawn opponent


ROSTERS = "roster-*-%s.json" % SEASON_TAG  # season-scoped: old files aren't deleted


def ladder_games():
    """A ladder game is a seed pairing where neither side has already lost --
    NOT simply "both sides seeded": eliminated teams keep playing a
    consolation ladder in the same periods"""
    seeds, beaten, played, aside = set(BRACKET_TEAMS), set(), [], []
    for i in BRACKET:
        for away, away_pf, home, home_pf in PERIODS[i]["games"]:
            if {away, home} <= seeds and not {away, home} & beaten:
                played.append(away_pf - home_pf)
                beaten.add(home if away_pf > home_pf else away)
            else:
                aside += [away_pf, home_pf]
    return played, aside


def reg_weeks(wk):
    keep = set(REGULAR)
    return tuple(x for i, x in zip(SCORED, wk) if i in keep)


def reg_week(wk):
    # averaged over SCORED (R1 included) but counted over REGULAR, since R1
    # is both a scored period and the bracket's first round
    return statistics.mean(reg_weeks(wk))


SEED0 = 101


@functools.lru_cache(maxsize=1)
def _pinned():
    """Every team on ONE basis (own file, projected rates, padded, this
    engine) -- why `mu_us` and `mu_opp` are comparable"""
    out = [measure(basis(path), os.path.basename(path))
           for path in sorted(glob.glob(os.path.join(ROSTER_DIR, ROSTERS)))]
    return tuple(sorted(out, key=lambda t: -t.pf))


def measure(roster, path, workers=None):
    # workers=1 from inside a per-player worker -- opening a second pool
    # after the shared one served a different job shape hangs
    res = engine.run(roster, workers=workers)
    return Team(path, res["pf"], reg_weeks(res["wk"]),
               bracket_weeks(roster, workers=workers))


_DRAWN = None


def team_levels():
    return _pinned() if _DRAWN is None else _DRAWN


team_levels.cache_clear = _pinned.cache_clear


@contextlib.contextmanager
def draw(seed0):
    # seed order does NOT move with the re-draw -- pf/regs stay _pinned's,
    # since seeding uncertainty is a separate error bar from this one
    global _DRAWN
    was = _DRAWN
    _DRAWN = tuple(
        t._replace(mus=bracket_weeks(basis(os.path.join(ROSTER_DIR, t.path)),
                                     seed0=seed0))
        for t in _pinned())
    try:
        yield
    finally:
        _DRAWN = was


def field():
    teams = team_levels()
    assert len(teams) >= len(BRACKET_TEAMS), (
        "%d roster files in rosters/ for a %d-team bracket -- `./run "
        "fetch_data.py roster` writes all of them"
        % (len(teams), len(BRACKET_TEAMS)))
    return teams[:len(BRACKET_TEAMS)]


def loaded(path=None):
    # basis(path) doesn't move this global, so an import-path caller with a
    # `path` must pass it here too
    return os.path.basename(path or roster_mod.ROSTER)


def opponents(path=None):
    return tuple(t for t in field() if t.path != loaded(path))


def _draw(seed, path=None):
    rest = list(opponents(path))[:len(BRACKET_TEAMS) - 1]
    return {s: None if s == seed else rest.pop(0)
            for s in range(1, len(BRACKET_TEAMS) + 1)}


def _climb(teams, rounds, sd=None):
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
    # the opponent reaches round `w` through the OTHER half of the draw, so
    # this enumerates in one pass -- no fixed point on the loaded roster
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
    if seed is None:
        return statistics.mean(t.mus[w] for t in opponents(path))
    return sum(p * t.mus[w] for t, p in opp_dist(seed, w, path=path).items())


def reg_mean(path=None):
    return statistics.mean(statistics.mean(t.regs) for t in team_levels()
                           if t.path != loaded(path))


def field_mean(w):
    return statistics.mean(t.mus[w] for t in field())


def sigma(w):
    # a property of the ROUND, not the roster loaded -- every game in the
    # draw, including the ones deciding the opponent, is priced with it
    return MARGIN_CV * field_mean(w)


def round_pwin(mu_us, w, seed, sd=None, path=None):
    s = sigma(w) if sd is None else sd
    return sum(p * cdf((mu_us - t.mus[w]) / s)
               for t, p in opp_dist(seed, w, sd, path).items())


def _entry(seed):
    ladder = LADDERS[0] if seed in LADDERS[0] else LADDERS[1]
    return max(0, ladder.index(seed) - 1)


def seed_title(mus, seed, sd=None, path=None):
    out = 1.0
    for w in range(_entry(seed), len(BRACKET)):
        out *= round_pwin(mus[w], w, seed, sd, path)
    return out


def bracket_weeks(roster, trials=TRIALS, seed0=SEED0, workers=None):
    return engine.run(roster, trials=trials, seed0=seed0, cal=BRACKET_CAL,
                      workers=workers)["wk"]


def title_prob(mus, band, sd=None, path=None):
    return statistics.mean(seed_title(mus, s, sd, path) for s in band.slots)


def title_slope(mus, band, w, path=None):
    out = []
    for seed in band.slots:
        rest = 1.0
        for v in range(_entry(seed), len(BRACKET)):
            if v != w:
                rest *= round_pwin(mus[v], v, seed, path=path)
        out.append(rest * sum(p * phi((mus[w] - t.mus[w]) / sigma(w)) / sigma(w)
                              for t, p in opp_dist(seed, w, path=path).items()))
    return statistics.mean(out)


TITLE_BLOCKS = 8  # more than PLAYER_BLOCKS -- each band needs its own error bar


def _bands_delta(after, before, path):
    return {b.label: block_stats([title_prob(a, b, path=path)
                                  - title_prob(w, b, path=path)
                                  for a, w in zip(after, before)])
            for b in BANDS}


def player_title(roster, names, blocks=None, trials=TRIALS, seed0=SEED0,
                 R=None, path=None):
    """ONE NAME AT A TIME -- a multi-piece side is `roster_title`, never
    summed rows"""
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


def incoming_title(roster, players, blocks=None, trials=TRIALS, seed0=SEED0,
                   R=None, path=None):
    """Never sum rows -- multi-piece sides use `roster_title`"""
    dupes = collections.Counter(p["n"] for p in players)
    twice = sorted(n for n, c in dupes.items() if c > 1)
    if twice:
        raise ValueError("%s: two bodies of one name -- rename the row you "
                         "mean" % ", ".join(twice))
    seeds, R = _sampling(roster, TITLE_BLOCKS if blocks is None else blocks,
                         trials, seed0, R)
    pads = [i for i, p in enumerate(roster) if p["n"] in PAD_NAMES]
    if not pads:
        raise ValueError("%d bodies and none of them padded -- pass the 37 "
                         "you would field, or `basis()`" % len(roster))
    room = roster[:pads[-1]] + roster[pads[-1] + 1:]
    ref, out = {}, {}
    for p in players:
        g = slot_group(p["elig"])
        if g not in ref:
            body = group_body(g, R[g], "REPL")
            ref[g] = [bracket_weeks(room + [body], trials=trials, seed0=s)
                      for s in seeds]
        with_mus = [bracket_weeks(room + [p], trials=trials, seed0=s)
                    for s in seeds]
        out[p["n"]] = _bands_delta(with_mus, ref[g], path)
    return out


def roster_title(after, before, blocks=None, trials=TRIALS, seed0=SEED0,
                 path=None):
    """ARG ORDER IS THE SIGN, as `wins(deal, base)`"""
    seeds = seed_blocks(TITLE_BLOCKS if blocks is None else blocks, trials,
                        seed0)
    return _bands_delta(
        [bracket_weeks(after, trials=trials, seed0=s) for s in seeds],
        [bracket_weeks(before, trials=trials, seed0=s) for s in seeds], path)
