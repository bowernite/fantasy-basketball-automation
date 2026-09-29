"""Fit the player progression model on BBRef history, and backtest it

    uv run --with pandas==2.3.3,statsmodels==0.15.0,numpy==2.2.6 python fit_progression.py [--backtest [--cutoff YEAR]]

- No flag: refit -> `data/progression-params.json`
- `--backtest`: walk-forward gates at each of CUTOFFS -> `data/progression-backtest.txt`
- `--cutoff YEAR`: that cutoff only, printed, report untouched
- Refit each offseason after the mirror's end-of-season push (bump `fetch_data.BBREF_COMMIT`, then `./run fetch_data.py bbref`)
- Run one refit or backtest at a time

CPython for pandas/statsmodels; the stdlib sampler (`simlib/progression.py`) reads the params. Spread knobs are tuned by running that sampler under pypy (`simlib/progression_eval.py`). FP/G is on the repo's scale (our scoring, era-normalised), GP per 82; seasons are BBRef end-years (the pool keys start-years).
"""
import datetime, json, os, subprocess, sys, warnings, zlib
import numpy as np
import pandas as pd
import statsmodels.api as sm
import fetch_data

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
PARAMS = os.path.join(HERE, "data", "progression-params.json")
BACKTEST = os.path.join(HERE, "data", "progression-backtest.txt")
WORK = os.path.join(fetch_data.BBREF_DIR, "work")

FIRST = 1983            # first season a vet pair or exit row may start from
ROOKIE_FIRST = 1985
GP_FIRST = 2000         # GP habits before this era don't carry
SHORT_SEASONS = {1999: 50, 2012: 66, 2020: 72, 2021: 72}
ACTIVE = 20             # GP82 that counts as a season played
EXIT_HALF_LIFE = 8      # seasons
ROOKIE_HALF_LIFE = 10   # seasons
OLD_AGE = (32, 35)      # exit blends from the main fit into OLD_EXIT across these ages
OLD_EXIT = ["1", "a", "lL", "gp", "bpm"]
OLD_LEVEL_CAP = 35.0    # FP/G; the old have too few players above it (or above their p90 BPM) to say more protects
ERA_BREAK = 2016        # first season of the regime exit reads as current
STAR_LL = float(np.log(38 / 30))
EXIT_LEVEL_CAP = 45.0   # FP/G; above it exit has too few old players to bend the curve further
BPM_DEV_CLIP = 3.0      # ~p5-p95 of BPM above its level's norm; the effect saturates past it
CUTOFFS = (2004, 2009, 2013, 2020)   # 2020: the latest with post-2016 exit rows to fit; scores years 2-5 only
PROXY_ERR = 0.18        # log miss of a preseason rate projection on the season it projects [prior]
PROXY_NOISE_GRID = (0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35)
TRANSPORT_CUT = 2022    # BBRef end-year; the pool origins' scored seasons all fall after it
LAST = 2026             # newest completed season in the pinned mirror

VET_DRIFT = ["1", "a", "a2", "ay", "lL", "lL*a", "lL*a2", "lL*ay", "lL^2"]
VET_EXIT = VET_DRIFT + ["a34", "gp", "bpm", "cy3", "cy4", "cy5"]
VET_SCALE = ["1", "lL", "ay"]
AGE_DRIFT = ["1", "a", "a2", "ay"]                 # the single-age-curve baseline
AGE_EXIT = AGE_DRIFT + ["a34", "gp"]
AGE_SCALE = ["1", "ay"]
ROOKIE_DRIFT = ["1", "c1", "c2", "lL", "lL^2", "lL*c1", "lL*c2", "ad", "ad*c1", "lp*c1"]
ROOKIE_EXIT = ["1", "c1", "c2", "lL", "lL^2", "ad", "lp", "gp"]
ROOKIE_SCALE = ["1", "lL", "c1"]
GP_TERMS = ["1", "gpraw", "a28", "lo20"]   # lo20: deep-bench bodies sit more, starters don't

# Starting knobs; `tune` overwrites smult/phi1/pick floor from the sampler run
KNOBS = {"smult": 1.1, "phi0": 0.3, "phi1": 0.0, "sd_floor": 0.12,
         "young_mult": 1.15, "young_mult_rookie": 1.1, "smult_rookie": 1.0,
         "sigma_u": 0.15, "sigma_u_rookie": 0.25, "growth_pick_floor": 1}

BOARD = {"gamma": [0.02, 0.02, 0.02, 0.02], "clip": 1.0, "flag": 0.8}
USABLE = 25.0           # FP/G on >= ACTIVE GP: a starter in 12 x 9
WRV_RG = 18.0           # FP/G of the ~216th player (12 teams x 18 scorers)


