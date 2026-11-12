"""Statistical significance testing for paired binary accuracy comparisons in GraphTrust.

Implements McNemar's test (with exact binomial fallback for small discordant counts)
and bootstrap confidence intervals on paired accuracy differences (delta Acc@1).
Follows the methodology established in Mind the Map (Perozzi & Galkin, 2024).
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple, Any
import numpy as np


def mcnemar_test(correct_a: list[bool], correct_b: list[bool]) -> dict[str, Any]:
    """Compute McNemar's test for paired binary outcomes.
    
    Args:
        correct_a: List of boolean correctness indicators for condition A.
        correct_b: List of boolean correctness indicators for condition B.
        
    Returns:
        dict containing:
            - statistic: Chi-square statistic (float)
            - p_value: Two-tailed p-value (float)
            - contingency_table: [[both_correct, a_only], [b_only, neither]]
            - discordant_a_only: int (b)
            - discordant_b_only: int (c)
            - total_pairs: int (n)
            - test_type: 'exact_binomial' or 'asymptotic_continuity_corrected'
    """
    if len(correct_a) != len(correct_b):
        raise ValueError(f"Lengths must match: len(a)={len(correct_a)}, len(b)={len(correct_b)}")
    
    n = len(correct_a)
    if n == 0:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "contingency_table": [[0, 0], [0, 0]],
            "discordant_a_only": 0,
            "discordant_b_only": 0,
            "total_pairs": 0,
            "test_type": "empty",
        }
    
    both_correct = sum(1 for a, b in zip(correct_a, correct_b) if a and b)
    a_only = sum(1 for a, b in zip(correct_a, correct_b) if a and not b)
    b_only = sum(1 for a, b in zip(correct_a, correct_b) if not a and b)
    neither = sum(1 for a, b in zip(correct_a, correct_b) if not a and not b)
    
    discordant_sum = a_only + b_only
    
    if discordant_sum == 0:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "contingency_table": [[both_correct, a_only], [b_only, neither]],
            "discordant_a_only": a_only,
            "discordant_b_only": b_only,
            "total_pairs": n,
            "test_type": "zero_discordant",
        }
    
    # Exact binomial test when discordant pairs < 25 (standard recommendation)
    if discordant_sum < 25:
        k = min(a_only, b_only)
        # Cumulative binomial P(X <= k) with p=0.5
        cdf = sum(math.comb(discordant_sum, i) * (0.5 ** discordant_sum) for i in range(k + 1))
        p_val = min(1.0, 2.0 * cdf)
        stat = float((abs(a_only - b_only) - 1.0) ** 2 / discordant_sum) if discordant_sum > 0 else 0.0
        return {
            "statistic": round(stat, 4),
            "p_value": round(p_val, 6),
            "contingency_table": [[both_correct, a_only], [b_only, neither]],
            "discordant_a_only": a_only,
            "discordant_b_only": b_only,
            "total_pairs": n,
            "test_type": "exact_binomial",
        }
    
    # Asymptotic test with Edwards' continuity correction
    stat = ((abs(a_only - b_only) - 1.0) ** 2) / discordant_sum
    from scipy.stats import chi2
    p_val = float(chi2.sf(stat, df=1))
    
    return {
        "statistic": round(stat, 4),
        "p_value": round(p_val, 6),
        "contingency_table": [[both_correct, a_only], [b_only, neither]],
        "discordant_a_only": a_only,
        "discordant_b_only": b_only,
        "total_pairs": n,
        "test_type": "asymptotic_continuity_corrected",
    }


def bootstrap_ci(
    correct_a: list[bool],
    correct_b: list[bool],
    n_resamples: int = 2000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> tuple[float, float]:
    """Compute empirical bootstrap confidence interval for accuracy difference (acc_a - acc_b)."""
    if len(correct_a) != len(correct_b):
        raise ValueError("Inputs must have identical length")
    
    n = len(correct_a)
    if n == 0:
        return (0.0, 0.0)
    
    rng = np.random.default_rng(seed)
    a_arr = np.array(correct_a, dtype=np.float64)
    b_arr = np.array(correct_b, dtype=np.float64)
    
    indices = rng.integers(0, n, size=(n_resamples, n))
    resampled_a = a_arr[indices]
    resampled_b = b_arr[indices]
    
    deltas = np.mean(resampled_a, axis=1) - np.mean(resampled_b, axis=1)
    
    alpha = (1.0 - confidence_level) / 2.0
    lower_pct = alpha * 100.0
    upper_pct = (1.0 - alpha) * 100.0
    
    ci_lower = float(np.percentile(deltas, lower_pct))
    ci_upper = float(np.percentile(deltas, upper_pct))
    
    return (round(ci_lower, 4), round(ci_upper, 4))
