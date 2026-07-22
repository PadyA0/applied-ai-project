# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

In summary, this program is a music recommender that uses rule to prioritize the best option for the user.

## How The System Works

Explain your design in plain language.
My design is a simple approach at making a music recommender. Music platforms in the real world tend to combine core-based filtering and content-based filtering to give the best option to the user. This program is a modest, but effective way to duplicate a more realistic platform like Youtube Music. My system will be more biased towards the genre and tempo though. In my experience, playing an upbeat hip hop song with sad themes to follow up another upbeat hip hop song that has happy themes at a party, it makes for a less brutal disruption to the dance moves and the state of mind.

Some prompts to answer:

- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo
Each song presents features like the genre, mood, tempo, and energy that help categorize it in an algorithm.

- What information does your `UserProfile` store
This stores information about the preferences input by the user. Maybe the listener is a pop fan or maybe they want a energyzed beat for the gym. That information is collected in the UserProfile to tailor the recommendations to that. 

- How does your `Recommender` compute a score for each song
The recommender computes a weighted final numerical value to both score and rank the songs in the list of recommendations. There are two different formulas at play that first measure how much of a good match a song is, then a decision maker for the actual song.
The core ide is that each song uses the single numerical score by adding different components, the song attributes, multiplied by a weight. 

- How do you choose which songs to recommend

You can include a simple diagram or bullet list if helpful.

My recommender, while using a weighted score to combine core-based filtering and content-based filtering, might prioritize genre and tempo. A genre match will be a stronger signal than a mood match.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.
I added more tests at the rate of at least 1 test per method in recommender.py. I also wanted to cover edge cases .

---

## Sample Recommendation Output

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:
Loaded songs: 40

================================================
  TOP RECOMMENDATIONS
  for profile:
    - genre: pop
    - mood: happy
    - energy: 0.8
    - valence: 0.85
    - danceability: 0.8
    - acousticness: 0.15
    - instrumental: 0.05
    - wordiness: 0.1
    - tempo_bpm: 120
    - popularity: 80
    - release_decade: 2020
================================================

+----+----------------------+------------------+-------+----------------------------------------------+
| #  | Title                | Artist           | Score | Reasons                                      |
+====+======================+==================+=======+==============================================+
| 1  | Sunrise City         | Neon Echo        | 7.72  | genre match (+2.0), mood match (+1.0),       |
|    |                      |                  |       | energy fit (+0.98), valence fit (+0.59),     |
|    |                      |                  |       | danceability fit (+0.59), instrumental fit   |
|    |                      |                  |       | (+0.40), wordiness fit (+0.28), acousticness |
|    |                      |                  |       | fit (+0.47), tempo_bpm fit (+0.49),          |
|    |                      |                  |       | popularity fit (+0.40), release_decade fit   |
|    |                      |                  |       | (+0.50)                                      |
+----+----------------------+------------------+-------+----------------------------------------------+
| 2  | Billie Jean          | Michael Jackson  | 6.57  | genre match (+2.0), energy fit (+0.99),      |
|    |                      |                  |       | valence fit (+0.59), danceability fit        |
|    |                      |                  |       | (+0.53), instrumental fit (+0.39), wordiness |
|    |                      |                  |       | fit (+0.30), acousticness fit (+0.48),       |
|    |                      |                  |       | tempo_bpm fit (+0.49), popularity fit        |
|    |                      |                  |       | (+0.45), release_decade fit (+0.35)          |
+----+----------------------+------------------+-------+----------------------------------------------+
| 3  | Gym Hero             | Max Pulse        | 6.42  | genre match (+2.0), energy fit (+0.87),      |
|    |                      |                  |       | valence fit (+0.55), danceability fit        |
|    |                      |                  |       | (+0.55), instrumental fit (+0.40), wordiness |
|    |                      |                  |       | fit (+0.30), acousticness fit (+0.40),       |
|    |                      |                  |       | tempo_bpm fit (+0.46), popularity fit        |
|    |                      |                  |       | (+0.39), release_decade fit (+0.50)          |
+----+----------------------+------------------+-------+----------------------------------------------+
| 4  | Shape of You         | Ed Sheeran       | 6.03  | genre match (+2.0), energy fit (+0.85),      |
|    |                      |                  |       | valence fit (+0.55), danceability fit        |
|    |                      |                  |       | (+0.58), instrumental fit (+0.38), wordiness |
|    |                      |                  |       | fit (+0.28), acousticness fit (+0.07),       |
|    |                      |                  |       | tempo_bpm fit (+0.41), popularity fit        |
|    |                      |                  |       | (+0.44), release_decade fit (+0.46)          |
+----+----------------------+------------------+-------+----------------------------------------------+
| 5  | Get Lucky            | Daft Punk        | 5.66  | mood match (+1.0), energy fit (+0.99),       |
|    |                      |                  |       | valence fit (+0.59), danceability fit        |
|    |                      |                  |       | (+0.59), instrumental fit (+0.38), wordiness |
|    |                      |                  |       | fit (+0.28), acousticness fit (+0.39),       |
|    |                      |                  |       | tempo_bpm fit (+0.49), popularity fit        |
|    |                      |                  |       | (+0.49), release_decade fit (+0.46)          |
+----+----------------------+------------------+-------+----------------------------------------------+
(venv) PS C:\Users\padya\vibecoding\musicrecommendersimulation> python -m src.main 
Loaded songs: 40

