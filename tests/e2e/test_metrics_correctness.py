"""E2E Test 4.8: Evaluation Metrics Correctness & Candidate Coverage Separation."""

import pytest
from graphtrust.schema import Task, ModelPrediction, RetrievedSubgraph
from graphtrust.evaluation import evaluate_task, aggregate_evaluations, compute_reciprocal_rank_5

def test_hand_computed_metric_formulas():
    """Verify Acc@1, Acc@5, and MRR@5 against known manual calculations."""
    gold = ["src/auth.py", "src/token.py"]

    # 1. Hit at Rank 1 -> Acc@1=1.0, Acc@5=1.0, MRR@5=1.0
    preds_rank1 = ["src/auth.py", "src/other.py"]
    assert compute_reciprocal_rank_5(preds_rank1, gold) == 1.0

    # 2. Hit at Rank 2 -> Acc@1=0.0, Acc@5=1.0, MRR@5=0.5
    preds_rank2 = ["src/wrong.py", "src/auth.py"]
    assert compute_reciprocal_rank_5(preds_rank2, gold) == 0.5

    # 3. Hit at Rank 4 -> Acc@1=0.0, Acc@5=1.0, MRR@5=0.25
    preds_rank4 = ["src/w1.py", "src/w2.py", "src/w3.py", "src/token.py"]
    assert compute_reciprocal_rank_5(preds_rank4, gold) == 0.25

    # 4. Hit at Rank 6 (outside top 5) -> Acc@1=0.0, Acc@5=0.0, MRR@5=0.0
    preds_rank6 = ["s1.py", "s2.py", "s3.py", "s4.py", "s5.py", "src/token.py"]
    assert compute_reciprocal_rank_5(preds_rank6, gold) == 0.0

def test_candidate_coverage_separated_from_end_to_end_accuracy():
    """
    Assert that when a gold file is missing from candidate set (retrieval failure),
    candidate coverage is 0.0, and the task remains in the overall accuracy denominator.
    """
    # Task whose gold file is "pkg/isolated_plugin.py"
    task_unretrievable = Task(
        instance_id="task_unretrievable",
        repo="synthetic/repo",
        base_commit="abc",
        problem_statement="plugin bug",
        gold_files=["pkg/isolated_plugin.py"]
    )
    # Subgraph candidate files only contain other files
    subgraph = RetrievedSubgraph(
        nodes=[], edges=[], seed_node_ids=[],
        candidate_files=["pkg/service.py", "pkg/client.py"]
    )
    # Model predicts candidate files
    pred = ModelPrediction(
        task_id="task_unretrievable",
        format_type="json",
        budget=1024,
        predicted_files=["pkg/service.py"],
        reasoning="model reasoned on available evidence",
        raw_output="{}",
        parsing_success=True
    )

    ev = evaluate_task(task_unretrievable, pred, subgraph, token_count=100)
    assert ev.candidate_coverage == 0.0, "Coverage must be 0.0 when gold file is absent from candidate set"
    assert ev.acc_at_1 == 0.0
    assert ev.conditional_acc_1 == 0.0

    # Aggregate with a successful covered task
    task_covered = Task(
        instance_id="task_covered",
        repo="synthetic/repo",
        base_commit="abc",
        problem_statement="service bug",
        gold_files=["pkg/service.py"]
    )
    subgraph_covered = RetrievedSubgraph(
        nodes=[], edges=[], seed_node_ids=[],
        candidate_files=["pkg/service.py"]
    )
    pred_covered = ModelPrediction(
        task_id="task_covered",
        format_type="json",
        budget=1024,
        predicted_files=["pkg/service.py"],
        reasoning="correct",
        raw_output="{}",
        parsing_success=True
    )
    ev_covered = evaluate_task(task_covered, pred_covered, subgraph_covered, token_count=100)

    agg = aggregate_evaluations([ev, ev_covered])
    assert agg["sample_size"] == 2
    # End-to-end Acc@1 is 1/2 = 0.50 (both tasks in denominator)
    assert agg["acc_at_1"] == 0.50
    # Candidate coverage is 1/2 = 0.50
    assert agg["candidate_coverage"] == 0.50
    # Conditional Acc@1 (given covered) is 1/1 = 1.0
    assert agg["conditional_acc_at_1"] == 1.0
