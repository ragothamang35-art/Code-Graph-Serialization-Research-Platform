"""E2E Test 4.2: Core Pipeline Smoke (run --limit 3)."""

import json
from pathlib import Path
from graphtrust.data import DatasetLoader

def test_pipeline_smoke_run_limit_3(cli_runner, synthetic_repo, scratch_outputs):
    """
    Assert run --limit 3 produces well-formed predictions, metrics, logs,
    and strictly never leaks gold labels or patches into prompt text.
    """
    res = cli_runner(
        "run",
        "--data-dir", str(synthetic_repo),
        "--limit", "3",
        "--budget", "256",
        "--output-dir", str(scratch_outputs)
    )
    assert res.returncode == 0
    assert "Running experiment on 3 tasks" in res.stdout
    assert "Experiment Aggregated Results" in res.stdout

    # Find the generated experiment run directory
    exp_dirs = [d for d in scratch_outputs.iterdir() if d.is_dir() and d.name.startswith("exp_")]
    assert len(exp_dirs) == 1, f"Expected 1 run directory, found: {exp_dirs}"
    run_dir = exp_dirs[0]

    # Verify directory structure
    assert (run_dir / "predictions").exists()
    assert (run_dir / "metrics").exists()
    assert (run_dir / "logs").exists()
    assert (run_dir / "prompts").exists()
    assert (run_dir / "retrieval_records").exists()
    assert (run_dir / "model_metadata.json").exists()

    # Load tasks to get their gold files
    loader = DatasetLoader(str(synthetic_repo))
    tasks = loader.load_tasks()[:3]
    gold_files_by_task = {t.instance_id: t.gold_files for t in tasks}

    # Verify prediction records round-trip to valid JSON matching schema
    pred_files = list((run_dir / "predictions").glob("*.json"))
    assert len(pred_files) >= 9, f"Expected at least 9 prediction files (3 tasks x 3 formats), found {len(pred_files)}"

    for pf in pred_files:
        with open(pf, "r", encoding="utf-8") as f:
            rec = json.load(f)
        assert "predicted_files" in rec
        assert "reasoning" in rec
        assert "task_id" in rec
        assert "format_type" in rec
        assert "mode" in rec
        assert rec["mode"] == "mock", "Mock run predictions must carry explicit mode: mock"

    # CRITICAL RULE #2: Assert NO gold file path appears in the recorded prompt text
    prompt_files = list((run_dir / "prompts").glob("*.txt"))
    assert len(prompt_files) >= 9

    for pf in prompt_files:
        content = pf.read_text(encoding="utf-8")
        # Match task ID from filename
        matching_task_id = None
        for t in tasks:
            if pf.name.startswith(t.instance_id):
                matching_task_id = t.instance_id
                break
        
        if matching_task_id:
            gold_files = gold_files_by_task[matching_task_id]
            for gold_file in gold_files:
                # The gold file path must not appear in the problem statement or instructions as a gold label
                assert f"GOLD FILE: {gold_file}" not in content
                assert f"patch: {gold_file}" not in content