def main(argv):
    mirror = fetch_data.bbref_mirror()
    P = panel(mirror)
    if "--backtest" in argv:
        dev = "--cutoff" in argv
        return backtest(P, [int(argv[argv.index("--cutoff") + 1])] if dev else CUTOFFS, dev)
    params = fit(P, LAST)
    params = tune(params, P, LAST, tag="full")
    params["fit"] = {"date": datetime.date.today().isoformat(),
                     "mirror": "%s@%s" % (fetch_data.BBREF_REPO, fetch_data.BBREF_COMMIT),
                     "through_season": LAST}
    with open(PARAMS, "w") as f:
        json.dump(params, f, indent=1)
    print("wrote", PARAMS)


# ---------------------------------------------------------------- panel

def panel(d):
    """player-season rows: nfpg (era-normalised FP/G), gp82, age (Feb 1,
    fractional), bpm, bpm2 (2-season GP-weighted), c (career year), pick"""
    tot = _nba(pd.read_csv(os.path.join(d, "Player Totals.csv"), low_memory=False))
    for c in ["g", "fg", "fga", "x3p", "x3pa", "orb", "trb", "ast", "stl", "blk",
              "tov", "pts", "trp_dbl"]:
        tot[c] = pd.to_numeric(tot[c], errors="coerce").fillna(0)
    tot = tot[tot.g > 0].copy()
    # our scoring from season totals; the DD bonus isn't in totals, and the era
    # rescale onto the repo's own scale (below) absorbs its average
    tot["fp"] = (tot.pts + tot.trb + tot.orb + 1.5 * tot.ast + 3 * tot.stl
                 + 2 * tot.blk - tot.tov + tot.x3p - 0.25 * (tot.fga - tot.fg)
                 - 0.25 * (tot.x3pa - tot.x3p) + 7 * tot.trp_dbl)
    tot["fpg"] = tot.fp / tot.g
    tot["gp82"] = (tot.g * 82 / tot.season.map(SHORT_SEASONS).fillna(82)).clip(upper=82)
    adv = _nba(pd.read_csv(os.path.join(d, "Advanced.csv"), low_memory=False))
    adv["bpm"] = pd.to_numeric(adv.bpm, errors="coerce")
    df = tot.merge(adv[["season", "player_id", "bpm"]], on=["season", "player_id"], how="left")
    scale = {s: g.loc[(g.fpg * g.gp82).nlargest(150).index, "fpg"].median()
             for s, g in df.groupby("season")}
    ref = repo_scale()
    df["nfpg"] = df.fpg * df.season.map(lambda s: ref / scale[s])
    ci = pd.read_csv(os.path.join(d, "Player Career Info.csv"))
    ci["born"] = pd.to_datetime(ci.birth_date, errors="coerce")
    ci["first"] = pd.to_numeric(ci["from"], errors="coerce")
    df = df.merge(ci[["player_id", "born", "first"]], on="player_id", how="left")
    feb1 = pd.to_datetime(df.season.astype(str) + "-02-01")
    exact = (feb1 - df.born).dt.days / 365.2425
    df["age"] = exact.fillna(pd.to_numeric(df.age, errors="coerce") + 0.5)
    dr = pd.read_csv(os.path.join(d, "Draft Pick History.csv"))
    dr = dr[dr.lg == "NBA"].copy()
    dr["pick"] = pd.to_numeric(dr.overall_pick, errors="coerce")
    dr = dr.dropna(subset=["pick"]).sort_values("season").drop_duplicates("player_id")
    df = df.merge(dr[["player_id", "pick"]], on="player_id", how="left")
    df["debut"] = df["first"].fillna(df.groupby("player_id").season.transform("min"))
    df["c"] = df.season - df.debut + 1
    df = df.sort_values(["player_id", "season"]).reset_index(drop=True)
    rookie = df[df.c == 1][["player_id", "age"]].rename(columns={"age": "age0"})
    df = df.merge(rookie, on="player_id", how="left")
    df["lp"] = np.log(df.pick.where(df.pick <= 60, 61).fillna(61).clip(1, 61))
    df["ad"] = df.age0 - 20
    df = _lag(df, ["nfpg", "gp82", "bpm"], -1)
    w = df.gp82.fillna(0) + df.gp82_m1.fillna(0)
    b0, b1 = df.bpm.fillna(0) * df.gp82.where(df.bpm.notna(), 0), \
        df.bpm_m1.fillna(0) * df.gp82_m1.where(df.bpm_m1.notna(), 0)
    wb = df.gp82.where(df.bpm.notna(), 0).fillna(0) + df.gp82_m1.where(df.bpm_m1.notna(), 0).fillna(0)
    df["bpm2"] = ((b0 + b1) / wb).where(wb > 0)
    act_prev = df.gp82_m1 >= ACTIVE
    df["lvl2"] = np.where(act_prev, (df.nfpg * df.gp82 + df.nfpg_m1 * df.gp82_m1) / w, df.nfpg)
    df["gp2"] = np.where(df.gp82_m1.notna(), (df.gp82 + df.gp82_m1.fillna(0)) / 2, df.gp82)
    # GP habits drift (load management), so exit reads GP against its season's norm
    rot = df[(df.nfpg >= 20) & (df.gp82 >= ACTIVE)].groupby("season").gp82.mean()
    df["gpn"] = df.season.map(rot)
    for k in range(1, 9):
        df = _lag(df, ["nfpg", "gp82"], k)
    print("panel: %d player-seasons %d-%d, repo scale %.2f FP/G vs mirror %.2f"
          % (len(df), df.season.min(), df.season.max(), ref, scale[LAST]))
    return df


