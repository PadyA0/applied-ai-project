"""Tests for the retrieval layer in src/rag.py.

The behaviour worth locking down here is not "does it find something" but
"does it refuse to find something when it should". A retriever that always
returns its best guess is indistinguishable from a system making things up, so
several of these tests target the abstain path.
"""

import logging

import pytest

from src.rag import (
    CONFIDENCE_BANDS,
    Note,
    RELEVANCE_THRESHOLD,
    build_index,
    confidence_label,
    build_query,
    fun_fact_for,
    load_index,
    load_notes,
    mentions_any,
    retrieve,
    tokenize,
    topic_phrases,
)

NOTES_PATH = "data/music_notes.md"


@pytest.fixture(scope="module")
def index():
    """The real corpus, indexed once and shared by the tests below."""
    return load_index(NOTES_PATH)


# --- Tokenizing ---

def test_tokenize_lowercases_and_splits():
    assert tokenize("Miles Davis") == ["miles", "davis"]


def test_tokenize_drops_stopwords():
    # "the" and "of" carry no signal about which note is the right one.
    assert "the" not in tokenize("the sound of the drum")
    assert "of" not in tokenize("the sound of the drum")


def test_tokenize_drops_single_characters():
    assert tokenize("a b jazz") == ["jazz"]


# --- Chunking the corpus ---

def test_load_notes_returns_notes(index):
    notes = load_notes(NOTES_PATH)
    assert len(notes) > 20
    assert all(isinstance(n, Note) for n in notes)


def test_load_notes_ignores_the_file_preamble():
    # Text above the first "### " heading explains the file format. If it were
    # chunked it could be retrieved and printed as a fun fact.
    notes = load_notes(NOTES_PATH)
    assert not any("splits on those headings" in n.body for n in notes)


def test_load_notes_gives_each_note_a_title_and_body():
    for note in load_notes(NOTES_PATH):
        assert note.title
        assert note.body


def test_note_ids_are_unique_and_sequential():
    notes = load_notes(NOTES_PATH)
    assert [n.note_id for n in notes] == list(range(len(notes)))


# --- Query construction ---

def test_build_query_uses_genre_artist_and_mood():
    song = {"title": "So What", "artist": "Miles Davis", "genre": "jazz", "mood": "cool"}
    query = build_query(song)
    assert "jazz" in query and "Miles Davis" in query and "cool" in query


def test_build_query_excludes_the_title():
    # Titles are full of common words that would pull in unrelated notes.
    song = {"title": "Storm Runner", "artist": "Voltline", "genre": "rock", "mood": "intense"}
    assert "Storm" not in build_query(song)


def test_build_query_tolerates_missing_fields():
    assert build_query({"genre": "jazz"}) == "jazz"


# --- Retrieval ---

def test_retrieve_finds_the_matching_artist_note(index):
    hits = retrieve(index, "jazz Miles Davis cool")
    assert hits
    assert "Miles Davis" in hits[0][0].title


def test_retrieve_finds_a_genre_note_when_the_artist_is_unknown(index):
    # Neon Echo is invented, so only the genre token can match anything.
    hits = retrieve(index, "pop Neon Echo happy")
    assert hits
    assert "pop" in hits[0][0].title.lower()


def test_retrieve_returns_nothing_for_an_undocumented_genre(index):
    # No note mentions ambient, so the honest answer is an empty result.
    assert retrieve(index, "ambient Orbit Bloom chill") == []


def test_retrieve_returns_nothing_for_an_empty_query(index):
    assert retrieve(index, "") == []


def test_retrieve_scores_are_above_the_threshold(index):
    for _, score in retrieve(index, "jazz Miles Davis cool", top_n=2):
        assert score > RELEVANCE_THRESHOLD


def test_retrieve_returns_hits_in_descending_order(index):
    scores = [score for _, score in retrieve(index, "reggaeton Bad Bunny playful", top_n=2)]
    assert scores == sorted(scores, reverse=True)


def test_retrieve_respects_top_n(index):
    assert len(retrieve(index, "pop happy", top_n=1)) <= 1


def test_retrieve_handles_an_empty_corpus():
    empty = build_index([])
    assert retrieve(empty, "jazz") == []


# --- Generation and grounding ---

def test_fun_fact_is_copied_from_the_corpus(index):
    song = {"title": "So What", "artist": "Miles Davis", "genre": "jazz", "mood": "cool"}
    fact = fun_fact_for(song, index)
    bodies = [n.body for n in index.notes]
    assert any(body in fact for body in bodies)


def test_fun_fact_abstains_when_nothing_is_relevant(index):
    song = {"title": "Spacewalk Thoughts", "artist": "Orbit Bloom",
            "genre": "ambient", "mood": "chill"}
    fact = fun_fact_for(song, index)
    assert "nothing in the notes about ambient" in fact


