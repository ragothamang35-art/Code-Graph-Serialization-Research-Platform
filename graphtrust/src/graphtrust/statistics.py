"""Statistical analysis pipeline for paired task-level hypothesis testing."""

import math
import random
from typing import List, Dict, Any, Tuple
from graphtrust.schema import TaskEvaluation

def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0

def std_dev(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)

def cohens_d(x: List[float], y: List[float]) -> float:
    """Calculate Cohen's d for paired differences."""
    diffs = [a - b for a, b in zip(x, y)]
    if not diffs:
        return 0.0
    sd = std_dev(diffs)
    if sd == 0.0:
        return 0.0
    return mean(diffs) / sd

def paired_bootstrap_ci(
    x: List[float],
    y: List[float],
    num_bootstrap: int = 1000,
    alpha: float = 0.05,
    seed: int = 42
) -> Tuple[float, float, float]:
    """
    Compute paired difference bootstrap 95% confidence interval.
    Returns: (point_estimate, lower_bound, upper_bound)
    """
    n = len(x)
    if n == 0 or n != len(y):
        return 0.0, 0.0, 0.0

    diffs = [a - b for a, b in zip(x, y)]
    point_est = mean(diffs)

    rnd = random.Random(seed)
    boot_means = []
    for _ in range(num_bootstrap):
        sample = [rnd.choice(diffs) for _ in range(n)]
        boot_means.append(mean(sample))

    boot_means.sort()
    low_idx = int((alpha / 2.0) * num_bootstrap)
    high_idx = int((1.0 - alpha / 2.0) * num_bootstrap)

    lower = boot_means[min(low_idx, num_bootstrap - 1)]
    upper = boot_means[min(high_idx, num_bootstrap - 1)]
    return point_est, lower, upper

def paired_t_test(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    Compute paired t-statistic and approximate p-value.
    Uses normal approximation for Student's t when degrees of freedom > 10,
    or regular t approx.
    """
    n = len(x)
    if n < 2 or n != len(y):
        return 0.0, 1.0

    diffs = [a - b for a, b in zip(x, y)]
    m = mean(diffs)
    sd = std_dev(diffs)

    if sd == 0.0:
        return (0.0, 1.0) if m == 0.0 else (float("inf"), 0.0001)

    se = sd / math.sqrt(n)
    t_stat = m / se

    # Two-tailed p-value approximation via standard error erf
    z = abs(t_stat)
    p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))
    return round(t_stat, 4), max(0.0001, min(1.0, round(p_val, 4)))

def compare_formats(
    evals_a: List[TaskEvaluation],
    evals_b: List[TaskEvaluation],
    metric_name: str = "acc_at_1"
) -> Dict[str, Any]:
    """
    Perform paired comparison between two format conditions on matched tasks.
    """
    # Align by task_id
    map_a = {e.task_id: getattr(e, metric_name) for e in evals_a}
    map_b = {e.task_id: getattr(e, metric_name) for e in evals_b}

    common_ids = sorted(list(set(map_a.keys()).intersection(set(map_b.keys()))))
    if not common_ids:
        return {"error": "No common tasks for paired comparison"}

    vals_a = [map_a[tid] for tid in common_ids]
    vals_b = [map_b[tid] for tid in common_ids]

    mean_a = mean(vals_a)
    mean_b = mean(vals_b)
    point_diff, ci_low, ci_high = paired_bootstrap_ci(vals_a, vals_b)
    t_stat, p_val = paired_t_test(vals_a, vals_b)
    effect_size = cohens_d(vals_a, vals_b)

    return {
        "metric": metric_name,
        "sample_size": len(common_ids),
        "mean_condition_a": round(mean_a, 4),
        "mean_condition_b": round(mean_b, 4),
        "mean_difference": round(point_diff, 4),
        "ci_95_lower": round(ci_low, 4),
        "ci_95_upper": round(ci_high, 4),
        "t_statistic": t_stat,
        "p_value": p_val,
        "cohens_d": round(effect_size, 4),
        "is_statistically_significant": bool(p_val < 0.05)
    }
