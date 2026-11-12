"""Unit tests for qualitative case study selection (§1)."""

import csv
from pathlib import Path
import pytest
from src.g4study.case_study_selection import find_diverging_tasks, write_case_studies_document


@pytest.fixture
def fake_raw_results(repo_root):
    return repo_root / "tests" / "fixtures" / "fake_raw_results.csv"


def test_finds_tasks_where_format_changes_outcome(fake_raw_results):
    """Assert selection function finds exactly diverging tasks hand-picked in fixture."""
    # In fake_raw_results.csv, for raw_json vs nl_sentences:
    # task_01: raw_json=false, nl_sentences=true (FLIP)
    # task_02: raw_json=true, nl_sentences=true (both true)
    # task_03: raw_json=false, nl_sentences=false (both false)
    # task_04: raw_json=false, nl_sentences=false (both false)
    diverging = find_diverging_tasks(fake_raw_results, format_a="raw_json", format_b="nl_sentences")
    assert len(diverging) == 1
    assert diverging[0]["task_id"] == "task_01"
    assert diverging[0]["correct_a"] is False
    assert diverging[0]["correct_b"] is True


def test_returns_empty_list_without_crashing_when_no_flips_exist(tmp_path):
    """When all formats agree, returns empty list and outputs a clean note without crashing."""
    csv_file = tmp_path / "all_agree.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["task_id", "repo", "format", "budget", "seed", "candidate_coverage", "correct_at1", "correct_at3", "correct_at5", "token_count", "latency_ms", "mode"]
        )
        writer.writeheader()
        writer.writerow({
            "task_id": "t1", "repo": "r", "format": "raw_json", "budget": 512, "seed": 42,
            "candidate_coverage": 1.0, "correct_at1": "true", "correct_at3": "true", "correct_at5": "true",
            "token_count": 500, "latency_ms": 100, "mode": "mock"
        })
        writer.writerow({
            "task_id": "t1", "repo": "r", "format": "nl_sentences", "budget": 512, "seed": 42,
            "candidate_coverage": 1.0, "correct_at1": "true", "correct_at3": "true", "correct_at5": "true",
            "token_count": 300, "latency_ms": 80, "mode": "mock"
        })

    diverging = find_diverging_tasks(csv_file, format_a="raw_json", format_b="nl_sentences")
    assert diverging == []

    out_md = tmp_path / "case_studies.md"
    content = write_case_studies_document(diverging, out_md)
    assert out_md.exists()
    assert "no diverging examples found at this sample size" in content.lower()


def test_selected_examples_include_required_fields(fake_raw_results):
    """Each returned example carries all metadata needed by the writeup without re-derivation."""
    diverging = find_diverging_tasks(fake_raw_results, format_a="raw_json", format_b="adjacency_list")
    # task_01: json=false, adj=true
    # task_04: json=false, adj=true
    assert len(diverging) == 2
    for item in diverging:
        assert "task_id" in item
        assert "repo" in item
        assert "format_a" in item
        assert "format_b" in item
        assert "correct_a" in item
        assert "correct_b" in item
        assert "serialized_excerpt_a" in item
        assert "serialized_excerpt_b" in item
        assert "diagnosis" in item
