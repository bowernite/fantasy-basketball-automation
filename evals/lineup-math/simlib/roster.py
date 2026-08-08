"""Rosters as the study prices them: load, project, pad to a common body count,
and build the synthetic bodies a trade swaps in."""
import collections, itertools
from fetch_data import SEASON_TAG, TEAM
from .board import pool_seasons
from .data import _load
from .gp import project_gp
from .lineups import SLOTS
from .projections import projected_rate
from .schedule import SIM_TM


# The 10 slots that take us 28 -> 38 in Sept '26: 3 rookie picks + 7 FA auction.
#
# HAND-TYPED, and `pad`/`basis` give the SAME ten to every team regardless of what
# picks it actually holds, so a counterparty's padded R is an upper bound on how
# thin his 38 really is.
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

    `projected=True` (default) is the '26-27 basis: the projected rate for EVERY
    player and `project_gp` for every player. Doing it here rather than per-caller
    is the point -- it makes "regress both sides identically" structural rather
    than a rule to remember, and only one side of a trade is ever ours.

    `projected=False` is the season that actually happened -- rates and GP alike,
    zeros and all. The calibration is measured against it, so projecting either
    there would recalibrate the study against itself; no ratio is quoted here,
    because the file is re-cut after every trade and it drifts (`calibration`).
    """
    rows = _load(path or ROSTER)
    if not rows:
        # `pad` tops a short roster up to 38, so an empty file does not read as
        # an empty table -- it reads as 38 auction bodies, and every figure
        # measured on them prints as a measurement of that team. A fetch that
        # reached nobody writes `[]`, so this is the shape a stale re-fetch takes.
        raise ValueError("%s carries no players -- re-run `python3 fetch_data.py"
                         " roster <team id>` (`team-info`)" % (path or ROSTER))
    out = []
    for p in rows:
        q = dict(p)
        if projected:
            # GP FIRST, and off the pool's own rate -- last season's actual, the
            # input the fit was built on. A projected rate is what a player will
            # score, not evidence of how many nights he is available, and running
            # it through the rate term recalibrates every GP in the study against
            # a variable the fit never saw.
            #
            # No pool history: fall back to the actual on his own file row --
            # `nopool` is as often a failed join as it is a rookie.
            in_pool = bool(pool_seasons(p["n"]))
            rate = projected_rate(p["n"])
            # The trailing 0.0 is deliberate: it silences `project_gp`'s raise for
            # a body with no pool row, no actual and no projection.
            gp_rate = None if in_pool else (q["avg"] or rate or 0.0)
            q["gp"] = round(project_gp(p["n"], gp=p["gp"], rate=gp_rate))
            if rate is not None:
                q["avg"] = rate
        if not q["elig"]:      # pre-`roster_rows` files left a 0-GP row with none
            q["elig"] = ["PG", "SG"]
        out.append(q)
    return out


# PROCESS-global, so "STAR7" identifies nothing across two runs -- see `star`.
_STAR_SEQ = itertools.count(1)


def star(rate, gp=68, elig=("SF", "PF"), tm=SIM_TM, n=None):
    """A synthetic body. The default name is UNIQUE per call: two `star()`s in one
    `swap()` is the documented multi-piece path, and a shared name is a body the
    scoring cannot tell apart from its twin (see `season`).

    Unique, NOT reproducible: the counter is process-global. Anything a reader
    keys on -- a printed row, a `swap` out_name, a `season` points row -- must
    pass `n=` rather than read the default back."""
    return {"n": n or "STAR%d" % next(_STAR_SEQ), "tm": tm,
            "avg": float(rate), "gp": gp, "elig": list(elig)}


def swap(roster, out_names, adds, dead=None):
    """Trade `out_names` away for `adds`; any shortfall refills at `dead` grade.

    Returns a NEW list in which each incoming body takes the vacated INDEX.
    Roster order drives the per-season rng draw order, so appending instead would
    reshuffle every untouched player's availability and turn a
    common-random-numbers comparison into an independent one -- several times the
    trials for the same precision.

    `dead` is the grade the bodies you ship out come BACK at, and it is the
    single biggest assumption under every break-even here. Price it by what is
    actually claimable at the moment the slot must be FIELDED, which is not the
    moment the trade is agreed.

    `adds` fill the vacated slots in ROSTER order, not in `out_names` order, so
    on a multi-piece deal the body listed first does not necessarily land in the
    first name's slot. The roster ends up holding the same bodies either way --
    what a printed row must not do is claim `adds[i]` replaced `out_names[i]`.
    """
    have = collections.Counter(p["n"] for p in roster)
    missing = [n for n in out_names if not have[n]]
    if missing:
        # Skipping what it could not find returned the incoming star ADDED with
        # nobody removed -- a scenario several hundred PF too high that still
        # printed. Our own names against a counterparty's file do exactly that.
        raise KeyError("not on this roster: %s" % ", ".join(missing))
    # Ambiguous only if you TRADE him. A roster may legitimately hold two bodies
    # of one name (the league rosters two Jaylin Williamses) and `season` prices
    # that correctly; which one LEFT is a question this cannot answer, and the
    # two answers are different trades.
    dupes = [n for n in out_names if have[n] > 1]
    if dupes:
        raise KeyError("%s: on this roster more than once -- rename the row you "
                       "mean before trading it" % ", ".join(sorted(set(dupes))))
    # One body cannot leave twice, so a name typed twice makes len(out_names) an
    # over-count of the bodies going out and leaves the second `fill` entry -- the
    # incoming body or the DEAD refill -- unplaced.
    twice = [n for n, c in collections.Counter(out_names).items() if c > 1]
    if twice:
        raise ValueError("%s: named twice in out_names -- one body leaves once, "
                         "so name the other body you mean" % ", ".join(sorted(twice)))
    if len(adds) > len(out_names):
        # Which of ours is dropped is the caller's call and there is no defensible
        # default, so say so instead of picking one.
        raise ValueError("%d in for %d out: the roster is capped, so name the "
                         "%d body/bodies dropped in `out_names`"
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
    """`roster` topped up to `n` bodies at the grades every team fills to 38 with.

    THE common basis for comparing two teams. `R` and every per-player win figure
    are properties of a roster's body COUNT before they are properties of its
    players, and no two live rosters share one (26-28 today, 38 from Sept '26), so
    a counterparty measured on his live bodies is not comparable to us on ours --
    his R lands ~7 rate points high and every player he owns reads cheap.

    Appends, so the real bodies keep their order and therefore their rng draws
    (see thin()). `pad(our_roster(), 38)` IS `our_roster() + EXPANSION`, which is
    what every 38-man figure in findings.md is measured on. Past those 10 fixed
    slots the grade is the bottom of the auction, spread over slot groups and NBA
    schedules so padding invents neither a positional hole nor a stacking one.
    """
    out = list(roster)
    for i in range(max(0, n - len(out))):
        if i < len(EXPANSION):
            # `elig` copied, not shared: `dict()` is shallow, and a body that
            # aliases EXPANSION's own list edits the constant for the process
            out.append(dict(EXPANSION[i], elig=list(EXPANSION[i]["elig"])))
        else:
            # The bottom auction GRADE only -- `dict(EXPANSION[-1], ...)` reads
            # as "another FA6" while overriding everything about him except his
            # rate and his GP.
            out.append({"n": "PAD%d" % i,
                        "tm": EXPANSION[i % len(EXPANSION)]["tm"],
                        "avg": EXPANSION[-1]["avg"], "gp": EXPANSION[-1]["gp"],
                        "elig": list(PAD_ELIG[i % len(PAD_ELIG)])})
    return out


# The names `pad` invents, so a caller can tell an invented slot from a body off
# a roster file. Off `pad` itself rather than hand-listed: the two schedules of
# grades would otherwise drift, and a pad this set misses reads as a real player.
PAD_NAMES = frozenset(p["n"] for p in pad([]))


# The pads a September auction actually bids for, as against the three rookie
# slots and the PAD tail. Off PAD_NAMES for the same reason PAD_NAMES is off
# `pad`: the prefix is `pad`'s to choose, and a second hand-typed copy drifts.
AUCTION_NAMES = frozenset(n for n in PAD_NAMES if n.startswith("FA"))


GROUPS = {"guard": ("PG", "SG"), "forward": ("SF", "PF"), "centre": ("C",)}


def slot_group(elig):
    """Which of GROUPS a body belongs to, on `Eval Definitions §Columns`' rule."""
    e = set(elig)
    return ("centre" if e == {"C"} else
            "guard" if e <= {"PG", "SG"} else "forward")


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
