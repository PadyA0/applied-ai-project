"""Tests for the reliability harness in src/reliability.py.

These are tests of the tester. A check that silently passes no matter what the
recommender does is worse than no check at all, so each test below confirms the
check actually reacts to the thing it claims to measure.
"""

import json

import pytest

from src.rag import load_index
from src.recommender import load_songs
from src.reliability import (
    CheckResult,
    check_catalog_coverage,
    check_determinism,
    check_genre_accuracy,
    check_golden_snapshot,
    check_grounding,
    check_perturbation_robustness,
    format_report,
    run_all,
    top_titles,
    write_golden,
)


@pytest.fixture(scope="module")
def songs():
    return load_songs("data/songs.csv")


@pytest.fixture(scope="module")
def index():
    return load_index("data/music_notes.md")


# --- Determinism ---

def test_determinism_passes_on_the_real_recommender(songs):
    assert check_determinism(songs).passed


def test_top_titles_is_repeatable(songs):
    prefs = {"genre": "jazz", "mood": "cool", "energy": 0.4}
    assert top_titles(prefs, songs) == top_titles(prefs, songs)


# --- Golden snapshot ---

def test_golden_snapshot_passes_against_a_freshly_written_baseline(songs, tmp_path):
    path = str(tmp_path / "golden.json")
    write_golden(songs, path)
    assert check_golden_snapshot(songs, path).passed


def test_golden_snapshot_detects_drift(songs, tmp_path):
    # Corrupt the baseline; the check must notice rather than shrug.
    path = tmp_path / "golden.json"
    write_golden(songs, str(path))
    tampered = json.loads(path.read_text())
    first_key = next(iter(tampered))
    tampered[first_key] = ["Something That Is Not There"]
    path.write_text(json.dumps(tampered))

    result = check_golden_snapshot(songs, str(path))
    assert not result.passed
    assert any("DRIFT" in d for d in result.details)


def test_golden_snapshot_fails_when_no_baseline_exists(songs, tmp_path):
    result = check_golden_snapshot(songs, str(tmp_path / "missing.json"))
    assert not result.passed


def test_write_golden_creates_readable_json(songs, tmp_path):
    path = tmp_path / "nested" / "golden.json"
    write_golden(songs, str(path))
    saved = json.loads(path.read_text())
    assert saved
    assert all(isinstance(titles, list) for titles in saved.values())


# --- Metrics ---

def test_genre_accuracy_is_perfect_while_genre_carries_the_top_weight(songs):
    result = check_genre_accuracy(songs)
    assert result.passed
    assert "100%" in result.summary


def test_catalog_coverage_reports_unreachable_songs(songs):
    result = check_catalog_coverage(songs)
    # Coverage is a measurement, not a bar to clear, so it always passes.
    assert result.passed
    assert "reachable" in result.summary


def test_perturbation_robustness_stays_within_the_churn_limit(songs):
    assert check_perturbation_robustness(songs).passed


def test_grounding_passes_on_the_real_corpus(songs, index):
    assert check_grounding(songs, index).passed


def test_grounding_fails_when_the_corpus_is_empty(songs):
    """With no notes, every song abstains, so nothing can be ungrounded."""
    from src.rag import build_index

    result = check_grounding(songs, build_index([]))
    assert result.passed
    assert any("abstained" in d for d in result.details)


# --- Reporting ---

def test_run_all_returns_every_check(songs, index):
    results = run_all(songs, index)
    assert len(results) == 6
    assert all(isinstance(r, CheckResult) for r in results)


def test_check_result_status_reflects_passed():
    assert CheckResult("x", True, "").status == "PASS"
    assert CheckResult("x", False, "").status == "FAIL"


def test_format_report_includes_every_check_name(songs, index):
    results = run_all(songs, index)
    report = format_report(results)
    for r in results:
        assert r.name in report


def test_format_report_counts_passing_checks():
    results = [CheckResult("a", True, "ok"), CheckResult("b", False, "bad")]
    assert "**1/2 checks passed.**" in format_report(results)
