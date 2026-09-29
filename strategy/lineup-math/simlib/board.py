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
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", s.lower().replace(".", "")
               .replace("'", "").replace("-", " "))
    return " ".join(s.split())


@functools.lru_cache(maxsize=1)
def pool():
    """The player pool, read-only"""
    return _load(POOL)


@functools.lru_cache(maxsize=1)
def _pool_by_key():
    return {_key(n): v for n, v in pool().items()}


def pool_seasons(name):
    v = pool().get(name) or _pool_by_key().get(_key(name))
    return (v or {}).get("seasons") or {}


def season_or_latest(seasons, season):
    return seasons.get(season) or seasons[max(seasons)]


@functools.lru_cache(maxsize=1)
def board_rows():
    with open(newest_board(), newline="") as f:
        return tuple((int(row["#"]), _key(row.get("Player") or ""))
                     for row in csv.DictReader(f)
                     if (row.get("#") or "").isdigit())


BOARD_MIN_GP = 30  # a rate under this many games is a sample, not a level


def board_rates(season=SEASON_STR, min_gp=BOARD_MIN_GP):
    """Rows that don't join between the board and the pool are dropped
    silently"""
    rate = {_key(n): v["seasons"][season][0] for n, v in pool().items()
            if season in v["seasons"] and v["seasons"][season][1] >= min_gp}
    return sorted((r, rate[k]) for r, k in board_rows() if k in rate)