def _nba(t):
    t = t[(t.lg == "NBA") & (t.season >= 1980)].copy()
    t["agg"] = t.team.astype(str).str.endswith("TM") | (t.team == "TOT")
    t = t.sort_values(["season", "player_id", "agg"], ascending=[True, True, False])
    return t.drop_duplicates(["season", "player_id"])


def _lag(df, cols, k):
    """`<col>_p<k>` = the same player's value k seasons later (`_m1` = one
    earlier); NaN when that season has no row"""
    tag = "m%d" % -k if k < 0 else "p%d" % k
    sh = df[["player_id", "season"] + cols].copy()
    sh["season"] = sh.season - k
    return df.merge(sh.rename(columns={c: "%s_%s" % (c, tag) for c in cols}),
                    on=["player_id", "season"], how="left")


def repo_scale():
    """Median FP/G of the repo pool's top 150 by season FP, newest season --
    the scale every fitted level is expressed on"""
    with open(os.path.join(HERE, "data", "players-%s.json" % fetch_data.SEASON_TAG)) as f:
        pool = json.load(f)
    s = str(fetch_data.SEASON)
    rows = sorted((v["seasons"][s] for v in pool.values() if s in v["seasons"]),
                  key=lambda x: -x[0] * x[1])[:150]
    return float(np.median([r[0] for r in rows]))


# ---------------------------------------------------------------- design

def base_vars(age, level, gp=None, bpm=None, cy=None, c=None, ad=None, lp=None,
              rookie=False, gp_ref=60.0):
    age = np.asarray(age, float)
    lo, hi = (-1.6, 0.7) if rookie else (-1.4, np.log(55 / 30))
    v = {"1": np.ones_like(age), "a": age - 28, "a2": np.maximum(age - 31, 0),
         "ay": np.maximum(24 - age, 0), "a34": np.maximum(age - 34, 0),
         "a28": np.maximum(age - 28, 0),
         "lo20": np.minimum(np.log(np.maximum(np.asarray(level, float), 1) / 20), 0),
         "lL": np.clip(np.log(np.maximum(np.asarray(level, float), 1) / 30), lo, hi)}
    if gp is not None:
        v["gp"] = (np.clip(np.asarray(gp, float), 0, 82) - gp_ref) / 10
        v["gpraw"] = np.asarray(gp, float)
    if bpm is not None:
        v["bpm"] = np.clip(np.nan_to_num(np.asarray(bpm, float)), -8, 12)
    if cy is not None:
        for n in (3, 4, 5):
            v["cy%d" % n] = (np.asarray(cy) == n).astype(float)
    if c is not None:
        v["c1"] = (np.asarray(c) == 1).astype(float)
        v["c2"] = (np.asarray(c) == 2).astype(float)
    if ad is not None:
        v["ad"] = np.asarray(ad, float)
    if lp is not None:
        v["lp"] = np.asarray(lp, float)
    return v


def design(v, terms):
    cols = []
    for t in terms:
        if t.endswith("^2"):
            cols.append(v[t[:-2]] ** 2)
        elif "*" in t:
            x, y = t.split("*")
            cols.append(v[x] * v[y])
        else:
            cols.append(v[t])
    return np.column_stack(cols)


def _model(terms, coef):
    return {"terms": list(terms), "coef": [float(x) for x in coef]}


def _quantiles(x, n=200):
    return [float(q) for q in np.quantile(x, np.linspace(0.5 / n, 1 - 0.5 / n, n))]


# ---------------------------------------------------------------- fit

def fit(P, cut, single=False):
    """All params from outcomes in seasons <= `cut`. `single`: the
    single-age-curve baseline -- same machinery, age-only terms, no BPM, no
    rookie stage"""
    dt, et, st = (AGE_DRIFT, AGE_EXIT, AGE_SCALE) if single else (VET_DRIFT, VET_EXIT, VET_SCALE)
    out = {"vet": vet_fit(P, cut, dt, et, st), "gp": gp_fit(P, cut),
           "gp_ref": float(P[(P.season <= cut) & (P.season > cut - 3)].gpn.mean()),
           "board": BOARD, "usable": USABLE, "wrv_rg": WRV_RG,
           "league_max": float(P[P.season == P.season.max()].nfpg.max()),
           "knobs": dict(KNOBS)}
    if single:
        out["vet"]["bpm_beta"] = []
    else:
        out["vet"]["bpm_ref"] = bpm_ref(P, cut)
        out["vet"]["bpm_dev_clip"] = BPM_DEV_CLIP
        out["proxy"] = proxy_fit(P, cut, out["vet"]["drift"])
        out["vet"]["bpm_beta"], out["vet"]["bpm_beta_ll"] = bpm_schedule(
            P, cut, out["vet"]["drift"], out["vet"]["bpm_ref"],
            proxy_fit(P, cut, out["vet"]["drift"], noise_grid=(0.0,)))
        out["rookie"] = rookie_fit(P, cut)
    return out


