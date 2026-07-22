"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import textwrap

try:
    # Works when run as a module from the project root: python -m src.main
    from .recommender import load_songs, recommend_songs
except ImportError:
    # Works when run as a script from inside src/: python src/main.py
    from recommender import load_songs, recommend_songs


def render_table(headers, rows, widths) -> str:
    """Render rows as an ASCII grid table, wrapping any cell that exceeds its width.

    Pure standard library so it needs no extra install. If you'd rather use the
    `tabulate` package (pip install tabulate), the same table is one call:

        from tabulate import tabulate
        print(tabulate(rows, headers=headers, tablefmt="grid",
                       maxcolwidths=widths))
    """
    def divider() -> str:
        return "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def render_row(cells) -> str:
        # Wrap each cell to its column width, then stack cells that wrapped onto
        # multiple physical lines (blank padding keeps columns aligned).
        wrapped = [textwrap.wrap(str(c), w) or [""] for c, w in zip(cells, widths)]
        height = max(len(col) for col in wrapped)
        lines = []
        for i in range(height):
            parts = []
            for col, w in zip(wrapped, widths):
                text = col[i] if i < len(col) else ""
                parts.append(f" {text:<{w}} ")
            lines.append("|" + "|".join(parts) + "|")
        return "\n".join(lines)

    out = [divider(), render_row(headers), divider().replace("-", "=")]
    for row in rows:
        out.append(render_row(row))
        out.append(divider())
    return "\n".join(out)


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Example profile. Every key here is used by score_song, so all song
    # features play a role in the ranking. Drop any key to ignore that feature.
    user_prefs = {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "valence": 0.85,
        "danceability": 0.8,
        "acousticness": 0.15,
        "instrumental": 0.05,
        "wordiness": 0.10,
        "tempo_bpm": 120,
        "popularity": 80,
        "release_decade": 2020,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    # A little header describing the full profile we searched for.
    print("\n" + "=" * 48)
    print("  TOP RECOMMENDATIONS")
    print("  for profile:")
    for key, value in user_prefs.items():
        print(f"    - {key}: {value}")
    print("=" * 48 + "\n")

    # Build one table row per recommendation. The reasons column is included so
    # each score is explained right next to it.
    headers = ["#", "Title", "Artist", "Score", "Reasons"]
    widths = [2, 20, 16, 5, 44]
    rows = [
        [rank, song["title"], song["artist"], f"{score:.2f}", explanation]
        for rank, (song, score, explanation) in enumerate(recommendations, start=1)
    ]
    print(render_table(headers, rows, widths))


if __name__ == "__main__":
    main()
