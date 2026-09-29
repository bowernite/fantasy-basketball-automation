"""Player progression: year-by-year FP/G, GP and exit paths over up to 20
seasons, sampled from the params `fit_progression.py` checks in.

A player is a dict: `rate1`/`gp1` (year-1 projection, printed as-is), `age1`
(Feb 1 of year 1), `stage` (D no NBA season yet, S one, V two or more), `cy1`
(career year in year 1), `bpm` (2-season, or None), `gp_last` (last season's
GP, or None), `pick` (NBA overall, None if undrafted), `age_rookie`, `bres`
(board residual, or None), `rate_mult` (manual injury hit from year 2 on)."""
import collections, functools, json, math, os, random
from . import shard
from .data import DATA_DIR

PARAMS = os.path.join(DATA_DIR, "progression-params.json")

Year = collections.namedtuple(
    "Year", "rate_p10 rate_p50 rate_p90 gp_mean p_active p_usable "
            "fp_p10 fp_p50 fp_p90 value")

ACTIVE = 20          # GP that counts as a season played
MIN_RATE = 4.0
MIN_SHOWN = 20       # fewer active paths than this and a year prints no rate band


@functools.lru_cache(maxsize=4)
def params(path=PARAMS):
    with open(path) as f:
        return json.load(f)


def project(player, years=20, n=1000, seed=1, p=None):
    """Per-year summaries, year 1 first. Paths share `seed`, so two players
    differ only by what differs about them"""
    p = p or params()
    runs = paths(player, years, n, seed, p)
    out = [_year_one(player, p)]
    for t in range(1, years):
        out.append(_summary([r[t] for r, _ in runs], [g[t] for _, g in runs], p))
    return out


_JOB = {}


def project_many(players, years=20, n=1000, seed=1):
    """`project` for each player, across processes"""
    _JOB.update(players=players, years=years, n=n, seed=seed, p=params())
    shard.retire()                 # workers fork with `_JOB` as it is now
    jobs = shard.chunks(len(players), shard.n_workers(None, len(players), floor=8))
    return [ys for part in shard.mapped(_project_chunk, jobs, len(jobs)) for ys in part]


def _project_chunk(job):
    start, count = job
    j = _JOB
    return [project(pl, j["years"], j["n"], j["seed"], j["p"])
            for pl in j["players"][start:start + count]]


def wrv(years):
    """Weighted remaining value: years 1-7 flat, then 5%/yr off (AGENTS.md)"""
    return sum(y.value * weight(t) for t, y in enumerate(years, 1))


def weight(t):
    return 1.0 if t <= 7 else 0.95 ** (t - 7)


def paths(player, years, n, seed=1, p=None):
    """n x (rates, gps) by year. A rate is None when the player didn't play"""
    p = p or params()
    s = _Sampler(p)
    rng = random.Random(seed)
    return [s.path(player, years, rng) for _ in range(n)]


def _year_one(player, p):
    r, g = player["rate1"], player["gp1"]
    active = g >= ACTIVE
    fp = r * g
    return Year(r, r, r, g, float(active), float(active and r >= p["usable"]),
                fp, fp, fp, g * max(0.0, r - p["wrv_rg"]))


def _summary(rates, gps, p):
    n = len(rates)
    act = sorted(r for r, g in zip(rates, gps) if r is not None and g >= ACTIVE)
    fp = sorted((r or 0.0) * g for r, g in zip(rates, gps))
    band = ((_q(act, .1), _q(act, .5), _q(act, .9)) if len(act) >= MIN_SHOWN
            else (None, None, None))
    return Year(band[0], band[1], band[2], sum(gps) / n, len(act) / n,
                sum(1 for r in act if r >= p["usable"]) / n,
                _q(fp, .1), _q(fp, .5), _q(fp, .9),
                sum(g * max(0.0, (r or 0.0) - p["wrv_rg"]) for r, g in zip(rates, gps)) / n)


def _q(xs, q):
    return xs[min(len(xs) - 1, int(q * len(xs)))]


class _Model:
    """A linear predictor over named terms: `x`, `x*y`, `x^2`"""

    def __init__(self, m):
        self.spec = []
        for t, c in zip(m["terms"], m["coef"]):
            x, _, y = t.replace("^2", "*" + t[:-2] if t.endswith("^2") else "").partition("*")
            self.spec.append((x, y or None, c))

    def __call__(self, v):
        s = 0.0
        for x, y, c in self.spec:
            s += c * v[x] * (v[y] if y else 1.0)
        return s


def _logistic(x):
    return 1.0 / (1.0 + math.exp(-x)) if x > -40 else 0.0


