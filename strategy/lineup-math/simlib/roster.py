"""Rosters as the study prices them: load, project, pad to a common body count,
and build the synthetic bodies a trade swaps in."""
import collections, itertools, os
from fetch_data import SEASON_TAG, TEAM
from .board import pool_seasons
from .data import _load, roster_path
from .gp import project_gp
from .lineups import SLOTS
from .projections import projected_rate, unprojected_rate
from .schedule import SIM_TM


# Short-roster filler, in order, so every roster prices at the same body count
FA_FILL = [
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


OURS = "roster-%d-%s.json" % (TEAM, SEASON_TAG)  # never moved; `--roster` sets ROSTER
ROSTER = OURS
MAX_WIRE = 38  # wire cap


def refuse_already_rostered(roster, players, fn):
    clash = sorted({p["n"] for p in players} & {p["n"] for p in roster})
    if clash:
        raise ValueError("%s already on this roster -- %s adds a body that "
                         "is not here. player_wins/player_title for one that "
                         "is; counterparty: %s(basis(), "
                         "our_roster(\"their.json\"))"
                         % (", ".join(clash), fn, fn))


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
            if rate is None:
                rate = unprojected_rate(p["avg"], p["gp"])
            gp_rate = None if in_pool else (q["avg"] or rate)
            q["gp"] = round(project_gp(p["n"], gp=p["gp"], rate=gp_rate))
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


def apply_trade(roster, out_names, adds, max_bodies=MAX_WIRE):
    """Apply a trade to a wire roster (unpadded). Net +bodies is allowed while the
    result stays at or under `max_bodies`; net -bodies drops vacated slots. Name
    explicit cuts in `out_names` only when the post-trade count would exceed the cap."""
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
    out_set = set(out_names)
    seen_out = set()
    out = []
    add_queue = list(adds)
    for p in roster:
        if p["n"] in out_set:
            if p["n"] in seen_out:
                continue
            seen_out.add(p["n"])
            if add_queue:
                out.append(add_queue.pop(0))
        else:
            out.append(p)
    out.extend(add_queue)
    if len(out) > max_bodies:
        raise ValueError("%d bodies after trade (%d in, %d out on %d-man roster): "
                         "name %d cut(s) in out_names"
                         % (len(out), len(adds), len(out_names), len(roster),
                            len(out) - max_bodies))
    return out


def basis_after_trade(path, out_names, adds):
    """Wire roster after the trade, then padded to 38 for pricing"""
    return pad(apply_trade(our_roster(path or ROSTER), out_names, adds))


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
        if i < len(FA_FILL):
            out.append(dict(FA_FILL[i], elig=list(FA_FILL[i]["elig"])))
        else:
            out.append({"n": "PAD%d" % i,
                        "tm": FA_FILL[i % len(FA_FILL)]["tm"],
                        "avg": FA_FILL[-1]["avg"], "gp": FA_FILL[-1]["gp"],
                        "elig": list(PAD_POS[i % len(PAD_POS)])})
    return out


class _PadNames:
    def __contains__(self, n):
        return isinstance(n, str) and n.startswith(("FA", "PAD"))

    def __and__(self, other):
        return {n for n in other if n in self}

    def __rand__(self, other):
        return self & other


PAD_NAMES = _PadNames()


def refuse_foreign_seat(roster, who, fn):
    seated = {p["n"] for p in our_roster(who) if p["n"] not in PAD_NAMES}
    here = {p["n"] for p in roster if p["n"] not in PAD_NAMES}
    if here and len(here & seated) * 2 < len(here):
        raise ValueError("%s: this roster is not %s -- pass path=" % (fn, who))


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
