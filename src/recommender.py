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
    # Columns that should stay as text; everything else is treated as numeric.
    text_fields = {"title", "artist", "genre", "mood"}

    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song: Dict = {}
            for key, value in row.items():
                if key == "id":
                    song[key] = int(value)
                elif key in text_fields:
                    song[key] = value
                else:
                    song[key] = float(value)
            songs.append(song)

    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a song vs. prefs (+2 genre, +1 mood, up to +1 energy fit); return (score, reasons)."""
    score = 0.0
    reasons: List[str] = []

    # Genre match (+2.0). Compare case-insensitively so "Pop" == "pop".
    if user_prefs.get("genre") and song.get("genre", "").lower() == user_prefs["genre"].lower():
        score += 2.0
        reasons.append("genre match (+2.0)")

    # Mood match (+1.0).
    if user_prefs.get("mood") and song.get("mood", "").lower() == user_prefs["mood"].lower():
        score += 1.0
        reasons.append("mood match (+1.0)")

    # Energy fit (up to +1.0). Reward songs whose energy is close to the target.
    if user_prefs.get("energy") is not None and "energy" in song:
        target = float(user_prefs["energy"])
        energy_fit = 1.0 - abs(target - float(song["energy"]))
        energy_fit = max(0.0, energy_fit)  # never let a big mismatch subtract
        score += energy_fit
        reasons.append(f"energy fit (+{energy_fit:.2f})")

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
