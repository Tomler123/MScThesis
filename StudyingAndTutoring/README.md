# Studying & Tutoring - Prompts

This folder contains evaluation prompts for the **Studying and Tutoring** domain.
The prompts focus on:
- **Correctness** (accurate explanations and computations)
- **Explanation quality** (clear intuition + step-by-step reasoning)
- **Guidance** (good teaching structure, helpful practice)
- **Level suitability** (matches the stated student level)

## Files
- `prompt1.txt` - Probability & Statistics tutoring (Bayes’ rule with numeric example + practice)
- `prompt2.txt` - ML Basics tutoring (confusion matrix, precision/recall/F1 + practice)
- `prompt3.txt` - Discrete Math / Logic tutoring (proof by contradiction + mistake diagnosis + practice)

## Prompt descriptions

### Prompt 1 - Probability & Statistics (Bayes’ Rule)
**Goal:** Evaluate tutoring ability on conditional probability and Bayes’ rule with a self-contained numeric task.

**What it tests**
- Correct application of Bayes’ theorem
- Clear intuition for conditional probability
- Step-by-step computation with correct intermediate steps
- Quality and relevance of practice questions + solutions
- Beginner-friendly explanations

**Expected strong output characteristics**
- Intuition explained simply and correctly
- Correct computation of \(P(\text{disease} \mid \text{positive})\)
- Practice questions similar difficulty, with full solutions

---

### Prompt 2 - ML Basics (Confusion Matrix Metrics)
**Goal:** Evaluate teaching of precision, recall, and F1 plus metric choice reasoning.

**What it tests**
- Correct calculation of precision, recall, and F1 from TP/FP/FN/TN
- Explanation quality (precision vs recall distinction)
- Reasoning about metric choice when false negatives are costly
- Quality of practice questions (one conceptual, one numerical) + solutions
- Intermediate-level communication (not too basic, not too advanced)

**Expected strong output characteristics**
- Accurate metric calculations with shown steps
- Clear justification for optimizing recall (or equivalent) when FN is worse
- Practice items aligned to the topic with correct solutions

---

### Prompt 3 - Discrete Math / Logic (Contradiction + Mistake Diagnosis)
**Goal:** Evaluate proof teaching and the ability to correct student misconceptions.

**What it tests**
- Correct explanation of proof by contradiction (and/or contrapositive reasoning)
- Correct proof of: “If \(n^2\) is even, then \(n\) is even.”
- Diagnostic tutoring skill: identifying exactly 3 mistakes in a flawed proof
- Providing corrected reasoning and a practice problem with solution

**Expected strong output characteristics**
- Logically valid proof with clear steps
- Exactly 3 distinct mistakes identified and explained
- A relevant practice statement + correct proof