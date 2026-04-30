# Writing & Communication — Prompts & Evaluation Data

**MSc Thesis**: *Understanding and Comparing Generative AI Models: Capabilities, Domains, and Identifying the Best Models for Specific Use Cases*

This folder contains all prompts, model responses, automated evaluation scores, and LLM-as-Judge assessments for the **Writing & Communication** domain of the thesis evaluation.

---

## Domain Overview

The Writing & Communication domain evaluates how well AI models handle structured, constraint-heavy writing tasks — the kind of writing that mirrors real professional use: crafting emails, tailoring messages for different audiences, and drafting formal internal documents. The central challenge embedded in all three prompts is **constraint adherence**: models must satisfy a combination of word limits, tone requirements, structural rules, and forbidden/required vocabulary simultaneously, not just produce fluent prose.

Three prompts were designed with escalating structural complexity, each targeting a distinct professional writing scenario.

---

## Models Evaluated

| Model   | Notes                             |
|---------|-----------------------------------|
| ChatGPT | General-purpose baseline (GPT-4o) |
| Claude  | Anthropic's assistant             |
| Gemini  | Google's assistant                |
| Grok    | xAI's assistant                   |
| Qwen    | Alibaba's assistant               |

All models received **identical prompts** with no additional context or system instructions.

---

## Prompts

### Prompt 1 — Professional Email with Strict Constraints (`prompt1.txt`)

**Task:** Rewrite a blunt, informal message into a polished professional email.

**Source message:** *"Hello, I have not received the updated document yet. I need it today. Please confirm when you can send it."*

**Constraints imposed:**
- Subject line of maximum 8 words
- Body word count: 110–130 words (subject line excluded)
- Exactly 3 paragraphs, no bullet points
- Must include the explicit deadline phrase `"by 5 PM today"`
- Must include one concrete next step (e.g., "Please reply with…")
- Forbidden words: *urgent*, *ASAP*, *need*
- Tone: professional and non-accusatory

**Purpose:** Tests whether a model can simultaneously satisfy multiple hard constraints (word count, paragraph count, forbidden vocabulary, required phrases) while rewriting a message that, in its original form, violates several of those constraints by design.

---

### Prompt 2 — Audience-Adaptive Dual Message (`prompt2.txt`)

**Task:** Communicate the same update in two versions — one for a technical teammate, one for a non-technical manager.

**Shared content:** *"A critical bug was fixed. Release is delayed by one day due to additional testing."*

**Constraints imposed:**
- Each message: 90–110 words
- Each message must contain exactly one sentence describing the reason for the delay
- Message A must include exactly **two** technical terms from: `{regression, deployment, patch, QA, rollback}`
- Message B must include **zero** technical terms from that list
- Both messages must include: (i) a clear next step, and (ii) a confidence statement (`"We are confident…"` or equivalent)
- No bullet points
- Output format must be `A) ... B) ...`

**Purpose:** Tests audience awareness and controlled vocabulary — specifically whether a model can include a precise count of technical terms in one message while completely excluding them from another, all while keeping both messages within a word range and meeting shared structural requirements. This is one of the most demanding constraint combinations in the domain.

---

### Prompt 3 — Structured Internal Announcement (`prompt3.txt`)

**Task:** Draft a formal internal maintenance announcement with mandatory section headings.

**Required headings (in order):** Summary, Impact, Time Window, Action Required, Contact

**Constraints imposed:**
- Each heading section must contain exactly 2 sentences (10 sentences total)
- "Time Window" must include the phrase `"next Tuesday"` and the duration `"2 hours"`
- "Impact" must mention both possible unavailability **and** possible slow performance
- "Action Required" must list exactly 3 actions written as an inline sentence separated by semicolons (no bullets)
- "Contact" must include the placeholder email `support@example.com`
- No apologies
- Tone: neutral and informative
- Total length: 150–190 words

**Purpose:** Tests structural precision at the section level. Every paragraph has an exact sentence count, the document has a mandatory heading order, and specific factual/formatting requirements are embedded into individual sections. This mirrors formal IT/ops communication templates used in real workplaces.

---

## Folder Structure

