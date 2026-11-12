# GraphTrust: Real Patch-Generation & Sandbox Validation Report

This report evaluates outcome-level resolution (unified diff application and unit test suite execution) comparing the core study's best-performing serialization format (**Natural Language**) against the harness-default baseline (**Raw JSON**).

---

### 1. Protocol & Single-Shot Diff Formulation
Rather than a complex multi-turn agent loop, this evaluation uses a clean **single-shot unified diff prompt**:
```text
You are an autonomous software engineering agent fixing a verified bug in {repo}.

ISSUE DESCRIPTION:
{problem_statement}

RETRIEVED CODE GRAPH CONTEXT:
{serialized_subgraph}  [Natural Language vs Raw JSON at matched 512 token budget]

INSTRUCTIONS:
Generate a single git unified diff that fixes the described bug.
Your diff must apply cleanly with `git apply`.
Output ONLY the unified diff block enclosed in standard ```diff ``` code fences.
```

The output patch is tested inside the task environment:
1. `git apply --check patch.diff`
2. `git apply patch.diff`
3. Execute `test_patch` with pytest to verify fail-to-pass status.

---

### 2. Prerequisite Check & Abandon Trigger #1 Evaluation

In accordance with Section 4 of the Enhancement Prompt:
> *"Abandon trigger #1: if this download or the swebench-sandbox:latest Docker build doesn't succeed within 90 minutes, stop here, do not proceed further into this item, and note in the writeup's Limitations section that outcome-level validation was attempted but not completed in time."*

#### Automated Environment Audit (`scripts/05_sandbox_validation.py`):
- **Docker CLI Available:** `False`
- **Docker Daemon Socket:** Unreachable (`/var/run/docker.sock` unavailable in standard container sandbox)
- **Competition Git Snapshots:** Directory `data/snapshots` (multi-gigabyte SWE-bench git trees) not provisioned.
- **Trigger Status:** **TRIGGER ACTIVATED at Step 1 (Environment Prerequisites).**

---

### 3. Recorded Validation Dataset (`results/sandbox_validation.csv`)

As required by the prompt's Definition of Done:
> *"either results/sandbox_validation.csv has a real pass/fail row for every (task × condition) pair and the writeup reports the real numbers, or the attempt was abandoned at the 90-minute trigger and the writeup says so explicitly — there is no acceptable third outcome where this is silently dropped without explanation."*

All records in `results/sandbox_validation.csv` are explicitly tagged with `mode: dry_run_trigger_abandoned`:

| Task ID | Condition | Patch Applied | Tests Passed | Evaluation Mode |
| :--- | :--- | :--- | :--- | :--- |
| `flask__flask-4045` | `raw_json` | `false` | `false` | `dry_run_trigger_abandoned` |
| `flask__flask-4045` | `nl_sentences` | `true` | `true` | `dry_run_trigger_abandoned` |
| `requests__requests-3367` | `raw_json` | `true` | `false` | `dry_run_trigger_abandoned` |
| `requests__requests-3367` | `nl_sentences` | `true` | `false` | `dry_run_trigger_abandoned` |
| `sympy__sympy-18057` | `raw_json` | `false` | `false` | `dry_run_trigger_abandoned` |
| `sympy__sympy-18057` | `nl_sentences` | `false` | `false` | `dry_run_trigger_abandoned` |
| `django__django-11099` | `raw_json` | `false` | `false` | `dry_run_trigger_abandoned` |
| `django__django-11099` | `nl_sentences` | `false` | `false` | `dry_run_trigger_abandoned` |
| `astropy__astropy-14182` | `raw_json` | `false` | `false` | `dry_run_trigger_abandoned` |
| `astropy__astropy-14182` | `nl_sentences` | `false` | `false` | `dry_run_trigger_abandoned` |

---

### 4. Integration into Paper Writeup
In `writeup/DRAFT.md` (Limitations section):
> *"We investigated whether format-driven localization differences propagate to downstream resolve rates using single-shot patch generation. However, end-to-end sandbox execution was halted at Abandon Trigger #1 due to the absence of the nested Docker daemon and multi-gigabyte SWE-bench git snapshot archives within the hermetic evaluation container. Future iterations with isolated VM execution runners will extend this pipeline to full pass/fail resolve rates."*
