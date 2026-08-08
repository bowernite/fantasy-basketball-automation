"""Expected games played -- the fit, the model bake-off behind it, and the
evidence flags saying how much history a projection actually rests on."""
import collections, datetime, functools, math, random, statistics
from fetch_data import SEASON
from .board import POOL, pool, pool_seasons, season_or_latest
from .data import SEASON_STR
from .stats import ols, slope


#
# GP is the dominant input here (~10x any format effect) and the only one with no
# market price: boards supply BASE, nothing supplies GP. So it needs a defensible
# input, not precision. Candidates are ranked out of sample in `report_gp` and the
# winner is what `project_gp` does. Gated to the rotation players we trade.
GP_MIN_RATE = 20.0


SEASONS = [str(SEASON - i) for i in range(4, -1, -1)]   # oldest first


def age_at(born, season):
    """Age on Feb 1 of `season`'s back half -- the NBA's own season-age convention.

    A fixed point INSIDE the season, never `detail.age`: that is age-as-scraped,
    which re-labels every historical row each time the file is read.
    """
    b = datetime.date.fromisoformat(born)
    return (datetime.date(int(season) + 1, 2, 1) - b).days / 365.2425


def gp_fit(min_rate=GP_MIN_RATE):
    """(a, b, n): next-season GP ~= a + b * this-season GP.

    b is the share of a GP deviation that persists. It is SMALL, and that is the
    finding: taking one season's GP literally is the largest error available here.
    Kept as the one-season BASELINE the richer models have to beat.
    """
    xy = []
    for v in pool().values():
        s = v["seasons"]
        for lo, hi in zip(SEASONS, SEASONS[1:]):
            if lo in s and hi in s and s[lo][0] >= min_rate:
                xy.append((s[lo][1], s[hi][1]))
    mx, my, b = slope([x for x, _ in xy], [y for _, y in xy])
    return my - b * mx, b, len(xy)


def gp_rows(min_rate=GP_MIN_RATE, min_hist=1):
    """One row per (player, predicted season):
    {name, season, y, hist, seasons, rate, age}.

    `hist` is prior-season GP, MOST RECENT FIRST, and `seasons` is where it came
    from -- strictly earlier than `season`, which is what keeps the comparison
    honest. Gated on the rate in the most recent prior season, so the population
    is the rotation-quality players we actually trade.

    CENSORED, and it matters: the pool only holds seasons a player actually
    appeared in, so a player who misses a whole year or leaves the league is
    absent rather than a 0. Every figure here is expected GP GIVEN he plays.
    """
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


# Where the rate term stops buying games. Empirical mean next-season GP by last
# season's rate is CONCAVE and PEAKS around 30-40, so a linear term keeps paying past
# the peak and over-projects the stars every headline table rests on (+6.6 GP of
# bias at rate>=45). Knots 20-35 all sit inside each other's noise; 30 is the CV
# optimum and the only one that beats the unknotted form on a clustered bootstrap.
GP_KNOT = 30.0


# Below this rate a season's GP measures ROLE, not health (`Eval Definitions
# §LATE`), so it is also the bar a season clears to count as evidence that the
# player holds a rotation spot at all -- which is what `rate_evidence` counts.
ROTATION_RATE = 15.0


# A season this short is the only evidence the GP model has, and it is a bad one
# (`Eval Definitions §Durability` -- flag it, don't patch it).
FRAGMENT_GP = 25


# Six models, and between them they make every argument this section makes: the
# flat prior one season must beat, that season, whether more history buys
# anything, whether age does, and whether the knot earns its place. Nothing
# richer beats `gp1` by more than its own uncertainty.
#
# Every model is scored on the SAME rows, so a k-season model averages whatever
# history a row has up to k -- which is what a real projection must do. No row
# here carries more than 4 prior seasons, so `gp5` never sees a 5th.
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
    """model -> per-row out-of-sample squared error, k-fold CV GROUPED BY PLAYER.

    Grouped, not row-wise. A player contributes several target seasons, so a
    row-wise split puts his own durability level on both sides of it and flatters
    every history-based model -- which is exactly the model class under suspicion.

    Per ROW rather than reduced straight to RMSE, because the uncertainty that
    matters is over PLAYERS and you cannot resample players out of a scalar.
    """
    names = sorted({r["name"] for r in rows})
    if seed is not None:
        random.Random(seed).shuffle(names)
    fold = {n: i % folds for i, n in enumerate(names)}
    out = {}
    for name in (models or GP_MODELS):
        feat = GP_MODELS[name]
        se = [float("nan")] * len(rows)   # a row left unscored must poison `_rmse`
        for f in range(folds):
            tr = [r for r in rows if fold[r["name"]] != f]
            beta = ols(tr, feat, [r["y"] for r in tr]) if tr else None
            if beta is None:
                # Never skipped. A model scored on the folds it managed would be
                # ranked against competitors scored on all of them, and
                # `gp_bootstrap` would difference two RMSEs over different rows.
                raise ValueError(
                    "%s: fold %d of %d has no least-squares fit, so it cannot be "
                    "scored on the same rows as the other models -- drop the "
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
    """model -> out-of-sample RMSE over `rows`. See `gp_sq_errors`."""
    return {k: _rmse(v)
            for k, v in gp_sq_errors(rows, folds=folds, seed=seed).items()}


GP_SHUFFLES = 8


GP_BOOT = 2000


def gp_bootstrap(rows, models=None, ref="gp1", n=GP_BOOT, seed=11,
                 shuffles=GP_SHUFFLES):
    """model -> {rmse, delta, lo, hi, p}: RMSE and its gap to `ref`, with a 95%
    interval from a bootstrap CLUSTERED ON PLAYER. `p` is P(model beats ref).

    This is the uncertainty a gap between two models has to be judged against.
    Sampling error over the PLAYERS runs ~0.14 RMSE against gaps of 0.1-0.7, so an
    interval straddling zero is the answer and not a ranking. The sd across FOLD
    SHUFFLES is ~0.01 and prices only reproducibility of the split, so ranking on
    it turns a 0.15 gap into "more seasons is WORSE".

    Errors are averaged over `shuffles` shuffles first, so the split is integrated
    out and what remains is the player sampling the interval prices.
    """
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
    # The reference RMSE depends on the resample alone, so it is one per pick and
    # not one per pick per model.
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
                   "rate knotted at GP_KNOT. More history and age were both "
                   "tested; NOTHING beat one season, so one season on Occam.")


