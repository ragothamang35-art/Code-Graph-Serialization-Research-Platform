"""E2E Test 4.1: CLI Surface (inspect)."""

import pytest
from pathlib import Path

def test_cli_inspect_valid_synthetic_fixture(cli_runner, synthetic_repo):
    """
    Assert inspect on synthetic fixture exits 0 and reports exact record counts:
    7 tasks, 15 nodes, 12 edges, 15 embeddings, 256 dim.
    """
    res = cli_runner("inspect", "--data-dir", str(synthetic_repo))
    assert res.returncode == 0
    stdout = res.stdout
    assert "GraphTrust Dataset Inspection Report" in stdout
    assert "total_tasks: 7" in stdout
    assert "graph_nodes: 15" in stdout
    assert "graph_edges: 12" in stdout
    assert "embeddings_count: 15" in stdout
    assert "embedding_dimension: 256" in stdout
    assert "tasks_missing_gold_labels: 0" in stdout

def test_cli_inspect_missing_file_fails_cleanly(cli_runner, tmp_path):
    """
    Assert inspect on broken fixture (missing embeddings) exits non-zero,
    identifies missing file by name, and never crashes with an unhandled traceback.
    """
    broken_dir = tmp_path / "broken_repo"
    broken_dir.mkdir()
    # Write only tasks.json, deliberately omit embeddings.json and graph files
    (broken_dir / "tasks.json").write_text("[]", encoding="utf-8")

    res = cli_runner("inspect", "--data-dir", str(broken_dir), check=False)
    assert res.returncode != 0
    assert "Missing required file(s)" in res.stderr
    assert "embeddings.json" in res.stderr
    # Confirm no raw unhandled python traceback
    assert "Traceback (most recent call last)" not in res.stderr
