"""Tests for load_songs -- CSV loading with per-column type coercion.

load_songs keeps a fixed set of columns as text and coerces everything else to
a number, choosing int vs float via a try/except on int(). These tests cover
that branching plus the real data file on disk.
"""

from src.recommender import load_songs

CSV_HEADER = "id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness,instrumental,wordiness,popularity,release_decade"


def write_csv(tmp_path, *rows):
    path = tmp_path / "songs.csv"
    path.write_text("\n".join((CSV_HEADER, *rows)) + "\n", encoding="utf-8")
    return str(path)


def test_text_fields_stay_as_strings(tmp_path):
    csv_path = write_csv(
        tmp_path,
        "1,Sunrise City,Neon Echo,pop,happy,0.82,118,0.84,0.79,0.18,0.05,0.05,60,2020",
    )
    song = load_songs(csv_path)[0]
    assert song["title"] == "Sunrise City"
    assert song["artist"] == "Neon Echo"
    assert song["genre"] == "pop"
    assert song["mood"] == "happy"


def test_whole_numbers_become_ints(tmp_path):
    csv_path = write_csv(
        tmp_path,
        "1,Sunrise City,Neon Echo,pop,happy,0.82,118,0.84,0.79,0.18,0.05,0.05,60,2020",
    )
    song = load_songs(csv_path)[0]
    # id, tempo_bpm, popularity, release_decade have no decimal point -> int.
    for field in ("id", "tempo_bpm", "popularity", "release_decade"):
        assert isinstance(song[field], int), f"{field} should be int"


def test_decimal_numbers_become_floats(tmp_path):
    csv_path = write_csv(
        tmp_path,
        "1,Sunrise City,Neon Echo,pop,happy,0.82,118,0.84,0.79,0.18,0.05,0.05,60,2020",
    )
    song = load_songs(csv_path)[0]
    for field in ("energy", "valence", "danceability", "acousticness"):
        assert isinstance(song[field], float), f"{field} should be float"
    assert song["energy"] == 0.82


def test_loads_every_row(tmp_path):
    csv_path = write_csv(
        tmp_path,
        "1,A,X,pop,happy,0.8,120,0.8,0.8,0.2,0.1,0.1,60,2020",
        "2,B,Y,lofi,chill,0.4,80,0.6,0.5,0.9,0.8,0.0,55,2020",
        "3,C,Z,rock,intense,0.9,150,0.5,0.6,0.1,0.1,0.1,50,2010",
    )
    assert len(load_songs(csv_path)) == 3


def test_loads_real_data_file():
    songs = load_songs("data/songs.csv")
    assert len(songs) > 0
    first = songs[0]
    assert isinstance(first["id"], int)
    assert isinstance(first["energy"], float)
    assert isinstance(first["title"], str)
