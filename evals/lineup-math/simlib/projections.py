"""The `projections` snapshot: the rate every `Delta w` runs on."""
import functools, os, sys
from .data import HERE


@functools.lru_cache(maxsize=1)
def _projections():
    """(module, index) for the `projections` snapshot; raises if unusable"""
    skill = os.path.join(HERE, os.pardir, os.pardir, ".claude", "skills",
                         "projections")
    if skill not in sys.path:
        sys.path.insert(0, skill)
    import sleeper
    try:
        idx = sleeper.index(sleeper.load())
        if not idx:
            raise ValueError("no rows")
        return sleeper, idx
    except Exception as e:
        raise RuntimeError(
            "unusable projection snapshot %s: %s: %s\nre-run `python3 "
            ".claude/skills/projections/sleeper.py refresh`"
            % (sleeper.SNAPSHOT, type(e).__name__, e)) from e


def projected_rate(name):
    """Projected FPts/G, or None if the feed doesn't carry `name`"""
    mod, idx = _projections()
    return mod.lookup(name, idx)
