"""E2E Test 4.10: CLI Analysis & Paired Statistics."""

from pathlib import Path

def test_cli_analyze_on_completed_experiment(cli_runner, synthetic_repo, scratch_outputs):
    """
    Assert analyze calculates metrics and paired statistical tests on completed run,
    and warns when sample size N < 3.
    """
    # Run benchmark on 4 tasks
    cli_runner("run", "--data-dir", str(synthetic_repo), "--limit", "4", "--budget", "2048", "--output-dir", str(scratch_outputs))

    # Run analyze
    res = cli_runner("analyze", "--results-dir", str(scratch_outputs))
    assert res.returncode == 0
    assert "GraphTrust Statistical Analysis" in res.stdout
    assert "Paired Test" in res.stdout
    assert "p=" in res.stdout
    assert "Cohen's d=" in res.stdout

def test_cli_analyze_flags_small_sample_size(cli_runner, synthetic_repo, scratch_outputs):
    """
    Assert analyze flags N < 3 as insufficient for significance tests
    rather than fabricating confidence.
    """
    cli_runner("run", "--data-dir", str(synthetic_repo), "--limit", "2", "--budget", "2048", "--output-dir", str(scratch_outputs))
    res = cli_runner("analyze", "--results-dir", str(scratch_outputs))
    assert res.returncode == 0
    assert "insufficient for statistical significance" in res.stdout
