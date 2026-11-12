"""End-to-End and unit tests for statistical significance testing (McNemar and Bootstrap CI)."""

import pytest
from src.g4study.significance import mcnemar_test, bootstrap_ci


def test_mcnemar_identical_series():
    """Identical series have 0 discordant pairs, statistic 0, p-value 1.0."""
    a = [True, False, True, True, False]
    b = [True, False, True, True, False]
    res = mcnemar_test(a, b)
    assert res["statistic"] == 0.0
    assert res["p_value"] == 1.0
    assert res["discordant_a_only"] == 0
    assert res["discordant_b_only"] == 0
    assert res["test_type"] == "zero_discordant"


def test_mcnemar_exact_binomial_small_sample():
    """Exact binomial is invoked when discordant count < 25."""
    # A is consistently better than B
    a = [True] * 12 + [False] * 4
    b = [False] * 10 + [True] * 2 + [False] * 4
    # Discordant: a_only = 10, b_only = 0 => sum = 10 (< 25)
    res = mcnemar_test(a, b)
    assert res["test_type"] == "exact_binomial"
    assert res["discordant_a_only"] == 10
    assert res["discordant_b_only"] == 0
    # Two-tailed p-value for 10-0 split under p=0.5: 2 * (0.5^10) = 0.001953
    assert res["p_value"] < 0.01


def test_mcnemar_asymptotic_contingency():
    """Edwards continuity corrected chi-square runs for discordant >= 25."""
    # 25 discordant pairs: 20 A-only, 5 B-only
    a = [True] * 20 + [False] * 5 + [True] * 10
    b = [False] * 20 + [True] * 5 + [True] * 10
    res = mcnemar_test(a, b)
    assert res["test_type"] == "asymptotic_continuity_corrected"
    assert res["discordant_a_only"] == 20
    assert res["discordant_b_only"] == 5
    assert res["statistic"] > 5.0
    assert res["p_value"] < 0.05


def test_bootstrap_ci_coverage_and_ordering():
    """Bootstrap CI accurately captures delta Acc and preserves bounds."""
    a = [True] * 20 + [False] * 10  # 66.7%
    b = [True] * 10 + [False] * 20  # 33.3%
    ci_lower, ci_upper = bootstrap_ci(a, b, n_resamples=1000, seed=123)
    assert ci_lower < ci_upper
    # Delta is around +0.333
    assert 0.10 <= ci_lower <= 0.35
    assert 0.30 <= ci_upper <= 0.55


def test_significance_input_mismatch_raises():
    """Mismatched list lengths must raise ValueError."""
    with pytest.raises(ValueError, match="Lengths must match"):
        mcnemar_test([True, False], [True])

    with pytest.raises(ValueError, match="Inputs must have identical length"):
        bootstrap_ci([True, False], [True])
