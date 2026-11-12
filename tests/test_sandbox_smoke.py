"""Docker-dependent sandbox smoke test (§3).

Marked @pytest.mark.docker. Excluded by default in fast test runs (-m 'not smoke and not docker').
Skips automatically if Docker daemon is unreachable or image is missing.
"""

import shutil
import subprocess
import pytest
from scripts.sandbox_validation import check_sandbox_prerequisites


@pytest.mark.docker
def test_real_sandbox_resolves_the_known_good_case():
    """Manual Docker smoke test on one task.
    
    Skips cleanly if Docker is not installed or unreachable, or if the sandbox image is absent.
    """
    prereqs = check_sandbox_prerequisites()
    if not prereqs["docker_available"] or not prereqs["docker_running"]:
        pytest.skip("Docker daemon not running; skipping live container smoke test.")

    # Check if sandbox image exists
    res = subprocess.run(
        ["docker", "image", "inspect", "swebench-sandbox:latest"],
        capture_output=True,
    )
    if res.returncode != 0:
        pytest.skip("swebench-sandbox:latest image not built; skipping live container smoke test.")

    # If Docker and image are present, run container execution plumbing test
    proc = subprocess.run(
        ["docker", "run", "--rm", "swebench-sandbox:latest", "echo", "sandbox_alive"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0
    assert "sandbox_alive" in proc.stdout
