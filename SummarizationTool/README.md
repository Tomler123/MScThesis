# Text Summarization Evaluation Tool — Setup

## Quick Start
```bash
pip install flask
python app.py
# Open http://localhost:5000
```

## Structure
```
text-summarization-eval/
├── app.py                  # Flask backend (all NLP metrics in pure Python)
└── templates/
    └── index.html          # Single Jinja2 template (dark dashboard UI)
```

## Features Implemented

### NLP Metrics (pure Python, no external libraries)
- ROUGE-1/2/L (Precision, Recall, F1)
- BLEU (up to 4-gram with brevity penalty)
- chrF (character n-gram F-score, β=2)
- TF-IDF Cosine Similarity
- Jaccard Similarity
- Content Word Overlap
- Bigram Overlap
- Compression Ratio
- Coverage Score
- Redundancy Score (repeated n-grams)
- Sentence-Level Overlap
- WER/CER vs key sentences
- Lexical Diversity (TTR)
- Information Density (content words / total)
- Novel Bigram Ratio
- Abstractivity Score

### Prompt Faithfulness Analysis
Auto-detects from the prompt text:
- Bullet point requests (and exact count)
- Word/sentence limits
- Section/heading requirements
- Brevity/detail requests
- Paragraph format requests
- Negative constraints ("do not...")

### LLM-as-Judge
- Groq API (llama-3.3-70b-versatile) — browser-side fetch
- Gemini API (gemini-2.0-flash) — browser-side fetch
- Flask only builds the prompt via `/api/llm-prompt`
- Scores: Factual Accuracy, Completeness, Conciseness, Coherence, Prompt Faithfulness, Overall (0-10)

### Analytics & Visualization
- Z-score normalization across entries
- Composite weighted scores with adjustable sliders
- 3 presets: Balanced, Coverage-Heavy, Conciseness-Heavy
- Radar charts (per model profile)
- Bar chart (composite scores)
- Heatmap (models × metrics)
- Leaderboard (ranked by composite)
- Cross-model statistics (mean, std, min, max)
- CSV and JSON export

### Grouping
- Entries grouped by prompt/task ID
- Filter by group in Entries, Analytics panels

## Prompts Included
The 4 prompt files are pre-loaded as quick-load buttons:
1. **P1**: Short text summarization (3 bullet points)
2. **P2**: Research paper PDF summarization (InstructGPT paper)
3. **P3**: Lecture notes PDF summarization
4. **P4**: Webpage summarization (Python 3.14 whatsnew)
