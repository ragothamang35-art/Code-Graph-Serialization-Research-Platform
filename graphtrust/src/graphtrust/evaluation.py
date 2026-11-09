"""Evaluation metrics for code file localization."""

from typing import List, Dict, Any
from graphtrust.schema import TaskEvaluation, ModelPrediction, Task, RetrievedSubgraph
from graphtrust.data import normalize_path

def compute_reciprocal_rank_5(predictions: List[str], gold_files: List[str]) -> float:
    """Compute Reciprocal Rank within top 5 predictions."""
    norm_gold = set(normalize_path(g) for g in gold_files)
    for rank_idx, pred in enumerate(predictions[:5], start=1):
        if normalize_path(pred) in norm_gold:
            return 1.0 / rank_idx
    return 0.0

def evaluate_task(
    task: Task,
    prediction: ModelPrediction,
    subgraph: RetrievedSubgraph,
    token_count: int
) -> TaskEvaluation:
    """Evaluate a single task prediction against gold labels."""
    norm_gold = set(normalize_path(g) for g in task.gold_files)
    norm_preds = [normalize_path(p) for p in prediction.predicted_files]
    norm_cands = set(normalize_path(c) for c in subgraph.candidate_files)

    # Accuracy@1
    acc_1 = 1.0 if norm_preds and (norm_preds[0] in norm_gold) else 0.0

    # Accuracy@5
    acc_5 = 1.0 if any(p in norm_gold for p in norm_preds[:5]) else 0.0

    # MRR@5
    mrr_5 = compute_reciprocal_rank_5(norm_preds, task.gold_files)

    # Candidate coverage: is at least one gold file in retrieved candidate set?
    cand_cov = 1.0 if any(g in norm_cands for g in norm_gold) else 0.0

    # Conditional accuracy: score if covered, else None / conditional metric
    cond_acc_1 = acc_1 if cand_cov > 0 else 0.0

    return TaskEvaluation(
        task_id=task.instance_id,
        format_type=prediction.format_type,
        budget=prediction.budget,
        acc_at_1=acc_1,
        acc_at_5=acc_5,
        mrr_at_5=mrr_5,
        candidate_coverage=cand_cov,
        conditional_acc_1=cond_acc_1,
        gold_files=task.gold_files,
        predicted_files=prediction.predicted_files,
        candidate_files=subgraph.candidate_files,
        token_count=token_count
    )

def aggregate_evaluations(evals: List[TaskEvaluation]) -> Dict[str, Any]:
    """Aggregate task evaluations into summary metrics."""
    if not evals:
        return {}

    n = len(evals)
    mean_acc_1 = sum(e.acc_at_1 for e in evals) / n
    mean_acc_5 = sum(e.acc_at_5 for e in evals) / n
    mean_mrr_5 = sum(e.mrr_at_5 for e in evals) / n
    mean_cov = sum(e.candidate_coverage for e in evals) / n
    mean_tokens = sum(e.token_count for e in evals) / n

    # Covered tasks subset
    covered = [e for e in evals if e.candidate_coverage > 0]
    cond_acc_1 = (sum(e.acc_at_1 for e in covered) / len(covered)) if covered else 0.0
    cond_acc_5 = (sum(e.acc_at_5 for e in covered) / len(covered)) if covered else 0.0

    return {
        "sample_size": n,
        "acc_at_1": round(mean_acc_1, 4),
        "acc_at_5": round(mean_acc_5, 4),
        "mrr_at_5": round(mean_mrr_5, 4),
        "candidate_coverage": round(mean_cov, 4),
        "conditional_acc_at_1": round(cond_acc_1, 4),
        "conditional_acc_at_5": round(cond_acc_5, 4),
        "covered_tasks": len(covered),
        "avg_token_count": round(mean_tokens, 1)
    }
