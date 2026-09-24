"""Expected games played -- the fit, the model bake-off behind it, and the
evidence flags saying how much history a projection actually rests on."""
import collections, datetime, functools, math, random, statistics
from fetch_data import SEASON
from .board import POOL, pool, pool_seasons, season_or_latest
from .projections import projected_gp
from .data import SEASON_STR
from .stats import ols, slope


# GP is the dominant input here. Candidates are ranked out of sample
# in `report_gp`; gated to the rotation players we trade.
GP_MIN_RATE = 20.0


SEASONS = [str(SEASON - i) for i in range(4, -1, -1)]   # oldest first


def age_at(born, season):
    """Age on Feb 1 of `season`'s back half -- NOT `detail.age`, which
    re-labels every historical row each time the file is read"""
    b = datetime.date.fromisoformat(born)
    return (datetime.date(int(season) + 1, 2, 1) - b).days / 365.2425


def gp_fit(min_rate=GP_MIN_RATE):
    """(a, b, n): next-season GP ~= a + b * this-season GP"""
    xy = []
    for v in pool().values():
        s = v["seasons"]
        for lo, hi in zip(SEASONS, SEASONS[1:]):
            if lo in s and hi in s and s[lo][0] >= min_rate:
                xy.append((s[lo][1], s[hi][1]))
    mx, my, b = slope([x for x, _ in xy], [y for _, y in xy])
    return my - b * mx, b, len(xy)


def gp_rows(min_rate=GP_MIN_RATE, min_hist=1):
    """Censored: a player who misses a whole year or leaves the league is
    absent rather than a 0, so every `y` here is expected GP GIVEN he plays"""
    rows = []
    for name, v in pool().items():
        if not v.get("born"):
            continue
        s = v["seasons"]
        for i, tgt in enumerate(SEASONS):
            hist = [x for x in SEASONS[:i] if x in s][::-1]
            if tgt not in s or len(hist) < min_hist or s[hist[0]][0] < min_rate:
                continue
            rows.append({"name": name, "season": tgt, "y": s[tgt][1],
                         "hist": [s[x][1] for x in hist], "seasons": hist,
                         "rate": s[hist[0]][0], "age": age_at(v["born"], tgt)})
    return rows


def _avg(xs):
    return sum(xs) / len(xs)


# Empirical GP-by-rate is concave and peaks ~30-40; the knot stops a linear
# term from over-projecting stars past that peak.
GP_KNOT = 30.0


# Below this rate a season's GP measures ROLE, not health (`Eval Definitions
# §Durability`), and is what `rate_evidence` counts as rotation evidence.
ROTATION_RATE = 15.0


FRAGMENT_GP = 25  # a season this short is the only (weak) evidence GP has


# Six models between them cover the arguments this section makes: the flat
# prior a model must beat, whether more history buys anything, whether age
# does, and whether the knot earns its place.
GP_MODELS = {
    "mean":      lambda r: (),
    "age":       lambda r: (r["age"],),
    "gp1":       lambda r: (r["hist"][0],),
    "gp5":       lambda r: (_avg(r["hist"][:5]),),
    "gp1+rate":  lambda r: (r["hist"][0], r["rate"]),
    "gp1+knot":  lambda r: (r["hist"][0], min(r["rate"], GP_KNOT)),
}


GP_FOLDS = 5


def gp_sq_errors(rows, models=None, folds=GP_FOLDS, seed=None):
    """model -> per-row out-of-sample squared error, k-fold CV grouped BY
    PLAYER (a row-wise split would leak a player's own durability level
    across folds)"""
    names = sorted({r["name"] for r in rows})
    if seed is not None:
        random.Random(seed).shuffle(names)
    fold = {n: i % folds for i, n in enumerate(names)}
    out = {}
    for name in (models or GP_MODELS):
        feat = GP_MODELS[name]
        se = [float("nan")] * len(rows)   # poisons `_rmse` if left unscored
        for f in range(folds):
            tr = [r for r in rows if fold[r["name"]] != f]
            beta = ols(tr, feat, [r["y"] for r in tr]) if tr else None
            if beta is None:
                raise ValueError(
                    "%s: fold %d of %d has no least-squares fit -- drop the "
                    "model or the fold, do not compare them" % (name, f, folds))
            for i, r in enumerate(rows):
                if fold[r["name"]] == f:
                    p = beta[0] + sum(b * x for b, x in zip(beta[1:], feat(r)))
                    se[i] = (p - r["y"]) ** 2
        out[name] = se
    return out


def _rmse(se):
    return math.sqrt(sum(se) / len(se))


def gp_models(rows, folds=GP_FOLDS, seed=None):
    return {k: _rmse(v)
            for k, v in gp_sq_errors(rows, folds=folds, seed=seed).items()}


GP_SHUFFLES = 8


