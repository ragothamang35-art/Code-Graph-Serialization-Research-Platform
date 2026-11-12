"""E2E Test 4.6: Gold Label Extraction from Unified Diffs."""

import inspect
from graphtrust.data import extract_gold_files_from_patch, normalize_path
from graphtrust.retrieval import GraphRetriever
from graphtrust.prompting import build_prompt

def test_unified_diff_header_variants():
    """Test standard diff --git, ---/+++, a/b prefixes, /dev/null, and renames."""
    # 1. Standard git diff
    patch1 = """diff --git a/pkg/service.py b/pkg/service.py
--- a/pkg/service.py
+++ b/pkg/service.py
@@ -10,2 +10,4 @@
+class New: pass
"""
    assert extract_gold_files_from_patch(patch1) == ["pkg/service.py"]

    # 2. Pure --- and +++ without diff --git
    patch2 = """--- a/pkg/auth.py
+++ b/pkg/auth.py
@@ -5,2 +5,4 @@
"""
    assert extract_gold_files_from_patch(patch2) == ["pkg/auth.py"]

    # 3. New file creation from /dev/null
    patch3 = """diff --git a/dev/null b/pkg/metrics.py
--- /dev/null
+++ b/pkg/metrics.py
@@ -0,0 +1,5 @@
"""
    assert extract_gold_files_from_patch(patch3) == ["pkg/metrics.py"]

    # 4. Git file rename
    patch4 = """diff --git a/pkg/old_session.py b/pkg/session.py
rename from pkg/old_session.py
rename to pkg/session.py
--- a/pkg/old_session.py
+++ b/pkg/session.py
"""
    assert extract_gold_files_from_patch(patch4) == ["pkg/session.py"]

def test_test_file_exclusion():
    """Assert test paths are excluded from gold label localization targets."""
    patch_with_tests = """diff --git a/pkg/core.py b/pkg/core.py
--- a/pkg/core.py
+++ b/pkg/core.py
diff --git a/tests/test_core.py b/tests/test_core.py
--- a/tests/test_core.py
+++ b/tests/test_core.py
diff --git a/pkg/tests/test_unit.py b/pkg/tests/test_unit.py
--- a/pkg/tests/test_unit.py
+++ b/pkg/tests/test_unit.py
"""
    extracted = extract_gold_files_from_patch(patch_with_tests, exclude_tests=True)
    assert extracted == ["pkg/core.py"]
    assert "tests/test_core.py" not in extracted
    assert "pkg/tests/test_unit.py" not in extracted

def test_gold_labels_never_in_retrieval_or_prompting_signatures():
    """
    Static safety invariant: GraphRetriever.retrieve and build_prompt
    must NEVER accept or take gold_files or patch as parameters.
    """
    retrieve_params = list(inspect.signature(GraphRetriever.retrieve).parameters.keys())
    assert "gold" not in str(retrieve_params).lower()
    assert "patch" not in str(retrieve_params).lower()

    prompt_params = list(inspect.signature(build_prompt).parameters.keys())
    assert "gold" not in str(prompt_params).lower()
    assert "patch" not in str(prompt_params).lower()