def vet_fit(P, cut, dterms, eterms, sterms):
    # pure-aging pairs: level from t-1 strips base-year luck from the change t -> t+1
    O = P[(P.season >= FIRST) & (P.season + 1 <= cut) & (P.c >= 3)
          & (P.gp82_m1 >= 40) & (P.gp82 >= ACTIVE) & (P.gp82_p1 >= ACTIVE)
          & (P.nfpg_m1 >= 8) & (P.nfpg > 0)]
    y = np.log(O.nfpg_p1 / O.nfpg).values
    v = base_vars(O.age, O.nfpg_m1)
    X = design(v, dterms)
    drift = sm.QuantReg(y, X).fit(q=0.5).params
    res = y - X @ drift
    Z = design(v, sterms)
    sc = sm.QuantReg(np.abs(res), Z).fit(q=0.5).params
    z = res / np.clip(Z @ sc, 0.03, None)
    star = v["lL"] >= STAR_LL if "lL" in dterms else np.zeros(len(z), bool)
    E = P[(P.season >= FIRST) & (P.season + 3 <= cut) & (P.c >= 3)
          & (P.gp82 >= ACTIVE) & (P.lvl2 >= 6)]
    ex = ~((E.gp82_p1 >= ACTIVE) | (E.gp82_p2 >= ACTIVE) | (E.gp82_p3 >= ACTIVE))
    ve = base_vars(E.age, np.minimum(E.lvl2, EXIT_LEVEL_CAP), gp=E.gp2, bpm=E.bpm2, cy=E.c, gp_ref=E.gpn)
    # from about 2016 the fringe leaves far faster (two-way deals, G League stashes); a level
    # slope that only turns on in that regime, once enough of it has been seen
    ve["era"] = (E.season.values >= ERA_BREAK).astype(float)
    if "lL" in eterms and ve["era"].sum() >= 500:
        eterms = eterms + ["era", "era*lL"]
    H = design(ve, eterms)
    # good players' exits fell from 2-5% to ~0-1% a year in the mid-2000s, so
    # the latest seasons speak loudest
    w = 0.5 ** ((cut - 3 - E.season.values) / EXIT_HALF_LIFE)
    exit_ = sm.GLM(ex.values.astype(float), H, family=sm.families.Binomial(),
                   var_weights=w).fit().params
    print("  vet cut %d: %d drift pairs, %d exit rows (%.1f%% exit)"
          % (cut, len(O), len(E), 100 * ex.mean()))
    old = {}
    if "lL" in eterms:
        # few stars play past 36, so the main fit's level x age terms protect
        # them far past its data; the old take over from a flatter fit on them
        o = (E.age >= OLD_AGE[0]).values
        vo = {k: x[o] for k, x in ve.items()}
        vo["lL"] = np.minimum(vo["lL"], np.log(OLD_LEVEL_CAP / 30))
        bpm_cap = float(np.quantile(vo["bpm"], 0.9))
        vo["bpm"] = np.minimum(vo["bpm"], bpm_cap)
        fo = sm.GLM(ex.values[o].astype(float), design(vo, OLD_EXIT), family=sm.families.Binomial()).fit()
        old = {"exit_old": _model(OLD_EXIT, fo.params), "old_age": list(OLD_AGE), "old_level_cap": OLD_LEVEL_CAP,
               "old_bpm_cap": bpm_cap}
        print("  old exit, %d rows aged %d+: %s" % (o.sum(), OLD_AGE[0], np.round(fo.params, 3).tolist()))
    return {"drift": _model(dterms, drift), "scale": _model(sterms, sc),
            "exit": _model(eterms, exit_), "exit_level_cap": EXIT_LEVEL_CAP, **old, "resq": _quantiles(z / z.std()),
            "zsd": float(z.std()), **_star_pool(z[star]), **_young_pool(z[(O.age <= 24).values & ~star])}


def _star_pool(z):
    """Stars' one-step misses, drawn from their own pool: a star's bad year is
    an injury-shaped drop more often than a role player's"""
    if len(z) < 100:
        return {}
    return {"star_ll": STAR_LL, "resq_star": _quantiles(z / z.std()), "zsd_star": float(z.std())}


def _young_pool(z):
    """Misses at 24 and under, from their own pool: a young player's surprise
    is a breakout as often as a slump, where an older one's leans down"""
    if len(z) < 100:
        return {}
    q = np.quantile(z / z.std(), [.05, .5, .95])
    print("  young pool n=%d: p5 %+.2f p50 %+.2f p95 %+.2f (SD units)" % (len(z), *q))
    return {"resq_young": _quantiles(z / z.std()), "zsd_young": float(z.std())}


