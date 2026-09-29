"""Season-scoped projection overrides — survive feed refresh.

    evals/board-snapshots/projections/overrides-2026.json

`gp` and/or `rate` on a row replace the feed for that player until the file is
edited. Refresh rewrites Sleeper / Hashtag / FanScout; it does not touch this file.
"""
import functools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sleeper

SEASON = "2026"
OVERRIDES = os.path.join(HERE, os.pardir, os.pardir, os.pardir, "evals",
                          "board-snapshots", "projections",
                          "overrides-%s.json" % SEASON)


def _load():
    if not os.path.isfile(OVERRIDES):
        return {}
    with open(OVERRIDES) as f:
        data = json.load(f)
    out = {}
    for name, row in data.get("players", {}).items():
        out[sleeper.norm(name)] = dict(row, name=name)
    return out


@functools.lru_cache(maxsize=1)
def index():
    return _load()


def lookup_gp(name):
    row = index().get(sleeper.norm(name))
    if row is not None and "gp" in row:
        return float(row["gp"])
    return None


def lookup_rate(name):
    row = index().get(sleeper.norm(name))
    if row is not None and "rate" in row:
        return float(row["rate"])
    return None
