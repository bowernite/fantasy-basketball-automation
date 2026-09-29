"""The generic math every table here is fitted and summarised with.

Nothing in this module knows what a roster, a night or a win is."""
import math, statistics


def block_stats(w):
    """(mean, sd across blocks, the per-block values)"""
    return (statistics.mean(w),
            statistics.stdev(w) if len(w) > 1 else 0.0, w)


def se_mean(xs):
    return statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0


def slope(xs, ys):
    """(mean x, mean y, slope) of the least-squares line through `xs` and `ys`"""
    mx, my = statistics.mean(xs), statistics.mean(ys)
    return mx, my, (sum((x - mx) * (y - my) for x, y in zip(xs, ys))
                    / sum((x - mx) ** 2 for x in xs))


def ols(rows, feat, ys):
    X = [[1.0] + list(feat(r)) for r in rows]
    k = len(X[0])
    A = [[sum(x[i] * x[j] for x in X) for j in range(k)]
         + [sum(x[i] * y for x, y in zip(X, ys))] for i in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(A[r][c]))
        A[c], A[p] = A[p], A[c]
        if abs(A[c][c]) < 1e-9:
            return None
        for r in range(k):
            if r != c:
                f = A[r][c] / A[c][c]
                A[r] = [a - f * b for a, b in zip(A[r], A[c])]
    return [A[i][k] / A[i][i] for i in range(k)]


def false_position(f, lo, hi, flo, fhi, tol):
    """Root of `f` inside a bracket that already straddles zero (caller's job
    to check). Only valid for `f` convex and increasing -- that's what
    guarantees the interpolated estimate converges rather than stalling"""
    x = prev = None
    while True:
        prev, x = x, (lo * fhi - hi * flo) / (fhi - flo)
        if prev is not None and abs(x - prev) <= tol / 2:
            return x
        fx = f(x)
        if fx < 0:
            lo, flo = x, fx
        else:
            hi, fhi = x, fx


def phi(z):
    """Standard normal density"""
    return math.exp(-z * z / 2) / math.sqrt(2 * math.pi)


def cdf(z):
    """Standard normal CDF"""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))
