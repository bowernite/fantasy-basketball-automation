"""Independent work split across processes and put back in the order it went
out.

Knows nothing about basketball. Order is the whole point: floats accumulated in
a different order disagree in their last digits, so handing out contiguous index
ranges and reassembling them in the order they went out is what makes a sharded
result the SAME number as the sequential one rather than merely close to it.
Stdlib only, like the rest of the package."""
import os
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from multiprocessing import get_context


# ONE pool for the process, reused across calls. A report is hundreds of runs and
# the pool costs more to build than a run costs to make
_POOL = None
_POOL_N = 0

# Below this many units the fork dominates whatever it saves, and the sequential
# path never touches a pool at all
SHARD_FLOOR = 50


def n_workers(workers, units):
    """How many processes `units` pieces of work are worth, `None` to decide.

    Capped at `units`, because a worker with nothing to do still costs an
    interpreter.
    """
    if units < 2:
        return 1
    if workers is None:
        workers = (os.cpu_count() or 1) if units >= SHARD_FLOOR else 1
    return max(1, min(int(workers), units))


def chunks(n, parts):
    """`n` units as `(start, count)` ranges, in order, the remainder spread over
    the first ranges rather than dumped on the last."""
    parts = min(parts, n)
    base, extra = divmod(n, parts)
    out, start = [], 0
    for i in range(parts):
        k = base + (i < extra)
        out.append((start, k))
        start += k
    return out


def _pool(n):
    """`fork`, not the platform default. Under `spawn` a worker re-imports the
    module it was started from, and for a caller off the import surface that is
    the caller's own script body -- so an unguarded script prints its table once
    per worker and puts a bootstrap traceback on stderr from each.
    """
    global _POOL, _POOL_N
    if _POOL is None or _POOL_N != n:
        if _POOL is not None:
            _POOL.shutdown(wait=True)
        _POOL = ProcessPoolExecutor(max_workers=n,
                                    mp_context=get_context("fork"))
        _POOL_N = n
    return _POOL


def retire():
    """Forget the cached pool. A worker that dies breaks the executor for good,
    and the pool outlives the call, so the next one has to build a fresh one."""
    global _POOL, _POOL_N
    dead, _POOL, _POOL_N = _POOL, None, 0
    if dead is not None:
        dead.shutdown(wait=False)


def mapped(fn, jobs, n):
    """`fn` over `jobs` across `n` processes, IN JOB ORDER, falling back to this
    process if the pool dies.

    Running the work in one process cannot fail on a dead worker, so spreading it
    may not introduce a way. The pool is cached across calls, so without the
    retirement one death -- the OOM killer, at one process per core -- would
    break every later call in the session and not just the one it lands on.
    Redone here rather than retried on a fresh pool, because whatever killed the
    worker is still true.
    """
    if n > 1:
        try:
            return list(_pool(n).map(fn, jobs))
        except BrokenProcessPool:
            retire()
    return [fn(job) for job in jobs]
