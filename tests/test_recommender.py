"""Tests for the object oriented wrapper: Song, UserProfile and Recommender.

This is the second of the two entry paths into the scoring core. `main.py` uses
the plain dictionary functions; this class based path translates a UserProfile
into the same preferences dictionary and calls the same `score_song`. These
tests cover the translation and the sorting, not the scoring rules themselves,
which are covered in test_score_song.py.
"""

from dataclasses import asdict

import pytest

from src.recommender import Recommender, Song, UserProfile, score_song


def make_song(**overrides) -> Song:
    """A Song with sensible defaults, so each test only states what it cares about."""
    fields = {
        "id": 1,
        "title": "Test Track",
        "artist": "Test Artist",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "tempo_bpm": 120,
        "valence": 0.9,
        "danceability": 0.8,
        "acousticness": 0.2,
    }
    fields.update(overrides)
    return Song(**fields)


def pop_happy_user(likes_acoustic: bool = False) -> UserProfile:
    return UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=likes_acoustic,
    )


def score_of(user: UserProfile, song: Song) -> float:
    """Score one song for one user through the OOP translation layer."""
    return score_song(Recommender._prefs_from_user(user), asdict(song))[0]


@pytest.fixture
def mixed_catalog() -> Recommender:
    """Catalog whose best match is placed last, so a real sort is required."""
    return Recommender([
        make_song(id=1, title="Wrong Rock", genre="rock", mood="intense",
                  energy=0.1, tempo_bpm=150, valence=0.4, danceability=0.5,
                  acousticness=0.9),
        make_song(id=2, title="Perfect Pop"),
    ])


# --- Translating a UserProfile into preferences ---

def test_prefs_from_user_maps_every_field():
    prefs = Recommender._prefs_from_user(pop_happy_user())
    assert prefs["genre"] == "pop"
    assert prefs["mood"] == "happy"
    assert prefs["energy"] == 0.8


def test_likes_acoustic_true_maps_to_the_top_of_the_scale():
    assert Recommender._prefs_from_user(pop_happy_user(True))["acousticness"] == 1.0


def test_likes_acoustic_false_maps_to_the_bottom_of_the_scale():
    assert Recommender._prefs_from_user(pop_happy_user(False))["acousticness"] == 0.0


def test_likes_acoustic_flips_the_penalty_direction():
    # The same acoustic song must score better for someone who wants acoustic.
    acoustic_song = make_song(genre="folk", mood="calm", acousticness=1.0)
    assert score_of(pop_happy_user(True), acoustic_song) > score_of(
        pop_happy_user(False), acoustic_song
    )


# --- Ranking ---

def test_recommend_sorts_best_match_first_despite_input_order(mixed_catalog):
    results = mixed_catalog.recommend(pop_happy_user(), k=2)
    assert [s.title for s in results] == ["Perfect Pop", "Wrong Rock"]


def test_recommend_returns_song_objects_not_dicts(mixed_catalog):
    # The OOP path returns Songs; the functional path returns tuples of dicts.
    assert all(isinstance(s, Song) for s in mixed_catalog.recommend(pop_happy_user()))


def test_recommend_results_are_in_non_increasing_score_order(mixed_catalog):
    user = pop_happy_user()
    results = mixed_catalog.recommend(user, k=len(mixed_catalog.songs))
    scores = [score_of(user, song) for song in results]
    assert scores == sorted(scores, reverse=True)


def test_recommend_respects_k(mixed_catalog):
    assert len(mixed_catalog.recommend(pop_happy_user(), k=1)) == 1


def test_recommend_k_larger_than_catalog_returns_all(mixed_catalog):
    results = mixed_catalog.recommend(pop_happy_user(), k=99)
    assert len(results) == len(mixed_catalog.songs)


def test_recommend_agrees_with_the_functional_path(mixed_catalog):
    """Both entry paths must rank identically, or the two are not one system."""
    from src.recommender import recommend_songs

    user = pop_happy_user()
    prefs = Recommender._prefs_from_user(user)
    catalog = [asdict(s) for s in mixed_catalog.songs]

    oop = [s.title for s in mixed_catalog.recommend(user, k=2)]
    functional = [song["title"] for song, _, _ in recommend_songs(prefs, catalog, k=2)]
    assert oop == functional


# --- Explanations ---

def test_explain_recommendation_returns_a_non_empty_string(mixed_catalog):
    explanation = mixed_catalog.explain_recommendation(
        pop_happy_user(), mixed_catalog.songs[0]
    )
    assert isinstance(explanation, str)
    assert explanation.strip()


def test_explain_recommendation_mentions_genre_match_for_a_fitting_song(mixed_catalog):
    perfect_pop = next(s for s in mixed_catalog.songs if s.title == "Perfect Pop")
    explanation = mixed_catalog.explain_recommendation(pop_happy_user(), perfect_pop)
    assert "genre match" in explanation


def test_explain_recommendation_falls_back_when_nothing_matches():
    # Nothing may contribute: genre and mood differ, energy is a full 1.0 away
    # so its closeness clamps to zero, and acousticness sits exactly halfway
    # from the preference so the penalty branch lands on zero too.
    rec = Recommender([make_song(genre="polka", mood="grim", energy=0.0,
                                 acousticness=0.5)])
    user = UserProfile("jazz", "cool", target_energy=1.0, likes_acoustic=False)
    assert rec.explain_recommendation(user, rec.songs[0]) == "no strong match"
