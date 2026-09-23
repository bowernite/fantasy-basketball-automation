"""Daily-lineup simulator for Fleaflicker league 30579.

Answers "what is a player actually worth to us?" under the 9-slot daily cap,
on the real NBA schedule. Stdlib only (no scipy/numpy).

    ./run sim.py [report ...]            # any of REPORTS; default `calibration`
    ./run sim_run.py <config.json>       # trade screens, player effects, batched reports
    ./run test                           # invariants findings.md's claims rest on
    ./run fetch_data.py [pool]           # rebuild the data files

    ./run fetch_data.py roster 160941            # any team -> a roster file
    ./run sim.py --roster roster-160941-2025-26.json players

`--roster` serves every report but four, which are built on our own player names
and weekly scores and refuse it: calibration, scenarios, breakevens, durability.

For an actual trade under negotiation, import instead:

    import sim
    full = sim.basis()                   # or sim.basis("roster-160941-2025-26.json")
    base = sim.run(full, cal=sim.DELTA_W_CAL)
    deal = sim.run(sim.swap(full, ["Jalen Suggs"], [sim.star(48, 70, ("C",))]),
                   cal=sim.DELTA_W_CAL)
    sim.wins(deal, base)                 # (after, before) -- reversed reads "wins lost"
    sim.breakeven(full, ["Jalen Suggs", "Coby White"], gp=70, elig=("C",))

`Δw` for a counterparty's players comes in two flavours (`Eval Definitions
§Δw`), not interchangeable:

    sim.player_wins(sim.basis("their.json"), names)         # Δw THEIRS
    sim.incoming_wins(sim.basis(), sim.our_roster("their.json"))   # Δw OURS

`ΔP(title)` (`Eval Definitions §ΔP(title)`) is unconditional title probability
and is never summed with, netted against or converted into `Δw`:

    sim.player_title(sim.basis(), names)                 # ours, on roster
    sim.incoming_title(sim.basis(), sim.our_roster("their.json"))  # ΔP OURS
    sim.roster_title(after, before)                      # one roster, joint pieces
    sim.deal_odds(after_us, after_them, "their.json")    # Δw and ΔP(title), both seats

    # a multi-piece side on one roster
    full = sim.basis()
    sim.roster_title(sim.swap(full, ["A", "B"], [sim.star(48, 70, ("C",))]), full)

    after, before = sim.swap_odds(sim.swap(full, ["A"], [sim.star(48, 70)]),
                                 full)
    after.title - before.title           # same joint change, as Odds
    sim.full_season()[sim.ROSTER].seeds  # P(each seed), all 12 teams

Pass `path=` when the roster came from `basis(path)`. Omitted seats
`ROSTER` and refuses if this roster is not that file. Never assign
`sim.ROSTER` to their file to price `incoming_*`.

Roster JSON (list of dicts), written by `fetch_data.roster_rows`:
    {"n": name, "tm": FF pro-team abbrev, "avg": FPts/G, "tot": season FPts,
     "gp": games played, "posLabel": display position,
     "elig": ["PG","SG"] | ["SF","PF"] | ["C"] | ["C","PF"] | ...,
     "surprise": optional per-player share of absence BLOCKS started into}
"""
import os, statistics, sys, types

import fetch_data

from simlib import engine, gp, roster, value
from simlib.data import (
    BRACKET, BRACKET_CAL, BRACKET_NIGHTS, DATA_DIR, DELTA_W_CAL, DELTA_W_MATCHUPS,
    DELTA_W_SCORED, FF2ESPN, FULL_FIELD, HERE, HIST_PERIODS, MARGINS,
    MARGINS_BY_WEEK, NIGHTS, OURS, PERIODS, REAL_MATCHUPS, REAL_WK_MEAN,
    REAL_WK_SD, REGULAR, ROSTER_DIR, SCORED, SCORED_CAL, SCORES, SCORING_NIGHTS,
    SEASON_STR, US, WEEK_OF, WEEKS, _load, period_nights, roster_path)
from simlib.lineups import SLOTS, lineup
from simlib.stats import block_stats, ols, se_mean, slope
from simlib.schedule import (
    LIGHT_GAMES, NBA_TEAMS, SIM_TM, SIM_TMS, UNSIGNED, bracket_games, coverage,
    is_light, light_nights, period_games, team_light_nights, team_nights,
    unsigned)
from simlib.wins import (
    MARGIN_MEAN, MARGIN_SD, PF_PER_WIN, margin_pwin, pf_per_win_band, pf_wins,
    wins)
