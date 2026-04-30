# Generative AI Model Evaluation — MSc Thesis Repository

**Thesis:** *Understanding and Comparing Generative AI Models: Capabilities, Domains, and Identifying the Best Models for Specific Use Cases*  
**Author:** Toma Sulava Sulaberidze  
**Institution:** Eötvös Loránd University (ELTE), Faculty of Informatics  
**Programme:** MSc Computer Science — Software and Service Architectures

---

## Purpose

This repository contains the complete empirical evaluation framework produced for the above MSc thesis. The central argument is that **no single generative AI model dominates across all use cases** — optimal model choice is task- and domain-specific. To support this claim, five domains were selected, purpose-built evaluation prompts were designed for each, responses were collected from multiple leading models, and every output was scored through two complementary layers: automated NLP/CV metrics and an LLM-as-Judge qualitative assessment.

The repository is structured around **five evaluation domains**. Each domain is represented by two folders: one containing the raw prompts, model responses, and evaluation artefacts, and one containing the standalone Flask-based evaluation tool used to produce those artefacts.

---

## Repository Structure

```
/
├── WritingAndCommunication/        # Prompts, responses, scores — Writing & Communication
├── WritingEvaluationTool/          # Flask evaluation dashboard for Writing & Communication
│
├── Summarization/                  # Prompts, responses, scores — Text Summarization
├── SummarizationTool/              # Flask evaluation dashboard for Text Summarization
│
├── Translation/                    # Prompts, responses, scores — Translation
├── TranslationEvaluationTool/      # Flask evaluation dashboard for Translation
│
├── CodingAssistant/                # Prompts, responses, scores — Coding Assistance
├── CodingEvaluationTool/           # Flask evaluation dashboard for Coding Assistance
│
├── ImageGeneration/                # Prompts, generated images, scores — Image Generation
└── ImageEvaluationTool/            # Flask evaluation dashboard for Image Generation
```

Each domain folder contains its own `README.md` with a full description of the prompts, folder layout, evaluation metrics, and key findings. Each tool folder contains its own `README.md` covering the architecture, metric implementations, API endpoints, and quick-start instructions.

---

## Domains at a Glance

| Domain | Data Folder | Models Evaluated | Prompts | Tool Folder |
|---|---|---|---|---|
| Writing & Communication | `WritingAndCommunication/` | ChatGPT, Claude, Gemini, Grok, QWEN | 3 | `WritingEvaluationTool/` |
| Text Summarization | `Summarization/` | ChatGPT, Claude, Gemini, Grok, QWEN | 3 | `SummarizationTool/` |
| Translation | `Translation/` | ChatGPT, Claude, Gemini, Grok, QWEN | 6 (3 language pairs × 2) | `TranslationEvaluationTool/` |
| Coding Assistance | `CodingAssistant/` | ChatGPT, Claude, Gemini, GLM, MiniMax | 10 | `CodingEvaluationTool/` |
| Image Generation | `ImageGeneration/` | ChatGPT, FLUX, Gemini, Grok, REVE, Stable Diffusion | 5 | `ImageEvaluationTool/` |

---

## Model Selection and Data Collection

Models were selected per domain to balance two objectives: including a **widely-used general-purpose baseline** (ChatGPT, identified as the dominant general-purpose assistant by popularity metrics and public adoption surveys) alongside **domain-relevant candidates** chosen based on their standings on public leaderboards and developer community adoption. All models were accessed through their standard free-tier web interfaces without API-level customisation, so the evaluation reflects typical user-facing conditions. Where available, extended or enhanced thinking modes were enabled so each model operated at maximum capability under free-tier constraints.

### Writing & Communication · Text Summarization · Translation
*Models selected and data collected: **23 March 2026***

| Model | Version | Platform |
|---|---|---|
| ChatGPT | GPT-5.3 | chatgpt.com (free tier) |
| Claude | Claude Sonnet 4.6 | claude.ai (free tier) |
| Gemini | Gemini 3 | gemini.google.com (free tier) |
| Grok | Grok 4.20 | grok.com (free tier) |
| QWEN | Qwen3.5-Flash | chat.qwen.ai (free tier) |

### Coding Assistance
*Models selected and data collected: **5 April 2026***

| Model | Version | Platform |
|---|---|---|
| ChatGPT | GPT-5.3 | chatgpt.com (free tier) |
| Claude | Claude Sonnet 4.6 | claude.ai (free tier) |
| Gemini | Gemini 3 | gemini.google.com (free tier) |
| GLM | GLM-5 | chat.z.ai (free tier) |
| MiniMax | MiniMax-M2.7 | agent.minimax.io (free tier) |

### Image Generation
*Models selected and data collected: **5–7 April 2026***