def _draw(q, rng):
    return q[int(rng.random() * len(q))]


class _Sampler:
    def __init__(self, p):
        self.p, self.k, v = p, p["knobs"], p["vet"]
        self.drift, self.exit = _Model(v["drift"]), _Model(v["exit"])
        self.scale, self.resq, self.zsd = _Model(v["scale"]), v["resq"], v["zsd"]
        self.star_ll = v.get("star_ll")
        self.resq_star, self.zsd_star = v.get("resq_star"), v.get("zsd_star")
        self.gp_ref = p.get("gp_ref", 60.0)
        self.beta = v["bpm_beta"]
        self.bpm_ref = _Model(v["bpm_ref"]) if "bpm_ref" in v else None
        self.gamma = p["board"]["gamma"]
        g = p["gp"]
        self.hurdle = _Model(g["hurdle"])
        self.lo, self.hi = math.log(MIN_RATE), math.log(1.1 * p["league_max"])
        r = p.get("rookie")
        self.rookie = r and {"drift": _Model(r["drift"]), "scale": _Model(r["scale"]),
                             "exit": _Model(r["exit"]), "miss": _Model(r["miss"]),
                             "resq": r["resq"], "zsd": r["zsd"]}

    def path(self, pl, years, rng):
        """Rookie-stage steps while the career is in its first two seasons,
        then vet steps on a latent level with season noise around it"""
        p, k = self.p, self.k
        rates, gps = [pl["rate1"]], [pl["gp1"]]
        bpm, dev = self._bpm(pl)
        bres = min(max(pl.get("bres") or 0.0, -p["board"]["clip"]), p["board"]["clip"])
        # year 2 chains straight off the GP projection: its own noise adds
        # little once shrunk by the chain's 0.3 slope
        st = _State(pl["age1"], pl["cy1"], pl["gp1"], pl.get("gp_last"))
        rookie_origin = pl["stage"] in ("D", "S") and self.rookie is not None
        young = k["young_mult_rookie"] if rookie_origin else k["young_mult"]
        if pl["stage"] == "D":
            sigma_u = k["sigma_u_rookie"]
        else:
            # the projection's own error, in proportion to how noisy his level is
            v1 = self._vars(pl["age1"], pl["rate1"], pl["gp1"], bpm, pl["cy1"])
            sigma_u = k["u_mult"] * self._sd(v1, pl["age1"], young)
        lr = math.log(pl["rate1"]) + sigma_u * _draw(self.resq, rng)
        t = 1
        if rookie_origin:
            t = self._rookie_steps(pl, st, lr, bres, years, rates, gps, rng)
            if st.alive and t < years:
                w = gps[-1] + gps[-2]
                lvl = ((rates[-1] * gps[-1] + rates[-2] * gps[-2]) / w if w
                       else (rates[-1] + rates[-2]) / 2)
                lr = math.log(lvl)
        tau = lr
        for t in range(t, years):
            if st.alive:
                v = self._vars(st.age, math.exp(tau), st.gpavg(), bpm, st.cy)
                st.alive = rng.random() >= _logistic(self.exit(v))
            if not st.alive:
                rates.append(None)
                gps.append(0.0)
                continue
            sd, phi = self._sd(v, st.age, young), self._phi(v["lL"])
            step = self.drift(v) + _at(self.beta, t) * dev - _at(self.gamma, t) * bres
            if t == 1 and pl.get("rate_mult"):
                step += math.log(pl["rate_mult"])
            tau = min(max(tau + step + sd * math.sqrt(phi) * self._eps(v["lL"], rng),
                          self.lo), self.hi)
            gp = self._gp_next(st.gp, st.age, rng)
            st.advance(gp)
            v2 = self._vars(st.age, math.exp(tau), gp, bpm, st.cy)
            sd2, phi2 = self._sd(v2, st.age, young), self._phi(v2["lL"])
            lr = tau + sd2 * math.sqrt((1 - phi2) / 2) * self._eps(v2["lL"], rng)
            rates.append(self._clip(lr))
            gps.append(gp)
        return rates, gps

    def _rookie_steps(self, pl, st, lr, bres, years, rates, gps, rng):
        """Career steps 1->2 and 2->3 on the observed log rate. Returns the
        next year index"""
        r, k = self.rookie, self.k
        pick = pl.get("pick") or 61
        ad = (pl.get("age_rookie") or pl["age1"] - (pl["cy1"] - 1)) - 20
        lp_exit = math.log(min(max(pick, 1), 61))
        lp_grow = math.log(min(max(pick, k["growth_pick_floor"]), 61))
        t = 1
        while st.cy < 3 and t < years:
            ve = _rookie_vars(lr, st.cy, ad, lp_exit, self._gp_feature(st.gp))
            if rng.random() < _logistic(r["exit"](ve)):
                st.alive = False
                return t
            vg = dict(ve, lp=lp_grow)
            sd = max(r["scale"](vg), 0.05) * r["zsd"] * k["smult_rookie"]
            step = r["drift"](vg) - _at(self.gamma, t) * bres
            if t == 1 and pl.get("rate_mult"):
                step += math.log(pl["rate_mult"])
            lr = min(max(lr + step + sd * _draw(r["resq"], rng), self.lo), self.hi)
            if rng.random() < _logistic(r["miss"](ve)):
                gp = _draw(self.p["gp"]["low_pool"], rng)
            else:
                gp = self._gp_mean_draw(st.gp, st.age, rng)
            st.advance(gp)
            rates.append(self._clip(lr))
            gps.append(gp)
            t += 1
        return t

    def _eps(self, lL, rng):
        """A one-step miss in SD units of the level's scale; stars draw from
        their own pool"""
        if self.star_ll is not None and lL >= self.star_ll:
            return _draw(self.resq_star, rng) * self.zsd_star
        return _draw(self.resq, rng) * self.zsd

    def _gp_feature(self, gp):
        """GP against the current season norm, the scale exit was fit on"""
        return (min(max(gp, 0.0), 82.0) - self.gp_ref) / 10

    def _vars(self, age, level, gp, bpm, cy):
        return {"1": 1.0, "a": age - 28, "a2": max(age - 31, 0.0),
                "ay": max(24 - age, 0.0), "a34": max(age - 34, 0.0),
                "lL": min(max(math.log(max(level, 1.0) / 30), LL_LO), LL_HI),
                "gp": self._gp_feature(gp), "bpm": bpm,
                "cy3": float(cy == 3), "cy4": float(cy == 4), "cy5": float(cy == 5)}

    def _clip(self, lr):
        return min(max(math.exp(lr), MIN_RATE), math.exp(self.hi))

    def _bpm(self, pl):
        """(BPM, its excess over the level-typical BPM). The drift's level
        terms already carry the typical BPM, so only the excess moves a path;
        a missing BPM is taken as typical"""
        if self.bpm_ref is None:
            return 0.0, 0.0
        typical = self.bpm_ref(self._vars(pl["age1"], pl["rate1"], 60.0, 0.0, 0))
        bpm = pl.get("bpm")
        bpm = typical if bpm is None else min(max(bpm, -8.0), 12.0)
        return bpm, bpm - typical

    def _sd(self, v, age, young):
        k = self.k
        sd = max(max(self.scale(v), 0.03) * self.zsd * k["smult"], k["sd_floor"])
        return sd * young if age <= 24 else sd

    def _phi(self, lL):
        k = self.k
        return min(k["phi0"] + k["phi1"] * max(lL, 0.0), 0.9)

    def _gp_next(self, gp_t, age, rng):
        """Next season's GP: a transient lost season, else the linear mean in
        this season's GP and age past 28 plus an empirical residual"""
        if rng.random() < _logistic(self.hurdle(_gp_vars(gp_t, age))):
            return _draw(self.p["gp"]["low_pool"], rng)
        return self._gp_mean_draw(gp_t, age, rng)

    def _gp_mean_draw(self, gp_t, age, rng):
        g = self.p["gp"]
        mean = g["c0"] + g["b_gp"] * gp_t + g["b_age"] * max(age - 28, 0.0)
        return min(max(mean + _draw(g["resq"], rng), ACTIVE), 82.0)


class _State:
    """Where a path stands: age and career year of the current season, its GP
    and the one before (exit reads their mean), and whether he's still in"""

    def __init__(self, age, cy, gp, gp_prev):
        self.age, self.cy, self.gp, self.gp_prev, self.alive = age, cy, gp, gp_prev, True

    def gpavg(self):
        return self.gp if self.gp_prev is None else (self.gp + self.gp_prev) / 2

    def advance(self, gp):
        self.age += 1
        self.cy += 1
        self.gp_prev, self.gp = self.gp, gp


def _rookie_vars(lr, c, ad, lp, gp):
    return {"1": 1.0, "c1": float(c == 1), "c2": float(c == 2),
            "lL": min(max(lr - math.log(30), -1.6), 0.7), "ad": ad, "lp": lp, "gp": gp}


def _at(schedule, t):
    return schedule[t - 1] if t <= len(schedule) else 0.0


def _gp_vars(gp, age):
    return {"1": 1.0, "gpraw": gp, "a28": max(age - 28, 0.0)}


LL_LO, LL_HI = -1.4, math.log(55 / 30)
