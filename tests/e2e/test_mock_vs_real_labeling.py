"""E2E Test 4.11: Mock vs Real Output Labeling."""

import json
from pathlib import Path

def test_all_mock_artifacts_carry_explicit_mode_marker(cli_runner, synthetic_repo, scratch_outputs):
    """
    Rule: Never let mock results look like real results.
    Assert every artifact type (metadata, predictions, metrics CSV, metrics JSON, logs)
    carries an explicit 'mode': 'mock' or 'mock' marker.
    """
    cli_runner("run", "--data-dir", str(synthetic_repo), "--limit", "2", "--budget", "2048", "--output-dir", str(scratch_outputs))

    exp_dirs = [d for d in scratch_outputs.iterdir() if d.is_dir() and d.name.startswith("exp_")]
    assert len(exp_dirs) == 1
    run_dir = exp_dirs[0]

    # 1. Model metadata
    meta = json.loads((run_dir / "model_metadata.json").read_text(encoding="utf-8"))
    assert meta.get("mode") == "mock" or meta.get("is_mock") is True

    # 2. Prediction records
    for pf in (run_dir / "predictions").glob("*.json"):
        pdata = json.loads(pf.read_text(encoding="utf-8"))
        assert pdata.get("mode") == "mock" or pdata.get("is_mock") is True

    # 3. Metrics JSON
    for mf in (run_dir / "metrics").glob("*.json"):
        mdata = json.loads(mf.read_text(encoding="utf-8"))
        assert mdata.get("mode") == "mock" or mdata.get("is_mock") is True

    # 4. Metrics CSV
    for cf in (run_dir / "metrics").glob("*.csv"):
        csv_text = cf.read_text(encoding="utf-8")
        assert "mock" in csv_text.lower(), f"CSV {cf.name} missing mock label"

    # 5. Logs
    for lf in (run_dir / "logs").glob("*.log"):
        log_text = lf.read_text(encoding="utf-8")
        assert "mock" in log_text.lower(), f"Log {lf.name} missing mock label"
