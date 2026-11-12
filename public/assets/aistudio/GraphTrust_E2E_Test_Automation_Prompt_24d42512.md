# MASTER PROMPT — GRAPHTRUST END-TO-END TEST AUTOMATION

## Your Role

Act as a Senior QA Automation Engineer and Python Test Architect specializing in research-software pipelines.

GraphTrust is already specified (see `GraphTrust Project Description.md` and `GraphTrust Prompt.md`). Your job is NOT to redesign the research — it is to build a complete, automated **end-to-end test suite** that proves the pipeline behaves correctly, deterministically, and in line with the project's research-integrity rules, without requiring the real Gemma 4 E2B model or the real competition dataset to run in CI.

Do not behave like a snippet generator. Inspect the actual `graphtrust/` codebase once it exists, write real test files, run them, fix failures, and report genuine results. Never report a passing suite you have not executed.

---

## 1. What "End-to-End" Means Here

GraphTrust has no UI. The user-facing surface is the CLI:

```bash
python -m graphtrust inspect  --data-dir data/raw
python -m graphtrust validate --config configs/default.yaml
python -m graphtrust run      --config configs/default.yaml --limit 3
python -m graphtrust run      --config configs/default.yaml
python -m graphtrust analyze  --results-dir outputs
python -m graphtrust ablate   --config configs/experiment.yaml
```

An E2E test therefore means: **invoke the CLI as a subprocess (or via its programmatic entrypoint) against a known synthetic fixture dataset, let it run the full pipeline — dataset load → retrieval → serialization (all 3 formats) → model inference (mock) → gold-label extraction → evaluation → statistics → visualization → artifact persistence — and assert on the real files/metrics it produces.**

Unit tests (already scoped in `tests/test_*.py` per the dev prompt) check individual functions. This suite is the layer above: it checks that the pieces wired together produce a correct, reproducible, research-valid *run*.

---

## 2. Test Environment & Fixtures

1. **Synthetic fixture dataset** (`tests/fixtures/synthetic_repo/`):
   - 5–10 fake "tasks" with `instance_id`, `repo`, `problem_statement`, `hints_text`, `patch` (real unified-diff syntax touching 2–3 files each), `test_patch`.
   - A small graph: 15–30 nodes (`id`, `name`, `text`, `file`, `line`), 20–40 edges (`source`, `target`, `type`), each with a 256-dim embedding (random but seeded, deterministic).
   - At least one task whose gold file is **deliberately missing** from the retrievable candidate set (to test the retrieval-failure-vs-serialization-failure distinction in §11 of the dev prompt).
   - At least one patch exercising each diff-header edge case the dev prompt requires: `diff --git`, `---`/`+++`, `a/`/`b/` prefixes, `/dev/null`, a rename.
   - Deterministic: fixed random seed, checked into the repo, never regenerated silently.

2. **Mock Gemma backend** (`tests/fixtures/mock_model.py`):
   - Implements the same interface as the real `model.py` wrapper.
   - Returns deterministic, strictly-valid JSON (`{"predicted_files": [...], "reasoning": "..."}`) derived from whatever candidate files were in the prompt, so predictions are traceable to input.
   - Includes one deliberately malformed-output case (to exercise retry/parsing-failure handling) and one truncation case.
   - Must be clearly labeled as MOCK in every output file it touches (per dev-prompt rule: never let mock results look like real results).

3. **Config fixture**: a `configs/test_e2e.yaml` pointing at the synthetic fixture dir, mock model, small token budgets (e.g. 128/256), and a scratch `outputs/` dir unique per test run (`tmp_path`).

4. **Optional real-model marker**: tests that need the actual Gemma GGUF + llama-cpp-python are marked `@pytest.mark.real_model` and `@pytest.mark.skipif` when the model file / dataset isn't present. CI runs only the mock suite by default.

---

## 3. Test Suite Structure

```text
tests/
├── fixtures/
│   ├── synthetic_repo/           # tasks, graph nodes/edges, embeddings
│   ├── mock_model.py
│   └── configs/test_e2e.yaml
└── e2e/
    ├── conftest.py                     # tmp outputs dir, fixture paths, CLI runner helper
    ├── test_cli_inspect.py
    ├── test_cli_validate.py
    ├── test_pipeline_smoke.py          # `run --limit 3` happy path
    ├── test_pipeline_full.py           # full fixture-sized run, all 3 formats + baselines
    ├── test_invariant_same_subgraph.py # THE core invariant
    ├── test_token_budget_enforcement.py
    ├── test_gold_label_extraction.py
    ├── test_json_output_contract.py    # strict JSON, no markdown fences, retry on malformed
    ├── test_metrics_correctness.py     # Acc@1/Acc@5/MRR@5/coverage on known fixture
    ├── test_reproducibility_artifacts.py
    ├── test_resume_and_no_overwrite.py
    ├── test_cli_analyze.py
    ├── test_cli_ablate.py
    └── test_mock_vs_real_labeling.py
```

