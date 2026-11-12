# GraphTrust — Automated End-to-End Test Suite Report

**Project**: GraphTrust (Kaggle Gemma 4 Developer Agent Paper Competition)  
**Role**: Senior QA Automation Engineer & Research Test Architect  
**Date**: November 2026  
**Status**: **ALL TESTS PASSED (56 / 56 Tests, 100% Green, 1 Optional Docker Smoke Test Skipped)**  

---

## 1. Executive Summary

We designed, implemented, and executed a complete automated End-to-End (E2E) and enhancement test suite validating the entire GraphTrust pipeline—from dataset ingestion through canonical graph retrieval, tri-format serialization, non-destructive token budgeting, model inference, unified diff gold-label extraction, paired statistical hypothesis testing (McNemar & bootstrap CIs), cross-model generalization, and sandbox patch validation.

### Test Execution Summary
- **Unit Test Suite** (`graphtrust/tests/test_all.py`): **6 / 6 Passed (100%)** in 0.005s.
- **Fast Pytest Test Suite** (`tests/` and `tests/e2e/`): **50 / 50 Passed (100%)** in 4.96s.
- **Docker-Dependent Smoke Test** (`tests/test_sandbox_smoke.py`): **1 Skipped Cleanly** (tagged `@pytest.mark.docker`, excludes Docker dependency from fast CI runs).
- **Combined Test Total**: **56 Passed, 1 Skipped, 0 Failed (100% Pass Rate)**.

---

## 2. Test Cases & Research Invariant Verification

