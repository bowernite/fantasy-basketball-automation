"""Score's fixed rates (`Eval Definitions §Score`) and the board BASE a sim cut is charged at."""
import functools, importlib.util, os
from .data import HERE

# Formula Δw sums pieces, so it reads ~0.3 high per extra incoming body; docked per net body
SCORE_FDW = 300
SCORE_DW = 250
SCORE_DP_TITLE = 80
SCORE_BODY_FDW = 0.3

BASE_RECIPE = os.path.join(HERE, os.pardir, os.pardir, ".claude", "skills",
                           "eval-player", "base.py")


@functools.lru_cache(maxsize=1)
def _recipe():
    spec = importlib.util.spec_from_file_location("eval_player_base", BASE_RECIPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def board_base(rows):
    """{name: BASE} off the committed board snapshots; a body off all three boards is 0"""
    priced = _recipe().price([(p["n"], p["n"], p["tm"]) for p in rows])
    return {label: base for label, _, _, base in priced}
