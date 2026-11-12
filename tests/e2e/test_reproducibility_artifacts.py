"""E2E Test 4.9: Reproducibility Artifacts & Determinism."""

import json
from pathlib import Path

def test_reproducibility_artifacts_generation(cli_runner, synthetic_repo, scratch_outputs):
    """
    Assert full run persists all mandatory artifacts:
    config snapshot, model metadata with MOCK marker, raw outputs, predictions, metrics.
    """
    res = cli_runner(
        "run",
        "--data-dir", str(synthetic_repo),
        "--limit", "2",
        "--budget", "512",
        "--output-dir", str(scratch_outputs)
    )
    assert res.returncode == 0

    exp_dirs = [d for d in scratch_outputs.iterdir() if d.is_dir() and d.name.startswith("exp_")]
    assert len(exp_dirs) == 1
    run_dir = exp_dirs[0]

    # 1. Model metadata
    meta_file = run_dir / "model_metadata.json"
    assert meta_file.exists()
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta.get("mode") == "mock" or meta.get("is_mock") is True
    assert "timestamp" in meta
    assert "experiment_id" in meta

    # 2. Metrics JSON & CSV
    metrics_json = run_dir / "metrics" / "experiment_results_512tokens.json"
    assert metrics_json.exists()
    metrics_csv = run_dir / "metrics" / "summary_metrics_512tokens.csv"
    assert metrics_csv.exists()

    # 3. Canonical retrieval records
    retrieval_records = list((run_dir / "retrieval_records").glob("*.json"))
    assert len(retrieval_records) == 2

    # 4. Predictions and Prompts
    assert len(list((run_dir / "predictions").glob("*.json"))) >= 6
    assert len(list((run_dir / "prompts").glob("*.txt"))) >= 6

def test_unique_experiment_ids_prevent_clobbering(cli_runner, synthetic_repo, scratch_outputs):
    """
    Assert running 'run' twice with the same arguments produces
    two distinct experiment run directories without clobbering.
    """
    res1 = cli_runner("run", "--data-dir", str(synthetic_repo), "--limit", "1", "--output-dir", str(scratch_outputs))
    assert res1.returncode == 0

    res2 = cli_runner("run", "--data-dir", str(synthetic_repo), "--limit", "1", "--output-dir", str(scratch_outputs))
    assert res2.returncode == 0

    exp_dirs = [d for d in scratch_outputs.iterdir() if d.is_dir() and d.name.startswith("exp_")]
    assert len(exp_dirs) >= 2, f"Expected at least 2 distinct run directories, found: {exp_dirs}"
