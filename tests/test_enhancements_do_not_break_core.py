"""Integration and non-interference tests (§4).

Verifies that the presence of enhancement files (cross_model_comparison.csv,
significance_tests.md, case_studies.md) alongside core results does not alter,
clobber, or crash the core analysis engine.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path
import pytest


def test_analyze_py_still_runs_with_enhancement_files_present(tmp_path, repo_root):
    """Core analyze command runs identically and outputs expected metrics when enhancement files are present."""
    results_dir = tmp_path / "results_scratch"
    results_dir.mkdir()

    # Create a valid core experiment_results JSON
    core_experiment_data = {
        "experiment_id": "core_baseline_run",
        "sample_size": 4,
        "budget": 2048,
        "aggregated_metrics": {
            "json": {
                "acc_at_1": 0.5,
                "acc_at_5": 0.75,
                "mrr_at_5": 0.625,
                "candidate_coverage": 1.0,
                "avg_token_count": 680.0,
            },
            "natural_language": {
                "acc_at_1": 0.75,
                "acc_at_5": 1.0,
                "mrr_at_5": 0.875,
                "candidate_coverage": 1.0,
                "avg_token_count": 315.0,
            },
        },
        "task_level_records": [
            {
                "task_id": "t1",
                "results": {
                    "json": {"token_count": 650, "correct_at_1": True},
                    "natural_language": {"token_count": 310, "correct_at_1": True},
                },
            },
            {
                "task_id": "t2",
                "results": {
                    "json": {"token_count": 700, "correct_at_1": False},
                    "natural_language": {"token_count": 320, "correct_at_1": True},
                },
            },
            {
                "task_id": "t3",
                "results": {
                    "json": {"token_count": 670, "correct_at_1": True},
                    "natural_language": {"token_count": 310, "correct_at_1": True},
                },
            },
            {
                "task_id": "t4",
                "results": {
                    "json": {"token_count": 700, "correct_at_1": False},
                    "natural_language": {"token_count": 320, "correct_at_1": False},
                },
            },
        ],
    }

    core_file = results_dir / "experiment_results_baseline.json"
    with open(core_file, "w", encoding="utf-8") as f:
        json.dump(core_experiment_data, f, indent=2)

    # 1. Run core analyze first (baseline output)
    env = dict(sys.modules.get("os", __import__("os")).environ)
    src_path = str(repo_root / "graphtrust" / "src")
    env["PYTHONPATH"] = f"{src_path}:{str(repo_root)}:{env.get('PYTHONPATH', '')}".rstrip(":")

    cmd = [sys.executable, "-m", "graphtrust.cli", "analyze", "--results-dir", str(results_dir)]
    baseline_run = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True)
    assert baseline_run.returncode == 0
    assert "Acc@1=0.5" in baseline_run.stdout
    assert "Acc@1=0.75" in baseline_run.stdout

    # 2. Inject enhancement files into the same results directory
    (results_dir / "cross_model_comparison.csv").write_text(
        "task_id,repo,model,format,budget,seed,candidate_coverage,correct_at1,correct_at3,correct_at5,token_count,latency_ms,mode\n"
        "t1,r,M,json,512,42,1.0,true,true,true,500,100,mock\n",
        encoding="utf-8"
    )
    (results_dir / "significance_tests.md").write_text(
        "# Significance Tests\n| Pair | Delta | p-value |\n",
        encoding="utf-8"
    )
    (results_dir / "case_studies.md").write_text(
        "# Case Studies\nTranscript details.\n",
        encoding="utf-8"
    )
    (results_dir / "sandbox_validation.csv").write_text(
        "task_id,condition,patch_applied,tests_passed,mode\n"
        "t1,json,false,false,mock\n",
        encoding="utf-8"
    )

    # 3. Run core analyze again with enhancement files present
    enhanced_run = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True)
    assert enhanced_run.returncode == 0
    # Core output must remain identical and completely uncorrupted
    assert baseline_run.stdout == enhanced_run.stdout
    assert "Acc@1=0.5" in enhanced_run.stdout
    assert "Acc@1=0.75" in enhanced_run.stdout
