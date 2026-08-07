# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

Sawndz 2.0

---

## 2. Intended Use

- What kind of recommendations does it generate

The model recommends songs to a user. It helps them make a choice according to their preference input, and it tells them a fun fact about whatever song it picked.

- What assumptions does it make about the user

It assumes the user has specific taste and that their mood can influence it. It also assumes they can describe that taste as a genre, a mood and an energy level, which is a real assumption because plenty of people cannot name the genre of the music they like.

- Is this for real users or classroom exploration

Classroom exploration. The catalog is 100 songs, which is enough to make the system behave interestingly but nowhere near enough for real recommendations. A real platform is working with millions of tracks and actual listening history, not a CSV I typed out by hand.

---

## 3. How the Model Works

The system has two halves. The first one picks songs. The second one finds something to say about the song it picked.

**Picking the songs.** Every song in the catalog gets a single number, and the highest number wins. That number comes from comparing the song to the user's profile across eleven features:

- Genre and mood are exact matches. If they match you get the points, if they do not you get nothing.
- Energy, valence, danceability, instrumental and wordiness are on a 0 to 1 scale, and the closer the song is to what the user asked for, the more points it earns. These can only help, never hurt.
- Acousticness works the same way except it can go negative. If someone wants acoustic and the song is fully electronic, that subtracts points instead of just adding zero.
- Tempo, popularity and release decade are on their own ranges, so the distance gets normalized by how wide the range is before it turns into points.

Genre is weighted at 2.0, which is double a mood match and double a perfect energy match. That is deliberate. If someone asks for jazz, giving them a pop song with the right mood is a worse answer than a jazz song with the wrong mood.

Every score comes back with a list of reasons, so the output does not just say 3.90, it says genre match, mood match, energy fit and what each one was worth.

**Finding the fun fact.** This part is retrieval augmented generation. I wrote a corpus of 113 notes about genres, artists and specific songs. When the recommender picks a winner, the system searches that corpus using the song's genre and artist, ranks the notes by TF-IDF similarity, and prints the best one.

The important part is that it is allowed to find nothing. If no note is relevant enough, it says so instead of making something up. There is no language model in this half and no API call. It runs offline on the Python standard library, which costs nothing and means it gives the same answer every time.

- What changes did you make from the starter logic

The starter code returned the first few songs with placeholder scores and no real logic. I implemented the CSV loading, the scoring rule and the ranking. I made genre and mood matching case insensitive. I moved the weights out of if statements and into lookup tables so adding a feature is one line instead of a new block of code. Then I added the retrieval layer and the reliability harness, neither of which was in the starter at all.

---

## 4. Data

- How many songs are in the catalog

100 songs across 32 genres. It started at 20, then 40, and I grew it to 100 so that every genre would have more than one song in it.

- What genres or moods are represented

The genres span across the globe: afrobeats, amapiano, soca, bhangra, arabic pop, flamenco pop, k-pop, j-pop, reggaeton, alongside the more expected pop, rock, jazz, metal, soul, funk, disco, house, hip hop, r&b and country. Moods run from happy and euphoric through to melancholic, angsty and mysterious.

There is a second dataset too, which is `data/music_notes.md`. That is 113 notes I wrote by hand about genres and artists, and it is the only thing the fun fact layer is allowed to know.

- Did you add or remove data

I added a lot. The original catalog was mostly invented songs by invented artists. I kept a few of those on purpose, because they are what tests the retrieval layer's behavior when nobody has written anything about an artist, but the majority of the catalog is real songs now.

- Are there parts of musical taste missing in the dataset

Loudness, which I did not add because it overlaps with energy. Language, which matters a lot for a catalog this international and is not represented anywhere. And anything about what a song is actually about. The wordiness feature is just a number saying roughly how many words there are, not what any of them mean.

---

## 5. Strengths

It gives the most intuitive results when a user's genre and mood both exist in the catalog. For a pop, happy, 0.8 energy profile, Sunrise City scored 3.98 and landed on top, which is exactly what I expected because it matches all three signals.

The reasons column is the strength I did not anticipate. Every recommendation explains itself, so I can tell the difference between a song that won because it genuinely fits and a song that won because it scraped points off five weak partial matches. That is what makes the whole thing debuggable.

The measured version: genre accuracy is 100 percent across all 32 genres, meaning if you ask for a genre, you get that genre at rank 1 every single time.

---

## 6. Limitations and Bias

- Features it does not consider

The system now scores all eleven features I put in the CSV, so the old version of this problem is fixed. What it still does not consider is anything semantic. It has no idea what a song is about, what language it is in, or whether the lyrics match the mood label I gave it. Two songs that feel completely different to a person can still score identically.

