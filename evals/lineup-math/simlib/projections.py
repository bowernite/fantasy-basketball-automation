"""The `projections` snapshot: the rate every `Delta w` runs on."""
import functools, os, sys
from .data import HERE


@functools.lru_cache(maxsize=1)
def _projections():
    """(module, index) for the `projections` snapshot.

    Joins through the module's own name folding, which is NOT `_key`'s -- it
    drops the spaces `_key` keeps. One convention per source is the whole reason
    a join fails silently when there are two.

    REFUSES an unusable snapshot rather than reporting it as an empty one: an
    empty feed is indistinguishable from a healthy one carrying nobody, so the
    study would re-cut silently onto the basis `projections` exists to replace.
    """
    # ONCE. `lru_cache` does not cache the raise below, so a caller that retries
    # re-enters here every time, and an unconditional insert would keep re-fronting
    # `sys.path` with this skill's `scoring.py`/`test_*.py` -- generic names,
    # shadowing whatever else answers to them.
    skill = os.path.join(HERE, os.pardir, os.pardir, ".claude", "skills",
                         "projections")
    if skill not in sys.path:
        sys.path.insert(0, skill)
    import sleeper
    try:
        idx = sleeper.index(sleeper.load())
        if not idx:
            raise ValueError("no rows -- the feed reached nobody")
        return sleeper, idx
    except Exception as e:
        raise RuntimeError(
            "unusable projection snapshot %s: %s: %s\nre-run `python3 "
            ".claude/skills/projections/sleeper.py refresh` (`projections`)"
            % (sleeper.SNAPSHOT, type(e).__name__, e)) from e


def projected_rate(name):
    """Projected FPts/G, or None for a player the feed does not carry.

    None leaves last season's average standing -- there is nothing better to
    give him -- and `report_players` flags the row `noproj` so the substitution
    is never silent.
    """
    mod, idx = _projections()
    return mod.lookup(name, idx)
