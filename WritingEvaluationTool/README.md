# Writing & Communication Evaluation Tool

**MSc Thesis**: *Understanding and Comparing Generative AI Models: Capabilities, Domains, and Identifying the Best Models for Specific Use Cases*

A Flask-based evaluation dashboard for benchmarking AI model outputs on structured writing and communication tasks. Built as part of the thesis empirical evaluation framework, this tool quantifies writing quality across 8 metric categories using only standard scientific Python libraries — no external NLP dependencies required.

---

## Purpose

This tool was built to evaluate model responses to the 3 Writing & Communication prompts in the thesis. Each prompt contains a set of explicit constraints (word limits, forbidden words, required phrases, structural rules), making **constraint adherence** measurable alongside standard prose quality metrics. The tool also integrates an optional LLM-as-Judge layer for qualitative assessment.

---

## Features

### 3-Step Wizard Interface

The UI guides users through a consistent workflow:

1. **Setup** — Paste the writing prompt (with constraints) and optional context/reference material
2. **Model Responses** — Add model names and paste their outputs
3. **Results** — View leaderboard, charts, per-category breakdowns, constraint adherence detail, and optionally run the LLM judge

### Automated Metrics — 8 Categories, 60+ Individual Metrics

All metrics are computed from scratch in `metrics_engine.py` using `numpy`, `scipy`, and `scikit-learn` only.

#### 1. Content Quality (weight: 20%)

Measures how well the response addresses the prompt's informational content.

| Metric | Description |
|--------|-------------|
| Context Similarity | TF-IDF cosine similarity between response and prompt+context |
| Information Coverage | Fraction of key content-bearing terms from the prompt found in the response |
| Entity Retention | Proportion of named entities/capitalized terms from the prompt retained in the response |
| Relevance Score | Composite: 50% context similarity + 30% information coverage + 20% entity retention |

#### 2. Constraint Adherence (weight: 20%)

Auto-parsed from the prompt text. Checks each identified constraint and scores pass/fail with partial credit where applicable. See the **Constraint Auto-Parser** section below for the full list of supported constraint types.

#### 3. Tone & Sentiment (weight: 15%)

Lexicon-based analysis using built-in word sets (no external sentiment libraries).

| Metric | Description |
|--------|-------------|
| Sentiment Polarity | Ratio of positive to negative sentiment words, mapped to 0–100 |
| Subjectivity | Proportion of subjective/opinion words relative to total tokens |
| Formality Score | Balance of formal indicators vs. informal indicators and contractions |
| Tone Consistency | Variance of per-sentence sentiment polarity (low variance = high consistency) |
| Emotional Range | Density of emotionally charged words (positive + negative) per total words |

Category score: `0.3 × formality + 0.3 × tone_consistency + 0.2 × sentiment_polarity + 0.2 × (1 − subjectivity)`

#### 4. Readability (weight: 15%)

Standard readability formulae, all implemented from scratch.

| Metric | Formula |
|--------|---------|
| Flesch Reading Ease | `206.835 − 1.015 × ASL − 84.6 × ASW` (higher = easier) |
| Flesch-Kincaid Grade | `0.39 × ASL + 11.8 × ASW − 15.59` |
| Gunning Fog Index | `0.4 × (ASL + 100 × complex_word_ratio)` |
| Coleman-Liau Index | `0.0588 × L − 0.296 × S − 15.8` |
| Automated Readability Index | `4.71 × (chars/words) + 0.5 × ASL − 21.43` |
| SMOG Grade | `1.043 × √(complex_words × 30/sentences) + 3.1291` |
| Readability Score (0–100) | Penalises deviation from Flesch target of 60 (optimal for professional writing) |

*ASL = average sentence length, ASW = average syllables per word. Syllable counting uses a rule-based approach handling common suffixes, silent-e, and special endings.*

#### 5. Lexical Analysis (weight: 10%)

Vocabulary richness and sophistication metrics.

