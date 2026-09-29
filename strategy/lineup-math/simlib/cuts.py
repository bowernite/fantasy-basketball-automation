"""A side's worst bodies by full `Score`: shortlist on the partial (board BASE + formula Δw), then sim each candidate cut and keep the one that costs least"""
import itertools, math

from . import engine, title
from .bracket import loaded, measure
from .roster import PAD_NAMES, basis, pad
from .score import SCORE_DP_TITLE, SCORE_DW, SCORE_FDW, board_base
from .value import deal_formula_wins, partial_cut_scores

SHORTLIST_FLOOR = 4
SHORTLIST_BAND = 250
SHORTLIST_CAP = 12
COMBINATION_CAP = 120

_ARRIVAL_CUTS = {}


def arrival_basis(path=None):
    """`basis(path)` with a padded slot free for `incoming_*`. A full roster cuts the body whose loss scores best on its own seat, whoever arrives"""
    full = basis(path)
    if any(p["n"] in PAD_NAMES for p in full):
        return full
    key = (loaded(path), _fingerprint(full), title.SEASON_TRIALS, engine.TRIALS)
    if key not in _ARRIVAL_CUTS:
        cut, = best_cut(full, 1, _seat_cut_score(full, path))
        _ARRIVAL_CUTS[key] = cut["n"]
    cut = _ARRIVAL_CUTS[key]
    return pad([p for p in full if p["n"] != cut], len(full))


def cache_clear():
    _ARRIVAL_CUTS.clear()


def seat_score(cut, fdw, dw, dp_title):
    """A side's `Score` less the terms its cut can't move: −BASE(cut) + formula Δw, Δw and ΔP(title) (a probability) at Score's rates"""
    return (-sum(board_base(cut).values()) + SCORE_FDW * fdw + SCORE_DW * dw
            + SCORE_DP_TITLE * 100 * dp_title)


def shortlist(rows, over):
    """The bottom `over` + 4 real bodies by partial, plus any within 250 of the `over`-th lowest, at most 12"""
    partial = partial_cut_scores(rows)
    ranked = sorted((p for p in rows if p["n"] in partial),
                    key=lambda p: (partial[p["n"]], p["n"]))
    reach = partial[ranked[over - 1]["n"]] + SHORTLIST_BAND
    picked = [p for i, p in enumerate(ranked)
              if i < over + SHORTLIST_FLOOR or partial[p["n"]] <= reach]
    return picked[:max(SHORTLIST_CAP, over)]


def best_cut(rows, over, score):
    """The `over` shortlisted bodies whose cut `score`s highest; ties go to the lower partial. Every combination up to 120, greedy past that"""
    candidates = shortlist(rows, over)
    if math.comb(len(candidates), over) <= COMBINATION_CAP:
        return _highest(itertools.combinations(candidates, over), score)
    chosen = []
    while len(chosen) < over:
        # the cuts not yet chosen are held at the lowest partials so every trial is a legal roster
        trials = []
        for c in candidates:
            if c in chosen:
                continue
            rest = [p for p in candidates if p not in chosen and p is not c]
            trials.append(chosen + [c] + rest[:over - len(chosen) - 1])
        chosen = _highest(trials, score)[:len(chosen) + 1]
    return chosen


def _highest(cuts, score):
    best, best_score = None, None
    for cut in cuts:
        s = score(list(cut))
        if best_score is None or s > best_score:
            best, best_score = list(cut), s
    return best


def _seat_cut_score(full, path):
    who, teams, at = title._seat(path)
    before = title.full_season()[who]

    def score(cut):
        gone = {p["n"] for p in cut}
        field = list(teams)
        field[at] = measure(pad([p for p in full if p["n"] not in gone],
                                len(full)), who)
        after = title.full_season(tuple(field))[who]
        return seat_score(cut, deal_formula_wins([], cut),
                          after.wins - before.wins, after.title - before.title)
    return score


def _fingerprint(rows):
    return tuple((p["n"], p["tm"], p["avg"], p["gp"], tuple(p["elig"]))
                 for p in rows)