def median_path(drift, age, level, years):
    """Deterministic median path from `level` at `age` -- log levels"""
    terms, coef = drift["terms"], np.array(drift["coef"])
    lv, out = np.log(np.asarray(level, float)), []
    age = np.asarray(age, float)
    for j in range(years):
        lv = lv + design(base_vars(age + j, np.exp(lv)), terms) @ coef
        out.append(lv)
    return out


BPM_REF = ["1", "lL", "lL^2", "a", "lL*a"]


def bpm_ref(P, cut):
    """BPM typical of a level and age. The drift's level terms already carry
    it, so only a player's BPM above or below it moves his path"""
    O = P[(P.season <= cut) & (P.season >= FIRST) & (P.c >= 2) & (P.gp82 >= ACTIVE)
          & P.bpm2.notna() & (P.lvl2 >= 6)]
    X = design(base_vars(O.age, O.lvl2), BPM_REF)
    return _model(BPM_REF, sm.OLS(np.clip(O.bpm2.values, -8, 12), X).fit().params)


def bpm_schedule(P, cut, drift, ref, proxy, steps=4, horizons=6):
    """Per-step drift per point of BPM above `ref`, as `(beta, beta_ll)`:
    the step's slope is beta + beta_ll * lL of year 1. Each is the cumulative
    survivor residual slope at each horizon, differenced; 0 after `steps` (it
    plateaus). Year 1 is `proxy_fit`'s noiseless stand-in, a calibrated level:
    against the actual year 1, that year's luck would pass for BPM; against
    a noisy stand-in, BPM would be correcting that stand-in's own misses"""
    O = P[(P.season >= FIRST) & (P.c >= 2) & (P.gp82 >= ACTIVE) & (P.gp82_p1 >= ACTIVE)
          & (P.nfpg_p1 >= 10) & P.bpm2.notna() & (P.season + 2 <= cut)]
    level1 = _proxy_rate(O, drift, proxy).values
    path = median_path(drift, O.age + 1, level1, horizons)
    cum = []
    for j in range(1, horizons + 1):
        ok = ((O["gp82_p%d" % (j + 1)] >= ACTIVE) & (O.season + 1 + j <= cut)).values
        y = np.log(O["nfpg_p%d" % (j + 1)].values[ok]) - path[j - 1][ok]
        v = base_vars(O.age.values[ok] + 1, level1[ok])
        dev = np.clip(np.clip(O.bpm2.values[ok], -8, 12) - design(v, ref["terms"]) @ np.array(ref["coef"]),
                      -BPM_DEV_CLIP, BPM_DEV_CLIP)
        X = sm.add_constant(np.column_stack([dev, dev * v["lL"]]))
        cum.append(sm.OLS(y, X).fit().params[1:] if ok.sum() > 200 else cum[-1])
    cum = np.array(cum)
    beta, beta_ll = (np.diff(np.r_[0.0, cum[:steps, i]]) for i in (0, 1))
    print("  bpm cumulative by horizon %s + %s*lL -> steps %s + %s*lL"
          % (np.round(cum[:, 0], 3).tolist(), np.round(cum[:, 1], 3).tolist(),
             np.round(beta, 4).tolist(), np.round(beta_ll, 4).tolist()))
    return [float(b) for b in beta], [float(b) for b in beta_ll]


def gp_fit(P, cut):
    """E3: a transient <20-GP hurdle, then a linear mean in last GP, age past
    28 and how far below 20 FP/G he sits, recentred on the last 3 target
    seasons; residuals are empirical"""
    T = P[(P.season >= GP_FIRST) & (P.season + 1 <= cut) & (P.gp82 >= ACTIVE) & (P.nfpg >= 6)].copy()
    alive = pd.Series(False, index=T.index)
    for j in (1, 2, 3):
        alive |= (T["gp82_p%d" % j] >= ACTIVE) & (T.season + j <= cut)
    T = T[alive]
    T["y"] = T.gp82_p1.fillna(0).clip(upper=82)
    H = T[T.y >= ACTIVE]
    X = design(base_vars(H.age, H.nfpg, gp=H.gp82), GP_TERMS)
    b = sm.OLS(H.y.values, X).fit().params
    recent = (H.season + 1 >= cut - 2).values
    shift = float(np.mean(H.y.values[recent] - X[recent] @ b))
    res = H.y.values[recent] - X[recent] @ b - shift
    b[0] += shift
    F = T[(T.season + 3 <= cut) & (T.season + 1 >= cut - 14)]
    low = (F.y < ACTIVE).values.astype(float)
    Xh = design(base_vars(F.age, F.nfpg, gp=F.gp82), GP_TERMS)
    hurdle = sm.Logit(low, Xh).fit(disp=0).params
    print("  gp cut %d: mean %s, P(low|alive) %.3f"
          % (cut, dict(zip(GP_TERMS, np.round(b, 3))), low.mean()))
    return {"mean": _model(GP_TERMS, b), "resq": _quantiles(res, 100),
            "hurdle": _model(GP_TERMS, hurdle), "low_pool": _quantiles(F.y.values[low > 0], 50)}


