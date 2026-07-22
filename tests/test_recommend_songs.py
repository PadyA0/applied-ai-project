"""Tests for recommend_songs -- ranks the catalog and returns the top k.

recommend_songs scores every song, sorts by score descending, and slices the
top k, attaching a human-readable explanation (or "no strong match").
"""

from src.recommender import recommend_songs


def make_catalog():
    return [
        {"title": "Perfect Pop", "genre": "pop", "mood": "happy", "energy": 0.8},
        {"title": "Wrong Rock", "genre": "rock", "mood": "intense", "energy": 0.1},
        {"title": "Half Match", "genre": "pop", "mood": "sad", "energy": 0.8},
    ]


def test_returns_at_most_k_results():
    prefs = {"genre": "pop"}
    results = recommend_songs(prefs, make_catalog(), k=2)
    assert len(results) == 2


def test_k_larger_than_catalog_returns_whole_catalog():
    catalog = make_catalog()
    results = recommend_songs({"genre": "pop"}, catalog, k=99)
    assert len(results) == len(catalog)


def test_results_sorted_by_score_descending():
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    results = recommend_songs(prefs, make_catalog(), k=3)
    scores = [score for _, score, _ in results]
    assert scores == sorted(scores, reverse=True)
    # The song matching every preference must rank first.
    assert results[0][0]["title"] == "Perfect Pop"


def test_result_tuple_shape():
    results = recommend_songs({"genre": "pop"}, make_catalog(), k=1)
    song, score, explanation = results[0]
    assert isinstance(song, dict)
    assert isinstance(score, float)
    assert isinstance(explanation, str)


def test_no_matching_preference_yields_no_strong_match_text():
    # A preference no song can satisfy -> every explanation is the fallback.
    prefs = {"genre": "jazz"}
    results = recommend_songs(prefs, make_catalog(), k=3)
    assert all(score == 0.0 for _, score, _ in results)
    assert all(explanation == "no strong match" for _, _, explanation in results)


def test_matched_song_has_explanation_text():
    prefs = {"genre": "pop"}
    results = recommend_songs(prefs, make_catalog(), k=1)
    _, score, explanation = results[0]
    assert score > 0
    assert "genre match" in explanation
