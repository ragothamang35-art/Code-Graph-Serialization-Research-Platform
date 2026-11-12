"""E2E Test 4.9: Resume and No Overwrite."""

import json
from pathlib import Path
from graphtrust.data import DatasetLoader
from graphtrust.retrieval import GraphRetriever
from graphtrust.model import GemmaAgent
from graphtrust.experiment import ControlledExperiment

def test_resume_preserves_completed_tasks_without_clobber(synthetic_repo, tmp_path):
    """
    Assert that resuming an interrupted experiment does not clobber
    completed tasks and continues to process remaining tasks.
    """
    loader = DatasetLoader(str(synthetic_repo))
    tasks = loader.load_tasks()
    nodes, edges = loader.load_graph()
    retriever = GraphRetriever(nodes, edges)
    agent = GemmaAgent(is_mock=True)

    exp_dir = tmp_path / "exp_resumable"

    # Step 1: Run on task 0 only
    exp1 = ControlledExperiment(
        retriever=retriever,
        agent=agent,
        output_dir=str(tmp_path),
        experiment_id="exp_resumable"
    )
    exp1.run_benchmark(tasks, limit=1, budget=2048)

    # Check that task 0 predictions exist
    task0_pred_file = exp_dir / "predictions" / f"{tasks[0].instance_id}_json_2048tokens.json"
    assert task0_pred_file.exists()
    mtime_before = task0_pred_file.stat().st_mtime

    # Step 2: Resume with limit=2
    exp2 = ControlledExperiment(
        retriever=retriever,
        agent=agent,
        output_dir=str(tmp_path),
        experiment_id="exp_resumable",
        resume=True
    )
    exp2.run_benchmark(tasks, limit=2, budget=2048)

    # Task 1 predictions must now exist
    task1_pred_file = exp_dir / "predictions" / f"{tasks[1].instance_id}_json_2048tokens.json"
    assert task1_pred_file.exists()

    # Task 0 predictions must NOT have been clobbered/modified
    mtime_after = task0_pred_file.stat().st_mtime
    assert mtime_before == mtime_after, "Completed task was re-run or clobbered on resume!"
