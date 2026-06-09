"""Poisson probability helpers used across the betting models."""
import math


def pmf(k: int, mu: float) -> float:
    """P(X = k) for X ~ Poisson(mu)."""
    if k < 0:
        return 0.0
    return math.exp(-mu + k * math.log(mu) - math.lgamma(k + 1)) if mu > 0 else (1.0 if k == 0 else 0.0)


def cdf(n: int, mu: float) -> float:
    """P(X <= n)."""
    if n < 0:
        return 0.0
    return sum(pmf(k, mu) for k in range(n + 1))


def tail_ge(n: int, mu: float) -> float:
    """P(X >= n)."""
    if n <= 0:
        return 1.0
    return 1.0 - cdf(n - 1, mu)
