"""Daily-lineup simulator for Fleaflicker league 30579.

Answers "what is a player actually worth to us?" under the 9-slot daily cap,
on the real NBA schedule. Stdlib only (no scipy/numpy).

    python3 sim.py [report ...]          # any of REPORTS; default `calibration`
    python3 -m unittest test_sim         # invariants the README's claims rest on
    python3 fetch_data.py [pool]         # rebuild the data files

    python3 fetch_data.py roster 160941            # any team -> a roster file
    python3 sim.py --roster roster-160941-2025-26.json players

Every table in README.md is one of REPORTS. Add the report before the table.
`--roster` works for every one of them: reports build their roster with `basis()`,
which pads whatever is loaded to 38 bodies, because R and every per-player win
figure move with the body COUNT and no two live rosters share one.

The CLI only knows fixed report names. For an actual trade under negotiation,
import instead -- this is the supported path and `trades` step 5 depends on it:

    import sim
    full = sim.basis()                   # or sim.basis("roster-160941-2025-26.json")
    base = sim.run(full)
    deal = sim.run(sim.swap(full, ["Jalen Suggs"], [sim.star(48, 70, ("C",))]))
    sim.wins(deal, base)                 # +wins over 20 matchups
    sim.breakeven(full, ["Jalen Suggs", "Coby White"], gp=70, elig=("C",))

Roster JSON format (list of dicts) -- LAST SEASON as it happened, written by
`fetch_data.roster_rows`, which is the schema of record:
    {"n": name, "tm": FF pro-team abbrev, "avg": FPts/G, "tot": season FPts,
     "gp": games played, "posLabel": display position,
     "elig": ["PG","SG"] | ["SF","PF"] | ["C"] | ["C","PF"] | ...,
     "surprise": optional per-player share of absence BLOCKS started into}

`our_roster` projects `gp` forward for every player, fills the `avg` of a missed
season from the pool, and overrides `avg` for the names in `PROJECTED_RATE`;
`projected=False` gives the raw season, which the calibration is measured against.
"""
import json, os, random, statistics, math, collections, sys
import csv, datetime, functools, glob, re, unicodedata

# ONE season constant for this directory, and it lives in the file that WRITES
# the data (see fetch_data.SEASON). Every filename below derives from it.
from fetch_data import SEASON, SEASON_TAG, TEAM

HERE = os.path.dirname(os.path.abspath(__file__))
SEASON_STR = str(SEASON)          # the pool keys seasons as strings

# 9 starters. Verified against FetchLeagueRules rosterPositions.
SLOTS = [("PG", {"PG"}), ("SG", {"SG"}), ("G", {"PG", "SG"}),
         ("SF", {"SF"}), ("PF", {"PF"}), ("F", {"SF", "PF"}), ("C", {"C"}),
         ("ANY", {"PG", "SG", "SF", "PF", "C"}),
         ("ANY", {"PG", "SG", "SF", "PF", "C"})]

# Fleaflicker abbrev -> ESPN abbrev (schedule file uses ESPN's)
FF2ESPN = {"GSW": "GS", "NOP": "NO", "WAS": "WSH", "UTA": "UTAH",
           "NYK": "NY", "SAS": "SA", "BRK": "BKN"}


def _load(name):
    with open(os.path.join(HERE, name)) as f:
        return json.load(f)


NIGHTS = [(d, set(tms)) for d, tms in sorted(_load(
    "nba-schedule-%s.json" % SEASON_TAG)["daymap"].items())]

PERIODS = _load("league-%s.json" % SEASON_TAG)["periods"]  # eligibleSchedulePeriods
SCORES = collections.defaultdict(dict)             # team -> period ordinal -> PF
FACED = collections.defaultdict(dict)              # team -> period -> opponent
for _p in PERIODS:
    for _a, _av, _h, _hv in _p["games"]:
        SCORES[_a][_p["ordinal"]] = _av
        SCORES[_h][_p["ordinal"]] = _hv
        FACED[_a][_p["ordinal"]], FACED[_h][_p["ordinal"]] = _h, _a
US = "Bathroom club"

# ONE basis for every PF figure in this study: the periods that count toward the
# standings (1-20 here). Periods 21-23 are the playoff/consolation bracket, and
# the standings' PF column excludes them -- calibrating on a 23-period total and
# comparing it to standings PF is a ~15% error.
SCORED = [i for i, p in enumerate(PERIODS) if "regular" in p["kinds"]]
WEEKS = len(SCORED)


def _week_of(date):
    """Index into SCORED for an ET date, or None if the date scores nothing.

    Do NOT bucket nights evenly. Real periods run 4-7 nights and 28-56 NBA
    games: the Cup knockout week has 28, the All-Star week 31, a full week 52-56.
    That spread is a first-order source of weekly variance and an even split
    deletes it. The fantasy season also ENDS before the NBA's -- 34 nights and
    22% of the NBA's games fall outside the scored periods entirely.
    """
    for w, i in enumerate(SCORED):
        if PERIODS[i]["start"] <= date <= PERIODS[i]["end"]:
            return w
    return None


WEEK_OF = [_week_of(d) for d, _ in NIGHTS]
SCORING_NIGHTS = [i for i, w in enumerate(WEEK_OF) if w is not None]

# Real weekly scores on that same basis. OURS is our operating point; MARGINS
# pools our score minus each other team's score in the SAME period, which is the
# distribution a matchup is actually decided on.
_P = [PERIODS[i]["ordinal"] for i in SCORED]
OURS = [SCORES[US][p] for p in _P if p in SCORES[US]]
# Grouped by period as well as pooled: the 11 margins in a period share OUR score
# for that period, so they are one cluster, not 11 draws. Any interval on them has
# to resample the period (see pf_per_win_band).
MARGINS_BY_WEEK = [[SCORES[US][p] - s[p] for t, s in SCORES.items()
                    if t != US and p in s]
                   for p in _P if p in SCORES[US]]
MARGINS = [m for wk in MARGINS_BY_WEEK for m in wk]
REAL_WK_MEAN, REAL_WK_SD = statistics.mean(OURS), statistics.stdev(OURS)
REAL_MATCHUPS = len(OURS)


def lineup(avail):
    """avail: [(fpts, eligset, key)]. Max-weight assignment into the 9 slots.

    Exact: capacities are 1 and players are added in descending value, so
    greedy placement with Kuhn augmentation cannot be improved on.
    """
    assign = [None] * len(SLOTS)
    for pi in sorted(range(len(avail)), key=lambda i: -avail[i][0]):
        if all(a is not None for a in assign):
            break
        seen = set()

        def place(x):
            for si, (_, elig) in enumerate(SLOTS):
                if si in seen or not (avail[x][1] & elig):
                    continue
                seen.add(si)
                if assign[si] is None or place(assign[si]):
                    assign[si] = x
                    return True
            return False
        place(pi)
    used = [a for a in assign if a is not None]
    return (sum(avail[a][0] for a in used), len(used),
            [avail[a][2] for a in used])


def _availability(p, rng, bursty):
    """Night indices this player actually suits up for."""
    tm = FF2ESPN.get(p["tm"], p["tm"])
    idxs = [i for i, (_, tms) in enumerate(NIGHTS) if tm in tms]
    # Unsigned in the NBA (`proTeamAbbreviation` "FA") or a team the schedule does not
    # know: he suits up for nothing. Return empty rather than falling through to
    # `tg = 1` against an empty `idxs`, which raised an opaque ValueError and made
    # `--roster their.json` crash on any counterparty holding an FA player.
    if not idxs:
        return set()
    tg = len(idxs)
    play = min(p["gp"], tg)
    if not bursty:
        return set(rng.sample(idxs, play))
    miss, out = tg - play, set()          # contiguous IL blocks, mean ~9 games
    while miss > 0 and len(out) < tg:
        blk = max(1, min(int(rng.gauss(9, 6)) or 1, miss))
        # place CIRCULARLY. Constraining starts to [0, tg-blk] makes mid-season
        # games ~blk x likelier to be covered than edge games, which inflates
        # October/April availability ~15pts and spuriously synchronises
        # absences across players.
        s = rng.randrange(0, tg)
        out.update((s + j) % tg for j in range(blk))
        miss = (tg - play) - len(out)
    return {idxs[j] for j in range(tg) if j not in out}


def _onsets(idxs, played):
    """Absence nights that BEGIN a contiguous absence run, from `idxs`.

    The only nights a scratch can surprise you on. `idxs` is the player's own
    team-game nights in order; from the second night of a block on he is on the
    public injury report and you simply do not start him. Sampling every absence
    night instead scales the lock-in by the mean block length -- `absence_blocks`
    measures that factor on the roster in hand.

    CIRCULAR, because `_availability` places blocks circularly: a block that wraps
    the end of the season is one block. `idxs[j - 1]` at j=0 is the last night by
    construction. Scanning strictly left-to-right split those in two -- ~26% of
    player-seasons -- and over-counted onsets ~9%.
    """
    if not played:
        return idxs[:1]        # never suits up: one block, and opening night is it
    return [i for j, i in enumerate(idxs)
            if i not in played and idxs[j - 1] in played]


