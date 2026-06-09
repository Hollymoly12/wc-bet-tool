import math
from app.models.poisson import pmf, cdf, tail_ge

def test_pmf_matches_formula():
    assert pmf(0, 2.0) == math.exp(-2.0)
    assert abs(pmf(2, 2.0) - (math.exp(-2.0) * 4 / 2)) < 1e-12

def test_cdf_is_cumulative():
    mu = 1.7
    assert abs(cdf(0, mu) - pmf(0, mu)) < 1e-12
    assert abs(cdf(3, mu) - sum(pmf(k, mu) for k in range(4))) < 1e-12

def test_tail_ge_complement():
    mu = 2.3
    assert abs(tail_ge(1, mu) - (1 - pmf(0, mu))) < 1e-12
    # over 2.5 == P(>=3) == 1 - cdf(2)
    assert abs(tail_ge(3, mu) - (1 - cdf(2, mu))) < 1e-12
