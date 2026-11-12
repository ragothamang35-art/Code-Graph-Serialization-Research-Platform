# GraphTrust End-to-End (E2E) Test Suite

## Overview
This automated E2E test suite validates the entire research pipeline—from dataset loading and 5-step canonical retrieval through tri-format serialization, token budgeting, mock inference, gold-label extraction, evaluation, and statistical significance analysis—strictly enforcing all research integrity rules and experimental invariants.

---

## Quickstart

Run the full hermetic E2E test suite locally or in CI:

```bash
PYTHONPATH=graphtrust/src pytest tests/e2e -v
```

Run only fast mock E2E tests (excluding any optional real-model tests):

```bash
PYTHONPATH=graphtrust/src pytest tests/e2e -m "not real_model" -v
```

---

## Test Organization

| Test File | Description | Dev Prompt Coverage |
| :--- | :--- | :---: |
| `test_cli_inspect.py` | Inspects synthetic repository record counts, embedding dimensions, and verifies missing-file error handling. | §5, §15 |
| `test_cli_validate.py` | Validates invariant checking and verifies that nonexistent model paths fail cleanly rather than silently falling back. | §4, §21 |
| `test_pipeline_smoke.py` | Runs `run --limit 3` end-to-end; asserts well-formed outputs and verifies that gold files/patches NEVER leak into prompts. | §9, §20, §21 |
| `test_invariant_same_subgraph.py` | **THE Core Invariant**: Verifies that Format A (JSON), Format B (Adjacency), and Format C (Natural Language) represent identical node and edge sets. | §3, §19, §21 |
| `test_token_budget_enforcement.py` | Tests non-destructive truncation across budgets (128/256/512/4096t) and verifies fixed prompt offset accounting. | §8, §19 |
| `test_baselines.py` | Verifies `No Graph` condition has 0 graph tokens and `Keyword Match` matches lexical retrieval. | §7 |
| `test_gold_label_extraction.py` | Tests unified diff variants (`diff --git`, `---`/`+++`, `a/`/`b/`, `/dev/null`, renames) and verifies test file exclusion. | §10, §19 |
| `test_json_output_contract.py` | Asserts strict JSON output, markdown fence stripping (` ```json `), and graceful handling of malformed outputs. | §9 |
| `test_metrics_correctness.py` | Verifies Acc@1, Acc@5, MRR@5 against hand-computed values and asserts candidate coverage is reported independently. | §11, §19 |
| `test_reproducibility_artifacts.py` | Asserts all artifacts (config snapshot, model metadata with MOCK marker, seeds, execution time) are persisted. | §18 |
| `test_resume_and_no_overwrite.py` | Simulates partial/interrupted runs and verifies that resuming does not clobber or re-run completed tasks. | §18 |
| `test_cli_analyze.py` | Verifies `analyze` calculates paired statistics (bootstrap CIs, t-test, Cohen's d) and flags when $N < 3$. | §12, §15 |
| `test_cli_ablate.py` | Verifies depth ablation (0, 1, 2 hops) produces non-decreasing node counts and saves to separate `outputs/ablations/`. | §13, §15 |
| `test_mock_vs_real_labeling.py` | Verifies that every single mock artifact carries an explicit `"mode": "mock"` or `"is_mock": True` marker. | §4, §21 |

---

## Fixtures

- **`tests/fixtures/synthetic_repo/`**: Deterministic synthetic dataset (7 tasks, 15 nodes, 12 edges, 15 256-d embeddings).
  - Includes task `syn__task-006-unretrievable-gold` whose gold file is deliberately omitted from the graph to verify coverage-failure vs serialization-failure independence.
  - Includes diff variants: standard git diff, triple-plus prefix, `/dev/null` addition, file rename, test file exclusion.
- **`tests/fixtures/mock_model.py`**: Deterministic mock agent mimicking Gemma 4 E2B behavior without requiring external weights or network access.
- **`tests/fixtures/configs/test_e2e.yaml`**: Hermetic configuration for test execution.

---

## Optional Real-Model Execution

To run tests against the real Gemma 4 E2B GGUF model via llama-cpp-python:

```bash
export GEMMA_MODEL_PATH="/path/to/gemma-4-e2b.Q4_K_M.gguf"
PYTHONPATH=graphtrust/src pytest tests/e2e -m "real_model" -v
```
