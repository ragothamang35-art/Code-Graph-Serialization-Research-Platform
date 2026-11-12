# Enhancement Test Prompt — "Same Subgraph, Different Story"

> Paste this into a coding agent **alongside or immediately after** `ENHANCEMENT_PROMPT.md`'s four items are implemented. It is self-contained, but assumes `TEST_PROMPT.md`'s suite, fixtures, and pytest conventions already exist in the repo — this document only adds coverage for the four new modules `ENHANCEMENT_PROMPT.md` introduces, which the original suite never touches: case-study selection, significance testing, cross-model comparison, and sandbox patch validation.

## 0. Scope

Four new things got built; none of them existed when `TEST_PROMPT.md` was written, so none of them are covered yet:
1. The selection logic that picks interesting task transcripts for `results/case_studies.md`.
2. `src/g4study/significance.py` — `mcnemar_test()` and `bootstrap_ci()`.
3. The cross-model comparison pipeline producing `results/cross_model_comparison.csv`.
4. `scripts/05_sandbox_validation.py` — diff application + test execution inside the SWE-bench-style sandbox.

Same non-negotiables as `TEST_PROMPT.md`: the fast suite (`pytest -m "not smoke and not docker"`) runs with **zero network, zero real model, zero real competition data, zero Docker** — every fixture below is synthetic. Anything needing a real Docker sandbox gets its own `@pytest.mark.docker` marker (separate from `@pytest.mark.smoke`, since a builder might have the LLM server running but not Docker, or vice versa — don't force both dependencies onto one marker).

## 1. New fixtures (`tests/fixtures/`)

- `fake_raw_results.csv` — a small, fully synthetic results table shaped exactly like the real `raw_results.csv` schema from `BUILD_PROMPT.md` §4 (8–10 rows covering 2 repos, all 3 formats, both budgets, 2 seeds), with the correctness columns hand-chosen so you know in advance: which (task, format) pairs flip outcome (for case-study selection tests), and a known discordant-pair count between two specific formats (for the McNemar test).
- `fake_cross_model_results.csv` — same shape plus a `model` column, two models, deliberately constructed so one test fixture has the ranking **agree** between models and a second fixture variant has it **flip** — both cases must be exercised.
- A tiny **synthetic local git repository**, built fresh inside a `tmp_path` fixture at test time (never a static file in the repo, and never real competition snapshot content): initialize with `git init`, one fake source file with an obvious off-by-one bug, one fake test file that fails against the buggy version, a known-good unified diff that fixes it, and a known-bad diff that doesn't apply cleanly. This is what the sandbox-validation unit tests run against — real git, fake and tiny content.

## 2. Unit tests

**`tests/test_case_studies.py`**
- `test_finds_tasks_where_format_changes_outcome` — against `fake_raw_results.csv`, assert the selection function returns exactly the (task, format_pair) combinations you hand-picked when building the fixture, and no others.
- `test_returns_empty_list_without_crashing_when_no_flips_exist` — construct a fixture variant where every format agrees on every task; assert the function returns an empty list cleanly rather than raising, and that the caller path that writes `case_studies.md` handles an empty list by writing a clear "no diverging examples found at this sample size" note instead of an empty or malformed file.
- `test_selected_examples_include_required_fields` — each returned example carries task_id, repo, both formats' serialized excerpts, and the two correctness values — whatever the write-up step consumes next must not have to re-derive any of this.

**`tests/test_significance.py`** (the most important file in this document)
- `test_mcnemar_matches_hand_computed_example` — build a tiny paired boolean example (e.g. 10 tasks) where you compute the discordant pairs and expected statistic by hand in the test's docstring, assert the function matches.
- `test_mcnemar_with_zero_discordant_pairs_does_not_divide_by_zero` — **critical edge case**: if `correct_a == correct_b` for every task (no disagreements), the classic McNemar statistic divides by the discordant-pair count, which is zero. Assert this returns a defined, documented value (e.g. `p_value=1.0`, statistic `0` or `NaN` with a note) instead of raising `ZeroDivisionError` or returning `NaN` silently without that being the documented contract.
- `test_mcnemar_rejects_mismatched_lengths` — `correct_a` and `correct_b` of different lengths raises a clear `ValueError`, not a silent misalignment.
- `test_bootstrap_ci_is_reproducible_with_a_fixed_seed` — same inputs + same seed → identical CI bounds across two calls.
- `test_bootstrap_ci_contains_the_point_estimate` — the observed accuracy delta should fall inside (or very near, given resampling noise) its own bootstrap CI on a reasonably-sized fixture.
- `test_bootstrap_ci_on_identical_arrays_centers_near_zero` — if `correct_a == correct_b`, the CI for the difference should straddle zero.
- `test_bootstrap_ci_lower_bound_never_exceeds_upper_bound`.

**`tests/test_cross_model_comparison.py`**
- `test_output_schema_matches_raw_results_plus_model_column` — load `fake_cross_model_results.csv`-shaped data through whatever loader the analysis step uses, assert every column from the core `raw_results.csv` schema is present plus exactly one new `model` column.
- `test_ranking_agreement_detected_correctly` — using the "agree" fixture variant, the ranking-comparison function reports agreement.
- `test_ranking_disagreement_detected_correctly` — using the "flip" fixture variant, it reports disagreement, not a false "agrees" — this is the one most likely to be gotten wrong by an implementation that just checks "best of model B is in top-2 of model A" instead of a strict match, so test it precisely against the fixture you built to flip.

**`tests/test_sandbox_validation.py`** (uses the synthetic git repo fixture; no Docker required for this file)
- `test_known_good_patch_applies_cleanly` — against the fixture repo, applying the known-good diff succeeds.
- `test_known_bad_patch_fails_to_apply_and_is_recorded_not_raised` — the malformed diff produces `patch_applied=False` in the result row, not an unhandled exception.
- `test_tests_passed_is_false_when_patch_does_not_apply` — if `patch_applied=False`, `tests_passed` must be `False`/`null`, never left as a stale `True` from a previous row or silently omitted.
- `test_result_row_schema_matches_spec` — exactly `task_id, condition, patch_applied, tests_passed` columns, for both the good and bad patch cases.
- `test_docker_availability_check_returns_false_when_docker_missing` — mock `shutil.which("docker")` (or however the implementation checks) to simulate Docker being absent; assert the script's pre-flight check reports this clearly and exits before attempting any real sandbox work, rather than failing deep inside a subprocess call with a confusing error.

## 3. Docker-dependent smoke test (new marker, excluded by default)

**`tests/test_sandbox_smoke.py`**, marked `@pytest.mark.docker`:
- `test_real_sandbox_resolves_the_known_good_case` — skips automatically if Docker isn't available or the `swebench-sandbox:latest` image hasn't been built; when it does run, builds/uses the real sandbox on exactly one task from the real qualifying subset (not all 15–20 — one, for a fast manual check) and asserts the pipeline completes and records a real pass/fail, mirroring how `TEST_PROMPT.md`'s model smoke test validates plumbing rather than correctness.

Run manually with `pytest -m docker -v` once Docker and the sandbox image are ready, before trusting the full 15–20 task run in `ENHANCEMENT_PROMPT.md` §4.

## 4. Integration / non-interference test

**`tests/test_enhancements_do_not_break_core.py`**
- `test_analyze_py_still_runs_with_enhancement_files_present` — drop fixture copies of `cross_model_comparison.csv`, `significance_tests.md`, and `case_studies.md` into a scratch results directory alongside a fixture `raw_results.csv`, then run the core `04_analyze.py` logic from `TEST_PROMPT.md`'s integration tests against that directory — assert it still produces its original outputs unchanged. The enhancement files must be purely additive; if any of them silently alters what the core analysis computes, that's a regression this test exists to catch.

## 5. Tooling & conventions

- Register a second marker, `docker`, alongside the existing `smoke` marker from `TEST_PROMPT.md`; default `addopts` excludes both: `-m "not smoke and not docker"`.
- Fast suite (including all of §2 and §4 above) stays under the same ~30-second budget as the original suite — none of this needs real git-repo-scale operations, the fixture repo is a handful of files.
- `pytest -m docker` is expected to take longer (real container build/run) — that's fine, it's explicitly opt-in and manual.

## 6. Definition of done

- `pytest` (fast suite, both old and new tests) green, zero failures, zero unexplained skips.
- `pytest -m docker` run manually at least once with a real Docker sandbox before trusting `ENHANCEMENT_PROMPT.md` §4's real run, and it passed on the one-task check.
- The zero-discordant-pairs McNemar edge case and the ranking-disagreement cross-model case are both explicitly covered — these are the two subtlest correctness traps in this batch and the ones most likely to silently misreport a result in the actual writeup if untested.
- The non-interference test (§4) passes, confirming enhancement outputs never mutate what the core submission's own numbers say.

## 7. When you are done

Report back: new test count by file, confirmation the zero-discordant-pairs and ranking-disagreement cases are both passing (not just present), whether the Docker smoke test was run and its result, and whether building these tests surfaced any discrepancy between what `ENHANCEMENT_PROMPT.md` specified and what got implemented — exactly the kind of gap this suite exists to catch before it shows up as a wrong number in the submitted writeup.
