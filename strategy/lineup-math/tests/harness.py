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
    real_run, real_many, real_wins, real_boot = (
        engine.run, engine.run_many, value.player_wins, gp.gp_bootstrap)
    was_blocks, was_seasons = value.PLAYER_BLOCKS, title.SEASON_TRIALS
    engine.run = lambda roster, **kw: real_run(roster, **dict(kw, trials=trials))
    engine.run_many = lambda rosters, **kw: real_many(
        rosters, **dict(kw, trials=trials))
    value.player_wins = lambda roster, names, **kw: real_wins(
        roster, names, **dict(kw, trials=trials))
    gp.gp_bootstrap = lambda rows, **kw: real_boot(rows, **dict(kw, n=50))
    value.PLAYER_BLOCKS = blocks
    title.SEASON_TRIALS = seasons
    bracket.team_levels.cache_clear()
    try:
        yield
    finally:
        engine.run, engine.run_many, value.player_wins, gp.gp_bootstrap = (
            real_run, real_many, real_wins, real_boot)
        value.PLAYER_BLOCKS, title.SEASON_TRIALS = was_blocks, was_seasons
        bracket.team_levels.cache_clear()


@contextlib.contextmanager
def league_rates(k):
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


def _gp_overlay_file(pairs):
    path = os.path.join(tempfile.mkdtemp(), "gp-overlay.json")
    if pairs is not None:
        with open(path, "w") as f:
            json.dump({"season": "2026-27", "source": "test", "updated": "",
                       "depth": len(pairs),
                       "rows": [{"name": n, "gp": g} for n, g in pairs]}, f)
    return path


@contextlib.contextmanager
def gp_snapshot(pairs, fanscout=()):
    hashtag_gp = skill_module("projections", "hashtag_gp")
    fanscout_gp = skill_module("projections", "fanscout_gp")
    hpath, fpath = _gp_overlay_file(pairs), _gp_overlay_file(fanscout)
    was_h, hashtag_gp.SNAPSHOT = hashtag_gp.SNAPSHOT, hpath
    was_f, fanscout_gp.SNAPSHOT = fanscout_gp.SNAPSHOT, fpath
    sim._feed_gp_index.cache_clear()
    try:
        yield
    finally:
        hashtag_gp.SNAPSHOT = was_h
        fanscout_gp.SNAPSHOT = was_f
        sim._feed_gp_index.cache_clear()


def sleeper_rows(*lines):
    return json.dumps({"season": "2026", "source": "test", "updated": 0,
                       "depth": len(lines),
                       "rows": [{"name": n, "updated": 0, "stats": s}
                                for n, s in lines]})


def roster_file(*rows):
    path = os.path.join(tempfile.mkdtemp(), "theirs.json")
    with open(path, "w") as f:
        json.dump(list(rows), f)
    return path


def committed_rosters():
    return sorted(glob.glob(os.path.join(sim.ROSTER_DIR, bracket.ROSTERS)))


def rostered(name, path=None, projected=True):
    p, = [q for q in sim.our_roster(path, projected=projected)
          if q["n"] == name]
    return p


def season_value(p):
    return p["avg"] * p["gp"]


def flat_R(rate=15.0):
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
    return " ".join(text.split())


def render(report, roster=None):
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
    return subprocess.run([sys.executable, "sim.py"] + list(args),
                          cwd=sim.HERE, capture_output=True, text=True)


def roster_payload(**over):
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
    return {t: len(sim.team_light_nights(t)) for t in sim.NBA_TEAMS}
