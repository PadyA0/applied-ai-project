"""Retrieval layer: find a grounded fun fact for a recommended song.

This is the "RAG" half of the system. The pipeline is the standard one:

    corpus -> chunk -> index -> retrieve -> generate

with one deliberate addition. Retrieval is allowed to fail. If nothing in the
corpus scores above RELEVANCE_THRESHOLD, `fun_fact_for` abstains and says so
instead of producing a plausible sounding fact from nowhere. That abstain path
is the point of the whole layer: the system can only repeat what a human wrote
in data/music_notes.md, so it cannot invent a fact about a genre nobody
documented.

There is no model call here and no network access. Ranking is plain TF-IDF
cosine similarity in standard library Python, and "generation" fills a template
with retrieved text. That keeps the layer free, offline and deterministic,
which in turn makes it testable.
"""

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

DEFAULT_NOTES_PATH = "data/music_notes.md"

# A note must clear this cosine similarity to be used. Tuned against the current
# corpus: real genre and artist hits land well above it, while a song whose
# genre nobody has written about lands below and triggers the abstain path.
RELEVANCE_THRESHOLD = 0.10

# Similarity bands reported alongside each fun fact. The retriever knows how
# good its own match was, so it should say so rather than presenting a 0.12
# match and a 0.50 match in identical language.
CONFIDENCE_BANDS = (
    (0.40, "high"),
    (0.20, "medium"),
    (0.0, "low"),
)

# Words that appear across most notes and carry no signal about which note is
# the right one.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "have", "in", "is", "it", "its", "of", "on", "or", "that", "the",
    "to", "was", "were", "which", "with", "song", "music", "genre",
}


@dataclass
class Note:
    """One retrievable chunk of the corpus: a heading plus its body text."""
    note_id: int
    title: str
    body: str

    @property
    def text(self) -> str:
        """Title and body together, which is what gets matched against."""
        return f"{self.title} {self.body}"


@dataclass
class NoteIndex:
    """A searchable TF-IDF index over the corpus."""
    notes: List[Note] = field(default_factory=list)
    # note_id -> {term: normalized tf-idf weight}
    vectors: Dict[int, Dict[str, float]] = field(default_factory=dict)
    idf: Dict[str, float] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.notes)


