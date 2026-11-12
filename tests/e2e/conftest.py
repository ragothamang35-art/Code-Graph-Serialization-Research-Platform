"""Pytest configuration and fixtures for GraphTrust E2E automation."""

import os
import sys
import subprocess
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures"
SYNTHETIC_REPO_DIR = FIXTURES_DIR / "synthetic_repo"
TEST_CONFIG_PATH = FIXTURES_DIR / "configs" / "test_e2e.yaml"

@pytest.fixture(scope="session")
def repo_root():
    return ROOT_DIR

@pytest.fixture(scope="session")
def synthetic_repo():
    return SYNTHETIC_REPO_DIR

@pytest.fixture(scope="session")
def test_config():
    return TEST_CONFIG_PATH

@pytest.fixture
def scratch_outputs(tmp_path):
    out = tmp_path / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    return out

@pytest.fixture
def cli_runner(repo_root):
    """Subprocess runner for CLI boundary tests."""
    def _run(subcommand: str, *args, check: bool = True):
        env = dict(os.environ)
        # Ensure PYTHONPATH includes graphtrust/src
        src_path = str(repo_root / "graphtrust" / "src")
        env["PYTHONPATH"] = f"{src_path}:{env.get('PYTHONPATH', '')}".rstrip(":")
        
        cmd = [sys.executable, "-m", "graphtrust.cli", subcommand] + list(args)
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True
        )
        if check and proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr
            )
        return proc
    return _run