def rookie_fit(P, cut):
    """Career steps 1->2 and 2->3 as a Markov chain on the observed log rate
    (c=3 rows are the dummies' baseline and share the slopes)"""
    R = P[(P.debut >= ROOKIE_FIRST) & (P.c <= 3) & (P.nfpg > 0)
          & (P.gp82 >= np.where(P.c == 1, 10, ACTIVE))]
    D = R[(R.season + 1 <= cut) & (R.gp82_p1 >= ACTIVE)]
    y = np.log(D.nfpg_p1.values / np.maximum(D.nfpg.values, 2))
    v = base_vars(D.age, np.maximum(D.nfpg, 2), c=D.c, ad=D.ad, lp=D.lp, rookie=True)
    X = design(v, ROOKIE_DRIFT)
    # rookies' development and hazards drift by era, so recent classes speak
    # loudest; weighting both sides of a median fit weights its absolute errors
    w = 0.5 ** ((cut - 1 - D.season.values) / ROOKIE_HALF_LIFE)
    drift = sm.QuantReg(y * w, X * w[:, None]).fit(q=0.5).params
    res = y - X @ drift
    Z = design(v, ROOKIE_SCALE)
    sc = sm.QuantReg(np.abs(res) * w, Z * w[:, None]).fit(q=0.5).params
    z = res / np.clip(Z @ sc, 0.05, None)
    E = R[R.season + 3 <= cut]
    act = [(E["gp82_p%d" % j] >= ACTIVE).values for j in (1, 2, 3)]
    ex = ~(act[0] | act[1] | act[2])
    miss = ~act[0] & (act[1] | act[2])
    H = design(base_vars(E.age, np.maximum(E.nfpg, 2), gp=E.gp82, c=E.c, ad=E.ad,
                         lp=E.lp, rookie=True, gp_ref=E.gpn), ROOKIE_EXIT)
    we = 0.5 ** ((cut - 3 - E.season.values) / ROOKIE_HALF_LIFE)
    ex_p, mi_p = (sm.GLM(y.astype(float), H, family=sm.families.Binomial(), var_weights=we).fit().params
                  for y in (ex, miss))
    print("  rookie cut %d: %d drift pairs, %d exit rows" % (cut, len(D), len(E)))
    return {"drift": _model(ROOKIE_DRIFT, drift), "scale": _model(ROOKIE_SCALE, sc),
            "exit": _model(ROOKIE_EXIT, ex_p), "miss": _model(ROOKIE_EXIT, mi_p),
            "resq": _quantiles(z / z.std()), "zsd": float(z.std())}


# ---------------------------------------------------------------- origins

def _aged(O, drift):
    """His 2-season level aged one year by `drift`"""
    return O.lvl2 * np.exp(design(base_vars(O.age, O.lvl2), drift["terms"]) @ np.array(drift["coef"]))


def proxy_fit(P, cut, drift, noise_grid=None):
    """The backtest's stand-in for a preseason rate projection: log rate =
    b0 + b1 * log(year 1 seen through noise) + b2 * log(aged 2-season level),
    median-fit so that year 2 follows it the way the sampler follows a true
    level. The noise is sized so the stand-in misses the actual year 1 by
    PROXY_ERR, as a real feed would; the fit keeps it calibrated -- an extreme
    year 1 is taken at less than face value, not with that year's luck"""
    O = P[(P.season >= 1990) & (P.season + 2 <= cut) & (P.c >= 1) & (P.gp82 >= ACTIVE)
          & (P.gp82_p1 >= ACTIVE) & (P.gp82_p2 >= ACTIVE)]
    coef, aged, z = np.array(drift["coef"]), np.log(_aged(O, drift)).values, _row_noise(O)
    best = None
    for noise in noise_grid or PROXY_NOISE_GRID:
        Z = np.column_stack([np.ones(len(O)), np.log(O.nfpg_p1.values) + noise * z, aged])
        x = np.log(O.nfpg_p1.values)
        for _ in range(4):
            y = np.log(O.nfpg_p2.values) - design(base_vars(O.age + 1, np.exp(x)), drift["terms"]) @ coef
            b = sm.QuantReg(y, Z).fit(q=0.5).params
            x = Z @ b
        err = float(np.std(np.log(O.nfpg_p1.values) - x))
        if best is None or abs(err - PROXY_ERR) < abs(best[0] - PROXY_ERR):
            best = (err, noise, b)
    err, noise, b = best
    print("  proxy cut %d: log proj = %.3f + %.3f*log(year 1 x noise %.2f) + %.3f*log(aged level); "
          "misses year 1 by %.3f" % (cut, b[0], b[1], noise, b[2], err))
    return {"b": [float(v) for v in b], "noise": noise}


def _row_noise(O):
    """A standard normal per player-season, the same on every run"""
    return np.array([np.random.default_rng(zlib.crc32(("%s%d" % (p, s)).encode())).standard_normal()
                     for p, s in zip(O.player_id, O.season)])