| Metric | Description |
|--------|-------------|
| Type-Token Ratio (TTR) | Unique words / total words |
| Root TTR (Guiraud's Index) | Unique words / √(total words) — more stable across text lengths |
| Hapax Legomena Ratio | Words appearing exactly once / total unique words |
| Yule's K | Statistical vocabulary repetitiveness measure (lower = richer) |
| Vocabulary Richness | Derived from Yule's K, normalised to 0–100 |
| Lexical Sophistication | Proportion of words with 3+ syllables and 7+ characters |
| Information Density | Proportion of content-bearing words (from a 200-word verb/noun list) |
| Brunet's W | Alternative vocabulary richness index |
| Honoré's R | Vocabulary richness based on hapax ratio |
| Average Word Length | Mean character length of all tokens |

#### 6. Structural Analysis (weight: 10%)

Counts and distributional statistics on document structure.

| Metric | Description |
|--------|-------------|
| Word / Sentence / Paragraph Count | Raw counts using custom tokenisers |
| Character Count (with/without spaces) | Raw character counts |
| Avg / Min / Max Sentence Length | Per-sentence word count statistics |
| Sentence Length Std Dev & Variance | Dispersion of sentence lengths |
| Sentence Length CV | Coefficient of variation; ~40% CV treated as stylistically optimal |
| Avg Paragraph Length & Std Dev | Per-paragraph word count statistics |
| Question / Exclamation / Declarative Ratio | Proportion of each sentence type |
| Sentence Type Variety | How many of the 3 sentence types appear (score: 33/67/100) |
| Words per Paragraph | Total words divided by paragraph count |

Category score: `0.5 × sentence_type_variety + 0.5 × CV_score` where CV_score penalises deviation from 40% CV.

#### 7. Coherence & Flow (weight: 5%)

Measures logical progression and topical continuity.

| Metric | Description |
|--------|-------------|
| Avg Inter-Sentence Similarity | Mean TF-IDF cosine similarity between consecutive sentence pairs |
| Min Inter-Sentence Similarity | Lowest consecutive-pair similarity (flags topic jumps) |
| Coherence Variance | Variance of inter-sentence similarities |
| Transition Word Density | Count of transition words found / number of sentences |
| Global Coherence | Mean pairwise TF-IDF cosine similarity across all sentence combinations |
| Flow Score | `0.4 × avg_inter_sentence + 0.3 × transition_density_scaled + 0.3 × global_coherence` |

#### 8. Redundancy (weight: 5%)

Detects repetitiveness at word and sentence level.

| Metric | Description |
|--------|-------------|
| Bigram Repetition Rate | Proportion of repeated bigrams relative to total bigrams |
| Trigram Repetition Rate | Proportion of repeated trigrams relative to total trigrams |
| Content Word Repetition | Proportion of repeated content words (stop words excluded) |
| Max Sentence Similarity | Highest TF-IDF cosine similarity between any two sentences |
| Avg Cross-Sentence Similarity | Mean pairwise similarity across all sentence pairs |
| Redundancy Score | `100 − (bigram_rate × 2 + trigram_rate × 3 + content_word_rep × 0.5)` |

---

### Constraint Auto-Parser (`constraint_parser.py`)

Reads the writing prompt using regex and NLP heuristics and automatically extracts constraints before evaluation. Supported constraint types:

| Constraint Type | Example Prompt Text | What is Checked |
|-----------------|---------------------|-----------------|
| `word_count_range` | "Body must be 110–130 words" | Actual word count vs. range; partial credit for near-misses |
| `word_count_max` / `word_count_min` | "Max 200 words" | Hard boundary check |
| `sentence_count_exact` | "Exactly 10 sentences" | Sentence count vs. target |
| `sentence_count_range` | "8–12 sentences" | Range check |
| `paragraph_count_exact` | "Use exactly 3 paragraphs" | Paragraph count (smart paragraph detection filters greetings/closings) |
| `required_phrase` | `"must include: 'by 5 PM today'"` | Case-insensitive substring search |
| `forbidden_word` | "Do not use the words: urgent, ASAP" | Whole-word regex search |
| `required_heading` | "Use these headings: Summary, Impact" | Heading found as formatted line or inline text |
| `no_bullet_points` | "No bullet points" | Detects `- `, `• `, `* `, and `1.` list patterns |
| `requires_subject_line` | "Include a subject line" | Detects `Subject:` / `Re:` prefix |
| `subject_line_max_words` | "Subject line (max 8 words)" | Counts words after the `Subject:` prefix |
| `tone_requirement` | "Keep tone professional and non-accusatory" | Lexicon-based tone scoring (professional, formal, neutral, friendly, persuasive, non-accusatory) |
| `technical_terms_required` | "Include exactly two technical terms from: {regression, QA, patch}" | Counts how many list terms appear in the response |
| `technical_terms_forbidden` | "Include zero technical terms from that list" | Verifies none of the listed terms appear |
| `item_count` | "Exactly 3 actions" | Counts semicolon-separated items as a proxy |
| `sentences_per_section` | "Each heading must have exactly 2 sentences" | Splits by section headers and counts sentences per section |
| `required_email` | "Contact must include support@example.com" | Exact email string search |
| `no_apologies` | "Do not include apologies" | Detects *sorry*, *apologise*, *regret*, *inconvenience* |
| `semicolon_separated` | "Separated by semicolons" | Checks for `;` presence |
| `requires_next_step` | "Include a clear next step" | Regex patterns for action-oriented phrases |
| `confidence_statement` | `"We are confident…" or equivalent` | Detects "we are confident", "rest assured", "we believe", etc. |
| `output_format` | "Output format must be: A) ... B) ..." | Checks for `A)` and `B)` labels |

Each constraint is scored 0–100 (100 = fully met, with partial credit for near-misses on numeric constraints). The **Constraint Adherence category score** is the arithmetic mean of all individual constraint scores.

---

### Composite Score & Weighting

```
Composite = Σ (category_score × weight)

Default weights:
  Content Quality      20%
  Constraint Adherence 20%
  Tone & Sentiment     15%
  Readability          15%
  Lexical Analysis     10%
  Structural           10%
  Coherence & Flow      5%
  Redundancy            5%
```

Weights are adjustable via sliders in the Results UI before computing the final composite.

---

### Cross-Model Analysis

When multiple models are loaded, the tool computes:

- **Leaderboard** — ranked by composite score
- **Radar chart** — 8-axis category comparison
- **Grouped bar chart** — category scores side by side
- **Z-score heatmap** — normalised scores showing which model leads/lags in each category relative to the group mean
- **Cross-model statistics table** — mean, std, min, max, range, and median per category

---

### LLM-as-Judge (Optional)

- Provider: Groq API (free tier), model `llama-3.3-70b-versatile`
- API key entered directly in the browser — no server-side key storage
- Evaluates 8 qualitative dimensions: Tone Accuracy, Constraint Following, Audience Appropriateness, Persuasiveness/Effectiveness, Grammar & Polish, Clarity & Conciseness, Structure & Organisation, Creativity & Naturalness
- Each dimension scored 1–10 with written justification
- A final score out of 100 is produced per model
- Can be run for a single model or all models in batch
- Results are displayed alongside the automated metrics and can be exported

---

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` in your browser.

---

## Project Structure

```
WritingEvaluationTool/
├── app.py                 # Flask routes and API endpoints
├── metrics_engine.py      # All 60+ NLP metrics (8 categories), composite scoring, z-scores
├── constraint_parser.py   # Prompt parser (extract constraints) + constraint evaluator
├── requirements.txt       # Python dependencies
├── README.md
└── templates/
    └── index.html         # Dark-themed 3-step SPA dashboard (Chart.js, vanilla JS)
```

---

## Dependencies

```
flask
numpy
scipy
scikit-learn
```

All NLP logic — tokenisation, syllable counting, readability formulae, lexical diversity measures, sentiment lexicons, coherence metrics — is implemented from scratch. No NLTK, spaCy, TextBlob, or other NLP libraries are required.

---

## Export

Results can be exported from the Results step as:

- **CSV** — one row per model, columns for all category scores and composite
- **JSON** — full nested structure including all individual metric values, constraint check details, and LLM judge scores (if run)