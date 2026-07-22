"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    recommendations = recommend_songs(user_prefs, songs, k=5)

    # A little header describing what we searched for.
    print("\n" + "=" * 48)
    print("  TOP RECOMMENDATIONS")
    print(f"  for: genre={user_prefs['genre']}, "
          f"mood={user_prefs['mood']}, energy={user_prefs['energy']}")
    print("=" * 48 + "\n")

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        # Line 1: rank, title + artist, and the final score (right-aligned).
        header = f"{rank}. {song['title']} - {song['artist']}"
        print(f"{header:<38}{score:>6.2f} pts")
        # Line 2: the specific reasons the scorer generated, indented.
        print(f"   reasons: {explanation}")
        print()


if __name__ == "__main__":
    main()
