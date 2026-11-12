"""Unit tests for cross-model architecture comparison and ranking agreement (§3)."""

import csv
from pathlib import Path
import pytest
from src.g4study.cross_model import (
    load_cross_model_results,
    compare_model_rankings,
)


@pytest.fixture
def agree_csv(repo_root):
    return repo_root / "tests" / "fixtures" / "fake_cross_model_agree.csv"


@pytest.fixture
def flip_csv(repo_root):
    return repo_root / "tests" / "fixtures" / "fake_cross_model_flip.csv"


def test_output_schema_matches_raw_results_plus_model_column(agree_csv):
    """Assert cross_model_comparison has all core raw_results columns plus model column."""
    core_columns = {
        "task_id", "repo", "format", "budget", "seed",
        "candidate_coverage", "correct_at1", "correct_at3", "correct_at5",
        "token_count", "latency_ms", "mode"
    }
    
    with open(agree_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
    
    header_set = set(header)
    # Check that all core columns are present
    assert core_columns.issubset(header_set)
    # Check that 'model' column is present
    assert "model" in header_set
    # Total columns is exactly core + 1 ('model')
    assert len(header_set) == len(core_columns) + 1


def test_ranking_agreement_detected_correctly(agree_csv):
    """Using the 'agree' fixture variant, compare_model_rankings reports agreement."""
    res = compare_model_rankings(agree_csv, model_a="Model_A", model_b="Model_B", budget=512)
    assert res["agrees"] is True
    assert res["ranking_a"] == res["ranking_b"]
    # In fake_cross_model_agree.csv, nl_sentences is 100% and raw_json is 0% for both
    assert res["ranking_a"] == ["nl_sentences", "raw_json"]


def test_ranking_disagreement_detected_correctly(flip_csv):
    """Using the 'flip' fixture variant, compare_model_rankings reports strict disagreement."""
    res = compare_model_rankings(flip_csv, model_a="Model_A", model_b="Model_B", budget=512)
    assert res["agrees"] is False
    assert res["ranking_a"] != res["ranking_b"]
    assert res["ranking_a"] == ["nl_sentences", "raw_json"]
    assert res["ranking_b"] == ["raw_json", "nl_sentences"]
