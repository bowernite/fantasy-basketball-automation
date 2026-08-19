"""Shared fixtures for tests/."""
import ast
import collections
import contextlib
import glob
import importlib
import io
import itertools
import json
import math
import multiprocessing
import os
import random
import re
import runpy
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

import fetch_data
import sim
from simlib import (bracket, engine, gp, roster as roster_mod, shard, stats,
                    title, value)
from simlib import reports
from simlib.reports import deals, durability

THEIR_ROSTER = "roster-161020-2025-26.json"
ROOKIE_ROSTER = "roster-160941-2025-26.json"
THREE_OUT = ["Jalen Suggs", "Coby White", "Myles Turner"]
SNAPSHOT = os.path.join(sim.HERE, os.pardir, "board-snapshots", "projections",
                        "sleeper-2026.json")


@contextlib.contextmanager
def cheap_monte_carlo(trials=4, blocks=1, seasons=200):
    """A trial count that answers whether a report runs, not what it says

    The three lambdas bind their sample size as a default at import, so
    lowering `TRIALS` alone changes nothing; `PLAYER_BLOCKS` and
    `SEASON_TRIALS` are module constants read at call time. Patched on the
    module that defines each one, since `sim` forwards them both ways
    """
    real_run, real_wins, real_boot = (engine.run, value.player_wins,
                                      gp.gp_bootstrap)
    was_blocks, was_seasons = value.PLAYER_BLOCKS, title.SEASON_TRIALS
    engine.run = lambda roster, **kw: real_run(roster, **dict(kw, trials=trials))
    value.player_wins = lambda roster, names, **kw: real_wins(
        roster, names, **dict(kw, trials=trials))
    gp.gp_bootstrap = lambda rows, **kw: real_boot(rows, **dict(kw, n=50))
    value.PLAYER_BLOCKS = blocks
    title.SEASON_TRIALS = seasons
    bracket.team_levels.cache_clear()
    try:
        yield
    finally:
        engine.run, value.player_wins, gp.gp_bootstrap = (real_run, real_wins,
                                                          real_boot)
        value.PLAYER_BLOCKS, title.SEASON_TRIALS = was_blocks, was_seasons
        bracket.team_levels.cache_clear()


@contextlib.contextmanager
def league_rates(k):
    """Every projected rate in the league scaled by `k`, at the one place a
    roster reads the feed -- so every team inflates together, which is the only
    way to move a level without moving anybody's edge"""
    real = roster_mod.projected_rate
    roster_mod.projected_rate = lambda n: (None if real(n) is None
                                           else k * real(n))
    bracket.team_levels.cache_clear()
    try:
        yield
    finally:
        roster_mod.projected_rate = real
        bracket.team_levels.cache_clear()


@contextlib.contextmanager
def recorded_rosters(trials=2):
    """Every roster `engine.run` is handed while the block runs, by name. Which
    bodies a column was priced on is not visible in the number it returns,
    since two bottom-grade rooms are under the noise apart"""
    seen, real = [], engine.run
    engine.run = lambda roster, **kw: (
        seen.append([p["n"] for p in roster]),
        real(roster, **dict(kw, trials=trials)))[1]
    try:
        yield seen
    finally:
        engine.run = real


@contextlib.contextmanager
def projection_snapshot(text):
    """Points `projections` at a snapshot file we wrote and lets the sim read
    it through its own loader, scorer and name join, so the file on disk is the
    only thing stubbed. `text=None` points it at a path with nothing on it"""
    sleeper = skill_module("projections", "sleeper")
    path = os.path.join(tempfile.mkdtemp(), "sleeper-2026.json")
    if text is not None:
        with open(path, "w") as f:
            f.write(text)
    was, sleeper.SNAPSHOT = sleeper.SNAPSHOT, path
    sim._projections.cache_clear()
    try:
        yield
    finally:
        sleeper.SNAPSHOT = was
        sim._projections.cache_clear()


def sleeper_rows(*lines):
    """A snapshot payload, in the feed's own shape"""
    return json.dumps({"season": "2026", "source": "test", "updated": 0,
                       "depth": len(lines),
                       "rows": [{"name": n, "updated": 0, "stats": s}
                                for n, s in lines]})


