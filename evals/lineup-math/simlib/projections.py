"""The `projections` snapshot: the rate every `Delta w` runs on."""
import functools, os, sys
from .data import HERE


@functools.lru_cache(maxsize=1)
def _projections():
    """(module, index) for the `projections` snapshot; raises if unusable"""
    _ensure_skill()
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


def projected_gp(name):
    gps = [g for g in (_lookup_gp(name, "hashtag_gp"),
                        _lookup_gp(name, "fanscout_gp"))
           if g is not None]
    if not gps:
        return None
    return sum(gps) / len(gps)


def _lookup_gp(name, mod_name):
    idx = _feed_gp_index(mod_name)
    if not idx:
        return None
    return __import__(mod_name).lookup(name, idx)


@functools.lru_cache(maxsize=2)
def _feed_gp_index(mod_name):
    _ensure_skill()
    mod = __import__(mod_name)
    try:
        return mod.index(mod.load())
    except FileNotFoundError:
        return {}


def _ensure_skill():
    skill = os.path.join(HERE, os.pardir, os.pardir, ".claude", "skills",
                         "projections")
    if skill not in sys.path:
        sys.path.insert(0, skill)
