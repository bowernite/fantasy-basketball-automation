"""Daily-lineup simulator for Fleaflicker league 30579.

Answers "what is a player actually worth to us?" under the 9-slot daily cap,
on the real NBA schedule. Stdlib only (no scipy/numpy).

    python3 sim.py [report ...]          # any of REPORTS; default `calibration`
    python3 -m unittest test_sim         # invariants findings.md's claims rest on
    python3 fetch_data.py [pool]         # rebuild the data files

    python3 fetch_data.py roster 160941            # any team -> a roster file
    python3 sim.py --roster roster-160941-2025-26.json players

Every table in findings.md is one of REPORTS. Add the report before the table.
`--roster` serves 9 of the 13 reports; four are built on our own player names and
weekly scores and refuse it: calibration, scenarios, breakevens, durability.
Seven of the nine build their roster with `basis()`, which pads whatever is
loaded to 38 bodies, because R and every per-player win figure move with the body
COUNT and no two live rosters share one. `gp` and `market` read it unpadded --
they report on the bodies a team actually holds.

The CLI only knows fixed report names. For an actual trade under negotiation,
import instead -- this is the supported path and `trades` step 5 depends on it:

    import sim
    full = sim.basis()                   # or sim.basis("roster-160941-2025-26.json")
    base = sim.run(full)
    deal = sim.run(sim.swap(full, ["Jalen Suggs"], [sim.star(48, 70, ("C",))]))
    sim.wins(deal, base)                 # +wins over 20 matchups. ARG ORDER IS THE
                                         # SIGN: (after, before). Reversed it reads
                                         # "wins lost".
    sim.breakeven(full, ["Jalen Suggs", "Coby White"], gp=70, elig=("C",))

`Δw` for a counterparty's players comes in two flavours and they are different
columns (`Eval Definitions §Δw`) -- neither substitutes for the other:

    sim.player_wins(sim.basis("their.json"), names)         # Δw THEIRS
    sim.incoming_wins(sim.basis(), sim.our_roster("their.json"))   # Δw OURS

Roster JSON format (list of dicts) -- LAST SEASON as it happened, written by
`fetch_data.roster_rows`, which is the schema of record:
    {"n": name, "tm": FF pro-team abbrev, "avg": FPts/G, "tot": season FPts,
     "gp": games played, "posLabel": display position,
     "elig": ["PG","SG"] | ["SF","PF"] | ["C"] | ["C","PF"] | ...,
     "surprise": optional per-player share of absence BLOCKS started into}

`our_roster` replaces `avg` with the projected rate (`projections`) wherever the
feed carries one and projects `gp` forward, for every player on every roster;
`projected=False` gives the raw season, which the calibration is measured
against.
"""
import os, sys, types

from simlib import engine, gp, roster, value
from simlib.data import (
    FF2ESPN, HERE, MARGINS, MARGINS_BY_WEEK, NIGHTS, OURS, PERIODS, REAL_MATCHUPS,
    REAL_WK_MEAN, REAL_WK_SD, SCORED, SCORES, SCORING_NIGHTS, SEASON_STR, US,
    WEEK_OF, WEEKS, _load)
from simlib.lineups import SLOTS, lineup
from simlib.stats import block_stats, ols, se_mean, slope
from simlib.schedule import (
    LIGHT_GAMES, NBA_TEAMS, SIM_TM, SIM_TMS, UNSIGNED, coverage, is_light,
    light_nights, team_light_nights, team_nights, unsigned)
from simlib.wins import (
    MARGIN_MEAN, MARGIN_SD, PF_PER_WIN, margin_pwin, pf_per_win_band, wins)
from simlib.engine import TRIALS, absence_blocks, season, unfilled_slots, _onsets
from simlib.board import (
    BOARD_DIR, BOARD_SUFFIX, POOL, board_rates, newest_board, pool, pool_seasons)
from simlib.gp import (
    FRAGMENT_GP, GP_BOOT, GP_FOLDS, GP_KNOT, GP_MIN_RATE, GP_MODELS, GP_SHUFFLES,
    PROJECT_GP_NOTE, ROTATION_RATE, SEASONS, age_at, evidence_flags,
    gp_fit, gp_model, gp_models, gp_rows, gp_sq_errors, project_gp, rate_evidence)
from simlib.projections import projected_rate, _projections
from simlib.roster import (
    DEAD, EXPANSION, GROUPS, PAD_ELIG, basis, group_slots, our_roster, pad,
    pure_bodies, slot_group, star, swap)
from simlib.auction import AUCTION_N, auction_slots, coverage_picks, steer
from simlib.value import (
    OutOfBracket, breakeven, breakeven_cell, breakeven_fmt, breakeven_value,
    group_body, group_fits, group_replacement, incoming_wins, replacement, thin,
    value_key)
from simlib.reports import OURS_ONLY, REPORTS

# Looked up LIVE on the module that defines them, never bound here. Everything
# above is a value; these five are state a caller can REPLACE -- the roster the
# reports load, and the four knobs a test turns down to shrink a run. Bound as a
# reference, `sim.run` would be a stale snapshot: patching it would leave every
# caller inside `simlib` on the real one, and reading it back would hand out the
# real one after a patch. Both fail silently, in opposite directions.
_LIVE = {"run": engine, "PLAYER_BLOCKS": value, "player_wins": value,
         "gp_bootstrap": gp, "ROSTER": roster}


