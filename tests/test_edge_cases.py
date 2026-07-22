"""Edge-case / boundary tests across the recommender.

These cover empty inputs, zero-length requests, and degenerate data that the
happy-path tests don't reach.
"""

import pytest

from src.recommender import (
    load_songs,
    score_song,
    recommend_songs,
    Recommender,
    Song,
    UserProfile,
    CATEGORICAL_WEIGHTS,
)

CSV_HEADER = "id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness,instrumental,wordiness,popularity,release_decade"


# --- recommend_songs boundaries ---

def test_recommend_songs_empty_catalog_returns_empty():
    assert recommend_songs({"genre": "pop"}, [], k=5) == []


def test_recommend_songs_k_zero_returns_empty():
    catalog = [{"genre": "pop"}, {"genre": "rock"}]
    assert recommend_songs({"genre": "pop"}, catalog, k=0) == []


def test_recommend_songs_empty_prefs_scores_everything_zero():
    catalog = [{"genre": "pop"}, {"genre": "rock"}]
    results = recommend_songs({}, catalog, k=2)
    assert all(score == 0.0 for _, score, _ in results)
    assert all(explanation == "no strong match" for _, _, explanation in results)


def test_recommend_songs_preserves_input_order_on_ties():
    # Equal scores (all zero) -> Python's stable sort keeps original order.
    catalog = [{"title": "first"}, {"title": "second"}, {"title": "third"}]
    results = recommend_songs({}, catalog, k=3)
    assert [song["title"] for song, _, _ in results] == ["first", "second", "third"]


# --- score_song degenerate inputs ---

def test_score_song_empty_song_and_prefs():
    score, reasons = score_song({}, {})
    assert score == 0.0
    assert reasons == []


def test_score_song_falsy_categorical_pref_is_ignored():
    # An empty-string genre preference is falsy, so it contributes nothing
    # even though the song technically has an empty genre too.
    score, reasons = score_song({"genre": ""}, {"genre": ""})
    assert score == 0.0
    assert reasons == []


# --- load_songs boundaries ---

def test_load_songs_header_only_returns_empty(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text(CSV_HEADER + "\n", encoding="utf-8")
    assert load_songs(str(path)) == []


def test_load_songs_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_songs(str(tmp_path / "does_not_exist.csv"))


def test_load_songs_non_numeric_value_becomes_none(tmp_path):
    # A non-numeric value in a numeric column must NOT crash the loader; it is
    # stored as None ("unknown") instead of propagating a ValueError.
    path = tmp_path / "bad.csv"
    path.write_text(
        CSV_HEADER + "\n"
        "1,Song,Artist,pop,happy,not_a_number,120,0.8,0.8,0.2,0.1,0.1,60,2020\n",
        encoding="utf-8",
    )
    song = load_songs(str(path))[0]
    assert song["energy"] is None
    # Valid columns on the same row still parse normally.
    assert song["tempo_bpm"] == 120
    assert song["title"] == "Song"


def test_load_songs_blank_numeric_cell_becomes_none(tmp_path):
    path = tmp_path / "blank.csv"
    path.write_text(
        CSV_HEADER + "\n"
        "1,Song,Artist,pop,happy,,120,0.8,0.8,0.2,0.1,0.1,60,2020\n",
        encoding="utf-8",
    )
    assert load_songs(str(path))[0]["energy"] is None


def test_score_song_skips_none_feature_value():
    # A song with an unknown (None) numeric feature is scored on its other
    # features without raising -- the None feature simply contributes nothing.
    song = {"genre": "pop", "energy": None, "acousticness": None, "tempo_bpm": None}
    prefs = {"genre": "pop", "energy": 0.8, "acousticness": 0.2, "tempo_bpm": 120}
    score, reasons = score_song(prefs, song)
    assert score == CATEGORICAL_WEIGHTS["genre"]  # only the genre match counts
    assert all("energy" not in r for r in reasons)


def test_recommend_ranks_song_with_missing_feature(tmp_path):
    # End-to-end: a catalog row with a bad numeric cell still loads and ranks.
    path = tmp_path / "mixed.csv"
    path.write_text(
        CSV_HEADER + "\n"
        "1,Good Pop,A,pop,happy,0.8,120,0.9,0.8,0.15,0.05,0.05,80,2020\n"
        "2,Broken,B,pop,happy,oops,120,0.9,0.8,0.15,0.05,0.05,80,2020\n",
        encoding="utf-8",
    )
    songs = load_songs(str(path))
    results = recommend_songs({"genre": "pop", "energy": 0.8}, songs, k=2)
    # Both rank; the complete row outscores the one missing its energy value.
    assert results[0][0]["title"] == "Good Pop"
    assert len(results) == 2


# --- Recommender boundaries ---

def test_recommender_empty_catalog_returns_empty():
    rec = Recommender([])
    user = UserProfile("pop", "happy", 0.8, likes_acoustic=False)
    assert rec.recommend(user, k=5) == []


def test_recommender_k_zero_returns_empty():
    song = Song(1, "T", "A", "pop", "happy", 0.8, 120, 0.9, 0.8, 0.2)
    rec = Recommender([song])
    user = UserProfile("pop", "happy", 0.8, likes_acoustic=False)
    assert rec.recommend(user, k=0) == []
