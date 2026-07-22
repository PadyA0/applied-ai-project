# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I told it to implement a penalty when one of the features is too bad of a match. Like the acousticness, if the match is too weak the model loses some points.

**Prompts used:**

say you are an AI trainer that wants to strengthen the recommender. Implement a penalty for a feature like acousticness if the match is too bad.

**What did the agent generate or change?**

The agent edited the recommender.py file by adding 11 lines.

**What did you verify or fix manually?**

the output would have some unicode Claude symbols in my terminal. That tends to break the workflow, so I went in and made it ASCII instead.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

I use the strategy pattern. I used something that's data driven so instead of having a Big L chain, I made sure that each feature could be scored with its own strategy.

**How did AI help you brainstorm or implement it?**

Originally score song the method was hard coded with 3 features namely general mood and energy with separate if blocks. When I asked to add about eight more features and later to make acousticness penalize bad matches, The assistant suggested pulling the weights out into lookup tables and looping over them, so each feature type follows one shared rule. So that conversation turned all of the if statements into just one strategy approach. 

**How does the pattern appear in your final code?**

We can see that in the recommender.py. There are four weight config dictionaries, and the score song function loops over each one to apply the matching scoring rule. Adding acoustic necks to penalize the unit weight instead of unit weight in my code is what makes a bad acoustic match subtract point off of the score. 