def _proxy_rate(O, drift, proxy):
    b, noise = proxy["b"], proxy["noise"]
    return np.exp(b[0] + b[1] * (np.log(O.nfpg_p1) + noise * _row_noise(O)) + b[2] * np.log(_aged(O, drift)))


def proxy_gp(gp, age, rate, g):
    """The backtest's stand-in for a preseason GP projection: the GP model's
    own expectation off the season before -- the feeds see no more than that"""
    gp, age, rate = (np.asarray(x, float) for x in (gp, age, rate))
    v = base_vars(age, rate, gp=gp)
    low = 1 / (1 + np.exp(-(design(v, g["hurdle"]["terms"]) @ np.array(g["hurdle"]["coef"]))))
    mean = np.clip(design(v, g["mean"]["terms"]) @ np.array(g["mean"]["coef"]), ACTIVE, 82)
    return (1 - low) * mean + low * np.mean(g["low_pool"])


def origins(P, lo, hi, ref, last=LAST):
    """Backtest players at origin seasons lo..hi: year 1 = origin + 1.
    Stage D = rookie season is year 1, S = one season done, V = two or more.
    Year 1 is `proxy_fit`'s and `proxy_gp`'s stand-ins for the preseason
    feeds; a draftee's is his actual rookie season, which the rookie stage is
    fit on. Outcomes after season `last` are left unseen"""
    drift = ref["vet"]["drift"]
    O = P[(P.season >= lo) & (P.season <= hi)]
    rows = []
    # a player with no year-1 season at all has left the league: the feeds
    # carry no projection for him, and neither does anything we'd run
    vet = O[(O.gp82 >= ACTIVE) & (O.c >= 1) & (O.gp82_p1 > 0)]
    vet = vet.assign(aged=_aged(vet, drift), proj=_proxy_rate(vet, drift, ref["proxy"]),
                     gp_proj=proxy_gp(vet.gp82, vet.age, vet.nfpg, ref["gp"]))
    for r in vet.itertuples():
        proj = r.proj if r.gp82_p1 >= ACTIVE else r.aged
        if proj < 8:
            continue
        rows.append(_origin(r, "S" if r.c == 1 else "V", proj, last, gp1=r.gp_proj, cy1=r.c + 1))
    # draftees: their rookie season is year 1, so the origin is the season before
    rk = P[(P.c == 1) & (P.season - 1 >= lo) & (P.season - 1 <= hi) & (P.gp82 >= 10)
           & (P.pick <= 60) & (P.debut >= ROOKIE_FIRST)]
    for r in rk.itertuples():
        rows.append(_origin(r, "D", max(r.nfpg, 2), last, gp1=r.gp82, cy1=1, rookie_row=True))
    return rows


def _origin(r, stage, proj, last, gp1, cy1, rookie_row=False):
    """Inputs the sampler needs plus realised outcomes by year (1 = origin+1)"""
    lead = 0 if rookie_row else 1
    s = r.season - 1 if rookie_row else r.season
    o = {"id": r.player_id, "origin": int(s), "stage": stage, "rate1": float(proj),
         "gp1": float(gp1), "age1": float(r.age + lead),
         "gp_last": None if rookie_row else float(r.gp82),
         "bpm": None if (rookie_row or r.bpm2 != r.bpm2) else float(r.bpm2),
         "cy1": int(cy1), "pick": None if r.pick != r.pick else int(r.pick),
         "age_rookie": None if r.age0 != r.age0 else float(r.age0),
         "rate": [], "gp": []}
    for k in range(1, 9):
        j = k - 1 + lead
        rate = r.nfpg if j == 0 else getattr(r, "nfpg_p%d" % j)
        gp = r.gp82 if j == 0 else getattr(r, "gp82_p%d" % j)
        seen = s + k <= last
        o["rate"].append(float(rate) if (seen and rate == rate) else None)
        o["gp"].append((0.0 if gp != gp else float(gp)) if seen else None)
    return o


