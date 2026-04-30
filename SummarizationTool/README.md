# Text Summarization Evaluation Tool

A Flask-based dashboard for evaluating and comparing AI-generated text summaries. Built as part of the MSc thesis:

> *Understanding and Comparing Generative AI Models: Capabilities, Domains, and Identifying the Best Models for Specific Use Cases*

All NLP metrics are implemented in **pure Python** with no external ML libraries — only the Python standard library is used for computation.

---

## Quick Start

```bash
pip install flask pdfplumber pypdf
python app.py
# Open http://localhost:5000
```

---

## Project Structure

```
SummarizationTool/
├── app.py               # Flask backend — all NLP metrics + API routes
├── requirements.txt     # pdfplumber, pypdf
└── templates/
    └── index.html       # Single-page dark dashboard UI
```

---

## Metrics

### Overlap Metrics (require a source text)

| Metric | Description |
|---|---|
| **ROUGE-1 / 2 / L** | Unigram, bigram, and LCS overlap (Precision, Recall, F1) |
| **BLEU** | Up to 4-gram precision with brevity penalty |
| **chrF** | Character n-gram F-score (β=2, up to 6-grams) |
| **TF-IDF Cosine** | Cosine similarity using TF-IDF weighted vectors |
| **Jaccard Similarity** | Token set intersection over union |
| **Content Word Overlap** | Jaccard restricted to non-stopword tokens |
| **Bigram Overlap** | Bigram set intersection over union |
| **Compression Ratio** | Summary tokens / source tokens |
| **Coverage Score** | Fraction of source content words appearing in summary |
| **Sentence-Level Overlap** | Fraction of summary sentences with a matching source sentence (Jaccard > 0.3) |
| **WER / CER vs Key Sentences** | Word / character error rate against top-TF extracted key sentences |
| **Novel Bigram Ratio** | Fraction of summary bigrams not present in source (abstractivity proxy) |
| **Abstractivity Score** | Same as novel bigram ratio but for trigrams |

### Intrinsic Metrics (source not required)

| Metric | Description |
|---|---|
| **Lexical Diversity** | Type-token ratio (unique tokens / total tokens) |
| **Information Density** | Content words / total tokens |
| **Redundancy** | Repeated trigram ratio within the summary |
| **Summary Word Count** | Token count of the summary |
| **Summary Sentence Count** | Sentence count (split on `.`, `!`, `?`) |

### Prompt Faithfulness Analysis

Auto-detects constraints from the prompt text and checks the summary against them. Detected signals include:

- **Bullet point requests** — detects presence and exact count, checks against `"exactly N bullet"` in the prompt
- **Numbered list requests** — checks for `1.` / `1)` style numbering
- **Word limits** — extracts limits like `"max 100 words"`, `"no more than 50 words"`, etc.
- **Sentence limits** — extracts `"exactly N sentences"` and checks sentence count
- **Section/heading requirements** — matches required section names against summary content
- **Brevity / detail requests** — soft scoring based on word count thresholds
- **Paragraph format** — checks for double-newline-separated paragraphs
- **Negative constraints** — extracts `"do not …"` clauses for reference

Returns an `overall_adherence` score (0.0–1.0) averaged across all detected constraints.

---

## LLM-as-Judge

The tool builds a structured evaluation prompt and the browser calls the LLM API directly (no API keys stored server-side):

- **Groq API** (`llama-3.3-70b-versatile`) — primary judge
- **Gemini API** (`gemini-2.0-flash`) — secondary judge

Evaluation dimensions scored 0–10:

1. Factual Accuracy
2. Completeness
3. Conciseness
4. Coherence & Fluency
5. Prompt Faithfulness
6. Overall

The Flask backend builds the prompt via `/api/llm-prompt`; the actual API call is made browser-side via `fetch()`.

---

## PDF Upload

The `/api/extract-pdf` endpoint extracts text from uploaded PDFs using a fallback chain:

1. `pdftotext` (poppler-utils) — best layout preservation
2. `pypdf` — pure-Python fallback
3. `pdfplumber` — last resort

---

## Analytics & Visualization

| Feature | Description |
|---|---|
| **Composite Score** | Weighted sum across metrics with adjustable sliders |
| **Presets** | Balanced / Coverage-Heavy / Conciseness-Heavy weight profiles |
| **Z-score normalization** | Standardizes each metric across all entries for fair comparison |
| **Radar chart** | Per-model metric profile visualization |
| **Bar chart** | Composite score comparison across models |
| **Heatmap** | Models × metrics score matrix |
| **Leaderboard** | Ranked table sorted by composite score |
| **Cross-model statistics** | Mean, std dev, min, max per metric |
| **Entry grouping** | Filter entries by prompt/task ID |
| **CSV / JSON export** | Full export of all metric values |

### Composite Score Presets

| Preset | Focus |
|---|---|
| **Balanced** | Equal weight across ROUGE, coverage, lexical quality, and prompt adherence |
| **Coverage-Heavy** | Emphasizes TF-IDF cosine and coverage; rewards completeness |
| **Conciseness-Heavy** | Rewards low compression ratio, high information density, low redundancy |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the dashboard UI |
| `POST` | `/api/evaluate` | Evaluates a single (prompt, source, summary) entry |
| `POST` | `/api/analytics` | Computes composite scores, Z-scores, leaderboard for a batch |
| `POST` | `/api/llm-prompt` | Builds and returns the LLM judge prompt |
| `POST` | `/api/extract-pdf` | Extracts text from an uploaded PDF |
| `POST` | `/api/export` | Exports entries as CSV or JSON |