from simlib.engine import TRIALS, absence_blocks, season, unfilled_slots, _onsets
from simlib.board import (
    BOARD_DIR, BOARD_SUFFIX, POOL, board_rates, newest_board, pool, pool_seasons)
from simlib.gp import (
    FRAGMENT_GP, GP_BOOT, GP_FOLDS, GP_KNOT, GP_MIN_RATE, GP_MODELS, GP_SHUFFLES,
    PROJECT_GP_NOTE, ROTATION_RATE, SEASONS, age_at, evidence_flags,
    gp_fit, gp_model, gp_models, gp_rows, gp_sq_errors, mapped_gp, project_gp, rate_evidence)
from simlib.projections import (
    projected_rate, projected_gp, _projections, _feed_gp_index)
from simlib.roster import (
    DEAD, EXPANSION, GROUPS, MAX_WIRE, PAD_POS, apply_trade, basis, basis_after_trade,
    group_slots, our_roster, pad, pick_slot, pure_bodies, resolve_picks, slot_group,
    star, swap)
from simlib.auction import AUCTION_N, auction_slots, coverage_picks, steer
from simlib.value import (
    OutOfBracket, breakeven, breakeven_cell, breakeven_fmt, breakeven_value,
    deal_formula_wins, formula_player_wins, league_pf,
    group_body, group_fits, group_replacement, incoming_wins, replacement, thin,
    value_key)
from simlib.bracket import (
    BANDS, BRACKET_TEAMS, FIELD_LEVEL_CV, FIELD_MARGIN_CV, LADDERS, LEVEL_CV,
    MARGIN_CV, WITHIN_CV, Band, Team, bracket_weeks, field, field_mean,
    ladder_games, loaded, measure, opp_dist, opp_mean,
    opponents, reg_mean, reg_week, round_pwin,
    seed_title, sigma, team_levels, title_prob, title_slope, week_points)
# NOT `SEASON_TRIALS` -- re-exporting it would bind a stale reference under
# the very patch it exists for; `_LIVE` below is the shape a settable name needs
from simlib.title import (
    PAIRINGS, bracket_odds, deal_odds, full_season, incoming_title, player_title,
    roster_title, season_run, swap_odds)
from simlib.reports import BLURB, OURS_ONLY, REPORTS, ROSTER_FREE, SLOW

# State a caller can REPLACE, looked up live on the module that defines it --
# bound as a plain reference here, `sim.run = x` would patch this module only
# and every caller inside `simlib` would stay on the real one
_LIVE = {"run": engine, "PLAYER_BLOCKS": value, "player_wins": value,
         "gp_bootstrap": gp, "ROSTER": roster}


# Every name bound above, derived from the module dict rather than `__all__`,
# which drops the `_`-prefixed re-exports (`_load`, `_onsets`, `_projections`).
# Excludes `sys`/`types`/the `simlib` module handles, this file's own tools
_BOUND = frozenset(n for n, v in globals().items()
                   if not n.startswith("__")
                   and not isinstance(v, types.ModuleType)
                   and n != "_LIVE")


# `from sim import *` copies the module dict, which holds neither the five live
# names (served by `__getattr__`) nor the module handles (would rebind the
# caller's own `roster`/`value`) -- both must be added explicitly
__all__ = sorted([n for n in _BOUND if not n.startswith("_")] + list(_LIVE))


# `globals()` at write time would name this facade's own dict, which
# `ModuleType.__setattr__` writes into -- letting an unexported name through
# once and refusing it the second time
_EXPORTED = _BOUND | frozenset(_LIVE)