# Every name the imports above BOUND: a reference snapshotted at import, which is
# the shape `__setattr__` must refuse. Derived from the module dict, NOT from
# `__all__`: that drops the `_`-prefixed names, and `_load`, `_onsets` and
# `_projections` are re-exported on exactly the same terms as the other hundred.
# `sys`, `types` and the `simlib` handles are this file's own tools, not
# re-exports.
_BOUND = frozenset(n for n, v in globals().items()
                   if not n.startswith("__")
                   and not isinstance(v, types.ModuleType)
                   and n != "_LIVE")


# What this facade OFFERS, for `from sim import *` and for `dir`. A star import
# copies the module dict, which holds neither the five live names -- they are
# served by `__getattr__`, so `run` came out of one as a NameError -- nor the
# module handles, which would rebind the caller's own `roster`/`value`.
__all__ = sorted([n for n in _BOUND if not n.startswith("_")] + list(_LIVE))


# The set the refusal below is about: everything bound here, plus the five served
# live. Asking `globals()` at write time would name the facade's own dict, which
# `ModuleType.__setattr__` writes into -- so a name nothing re-exports was
# settable once and refused the second time, citing a `simlib` name that does not
# exist.
_EXPORTED = _BOUND | frozenset(_LIVE)


class _Facade(types.ModuleType):
    """The whole seam, in one place: reads AND writes of the five land on the
    module that defines them.

    A plain module `__getattr__` fires only when normal lookup fails, and an
    assignment is what stops it failing: `sim.ROSTER = path` landed in this
    module's own dict, read back the caller's value and left every reader inside
    `simlib` on the real one. A seam that resolves reads live and writes locally
    is worse than no seam -- both sides have to reach the same place.

    Every OTHER name above is a reference bound at import, so `sim.SLOTS = x` has
    exactly that broken shape with no seam behind it. Those RAISE rather than
    shadow: five names are worth forwarding, the hundred-odd others are worth
    refusing, and silently diverging is the one thing neither may do.
    """

    def __getattr__(self, name):
        if name in _LIVE:
            return getattr(_LIVE[name], name)
        raise AttributeError("module %r has no attribute %r" % (__name__, name))

    def __setattr__(self, name, val):
        if name in _LIVE:
            setattr(_LIVE[name], name, val)
        elif name in _EXPORTED:
            raise AttributeError(
                "sim.%s is re-exported from simlib, not owned here: assigning it"
                " reaches nobody inside simlib. Set it on the module that "
                "defines it, or pass it as an argument." % name)
        else:
            types.ModuleType.__setattr__(self, name, val)

    def __dir__(self):
        return list(__all__)


sys.modules[__name__].__class__ = _Facade

if __name__ == "__main__":
    # One flag, both spellings. Matching the bare word alone sent `--roster=x`
    # whole into the report check, which then complained about an unknown REPORT.
    args = [t for a in sys.argv[1:]
            for t in (a.split("=", 1) if a.startswith("--roster=") else [a])]
    theirs_loaded = "--roster" in args
    if theirs_loaded:
        i = args.index("--roster")
        # An EMPTY value too, not just a missing one: `--roster=` satisfies an
        # argv count and then loads the data directory itself.
        if i + 1 >= len(args) or not args[i + 1]:
            sys.exit("--roster takes a roster file: --roster %s\n`python3 "
                     "fetch_data.py roster <team id>` writes one (`team-info`)."
                     % roster.ROSTER)
        # On `roster`, the module `basis` reads it out of. `sim.ROSTER` forwards
        # here too, but one hop is one fewer thing to be wrong about the file
        # every report below is about to load.
        roster.ROSTER = args[i + 1]
        # Checked HERE, where the flag is read, rather than left to the first
        # report's own `basis()`: a wrong path is the commonest way to mistype
        # this flag, and a report that dies part-built has already printed a
        # header that reads as a started run. The path resolves against the DATA
        # directory, which is not the shell's cwd.
        path = os.path.join(HERE, roster.ROSTER)
        if not os.path.isfile(path):
            sys.exit("no roster file at %s\n`python3 fetch_data.py roster <team "
                     "id>` writes one beside sim.py (`team-info`); a bare name is"
                     " resolved there, not in the directory you are standing in."
                     % path)
        del args[i:i + 2]
    # Defaulted BEFORE the refusal below, never after: naming no report at all
    # ran `calibration` -- the report `--roster` refuses when you DO name it --
    # over a counterparty's file and our own standings, and exited 0.
    args = args or ["calibration"]
    if theirs_loaded:
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
    if theirs_loaded:
        # Banner AFTER every refusal above: printed before them, it announces a
        # roster for a run that is about to be refused.
        print("roster: %s" % roster.ROSTER)
    for i, name in enumerate(args):
        print(("\n" if i else "") + "=" * 72 + "\n" + name.upper() + "\n"
              + "=" * 72)
        REPORTS[name]()