| Model | Version | Platform |
|---|---|---|
| ChatGPT | GPT-5.3 (image generation) | chatgpt.com (free tier) |
| FLUX | FLUX.1 [dev] | flux.ai (free tier) |
| Grok | Grok Aurora | grok.com (free tier) |
| Gemini | Gemini Imagen 3 | gemini.google.com (free tier) |
| REVE | Reve Image 1.0 | reve.art (free tier) |
| Stable Diffusion | Stable Diffusion 3.5 | stability.ai (free tier) |

---

## Evaluation Framework

### Prompt Design Philosophy

All prompts across all domains were written with **explicit, verifiable constraints** — word limits, required phrases, forbidden vocabulary, exact structural rules, object counts — rather than open-ended stylistic requests. This makes constraint adherence measurable as a first-class scoring dimension and mirrors the kind of instruction-following demands found in real professional use.

### Two-Layer Scoring

Every model response is evaluated through two complementary layers.

**Layer 1 — Automated Metrics.** Each domain has a dedicated Flask tool that computes deterministic, reproducible scores using Python standard and scientific libraries. No large external NLP or CV frameworks are required. Results are exported as CSV files with one row per model per prompt.

**Layer 2 — LLM-as-Judge.** Qualitative assessment is provided by `llama-3.3-70b-versatile` via the Groq API. The judge receives the original prompt alongside the model's response and scores multiple qualitative dimensions on a 0–10 or 0–100 scale with written justifications. For image generation, where Groq does not support vision inputs, the tool first generates a structured programmatic description of each image and passes that to the judge. Verdicts are stored as plain-text files in each domain's `LLM_Judge/` or `LLM_Judgement/` folder.

### Composite Scoring

Each tool computes a weighted composite score from its category scores. Default weights reflect the relative importance of each quality dimension within the domain (e.g., test pass rate carries the most weight in Coding; constraint adherence is heavily weighted in Writing). Weights are adjustable via sliders in each tool's UI before final results are computed.

---

## Domain Summaries

### Writing & Communication
Three constraint-heavy professional writing tasks — a formal email rewrite, a dual-audience message, and a structured internal announcement — tested instruction-following precision. Constraint adherence was the primary differentiator: prose fluency was uniformly strong across models, but compliance with simultaneous multi-part structural rules varied significantly. The evaluation tool computes 60+ metrics across 8 categories including readability, lexical analysis, tone and sentiment, structural analysis, coherence, and a dedicated constraint auto-parser.

### Text Summarization
Three tasks covered constrained short-text summarisation, long-form academic paper summarisation (the InstructGPT paper, ~30,000 words), and live webpage summarisation requiring real-time web access. The web-access task introduced a capability variable absent from the others — models that could not fetch the live page were instructed to state this explicitly and stop. Metrics include ROUGE-1/2/L, BLEU, chrF, TF-IDF cosine, WER/CER, compression ratio, and prompt faithfulness analysis.

### Translation
A single literary source text — *Negotiation Over Ship Salvage*, a fictional dialogue engineered with deliberately contrasting registers and dense lexical polysemy — was translated into Russian, Italian, and Georgian by each model, then back-translated into English. Round-trip back-translation similarity was measured using 20+ NLP metrics, enabling objective scoring without native-language human evaluators for each target language. The three language pairs were chosen to represent a range of linguistic distances from English: Italian (close, Latin-script), Russian (moderate, Cyrillic), and Georgian (distant, unique Mkhedruli script, non-Indo-European).

### Coding Assistance
Ten Python programming tasks spanning three task types (implementation, debugging, optimisation) and three difficulty tiers (easy, medium, hard) were evaluated. Each response was scored across 15+ metric categories including test pass rate, cyclomatic complexity, Halstead metrics, maintainability index, AST structure, nesting depth, documentation coverage, DRY score, and constraint adherence — all computed via static analysis on extracted code files.

### Image Generation
Five image prompts — photorealistic product photography, multi-object flat-lay composition, counting and text rendering, and two style-transfer editing tasks — were used to benchmark six image generation platforms. Automated metrics are computed entirely from image data using Pillow, OpenCV, NumPy, SciPy, and scikit-learn. The LLM judge operates on a programmatic image description generated by the tool, covering 7 qualitative dimensions including prompt adherence, style accuracy, composition, and technical quality.

---

## Running the Evaluation Tools

Each tool is a self-contained Flask application. The general pattern is:

```bash
cd <ToolFolder>
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

For LLM-as-Judge scoring, a free Groq API key (obtainable at [console.groq.com](https://console.groq.com)) is entered directly in the browser — no environment variables or server-side key storage required.

Full quick-start instructions, API endpoint documentation, and metric implementation details are in each tool's own `README.md`.

---

## Reproducibility Notes

- All model responses were collected in a **single session per domain** without regeneration. Generative models are non-deterministic, so re-running the same prompts may produce different outputs.
- Free-tier interfaces can impose rate limits and may surface different model versions over time, which limits perfect long-term reproducibility.
- Automated metric scores are fully deterministic given the stored response text and are reproducible by re-running the evaluation tools against the saved response files.
- LLM judge scores are non-deterministic. The stored verdict files represent the evaluations as originally produced during data collection.