def transport_origins(P, ref):
    """Repo pool 2021-25 (start-years) as origins, scored on its own FP/G and
    GP: does a fit on BBRef travel to the league's own numbers?"""
    with open(os.path.join(HERE, "data", "players-%s.json" % fetch_data.SEASON_TAG)) as f:
        pool = json.load(f)
    with open(os.path.join(HERE, "data", "bbref-%s.json" % fetch_data.SEASON_TAG)) as f:
        ids = json.load(f)
    drift, b, g = ref["vet"]["drift"], ref["proxy"]["b"], ref["gp"]
    bpm2 = {(r.player_id, r.season): r.bpm2 for r in P.itertuples() if r.bpm2 == r.bpm2}
    rows = []
    for name, v in pool.items():
        if name not in ids or not v.get("born"):
            continue
        s, bb = v["seasons"], ids[name]
        b_id = bb["bbref"]
        born = datetime.date.fromisoformat(v["born"])
        for o in (2021, 2022, 2023):
            cur, prev, nxt = s.get(str(o)), s.get(str(o - 1)), s.get(str(o + 1))
            if not cur or cur[1] < ACTIVE:
                continue
            hist = ((cur[0] * cur[1] + prev[0] * prev[1]) / (cur[1] + prev[1])
                    if prev and prev[1] >= ACTIVE else cur[0])
            age1 = (datetime.date(o + 2, 2, 1) - born).days / 365.2425
            aged = hist * float(np.exp(design(base_vars([age1 - 1], [hist]), drift["terms"])
                                       @ np.array(drift["coef"]))[0])
            z = np.random.default_rng(zlib.crc32(("%s%d" % (b_id, o)).encode())).standard_normal()
            proj = (float(np.exp(b[0] + b[1] * (np.log(nxt[0]) + ref["proxy"]["noise"] * z)
                                 + b[2] * np.log(aged)))
                    if nxt and nxt[1] >= ACTIVE else aged)
            if proj < 8 or not nxt:
                continue
            cy1 = o + 1 - bb["debut"] + 1
            row = {"id": name, "origin": o, "stage": "S" if cy1 == 2 else ("D" if cy1 == 1 else "V"),
                   "rate1": proj, "gp1": float(proxy_gp([cur[1]], [age1 - 1], [cur[0]], g)[0]),
                   "age1": age1, "gp_last": float(cur[1]), "bpm": bpm2.get((b_id, o + 1)),
                   "cy1": cy1, "pick": bb["pick"], "age_rookie": age1 - (cy1 - 1),
                   "rate": [], "gp": []}
            if row["stage"] == "D":
                continue
            for k in range(1, 5):
                x = s.get(str(o + k))
                seen = o + k <= fetch_data.SEASON
                row["rate"].append(float(x[0]) if (seen and x) else None)
                row["gp"].append((float(x[1]) if x else 0.0) if seen else None)
            rows.append(row)
    return rows


# ---------------------------------------------------------------- tune / backtest (pypy)

def _eval(cmd, *paths):
    """Run `simlib/progression_eval.py` under pypy: the sampler is stdlib and
    ~30x faster there"""
    os.makedirs(WORK, exist_ok=True)
    out = subprocess.run(["pypy3.11", "-m", "simlib.progression_eval", cmd] + list(paths),
                         cwd=HERE, capture_output=True, text=True)
    if out.returncode:
        sys.exit(out.stdout + out.stderr)
    return out.stdout


def _dump(name, obj):
    os.makedirs(WORK, exist_ok=True)
    path = os.path.join(WORK, name)
    with open(path, "w") as f:
        json.dump(obj, f)
    return path


def tune(params, P, cut, tag, ref=None):
    """Spread knobs chosen on origins whose years 2-5 all fall <= `cut`.
    Origins are built with `ref`'s drift and proxy (default: `params`')"""
    ref = ref or params
    tr = origins(P, 1990, cut - 5, ref, last=cut)
    pp, op = _dump("params-%s.json" % tag, params), _dump("tune-origins-%s.json" % tag, tr)
    out = _eval("tune", pp, op)
    print(out.strip())
    with open(pp) as f:
        return json.load(f)


def backtest(P, cutoffs, dev=False):
    """Walk-forward gates at each cutoff, then transport. `dev`: print only,
    leaving the checked-in report alone"""
    report = []
    for cut in cutoffs:
        print("cutoff", cut)
        full = tune(fit(P, cut), P, cut, "full-%d" % cut)
        single = tune(fit(P, cut, single=True), P, cut, "single-%d" % cut, full)
        test = origins(P, cut + 1, LAST - 2, full)
        paths = [_dump("params-full-%d.json" % cut, full),
                 _dump("params-single-%d.json" % cut, single),
                 _dump("test-origins-%d.json" % cut, test),
                 os.path.join(WORK, "tune-origins-full-%d.json" % cut)]
        report.append("=" * 72 + "\nCUTOFF %d  (fit on outcomes <= %d; test origins %d-%d, n=%d)\n"
                      % (cut, cut, cut + 1, LAST - 2, len(test)) + _eval("backtest", *paths))
        print(report[-1])
    if dev:
        return
    # fit before the pool's scored seasons, so the league's own numbers are out of sample
    print("transport cutoff", TRANSPORT_CUT)
    tp = tune(fit(P, TRANSPORT_CUT), P, TRANSPORT_CUT, "full-%d" % TRANSPORT_CUT)
    tr = transport_origins(P, tp)
    report.append("=" * 72 + "\nTRANSPORT  repo pool origins 2021-23 (n=%d), fit on outcomes <= %d\n"
                  % (len(tr), TRANSPORT_CUT)
                  + _eval("transport", _dump("params-full-%d.json" % TRANSPORT_CUT, tp),
                          _dump("transport-origins.json", tr)))
    print(report[-1])
    with open(BACKTEST, "w") as f:
        f.write("Progression backtest, %s, mirror %s\n\n" % (datetime.date.today(), fetch_data.BBREF_COMMIT)
                + "\n".join(report))
    print("wrote", BACKTEST)


if __name__ == "__main__":
    main(sys.argv[1:])
