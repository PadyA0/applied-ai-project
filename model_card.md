# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  
Sawndz 1.0
---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
The model recommends song to a user. It helps them make a choice according to their preference input.

- What assumptions does it make about the user  
It assumes the user has specific taste that their mood can influence.
- Is this for real users or classroom exploration  
At this stage, the model is for classroom exploration because of its limited dataset. A real model would thousands more data points to learn from and avoid overtraining.

---

## 3. How the Model Works  

Explain your scoring approach in simple language.  

Prompts:  

- What features of each song are used (genre, energy, mood, etc.)  
The recommender looks at three things about each song its genre, its mood, and its energy.
- What user preferences are considered
 The user describes their taste as a small profile but their favorite genre, their favorite moon, and a target energy level .  
- How does the model turn those into a score  
To turn all of that into a score, the model adds points + two if the songs genre matches the user's favorite genre. + one if the song mood matches the user's favorite mood. + one for energy target reaching.
- What changes did you make from the starter logic  
The starter code returned the first few songs with placeholder scores and no real logic. I implemented the actual CSV loading, the algorithm recipe, and the ranking. I made a general mood matching case insensitive code .

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog 
The catalog contains 20 songs as of now. 
- What genres or moods are represented  
The genres represented span across the globe: afrobeats, lofi, jazz, reggeaton etc.
- Did you add or remove data  
I mostly added data like more songs and attributes.
- Are there parts of musical taste missing in the dataset  
I can think of few like loudness of a song, but this could be tied to other features that are already present.
---

## 5. Strengths  

Where does your system seem to work well  
It gives the most intuitive results when a user's genre and mood both exist in the catalog For a, happy, 0.8 energy level profile, sunrise C scored 3.98 and landed on top . This is exactly what we expected because it matches all the three signals . Genre dominates the scores.

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
Some features I added into the CSV file were not considered in the score so there's tempo beats per minute, densibility, instrumental, worthiness period two songs that feel very different can score exactly the same. 
- Genres or moods that are underrepresented  
Generals that are underrepresented in my list are some fusion ones like if the user wants something indeed they cannot get any indie pop recommendation so there's an exact string matching going on in my model. 
- Cases where the system overfits to one preference  
Genera is worth twice as much as mood and up to twice as much as energy, so as a general match almost guarantees a top shot even if mood and energy are wrong so I could fix that.
- Ways the scoring might unintentionally favor some users  
There's a catalog bias because the data set is so small and unevenly spread. For example many genres appear just once. So that doesn't let the model really learn from the distribution.
---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 
I mostly check behavior by running the main code and then I read the ranked output with the reasons it showed, since the reason make it easy to see why each song was recommended. What I was looking for was a songs that match all specificities. What surprised me about the model is how song that matched neither genre or mood could still appear in the top five just because the energy level reached the target.

No need for numeric metrics unless you created some.

---

## 8. Future Work  

Ideas for how you would improve the model next.  
For future work I would add features that I tried to put in the songs dot CSV file like tempo dance ability and acousticness the same way that energy is working so the closer the recommendation is to the target the better the reward for the model. I would also put some fusion generas that could work as a partial match like Alt Indie could count as Indie. 

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  
Building this made me realize how much of a recommender is just turning preferences into numbers and sorting them using a magic scoring rule basically. I did not expect how much the catalog could shape the result with only 20 songs and many genres appearing more than once and some appearing just one time, the model's fairness was a little bit off . 

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
