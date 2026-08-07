# 🎵 Music Recommender Simulation

## Project Summary

This program is a music recommender that uses rules to prioritize the best option for the user.

## How The System Works

My design started as a simple approach at making a music recommender. It now features AI engineering techniques like RAG to implement a fun fact generator in the terminal output.

 Music platforms in the real world tend to combine core-based filtering and content-based filtering to give the best option to the user. This program is a modest, but effective way to duplicate a more realistic platform like Youtube Music. My system will be more biased towards the genre and tempo though. In my experience, playing an upbeat hip hop song with sad themes to follow up another upbeat hip hop song that has happy themes at a party, it makes for a less brutal disruption to the dance moves and the state of mind.


- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo
Each song presents features like the genre, mood, tempo, and energy that help categorize it in an algorithm.

- What information does your `UserProfile` store
This stores information about the preferences input by the user. Maybe the listener is a pop fan or maybe they want a energyzed beat for the gym. That information is collected in the UserProfile to tailor the recommendations to that. 

- How does your `Recommender` compute a score for each song
The recommender computes a weighted final numerical value to both score and rank the songs in the list of recommendations. There are two different formulas at play that first measure how much of a good match a song is, then a decision maker for the actual song.
The core ide is that each song uses the single numerical score by adding different components, the song attributes, multiplied by a weight. 

- How do you choose which songs to recommend

My recommender, while using a weighted score to combine core-based filtering and content-based filtering, might prioritize genre and tempo. A genre match will be a stronger signal than a mood match.

### Architecture

A diagram of the whole system lives in [`diagrams/architecture.mmd`](diagrams/architecture.mmd). In words, the system is a straight pipeline with a testing loop hanging off it:

**Input.** Two things come in: the song catalog (`data/songs.csv`, 100 songs with 14 columns each) and a user taste profile, which is just a dictionary of preferences like `{"genre": "pop", "mood": "happy", "energy": 0.8}`.

**Process.** Six components, each doing one job:

- **Loader** (`load_songs`) reads the CSV and turns each row into a dictionary, converting the numeric columns to ints and floats. Anything it can't parse becomes `None`, which means "unknown", so scoring skips those fields instead of crashing or guessing.
- **Weight config** is the four dictionaries near the top of `recommender.py` (`CATEGORICAL_WEIGHTS`, `UNIT_WEIGHTS`, `PENALIZED_UNIT_WEIGHTS`, `RANGED_WEIGHTS`). This is the tuning surface, so the genre weight experiments described below are just edits to these numbers.
- **Scorer** (`score_song`) compares one song against one profile, walking all four weight groups, and returns both a number and a list of reasons. Returning the reasons alongside the score is what makes the output explainable.
- **Ranker** (`recommend_songs`) calls the scorer once per song, sorts highest first, and keeps the top k.
- **Retriever** (`src/rag.py`) takes the winning song and searches `data/music_notes.md` for something written about its genre or artist. Ranking is TF-IDF cosine similarity in plain standard library Python.
- **Generator** (`fun_fact_for`) fills a template with the retrieved note text and reports how confident the match was, as a band (high, medium, low) and a raw similarity number. There is no model call and no network access, which is what keeps the layer free, offline and deterministic.

**Output.** `render_table` formats the ranked results as an ASCII grid with the reasons wrapped into the last column, followed by the retrieved fun fact and its confidence.

**What happens when something is missing.** The two data files are not equally important, so they fail differently. The catalog is required, so a missing `data/songs.csv` logs an error and exits 1 rather than printing an empty table. The notes corpus is optional, so a missing `data/music_notes.md` logs a warning and carries on with an empty index, which makes every song abstain. Losing the garnish does not take down the meal.

**Why the retriever is allowed to fail.** If no note clears the relevance threshold, the system prints "nothing in the notes about ambient yet" instead of producing a fact from nowhere. That refusal is the whole point of grounding the layer in a corpus. The system can only repeat what a human wrote down, so it cannot invent a claim about a genre nobody documented.

**Testing and human review.** Two separate layers check the system, because they answer different questions:

