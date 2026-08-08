"""The dynasty board and the player pool: board rank <-> scoring rate."""
import csv, functools, glob, os, re, unicodedata
from fetch_data import SEASON_TAG
from .data import HERE, SEASON_STR, _load


POOL = "players-%s.json" % SEASON_TAG        # fetch_data.py pool


BOARD_DIR = os.path.join(HERE, os.pardir, "board-snapshots", "dizzle-dynasty")


BOARD_SUFFIX = "dynasty-ranks-points.csv"    # points league; 9cat is cross-check


_MONTHS = ("january february march april may june july august september october"
           " november december").split()


def newest_board(d=BOARD_DIR):
    """Path to the newest month-stamped points dynasty snapshot in `d`.

    NEVER hardcode a month: `dizzle-dynasty` re-snapshots under a new one and the
    old file stays put, so a hardcoded name goes stale in place while every rank
    in the study keeps resolving. Raises rather than falling back to a stale
    board -- this is the only rank -> rate bridge here.
    """
    found = []
    for p in glob.glob(os.path.join(d, "*-" + BOARD_SUFFIX)):
        m = re.match(r"([a-z]+)-(\d{4})-", os.path.basename(p))
        if m and m.group(1) in _MONTHS:
            found.append(((int(m.group(2)), _MONTHS.index(m.group(1))), p))
    if not found:
        raise FileNotFoundError("no <month>-<year>-%s in %s"
                                % (BOARD_SUFFIX, d))
    return max(found)[1]


def _key(name):
    """Match names across two sources that punctuate and accent differently."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", s.lower().replace(".", "")
               .replace("'", "").replace("-", " "))
    return " ".join(s.split())


@functools.lru_cache(maxsize=1)
def pool():
    """The player pool, read-only. Cached because GP projection reads it once per
    scenario."""
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


def season_or_latest(seasons, season):
    """`seasons[season]`, or his MOST RECENT one if that season is missing.

    The pool holds only seasons a player actually appeared in, so "missed the
    whole year" and "left the league" both look like a missing key -- and every
    caller wants the same answer to it. Written once because two of them feed
    `Δw` inputs: `project_gp` reads the GP the projection is built on and
    `rate_evidence` reads the games the rate rests on, and a player whose latest
    season those two disagreed about would be projected off one and flagged off
    the other.
    """
    return seasons.get(season) or seasons[max(seasons)]


@functools.lru_cache(maxsize=1)
def board_rows():
    """((rank, normalised name), ...) for every RANKED row on the newest board.

    The denominator `board_rates` joins against, so "how many rows did not join"
    is a subtraction rather than a second read of the same file under a second
    idea of what counts as a row. Cached because every miss re-globs the snapshot
    directory and re-parses the CSV.
    """
    with open(newest_board(), newline="") as f:
        return tuple((int(row["#"]), _key(row.get("Player") or ""))
                     for row in csv.DictReader(f)
                     if (row.get("#") or "").isdigit())


# A rate under this many games is a sample, not a level: unfiltered, a 13-game
# season puts a rank-418 player in the table at 32 FPts/G. It is also what makes
# every figure downstream CONDITIONAL on availability, so it is a named constant
# the report can print rather than a default nothing states.
BOARD_MIN_GP = 30


def board_rates(season=SEASON_STR, min_gp=BOARD_MIN_GP):
    """[(board rank, FPts/G)] for every player on the points dynasty board we can
    price. THE bridge the framework otherwise asserts: rank is what a trade costs
    and rate is what it pays, and nothing else here connects them. Without it you
    cannot tell whether a break-even is purchasable at any price.

    DROPS SILENTLY, and the count is the caveat: a board row joins only if the
    pool carries that player with a `min_gp`+ season, so the rate this hands back
    for a rank is "what a player of that rank supplies GIVEN he played `min_gp`
    games". `report_market` prints how many rows fell out, because the ones that
    do are disproportionately the ranks a trade is actually about.
    """
    rate = {_key(n): v["seasons"][season][0] for n, v in pool().items()
            if season in v["seasons"] and v["seasons"][season][1] >= min_gp}
    return sorted((r, rate[k]) for r, k in board_rows() if k in rate)
