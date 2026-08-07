"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import logging
import sys
import textwrap

try:
    # Works when run as a module from the project root: python -m src.main
    from .recommender import load_songs, recommend_songs
    from .rag import load_index, fun_fact_for
except ImportError:
    # Works when run as a script from inside src/: python src/main.py
    from recommender import load_songs, recommend_songs
    from rag import load_index, fun_fact_for


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


# Three example profiles to experiment with. Each is (label, prefs); every key
# in a prefs dict is used by score_song, so add/drop keys to ignore features.
# Genre/mood tokens use exact catalog values (see data/songs.csv) so they match.
PROFILES = [
    ("Chill Indie  (indie pop / melancholic / low energy)",
     {"genre": "indie pop", "mood": "melancholic", "energy": 0.2}),
    ("Smooth Jazz  (jazz / cool / mid energy)",
     {"genre": "jazz", "mood": "cool", "energy": 0.4}),
    ("Upbeat Pop   (pop / happy / high energy)",
     {"genre": "pop", "mood": "happy", "energy": 0.8}),
    ("Deep Ambient (ambient / chill / very low energy)",
     {"genre": "ambient", "mood": "chill", "energy": 0.1}),
]


def print_profile_recommendations(label: str, user_prefs: dict, songs: list,
                                  index=None, k: int = 3) -> None:
    """Print a labeled header and a ranked recommendation table for one profile.

    If a note index is supplied, a retrieved fun fact about the top ranked song
    is printed underneath the table.
    """
    recommendations = recommend_songs(user_prefs, songs, k=k)

    print("\n" + "=" * 78)
    print(f"  {label}")
    print("  profile: " + ", ".join(f"{key}={value}" for key, value in user_prefs.items()))
    print("=" * 78)

    headers = ["#", "Title", "Artist", "Score", "Reasons"]
    widths = [2, 20, 16, 5, 44]
    rows = [
        [rank, song["title"], song["artist"], f"{score:.2f}", explanation]
        for rank, (song, score, explanation) in enumerate(recommendations, start=1)
    ]
    print(render_table(headers, rows, widths))

    # Retrieval step: look up a written note about the song that won, and print
    # it. When the corpus has nothing relevant this says so rather than guessing.
    if index is not None and recommendations:
        top_song = recommendations[0][0]
        print(textwrap.fill(fun_fact_for(top_song, index), width=78))


def ask_profile(genre: str, energy: float = 0.5) -> tuple:
    """Build a one off profile from a genre typed on the command line.

    Used by `python -m src.main --ask jazz`, which exists so a single genre can
    be demonstrated without scrolling past the four built in profiles.
    """
    return (f"Asked for: {genre}", {"genre": genre.lower(), "energy": energy})


def main() -> int:
    # Warnings from the retrieval layer go to stderr so they stay separate from
    # the tables on stdout.
    logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.INFO)

    # The catalog is not optional. Without it there is nothing to recommend, so
    # this fails loudly with an actionable message instead of a stack trace.
    try:
        songs = load_songs("data/songs.csv")
    except OSError as error:
        logging.error("Could not read data/songs.csv (%s). "
                      "Run this from the project root.", error)
        return 1

    if not songs:
        logging.error("data/songs.csv loaded but contains no songs.")
        return 1

    # The corpus IS optional. load_index degrades to an empty index and logs
    # why, and every song then abstains rather than the program dying.
    index = load_index("data/music_notes.md")

    print(f"Loaded songs: {len(songs)}")
    print(f"Loaded notes: {len(index)}")

    # --ask GENRE runs a single genre instead of all four demo profiles.
    if "--ask" in sys.argv:
        position = sys.argv.index("--ask")
        genre = " ".join(sys.argv[position + 1:]).strip()
        if not genre:
            logging.error("--ask needs a genre, for example: --ask jazz")
            return 1
        label, prefs = ask_profile(genre)
        print_profile_recommendations(label, prefs, songs, index=index)
        return 0

    # Run every example profile so their outputs can be compared side by side.
    for label, user_prefs in PROFILES:
        print_profile_recommendations(label, user_prefs, songs, index=index)

    return 0


if __name__ == "__main__":
    sys.exit(main())
