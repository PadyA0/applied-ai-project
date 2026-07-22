import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV into a list of dicts, converting numeric columns to int/float."""
    # Columns that should stay as text; everything else is coerced to a number.
    text_fields = {"title", "artist", "genre", "mood"}

    def to_number(value: str):
        # Whole numbers (id, tempo_bpm, popularity, release_decade) become ints;
        # anything with a decimal point (energy, valence, ...) becomes a float.
        try:
            return int(value)
        except ValueError:
            return float(value)

    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song: Dict = {
                key: value if key in text_fields else to_number(value)
                for key, value in row.items()
            }
            songs.append(song)

    return songs

# --- Scoring configuration: every feature below contributes to the score. ---

# Exact-match (categorical) features and the points a match is worth.
CATEGORICAL_WEIGHTS = {"genre": 2.0, "mood": 1.0}

# Numeric features already on a 0.0-1.0 scale. Points = weight * closeness,
# where closeness = 1 - |target - value| (so an exact match earns the full weight
# and a total mismatch earns 0 -- these features can only help, never hurt).
UNIT_WEIGHTS = {
    "energy": 1.0,
    "valence": 0.6,
    "danceability": 0.6,
    "instrumental": 0.4,
    "wordiness": 0.3,
}

# Penalizing 0.0-1.0 features. Here closeness = 1 - 2*|target - value|, which runs
# from +1 (perfect) through 0 (halfway off) to -1 (opposite), so a bad match
# actively subtracts points instead of merely adding nothing.
PENALIZED_UNIT_WEIGHTS = {
    "acousticness": 0.5,
}

# Numeric features on their own range: feature -> (min, max, weight).
# Closeness is normalized by the range width so all features are comparable.
RANGED_WEIGHTS = {
    "tempo_bpm": (60.0, 200.0, 0.5),
    "popularity": (0.0, 100.0, 0.5),
    "release_decade": (1900.0, 2030.0, 0.5),
}


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a song against every preference (categorical match + numeric closeness); return (score, reasons)."""
    score = 0.0
    reasons: List[str] = []

    # Categorical features: full points for an exact, case-insensitive match.
    for feature, weight in CATEGORICAL_WEIGHTS.items():
        pref = user_prefs.get(feature)
        if pref and str(song.get(feature, "")).lower() == str(pref).lower():
            score += weight
            reasons.append(f"{feature} match (+{weight:.1f})")

    # 0-1 scale features (reward-only): closeness stays >= 0, so they never hurt.
    for feature, weight in UNIT_WEIGHTS.items():
        pref = user_prefs.get(feature)
        if pref is not None and feature in song:
            closeness = max(0.0, 1.0 - abs(float(pref) - float(song[feature])))
            points = weight * closeness
            if points > 0:
                score += points
                reasons.append(f"{feature} fit (+{points:.2f})")

    # 0-1 scale features (penalizing): a bad match subtracts points.
    for feature, weight in PENALIZED_UNIT_WEIGHTS.items():
        pref = user_prefs.get(feature)
        if pref is not None and feature in song:
            closeness = 1.0 - 2.0 * abs(float(pref) - float(song[feature]))  # +1..-1
            points = weight * closeness
            if points != 0:
                score += points
                label = "fit" if points > 0 else "mismatch"
                reasons.append(f"{feature} {label} ({points:+.2f})")

    # Custom-range features: normalize the gap by the range width, then scale.
    for feature, (low, high, weight) in RANGED_WEIGHTS.items():
        pref = user_prefs.get(feature)
        if pref is not None and feature in song:
            span = high - low
            closeness = max(0.0, 1.0 - abs(float(pref) - float(song[feature])) / span)
            points = weight * closeness
            if points > 0:
                score += points
                reasons.append(f"{feature} fit (+{points:.2f})")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song and return the top k as (song, score, explanation), highest first."""
    # Judge every song in the catalog. One tuple per song: (song, score, explanation).
    scored = [
        (song, score, ", ".join(reasons) if reasons else "no strong match")
        for song in songs
        for score, reasons in [score_song(user_prefs, song)]
    ]

    # Sort highest score first, then keep only the top k.
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]