==============================================================================
  Chill Indie  (indie pop / melancholic / low energy)
  profile: genre=indie pop, mood=melancholic, energy=0.2
==============================================================================
+----+----------------------+------------------+-------+----------------------------------------------+
| #  | Title                | Artist           | Score | Reasons                                      |
+====+======================+==================+=======+==============================================+
| 1  | Rooftop Lights       | Indigo Parade    | 2.44  | genre match (+2.0), energy fit (+0.44)       |
+----+----------------------+------------------+-------+----------------------------------------------+
| 2  | Nothing Else Matters | Metallica        | 1.65  | mood match (+1.0), energy fit (+0.65)        |
+----+----------------------+------------------+-------+----------------------------------------------+
| 3  | Spacewalk Thoughts   | Orbit Bloom      | 0.92  | energy fit (+0.92)                           |
+----+----------------------+------------------+-------+----------------------------------------------+

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
| 2  | Billie Jean          | Michael Jackson  | 2.99  | genre match (+2.0), energy fit (+0.99)       |
+----+----------------------+------------------+-------+----------------------------------------------+
| 3  | Gym Hero             | Max Pulse        | 2.87  | genre match (+2.0), energy fit (+0.87)       |
+----+----------------------+------------------+-------+----------------------------------------------+

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->
![screenshot of main output](image.png)
![screenshot with 3 different user profile in output](image-1.png)
---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users
I ran all of these against the 40 song catalog with the example of a profile with Pop and Happy as a baseline. I lowered the general weight from 2.0 to 0.05 and all of the top results were from the pub genre. When I dropped it to 0.5 that led non pop songs to come up so the audio features like the mood could climb. So the general says how strict about genera the model can be. I added features like tempo violins popularity release decade into the scoring system.

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

The limitations I can think of at the moment or from the tiny data set because the catalog of songs is small at the moment. I just have 40 songs with many genres that span across cultures. Some of the genres appear just once or twice. A user whose taste is one of those generous that appeared just once like classical, metal, a piano, soca would get just one single option and some type of filler for the other scores. When it comes to the lyrics or the language of the songs the model doesn't really have an understanding of the semantics. The wordiness feature just represents a number, the system doesn't actually assess what the song is about or what language it is in and this might be an important decision making factor for a user that's looking for a specific theme or a specific language. Some genres will dominate the ranking in the output just because there's a bias that I intentionnally left in the scoring logic.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

 Building this model made it more clear how a recommender turns data into predictions. It takes human preferences into numbers maybe even matrices to make a scoring system for each item on a list. There are fixed rules to classify them sort the songs. The intelligent part of the machine is the recipe for the algorithm. Basically how we choose to weight the features is what affects the models results directly. Adding reasons to each recommendations also change how I think about these systems. Because you can explain the thought process behind the result.



