"""Case study selection and document generation logic for GraphTrust (§1)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Any


def find_diverging_tasks(
    raw_results_path: str | Path,
    format_a: str = "raw_json",
    format_b: str = "nl_sentences",
    budget: int | None = 512,
) -> list[dict[str, Any]]:
    """Scan raw_results.csv and find task transcripts where format changes the outcome.
    
    Returns a list of dicts carrying task_id, repo, both formats, both correctness values,
    and serialized excerpts.
    """
    raw_results_path = Path(raw_results_path)
    if not raw_results_path.exists():
        raise FileNotFoundError(f"Results file not found: {raw_results_path}")

    # Group by (task_id, budget, seed) -> format -> row
    groups: dict[tuple[str, int, int], dict[str, dict[str, Any]]] = {}
    with open(raw_results_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bgt = int(row["budget"])
            if budget is not None and bgt != budget:
                continue
            key = (row["task_id"], bgt, int(row["seed"]))
            if key not in groups:
                groups[key] = {}
            groups[key][row["format"]] = row

    diverging = []
    for (task_id, bgt, seed), fmt_dict in groups.items():
        if format_a in fmt_dict and format_b in fmt_dict:
            row_a = fmt_dict[format_a]
            row_b = fmt_dict[format_b]
            corr_a = row_a["correct_at1"].strip().lower() == "true"
            corr_b = row_b["correct_at1"].strip().lower() == "true"

            if corr_a != corr_b:
                repo = row_a.get("repo", "unknown/repo")
                diverging.append({
                    "task_id": task_id,
                    "repo": repo,
                    "budget": bgt,
                    "seed": seed,
                    "format_a": format_a,
                    "format_b": format_b,
                    "correct_a": corr_a,
                    "correct_b": corr_b,
                    "serialized_excerpt_a": f"[{format_a} excerpt for {task_id}]",
                    "serialized_excerpt_b": f"[{format_b} excerpt for {task_id}]",
                    "diagnosis": f"Outcome diverged between {format_a} ({corr_a}) and {format_b} ({corr_b}) under {bgt} tokens.",
                })

    return diverging


def write_case_studies_document(
    examples: list[dict[str, Any]],
    output_path: str | Path,
) -> str:
    """Format selected case studies into Markdown.
    
    If examples is empty, cleanly outputs a defined notice rather than crashing or creating
    an empty/malformed file.
    """
    lines = ["# GraphTrust: Qualitative Case Studies", ""]
    if not examples:
        lines.append("No diverging examples found at this sample size.")
        content = "\n".join(lines)
        Path(output_path).write_text(content, encoding="utf-8")
        return content

    for i, ex in enumerate(examples, 1):
        lines.append(f"### Case Study {i}: {ex['task_id']}")
        lines.append(f"- **Repository:** `{ex['repo']}`")
        lines.append(f"- **Budget:** {ex['budget']} tokens | **Seed:** {ex['seed']}")
        lines.append(f"- **{ex['format_a']}:** `correct_at1={ex['correct_a']}`")
        lines.append(f"- **{ex['format_b']}:** `correct_at1={ex['correct_b']}`")
        lines.append(f"- **Diagnosis:** {ex['diagnosis']}")
        lines.append("")

    content = "\n".join(lines)
    Path(output_path).write_text(content, encoding="utf-8")
    return content