@functools.lru_cache(maxsize=1)
def gp_model():
    """(a, b_gp, b_rate) for next-season GP, the rate term knotted at GP_KNOT.
    What survived `report_gp`.

    Fit UNGATED, because it has to price a bench body as well as a starter and
    that is the whole job of the rate term: expected GP runs ~40 at rate <10
    against ~63 at rate 30-40. The knot is what stops that same term running on
    past the peak -- see GP_KNOT.
    """
    rows = gp_rows(min_rate=0.0)
    a, b, c = ols(rows, GP_MODELS["gp1+knot"], [r["y"] for r in rows])
    return a, b, c


def rate_evidence(name, season=SEASON_STR):
    """What the rate `Δw` runs on actually rests on.

    `our_roster` carries a rate forward at face value -- no shrinkage, no
    sample-size weighting -- and `Δwₜ` is flat across a productive window, so a
    rate posted over a fragment is charged to every season in that window. The
    games behind it is the evidence the window is set from.
    """
    s = pool_seasons(name)
    if not s:
        raise KeyError("no pool season for %r -- check the spelling against %s"
                       % (name, POOL))
    _, gp = season_or_latest(s, season)
    years = sorted(int(y) for y in s)
    # A gap INSIDE his history, or `season` itself missing. The second is the
    # censoring the GP fit is blindest to and it is not an interior gap, so
    # checking only the span silently passes every Kyrie on the board.
    missed = len(years) < years[-1] - years[0] + 1 or season not in s
    return {"gp": gp,
            "missed": missed,
            "rotation": sum(1 for r, _ in s.values() if r >= ROTATION_RATE)}


def evidence_flags(name, season=SEASON_STR):
    """EVERY flag code this player's POOL HISTORY earns, not a subset of it:
    `frag` (§Durability's fragment band), `miss`, `rotN` (fewer than 3 seasons at
    rate >= ROTATION_RATE) and `nopool`.

    Those four plus `fa` and `noproj` are the whole vocabulary `sim.py players`
    prints. Both of those are facts about the ROSTER ROW rather than about the
    pool, so `report_players` adds them there; the rest of §Output's codes --
    `split`, `1brd`, `stale`, `bear` -- are judgment or board data and nothing
    here can derive them.
    """
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


def project_gp(name, season=SEASON_STR, gp=None, rate=None):
    """Expected GP next season. THE projection this study uses, for every player on
    every roster -- ours and a counterparty's, through the same `our_roster`.

    Reads the player's most recent pool season, which is why a player who missed
    all of `season` is handled without being special-cased: his last season that
    exists is the one used.

    `rate` OVERRIDES the pool when given -- as a mere fallback it would be a
    silent no-op for every player the pool has seen, i.e. for all of ours.
    `gp` is a FALLBACK only, used for a player the pool has never seen: the
    pool's GP is what this model was fitted on, and a roster file's GP is the
    same season rounded differently. A name the pool does not have and you gave no
    fallback for RAISES, rather than returning a None that surfaces frames away as
    a TypeError under `round()`.
    """
    s = pool_seasons(name)
    if s:
        pool_rate, gp = season_or_latest(s, season)
        rate = pool_rate if rate is None else rate
    if gp is None or rate is None:
        raise KeyError("no pool season for %r -- pass gp= and rate=, or check the"
                       " spelling against %s" % (name, POOL))
    a, b, c = gp_model()
    return a + b * gp + c * min(rate, GP_KNOT)
