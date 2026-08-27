"""Rosters as the study prices them: load, project, pad to a common body count,
and build the synthetic bodies a trade swaps in."""
import collections, itertools, os
from fetch_data import SEASON_TAG, TEAM
from .board import pool_seasons
from .data import _load, roster_path
from .gp import project_gp
from .lineups import SLOTS
from .projections import projected_rate
from .schedule import SIM_TM


# The 10 slots Sept '26 fills: 3 rookie picks + a 7-man FA auction. `pad` takes
# only as many of these as a roster is short of 38, so every team is padded on
# the SAME schedule of grades regardless of what picks it actually holds.
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


DEAD = {"tm": "MIA", "avg": 6.0, "gp": 40, "elig": ["PG", "SG"]}  # backfill grade for a shipped-out body


PAD_POS = (["PG", "SG"], ["SF", "PF"], ["C"])  # slot groups for padding without a positional hole


ROSTER = "roster-%d-%s.json" % (TEAM, SEASON_TAG)  # ours; `--roster PATH` overrides


def label(path=None):
    name = os.path.basename(path or ROSTER)
    try:
        teams = _load("teams-%s.json" % SEASON_TAG)
    except (OSError, ValueError):
        return name
    parts = name.split("-")
    team = teams.get(parts[1]) if len(parts) > 1 else None
    return "%s (%s)" % (name, team) if team else name


def our_roster(path=None, projected=True):
    """`projected=False` is the season that actually happened, rates and GP
    as-is -- used to measure calibration, so projecting it would recalibrate
    the study against itself"""
    rows = _load(roster_path(path or ROSTER))
    if not rows:
        raise ValueError("%s carries no players -- re-run `./run fetch_data.py"
                         " roster <team id>`" % (path or ROSTER))
    out = []
    for p in rows:
        q = dict(p)
        if projected:
            # GP uses the pool's own (actual) rate, computed BEFORE q["avg"] is
            # overwritten below with the projected rate
            in_pool = bool(pool_seasons(p["n"]))
            rate = projected_rate(p["n"])
            gp_rate = None if in_pool else (q["avg"] or rate or 0.0)
            q["gp"] = round(project_gp(p["n"], gp=p["gp"], rate=gp_rate))
            if rate is not None:
                q["avg"] = rate
        if not q["elig"]:      # pre-`roster_rows` files left a 0-GP row with none
            q["elig"] = ["PG", "SG"]
        out.append(q)
    return out


_STAR_SEQ = itertools.count(1)  # process-global, so names are unique per call


def star(rate, gp=68, elig=("SF", "PF"), tm=SIM_TM, n=None):
    """A synthetic body. Default name is unique per call but NOT reproducible
    across runs -- pass `n=` if the name needs to be stable"""
    return {"n": n or "STAR%d" % next(_STAR_SEQ), "tm": tm,
            "avg": float(rate), "gp": gp, "elig": list(elig)}


def swap(roster, out_names, adds, dead=None):
    """Each incoming body takes a vacated roster INDEX, in ROSTER order (not
    `out_names` order) -- order drives per-season rng draws, so appending
    instead would reshuffle every other player's availability"""
    have = collections.Counter(p["n"] for p in roster)
    missing = [n for n in out_names if not have[n]]
    if missing:
        raise KeyError("not on this roster: %s" % ", ".join(missing))
    dupes = [n for n in out_names if have[n] > 1]
    if dupes:
        raise KeyError("%s: on this roster more than once -- rename the row "
                       "you mean before trading it" % ", ".join(sorted(set(dupes))))
    twice = [n for n, c in collections.Counter(out_names).items() if c > 1]
    if twice:
        raise ValueError("%s: named twice in out_names" % ", ".join(sorted(twice)))
    if len(adds) > len(out_names):
        raise ValueError("%d in for %d out: name the %d body/bodies dropped "
                         "in `out_names`"
                         % (len(adds), len(out_names),
                            len(adds) - len(out_names)))
    grade = dead or DEAD
    fill = list(adds) + [dict(grade, n="DEAD%d" % i, elig=list(grade["elig"]))
                         for i in range(len(out_names) - len(adds))]
    out = []
    for p in roster:
        if p["n"] in out_names:
            out.append(fill.pop(0))
        else:
            out.append(p)
    return out


def pad(roster, n=38):
    """Appends, so real bodies keep their order (and rng draws)"""
    out = list(roster)
    for i in range(max(0, n - len(out))):
        if i < len(EXPANSION):
            # copy elig, don't alias EXPANSION's own list
            out.append(dict(EXPANSION[i], elig=list(EXPANSION[i]["elig"])))
        else:
            out.append({"n": "PAD%d" % i,
                        "tm": EXPANSION[i % len(EXPANSION)]["tm"],
                        "avg": EXPANSION[-1]["avg"], "gp": EXPANSION[-1]["gp"],
                        "elig": list(PAD_POS[i % len(PAD_POS)])})
    return out


PAD_NAMES = frozenset(p["n"] for p in pad([]))  # off `pad` itself, so the two can't drift


AUCTION_NAMES = frozenset(n for n in PAD_NAMES if n.startswith("FA"))


GROUPS = {"guard": ("PG", "SG"), "forward": ("SF", "PF"), "center": ("C",)}


def slot_group(elig):
    e = set(elig)
    return ("center" if e == {"C"} else
            "guard" if e <= {"PG", "SG"} else "forward")


def pure_bodies(roster, elig):
    """Bodies eligible ONLY inside `elig` (dual-eligible bodies count toward
    no group)"""
    return sum(1 for p in roster if set(p["elig"]) <= set(elig))


def group_slots(elig):
    """Starting slots a body pure to `elig` can fill, off SLOTS rather than a
    hand count"""
    return sum(1 for _, e in SLOTS if e & set(elig))


def basis(path=None):
    return pad(our_roster(path))
