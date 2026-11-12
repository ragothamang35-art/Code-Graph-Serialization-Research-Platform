# Enhancement Prompt — "Same Subgraph, Different Story"

> Paste this into a coding agent (Claude Code, Codex, OpenCode, or equivalent) **after** `BUILD_PROMPT.md`'s core pipeline is built and its Phase 3 grid has produced a complete `results/raw_results.csv`. This document is additive, not a replacement — it assumes the repo, module signatures, and result schema from `BUILD_PROMPT.md` already exist. Do not start any item here before the core deliverable (§6 Phases 0–5 of `BUILD_PROMPT.md`) is in a submittable state. The core submission must survive even if every item below is abandoned.

## 0. Why these four and not others

The core study (fixed retrieval, 3 serialization formats, 1 primary model, file-level accuracy) is deliberately narrow — that narrowness is what made it finishable and what gave the writeup one clean, quotable claim. Everything below makes that *same* claim more convincing with more evidence; none of it changes the claim, adds a second research question, or re-opens factors the design deliberately closed. If you find yourself tempted to add a 4th serialization format, compare more retrieval strategies, or scope a full leaderboard submission — stop. Those were considered and explicitly rejected (see `PROJECT.md` §12) because they re-create the "muddy grid search" and "trying to be three papers" problems the idea already survived a hard adversarial review to escape.

**Hard rule for all four items below: each gets its own time box. If an item blows its time box, abandon it, note what was attempted and why it was cut in `writeup/DRAFT.md`'s Limitations section, and move to the next item or to final polish. A half-finished enhancement that threatens the deadline is strictly worse than a clean submission without it.**

Do these in the order listed — cheapest and safest first, so you always have *something* banked before attempting the expensive one.

---

## 1. Qualitative case studies (time box: 1 hour)

**What:** Hand-read 3–5 task transcripts from `results/raw_results.csv` where the serialization format changed the outcome (one format got `correct_at1=true`, another got `false`, same task, same budget, same seed-ish). Pick a mix: at least one where the better format clearly won because of *content* it could include that the worse one truncated, and at least one where the win is about *structure* (the model found the relevant edge faster in a more explicit format) rather than content.

**Produce:** `results/case_studies.md` — for each example: task id and repo, a one-line plain-English summary of the bug, the two relevant serialized excerpts side by side (trimmed to the relevant few lines, not the full context dump), and a 2–3 sentence diagnosis of *why* the outcome differed.

**Writeup integration:** fold 2–3 of these into the Results section as short callouts (~100–150 words combined, not per example) — a judge remembers one good concrete example far better than a 16-row table. Do not let this section grow past ~150 words total; trim the weakest example rather than including all 5 at length.

**DoD:** `results/case_studies.md` exists with at least 3 examples; the writeup's Results section references at least 2 of them by task id.

---

## 2. Statistical significance (time box: 1.5 hours)

**What:** For each pair of formats (raw_json vs adjacency_list, raw_json vs nl_sentences, adjacency_list vs nl_sentences), run a paired significance test on per-task correctness at the matched budget: McNemar's test (standard for paired binary classifier comparison — exactly what the toughest known prior work on this dataset, "Mind the Map," already used, so this also matches the rigor bar a judge familiar with that work will expect). Additionally compute a bootstrap 95% CI on the accuracy difference (resample tasks with replacement, ~2,000 resamples, report the interval) as a second, complementary check.

**Produce:** `src/g4study/significance.py` with `mcnemar_test(correct_a: list[bool], correct_b: list[bool]) -> dict` (statistic, p-value) and `bootstrap_ci(correct_a, correct_b, n_resamples=2000) -> tuple[float, float]`. Write results to `results/significance_tests.md` as a small table: pair, accuracy delta, McNemar p-value, bootstrap 95% CI.

**Writeup integration:** one sentence in Results stating whether the headline difference is statistically significant at the sample size used, and the honest caveat if it isn't (an honest "the direction is consistent but not significant at n=40" is a *better* look to this judge panel than an uncaveated claim — Perozzi and Galkin's own position paper is explicitly about sloppy benchmarking practices in graph ML).

**DoD:** `results/significance_tests.md` has a row for every format pair at every budget tested; the writeup's Results section states significance plainly, including if the answer is "not significant."

---

## 3. Cross-model generalization check (time box: 2–3 hours, includes a model download)

