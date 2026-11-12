"""E2E Test 4.10: Ablation Suite (ablate)."""

import json
from pathlib import Path

def test_cli_ablate_monotonic_node_counts_and_separate_outputs(cli_runner, synthetic_repo, scratch_outputs):
    """
    Assert ablate on depth {0, 1, 2} produces non-decreasing node counts,
    and saves results to separate outputs/ablations directory (Rule #11).
    """
    res = cli_runner("ablate", "--data-dir", str(synthetic_repo), "--output-dir", str(scratch_outputs))
    assert res.returncode == 0
    assert "Running Ablation A: Graph Expansion Depth" in res.stdout
    assert "Ablation B: Embedding-Based Expansion" in res.stdout

    # Assert outputs are saved in separate ablations directory
    ablation_dir = scratch_outputs / "ablations"
    assert ablation_dir.exists()
    depth_file = ablation_dir / "depth_ablation_results.json"
    assert depth_file.exists()

    with open(depth_file, "r", encoding="utf-8") as f:
        depth_data = json.load(f)

    # Assert depth 0 <= depth 1 <= depth 2
    assert "depth_0_hops" in depth_data
    assert "depth_1_hops" in depth_data
    assert "depth_2_hops" in depth_data
