"""Tests for score_song -- the core scoring strategy in recommender.py.

score_song loops over four weight tables (categorical, reward-only unit,
penalizing unit, custom-range) and applies a scoring rule per feature. Each
test below targets one of those conditional branches.
"""

from src.recommender import (
    score_song,
    CATEGORICAL_WEIGHTS,
    UNIT_WEIGHTS,
    PENALIZED_UNIT_WEIGHTS,
    RANGED_WEIGHTS,
)


# --- Categorical features (genre, mood): exact case-insensitive match ---

def test_categorical_exact_match_adds_full_weight():
    song = {"genre": "pop", "mood": "happy"}
    prefs = {"genre": "pop", "mood": "happy"}
    score, reasons = score_song(prefs, song)
    assert score == CATEGORICAL_WEIGHTS["genre"] + CATEGORICAL_WEIGHTS["mood"]
    assert any("genre match" in r for r in reasons)
    assert any("mood match" in r for r in reasons)


def test_categorical_match_is_case_insensitive():
    song = {"genre": "POP"}
    prefs = {"genre": "pop"}
    score, reasons = score_song(prefs, song)
    assert score == CATEGORICAL_WEIGHTS["genre"]


def test_categorical_mismatch_adds_nothing():
    song = {"genre": "rock", "mood": "intense"}
    prefs = {"genre": "pop", "mood": "happy"}
    score, reasons = score_song(prefs, song)
    assert score == 0.0
    assert reasons == []


def test_categorical_missing_preference_is_skipped():
    song = {"genre": "pop"}
    prefs = {}  # no genre preference expressed
    score, reasons = score_song(prefs, song)
    assert score == 0.0


# --- Reward-only unit features: closeness clamped at 0, never negative ---

def test_unit_feature_perfect_match_adds_full_weight():
    song = {"energy": 0.8}
    prefs = {"energy": 0.8}
    score, reasons = score_song(prefs, song)
    assert score == UNIT_WEIGHTS["energy"]
    assert any("energy fit" in r for r in reasons)


def test_unit_feature_total_mismatch_adds_zero_not_negative():
    # |1.0 - 0.0| = 1.0 -> closeness clamped to 0 -> no points, no reason line.
    song = {"energy": 0.0}
    prefs = {"energy": 1.0}
    score, reasons = score_song(prefs, song)
    assert score == 0.0
    assert reasons == []


def test_unit_feature_partial_match_is_proportional():
    # closeness = 1 - 0.5 = 0.5 -> points = weight * 0.5
    song = {"energy": 0.5}
    prefs = {"energy": 1.0}
    score, _ = score_song(prefs, song)
    assert score == UNIT_WEIGHTS["energy"] * 0.5


# --- Penalizing unit features (acousticness): a bad match subtracts points ---
# This is the SF8 stretch feature; these tests lock in the penalty behavior.

def test_penalized_feature_perfect_match_is_positive():
    song = {"acousticness": 0.2}
    prefs = {"acousticness": 0.2}
    score, reasons = score_song(prefs, song)
    assert score == PENALIZED_UNIT_WEIGHTS["acousticness"]
    assert any("acousticness fit" in r for r in reasons)


def test_penalized_feature_opposite_match_subtracts_points():
    # closeness = 1 - 2*|1.0 - 0.0| = -1 -> points = -weight (a real penalty).
    song = {"acousticness": 1.0}
    prefs = {"acousticness": 0.0}
    score, reasons = score_song(prefs, song)
    assert score == -PENALIZED_UNIT_WEIGHTS["acousticness"]
    assert score < 0
    assert any("acousticness mismatch" in r for r in reasons)


def test_penalized_feature_halfway_is_neutral():
    # closeness = 1 - 2*0.5 = 0 -> points == 0 -> skipped, no reason line.
    song = {"acousticness": 0.5}
    prefs = {"acousticness": 0.0}
    score, reasons = score_song(prefs, song)
    assert score == 0.0
    assert reasons == []


def test_penalty_can_pull_total_score_below_a_categorical_gain():
    # A genre match (+2.0) minus a worst-case acousticness penalty (-0.5) = 1.5.
    song = {"genre": "pop", "acousticness": 1.0}
    prefs = {"genre": "pop", "acousticness": 0.0}
    score, _ = score_song(prefs, song)
    assert score == CATEGORICAL_WEIGHTS["genre"] - PENALIZED_UNIT_WEIGHTS["acousticness"]


# --- Custom-range features (tempo_bpm, popularity, release_decade) ---

def test_ranged_feature_perfect_match_adds_full_weight():
    _, _, weight = RANGED_WEIGHTS["tempo_bpm"]
    song = {"tempo_bpm": 120}
    prefs = {"tempo_bpm": 120}
    score, reasons = score_song(prefs, song)
    assert score == weight
    assert any("tempo_bpm fit" in r for r in reasons)


def test_ranged_feature_normalizes_gap_by_span():
    low, high, weight = RANGED_WEIGHTS["tempo_bpm"]
    span = high - low
    # A gap of `span` would drive closeness to exactly 0; half that -> 0.5.
    song = {"tempo_bpm": low + span / 2}
    prefs = {"tempo_bpm": low}
    score, _ = score_song(prefs, song)
    assert score == weight * 0.5


def test_ranged_feature_beyond_range_clamps_to_zero():
    low, high, _ = RANGED_WEIGHTS["tempo_bpm"]
    song = {"tempo_bpm": high + 1000}  # far outside the range
    prefs = {"tempo_bpm": low}
    score, reasons = score_song(prefs, song)
    assert score == 0.0
    assert reasons == []


def test_missing_feature_in_song_is_skipped():
    # Preference expressed, but the song lacks the column -> no contribution.
    song = {"genre": "pop"}
    prefs = {"genre": "pop", "energy": 0.9, "tempo_bpm": 120}
    score, _ = score_song(prefs, song)
    assert score == CATEGORICAL_WEIGHTS["genre"]
