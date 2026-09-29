"""Independent work split across processes and put back in the order it went
out. Order matters: floats accumulated in a different order disagree in their
last digits, so results must come back in job order to match the sequential
run digit for digit."""
import os
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from multiprocessing import get_context


_POOL = None
_POOL_N = 0

SHARD_FLOOR = 50  # below this many units, forking costs more than it saves


def n_workers(workers, units, floor=SHARD_FLOOR):
    """How many processes `units` pieces of work are worth, `None` to decide"""
    if units < 2:
        return 1
    if workers is None:
        workers = (os.cpu_count() or 1) if units >= floor else 1
    return max(1, min(int(workers), units))


def chunks(n, parts):
    """`n` units as `(start, count)` ranges, in order; remainder spread over
    the first ranges"""
    parts = min(parts, n)
    base, extra = divmod(n, parts)
    out, start = [], 0
    for i in range(parts):
        k = base + (i < extra)
        out.append((start, k))
        start += k
    return out


def _pool(n):
    """`fork`, not the platform default -- `spawn` re-imports the caller's
    own script on each worker"""
    global _POOL, _POOL_N
    if _POOL is None or _POOL_N != n:
        if _POOL is not None:
            _POOL.shutdown(wait=True)
        _POOL = ProcessPoolExecutor(max_workers=n,
                                    mp_context=get_context("fork"))
        _POOL_N = n
    return _POOL


def retire():
    """Forget the cached pool (a dead worker breaks its executor for good)"""
    global _POOL, _POOL_N
    dead, _POOL, _POOL_N = _POOL, None, 0
    if dead is not None:
        dead.shutdown(wait=False)


def mapped(fn, jobs, n):
    """`fn` over `jobs` across `n` processes, in job order; falls back to
    sequential in this process if the pool dies"""
    if n > 1:
        try:
            return list(_pool(n).map(fn, jobs))
        except BrokenProcessPool:
            retire()
    return [fn(job) for job in jobs]
