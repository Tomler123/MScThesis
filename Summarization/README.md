# Text Summarization — Prompts & Evaluation Data

This folder contains the prompts, source materials, model responses, automated evaluation scores, and LLM judge verdicts for the **Text Summarization** domain of the thesis:

> *Understanding and Comparing Generative AI Models: Capabilities, Domains, and Identifying the Best Models for Specific Use Cases*

---

## Models Evaluated

- **ChatGPT** (GPT-4 / GPT-5 via chatgpt.com free tier)
- **Claude** (claude.ai)
- **Gemini** (Google Gemini)
- **Grok** (xAI Grok)
- **QWEN** (Alibaba Qwen)

---

## Folder Structure

```
Summarization/
├── prompt1.txt                          # Prompt 1 definition
├── prompt2.txt                          # Prompt 2 definition
├── prompt3.txt                          # Prompt 3 definition
│
├── 2203.02155v1.pdf                     # Source paper for Prompt 2 (InstructGPT)
├── 2203.02155v1.txt                     # Plain-text extraction of the same paper
├── python_3_14_whats_new_clean.txt      # Cached content of the Python 3.14 changelog (Prompt 3 fallback)
│
├── Responses_Prompt1/                   # Model responses to Prompt 1
│   ├── chatgpt_response.txt
│   ├── claude_response.txt
│   ├── gemini_response.txt
│   ├── grok_response.txt
│   └── qwen_response.txt
│
├── Responses_Prompt2/                   # Model responses to Prompt 2
│   └── (same structure)
│
├── Responses_Prompt3/                   # Model responses to Prompt 3
│   └── (same structure)
│
├── AutomatedEvaluationScores/           # CSV output from the Summarization Evaluation Tool
│   ├── eval_prompt-1.csv
│   ├── eval_prompt-2.csv
│   └── eval_prompt-3.csv
│
└── LLM_Judgement/                       # LLM-as-Judge verdicts (Groq / Llama-3.3-70B)
    ├── prompt1_LLM_judgement.txt
    ├── prompt2_LLM_judgement.txt
    └── prompt3_LLM_judgement.txt
```

---

## Prompts

### Prompt 1 — Constrained Short-Text Summarization
**Type:** Instruction-following / Constraint adherence  
**Difficulty:** Low  
**Source:** Inline short paragraph (remote work topic)

The model is asked to summarize a 3-sentence paragraph under strict formatting constraints:
- Exactly **3 bullet points**
- Each bullet must be **10–14 words**
- No invented information
- Neutral tone only

This prompt tests the model's ability to follow tight structural and length constraints while staying faithful to the source.

---

### Prompt 2 — Long-Form Academic Paper Summarization
**Type:** Document understanding / Structured output  
**Difficulty:** Medium–High  
**Source:** `2203.02155v1.pdf` — *Training language models to follow instructions with human feedback* (InstructGPT paper)

The model receives a research paper PDF and must produce a structured summary with exactly five sections in a prescribed order: **Purpose → Method → Key Contributions → Results → Limitations**. Each section must be 2–4 sentences using precise terminology from the paper.

This prompt tests long-context comprehension, factual grounding, and section-ordering discipline.

---

### Prompt 3 — Live Webpage Summarization
**Type:** Web access / Structured output  
**Difficulty:** Medium  
**Source:** `https://docs.python.org/3.14/whatsnew/3.14.html`

The model is asked to fetch and summarize a live webpage into exactly four labelled sections: **Overview, What's New, Who It's For, Key Themes**. Each section must have 2–3 bullet points, and models that cannot access the page must explicitly say so.

This prompt tests real-time web access capability and honesty about limitations. The file `python_3_14_whats_new_clean.txt` contains the page content as a reference for evaluation when a model couldn't access the URL.

---

## Evaluation Data

### Automated Scores (`AutomatedEvaluationScores/`)

Each CSV file corresponds to one prompt and contains per-model metric scores computed by the Summarization Evaluation Tool. Metrics include:

| Category | Metrics |
|---|---|
| Overlap (vs. source) | ROUGE-1/2/L (P/R/F1), BLEU, chrF, TF-IDF Cosine, Jaccard |
| Coverage & Compression | Content Word Overlap, Bigram Overlap, Compression Ratio, Coverage Score, Sentence Overlap |
| Quality | Lexical Diversity (TTR), Information Density, Redundancy, Novel Bigram Ratio, Abstractivity |
| Error Analysis | WER / CER vs. extracted key sentences |
| Constraint Adherence | Prompt Faithfulness (bullet count, word limit, section order, format, negative constraints) |
| Composite | Weighted composite score (Balanced / Coverage-Heavy / Conciseness-Heavy presets) |

### LLM Judgements (`LLM_Judgement/`)

Each file contains the LLM-as-Judge evaluation (via Groq API, `llama-3.3-70b-versatile`) for all models on a given prompt. Scores are given on a 0–10 scale across six dimensions:

1. Factual Accuracy
2. Completeness
3. Conciseness
4. Coherence & Fluency
5. Prompt Faithfulness
6. Overall

---

## Key Design Decisions

- **Prompt 1** uses an inline source text so all models work from identical input — isolating instruction-following ability.
- **Prompt 2** uses a real academic PDF to stress-test long-document understanding and structured extraction.
- **Prompt 3** introduces a web-access variable: models with browsing access (ChatGPT, Gemini) can fetch the page live, while others must admit they cannot — testing both capability and transparency.
- Cached content (`python_3_14_whats_new_clean.txt`) was used as the evaluation reference for models that accessed the live page.