- The **pytest suite** (128 tests) asks "does each function do what I said it does". It covers the loader, scorer, ranker, formatter, retriever and the harness itself.
- The **evaluator** (`src/reliability.py`) asks "does the system as a whole stay trustworthy when I change something". It measures determinism, drift against a saved baseline, genre accuracy, catalog coverage, robustness to tiny input changes, and whether every fun fact is traceable to the corpus.

The human sits at the end of both. I read the reasons column to judge whether a ranking is actually sensible, and I approve the golden baseline before it becomes the thing future runs are measured against. When either one looks wrong, the fix is to go back and change the weight config. That loop, from output to human judgment to weights, is the arrow that closes the diagram.

One structural note: there are two ways into the same scoring core. `main.py` uses the plain dictionary functions, while the `Recommender` class with its `Song` and `UserProfile` dataclasses is an object oriented wrapper that translates a `UserProfile` into the same preferences dictionary before calling `score_song`. Both paths score songs identically. Only the interface differs.

---

## Getting Started

### Setup Instructions

Everything here runs offline on the Python standard library. There is no API key to obtain, no account to create and no per run cost.

**1. Clone the repository and enter it**

```bash
git clone <your-repo-url>
cd applied-ai-system-final
```

**2. Create a virtual environment** (optional but recommended)

```bash
python -m venv .venv
```

Then activate it:

```bash
source .venv/bin/activate      # Mac or Linux
.venv\Scripts\activate         # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the recommender**

```bash
python -m src.main
```

Run this from the project root, not from inside `src/`. The paths to `data/songs.csv` and `data/music_notes.md` are relative to the root. You should see `Loaded songs: 100` and `Loaded notes: 113`, then one table per profile with a fun fact underneath.

**5. Run the reliability evaluator**

```bash
python -m src.reliability
```

This prints a pass or fail line per check and writes a full report to `tests/results/reliability_report.md`. It exits with status 0 when everything passes and 1 when anything fails, so it can be wired into CI later.

If you change a weight in `recommender.py` on purpose and the golden snapshot check fails as a result, approve the new rankings as the baseline:

```bash
python -m src.reliability --update-golden
```

### Running Tests

Run the whole suite from the project root:

```bash
pytest
```

To write the results into `tests/results/` the way this repo records them:

```bash
pytest -q --junitxml=tests/results/junit.xml > tests/results/results.txt 2>&1
```

The suite is 128 tests across 9 files. I wrote at least one test per method in `recommender.py`, plus edge cases for the scoring boundaries, plus `tests/test_rag.py` for the retrieval layer and `tests/test_reliability.py` for the evaluator. The retrieval tests deliberately spend more effort on the refusal path than the success path, because a retriever that always returns its best guess is indistinguishable from a system making things up.

### What Each Command Produces

| Command | What it does | Where the output goes |
| --- | --- | --- |
| `python -m src.main` | Ranked recommendations plus a retrieved fun fact per profile | terminal |
| `python -m src.reliability` | Six reliability checks | terminal and `tests/results/reliability_report.md` |
| `python -m src.reliability --update-golden` | Re-approves the current rankings as the baseline | `tests/golden_recommendations.json` |
| `pytest` | 90 unit and integration tests | terminal |

---

## Sample Interactions

These are copied straight from real runs of `python -m src.main` and `python -m src.reliability`. The first three show the recommender and the fun fact retriever working together. The fourth one is the evaluator. I picked these four because each one shows a different thing, including the system refusing to answer, which ended up being the part I care about most.

### Interaction 1: a genre with a documented artist

**Input**

```python
{"genre": "jazz", "mood": "cool", "energy": 0.4}
```

**Output**

```text
==============================================================================
  Smooth Jazz  (jazz / cool / mid energy)
  profile: genre=jazz, mood=cool, energy=0.4