def absence_blocks(roster, seeds=40, seed0=101):
    """-> {nights, blocks, mean_block}: how absences ARRIVE on this roster.

    `mean_block` is the whole of the lock-in correction: drawing the surprise from
    every absence night rather than each block's first night over-states the
    penalty by exactly this factor. It is a property of the roster's projected GP,
    so it has to be measured on the roster in hand -- hard-coding it is how a
    stale triple survived three revisions under a heading naming a roster that
    never produced it. Uses the same `_availability`/`_onsets` pair `season()`
    does, so the factor cannot drift from the model that applies it.
    """
    nights = blocks = 0
    for s in range(seeds):
        rng = random.Random(seed0 + s)
        for p in roster:
            played = _availability(p, rng, True)
            tm = FF2ESPN.get(p["tm"], p["tm"])
            idxs = [i for i, (_, tms) in enumerate(NIGHTS) if tm in tms]
            nights += len(idxs) - len(played)
            blocks += len(_onsets(idxs, played))
    return {"nights": nights / seeds, "blocks": blocks / seeds,
            "mean_block": nights / blocks if blocks else 0.0}


def season(roster, seed, bursty=False, surprise=0.0):
    """`surprise`: share of a player's absence BLOCKS he is started into.

    Lineups lock before tip, so a late scratch does not free the slot -- you have
    started a player who scores 0 and cannot refill. Everything else here assumes
    perfect foreknowledge of who plays, which is the study's one structural
    over-statement of a fragile player's worth.

    Only meaningful with `bursty=True`: independent per-night absences are their
    own onsets, so the correction is a near no-op against a draw that is not how
    injuries arrive.
    """
    rng = random.Random(seed)
    sched = [_availability(p, rng, bursty) for p in roster]
    ghosts = []
    for k, p in enumerate(roster):
        q = p.get("surprise", surprise)     # per-player override
        tm = FF2ESPN.get(p["tm"], p["tm"])
        idxs = [i for i, (_, tms) in enumerate(NIGHTS) if tm in tms]
        onsets = _onsets(idxs, sched[k])
        # Independent per block, NOT round(q * blocks): a typical player has 2-3
        # absence blocks, so the deterministic count floors to zero and a 10%
        # rate becomes 0% for most of the roster.
        g = {i for i in onsets if rng.random() < q} if q else set()
        ghosts.append(g)
        sched[k] |= g                      # started, but will score nothing
    weeks = [0.0] * WEEKS
    starts, pts = collections.Counter(), collections.Counter()
    by_night = []
    for i in SCORING_NIGHTS:
        tms = NIGHTS[i][1]
        av = [(p["avg"], set(p["elig"]), p["n"], i not in ghosts[k])
              for k, p in enumerate(roster) if i in sched[k]]
        if not av:
            by_night.append((len(tms) // 2, 0, 0, 0.0))
            continue
        _, filled, who = lineup(av)
        scored = {a[2]: a[0] if a[3] else 0.0 for a in av}
        total = sum(scored[w] for w in who)
        weeks[WEEK_OF[i]] += total
        for w in who:
            starts[w] += 1
            pts[w] += scored[w]
        by_night.append((len(tms) // 2, len(av), filled, total))
    return weeks, starts, pts, by_night


TRIALS = 200              # deltas are stable to +-0.02 wins from ~50 up now that
                          # swap() preserves common random numbers.
PLAYER_BLOCKS = 3         # independent seed blocks behind every per-player row.
                          # +-0.02 on a delta is fine for a scenario and far too
                          # coarse for an ORDERING -- see player_wins().


def run(roster, trials=TRIALS, bursty=False, seed0=101, surprise=0.0):
    """-> dict(pf, wk_mean, wk_sd, cv, starts, pts, by_night)"""
    allweeks, starts, pts = [], collections.Counter(), collections.Counter()
    agg = collections.defaultdict(lambda: [0, 0, 0.0, 0])
    for t in range(trials):
        w, st, pt, bn = season(roster, seed0 + t, bursty, surprise)
        allweeks += w
        starts.update(st)
        pts.update(pt)
        for g, na, f, p in bn:
            a = agg[g]
            a[0] += na; a[1] += f; a[2] += p; a[3] += 1
    m, sd = statistics.mean(allweeks), statistics.stdev(allweeks)
    return {
        "pf": m * WEEKS, "wk_mean": m, "wk_sd": sd, "cv": sd / m,
        "starts": {k: v / trials for k, v in starts.items()},
        "pts": {k: v / trials for k, v in pts.items()},
        "by_night": {g: (v[0] / v[3], v[1] / v[3], v[2] / v[3], v[3] / trials)
                     for g, v in agg.items()},
    }


# ------------------------------------------------------- PF -> wins conversion

MARGIN_MEAN, MARGIN_SD = statistics.mean(MARGINS), statistics.stdev(MARGINS)


def _phi(z):
    return math.exp(-z * z / 2) / math.sqrt(2 * math.pi)


def _cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def margin_pwin(shift=0.0):
    """P(we win a matchup) if every weekly score moves by `shift`."""
    return _cdf((MARGIN_MEAN + shift) / MARGIN_SD)


# 1 win per this many season PF. Measured off the real MARGIN distribution, NOT by
# adding our sd and the opponent's in quadrature: the two are correlated rho = 0.67
# through the shared NBA calendar, so independence overstates the margin sd 1.74x
# and gives 1,030. Treat as +-14% (period-clustered bootstrap: 595 [518, 679]);
# the corroborations in README are on the SAME score matrix, not independent.
PF_PER_WIN = WEEKS * MARGIN_SD / _phi(MARGIN_MEAN / MARGIN_SD) / REAL_MATCHUPS


def pf_per_win_band(n=2000, seed=7, lo=0.025, hi=0.975):
    """(lo, hi) for PF_PER_WIN, bootstrapped CLUSTERED ON PERIOD.

    Printed, not asserted: `team-eval` prices every verdict through this constant
    and quotes the band, so the band has to be re-derivable here. The corroborating
    figures in README are other estimators on the SAME score matrix, so they are
    not independent of it and do not widen it.
    """
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        ms = []
        for _ in MARGINS_BY_WEEK:
            ms += rng.choice(MARGINS_BY_WEEK)
        mu, sd = statistics.mean(ms), statistics.stdev(ms)
        out.append(WEEKS * sd / _phi(mu / sd) / REAL_MATCHUPS)
    out.sort()
    return out[int(lo * n)], out[int(hi * n)]


def wins(res, baseline, games=None):
    """Extra wins per `games` matchups vs a baseline run().

    Converts DELTA PF at our real operating point, not by running a normal CDF on
    the sim's own weekly mean: the sim's absolute level is a calibration artifact,
    and pwin() out in the tail compresses deltas non-uniformly, which distorts the
    ordering rather than just the scale.
    """
    games = REAL_MATCHUPS if games is None else games
    return (res["pf"] - baseline["pf"]) / PF_PER_WIN * (games / REAL_MATCHUPS)


# No variance_wins(). Measured across all 15 scenarios and every `durability` trade
# shape: max |effect| 0.08 wins, always inside the noise on the PF column.

# ---------------------------------------------------------------- our roster

# RATES ONLY. GP comes from `project_gp` for every player on every roster, which
# is what makes the regression symmetric across both sides of a trade instead of
# something to remember.
#
# NO-USABLE-SAMPLE ONLY, and never an age haircut: a haircut on a rate the player
# actually posted is an aging term, `team-eval` forbids one inside a win delta,
# and it made the eval tables disagree with `sim.py players` on who was better.
# Age belongs in BASE, where the boards already charge for it.
PROJECTED_RATE = {"Kyrie Irving": 38.0,      # 0 GP in '25-26; 39.6 in '24-25
                  "Fred VanVleet": 29.0,     # 0 GP in '25-26; 30.3 in '24-25
                  "Khaman Maluach": 16.0,    # 8.2 as a rookie, starting C now
                  "DaRon Holmes": 14.0}      # 6.8 over 25 games

# The 10 slots that take us 28 -> 38 in Sept '26: 3 rookie picks + 7 FA auction.
# Rookies rarely clear 20 FPts; the auction tail is the ~450th man in the NBA.
EXPANSION = [
    {"n": "RK0", "tm": "SAC", "avg": 18.0, "gp": 60, "elig": ["SF", "PF"]},
    {"n": "RK1", "tm": "UTA", "avg": 13.0, "gp": 60, "elig": ["PG", "SG"]},
    {"n": "RK2", "tm": "POR", "avg": 10.0, "gp": 60, "elig": ["C"]},
    {"n": "FA0", "tm": "MIN", "avg": 14.0, "gp": 55, "elig": ["PG", "SG"]},
    {"n": "FA1", "tm": "OKC", "avg": 13.0, "gp": 55, "elig": ["C"]},
    {"n": "FA2", "tm": "BOS", "avg": 12.0, "gp": 55, "elig": ["SF", "PF"]},
    {"n": "FA3", "tm": "CLE", "avg": 11.0, "gp": 55, "elig": ["PG", "SG"]},
    {"n": "FA4", "tm": "ATL", "avg": 10.0, "gp": 55, "elig": ["SF", "PF"]},
    {"n": "FA5", "tm": "SAS", "avg": 9.0, "gp": 55, "elig": ["C"]},
    {"n": "FA6", "tm": "NYK", "avg": 8.0, "gp": 55, "elig": ["PG", "SG"]},
]
# A shipped-out player leaves a hole nothing fills — the pool is empty at 38.
DEAD = {"tm": "MIA", "avg": 6.0, "gp": 40, "elig": ["PG", "SG"]}

# Slot groups, for padding a short roster without inventing a positional hole.
PAD_ELIG = (["PG", "SG"], ["SF", "PF"], ["C"])


# Ours, written by the SAME command as any counterparty's (`fetch_data.py roster
# 161025`), so re-fetching it after a trade executes lands on the file that is
# actually read. `--roster PATH` overrides it.
ROSTER = "roster-%d-%s.json" % (TEAM, SEASON_TAG)


def our_roster(path=None, projected=True):
    """Whichever roster is loaded -- ours by default, a counterparty's with
    `--roster`. Every report goes through here, so `--roster their.json players`
    prices their team on exactly our basis.

    `projected=True` (default) is the '26-27 basis: `project_gp` for EVERY player,
    a pool rate for anyone who missed the season, and a hand-typed rate for the
    handful in `PROJECTED_RATE`. Doing it here rather than per-caller is the point
    -- it makes "regress both sides identically" structural rather than a rule to
    remember, and only one side of a trade is ever ours.

    `projected=False` is the season that actually happened, and the 1.006
    calibration depends on it staying raw.
    """
    out = []
    for p in _load(path or ROSTER):
        q = dict(p)
        if projected:
            # A missed season reads 0.0 -- `seasonAverage` is absent, not zero. Take
            # his last real one off the pool, because PROJECTED_RATE holds OUR names
            # and nothing was ever going to hand-type a counterparty's roster: this
            # is the half of "both sides regress identically" that GP already had.
            s = pool_seasons(p["n"]) if not q["avg"] else {}
            q["avg"] = PROJECTED_RATE.get(
                p["n"], s[max(s)][0] if s else q["avg"])
            q["gp"] = round(project_gp(p["n"], gp=p["gp"], rate=q["avg"]))
        if not q["elig"]:      # pre-`roster_rows` files left a 0-GP row with none
            q["elig"] = ["PG", "SG"]
        out.append(q)
    return out


# ------------------------------------------------- board rank <-> scoring rate

POOL = "players-%s.json" % SEASON_TAG        # fetch_data.py pool

BOARD_DIR = os.path.join(HERE, os.pardir, "dizzle-dynasty")
BOARD_SUFFIX = "dynasty-ranks-points.csv"    # points league; 9cat is cross-check
_MONTHS = ("january february march april may june july august september october"
           " november december").split()


def newest_board(d=None):
    """Path to the newest month-stamped points dynasty snapshot in `d`.

    NEVER hardcode a month: `dizzle-dynasty` re-snapshots under a new one and the
    old file stays put, so a hardcoded name goes stale in place while every rank
    in the study keeps resolving. Raises rather than falling back to a stale
    board -- this is the only rank -> rate bridge here.
    """
    found = []
    for p in glob.glob(os.path.join(d or BOARD_DIR, "*-" + BOARD_SUFFIX)):
        m = re.match(r"([a-z]+)-(\d{4})-", os.path.basename(p))
        if m and m.group(1) in _MONTHS:
            found.append(((int(m.group(2)), _MONTHS.index(m.group(1))), p))
    if not found:
        raise FileNotFoundError("no <month>-<year>-%s in %s"
                                % (BOARD_SUFFIX, d or BOARD_DIR))
    return max(found)[1]


def _key(name):
    """Match names across two sources that punctuate and accent differently."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", s.lower().replace(".", "")
               .replace("'", "").replace("-", " "))
    return " ".join(s.split())


@functools.lru_cache(maxsize=1)
def pool():
    """Read-only; cached because `our_roster` now projects GP off it, and that runs
    once per scenario."""
    return _load(POOL)


@functools.lru_cache(maxsize=1)
def _pool_by_key():
    return {_key(n): v for n, v in pool().items()}


def pool_seasons(name):
    """`{season: [FPts/G, GP]}` for `name`, or `{}`.

    Falls back to the NORMALISED key, because the pool is joined on a name and a
    roster file that spells one without its accents is not a typo the caller can
    see. The exact name still wins, so two players who normalise alike cannot
    swap rows.
    """
    v = pool().get(name) or _pool_by_key().get(_key(name))
    return (v or {}).get("seasons") or {}


def board_rates(season=SEASON_STR, min_gp=30):
    """[(board rank, FPts/G)] for every player on the points dynasty board we can
    price. THE bridge the framework otherwise asserts: rank is what a trade costs
    and rate is what it pays, and nothing else here connects them. Without it you
    cannot tell whether a break-even is purchasable at any price.

    `min_gp` guards the rate: a 13-game sample tops the rate sort and would say a
    rank-418 player supplies 32 FPts/G.
    """
    rate = {_key(n): v["seasons"][season][0] for n, v in pool().items()
            if season in v["seasons"] and v["seasons"][season][1] >= min_gp}
    out = []
    with open(newest_board(), newline="") as f:
        for row in csv.DictReader(f):
            r, k = row.get("#"), _key(row.get("Player") or "")
            if r and r.isdigit() and k in rate:
                out.append((int(r), rate[k]))
    return sorted(out)


# -------------------------------------------------------------- expected GP
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
    mx = statistics.mean([x for x, _ in xy])
    my = statistics.mean([y for _, y in xy])
    b = (sum((x - mx) * (y - my) for x, y in xy)
         / sum((x - mx) ** 2 for x, _ in xy))
    return my - b * mx, b, len(xy)


def gp_rows(min_rate=GP_MIN_RATE, min_hist=1):
    """One row per (player, predicted season): {name, season, y, hist, seasons, age}.

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


def _ols(rows, feat, ys):
    """Least squares with an intercept, via the normal equations. Stdlib only, and
    the designs here are 1-3 columns, so conditioning is not a concern."""
    X = [[1.0] + list(feat(r)) for r in rows]
    k = len(X[0])
    A = [[sum(x[i] * x[j] for x in X) for j in range(k)]
         + [sum(x[i] * y for x, y in zip(X, ys))] for i in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(A[r][c]))
        A[c], A[p] = A[p], A[c]
        if abs(A[c][c]) < 1e-9:
            return None
        for r in range(k):
            if r != c:
                f = A[r][c] / A[c][c]
                A[r] = [a - f * b for a, b in zip(A[r], A[c])]
    return [A[i][k] / A[i][i] for i in range(k)]


def _avg(xs):
    return sum(xs) / len(xs)


# Every model is scored on the SAME rows, so a k-season model averages whatever
# history a row has up to k. That is also what a real projection must do -- most
# players do not have five prior seasons.
# Where the rate term stops buying games. Empirical mean next-season GP by last
# season's rate is CONCAVE and PEAKS around 30-40, so a linear term keeps paying past
# the peak and over-projects the stars every headline table rests on (+6.6 GP of
# bias at rate>=45). Knots 20-35 all sit inside each other's noise; 30 is the CV
# optimum and the only one that beats the unknotted form on a clustered bootstrap.
GP_KNOT = 30.0

# Six models, and between them they make every argument this section makes: the
# flat prior one season must beat, that season, whether more history buys
# anything, whether age does, and whether the knot earns its place. Richer
# combinations were scored; none beat `gp1`, and carrying them only invited
# quoting a gap smaller than its own uncertainty.
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
        se = [float("nan")] * len(rows)
        for f in range(folds):
            tr = [r for r in rows if fold[r["name"]] != f]
            beta = _ols(tr, feat, [r["y"] for r in tr]) if tr else None
            if beta is None:
                continue
            for i, r in enumerate(rows):
                if fold[r["name"]] == f:
                    p = beta[0] + sum(b * x for b, x in zip(beta[1:], feat(r)))
                    se[i] = (p - r["y"]) ** 2
        out[name] = se
    return out


def _rmse(se):
    v = [x for x in se if x == x]
    return math.sqrt(sum(v) / len(v)) if v else float("nan")


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

    This is the uncertainty a gap between two models has to be judged against. The
    `noise` column this replaced was the sd across FOLD SHUFFLES, holding the 286
    players fixed -- reproducibility of the split, not sampling error over the
    population, and ~0.01 against a real ~0.14. Ranking models on it turned
    0.15-RMSE gaps into the finding "more seasons is WORSE" when every one of those
    intervals straddles zero.

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
    out = {}
    for m in models:
        d = sorted(_rmse([se[m][i] for i in idx]) - _rmse([se[ref][i] for i in idx])
                   for idx in picks)
        out[m] = {"rmse": _rmse(se[m]), "delta": _rmse(se[m]) - _rmse(se[ref]),
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
    a, b, c = _ols(rows, GP_MODELS["gp1+knot"], [r["y"] for r in rows])
    return a, b, c


def project_gp(name, season=SEASON_STR, gp=None, rate=None):
    """Expected GP next season. THE projection this study uses, for every player on
    every roster -- ours and a counterparty's, through the same `our_roster`.

    Reads the player's most recent pool season, which is why a player who missed
    all of `season` is handled without being special-cased: his last season that
    exists is the one used.

    `rate` OVERRIDES the pool when given. That is what `PROJECTED_RATE` is for,
    and treating it as a mere fallback made it a silent no-op for every player
    the pool has seen -- i.e. for all of ours. `gp` is a FALLBACK only, used for
    a player the pool has never seen: the pool's GP is what this model was
    fitted on, and a roster file's GP is the same season rounded differently.
    RAISES on a name the pool does not have and you gave no fallback for, rather
    than returning None: the None went on to `round()` a few frames away, so a
    misspelling surfaced as a TypeError about NoneType, or not at all.
    """
    s = pool_seasons(name)
    if s:
        pool_rate, gp = s.get(season) or s[max(s)]
        rate = pool_rate if rate is None else rate
    if gp is None or rate is None:
        raise KeyError("no pool season for %r -- pass gp= and rate=, or check the"
                       " spelling against %s" % (name, POOL))
    a, b, c = gp_model()
    return a + b * gp + c * min(rate, GP_KNOT)


# THE schedule every synthetic body is priced on. Which NBA team a body sits on
# moves its added PF by 189 across the 30 schedules (mean 1516, sd 57, OKC +1614
# to DET +1425) = ~3.6 rate points, so a study that mixes teams charges a
# schedule handicap and books it as body count. LAC is the schedule closest to the
# 30-team mean; the old default LAL sat +1.2 sd favourable, which ran every
# break-even ~1.3 rate points low. Change it in ONE place or not at all.
SIM_TM = "LAC"

# For a MULTI-body row, reusing SIM_TM three times would swap a schedule
# handicap for a stacking one: three bodies sharing one team's nights cannibalise
# each other's slots, worth ~120 PF over three. So spread them, but only over
# schedules that are themselves near the 30-team mean (LAC -10, TOR -9, MEM +16
# PF against mean 1519). Mean of the trio 1518, i.e. no net handicap either way.
SIM_TMS = ("LAC", "TOR", "MEM")


def star(rate, gp=68, elig=("SF", "PF"), tm=SIM_TM, n="STAR"):
    return {"n": n, "tm": tm, "avg": float(rate), "gp": gp, "elig": list(elig)}


def swap(roster, out_names, adds, dead=None):
    """Trade `out_names` away for `adds`; any shortfall refills at `dead` grade.

    Replaces IN PLACE. Roster order drives the per-season rng draw order, so
    appending instead would reshuffle every untouched player's availability and
    turn a common-random-numbers comparison into an independent one -- several
    times the trials for the same precision.

    `dead` is the grade the bodies you ship out come BACK at, and it is the
    single biggest assumption under every break-even here. Price it by what is
    actually claimable at the moment the slot must be FIELDED, which is not the
    moment the trade is agreed.
    """
    have = {p["n"] for p in roster}
    missing = [n for n in out_names if n not in have]
    if missing:
        # Skipping what it could not find returned the incoming star ADDED with
        # nobody removed -- a scenario several hundred PF too high that still
        # printed. Our own names against a counterparty's file do exactly that.
        raise KeyError("not on this roster: %s" % ", ".join(missing))
    fill = list(adds) + [dict(dead or DEAD, n="DEAD%d" % i)
                         for i in range(max(0, len(out_names) - len(adds)))]
    out = []
    for p in roster:
        if p["n"] in out_names and fill:
            out.append(fill.pop(0))
        elif p["n"] not in out_names:
            out.append(p)
    return out + fill




def pad(roster, n=38):
    """`roster` topped up to `n` bodies at the grades every team fills to 38 with.

    THE common basis for comparing two teams. `R` and every per-player win figure
    are properties of a roster's body COUNT before they are properties of its
    players, and no two live rosters share one (26-28 today, 38 from Sept '26), so
    a counterparty measured on his live bodies is not comparable to us on ours --
    his R lands ~7 rate points high and every player he owns reads cheap.

    Appends, so the real bodies keep their order and therefore their rng draws
    (see thin()). `pad(our_roster(), 38)` IS `our_roster() + EXPANSION`, which is
    what every 38-man figure in the README is measured on. Past those 10 fixed
    slots the grade is the bottom of the auction, spread over slot groups and NBA
    schedules so padding invents neither a positional hole nor a stacking one.
    """
    out = list(roster)
    for i in range(max(0, n - len(out))):
        if i < len(EXPANSION):
            out.append(dict(EXPANSION[i]))
        else:
            out.append(dict(EXPANSION[-1], n="PAD%d" % i,
                            tm=EXPANSION[i % len(EXPANSION)]["tm"],
                            elig=list(PAD_ELIG[i % len(PAD_ELIG)])))
    return out


GROUPS = {"guard": ("PG", "SG"), "forward": ("SF", "PF"), "centre": ("C",)}


def pure_bodies(roster, elig):
    """Bodies eligible ONLY inside `elig` -- the crowding that lifts that group's
    `R`. A dual-eligible body relieves crowding, so it counts toward no group."""
    return sum(1 for p in roster if set(p["elig"]) <= set(elig))


def group_slots(elig):
    """Starting slots a body pure to `elig` can fill, off `SLOTS` rather than
    counted by hand: the two ANY slots make guards 5 and centres 3, and a hand
    count keeps missing them."""
    return sum(1 for _, e in SLOTS if e & set(elig))


def basis(path=None):
    """THE roster every report measures on: whoever is loaded, padded to 38.

    A body COUNT, not `+ EXPANSION`: that is 10 bodies, so it lands on 38 only for
    our own 28 and quietly measured a 26-man counterparty at 36.
    """
    return pad(our_roster(path))


def thin(roster, n):
    """Best `n` bodies by (rate-17)*gp, IN THE ORIGINAL ORDER.

    Returning them sorted would be a different measurement of the same roster:
    order drives the per-season rng draw order, so `thin(r, len(r))` would not
    reproduce `r`.
    """
    keep = set(sorted(range(len(roster)), key=lambda i:
                      -(roster[i]["avg"] - 17) * roster[i]["gp"])[:n])
    return [p for i, p in enumerate(roster) if i in keep]


def breakeven(roster, out_names, gp=68, elig=("SF", "PF"), tm=SIM_TM,
              lo=20.0, hi=90.0, tol=0.15, dead=None):
    """Incoming rate at which trading `out_names` away is PF-neutral.

    GP and eligibility are ARGUMENTS, not incidentals: the break-even for a
    65-GP centre is several points above the one for a 68-GP forward, and a
    reader who compares a real player's rate to the wrong row gets the sign of
    the deal wrong. `dead` is the backfill grade -- see swap().
    """
    base = run(roster)["pf"]

    def d(rate):
        return run(swap(roster, out_names,
                        [star(rate, gp, elig, tm)], dead))["pf"] - base
    while hi - lo > tol:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if d(mid) < 0 else (lo, mid)
    return (lo + hi) / 2


def player_wins(roster, names, blocks=3, trials=TRIALS, seed0=101, R=None):
    """name -> (mean wins lost if swapped for a replacement 68-GP forward,
    sd across `blocks` independent seed blocks).

    The sd is not decoration. Common random numbers make ONE block's delta stable
    to ~0.02 wins, which is fine for a scenario but not for an ORDERING: the top
    rows here sit ~0.01 wins apart, so a single block picks the winner of the top
    pair essentially at random -- and picking one and publishing "X moved 4th to
    1st" is how a seed became a finding. Compare any gap to these sds first.
    """
    R = replacement(roster)[0] if R is None else R
    seeds = [seed0 + b * trials for b in range(blocks)]
    base = [run(roster, trials=trials, seed0=s) for s in seeds]
    out = {}
    for n in names:
        w = [wins(base[i], run(swap(roster, [n], [star(R, 68)]),
                               trials=trials, seed0=s))
             for i, s in enumerate(seeds)]
        out[n] = (statistics.mean(w),
                  statistics.stdev(w) if len(w) > 1 else 0.0)
    return out


def replacement(roster, gp=68, elig=("SF", "PF"), rates=(30, 40, 50, 65)):
    """-> (R, c): value of an added body is ~ c * (rate - R) * gp PF.

    R is the x-INTERCEPT of a line fitted over `rates`. It is not the rate at
    which a body is worth zero -- no such rate exists, because adding a body can
    never LOWER your PF. Value in rate is convex, so this line goes negative below
    R while the truth stays positive: that, not noise, is why the formula cannot
    be used on sub-25 players. Two different `rates` grids give two different
    x-intercepts; quote the one from the grid you fitted.
    """
    base = run(roster)["pf"]
    v = [run(roster + [star(r, gp, elig, SIM_TM, "ADD")])["pf"] - base
         for r in rates]
    mx, mv = statistics.mean(rates), statistics.mean(v)
    a = (sum((r - mx) * (y - mv) for r, y in zip(rates, v))
         / sum((r - mx) ** 2 for r in rates))
    return mx - mv / a, a / gp


# ------------------------------------------------------------------- reports

def report_calibration():
    print("NBA calendar: %d nights, %d games, mean %.2f/night"
          % (len(NIGHTS), sum(len(t) for _, t in NIGHTS) // 2,
             sum(len(t) for _, t in NIGHTS) / 2 / len(NIGHTS)))
    g = collections.Counter()
    for i in SCORING_NIGHTS:
        g[WEEK_OF[i]] += len(NIGHTS[i][1]) // 2
    gv = sorted(g.values())
    print("fantasy season: %d scored periods over %d of those nights (%d games)."
          % (WEEKS, len(SCORING_NIGHTS), sum(gv)))
    print("  games per period %d-%d, mean %.1f, CV %.1f%%  <- NOT flat"
          % (gv[0], gv[-1], statistics.mean(gv),
             100 * statistics.stdev(gv) / statistics.mean(gv)))
    print("  %d NBA nights fall after the last scored period and are worth 0."
          % (len(NIGHTS) - len(SCORING_NIGHTS)))

    a = run(our_roster(projected=False))
    print("\nCALIBRATION  '25-26 roster at '25-26 rates, standings basis")
    print("  simulated season PF : %8.0f" % a["pf"])
    print("  real standings PF   : %8.0f  (%d scored periods)"
          % (REAL_WK_MEAN * WEEKS, WEEKS))
    print("  ratio               : %8.3f" % (a["pf"] / (REAL_WK_MEAN * WEEKS)))
    print("  weekly mean / sd    : %.0f / %.0f   real %.0f / %.0f"
          % (a["wk_mean"], a["wk_sd"], REAL_WK_MEAN, REAL_WK_SD))
    print("  weekly CV           : %.1f%%          real %.1f%%"
          % (100 * a["cv"], 100 * REAL_WK_SD / REAL_WK_MEAN))
    print("    sim CV EXCEEDS real with ZERO per-game scoring noise, so the")
    print("    availability draw is ~%.0f%% too noisy: 'variance is third-order'"
          % (100 * (a["cv"] / (REAL_WK_SD / REAL_WK_MEAN) - 1)))
    print("    survives by an over-statement, not a measurement.")
    b = run(our_roster(projected=False), bursty=True)
    print("  bursty absences     : %+.2f%% of PF (EV only)"
          % (100 * (b["pf"] / a["pf"] - 1)))

    print("\nPF -> WINS. Real per-matchup margins vs the 11 other teams, pooled")
    print("over the %d scored periods (n=%d): mean %+.0f, sd %.0f -> P(win) %.3f"
          % (WEEKS, len(MARGINS), MARGIN_MEAN, MARGIN_SD, margin_pwin()))
    ind = math.sqrt(REAL_WK_SD ** 2 + statistics.stdev(
        [v for t, s in SCORES.items() if t != US for v in s.values()]) ** 2)
    print("  assuming independence instead gives sd %.0f (%.2fx too wide):"
          % (ind, ind / MARGIN_SD))
    print("  our weekly score and our opponent's share the NBA calendar,")
    print("  correlation rho = %.2f. 1 win = %.0f PF, not %.0f."
          % (1 - MARGIN_SD ** 2 / ind ** 2, PF_PER_WIN,
             WEEKS * ind / _phi(MARGIN_MEAN / ind) / REAL_MATCHUPS))
    blo, bhi = pf_per_win_band()
    print("  band, bootstrap CLUSTERED ON PERIOD: [%.0f, %.0f] = +-%.0f%%."
          % (blo, bhi, 100 * max(bhi - PF_PER_WIN, PF_PER_WIN - blo) / PF_PER_WIN))
    print("  Quote the band, not the point: `team-eval` reads it from here.")
    print("  %6s %s" % ("+PF", "  ".join("%6d" % d for d in
                                         (250, 500, 1000, 2000, 3000))))
    print("  %6s %s" % ("+wins", "  ".join(
        "%+6.2f" % (REAL_MATCHUPS * (margin_pwin(d / WEEKS) - margin_pwin()))
        for d in (250, 500, 1000, 2000, 3000))))


def report_nights():
    """Where the 9-slot cap actually bites. The deliverable is the SHARES.

    Deliberately no headline "season loss = N PF". That number is just your
    assumed price for an empty slot times a slot count, and there is no defensible
    price: R is a fitted x-intercept, and `replacement()` says in its own docstring
    that it is NOT the rate at which a body is worth zero. Pricing the same slots
    at R gives ~1,559 PF, at 10 gives 928 and at 20 gives 1,857 -- the figure
    reports the assumption. The share columns below are invariant to that price,
    which is why they are the only thing here worth quoting.
    """
    full = basis()
    r = run(full)
    print("fill rate by night size, %d-man roster, %d scored nights."
          % (len(full), len(SCORING_NIGHTS)))
    print("`cum` = share of the season's WHOLE unfilled-slot count sitting on"
          " nights\nthis small or smaller. Price-free, hence quotable.")
    print("  %5s %7s %8s %9s %10s %6s" %
          ("games", "nights", "avail", "filled/9", "slotsLost", "cum"))
    lost = {g: (9 - v[1]) * v[3] for g, v in r["by_night"].items()}
    tot, cum = sum(lost.values()), 0.0
    for g in sorted(r["by_night"]):
        na, f, _, n = r["by_night"][g]
        cum += lost[g]
        print("  %5d %7.1f %8.1f %9.2f %10.1f %5.0f%%"
              % (g, n, na, f, lost[g], 100 * cum / tot))
    print("  %.0f unfilled slot-nights of %d (%.1f%%). Pricing them needs a rate"
          % (tot, 9 * len(SCORING_NIGHTS), 100 * tot / (9 * len(SCORING_NIGHTS))))
    print("  an empty slot forgoes; this report refuses to pick one.")
    print("\nWhy a slot goes empty -- no body at all, or bodies with no legal slot:")
    posn = sum((min(9, v[0]) - v[1]) * v[3] for v in r["by_night"].values())
    bod = sum(max(0.0, 9 - v[0]) * v[3] for v in r["by_night"].values())
    print("  slot-nights lost to no legal slot : %5.1f (%.1f%% of all slot-nights)"
          % (posn, 100 * posn / (9 * len(SCORING_NIGHTS))))
    print("  slot-nights lost to no body       : %5.1f (%.1f%%)"
          % (bod, 100 * bod / (9 * len(SCORING_NIGHTS))))
    print("  ^ both take min(9,.) of a BUCKET MEAN, so by Jensen the positional")
    print("    figure is an UPPER BOUND, not an estimate. It runs with the")
    print("    conclusion that positions rarely bind -- say so when quoting it.")


def report_scenarios():
    full = basis()
    base = run(full)
    # Jokic priced on SIM_TM like every other incoming body, NOT on DEN. His real
    # schedule is 1.0 sd BELOW the 30-team mean, which charged him ~76 PF of
    # handicap that the ladder then read as body count.
    JOKIC = dict(gp=65, elig=("C",), tm=SIM_TM)
    # A scenario's FILLER, not a bucket, a surplus list or a recommendation: held
    # fixed so the only variable down the ladder is body count. Two of these price
    # as Core, where shipping one is a walk-away trigger (`trades`).
    MID = ["Jalen Suggs", "Coby White", "Myles Turner", "Jakob Poeltl",
           "Naz Reid"]
    SC = [
        # Body count held fixed at 1 incoming, GP and position held fixed too,
        # so the ONLY variable down this ladder is how many bodies you pay.
        ("Jokic 1-for-1  (Suggs)", MID[:1], [star(65.2, **JOKIC)]),
        ("Jokic 2-for-1  (+Coby White)", MID[:2], [star(65.2, **JOKIC)]),
        ("Jokic 3-for-1  (+Turner)", MID[:3], [star(65.2, **JOKIC)]),
        ("Jokic 4-for-1  (+Poeltl)", MID[:4], [star(65.2, **JOKIC)]),
        ("Jokic 5-for-1  (+Naz Reid)", MID[:5], [star(65.2, **JOKIC)]),
        ("1-for-1  Suggs -> 50", MID[:1], [star(50)]),
        ("1-for-1  Suggs -> 45", MID[:1], [star(45)]),
        ("1-for-1  Suggs -> 40 @78gp", MID[:1], [star(40, 78)]),
        ("2-for-1  -> 50", MID[:2], [star(50)]),
        ("3-for-1  -> 50", MID[:3], [star(50)]),
        ("3-for-1  dregs -> 45",
         ["De'Anthony Melton", "Anfernee Simons", "Keon Ellis"], [star(45)]),
        ("3-for-1  -> fragile 55 @40gp", MID[:3], [star(55, 40)]),
        # Same 68 GP as every other row: three separate swaps, not one. Spread
        # over SIM_TMS so neither a schedule nor a stacking effect is booked as
        # body count -- the two things the old MIN/OKC/BOS-vs-DEN basis mixed.
        ("three separate 1-for-1s -> 42s", MID[:3],
         [star(42, 68, ("SF", "PF"), SIM_TMS[0], "S1"),
          star(42, 68, ("PG", "SG"), SIM_TMS[1], "S2"),
          star(42, 68, ("C",), SIM_TMS[2], "S3")]),
        ("two separate 1-for-1s -> 42s", MID[:2],
         [star(42, 68, ("SF", "PF"), SIM_TMS[0], "S1"),
          star(42, 68, ("PG", "SG"), SIM_TMS[1], "S2")]),
        ("bottom-up  3 dregs -> 3x 26",
         ["Khaman Maluach", "DaRon Holmes", "Khris Middleton"],
         [star(26, 76, ("SF", "PF"), SIM_TMS[0], "V1"),
          star(26, 76, ("PG", "SG"), SIM_TMS[1], "V2"),
          star(26, 76, ("C",), SIM_TMS[2], "V3")]),
    ]
    print("%d-man baseline: PF %.0f, weekly CV %.1f%%.  1 win = %.0f PF."
          % (len(full), base["pf"], 100 * base["cv"], PF_PER_WIN))
    print("Every incoming body is on %s (multi-body rows spread over %s) -- one"
          % (SIM_TM, "/".join(SIM_TMS)))
    print("schedule, because which NBA team a body sits on is worth up to 3.7")
    print("rate points and is not a fact about the trade.")
    print("BACKFILL ASSUMPTION, stated here rather than in a footnote: outgoing")
    print("bodies 2..N come back at %.0f FPts / %d GP. That is the post-auction"
          % (DEAD["avg"], DEAD["gp"]))
    print("open-FA grade. `breakevens` reports the bracket to a %.0f/%d refund."
          % (14.0, 55))
    print("%-30s %9s %7s %8s" % ("scenario", "dPF", "CV", "wins"))
    for label, out, adds in SC:
        r = run(swap(full, out, adds))
        print("%-30s %+9.0f %6.1f%% %+8.2f"
              % (label, r["pf"] - base["pf"], 100 * r["cv"], wins(r, base)))


def report_breakevens():
    print("break-even incoming rate for an N-for-1, by roster size. GP and")
    print("position are STATED because they move the answer several points:")
    print("compare a real player against the row that matches him.")
    full = basis()
    print("Two counts: padded to %d (the common basis, and ours from Sept '26)"
          % len(full))
    print("and the file as it stands. Every incoming body is on %s." % SIM_TM)
    # Same filler as `scenarios`, same warning: chosen to hold a comparison steady,
    # not because these five are the ones to send. Buckets live in
    # `my-team-situation`; this list is not one and must not be read as one.
    OUT = ["Jalen Suggs", "Coby White", "Myles Turner", "Jakob Poeltl",
           "Naz Reid"]
    shapes = [("68 GP forward", 68, ("SF", "PF")),
              ("65 GP centre", 65, ("C",)),
              ("78 GP forward", 78, ("SF", "PF"))]
    for roster in (full, our_roster()):
        avail = [n for n in OUT if any(p["n"] == n for p in roster)]
        print("\n  %d-man roster. give up %s" % (len(roster), ", ".join(
            "%s(%.1f)" % (n, next(p["avg"] for p in roster if p["n"] == n))
            for n in avail)))
        print("    %-16s %s" % ("incoming shape", "  ".join(
            "%d-for-1" % k for k in range(2, len(avail) + 1))))
        for lab, gp, elig in shapes:
            row = [breakeven(roster, avail[:k], gp, elig)
                   for k in range(2, len(avail) + 1)]
            print("    %-16s %s" % (lab, "  ".join("%7.1f" % v for v in row)))
    print("\n  3 dregs (Melton, Simons, Ellis) at %d men, 68 GP forward: %.1f"
          % (len(full), breakeven(full, ["De'Anthony Melton",
                                         "Anfernee Simons", "Keon Ellis"])))

    print("\nBACKFILL GRADE. Every row above refunds outgoing bodies 2..N at some")
    print("rate/GP. Honest bracket: %.0f/%d is post-auction open FA (all 10 fixed"
          % (DEAD["avg"], DEAD["gp"]))
    print("auction+rookie slots already spent); 14/55 is generous -- a body must")
    print("be FIELDED at 456 owned, and our own worst KEPT bodies are 13.9-14.7.")
    print("    %-16s %s" % ("refund grade", "  ".join(
        "%d-for-1" % k for k in range(2, 6))))
    band = {}
    for lab, d in (("%.0f/%d" % (DEAD["avg"], DEAD["gp"]), None),
                   ("10/48", {"tm": "MIA", "avg": 10.0, "gp": 48,
                              "elig": ["PG", "SG"]}),
                   ("14/55", {"tm": "MIA", "avg": 14.0, "gp": 55,
                              "elig": ["PG", "SG"]})):
        band[lab] = [breakeven(full, OUT[:k], 68, ("SF", "PF"), dead=d)
                     for k in range(2, 6)]
        print("    %-16s %s" % (lab, "  ".join("%7.1f" % v for v in band[lab])))
    lo, hi = band["%.0f/%d" % (DEAD["avg"], DEAD["gp"])], band["14/55"]
    print("  band across the honest bracket: %s rate points at 2..5-for-1."
          % "/".join("%.1f" % (a - b) for a, b in zip(lo, hi)))
    print("  Cap-at-3-for-1 survives every grade. A modifier, not a sign flip.")


def report_replacement():
    full = basis()
    print("value of an added 68-GP forward, fitted as c*(rate-R)*GP over rates")
    print("30/40/50/65. K = PF per win / c, so wins = (rate-R)*GP / K.")
    print("Rows are thin(basis(),n) -- the best n of the PADDED 38, so the 28 row")
    print("is not the live file's R. Measure a live roster with replacement() on it.")
    print("  %6s %10s %8s %8s" % ("thin to", "R", "c", "K"))
    for n in (38, 28):        # the only two roster sizes that exist
        R, c = replacement(thin(full, n))
        print("  %6d %10.1f %8.3f %8.0f" % (n, R, c, PF_PER_WIN / c))

    print("\nR IS POSITION-DEPENDENT, and this is a third of the formula's error.")
    print("  %8s %8s %8s %8s" % ("group", "R", "c", "K"))
    Rs = {}
    for lab, elig in GROUPS.items():
        R, c = replacement(full, 68, elig)
        Rs[lab] = R
        print("  %8s %8.1f %8.3f %8.0f" % (lab, R, c, PF_PER_WIN / c))
    # Numbers AND cause DERIVED off the LOADED roster, which `--roster` serves for
    # every team: the deltas were signed but the cause stayed the guard sentence,
    # so a negative guard delta printed our own guard glut as its explanation.
    tight = max(Rs, key=lambda g: Rs[g])
    print("  R against forwards: guard %+.1f, centre %+.1f."
          % (Rs["guard"] - Rs["forward"], Rs["centre"] - Rs["forward"]))
    print("  Tightest group is %s: %d bodies pure to it for %d slots -- crowding"
          % (tight, pure_bodies(our_roster(), GROUPS[tight]),
             group_slots(GROUPS[tight])))
    print("  a group lifts its R. A property of THIS roster's shape; re-measure")
    print("  it when the shape moves.")

    print("\nvalue in rate is LINEAR above ~30, not a power law.")
    base = run(full)["pf"]
    rates = list(range(20, 70, 5))
    v = [run(full + [star(r, 68, ("SF", "PF"), SIM_TM, "ADD")])["pf"] - base
         for r in rates]
    print("  %6s %9s %11s" % ("rate", "addedPF", "increment"))
    for i, (r, y) in enumerate(zip(rates, v)):
        print("  %6d %9.0f %11s"
              % (r, y, "%.0f" % (y - v[i - 1]) if i else "-"))
    hi = [(r, y) for r, y in zip(rates, v) if r >= 30]
    mx = statistics.mean([r for r, _ in hi])
    my = statistics.mean([y for _, y in hi])
    a = (sum((r - mx) * (y - my) for r, y in hi)
         / sum((r - mx) ** 2 for r, _ in hi))
    print("  fit over rate>=30: %.1f PF per rate point, x-intercept %.1f."
          % (a, mx - my / a))
    print("  The x-intercept of THIS line is not R: R is fitted over 30/40/50/65")
    print("  and printed above, this one over 30..65 in fives. They differ, and")
    print("  quoting either as 'the' replacement level invites the mismatch.")
    print("  Constant increments => NO convexity above 30. The real convexity is")
    print("  confined to rate < 30, which is exactly what makes the linear")
    print("  formula unusable down there.")


def report_positions():
    full = basis()
    base = run(full)["pf"]
    print("value of an ADDED body of each eligibility, vs the same rate as a")
    print("guard. this roster's %d pure PG/SG chase at most %d guard-eligible slots."
          % (pure_bodies(our_roster(), GROUPS["guard"]),
             group_slots(GROUPS["guard"])))
    print("  %6s %10s %10s %10s" % ("rate", "guard PF", "forward", "centre"))
    for rate in (25, 35, 45):
        v = {}
        for lab, elig in (("G", ("PG", "SG")), ("F", ("SF", "PF")),
                          ("C", ("C",))):
            v[lab] = run(full + [star(rate, 68, elig, SIM_TM, "ADD")])["pf"] - base
        print("  %6d %10.0f %+9.0f%% %+9.0f%%"
              % (rate, v["G"], 100 * (v["F"] / v["G"] - 1),
                 100 * (v["C"] / v["G"] - 1)))


def report_formula():
    """Does (rate - R) x GP predict what the sim measures? For whom?"""
    full = basis()
    base = run(full)
    R, c = replacement(full)
    K = PF_PER_WIN / c
    print("formula: (rate - %.1f) x GP / %.0f = wins, tested as 1-for-1s against"
          % (R, K))
    print("a %.1f-rate/68-GP forward -- the counterfactual the formula prices.\n" % R)
    grp = {}
    for lab, elig in (("guard", ("PG", "SG")), ("forward", ("SF", "PF")),
                      ("centre", ("C",))):
        grp[lab] = replacement(full, 68, elig)
    print("  %-22s %5s %4s %8s %8s %7s %7s" %
          ("player", "rate", "gp", "sim", "1R", "err", "posR err"))
    rows = []
    for p in sorted(our_roster(), key=lambda q: -(q["avg"] - R) * q["gp"])[:12]:
        r = run(swap(full, [p["n"]], [star(R, 68)]))
        sim_w = wins(base, r)
        pred = (p["avg"] - R) * p["gp"] / K
        e = set(p["elig"])
        Rp, cp = grp["centre" if e == {"C"} else
                     "guard" if e <= {"PG", "SG"} else "forward"]
        predp = (p["avg"] - Rp) * p["gp"] / (PF_PER_WIN / cp)
        rows.append((p["n"], p["avg"], p["gp"], sim_w, pred, predp))
        print("  %-22s %5.1f %4d %+8.2f %+8.2f %+6.0f%% %+6.0f%%"
              % (p["n"], p["avg"], p["gp"], sim_w, pred,
                 100 * (pred / sim_w - 1) if sim_w else 0,
                 100 * (predp / sim_w - 1) if sim_w else 0))
    err = [abs(pr / s - 1) for _, _, _, s, pr, _ in rows if s > 0.1]
    errp = [abs(pp / s - 1) for _, _, _, s, _, pp in rows if s > 0.1]
    print("\n  |error| median %.0f%%, worst %.0f%%. It is NOT a 1%% formula."
          % (100 * statistics.median(err), 100 * max(err)))
    print("  With a PER-POSITION R: median %.0f%%, worst %.0f%%. A third of the"
          % (100 * statistics.median(errp), 100 * max(errp)))
    print("  error is a fixable constant, not irreducible roster shape -- use the")
    print("  per-position R from `replacement` when you sort with this.")
    by_sim = [r[0] for r in sorted(rows, key=lambda r: -r[3])][:5]
    by_f = [r[0] for r in sorted(rows, key=lambda r: -r[4])][:5]
    by_fp = [r[0] for r in sorted(rows, key=lambda r: -r[5])][:5]
    print("  top 5 by sim         : %s" % ", ".join(by_sim))
    print("  top 5 by formula     : %s" % ", ".join(by_f))
    print("  top 5 by formula+posR: %s" % ", ".join(by_fp))
    # DERIVED, never asserted: this line has been prose contradicting the three
    # lines above it. Every ordering claim here is a comparison, not a sentence.
    print("  posR %s the top-5 order, and it %s the sim's."
          % ("leaves" if by_f == by_fp else "changes",
             "matches" if by_fp == by_sim else "still differs from"))
    print("  Judge any such difference against the per-block sd in `players`")
    print("  before reading it as a mis-ranking either R fixes.")


def report_durability():
    """Does OUR format penalise a missed game differently from a dynasty board?

    A board prices roughly expected production: any multiplicative model
    (rate x GP, or convex(rate) x GP) has GP-elasticity exactly 1 -- lose 30% of
    your games, lose 30% of your value. Measure ours against that.
    """
    full = basis()
    base = run(full)
    bbase = run(full, bursty=True)["pf"]      # lock-in is a block phenomenon
    R = replacement(full)[0]
    print("%d-man baseline PF %.0f (trials=%d)"
          % (len(full), base["pf"], TRIALS))

    def pf(rate, gp, name="Jalen Suggs"):
        return run([star(rate, gp) if p["n"] == name else p for p in full])["pf"]

    print("\nGP is the input we are worst at. What one player's GP is worth,")
    print("1-for-1 for Suggs (30.5 @ 57), for a 48.9-rate forward:")
    print("  %5s %s" % ("gp", "  ".join("%8d" % g for g in (36, 45, 55, 65))))
    print("  %5s %s" % ("wins", "  ".join(
        "%+8.2f" % ((pf(48.9, g) - base["pf"]) / PF_PER_WIN)
        for g in (36, 45, 55, 65))))

    print("\nfraction of a healthy(82 GP) season retained; a board implies gp/82:")
    print("  %5s %5s %9s %9s %8s" % ("rate", "gp", "board", "ours", "delta"))
    for rate in (26, 45, 60):
        absent, healthy = pf(rate, 0), pf(rate, 82)
        for gp in (41, 55, 70):
            ours = (pf(rate, gp) - absent) / (healthy - absent)
            print("  %5d %5d %9.3f %9.3f %+7.1f%%"
                  % (rate, gp, gp / 82, ours, 100 * (ours / (gp / 82) - 1)))

    print("\nTHE LOCK-IN. Measured on BLOCK absences with the surprise restricted")
    print("to a block's FIRST night, which is the only night it can be one -- from")
    print("night 2 he is on the public injury report and you do not start him.")
    print("`surprise` = share of a player's absence BLOCKS he is started into.")
    ab = absence_blocks(full)
    print("MEASURED on this roster, not quoted: absences arrive as %.0f nights in"
          % ab["nights"])
    print("%.0f blocks of %.2f. Drawing the surprise from every absence NIGHT"
          % (ab["blocks"], ab["mean_block"]))
    print("instead multiplies the penalty by that %.2f." % ab["mean_block"])
    print("  whole %d-man roster:" % len(full))
    for s in (0.10, 0.25, 0.40):
        d = run(full, bursty=True, surprise=s)["pf"] - bbase
        print("    %2d%% surprised: %+6.0f PF = %+.2f wins"
              % (100 * s, d, d / PF_PER_WIN))
    print("  carried by ONE 45-rate player as a share of HIS OWN value (measured")
    print("  1-for-1 against a %.1f-rate body). A board charges gp/82 and stops;" % R)
    print("  this column is what it does not charge:")
    print("    %5s %11s %s" % ("gp", "wins", "  ".join(
        "%14s" % ("lock-in @%d%%" % (100 * s)) for s in (0.15, 0.30))))

    def one(gp, s):
        r = [dict(star(45, gp), surprise=s) if p["n"] == "Jalen Suggs" else p
             for p in full]
        return run(r, bursty=True)["pf"]
    repl = run([star(R, 68) if p["n"] == "Jalen Suggs" else p for p in full],
               bursty=True)["pf"]
    for gp in (41, 55, 70, 82):
        clean = one(gp, 0.0)
        val = (clean - repl) / PF_PER_WIN
        print("    %5d %+11.2f %s" % (gp, val, "  ".join(
            "%+8.2f %4.0f%%" % (d, 100 * abs(d) / val)
            for d in [(one(gp, s) - clean) / PF_PER_WIN for s in (0.15, 0.30)])))
    print("  <=2% of value at any plausible input, and FLAT in GP. The shape that")
    print("  costs most is a high-GP veteran resting scattered single games, where")
    print("  every absence IS its own onset. Not a fragility discount; do not levy")
    print("  one. And the slate-wide-lock premise is unverified, which can only")
    print("  make this smaller.")

    print("\ndead-slot cost: at 38 with an empty pool a season-long absence also")
    print("burns a roster spot. Marginal last bodies:")
    for p in EXPANSION[-4:]:
        d = run([q for q in full if q["n"] != p["n"]])["pf"] - base["pf"]
        print("  drop %s (%.0f FPts/%d GP): %+5.0f PF = %+.3f wins"
              % (p["n"], p["avg"], p["gp"], d, d / PF_PER_WIN))

    print("\nfragility at CONSTANT (rate-17)xGP, top 6 / top 12. Weekly sd raw:")
    print("  independent absences do not synchronise, so concentrating glass")
    print("  jaws neither helps nor hurts materially.")
    for k in (6, 12):
        top = sorted(full, key=lambda p: -(p["avg"] - 17) * p["gp"])[:k]
        names = {p["n"] for p in top}
        for gp in (78, 45):
            r = run([dict(p, gp=gp, avg=17 + (p["avg"] - 17) * p["gp"] / gp)
                     if p["n"] in names else p for p in full])
            print("  top %-2d all at %d GP: PF %+6.0f  weekly sd %5.0f (base %.0f)"
                  % (k, gp, r["pf"] - base["pf"], r["wk_sd"], base["wk_sd"]))

def report_extras():
    full = basis()
    base = run(full)
    d = base["pf"] - run(our_roster())["pf"]
    print("\nSept '26 expansion: filling %d -> %d with auction-grade bodies"
          % (len(our_roster()), len(full)))
    print("  %+5.0f PF = %+.2f wins, free" % (d, d / PF_PER_WIN))


def report_players():
    """Per-player win value. STATE THE COUNTERFACTUAL: this is 'swapped for a
    replacement-level 68-GP forward', not 'if he vanished and the slot went
    empty'. Those differ by the whole value of the replacement."""
    full = basis()
    R = replacement(full)[0]
    ours = our_roster()
    print("wins lost if swapped for a replacement-level (%.1f rate, 68 GP)"
          " forward, %d-man roster." % (R, len(full)))
    print("R is fitted on THIS roster, so a short input file gives a low R and")
    print("inflates every row -- check the body count before quoting these.")
    print("Averaged over %d independent %d-trial seed blocks, with the sd across"
          % (PLAYER_BLOCKS, TRIALS))
    print("them. `next` is the gap to the row below in sigma of that gap -- the")
    print("+-sd is PER BLOCK, so the mean's se is sd/sqrt(%d) and hand-computing"
          % PLAYER_BLOCKS)
    print("it is how this table twice published an order it had not measured.")
    print("Below ~2 sigma the two rows are not ordered. QUOTE NO ORDER THERE.")
    w = player_wins(full, [p["n"] for p in ours], blocks=PLAYER_BLOCKS, R=R)
    order = sorted(ours, key=lambda q: -w[q["n"]][0])
    for i, p in enumerate(order):
        m, sd = w[p["n"]]
        nxt = ""
        if i + 1 < len(order):
            m2, sd2 = w[order[i + 1]["n"]]
            se = math.sqrt((sd ** 2 + sd2 ** 2) / PLAYER_BLOCKS)
            nxt = "%5.1f" % ((m - m2) / se) if se else "   inf"
        print("  %-24s %5.1f rate %3d gp  %-6s %+.2f  +-%.3f  %s"
              % (p["n"], p["avg"], p["gp"], "/".join(p["elig"]), m, sd, nxt))


def report_gp():
    """Is a per-player GP projection defensible AT ALL?

    GP is the dominant input here and the only one with no market price: the
    boards supply BASE, nothing supplies GP. So the question is not "how accurate
    can we get", it is "what is the smallest defensible input". Candidates are
    ranked out of sample and the winner is what `project_gp` does.
    """
    rows = gp_rows()
    allrows = gp_rows(min_rate=0.0)
    print("%d seasons of pool data (%s-%s); %d of %d players have a birthday."
          % (len(SEASONS), SEASONS[0], SEASONS[-1],
             sum(1 for v in pool().values() if v.get("born")), len(pool())))
    print("CENSORED, and it caps everything below: a player who misses a WHOLE")
    print("season is absent from the pool rather than a zero, so every figure here")
    print("is expected GP GIVEN he plays at all.")
    print("\n%d-fold CV grouped by player, errors averaged over %d fold shuffles,"
          % (GP_FOLDS, GP_SHUFFLES))
    print("then a %d-sample bootstrap CLUSTERED ON PLAYER for the interval. The"
          % GP_BOOT)
    print("interval is the point: gaps here are ~0.1-0.7 RMSE and the player")
    print("sampling error on them is ~0.15, so a gap whose interval straddles 0")
    print("is NOT a result. `P` = P(this model beats gp1).")

    for label, rs in (("rate >= %.0f, the players we trade" % GP_MIN_RATE, rows),
                      ("the whole pool, bench included", allrows)):
        ys = [r["y"] for r in rs]
        b = gp_bootstrap(rs)
        print("\n%s -- %d rows, %d players, target GP mean %.1f sd %.1f"
              % (label, len(rs), len({r["name"] for r in rs}),
                 statistics.mean(ys), statistics.stdev(ys)))
        print("  %-10s %7s %9s %-18s %6s"
              % ("model", "RMSE", "vs gp1", "95% CI on that gap", "P"))
        for k, v in sorted(b.items(), key=lambda kv: kv[1]["rmse"]):
            print("  %-10s %7.2f %+9.2f  [%+.2f, %+.2f]%5s %6.3f"
                  % (k, v["rmse"], v["delta"], v["lo"], v["hi"], "", v["p"]))

    deep = gp_bootstrap(gp_rows(min_hist=4), models=("mean", "age", "gp1", "gp5"))
    print("\nwhat the 4th and 5th season buy, on the %d rows that HAVE 4+ prior"
          % len(gp_rows(min_hist=4)))
    print("seasons (RMSE comparable only within this block):")
    print("  %-10s %7s %9s %-18s %6s"
          % ("model", "RMSE", "vs gp1", "95% CI on that gap", "P"))
    for k, v in sorted(deep.items(), key=lambda kv: kv[1]["rmse"]):
        print("  %-10s %7.2f %+9.2f  [%+.2f, %+.2f]%5s %6.3f"
              % (k, v["rmse"], v["delta"], v["lo"], v["hi"], "", v["p"]))
    print("  Even where all five seasons EXIST the interval straddles 0. More")
    print("  history is not measurably worse than one season, and it is certainly")
    print("  not better -- so one season, on Occam, not on a measured loss.")

    print("\nWHY THE RATE TERM IS KNOTTED at %.0f. Mean next-season GP by last"
          % GP_KNOT)
    print("season's rate is CONCAVE and turns DOWN, so a linear term keeps paying")
    print("for rate the pool says buys no games. Bias = predicted - actual, on the")
    print("whole pool, same grouped CV:")
    per = [gp_sq_errors(allrows, ("gp1+rate", "gp1+knot"), seed=s)
           for s in range(GP_SHUFFLES)]
    fits = {m: _ols(allrows, GP_MODELS[m], [r["y"] for r in allrows])
            for m in ("gp1+rate", "gp1+knot")}
    print("  %9s %6s %8s %10s %10s"
          % ("rate band", "n", "actual", "linear", "knotted"))
    for lo, hi in ((0, 10), (10, 20), (20, 30), (30, 40), (40, 45), (45, 999)):
        idx = [i for i, r in enumerate(allrows) if lo <= r["rate"] < hi]
        act = statistics.mean(allrows[i]["y"] for i in idx)
        cells = []
        for m in ("gp1+rate", "gp1+knot"):
            f, be = GP_MODELS[m], fits[m]
            pred = statistics.mean(
                be[0] + sum(x * z for x, z in zip(be[1:], f(allrows[i])))
                for i in idx)
            cells.append(pred - act)
        print("  %4d-%-4s %6d %8.1f %+10.1f %+10.1f"
              % (lo, "+" if hi > 900 else hi, len(idx), act, cells[0], cells[1]))
    print("  The linear term runs +7 GP high on the rate>=45 rows -- exactly the")
    print("  players every headline table on this page is built on.")
    k = gp_bootstrap(allrows, models=("gp1+knot",), ref="gp1+rate")["gp1+knot"]
    print("  knot vs the UNKNOTTED rate term, same clustered bootstrap:")
    print("    %+.3f RMSE [%+.3f, %+.3f], P(knot better) %.3f -- this is the"
          % (k["delta"], k["lo"], k["hi"], k["p"]))
    print("    comparison the adoption rests on, so it is printed rather than")
    print("    inferred by subtracting two gaps that share a reference.")

    a, b, c = gp_model()
    print("\nADOPTED -- %s" % PROJECT_GP_NOTE)
    print("  GP = %.1f + %.3f x last GP + %.3f x min(last FPts/G, %.0f)"
          % (a, b, c, GP_KNOT))
    print("  The rate term separates a bench body from a starter -- expected GP")
    print("  runs ~40 at rate <10 against ~63 at rate 30-40 -- and the knot stops")
    print("  it running on past where the pool stops paying.")
    print("  %-24s %7s %6s %6s %7s"
          % ("player", "pool gp", "rate", "proj", "delta"))
    print("  'pool gp' is the season the projection actually READ -- not always the")
    print("  roster file's, which rounds some seasons a game differently. 'proj' is")
    print("  taken straight from our_roster(), so this table cannot drift from the")
    print("  GP the scenarios are actually run on.")
    for q in sorted(our_roster(), key=lambda r: r["gp"]):
        s = pool_seasons(q["n"])
        pgp = (s.get(SEASON_STR) or s[max(s)])[1] if s else q["gp"]
        print("  %-24s %7d %6.1f %6d %+7d"
              % (q["n"], pgp, q["avg"], q["gp"], q["gp"] - pgp))
    print("  Weakest where the most recent season is a FRAGMENT: it regresses hard")
    print("  but still reads that season as the only evidence, because measured,")
    print("  that is all it is. Read the fragment rows off the table above.")


def report_market():
    """Board rank <-> FPts/G, and how much of a GP season carries forward.

    Answers the question every break-even above raises and none of them can:
    is the incoming rate a break-even demands actually BUYABLE, and at what rank?
    """
    pairs = board_rates()
    # WHICH snapshot, printed: the month moves and the old file stays put, so a
    # table that does not name its board cannot be checked against one.
    print("board: %s" % os.path.basename(newest_board()))
    print("board rank -> %s FPts/G, %d joined players." % (SEASON_TAG, len(pairs)))
    print("This is the bridge from what a trade COSTS (rank) to what it PAYS")
    print("(rate). Everything else here assumes it; nothing else measures it.")
    print("  %10s %7s %9s %9s %9s" % ("rank band", "n", "median", "p25", "p75"))
    for lo, hi in ((1, 12), (13, 24), (25, 36), (37, 60), (61, 96),
                   (97, 150), (151, 250), (251, 456)):
        v = sorted(r for k, r in pairs if lo <= k <= hi)
        if not v:
            continue
        print("  %4d-%-5d %7d %9.1f %9.1f %9.1f"
              % (lo, hi, len(v), statistics.median(v),
                 v[len(v) // 4], v[3 * len(v) // 4]))
    print("\n  rate needed -> the best rank that has historically supplied it:")
    for want in (30, 40, 45, 50, 55, 60, 65):
        ok = [k for k, r in pairs if r >= want]
        print("    %2d FPts/G: %3d players clear it; %s"
              % (want, len(ok),
                 "shallowest rank %d" % max(ok) if ok else "NOBODY"))
    print("  Read a 4-for-1 break-even against this: if it demands a rate only a")
    print("  handful of players reach, the deal is not purchasable at a fair price")
    print("  regardless of what the win table says.")

    print("\nGP PERSISTENCE. next-season GP = a + b x this-season GP, over every")
    print("consecutive pair in the pool -- the one-season baseline the richer")
    print("models are ranked against in `sim.py gp`, which is where GP now lives.")
    print("  %12s %7s %7s %7s %9s" % ("population", "n", "a", "b", "converges"))
    for thr in (0, 10, 20, 25, 30):
        a, b, n = gp_fit(thr)
        print("  %11s+ %7d %7.1f %7.3f %9.1f"
              % ("rate %d" % thr, n, a, b, a / (1 - b)))
    print("  Among rotation-quality players only ~17-28% of a GP deviation")
    print("  carries forward, so everyone converges to ~59-62 GP whatever he just")
    print("  did. That is the strongest possible form of 'regress GP hard'.")


REPORTS = {"calibration": report_calibration, "nights": report_nights,
           "scenarios": report_scenarios, "breakevens": report_breakevens,
           "replacement": report_replacement, "positions": report_positions,
           "formula": report_formula, "durability": report_durability,
           "extras": report_extras, "players": report_players,
           "market": report_market, "gp": report_gp}

# Built on OUR player names or OUR real weekly scores, so they answer nothing about
# another team: `scenarios`/`breakevens` trade Suggs and Coby, `durability` reshapes
# Suggs, `calibration` divides by our standings PF. Under `--roster` they used to
# print a full table of numbers anyway.
OURS_ONLY = {"calibration", "scenarios", "breakevens", "durability"}

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--roster" in args:
        i = args.index("--roster")
        ROSTER = args[i + 1]
        print("roster: %s" % ROSTER)
        del args[i:i + 2]
        theirs = [a for a in args if a in OURS_ONLY]
        if theirs:
            sys.exit("--roster cannot serve %s: built on our own player names and "
                     "weekly scores.\nany roster: %s"
                     % (", ".join(theirs),
                        " ".join(sorted(set(REPORTS) - OURS_ONLY))))
    # Fail LOUDLY on an unrecognised name. Filtering argv down to known reports
    # and defaulting to `calibration` meant `sim.py breakeven` (singular) exited
    # 0 having printed a table nobody asked for, and two skills mandate a sim run
    # before recommending a deal.
    unknown = [a for a in args if a not in REPORTS]
    if unknown:
        sys.exit("unknown report: %s\navailable: %s"
                 % (", ".join(unknown), " ".join(sorted(REPORTS))))
    for i, name in enumerate(args or ["calibration"]):
        print(("\n" if i else "") + "=" * 72 + "\n" + name.upper() + "\n"
              + "=" * 72)
        REPORTS[name]()
