"""Unit tests for sandbox patch application and validation (§4).

Uses a tiny synthetic local git repository built inside tmp_path at test time.
Requires zero Docker daemon or external dependencies.
"""

import subprocess
from pathlib import Path
from unittest.mock import patch
import pytest

from scripts.sandbox_validation import (
    apply_unified_diff,
    validate_task_patch,
    check_sandbox_prerequisites,
)


@pytest.fixture
def synthetic_git_repo(tmp_path):
    """Build a tiny synthetic git repo with a bug and failing test inside tmp_path."""
    repo_dir = tmp_path / "tiny_repo"
    repo_dir.mkdir()

    # Git init
    subprocess.run(["git", "init"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@graphtrust.org"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "GraphTrust Test"], cwd=str(repo_dir), check=True, capture_output=True)

    # Buggy source file (off-by-one error)
    buggy_code = "def add(a, b):\n    return a + b + 1  # off-by-one\n"
    (repo_dir / "calculator.py").write_text(buggy_code, encoding="utf-8")

    # Failing unit test
    test_code = (
        "import sys\n"
        "from calculator import add\n"
        "if __name__ == '__main__':\n"
        "    res = add(2, 3)\n"
        "    if res != 5:\n"
        "        sys.exit(1)\n"
        "    sys.exit(0)\n"
    )
    (repo_dir / "test_calculator.py").write_text(test_code, encoding="utf-8")

    subprocess.run(["git", "add", "."], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial commit with buggy add()"], cwd=str(repo_dir), check=True, capture_output=True)

    return repo_dir


KNOWN_GOOD_DIFF = """--- a/calculator.py
+++ b/calculator.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a + b + 1  # off-by-one
+    return a + b
"""

KNOWN_BAD_DIFF = """--- a/nonexistent_file.py
+++ b/nonexistent_file.py
@@ -1,1 +1,1 @@
-bad
+broken
"""


def test_known_good_patch_applies_cleanly(synthetic_git_repo):
    """Applying a well-formed unified diff succeeds on the synthetic repo."""
    success = apply_unified_diff(synthetic_git_repo, KNOWN_GOOD_DIFF)
    assert success is True


def test_known_bad_patch_fails_to_apply_and_is_recorded_not_raised(synthetic_git_repo):
    """Malformed or invalid diff returns patch_applied=False rather than raising an unhandled exception."""
    res = validate_task_patch(synthetic_git_repo, "task_dummy", "raw_json", KNOWN_BAD_DIFF)
    assert res["patch_applied"] is False
    assert res["task_id"] == "task_dummy"
    assert res["condition"] == "raw_json"


def test_tests_passed_is_false_when_patch_does_not_apply(synthetic_git_repo):
    """Contract: if patch_applied is False, tests_passed must be strictly False (never True or omitted)."""
    # Even if test_cmd passes on unpatched code, a failed patch must result in tests_passed=False
    res = validate_task_patch(
        synthetic_git_repo,
        task_id="task_fail",
        condition="raw_json",
        diff_text=KNOWN_BAD_DIFF,
        test_cmd=["python3", "test_calculator.py"],
    )
    assert res["patch_applied"] is False
    assert res["tests_passed"] is False


def test_result_row_schema_matches_spec(synthetic_git_repo):
    """Assert output record has exactly task_id, condition, patch_applied, tests_passed."""
    res_good = validate_task_patch(
        synthetic_git_repo,
        task_id="task_good",
        condition="nl_sentences",
        diff_text=KNOWN_GOOD_DIFF,
        test_cmd=["python3", "test_calculator.py"],
    )
    assert set(res_good.keys()) == {"task_id", "condition", "patch_applied", "tests_passed"}
    assert res_good["patch_applied"] is True
    assert res_good["tests_passed"] is True

    # Revert repo for next test
    subprocess.run(["git", "checkout", "calculator.py"], cwd=str(synthetic_git_repo), check=True, capture_output=True)

    res_bad = validate_task_patch(
        synthetic_git_repo,
        task_id="task_bad",
        condition="raw_json",
        diff_text=KNOWN_BAD_DIFF,
        test_cmd=["python3", "test_calculator.py"],
    )
    assert set(res_bad.keys()) == {"task_id", "condition", "patch_applied", "tests_passed"}
    assert res_bad["patch_applied"] is False
    assert res_bad["tests_passed"] is False


def test_docker_availability_check_returns_false_when_docker_missing():
    """Simulate missing docker binary and assert pre-flight check detects it cleanly."""
    with patch("shutil.which", return_value=None):
        prereqs = check_sandbox_prerequisites()
        assert prereqs["docker_available"] is False
        assert prereqs["abandon_triggered"] is True
        assert any("Docker CLI not installed" in r for r in prereqs["reasons"])
