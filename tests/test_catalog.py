"""Data integrity tests for data/songs.csv and data/music_notes.md.

The other test files check code. This one checks the data, because on a catalog
this size a typo is invisible by eye and silently changes every ranking. A
genre misspelled in one row simply never matches anything, and nothing crashes
to tell me about it.
"""

import pytest

from src.main import PROFILES
from src.rag import load_notes
from src.recommender import RANGED_WEIGHTS, UNIT_WEIGHTS, load_songs

SONGS_PATH = "data/songs.csv"
NOTES_PATH = "data/music_notes.md"

TEXT_FIELDS = ("title", "artist", "genre", "mood")


@pytest.fixture(scope="module")
def songs():
    return load_songs(SONGS_PATH)


@pytest.fixture(scope="module")
def notes():
    return load_notes(NOTES_PATH)


# --- Structure ---

def test_catalog_is_not_trivially_small(songs):
    assert len(songs) >= 100


def test_ids_are_unique(songs):
    ids = [s["id"] for s in songs]
    assert len(set(ids)) == len(ids)


def test_ids_are_sequential_from_one(songs):
    assert [s["id"] for s in songs] == list(range(1, len(songs) + 1))


def test_no_song_is_listed_twice(songs):
    pairs = [(s["title"], s["artist"]) for s in songs]
    duplicates = {p for p in pairs if pairs.count(p) > 1}
    assert not duplicates, f"duplicate entries: {duplicates}"


# --- Every field is populated ---

def test_text_fields_are_never_blank(songs):
    for song in songs:
        for field in TEXT_FIELDS:
            assert song[field].strip(), f"{song['title']}: blank {field}"


def test_no_numeric_field_failed_to_parse(songs):
    # load_songs turns anything unparseable into None. In the real catalog that
    # would mean a typo, not a deliberate unknown.
    for song in songs:
        for field, value in song.items():
            if field not in TEXT_FIELDS:
                assert value is not None, f"{song['title']}: {field} did not parse"


# --- Values are inside the ranges the scorer assumes ---

def test_unit_scale_features_stay_between_zero_and_one(songs):
    for song in songs:
        for field in UNIT_WEIGHTS:
            if field in song:
                assert 0.0 <= song[field] <= 1.0, f"{song['title']}: {field} out of range"


def test_acousticness_stays_between_zero_and_one(songs):
    for song in songs:
        assert 0.0 <= song["acousticness"] <= 1.0, song["title"]


def test_ranged_features_stay_inside_their_declared_range(songs):
    # A value outside the declared range clamps to zero closeness, so the
    # feature silently stops contributing for that song.
    for field, (low, high, _) in RANGED_WEIGHTS.items():
        for song in songs:
            assert low <= song[field] <= high, (
                f"{song['title']}: {field}={song[field]} outside {low}-{high}"
            )


# --- Categorical values are consistent ---

def test_genres_are_lowercase_and_trimmed(songs):
    # Matching is case insensitive, but inconsistent casing in the data makes
    # the coverage numbers in the reliability report hard to read.
    for song in songs:
        assert song["genre"] == song["genre"].strip().lower(), song["title"]


def test_moods_are_lowercase_and_trimmed(songs):
    for song in songs:
        assert song["mood"] == song["mood"].strip().lower(), song["title"]


def test_no_genre_is_a_near_duplicate_of_another(songs):
    # Catches "hip hop" vs "hip-hop", which would split one genre into two that
    # can never match each other.
    normalized = {}
    for genre in {s["genre"] for s in songs}:
        key = genre.replace("-", " ").replace("_", " ")
        normalized.setdefault(key, []).append(genre)
    collisions = {k: v for k, v in normalized.items() if len(v) > 1}
    assert not collisions, f"near duplicate genres: {collisions}"


def test_most_genres_have_more_than_one_song(songs):
    """A genre with a single song can only ever return that song."""
    genres = [s["genre"] for s in songs]
    singletons = sorted({g for g in genres if genres.count(g) == 1})
    # Some singletons are acceptable, but they should be the exception now.
    assert len(singletons) <= len(set(genres)) / 2, f"too many one song genres: {singletons}"


# --- The demo profiles must actually work ---

def test_every_demo_profile_genre_exists_in_the_catalog(songs):
    catalog_genres = {s["genre"] for s in songs}
    for label, prefs in PROFILES:
        assert prefs["genre"] in catalog_genres, f"{label}: unknown genre {prefs['genre']}"


def test_every_demo_profile_mood_exists_in_the_catalog(songs):
    catalog_moods = {s["mood"] for s in songs}
    for label, prefs in PROFILES:
        assert prefs["mood"] in catalog_moods, f"{label}: unknown mood {prefs['mood']}"


def test_every_demo_profile_energy_is_on_the_unit_scale():
    for label, prefs in PROFILES:
        assert 0.0 <= prefs["energy"] <= 1.0, label


# --- The notes corpus ---

def test_corpus_is_not_trivially_small(notes):
    assert len(notes) >= 50


def test_note_titles_are_unique(notes):
    titles = [n.title for n in notes]
    duplicates = {t for t in titles if titles.count(t) > 1}
    assert not duplicates, f"duplicate note titles: {duplicates}"


def test_no_note_body_is_empty(notes):
    for note in notes:
        assert note.body.strip(), f"empty note: {note.title}"


def test_notes_are_long_enough_to_be_worth_retrieving(notes):
    for note in notes:
        assert len(note.body) > 40, f"note too short to be useful: {note.title}"


def test_corpus_covers_most_catalog_genres(songs, notes):
    """Retrieval can only work for genres somebody wrote about."""
    corpus = " ".join(n.text.lower() for n in notes)
    genres = {s["genre"] for s in songs}
    covered = {g for g in genres if g in corpus}
    assert len(covered) / len(genres) >= 0.8, (
        f"only {len(covered)}/{len(genres)} genres appear in the corpus: "
        f"missing {sorted(genres - covered)}"
    )