- Genres or moods that are underrepresented

Genre matching is still exact string matching, so indie pop and pop are two unrelated things as far as the model is concerned. Someone who likes indie pop gets nothing from the pop section even though a human would obviously connect them. Same for disco pop, electropop and every other fusion label in the catalog.

The fun fact corpus has its own coverage gaps. It covers 29 genres out of 32, so ambient songs get no fact at all.

- Cases where the system overfits to one preference

Genre at 2.0 is worth double everything else, so a genre match nearly guarantees a top slot even when mood and energy are both wrong. The 100 percent genre accuracy number in the strengths section is the same fact viewed from a friendlier angle. It means the other ten features are mostly just deciding the ordering inside one genre.

- Ways the scoring might unintentionally favor some users

There is a catalog bias and growing the catalog did not remove it, it moved it. When I had 40 songs the problem was genres with only one song in them. Now that I have 100, 18 songs can never reach a top 3 slot for any genre profile, because they are competing against other songs in their own genre that always beat them. Toxic, Umbrella and Stairway to Heaven are all in the catalog and all effectively invisible.

There is also a bias in the notes corpus that is worth naming, which is that it only knows what I knew enough to write down.

---

## 7. Evaluation

I check this two different ways, because they answer different questions.

**Reading the output.** I run the main program and read the ranked results with their reasons. The reasons make it easy to see why each song was recommended. What surprised me early on was how a song matching neither genre nor mood could still reach the top five just by hitting the energy target.

**Measuring it.** I built a reliability harness (`python -m src.reliability`) that runs six checks and writes a report. Current results on 100 songs and 113 notes:

| Check | Result |
| --- | --- |
| Determinism | Identical rankings across repeated runs |
| Golden snapshot | No drift from the approved baseline |
| Genre accuracy at rank 1 | 32/32 genres, 100 percent |
| Catalog coverage | 82 percent of songs reachable |
| Perturbation robustness | 0 percent material churn |
| Fun fact grounding | 0 ungrounded claims out of 100 songs |

On top of that there are 122 unit tests covering the loader, scorer, ranker, formatter, retriever, the harness itself, and the data.

**Guardrails.** Two of those checks are guardrails rather than metrics. Grounding walks the entire catalog and confirms every fun fact is either copied word for word from my corpus or is the honest refusal message, so there is no third possible outcome where the system says something nobody wrote. The golden snapshot check fails on any ranking change until I explicitly approve the new baseline, which makes changing the output a decision instead of an accident.

The most useful thing evaluation did was catch a bug I could not see. A Brian Eno ambient track was returning a fun fact about AC/DC, because my AC/DC note mentions Brian Johnson and the retriever was matching on single words. The grounding check passed it, because the text really was from my corpus. It was still about the wrong band. That taught me that grounded and relevant are two separate properties and I had only been checking one of them.

---

## 8. Future Work

The features I wanted last time are done. Tempo, danceability and acousticness all score by closeness to a target now, the same way energy does, and acousticness can even penalize.

What I would do next:

- **Fuzzy genre matching**, so indie pop counts as a partial match for pop instead of scoring zero. This is the single biggest gap left.
- **Diversity in the top results.** Right now the top 3 for a genre profile is almost always three songs from that one genre. Real recommenders deliberately mix in something adjacent.
- **A tie breaker with meaning.** My robustness testing showed songs routinely scoring within a hundredth of each other, and which one lands first is currently arbitrary. Breaking ties by popularity or release decade would at least make it a choice.
- **Grow the notes corpus and track its coverage**, since 3 genres currently have no fun fact at all and the system just refuses for them.
- **Something semantic.** Even a simple keyword layer over lyrics would let the system answer "sad songs in Spanish" instead of only "sad songs".

---

## 9. Personal Reflection

Building this made me realize how much of a recommender is just turning preferences into numbers and sorting them using a magic scoring rule basically. The intelligent looking part is really the recipe, and how I choose to weight the features is what decides the output.

The thing I did not expect was how much the catalog shapes everything. When I had 20 songs and some genres appearing only once, the fairness was clearly off. So I grew it to 100 thinking that would fix it, and it did fix the thin genres, but it created a new problem where 18 songs became permanently unreachable. Adding data solved one bias and introduced another one, and I only know that because I measured it.

The other thing that stuck with me is from the fun fact layer. I had a check confirming every fact came from my own corpus, and it passed, and the system was still telling me about the wrong band. Verifying that output came from a legitimate source felt like a much stronger guarantee than it actually is. That changed how I think about the music apps I use, because when Spotify tells me why it picked something, I now wonder what exactly they checked before showing me that sentence.