| Section | Test File | Verified Invariant / Rule | Result |
| :--- | :--- | :--- | :---: |
| **§4.1** | `test_cli_inspect.py` | Exact counts verified on synthetic fixture (7 tasks, 15 nodes, 12 edges, 15 embeddings). Missing files report cleanly with exit code 1; no raw traceback. | **PASSED** |
| **§4.1** | `test_cli_validate.py` | Controlled invariant validated. Nonexistent model path fails informatively without silent fallback (Rule #5). | **PASSED** |
| **§4.2** | `test_pipeline_smoke.py` | `run --limit 3` produces all artifact directories. **Rule #2 Verified**: Zero gold labels or patch strings leak into prompts. | **PASSED** |
| **§4.3** | `test_invariant_same_subgraph.py` | **THE Core Invariant**: For every task, retrieved node and edge ID sets are byte-for-byte identical across JSON, Adjacency, and Natural Language. Truncation never cuts mid-node or mid-edge. | **PASSED** |
| **§4.4** | `test_token_budget_enforcement.py` | Included node/edge counts are non-increasing as budget shrinks (4096 $\rightarrow$ 128 tokens). Truncation logged explicitly. Prompt overhead included in budget. | **PASSED** |
| **§4.5** | `test_baselines.py` | No Graph condition contains 0 graph tokens in prompt. Keyword Match candidate file list matches independent lexical retrieval. | **PASSED** |
| **§4.6** | `test_gold_label_extraction.py` | Verified against `diff --git`, `---`/`+++`, `a/`/`b/`, `/dev/null`, and renames. Test paths excluded. Static check: gold labels never in retrieval or prompt signatures. | **PASSED** |
| **§4.7** | `test_json_output_contract.py` | Strict JSON parsed. Markdown fences (` ```json `) stripped and handled. Malformed output captured without crashing pipeline. | **PASSED** |
| **§4.8** | `test_metrics_correctness.py` | Acc@1, Acc@5, MRR@5 match hand-computed values. Candidate coverage reported separately; unretrievable gold task remains in accuracy denominator. | **PASSED** |
| **§4.9** | `test_reproducibility_artifacts.py` | Output contains config snapshot, model metadata with MOCK marker, seeds, execution time. Unique experiment IDs prevent clobbering. | **PASSED** |
| **§4.10** | `test_resume_and_no_overwrite.py` | Resuming an experiment skips completed tasks without re-running or clobbering completed task prediction files. | **PASSED** |
| **§4.10** | `test_cli_analyze.py` | `analyze --results-dir` produces mean, bootstrap 95% CIs, paired t-tests, Cohen's d. Flags when $N < 3$. | **PASSED** |
| **§4.10** | `test_cli_ablate.py` | Depth ablation produces non-decreasing node counts ($0 \le 1 \le 2$). Outputs saved separately in `outputs/ablations/` (Rule #11). | **PASSED** |
| **§4.11** | `test_mock_vs_real_labeling.py` | Every artifact type (metadata, predictions, metrics CSV, metrics JSON, logs) carries an explicit `"mode": "mock"` marker (Rule #7). | **PASSED** |
| **§E.1** | `test_case_studies.py` | **Transcript Selection (§1)**: Identifies tasks where format flips outcome; returns empty list cleanly without crashing when all agree; verifies required fields in payload. | **PASSED** |
| **§E.2** | `test_significance.py` | **Significance Rigor (§2)**: Matches hand-computed 10-task example ($p=0.625$, stat=0.25). **Zero-Discordant Edge Case**: Safely handles $a == b$ (returns $p=1.0$, stat=0.0, avoids zero-division). Rejection of mismatched lengths. Bootstrap reproducibility, point-estimate coverage, and centering around zero. | **PASSED** |
| **§E.3** | `test_cross_model_comparison.py` | **Cross-Model Replication (§3)**: Schema matches `raw_results.csv` plus `model` column. Detects ranking agreement on concordant fixture; detects ranking disagreement/flip on inverted fixture. | **PASSED** |
| **§E.4** | `test_sandbox_validation.py` | **Sandbox Patch Validation (§4)**: Tests against synthetic local git repo fixture in `tmp_path`. Known-good diff applies cleanly. Malformed diff recorded as `patch_applied=False` without raising unhandled exceptions. `tests_passed` strictly `False` when patch fails. Verifies output schema. Pre-flight checks detect missing Docker cleanly. | **PASSED** |
| **§E.5** | `test_sandbox_smoke.py` | **Docker Smoke Test (§3)**: Marked `@pytest.mark.docker`. Skips cleanly when Docker daemon or `swebench-sandbox:latest` image is absent. | **SKIPPED (Clean)** |
| **§E.6** | `test_enhancements_do_not_break_core.py` | **Non-Interference Test (§4)**: Placing enhancement files (`cross_model_comparison.csv`, `significance_tests.md`, `case_studies.md`, `sandbox_validation.csv`) alongside core results produces identical outputs with zero mutation or regression. | **PASSED** |


---

## 3. Failures Identified & Fixed During Automation

During initial suite execution, one failure was encountered and resolved:

### Issue: Run Directory Subdirectory Mismatch on Experiment Resume
- **Symptom**: `test_resume_and_no_overwrite.py` failed with `AssertionError: assert False where False = task1_pred_file.exists()`.
- **Root Cause**: In `ControlledExperiment.__init__`, when `resume=True` was passed with an explicit `experiment_id`, `self.run_dir` erroneously defaulted to `self.base_output_dir` rather than `self.base_output_dir / self.experiment_id`, causing the resumed process to write to the parent directory.
- **Fix**: Updated `experiment.py` so `self.run_dir` consistently targets `self.base_output_dir / self.experiment_id` whether `resume` is True or False, and properly discovers existing `exp_*` subdirectories when resuming without an explicit ID.
- **Verification**: Re-ran `test_resume_and_no_overwrite.py` and the full suite; test passed immediately in 0.03s.

---

## 4. Known Gaps & Boundaries

1. **Hermetic Mock vs Real Model**:
   - The default E2E suite executes against the deterministic `MockGemmaAgent` and synthetic repository fixtures (`tests/fixtures/synthetic_repo/`), completing in **1.66s** with zero network calls or external weight dependencies.
   - Real Gemma 4 E2B model inference requires local GGUF weights (`gemma-4-e2b.Q4_K_M.gguf`) and `llama-cpp-python` or live Gemini API access. These are intentionally gated behind `@pytest.mark.real_model` so CI remains fast, free, and 100% reproducible.
2. **Competition Dataset Size**:
   - The synthetic fixture contains 7 tasks and 15 nodes designed to exercise edge cases (renames, `/dev/null`, missing candidate gold files). Full 100+ task benchmark evaluation should be run in a dedicated GPU environment using the CLI reproduction commands.

---

## 5. Exact Commands to Reproduce

```bash
# 1. Run the entire E2E test suite (all 26 tests)
PYTHONPATH=graphtrust/src pytest tests/e2e -v

# 2. Run the unit test suite (6 tests)
PYTHONPATH=graphtrust/src python3 graphtrust/tests/test_all.py

# 3. Run individual test categories
PYTHONPATH=graphtrust/src pytest tests/e2e/test_invariant_same_subgraph.py -v
PYTHONPATH=graphtrust/src pytest tests/e2e/test_gold_label_extraction.py -v
PYTHONPATH=graphtrust/src pytest tests/e2e/test_token_budget_enforcement.py -v
PYTHONPATH=graphtrust/src pytest tests/e2e/test_metrics_correctness.py -v
```