**What:** Pick one additional small open model of a similar size class to Gemma-4 E2B, from a different model family (e.g., a ~2–4B parameter instruction-tuned open model with an available GGUF — pick whatever is easiest to source in GGUF form at the time of building, the specific choice doesn't matter as much as it being a genuinely different training lineage from Gemma). Run only the single best-performing and single worst-performing format from the E2B grid (not all three, not the full budget sweep) on the same ~40-task subset, same seeds, same budgets.

**Produce:** `results/cross_model_comparison.csv`, same schema as the main `raw_results.csv` with an extra `model` column populated.

**Writeup integration:** one short paragraph (~100 words) in Results or Discussion: does the best/worst ranking hold on the second model? If yes, this is a genuine strengthening of the Quality ("does it generalize") rubric line — say so plainly. If the ranking flips, that is *also* a legitimate and interesting finding (format sensitivity may be architecture-dependent) — report it honestly rather than omitting an inconvenient result.

**DoD:** `results/cross_model_comparison.csv` has rows for both formats × both budgets × all seeds on the second model; the writeup states the generalization result explicitly either way.

---

## 4. Real patch-generation + sandbox validation (time box: 4 hours total, hard abandon trigger at 90 minutes if the sandbox isn't running)

**This is the highest-value and highest-risk item. Attempt it last, only if items 1–3 are done and at least one full day remains before the deadline.**

**What it answers:** the single sharpest critique the idea received was that "file touched by the gold patch" is a well-known weak proxy for whether better localization actually produces more fixed bugs. This item closes that gap with real evidence on a small subsample, without taking on a full leaderboard submission.

**New data dependency — not pulled in `BUILD_PROMPT.md` Phase 1:** this needs the `snapshots/`, `wheels/`, and `docker/` directories from the competition dataset (skipped earlier deliberately, since the core study never executes code). Pull them now: extend `scripts/00_fetch_data.sh` or run the additional `kaggle competitions download` calls for those paths. **Abandon trigger #1:** if this download or the `swebench-sandbox:latest` Docker build doesn't succeed within 90 minutes, stop here, do not proceed further into this item, and note in the writeup's Limitations section that outcome-level validation was attempted but not completed in time.

**Scope, precisely:** this is a small internal comparison in support of the paper's claim, **not** a full ADK agent submission and **not** an attempt at the main leaderboard. Do not build a multi-turn agent loop for this.

1. Pick 15–20 tasks from the qualifying subset, preferring ones where `gold_in_candidate=true` in the core results (so this tests "does good context produce a good patch," not "can we find the file at all" again).
2. For each task, for exactly two conditions — the core study's single best-performing format, and `raw_json` as the harness-default baseline — build a **single-shot** prompt: same context block as the localization experiment, but ask the model to emit a unified diff directly instead of a file list.
3. Apply the returned diff with `git apply` inside a container built from `docker/Dockerfile.sandbox`, against that task's `base_commit` snapshot.
4. Apply `test_patch` and run the test suite; record pass/fail exactly as the official harness would (fail-to-pass check).
5. Compare resolve rate: best-format-driven patches vs. raw-JSON-driven patches, on the same 15–20 tasks.

**Produce:** `scripts/05_sandbox_validation.py`, `results/sandbox_validation.csv` (columns: `task_id, condition, patch_applied, tests_passed`), a short `results/sandbox_validation.md` summary.

**Writeup integration:** if it completes, this becomes one of the strongest sentences in the paper — a short paragraph in Results stating the resolve-rate comparison plainly, with the sample size caveat (15–20 tasks is small; say so). If it doesn't complete in time, do not fabricate or estimate a result — state in Limitations that this validation was scoped but not completed, and why, which is itself an honest, creditable thing to say to a judge panel that explicitly rewards Verifiability.

**DoD:** either `results/sandbox_validation.csv` has a real pass/fail row for every (task × condition) pair and the writeup reports the real numbers, or the attempt was abandoned at the 90-minute trigger and the writeup says so explicitly — there is no acceptable third outcome where this is silently dropped without explanation.

---

## 5. Writeup word-budget adjustment

Adding real content from items above will press against the 3,000-word cap. Do not let that cap slip — trim before you exceed it:
- Shrink Related Work by ~100–150 words (tighten citations to one clause each) to make room.
- Case studies (§1) stay under 150 words total, no exceptions.
- Significance reporting (§2) is one sentence per claim, not a new subsection.
- Cross-model (§3) is one short paragraph, not a new Methods subsection — fold it into the existing Results flow.
- Sandbox validation (§4), if completed, earns its own short paragraph since it's the strongest evidence in the paper; if it didn't complete, it's one sentence in Limitations, not a paragraph explaining the Docker setup.

## 6. When you are done

Report back, for each of the four items: attempted or skipped, time actually spent vs. the time box, and if attempted, the one-sentence result. If item 4 was abandoned at the trigger, say exactly what step it failed at (download, Docker build, `git apply`, or test execution) so it's clear whether it's worth a second attempt with more runway next time. Confirm the final writeup word count after integrating whatever was completed.
