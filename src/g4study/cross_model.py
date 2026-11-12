"""Cross-model architecture comparison and ranking agreement analysis (§3)."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any


def load_cross_model_results(csv_path: str | Path) -> list[dict[str, Any]]:
    """Load cross_model_comparison.csv and return parsed row dictionaries."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Cross-model results file not found: {csv_path}")

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed = dict(row)
            parsed["correct_at1"] = parsed["correct_at1"].strip().lower() == "true"
            parsed["correct_at3"] = parsed["correct_at3"].strip().lower() == "true"
            parsed["correct_at5"] = parsed["correct_at5"].strip().lower() == "true"
            parsed["budget"] = int(parsed["budget"])
            parsed["seed"] = int(parsed["seed"])
            rows.append(parsed)
    return rows


def compute_model_format_rankings(
    results: list[dict[str, Any]],
    budget: int = 512,
) -> dict[str, list[str]]:
    """Compute format accuracy rankings per model at matched budget.
    
    Returns a dict mapping model_name -> list of formats sorted in descending accuracy order.
    """
    # model -> format -> list of bools
    acc_map: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    for r in results:
        if r["budget"] == budget:
            acc_map[r["model"]][r["format"]].append(r["correct_at1"])

    rankings: dict[str, list[str]] = {}
    for model, fmt_data in acc_map.items():
        # Compute mean accuracy for each format
        mean_accs = {
            fmt: (sum(vals) / len(vals) if vals else 0.0)
            for fmt, vals in fmt_data.items()
        }
        # Sort descending by accuracy, secondary sort alphabetical
        sorted_formats = sorted(mean_accs.keys(), key=lambda f: (-mean_accs[f], f))
        rankings[model] = sorted_formats

    return rankings


def compare_model_rankings(
    csv_path: str | Path,
    model_a: str = "Model_A",
    model_b: str = "Model_B",
    budget: int = 512,
) -> dict[str, Any]:
    """Strictly compare format rankings between two models.
    
    Returns {"agrees": bool, "ranking_a": list[str], "ranking_b": list[str]}.
    """
    results = load_cross_model_results(csv_path)
    rankings = compute_model_format_rankings(results, budget=budget)

    rank_a = rankings.get(model_a, [])
    rank_b = rankings.get(model_b, [])

    agrees = (rank_a == rank_b) and (len(rank_a) > 0)

    return {
        "agrees": agrees,
        "model_a": model_a,
        "model_b": model_b,
        "ranking_a": rank_a,
        "ranking_b": rank_b,
    }