def tokenize(text: str) -> List[str]:
    """Lowercase the text and split it into meaningful word tokens."""
    words = re.findall(r"[a-z0-9']+", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def confidence_label(similarity: float) -> str:
    """Turn a raw similarity score into a word a reader can act on."""
    for floor, label in CONFIDENCE_BANDS:
        if similarity >= floor:
            return label
    return "low"


def load_notes(path: str = DEFAULT_NOTES_PATH) -> List[Note]:
    """Chunk the markdown corpus into Notes, one per `### ` heading.

    Text before the first heading (the file's own preamble) is ignored, so the
    explanatory header in music_notes.md never gets retrieved as a fact.

    Raises the underlying OSError if the corpus cannot be read. Callers that
    want to survive a missing corpus should use `load_index`, which degrades to
    an empty index instead.
    """
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    notes: List[Note] = []
    title: Optional[str] = None
    body: List[str] = []

    def flush() -> None:
        # Close off the note we were accumulating, if there is one.
        if title is not None and body:
            notes.append(Note(len(notes), title, " ".join(body).strip()))

    for line in lines:
        if line.startswith("### "):
            flush()
            title = line[4:].strip()
            body = []
        elif title is not None and line.strip():
            body.append(line.strip())

    flush()
    return notes


def build_index(notes: List[Note]) -> NoteIndex:
    """Build normalized TF-IDF vectors for every note.

    Normalizing each vector to unit length means cosine similarity later is just
    a dot product, and it stops long notes from outranking short ones purely on
    word count.
    """
    total = len(notes)
    document_freq: Counter = Counter()
    tokenized: Dict[int, List[str]] = {}

    for note in notes:
        tokens = tokenize(note.text)
        tokenized[note.note_id] = tokens
        for term in set(tokens):
            document_freq[term] += 1

    # Smoothed IDF: rare terms (an artist name) outweigh common ones ("the mix").
    idf = {
        term: math.log(total / (1 + freq)) + 1.0
        for term, freq in document_freq.items()
    }

    vectors: Dict[int, Dict[str, float]] = {}
    for note in notes:
        tokens = tokenized[note.note_id]
        counts = Counter(tokens)
        raw = {term: (count / len(tokens)) * idf[term] for term, count in counts.items()}
        magnitude = math.sqrt(sum(w * w for w in raw.values())) or 1.0
        vectors[note.note_id] = {term: w / magnitude for term, w in raw.items()}

    return NoteIndex(notes=notes, vectors=vectors, idf=idf)


def build_query(song: Dict) -> str:
    """Turn a recommended song into a retrieval query.

    Genre, artist and mood only. The title is left out on purpose: titles are
    full of common words that pull in unrelated notes.
    """
    parts = [str(song.get(field, "") or "") for field in ("genre", "artist", "mood")]
    return " ".join(part for part in parts if part)


def topic_phrases(song: Dict) -> List[str]:
    """The phrases a note must mention to count as being about this song.

    Similarity alone is not enough. Scoring is done on single tokens, so a song
    by Brian Eno once retrieved a note about AC/DC purely because that note
    mentions Brian Johnson. The text was real, the fact was grounded, and it was
    still about the wrong band. Requiring the note to name the genre or the
    whole artist is what separates "similar" from "on topic".
    """
    phrases = []
    for field in ("genre", "artist"):
        value = str(song.get(field, "") or "").strip().lower()
        if value:
            phrases.append(value)
    return phrases


def phrase_hits(note: Note, phrases: List[str]) -> int:
    """How many of these phrases the note contains as whole words."""
    text = note.text.lower()
    return sum(
        1 for phrase in phrases
        if re.search(rf"\b{re.escape(phrase)}\b", text)
    )


def mentions_any(note: Note, phrases: List[str]) -> bool:
    """True if the note contains any of these phrases as whole words."""
    return phrase_hits(note, phrases) > 0


def retrieve(index: NoteIndex, query: str, top_n: int = 2,
             require_any: Optional[List[str]] = None) -> List[Tuple[Note, float]]:
    """Return the top_n notes most similar to the query, best first.

    Only notes scoring above RELEVANCE_THRESHOLD are returned, so an empty list
    is a meaningful answer: the corpus has nothing to say about this query.

    `require_any` adds a precision filter on top of that: a note is only
    eligible if it mentions one of the given phrases as a whole word. TF-IDF
    supplies the recall, this supplies the topicality.
    """
    tokens = tokenize(query)
    if not tokens or not index.notes:
        return []

    counts = Counter(tokens)
    raw = {
        term: (count / len(tokens)) * index.idf.get(term, 0.0)
        for term, count in counts.items()
    }
    magnitude = math.sqrt(sum(w * w for w in raw.values())) or 1.0
    query_vector = {term: w / magnitude for term, w in raw.items()}

    scored: List[Tuple[int, Note, float]] = []
    for note in index.notes:
        matched = phrase_hits(note, require_any) if require_any else 0
        if require_any and not matched:
            continue
        note_vector = index.vectors[note.note_id]
        # Cosine similarity of two unit vectors is their dot product. Iterate the
        # shorter side so the loop stays cheap.
        similarity = sum(
            weight * note_vector.get(term, 0.0)
            for term, weight in query_vector.items()
        )
        if similarity > RELEVANCE_THRESHOLD:
            scored.append((matched, note, similarity))

    # Notes matching more topic phrases win first, similarity only breaks ties.
    # A rock song by Queen should get the note naming both "Queen" and "rock",
    # not the ABBA note that happens to contain the words "Dancing Queen".
    scored.sort(key=lambda triple: (triple[0], triple[2]), reverse=True)
    return [(note, similarity) for _, note, similarity in scored[:top_n]]


def fun_fact_for(song: Dict, index: NoteIndex) -> str:
    """Retrieve a note about this song and format it as a fun fact line.

    The returned string always contains either verbatim corpus text or the
    abstain message. Nothing else can come out of this function, which is what
    the grounding check in src/reliability.py verifies.
    """
    hits = retrieve(index, build_query(song), top_n=1,
                    require_any=topic_phrases(song))
    if not hits:
        genre = song.get("genre") or "this song"
        return f"Fun fact: nothing in the notes about {genre} yet, so no fact to give."

    note, score = hits[0]
    return (
        f"Fun fact ({note.title}, {confidence_label(score)} confidence, "
        f"match {score:.2f}): {note.body}"
    )


def load_index(path: str = DEFAULT_NOTES_PATH) -> NoteIndex:
    """Read the corpus and index it, degrading to an empty index on failure.

    The fun fact layer is a garnish on top of the recommender, so a missing or
    unreadable corpus must not take the recommendations down with it. On failure
    this logs why and returns an empty index, which makes every song abstain.
    That is the same honest behaviour as a genre nobody wrote about, just
    applied to everything at once.
    """
    try:
        notes = load_notes(path)
    except OSError as error:
        log.warning("Could not read the notes corpus at %s (%s). "
                    "Continuing without fun facts.", path, error)
        return build_index([])

    if not notes:
        log.warning("The notes corpus at %s parsed to zero notes. "
                    "Check that it uses '### ' headings.", path)
    return build_index(notes)
