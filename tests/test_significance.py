"""Unit tests for paired statistical significance testing (§2).

Covers McNemar's test (with zero-discordant division guard) and bootstrap confidence intervals.
"""

import numpy as np
import pytest
from src.g4study.significance import mcnemar_test, bootstrap_ci


def test_mcnemar_matches_hand_computed_example():
    """Verify McNemar calculation against hand-computed 10-task contingency table.
    
    Hand-computed setup (n=10 tasks):
      Task:   1  2  3  4  5  6  7  8  9 10
      A:      T  T  T  T  T  F  F  F  F  F  (5 True)
      B:      T  T  F  F  F  T  F  F  F  F  (3 True)
      
    Both True (a):   Tasks 1, 2 = 2
    A True, B False (b): Tasks 3, 4, 5 = 3 (discordant A-only)
    A False, B True (c): Task 6 = 1        (discordant B-only)
    Neither (d):     Tasks 7, 8, 9, 10 = 4
    
    Discordant count (b + c) = 3 + 1 = 4 (< 25 -> exact binomial).
    Expected statistic: (|3 - 1| - 1)^2 / 4 = 1^2 / 4 = 0.25
    Exact binomial two-tailed p-value:
      k = min(3, 1) = 1
      P(X <= 1) for Binomial(4, 0.5):
        comb(4,0)*(0.5^4) + comb(4,1)*(0.5^4) = (1 + 4)/16 = 5/16 = 0.3125
      Two-tailed p = 2 * 0.3125 = 0.6250
    """
    correct_a = [True, True, True, True, True, False, False, False, False, False]
    correct_b = [True, True, False, False, False, True, False, False, False, False]
    
    res = mcnemar_test(correct_a, correct_b)
    
    assert res["discordant_a_only"] == 3
    assert res["discordant_b_only"] == 1
    assert res["statistic"] == 0.25
    assert res["p_value"] == 0.625
    assert res["test_type"] == "exact_binomial"


def test_mcnemar_with_zero_discordant_pairs_does_not_divide_by_zero():
    """Critical edge case: correct_a == correct_b for all tasks.
    
    Discordant count is 0. Must return documented values (p_value=1.0, statistic=0.0)
    rather than raising ZeroDivisionError or unhandled exception.
    """
    a = [True, False, True, True, False, True]
    b = [True, False, True, True, False, True]
    
    res = mcnemar_test(a, b)
    
    assert res["discordant_a_only"] == 0
    assert res["discordant_b_only"] == 0
    assert res["statistic"] == 0.0
    assert res["p_value"] == 1.0
    assert res["test_type"] == "zero_discordant"


def test_mcnemar_rejects_mismatched_lengths():
    """Mismatched series lengths must raise ValueError, not cause silent misalignment."""
    with pytest.raises(ValueError, match="Lengths must match"):
        mcnemar_test([True, False, True], [True, False])


def test_bootstrap_ci_is_reproducible_with_a_fixed_seed():
    """Identical inputs with identical random seed must produce identical CI bounds."""
    a = [True, True, False, True, False, False, True, True]
    b = [False, True, False, False, False, True, False, True]
    
    ci1 = bootstrap_ci(a, b, n_resamples=1000, seed=42)
    ci2 = bootstrap_ci(a, b, n_resamples=1000, seed=42)
    
    assert ci1 == ci2


def test_bootstrap_ci_contains_the_point_estimate():
    """The observed accuracy point estimate (delta) must fall inside the bootstrap 95% CI."""
    np.random.seed(99)
    # 50 tasks with clear delta
    a = [True] * 35 + [False] * 15  # 70%
    b = [True] * 20 + [False] * 30  # 40%
    point_estimate = (35 / 50) - (20 / 50)  # +0.30
    
    ci_lower, ci_upper = bootstrap_ci(a, b, n_resamples=2000, seed=123)
    
    assert ci_lower <= point_estimate <= ci_upper


def test_bootstrap_ci_on_identical_arrays_centers_near_zero():
    """When correct_a == correct_b, difference is 0.0, so CI must straddle zero."""
    a = [True, False, True, True, False, True, False, False]
    b = list(a)
    
    ci_lower, ci_upper = bootstrap_ci(a, b, n_resamples=1000, seed=42)
    
    assert ci_lower <= 0.0 <= ci_upper


def test_bootstrap_ci_lower_bound_never_exceeds_upper_bound():
    """Lower bound must strictly be <= upper bound for any input configuration."""
    a = [True, False, False, True]
    b = [True, True, True, False]
    
    ci_lower, ci_upper = bootstrap_ci(a, b, n_resamples=500, seed=7)
    assert ci_lower <= ci_upper