```
WritingAndCommunication/
├── prompt1.txt                          # Professional email rewrite
├── prompt2.txt                          # Dual-audience message
├── prompt3.txt                          # Internal maintenance announcement
│
├── Responses_Prompt1/                   # Raw model outputs for Prompt 1
│   ├── chatgpt_response.txt
│   ├── claude_response.txt
│   ├── gemini_response.txt
│   ├── grok_response.txt
│   └── qwen_response.txt
│
├── Responses_Prompt2/                   # Raw model outputs for Prompt 2
│   ├── chatgpt_response.txt
│   ├── claude_response.txt
│   ├── gemini_response.txt
│   ├── grok_response.txt
│   └── qwen_response.txt
│
├── Responses_Prompt3/                   # Raw model outputs for Prompt 3
│   ├── chatgpt_response.txt
│   ├── claude_response.txt
│   ├── gemini_response.txt
│   ├── grok_response.txt
│   └── qwen_response.txt
│
├── AutomatedEvaluationScores/           # CSV outputs from the evaluation tool
│   ├── writing_eval_results_prompt1.csv
│   ├── writing_eval_results_prompt2.csv
│   └── writing_eval_results_prompt3.csv
│
├── LLM_Judgement/                       # Qualitative LLM-as-Judge verdicts
│   ├── prompt1_LLM_judgement.txt
│   ├── prompt2_LLM_judgement.txt
│   └── prompt3_LLM_judgement.txt
│
└── README.md
```

---

## Evaluation Approach

Each model response was evaluated through two complementary layers, following the framework described in Chapter 5 of the thesis.

### Layer 1 — Automated Metrics (via WritingEvaluationTool)

The custom Flask-based evaluation tool computed 8 metric categories per response:

| Category             | Weight | What it measures |
|----------------------|--------|-----------------|
| Content Quality      | 20%    | TF-IDF similarity to prompt, information coverage, entity retention |
| Constraint Adherence | 20%    | Auto-parsed constraint checks (word limits, forbidden words, required phrases, structure rules) |
| Tone & Sentiment     | 15%    | Formality score, tone consistency, sentiment polarity, subjectivity |
| Readability          | 15%    | Flesch Reading Ease, Flesch-Kincaid Grade, Gunning Fog, Coleman-Liau, ARI, SMOG |
| Lexical Analysis     | 10%    | Type-Token Ratio, vocabulary richness, lexical sophistication, information density |
| Structural           | 10%    | Sentence/paragraph counts, length variation, sentence type variety |
| Coherence & Flow     | 5%     | Inter-sentence TF-IDF similarity, transition word density, global coherence |
| Redundancy           | 5%     | Bigram/trigram repetition, cross-sentence similarity, content word repetition |

Results are exported as CSV files in `AutomatedEvaluationScores/`, with one file per prompt.

### Layer 2 — LLM-as-Judge (Groq / Llama 3.3 70B)

The LLM judge evaluated each response across 8 qualitative dimensions:

1. **Tone Accuracy** — Does the tone match what the prompt requested?
2. **Constraint Following** — Were all explicit constraints satisfied?
3. **Audience Appropriateness** — Is the writing suitable for the intended reader?
4. **Persuasiveness / Effectiveness** — Does the writing achieve its communicative goal?
5. **Grammar & Polish** — Correctness and overall writing quality
6. **Clarity & Conciseness** — Is the message clear and economical?
7. **Structure & Organisation** — Is the content logically organised?
8. **Creativity & Naturalness** — Does it read as genuine rather than templated?

Each dimension is scored 1–10 with a short rationale. A final overall score out of 100 is provided per model per prompt. Judgements are stored in `LLM_Judgement/`.

---

## Key Observations (Summary)

Across the three prompts, the models showed a consistent pattern: **fluency and grammar were uniformly strong**, while **constraint adherence was the primary differentiator**. Models that followed every constraint precisely tended to score lower on creativity and naturalness, while models that produced more expressive prose often missed one or more structural rules.

Prompt 2 proved the most discriminating — the requirement to include exactly two technical terms in Message A while using zero in Message B exposed clear differences in how carefully models read and apply multi-part, list-based constraints.

Prompt 3 revealed differences in structural discipline: the requirement for exactly two sentences per section and a precise word count window was met by some models but not all, with violations most commonly appearing in the "Action Required" section.

Detailed results and cross-model analysis are discussed in **Chapter 7.1** of the thesis.