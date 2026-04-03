# Writing & Communication — GenAI Evaluation Tool

**MSc Thesis**: *Understanding and Comparing Generative AI Models: Capabilities, Domains, and Identifying the Best Models for Specific Use Cases*

A Flask-based evaluation tool for benchmarking AI model outputs on writing and communication tasks. This tool complements the Text Summarization evaluation tool by focusing on structured writing quality assessment with constraint adherence checking.

## Features

### Automated Evaluation (30+ Metrics)
- **Content Quality**: TF-IDF cosine similarity, information coverage, entity retention, relevance scoring
- **Tone & Sentiment**: Lexicon-based sentiment polarity, subjectivity, formality score, tone consistency, emotional range
- **Readability**: Flesch Reading Ease, Flesch-Kincaid Grade, Gunning Fog Index, Coleman-Liau Index, Automated Readability Index, SMOG Grade
- **Lexical Analysis**: Type-Token Ratio, Root TTR (Guiraud's), Hapax Legomena Ratio, Yule's K, Brunet's W, Honoré's R, lexical sophistication, information density
- **Structural Analysis**: Sentence/paragraph/word counts, sentence length variance, coefficient of variation, sentence type variety
- **Coherence & Flow**: Inter-sentence TF-IDF similarity, transition word density, global coherence
- **Redundancy**: Bigram/trigram repetition rates, cross-sentence similarity, content word repetition
- **Constraint Adherence**: Auto-parsed from prompt — word/sentence limits, required sections, tone requirements, formatting rules, forbidden words, technical term counts

### Constraint Auto-Parser
Reads your writing prompt and automatically extracts constraints including:
- Word/sentence/paragraph count limits and ranges
- Required and forbidden phrases/words
- Required headings/sections
- Tone requirements (professional, neutral, formal, etc.)
- Technical term constraints
- Format rules (no bullet points, subject lines, semicolons)
- Required elements (next steps, confidence statements, emails)

### LLM-as-Judge (Optional)
- Groq API integration (free tier) with Llama 3.3 70B Versatile
- Evaluates: tone accuracy, constraint following, audience fit, persuasiveness, grammar, clarity, structure, creativity
- Single-model or batch evaluation
- Separate from automated metrics — triggered manually

### Visualization & Export
- Dark-themed professional dashboard
- 3-step wizard: Setup → Model Responses → Results
- Radar chart, bar chart, grouped bar chart
- Z-score heatmap (cross-model normalization)
- Cross-model statistics (mean, std, min, max, range, median)
- Composite score with adjustable weight sliders
- Constraint adherence detail panel
- CSV and JSON export

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5000` in your browser.

## Project Structure

```
WritingEvaluationTool/
├── app.py                 # Flask application & routes
├── metrics_engine.py      # All NLP/data-science metrics (30+)
├── constraint_parser.py   # Auto-parses prompts to extract constraints
├── requirements.txt       # Python dependencies
├── README.md
└── templates/
    └── index.html         # Full dark-themed SPA dashboard
```

## Usage

1. **Setup**: Paste your writing prompt (with constraints) and optional context material
2. **Model Responses**: Add AI model names and paste/upload their outputs
3. **Results**: View leaderboard, charts, detailed metrics, constraint adherence, and optionally run LLM-as-Judge

## Dependencies

- Flask (web framework)
- NumPy + SciPy (numerical computation)
- scikit-learn (TF-IDF vectorization, cosine similarity)

All NLP metrics are implemented from scratch — no external NLP libraries (NLTK, spaCy, etc.) required.