==============================================================================
+----+----------------------+------------------+-------+----------------------------------------------+
| #  | Title                | Artist           | Score | Reasons                                      |
+====+======================+==================+=======+==============================================+
| 1  | So What              | Miles Davis      | 3.90  | genre match (+2.0), mood match (+1.0),       |
|    |                      |                  |       | energy fit (+0.90)                           |
+----+----------------------+------------------+-------+----------------------------------------------+
| 2  | Coffee Shop Stories  | Slow Stereo      | 2.97  | genre match (+2.0), energy fit (+0.97)       |
+----+----------------------+------------------+-------+----------------------------------------------+
| 3  | Take Five            | Dave Brubeck     | 2.95  | genre match (+2.0), energy fit (+0.95)       |
+----+----------------------+------------------+-------+----------------------------------------------+
Fun fact (Miles Davis, So What, match 0.35): "So What" opens Kind of Blue from
1959 and is a landmark of modal jazz. It stays on two scales instead of moving
through chord changes, which left the soloists far more room.
```

What I want to point out here is that the retriever had a choice. There is a general note about jazz in my corpus and there is a specific note about Miles Davis. It picked the artist one. That happens because "miles" and "davis" are rare words across the whole corpus and TF-IDF gives rare words more weight. So the specific note beats the generic note without me writing any rule that says so.

### Interaction 2: a genre with an artist the corpus has never heard of

**Input**

```python
{"genre": "pop", "mood": "happy", "energy": 0.8}
```

**Output**

```text
==============================================================================
  Upbeat Pop   (pop / happy / high energy)
  profile: genre=pop, mood=happy, energy=0.8
==============================================================================
+----+----------------------+------------------+-------+----------------------------------------------+
| #  | Title                | Artist           | Score | Reasons                                      |
+====+======================+==================+=======+==============================================+
| 1  | Sunrise City         | Neon Echo        | 3.98  | genre match (+2.0), mood match (+1.0),       |
|    |                      |                  |       | energy fit (+0.98)                           |
+----+----------------------+------------------+-------+----------------------------------------------+
| 2  | Umbrella             | Rihanna          | 3.00  | genre match (+2.0), energy fit (+1.00)       |
+----+----------------------+------------------+-------+----------------------------------------------+
| 3  | Billie Jean          | Michael Jackson  | 2.99  | genre match (+2.0), energy fit (+0.99)       |
+----+----------------------+------------------+-------+----------------------------------------------+
Fun fact (pop, match 0.49): Pop is less a sound than a chart position. The
label follows whatever is selling at the time, which is why a 1983 pop record
and a 2020 pop record can share almost no instruments.
```

Neon Echo is a made up artist that I invented for the catalog, so no note in my corpus mentions them. The retriever fell back to the genre note. What I like about this is that it did not go grab the Rihanna or the Michael Jackson note just because those are sitting right there in the same table and it knows things about them. It answers about the song that actually won, not about whichever song it has the best trivia for.

Also notice how close the scores are. Umbrella at 3.00 and Billie Jean at 2.99. That one hundredth of a point is the entire reason one is above the other, and it comes back later in the testing section.

### Interaction 3: a genre nobody wrote a note about

**Input**

```python
{"genre": "ambient", "mood": "chill", "energy": 0.1}
```

**Output**

```text
==============================================================================
  Deep Ambient (ambient / chill / very low energy)
  profile: genre=ambient, mood=chill, energy=0.1
==============================================================================
+----+----------------------+------------------+-------+----------------------------------------------+
| #  | Title                | Artist           | Score | Reasons                                      |
+====+======================+==================+=======+==============================================+
| 1  | Weightless           | Marconi Union    | 4.00  | genre match (+2.0), mood match (+1.0),       |
|    |                      |                  |       | energy fit (+1.00)                           |
+----+----------------------+------------------+-------+----------------------------------------------+
| 2  | Spacewalk Thoughts   | Orbit Bloom      | 3.82  | genre match (+2.0), mood match (+1.0),       |
|    |                      |                  |       | energy fit (+0.82)                           |
+----+----------------------+------------------+-------+----------------------------------------------+
| 3  | Music for Airports   | Brian Eno        | 2.98  | genre match (+2.0), energy fit (+0.98)       |
+----+----------------------+------------------+-------+----------------------------------------------+
Fun fact: nothing in the notes about ambient yet, so no fact to give.
```

This is the one I care about most. My corpus covers 29 genres and ambient is not one of them, on purpose, so I could keep testing this path. Nothing cleared the relevance threshold and the system just said so.

The recommendations above it are still good, which matters. The retriever failing does not drag the recommender down with it, they are separate steps. And if the system had guessed instead, the made up fact would have looked exactly as confident as the two real ones in the interactions above. Reading the output alone I would have no way to tell them apart. That is the whole reason I built the refusal in.

### Interaction 4: the evaluator

**Input**

```bash
python -m src.reliability
```

**Output**

```text
Reliability: 100 songs, 113 notes