class _Facade(types.ModuleType):
    """Reads and writes of the five live names land on the module that defines
    them, not on this facade.

    A plain module `__getattr__` only fires when lookup fails, so `sim.ROSTER =
    path` would otherwise land in this module's own dict and leave every reader
    inside `simlib` on the stale value.

    Every other bound name is a reference snapshotted at import, so those RAISE
    on assignment rather than silently diverge.
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
                "sim.%s is re-exported from simlib, not owned here -- set it "
                "on the module that defines it" % name)
        else:
            types.ModuleType.__setattr__(self, name, val)

    def __dir__(self):
        return list(__all__)


sys.modules[__name__].__class__ = _Facade

def _usage():
    out = ["usage: ./run sim.py [--roster <file>] [report ...]",
           "",
           "Prices a roster in expected wins on the real %s NBA calendar."
           % fetch_data.SEASON_TAG,
           "With no report named, runs `calibration`. Names several, runs each.",
           "", "reports:"]
    for name in sorted(REPORTS):
        out.append("  %-12s %s%s%s"
                   % (name, BLURB[name],
                      "  (ours only)" if name in OURS_ONLY else "",
                      "  (%s)" % SLOW[name] if name in SLOW else ""))
    out += ["",
            "--roster <file>  price another team's roster instead of ours. The",
            "                 file is resolved in rosters/, not in the",
            "                 directory you are standing in; `./run",
            "                 fetch_data.py roster <team id>` writes one. The",
            "                 four reports marked (ours only) are built on our",
            "                 own player names and weekly scores and refuse it.",
            "",
            "Every number a report prints is labelled in that report's own",
            "preamble, including its units. Exits 0 only if every report named",
            "ran to completion; any other status means nothing printed above it",
            "is a finished run.",
            "",
            "For a live trade, import instead: see the `sim.py` module docstring."]
    return "\n".join(out)


if __name__ == "__main__":
    # Force line buffering -- block-buffered pipe output made `sim.py x | tee`
    # print nothing for minutes. `hasattr` guard: a StringIO redirect has none
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    if {"-h", "--help", "help"} & set(sys.argv[1:]):
        print(_usage())
        sys.exit(0)
    # handle `--roster=x`, not just bare `--roster x`
    args = [t for a in sys.argv[1:]
            for t in (a.split("=", 1) if a.startswith("--roster=") else [a])]
    theirs_loaded = "--roster" in args
    if theirs_loaded:
        i = args.index("--roster")
        # also refuse `--roster=` -- an empty value would load the data dir itself
        if i + 1 >= len(args) or not args[i + 1]:
            sys.exit("--roster takes a roster file: --roster %s\n`./run "
                     "fetch_data.py roster <team id>` writes one (`team-info`)."
                     % roster.ROSTER)
        # set on `roster` directly (which `basis` reads), one fewer hop than
        # going through `sim.ROSTER`
        roster.ROSTER = args[i + 1]
        # checked here, not left to the first report's `basis()` -- by then a
        # header has already printed, so a bad path reads as a started run
        path = roster_path(roster.ROSTER)
        if not os.path.isfile(path):
            sys.exit("no roster file at %s\n`./run fetch_data.py roster <team "
                     "id>` writes one in rosters/ (`team-info`)"
                     % path)
        # confirms the file is readable, not just present -- existence alone let
        # a half-written fetch through to the first report to die on a JSON error
        try:
            roster.our_roster(roster.ROSTER)
        except ValueError as e:
            sys.exit("%s is not a roster file this can price: %s\n`./run "
                     "fetch_data.py roster <team id>` writes the schema (a list "
                     "of {n, tm, avg, tot, gp, posLabel, elig})." % (path, e))
        del args[i:i + 2]
    # defaulted before the OURS_ONLY refusal below -- naming no report used to
    # run `calibration` (one of the reports --roster refuses) and exit 0
    args = args or ["calibration"]
    if theirs_loaded:
        theirs = [a for a in args if a in OURS_ONLY]
        if theirs:
            sys.exit("--roster cannot serve %s: built on our own player names and "
                     "weekly scores.\nany roster: %s\n`./run sim.py --help` "
                     "describes all %d."
                     % (", ".join(theirs),
                        " ".join(sorted(set(REPORTS) - OURS_ONLY)), len(REPORTS)))
    # fail loudly on an unrecognised name -- a silent fallback to `calibration`
    # used to print a table nobody asked for and exit 0
    unknown = [a for a in args if a not in REPORTS]
    if unknown:
        sys.exit("unknown report: %s\navailable: %s\n`./run sim.py --help` "
                 "says what each one answers."
                 % (", ".join(unknown), " ".join(sorted(REPORTS))))
    # printed before every report, not once at the top -- a lifted-out table
    # (how these get quoted) would otherwise name no team
    for i, name in enumerate(args):
        print(("\n" if i else "") + "=" * 72 + "\n"
              + "%s  --  %s" % (name.upper(),
                                "no roster: board and pool only"
                                if name in ROSTER_FREE
                                else "roster: %s" % roster.label())
              + "\n" + "=" * 72)
        try:
            REPORTS[name]()
        except statistics.StatisticsError:
            # re-raised, not caught below -- it's a ValueError subclass, but the
            # one arrival here that's a bug, not an authored refusal
            raise
        except (ValueError, KeyError, OSError, RuntimeError) as e:
            # each of these is authored prose for this moment (missing board
            # snapshot, unknown name, empty auction) -- only here; the import
            # path still raises
            sys.exit("\n%s could not be produced on %s:\n  %s%s"
                     % (name, roster.label(), e,
                        "\nnot run: %s" % " ".join(args[i + 1:])
                        if args[i + 1:] else ""))