def test_abstain_message_names_the_missing_genre(index):
    song = {"genre": "polka", "artist": "Unlisted Artist", "mood": "jolly"}
    assert "polka" in fun_fact_for(song, index)


# --- Topicality: similar is not the same as on topic ---
# These are regression tests. Before the topic filter existed, a Brian Eno
# ambient track retrieved a fact about AC/DC, because the Back in Black note
# mentions Brian Johnson and scoring worked on single tokens. The text was
# genuine corpus text, so the grounding check saw nothing wrong with it.

def test_a_shared_first_name_does_not_make_a_note_relevant(index):
    song = {"title": "Music for Airports", "artist": "Brian Eno",
            "genre": "ambient", "mood": "dreamy"}
    fact = fun_fact_for(song, index)
    assert "AC/DC" not in fact
    assert "Back in Black" not in fact
    assert "nothing in the notes about ambient" in fact


def test_topic_phrases_are_the_genre_and_the_artist():
    song = {"genre": "jazz", "artist": "Miles Davis", "mood": "cool"}
    assert topic_phrases(song) == ["jazz", "miles davis"]


def test_mentions_any_requires_a_whole_word():
    note = Note(0, "pop", "Pop is less a sound than a chart position.")
    assert mentions_any(note, ["pop"])
    # "op" is inside "pop" but is not a word in it.
    assert not mentions_any(note, ["op"])


def test_a_note_naming_the_artist_is_eligible(index):
    song = {"genre": "rock", "artist": "Queen", "mood": "dramatic"}
    assert "Bohemian Rhapsody" in fun_fact_for(song, index)


def test_a_note_naming_only_the_genre_is_eligible(index):
    # Neon Echo is invented, so only the genre can qualify a note.
    song = {"genre": "synthwave", "artist": "Neon Echo", "mood": "moody"}
    fact = fun_fact_for(song, index)
    assert "nothing in the notes" not in fact
    assert "synthwave" in fact.lower()


def test_require_any_filters_out_otherwise_similar_notes(index):
    unfiltered = retrieve(index, "ambient Brian Eno dreamy", top_n=1)
    filtered = retrieve(index, "ambient Brian Eno dreamy", top_n=1,
                        require_any=["ambient", "brian eno"])
    # Similarity alone finds something; topicality correctly finds nothing.
    assert unfiltered
    assert filtered == []


# --- Confidence reporting ---

def test_confidence_label_bands():
    assert confidence_label(0.55) == "high"
    assert confidence_label(0.40) == "high"
    assert confidence_label(0.30) == "medium"
    assert confidence_label(0.20) == "medium"
    assert confidence_label(0.11) == "low"


def test_fun_fact_reports_its_confidence(index):
    song = {"artist": "Miles Davis", "genre": "jazz", "mood": "cool"}
    fact = fun_fact_for(song, index)
    assert "confidence" in fact
    assert any(band in fact for _, band in CONFIDENCE_BANDS)


# --- Error handling: the corpus is optional, the recommender is not ---

def test_load_index_survives_a_missing_corpus(tmp_path, caplog):
    """A missing corpus must degrade to abstaining, not crash the program."""
    missing = str(tmp_path / "not_here.md")
    with caplog.at_level(logging.WARNING):
        index = load_index(missing)
    assert len(index) == 0
    assert "Could not read the notes corpus" in caplog.text


def test_a_degraded_index_abstains_instead_of_guessing(tmp_path):
    index = load_index(str(tmp_path / "not_here.md"))
    fact = fun_fact_for({"genre": "jazz", "artist": "Miles Davis"}, index)
    assert "nothing in the notes about jazz" in fact


def test_load_index_warns_when_the_corpus_parses_to_nothing(tmp_path, caplog):
    # A file with no "### " headings is readable but yields no notes, which is
    # a formatting mistake worth saying out loud rather than silently ignoring.
    path = tmp_path / "empty.md"
    path.write_text("just some prose with no headings at all\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING):
        index = load_index(str(path))
    assert len(index) == 0
    assert "parsed to zero notes" in caplog.text


def test_load_notes_still_raises_so_callers_can_choose(tmp_path):
    # load_index swallows the error on purpose; load_notes does not, so a caller
    # that genuinely needs the corpus can still find out it is missing.
    with pytest.raises(OSError):
        load_notes(str(tmp_path / "not_here.md"))


def test_every_catalog_song_is_grounded_or_abstains(index):
    """The property that makes the layer safe: no third outcome exists."""
    from src.recommender import load_songs

    bodies = [n.body for n in index.notes]
    for song in load_songs("data/songs.csv"):
        fact = fun_fact_for(song, index)
        grounded = any(body in fact for body in bodies)
        abstained = "nothing in the notes about" in fact
        assert grounded or abstained, f"ungrounded fact for {song['title']}"
