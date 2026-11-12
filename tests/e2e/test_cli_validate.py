"""E2E Test 4.1: CLI Surface (validate)."""

import pytest
from pathlib import Path

def test_cli_validate_success(cli_runner, test_config):
    """Assert validate against test config passes and verifies invariants."""
    res = cli_runner("validate", "--config", str(test_config))
    assert res.returncode == 0
    assert "Controlled Invariant Validation" in res.stdout
    assert "Controlled invariant verified" in res.stdout

def test_cli_validate_nonexistent_model_fails_informative(cli_runner, tmp_path, synthetic_repo):
    """
    Assert validate against a config with nonexistent model path (when is_mock=false)
    fails with an informative message rather than silently falling back (Rule #5).
    """
    bad_config = tmp_path / "bad_model.yaml"
    bad_config.write_text(f"""
data:
  data_dir: "{synthetic_repo}"
model:
  path: "/nonexistent/path/to/gemma-4-e2b.gguf"
  is_mock: false
""", encoding="utf-8")

    res = cli_runner("validate", "--config", str(bad_config), check=False)
    assert res.returncode != 0
    assert "Configured model file does not exist" in res.stderr
    assert "/nonexistent/path/to/gemma-4-e2b.gguf" in res.stderr
    assert "rule #5" in res.stderr