[PASS] Determinism: 4 profiles scored 5 times each
[PASS] Golden snapshot: 4 baselines compared
[PASS] Genre accuracy at rank 1: 32/32 genres (100%) surface themselves at rank 1
[PASS] Catalog coverage: 82% of the catalog is reachable
[PASS] Perturbation robustness: total churn up to 67%, material churn 0% (limit 34%)
[PASS] Fun fact grounding: 0 ungrounded claims out of 100 songs

Report written to tests/results/reliability_report.md
```

Everything passes but two of these numbers are telling me something anyway.

Coverage is 82 percent, so 18 songs out of 100 never reach a top 3 slot no matter which genre profile I run. Songs like Toxic, Umbrella and Stairway to Heaven are in my catalog but effectively unreachable, because they are competing against other songs in the same genre that always beat them. When my catalog was 40 songs this number was 98 percent. Growing the catalog made the recommendations better and the coverage worse at the same time, which I did not see coming.

Total churn goes up to 67 percent but material churn is 0 percent. That means when I nudge the target energy by 0.02, two thirds of the top 3 can reorder, but not a single one of those swaps crosses a real score gap. It is all songs that were basically tied anyway. The system is not changing its mind, it is just shuffling near ties.

---

## Design Decisions

Why I built it this way, and what I gave up for each choice.

**Weights live in dictionaries instead of if statements.** My first version of `score_song` had a separate `if` block for genre, mood and energy. When I went to add eight more features that was going to turn into a wall of nearly identical code. So the four weight tables at the top of `recommender.py` hold the numbers and the function just loops over them. The trade off is that the code is a bit more abstract to read the first time, you have to look at the dictionary and the loop together to know what a feature does. What I get back is that adding a feature is one line in a dictionary and tuning is editing a number instead of editing logic.

**Genre is worth 2.0 and I kept it that way on purpose.** A genre match is worth double a mood match and roughly double a perfect energy match. This is a real bias and it is deliberate. My reasoning is the party one from the top of this README, if someone asks for jazz then handing them a pop song with the right mood is a worse answer than a jazz song with the wrong mood. The cost is that genre almost decides the winner by itself. The evaluator confirms this, genre accuracy is 100 percent across all 32 genres, which sounds great but really means the other ten features are mostly fighting over the ordering inside one genre.

**Only acousticness can subtract points.** Everything else on the 0 to 1 scale can only add. I made acousticness the exception because it is the one feature where being wrong is actively bad, if someone wants an acoustic track then a fully electronic one is not neutral, it is the opposite of what they asked for. The trade off is inconsistency, two features on the same 0 to 1 scale behave differently and you have to know which is which. I decided that was worth it for one feature but I would not want it for five.

**The scorer returns reasons, not just a number.** Every score comes back with the list of what contributed to it. This roughly doubles what `score_song` returns and made the table code more complicated. It is the best decision in the whole project. It is how I debug, it is how I judge whether a ranking is sensible, and it is the only reason I could tell that a song reaching the top 3 on energy alone was even happening.

**The RAG layer makes no API call.** Retrieval is TF-IDF in plain Python and generation fills a template with the retrieved text. I chose this over calling a model because it is free, it needs no key, it runs offline and it gives the same answer every time, which is what makes it testable at all. The honest trade off is that "generation" here is string formatting. A real model would write a nicer sentence. But the retrieval half, which is the part that actually decides what the system knows, is doing real work either way, and I would rather have a system I can fully test than a nicer sentence.

**The retriever is allowed to refuse.** If nothing clears the relevance threshold it says so instead of returning its best guess. The cost is fewer fun facts, ambient songs get nothing at all. I think that is the correct price. A retriever that always returns something is not distinguishable from a system making things up, and I cannot check every fact by eye.

**The retriever also has a topic filter on top of the similarity score.** A note only counts if it names the song's genre or the full artist name as a whole word, and notes matching more of those win before similarity is even considered. I added this after finding a real bug, which is written up in the testing section below. The trade off is recall, if I wrote a note that describes reggae perfectly but never uses the word "reggae", the filter throws it away. I would rather miss a good note than print a confident wrong one.

**Golden snapshots need a human to approve them.** The evaluator compares today's rankings to a saved baseline and fails on any difference. It only updates when I run it with `--update-golden`. This means every intentional weight change costs me an extra command. That friction is the point, it makes changing the output a decision instead of something that quietly happens.

**There are two ways into the scoring core and I kept both.** `main.py` uses plain dictionaries and the `Recommender` class uses `Song` and `UserProfile` objects. They both end up calling the same `score_song`. Keeping two is duplication, and there is now a test that fails if they ever disagree. I kept it because the dictionary path is what the CLI actually needs and the object path is what the starter tests were written against.

---

## Testing Summary

**The short version.** I measure reliability four ways. **Automated tests:** 128 pytest tests covering every function, plus a six check harness (`python -m src.reliability`) that measures the system as a whole and writes a report. **Confidence scoring:** the retriever reports how good its own match was, as a band and a raw number, so a weak fact does not look like a strong one. **Logging and error handling:** a missing notes corpus logs a warning and degrades to giving no fun facts, while a missing catalog logs an error and exits 1, because one of those is optional and the other is not. **Human evaluation:** every recommendation prints the reasons behind its score for me to sanity check, and the golden baseline only updates when I approve it by hand. Current state is 128 tests passing and 6/6 checks passing, with the honest caveat that 18 songs are unreachable and 3 genres have no fun fact.

The rest of this section is what that process actually turned up.

---

What worked, what did not, and what I actually learned from it.

### What worked

The 128 tests are split across nine files, one per unit, and that structure earned itself back. When I widened the tempo range, exactly one test failed and it told me which song and which range in the failure message. I did not have to go hunting.

Writing tests per branch rather than per function was the useful move. `score_song` has four different scoring rules inside it and my tests hit each one separately, including the boring cases like a preference the song does not have a column for. Those boring tests are the ones that caught things.

The evaluator turned out to do something the unit tests structurally cannot. Every unit test can pass while the system as a whole is behaving badly, because a unit test only knows about the thing in front of it. Coverage being 82 percent is not a broken function anywhere, it is a property of the whole catalog plus the whole scoring rule, and no single test was ever going to notice it.

Testing the tester mattered too. `test_reliability.py` deliberately corrupts a golden baseline and checks the drift check actually catches it. A check that silently passes no matter what is worse than no check, because it makes you feel covered.

### What did not work

**The grounding check passed while the system was wrong.** This is the big one. After I grew the catalog I found that Music for Airports by Brian Eno was returning a fun fact about AC/DC. The reason is that my Back in Black note mentions Brian Johnson, the singer, and my retriever scored on single words, so "brian" matched "brian". The fact was real, it was copied from my corpus word for word, and the grounding check was completely happy with it. It was still about the wrong band.

What I learned from this is that grounded and relevant are two different properties and I had only tested one of them. My check was asking "did this text come from the corpus" when the question that mattered was "is this text about this song". The fix was the topic filter described above, and there are now regression tests that specifically reproduce the Brian Eno case so it cannot come back.

**My first robustness metric was misleading.** I built a check that nudges the target energy by 0.02 and measures how much the top 3 reorders. It reported 67 percent churn and I read that as the system being fragile. Then I looked at the actual scores and the four songs involved were at 3.00, 2.99, 2.98 and 2.97. They were tied for any practical purpose and the order between them was always arbitrary.

So the number was real but the conclusion I drew from it was wrong. I rewrote the check to split churn in two, material churn only counts swaps that cross a score gap bigger than 0.05, and tie order churn counts the rest. Material churn is 0 percent. The system genuinely never changes its mind under a small nudge, it just has a lot of ties. The lesson is that a metric with no threshold attached to it will let you tell yourself whatever story you want.

**A feature was silently switching itself off.** My tempo range was declared as 60 to 220 bpm, except it was originally 60 to 200. When I added Master of Puppets at 212 bpm, that song's tempo landed outside the range, the closeness clamped to zero, and tempo just stopped contributing for it. Nothing crashed. Nothing warned me. The song still ranked, just on ten features instead of eleven.

This came out of a data test, not a code test. I added `tests/test_catalog.py` to check the data itself, that ids are unique, that no field failed to parse, that every value sits inside the range its scorer expects. On a 40 song catalog I could eyeball the CSV. At 100 songs I cannot, and a typo in one genre cell would just quietly never match anything.

**Growing the catalog made one number worse.** Coverage went from 98 percent at 40 songs to 82 percent at 100. More songs per genre means more songs that can never win their genre. This is not a bug and I am not going to fix it, but I would not have known it was happening without measuring it, and my instinct before running it was that more data would only help.

### What I learned

The thing that stuck with me is that testing an AI feature is not the same as testing a function. A function has a right answer and you assert on it. My retriever does not, it has answers that are more or less appropriate, and my grounding check was passing on an answer that was traceable and still wrong. Checking that output came from a legitimate source is a much weaker guarantee than it feels like when you write it.

The other thing is that the metrics were only useful once they had a line drawn next to them. "67 percent churn" told me nothing until I decided what counted as a real change. Before that I was just looking at a number and reacting to how big it felt.

---

## Experiments You Tried

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users
I ran all of these against the 40 song catalog with the example of a profile with Pop and Happy as a baseline. I lowered the general weight from 2.0 to 0.05 and all of the top results were from the pub genre. When I dropped it to 0.5 that led non pop songs to come up so the audio features like the mood could climb. So the general says how strict about genera the model can be. I added features like tempo violins popularity release decade into the scoring system.

---

## Limitations and Risks

Summarize some limitations of your recommender.

The limitations I can think of at the moment or from the tiny data set because the catalog of songs is small at the moment. I just have 40 songs with many genres that span across cultures. Some of the genres appear just once or twice. A user whose taste is one of those generous that appeared just once like classical, metal, a piano, soca would get just one single option and some type of filler for the other scores. When it comes to the lyrics or the language of the songs the model doesn't really have an understanding of the semantics. The wordiness feature just represents a number, the system doesn't actually assess what the song is about or what language it is in and this might be an important decision making factor for a user that's looking for a specific theme or a specific language. Some genres will dominate the ranking in the output just because there's a bias that I intentionnally left in the scoring logic.

**Update after growing the catalog to 100 songs.** Most of the above still holds but the numbers changed and one of them changed in a direction I did not expect. The one song per genre problem is mostly gone, every genre has at least two songs now and the test suite fails if too many singletons come back. What replaced it is the opposite problem. With more songs per genre, 18 of my 100 songs can never reach a top 3 slot for any genre profile, so coverage dropped from 98 percent to 82 percent. Adding data fixed the thin genres and created a new pile of unreachable songs at the same time.

The semantic limitation is completely unchanged. The system still has no idea what any song is about. The fun fact layer might look like it understands the music but it does not, it is matching words against notes I wrote by hand, and if I never wrote a note about a genre it has nothing to say. That is also a limitation of the corpus and not just the code, since everything the system can tell you about music is something a human typed into `data/music_notes.md` first.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

 Building this model made it more clear how a recommender turns data into predictions. It takes human preferences into numbers maybe even matrices to make a scoring system for each item on a list. There are fixed rules to classify them sort the songs. The intelligent part of the machine is the recipe for the algorithm. Basically how we choose to weight the features is what affects the models results directly. Adding reasons to each recommendations also change how I think about these systems. Because you can explain the thought process behind the result.



