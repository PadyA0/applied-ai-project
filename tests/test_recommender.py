from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def make_ordering_recommender() -> Recommender:
    """Catalog whose best match is NOT first, so a real sort is required."""
    return Recommender([
        # Deliberately first, but the worst fit for the pop/happy user below.
        Song(
            id=1,
            title="Wrong Rock",
            artist="A",
            genre="rock",
            mood="intense",
            energy=0.1,
            tempo_bpm=150,
            valence=0.4,
            danceability=0.5,
            acousticness=0.9,
        ),
        # Best fit, but placed last in the input list.
        Song(
            id=2,
            title="Perfect Pop",
            artist="B",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.1,
        ),
    ])


def pop_happy_user(likes_acoustic: bool = False) -> UserProfile:
    return UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=likes_acoustic,
    )


def test_recommend_sorts_best_match_first_despite_input_order():
    rec = make_ordering_recommender()
    results = rec.recommend(pop_happy_user(), k=2)

    # "Perfect Pop" is last in the catalog but must be ranked first.
    assert [s.title for s in results] == ["Perfect Pop", "Wrong Rock"]


def test_recommend_results_are_in_non_increasing_score_order():
    rec = make_ordering_recommender()
    user = pop_happy_user()

    results = rec.recommend(user, k=len(rec.songs))
    prefs = Recommender._prefs_from_user(user)
    from dataclasses import asdict
    from src.recommender import score_song

    scores = [score_song(prefs, asdict(s))[0] for s in results]
    assert scores == sorted(scores, reverse=True)


def test_recommend_respects_k():
    rec = make_ordering_recommender()
    assert len(rec.recommend(pop_happy_user(), k=1)) == 1


def test_recommend_k_larger_than_catalog_returns_all():
    rec = make_ordering_recommender()
    results = rec.recommend(pop_happy_user(), k=99)
    assert len(results) == len(rec.songs)


def test_explain_recommendation_mentions_genre_match_for_fitting_song():
    rec = make_ordering_recommender()
    perfect_pop = next(s for s in rec.songs if s.title == "Perfect Pop")

    explanation = rec.explain_recommendation(pop_happy_user(), perfect_pop)
    assert "genre match" in explanation


def test_likes_acoustic_flips_acousticness_preference():
    # A highly acoustic song should score better for an acoustic-loving user
    # than for one who dislikes acoustic (the penalty branch flips sign).
    acoustic_song = Song(
        id=3,
        title="Acoustic Ballad",
        artist="C",
        genre="folk",
        mood="calm",
        energy=0.3,
        tempo_bpm=90,
        valence=0.5,
        danceability=0.3,
        acousticness=1.0,
    )
    rec = Recommender([acoustic_song])
    from dataclasses import asdict
    from src.recommender import score_song

    likes = score_song(
        Recommender._prefs_from_user(pop_happy_user(likes_acoustic=True)),
        asdict(acoustic_song),
    )[0]
    dislikes = score_song(
        Recommender._prefs_from_user(pop_happy_user(likes_acoustic=False)),
        asdict(acoustic_song),
    )[0]
    assert likes > dislikes
