# Translation Evaluation Tool

A Flask-based web dashboard for evaluating LLM translation quality using a **back-translation methodology**. Built as part of the MSc thesis empirical evaluation suite.

The tool computes 20+ automated NLP metrics by comparing an original source text against a back-translated version of the model's output, and supports an optional LLM-as-Judge evaluation via the Groq API.

---

## How It Works

The tool is built around the **round-trip back-translation** principle:

```
Original (EN) ──[Model]──▶ Translation (e.g. RU) ──[Model]──▶ Back-Translation (EN)
                                                                        │
                                                              Compare against Original
```

Since the back-translation is in the same language as the original, standard reference-based NLP metrics (BLEU, ROUGE, etc.) can be applied objectively — without requiring native-language human evaluators for each target language.

---

## Stack

- **Backend:** Python / Flask
- **Frontend:** Single-page HTML (`templates/index.html`) with Chart.js for visualization
- **LLM Judge:** Groq API (`llama-3.3-70b-versatile`), called directly from the browser via `fetch()` to bypass server-side SSL constraints
- **Dependencies:** Python standard library only — no NLTK, no scikit-learn, all metrics implemented from scratch

---

## Running the Tool

```bash
cd TranslationEvaluationTool
pip install flask
python app.py
```

Then open `http://localhost:5000` in your browser.

---

## API Endpoints

| Method | Endpoint              | Description                                                       |
|--------|-----------------------|-------------------------------------------------------------------|
| `GET`  | `/`                   | Serves the evaluation dashboard                                   |
| `POST` | `/api/evaluate`       | Computes all NLP metrics for a single original/back-translation pair |
| `POST` | `/api/composite`      | Computes composite scores, z-scores, and per-language-pair stats for a batch of entries |
| `POST` | `/api/llm-prompt`     | Builds and returns the structured LLM judge prompt (for browser-side Groq call) |
| `POST` | `/api/export`         | Exports all results as CSV or JSON                                |
| `GET`  | `/api/weight-profiles`| Returns the available composite score weight profiles            |

---

## Metrics

All metrics are implemented in pure Python in `app.py` with no external NLP libraries.

### N-gram Overlap

| Metric   | Description                                                              |
|----------|--------------------------------------------------------------------------|
| BLEU-1   | Unigram precision with brevity penalty                                   |
| BLEU-2   | Bigram precision with brevity penalty                                    |
| BLEU-4   | 4-gram precision with brevity penalty (primary BLEU metric in composite) |

The BLEU implementation uses a modified geometric mean over non-zero n-gram precisions and applies a brevity penalty.

### ROUGE

| Metric     | Description                                        |
|------------|----------------------------------------------------|
| ROUGE-1 F1 | Unigram recall/precision/F1                        |
| ROUGE-2 F1 | Bigram recall/precision/F1                         |
| ROUGE-L F1 | Longest Common Subsequence (space-optimised DP)    |

### Character-Level

| Metric | Description                                                              |
|--------|--------------------------------------------------------------------------|
| chrF   | Character n-gram F-score (n=1–6, β=2), averaged across all n-gram orders |

### Edit Distance

| Metric | Description                                                              |
|--------|--------------------------------------------------------------------------|
| WER    | Word Error Rate — Levenshtein distance over word tokens / reference length |
| CER    | Character Error Rate — Levenshtein distance over characters / reference length |

Both use a space-optimised O(n) rolling DP implementation.

### Semantic Similarity

| Metric         | Description                                                              |
|----------------|--------------------------------------------------------------------------|
| TF-IDF Cosine  | Cosine similarity of smoothed TF-IDF vectors over the shared vocabulary  |
| Jaccard        | Token-set Jaccard index                                                   |

### Content & Structural Overlap

| Metric                | Description                                                              |
|-----------------------|--------------------------------------------------------------------------|
| Content Word Overlap  | Stopword-filtered Jaccard over words with length > 3                     |
| Bigram Overlap        | Jaccard over bigram sets (measures structural/phrasing preservation)     |
| Sentence Overlap      | For each source sentence, finds the best-matching sentence in the back-translation by Jaccard, averaged |

### Length

| Metric       | Description                                                                    |
|--------------|--------------------------------------------------------------------------------|
| Length Ratio | Back-translation word count / original word count                              |
| Length Score | `max(0, 1 − |1 − length_ratio|)` — penalises both truncation and padding       |

### Lexical Diversity

| Metric                    | Description                                  |
|---------------------------|----------------------------------------------|
| Lex. Diversity (Original) | Type-Token Ratio (TTR) of the original text  |
| Lex. Diversity (BT)       | TTR of the back-translation                  |

---

## Composite Score

A single weighted composite score aggregates the key metrics into one quality signal. Three weight profiles are available:

| Profile          | Focus                                                             |
|------------------|-------------------------------------------------------------------|
| `balanced`       | Balanced across all metric categories (default)                  |
| `meaning_heavy`  | Heavily weights BLEU-4, ROUGE-L, chrF, and semantic similarity   |
| `fluency_heavy`  | Heavily weights WER, CER, and length score                        |

**Composite metric weights (balanced profile):**

| Metric              | Weight | Category            |
|---------------------|--------|---------------------|
| TF-IDF Cosine       | 0.12   | Semantic Similarity |
| WER                 | 0.13   | Fluency (inverted)  |
| ROUGE-L F1          | 0.10   | Meaning Preservation|
| chrF                | 0.10   | Meaning Preservation|
| BLEU-4              | 0.10   | Meaning Preservation|
| ROUGE-1 F1          | 0.08   | Meaning Preservation|
| Jaccard             | 0.08   | Semantic Similarity |
| Content Word Overlap| 0.08   | Semantic Similarity |
| Bigram Overlap      | 0.08   | Structural          |
| CER                 | 0.07   | Fluency (inverted)  |
| Length Score        | 0.06   | Structural          |

Negative-direction metrics (WER, CER) are inverted as `1 − value` before weighting.

The `/api/composite` endpoint also returns **z-scores** per metric across all submitted entries, and **per-language-pair statistics** (mean, std, min, max) for each metric.

---

## LLM Judge

When a Groq API key is provided in the UI, the tool invokes `llama-3.3-70b-versatile` as an expert judge. The judge receives:

- The original English text (A)
- The model's translation into the target language (B)
- The back-translation into English (C)

And scores the following 5 dimensions on a 0–10 scale:

| Dimension               | What It Measures                                                    |
|-------------------------|---------------------------------------------------------------------|
| Translation Accuracy    | Faithfulness of (B) to the meaning and nuance of (A)               |
| Fluency                 | Naturalness and readability of the back-translation (C)             |
| Meaning Preservation    | How much original meaning survived the full A→B→C round-trip        |
| Naturalness             | How natural (B) likely reads to a native target-language speaker    |
| Grammatical Correctness | Grammatical quality of the back-translation (C)                     |

Each dimension includes a score and a written justification. An overall score (0–10) and summary assessment are also returned.

The LLM judge prompt is built server-side via `/api/llm-prompt` and the actual Groq call is made from the browser to avoid server-side SSL issues.

---

## Export

Results can be exported from the UI in two formats:

- **CSV** — one row per model/language-pair entry, all metrics and LLM judge scores as columns
- **JSON** — full structured export including nested metric objects

---

## File Structure

```
TranslationEvaluationTool/
├── app.py              # Flask backend — all metrics, routes, composite scoring
└── templates/
    └── index.html      # Single-page evaluation dashboard with Chart.js
```