GP_BOOT = 2000


def gp_bootstrap(rows, models=None, ref="gp1", n=GP_BOOT, seed=11,
                 shuffles=GP_SHUFFLES):
    """model -> {rmse, delta, lo, hi, p}: RMSE and its gap to `ref`, with a
    95% interval from a bootstrap clustered on player. `p` is P(model beats
    ref). Errors are averaged over `shuffles` fold-shuffles first, so the
    interval prices player sampling rather than split reproducibility."""
    models = list(models or GP_MODELS)
    if ref not in models:
        models = models + [ref]
    per = [gp_sq_errors(rows, models, seed=s) for s in range(shuffles)]
    se = {m: [statistics.mean(p[m][i] for p in per) for i in range(len(rows))]
          for m in models}
    names = sorted({r["name"] for r in rows})
    byname = collections.defaultdict(list)
    for i, r in enumerate(rows):
        byname[r["name"]].append(i)
    rng = random.Random(seed)
    picks = [[i for nm in (rng.choice(names) for _ in names) for i in byname[nm]]
             for _ in range(n)]
    ref_rmse = [_rmse([se[ref][i] for i in idx]) for idx in picks]
    ref_full = _rmse(se[ref])
    out = {}
    for m in models:
        d = sorted(_rmse([se[m][i] for i in idx]) - r
                   for idx, r in zip(picks, ref_rmse))
        rmse = _rmse(se[m])
        out[m] = {"rmse": rmse, "delta": rmse - ref_full,
                  "lo": d[int(0.025 * n)], "hi": d[int(0.975 * n)],
                  "p": sum(x < 0 for x in d) / n}
    return out


PROJECT_GP_NOTE = ("one prior season of GP shrunk toward the pool, plus scoring "
                   "rate knotted at GP_KNOT, used only when neither Hashtag nor "
                   "FanScout carries him. More history and age were both "
                   "tested; NOTHING beat one season, so one season on Occam.")


@functools.lru_cache(maxsize=1)
def gp_model():
    """Fit UNGATED -- it must price a bench body as well as a starter"""
    rows = gp_rows(min_rate=0.0)
    a, b, c = ols(rows, GP_MODELS["gp1+knot"], [r["y"] for r in rows])
    return a, b, c


def rate_evidence(name, season=SEASON_STR):
    s = pool_seasons(name)
    if not s:
        raise KeyError("no pool season for %r -- check the spelling against %s"
                       % (name, POOL))
    _, gp = season_or_latest(s, season)
    years = sorted(int(y) for y in s)
    # a gap inside his history, or `season` itself missing
    missed = len(years) < years[-1] - years[0] + 1 or season not in s
    return {"gp": gp,
            "missed": missed,
            "rotation": sum(1 for r, _ in s.values() if r >= ROTATION_RATE)}


def evidence_flags(name, season=SEASON_STR):
    """Every flag code this player's pool history earns: `frag`
    (§Durability's fragment band), `miss`, `rotN` (fewer than 3 seasons at
    rate >= ROTATION_RATE), `nopool`. `report_players` adds `fa`/`noproj`,
    which are facts about the roster row rather than the pool."""
    try:
        e = rate_evidence(name, season)
    except KeyError:
        return ["nopool"]
    flags = []
    if e["gp"] <= FRAGMENT_GP:
        flags.append("frag")
    if e["missed"]:
        flags.append("miss")
    if e["rotation"] < 3:
        flags.append("rot%d" % e["rotation"])
    return flags


def mapped_gp(name, season=SEASON_STR, gp=None, rate=None):
    """Expected GP next season, off the player's most recent pool season

    `rate` OVERRIDES the pool when given; `gp` is a FALLBACK used only when
    the pool has never seen this player. Raises rather than silently
    returning None if neither the pool nor a fallback is available"""
    s = pool_seasons(name)
    if s:
        pool_rate, gp = season_or_latest(s, season)
        rate = pool_rate if rate is None else rate
    if gp is None or rate is None:
        raise KeyError("no pool season for %r -- pass gp= and rate=, or check the"
                       " spelling against %s" % (name, POOL))
    a, b, c = gp_model()
    return a + b * gp + c * min(rate, GP_KNOT)


def durable_gp(p):
    """Projected GP floored at the durability map. A projection under his
    track record is this-season absence (injury, suspension), not what he is
    worth. A body the pool has never seen keeps its projection"""
    if not pool_seasons(p["n"]):
        return p["gp"]
    return max(p["gp"], mapped_gp(p["n"]))


def project_gp(name, season=SEASON_STR, gp=None, rate=None):
    """`gp` and `rate` only apply when neither Hashtag nor FanScout hits"""
    feed_gp = projected_gp(name)
    if feed_gp is not None:
        return feed_gp
    return mapped_gp(name, season=season, gp=gp, rate=rate)
