# Translation — Prompts & Model Responses

This folder contains the source text, prompts, and raw model responses used to evaluate the **Translation** capabilities of five large language models as part of the MSc thesis:

> *"Understanding and Comparing Generative AI Models: Capabilities, Domains, and Identifying the Best Models for Specific Use Cases"*

---

## Models Evaluated

| Model    |
|----------|
| ChatGPT  |
| Claude   |
| Gemini   |
| Grok     |
| QWEN     |

---

## Source Text

**File:** `basetext.txt`

A single, deliberately complex literary passage was used as the evaluation corpus across all language pairs. The text — *"Negotiation Over Ship Salvage"* — is a fictional dialogue between two characters with **starkly contrasting registers**:

- **Alistair Vance** — a formal, aristocratic corporate representative who speaks in elaborate, legalistic, and bureaucratic English, frequently deploying archaic phrasing and multi-clause sentences.
- **Jax** — a working-class salvage foreman who speaks in dense American slang, idioms, and colloquialisms (e.g., *"kicking the can down the road"*, *"bite the bullet"*, *"spill the beans"*).

The text was specifically engineered to stress-test translation quality along multiple axes:
- **Register preservation** — can the model maintain the formal/informal contrast across languages?
- **Idiomatic adaptation** — can colloquialisms be translated contextually rather than literally?
- **Semantic density** — the passage is rich in homonyms and polysemous words (e.g., *"bank"*, *"current"*, *"draft"*, *"sound"*, *"bark"* each appear multiple times with different meanings).
- **Length and structure fidelity** — paragraph breaks, dialogue tags, and punctuation must be preserved exactly.

---

## Prompts

Each prompt used the same role/task/constraint structure, differing only in the target language direction.

| File        | Task Description                          | Language Pair         |
|-------------|-------------------------------------------|-----------------------|
| `prompt1.txt` | Translate source text                   | English → Russian     |
| `prompt2.txt` | Back-translate model's Russian output   | Russian → English     |
| `prompt3.txt` | Translate source text                   | English → Italian     |
| `prompt4.txt` | Back-translate model's Italian output   | Italian → English     |
| `prompt5.txt` | Translate source text                   | English → Georgian    |
| `prompt6.txt` | Back-translate model's Georgian output  | Georgian → English    |

### Prompt Structure

All prompts share the same instruction template:

```
Role: You are an expert, professional literary and diplomatic translator.
Task: Translate the following text from [Source] into [Target].

Constraints & Guidelines:
  - Preserve Meaning and Intent: No summarization, condensation, or omission.
  - Contextual Adaptation: Translate idioms by meaning, not word-for-word.
  - Maintain Register: Preserve the formal/informal character voice contrast.
  - Formatting: Preserve all paragraph breaks, punctuation, and dialogue tags.
  - Strict Output: Output only the translated text — no notes or preamble.
```

### Evaluation Methodology: Back-Translation

The evaluation uses a **round-trip back-translation** approach:

1. Each model translates the English source text into the target language (odd prompts: 1, 3, 5).
2. Each model's translated output is then back-translated into English (even prompts: 2, 4, 6).
3. The back-translated English is compared against the original English source using automated NLP metrics and an LLM judge.

This methodology allows objective, reference-based scoring without requiring native-language human evaluators for Russian, Italian, and Georgian.

---

## Language Pairs

Three language pairs were selected to cover a range of linguistic distances from English:

| Language Pair     | Rationale                                                                 |
|-------------------|---------------------------------------------------------------------------|
| English ↔ Russian  | Cyrillic script, Slavic morphology, different grammatical gender system  |
| English ↔ Italian  | Latin script, Romance language, grammatically closer to English          |
| English ↔ Georgian | Non-Indo-European, unique Mkhedruli script, agglutinative morphology     |

---

## Folder Structure

```
Translation/
├── basetext.txt                        # Original English source passage
├── prompt1.txt                         # EN → RU translation prompt
├── prompt2.txt                         # RU → EN back-translation prompt
├── prompt3.txt                         # EN → IT translation prompt
├── prompt4.txt                         # IT → EN back-translation prompt
├── prompt5.txt                         # EN → KA translation prompt
├── prompt6.txt                         # KA → EN back-translation prompt
│
├── Responses_Prompt1/                  # EN → RU translations
│   ├── chatgpt_response.txt
│   ├── claude_response.txt
│   ├── gemini_response.txt
│   ├── grok_response.txt
│   └── qwen_response.txt
├── Responses_Prompt2/                  # RU → EN back-translations
├── Responses_Prompt3/                  # EN → IT translations
├── Responses_Prompt4/                  # IT → EN back-translations
├── Responses_Prompt5/                  # EN → KA translations
├── Responses_Prompt6/                  # KA → EN back-translations
│
├── AutomatedScores/
│   ├── translation_evaluation1.csv     # Scores for English ↔ Russian
│   ├── translation_evaluation2.csv     # Scores for English ↔ Italian
│   └── translation_evaluation3.csv     # Scores for English ↔ Georgian
│
└── LLM_Judge/
    ├── english_russian.txt             # LLM judge verdicts for EN ↔ RU
    ├── english_italian.txt             # LLM judge verdicts for EN ↔ IT
    └── english_georgian.txt            # LLM judge verdicts for EN ↔ KA
```

---

## Automated Scores

Scores were produced by the **Translation Evaluation Tool** (see `TranslationEvaluationTool/`). Each CSV file contains the following per-model, per-language-pair metrics:

**Back-Translation Similarity Metrics** (comparing original EN vs. back-translated EN):

| Metric Group       | Metrics                                              |
|--------------------|------------------------------------------------------|
| N-gram Overlap     | BLEU-1, BLEU-2, BLEU-4                               |
| ROUGE              | ROUGE-1 F1, ROUGE-2 F1, ROUGE-L F1                  |
| Character-level    | chrF                                                 |
| Edit Distance      | WER (Word Error Rate), CER (Character Error Rate)    |
| Semantic Similarity| TF-IDF Cosine, Jaccard Similarity                    |
| Content Overlap    | Content Word Overlap, Bigram Overlap, Sentence Overlap |
| Length             | Length Ratio, Length Score                           |
| Lexical Diversity  | TTR of original and back-translation                 |
| Composite          | Weighted composite score (configurable profile)      |

**LLM Judge Scores** (via Groq API, `llama-3.3-70b-versatile`):

| Dimension                  | Score (0–10) |
|----------------------------|--------------|
| Translation Accuracy       | ✓            |
| Fluency                    | ✓            |
| Meaning Preservation       | ✓            |
| Naturalness                | ✓            |
| Grammatical Correctness    | ✓            |
| Overall Score              | ✓            |

---

## LLM Judge Files

The `LLM_Judge/` subfolder contains the raw textual output from the LLM judge (Groq `llama-3.3-70b-versatile`) for each language pair. Each file records per-model evaluations with dimension-level scores and justifications, as well as an overall assessment summary.