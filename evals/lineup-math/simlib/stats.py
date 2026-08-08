"""The generic math every table here is fitted and summarised with.

Nothing in this module knows what a roster, a night or a win is. It is the one
place a regression or a summary in this package can be wrong, which is the whole
reason it exists: four hand-rolled copies of the same line fit are four places.
"""
import math, statistics


def block_stats(w):
    """(mean, sd across blocks, the per-block values) -- the shape BOTH `Delta w`
    columns return, so `Delta w ours` and `Delta w theirs` cannot come back
    differently shaped. The blocks travel with the summary because they are
    SHARED across rows, and only the paired differences see that."""
    return (statistics.mean(w),
            statistics.stdev(w) if len(w) > 1 else 0.0, w)


def se_mean(xs):
    """Standard error of the mean of `xs`.

    Both "is this gap real?" columns feed PAIRED differences through here, so
    neither can go back to treating two shared-seed measurements as independent.
    """
    return statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0


def slope(xs, ys):
    """(mean x, mean y, slope) of the least-squares line through `xs` and `ys`.

    The means come back with the slope because every caller wants an INTERCEPT
    off them -- `mx - my / b` is the x-intercept `replacement` calls R -- and
    re-deriving them outside is how two fits of the same points end up quoting
    two R's. `ols` is the same fit by the normal equations; this form is kept
    because it is what the published figures were measured with.
    """
    mx, my = statistics.mean(xs), statistics.mean(ys)
    return mx, my, (sum((x - mx) * (y - my) for x, y in zip(xs, ys))
                    / sum((x - mx) ** 2 for x in xs))


def ols(rows, feat, ys):
    """Least squares with an intercept, via the normal equations. Stdlib only, and
    the designs here are 1-3 columns, so conditioning is not a concern."""
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


def phi(z):
    """Standard normal density."""
    return math.exp(-z * z / 2) / math.sqrt(2 * math.pi)


def cdf(z):
    """Standard normal CDF."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))