def roster_file(*rows):
    """A one-off roster file in the shape `fetch_data.py roster` writes, the
    only way to hand `our_roster` a row no committed file carries"""
    path = os.path.join(tempfile.mkdtemp(), "theirs.json")
    with open(path, "w") as f:
        json.dump(list(rows), f)
    return path


def committed_rosters():
    """Every roster file in the tree for THIS season. The league is 12 and they
    are re-cut with `fetch_data.py roster <id>`, so the set is the directory's
    to state -- and the previous season's files sit beside them"""
    return sorted(glob.glob(os.path.join(sim.HERE, bracket.ROSTERS)))


def rostered(name, path=None, projected=True):
    """His row on a loaded roster, exactly one or the unpacking says so"""
    p, = [q for q in sim.our_roster(path, projected=projected)
          if q["n"] == name]
    return p


def season_value(p):
    """Rate x games, the whole season of production a body supplies"""
    return p["avg"] * p["gp"]


def flat_R(rate=15.0):
    """One replacement level for all three slot groups, for a test whose
    subject is not which group a body lands in"""
    return dict.fromkeys(sim.GROUPS, rate)


def skills_path(*parts):
    return os.path.join(sim.HERE, os.pardir, os.pardir, ".claude", "skills",
                        *parts)


def skill_module(skill, name):
    path = skills_path(skill)
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module(name)


def read_text(path):
    with open(path) as f:
        return f.read()


def one_line(text):
    """Single-spaced, so a sentence can be matched across the wraps it is
    printed or written in"""
    return " ".join(text.split())


def render(report, roster=None):
    """The stdout of one report, driven the way `__main__` drives it.
    `roster_mod` is where `basis` reads the default path from, so this sets it
    there"""
    was = roster_mod.ROSTER
    if roster:
        roster_mod.ROSTER = roster
    buf = io.StringIO()
    try:
        with cheap_monte_carlo(), contextlib.redirect_stdout(buf):
            sim.REPORTS[report]()
    finally:
        roster_mod.ROSTER = was
    return buf.getvalue()


def cli(*args):
    """One `python3 sim.py ...`, argv parsing and all, without the process

    Returns (exit status, everything the run said). `sim.py` exits with its
    explanation as the status, so that text is folded into the output too
    """
    was_argv, was_roster = sys.argv, roster_mod.ROSTER
    sys.argv = ["sim.py"] + list(args)
    buf, status = io.StringIO(), 0
    try:
        with cheap_monte_carlo(), contextlib.redirect_stdout(buf):
            runpy.run_path(sim.__file__, run_name="__main__")
    except SystemExit as e:
        status = e.code
    finally:
        sys.argv, roster_mod.ROSTER = was_argv, was_roster
    return status, buf.getvalue() + (status if isinstance(status, str) else "")


def sim_process(*args):
    """One real `python3 sim.py ...`, real interpreter, real argv, real exit
    status, at the published trial counts. The paths worth this are the ones
    `cli` cannot reach, how the command behaves as it is actually typed"""
    return subprocess.run([sys.executable, "sim.py"] + list(args),
                          cwd=sim.HERE, capture_output=True, text=True)


def roster_payload(**over):
    """One `FetchRoster?season=` row, trimmed to the keys the transform reads.
    Fleaflicker omits zero and default fields entirely, so the shape that bites
    is a row with no `seasonAverage`, `seasonTotal` or `rankFantasy` at all"""
    row = {"proPlayer": {"id": 1, "nameFull": "Darius Garland", "position": "G",
                         "proTeamAbbreviation": "LAC",
                         "positionEligibility": ["PG", "SG"]},
           "seasonAverage": {"value": 31.894444},
           "seasonTotal": {"value": 1435.25},
           "rankFantasy": {"positions": [
               {"position": {"eligibility": ["PG"]}},
               {"position": {"eligibility": ["SG"]}}]}}
    row.update(over)
    return {"groups": [{"slots": [{}, {"leaguePlayer": row}]}]}


def light_nights_per_team():
    """{team: the light nights it plays}, the table `schedules` prints and the
    quantity every coverage bound is read off. Derived rather than a literal,
    since the deepest and emptiest schedules move with the calendar every
    season"""
    return {t: len(sim.team_light_nights(t)) for t in sim.NBA_TEAMS}