Use `pytest` + `subprocess.run([...], capture_output=True)` for CLI-boundary tests, and direct Python-API calls for tests that need to inspect intermediate objects (e.g. the canonical retrieved subgraph) that the CLI doesn't expose directly.

---

## 4. Required Test Cases (map 1:1 to dev-prompt sections)

### 4.1 CLI surface (`inspect`, `validate`)
- `inspect` on the synthetic fixture exits 0 and reports: file list, formats, record counts, field names, missing-value counts, node/edge counts, embedding dim, valid-task count — assert exact numbers match the known fixture.
- `inspect` on a deliberately broken fixture (missing embeddings file) exits non-zero or reports the missing file by name, never crashes with a raw traceback.
- `validate` against `configs/test_e2e.yaml` passes; against a config with a nonexistent model path, fails with an informative error (not a silent fallback to another model — dev-prompt rule #5).

### 4.2 Core pipeline smoke (`run --limit 3`)
- Runs end-to-end on 3 fixture tasks in mock mode, produces `outputs/predictions/`, `outputs/metrics/`, `outputs/logs/` with non-empty, well-formed content.
- Every prediction record round-trips to valid JSON matching the `predicted_files`/`reasoning` schema.
- No gold file path or gold patch content appears anywhere in the recorded prompts (grep the saved raw prompts for gold file strings — dev-prompt rule #2).

### 4.3 Same-subgraph invariant (the most important test)
- For every task, assert the **retrieved node ID set** and **retrieved edge ID set** feeding Raw JSON, Adjacency List, and Natural Language are byte-for-byte identical (compare the persisted retrieval record, not the rendered text).
- Only exception: when a documented token-budget truncation applies — assert the truncation log entry exists and that the *included* subset is still identical across formats at that budget, and that truncation never splits a node/edge mid-object (parse each serialized output back and confirm it's complete, valid structure — no dangling JSON, no half adjacency entry, no orphaned sentence fragment).

### 4.4 Token budget enforcement
- Run the same task at 512/1024/2048/4096-token budgets (test fixture equivalents, e.g. 32/64/128/256 so fixtures are small/fast).
- Assert measured tokens use the actual Gemma tokenizer (or a pinned-vocab mock tokenizer for CI) — not a word/char heuristic.
- Assert included-node/edge counts are non-increasing as budget shrinks, and that "subgraph did not fit in budget" is explicitly logged when truncation occurs.
- Assert the fixed prompt + task description tokens are included in the total, not just the serialized graph.

### 4.5 Baselines
- `No Graph` condition: assert no node/edge text appears anywhere in that condition's saved prompt.
- `Keyword Match` baseline: assert the candidate file list given to the model matches what the lexical matcher would independently produce on the same task (cross-check against the retrieval module's own output).
- All conditions (3 serializations + 2 baselines) ran against the identical task set and identical retrieval config — assert task-ID sets are set-equal across every condition's output file.

### 4.6 Gold-label extraction
- Feed each fixture patch variant (`diff --git`, `---`/`+++`, `a/`/`b/`, `/dev/null`, rename) through the extractor; assert exact expected file-path sets, normalized (no `a/`/`b/` prefix, no trailing whitespace, forward slashes).
- Assert test-only paths are excluded by default per the configured protocol.
- Assert gold labels are never passed into `retrieval.py` or `prompting.py` call signatures (static check: grep the retrieval/prompting modules' call sites in the executed run for gold-label variable names, or structurally assert via a monkeypatched canary value that raises if touched before evaluation).

### 4.7 JSON output contract & parsing robustness
- Mock model emits valid JSON → predictions parsed, no retry triggered.
- Mock model emits JSON wrapped in ```` ```json ... ``` ```` fences → parser strips fences and still succeeds (while this still counts as a non-strict-output event and must be logged).
- Mock model emits truncated/invalid JSON → retry path triggers once (or configured max), and if still invalid, task is recorded as a parsing failure (not silently dropped, not crashing the run) and `parsing_failure_rate` in metrics reflects it.

### 4.8 Evaluation metrics correctness
- Build a fixture with known, hand-computed Accuracy@1/@5 and MRR@5 given fixed predictions and fixed gold labels; assert the pipeline's computed metrics match the hand-computed values exactly.
- Assert "candidate coverage" and "end-to-end accuracy" are reported as separate numbers, and that a task whose gold file was never retrieved shows coverage=miss but does not silently get excluded from the accuracy denominator (or if excluded, it's explicitly reported as such).

### 4.9 Reproducibility artifacts
- After a `run`, assert the output directory contains: config snapshot, dataset identifier, model identifier + quantization label (or `MOCK` marker), seed, retrieval params, serialization format, token budget, prompt version, raw model output, parsed predictions, gold labels, metrics, execution time, software/library versions.
- Re-run with the same config/seed → byte-identical predictions and metrics (determinism check) in mock mode.
- Assert every run gets a unique experiment ID and nothing is overwritten: running `run` twice with the same config must produce two distinct output sets, not a clobber.
- Kill a run mid-way (simulate via a monkeypatched exception after task N) and restart — assert it resumes rather than redoing completed tasks, and completed-task outputs are untouched.

### 4.10 `analyze` and `ablate`
- `analyze --results-dir outputs` on a completed fixture run produces mean/median/stdev, paired bootstrap CIs, and a significance test result per metric, with sample sizes reported; assert it refuses (or clearly flags) to run significance tests on fewer than some minimum N rather than fabricating confidence.
- `ablate` on depth {0,1,2} produces three distinct retrieval outputs with monotonically non-decreasing node counts as depth increases (on a fixture graph built to make this checkable), and ablation outputs are saved separately from primary-experiment outputs (dev-prompt rule #11).

### 4.11 Mock vs. real labeling
- Every artifact produced in mock mode (metrics CSVs, figures, paper-ready tables) carries an explicit `"mode": "mock"` / filename or header marker. Assert this programmatically — grep every output file type for the marker; fail the test if any output file type is missing it.

---

## 5. Non-Functional Requirements

- **Deterministic & hermetic**: no network calls, no real model download, no real dataset dependency for the default suite. Everything needed lives in `tests/fixtures/`.
- **Fast**: full mock E2E suite should run in well under 2 minutes locally; keep fixture sizes small (3–10 tasks, graphs under ~50 nodes).
- **CI-ready**: a single `pytest tests/e2e -m "not real_model"` command is the CI entrypoint; add a GitHub Actions (or equivalent) workflow if the repo has CI config.
- **Readable failures**: assertion messages should state what invariant broke and show the offending task ID / file diff, not just "assert False".
- **No flaky tests**: no reliance on wall-clock timing thresholds beyond generous upper bounds for the "not hung" check; no unseeded randomness anywhere in fixtures or mock model.

---

## 6. Execution Strategy

1. **Inspect** the actual `graphtrust/` codebase (module names, CLI entrypoints, config schema) once it exists — do not assume the dev-prompt's suggested file layout was followed exactly.
2. **Build fixtures first** (§2) — these are reusable across unit and E2E tests.
3. **Write `conftest.py`** with a CLI-runner helper (subprocess wrapper that captures stdout/stderr/exit code and returns the output dir) and a Python-API helper for tests that need internal object access.
4. **Implement test files in the order of §4** (CLI surface → smoke → invariant → budget → baselines → gold labels → JSON contract → metrics → reproducibility → analyze/ablate → mock labeling), running the suite after each file and fixing failures before moving on.
5. **Run the complete suite**, report real pass/fail counts, and fix every failure — do not report a suite as green without having executed it.
6. Add a `tests/e2e/README.md` explaining how to run the mock suite vs. the optional real-model suite, and exactly which env vars / file paths the real-model markers expect.

## 7. Deliverables

- Complete `tests/e2e/` suite + `tests/fixtures/` as described, all passing against the current `graphtrust/` implementation.
- A short `TEST_REPORT.md`: what was tested, what passed, what failed and was fixed, what's still a known gap (e.g. if real-model/real-dataset tests couldn't run in this environment — state that plainly, do not fabricate results for them), and the exact commands to reproduce the test run.
- CI config (if the repo doesn't have one) wiring `pytest tests/e2e -m "not real_model"` into the pipeline.

**Final objective: prove, with executed tests and real output, that the GraphTrust pipeline is correct, reproducible, and faithful to its own research-integrity rules — not just that its functions individually work.**
