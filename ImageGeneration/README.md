# Image Generation — Prompts & Outputs

**MSc Thesis: Understanding and Comparing Generative AI Models: Capabilities, Domains, and Identifying the Best Models for Specific Use Cases**  
**Domain: Image Generation**

---

## Overview

This folder contains the five evaluation prompts used to benchmark image generation models, the images produced by each model, automated evaluation score exports, and the LLM judge verdicts. The goal of this domain was to assess how well leading image generation platforms follow complex, constraint-heavy prompts — covering photorealistic product photography, multi-object flat-lay composition, precise counting and text rendering, and style-transfer editing.

---

## Models Evaluated

| Model | Platform | Engine |
|---|---|---|
| **ChatGPT** | chatgpt.com | OpenAI DALL·E 3 |
| **FLUX** | playground.bfl.ai | FLUX.2 MAX |
| **Gemini** | gemini.google.com | Imagen 3 (via Gemini) |
| **GROK** | grok.com | Grok Imagine |
| **REVE** | app.reve.com | reve-v1 1.5 |
| **Stable Diffusion** | stablediffusionweb.com | SD Plus |

All images were generated on **24 March 2026** using each platform's default free-tier web interface. Model-specific settings (aspect ratio, resolution, prompt upscaling) are documented in each model's `overview.txt`.

---

## Prompts

All prompts were written with explicit, verifiable constraints to stress-test instruction-following beyond vague stylistic requests.

### Prompt 1 — Photorealistic Product Photography
**File:** `prompt1.txt`

A studio product photo of a **matte-black reusable water bottle** on a seamless white background. Constraints cover camera angle (3/4 view, mid-height), surface finish (matte, no gloss), material texture (brushed-metal screw cap), subtle water droplets, softbox lighting from upper-left with a single soft shadow, depth of field, and strict absence of branding or props.

**Purpose:** Tests photorealistic rendering accuracy and the ability to follow precise technical photography constraints — lighting direction, material properties, and compositional rules simultaneously.

---

### Prompt 2 — Multi-Object Flat-Lay Composition
**File:** `prompt2.txt`

A top-down desk flat-lay on a light wooden surface containing **exactly eight specified objects**: open laptop (screen on, blank document), blue notebook, red pen, white coffee mug, small green plant in a white pot, black smartphone (screen off), three stacked sticky notes (yellow/pink/green), and exactly one silver paperclip next to the notebook. Objects must not overlap; all must be fully visible with no logos or brand text.

**Purpose:** Tests object-manifest compliance — the model's ability to include a precise object list, maintain exact counts, and arrange items in a coherent, non-overlapping layout.

---

### Prompt 3 — Counting and Text Rendering
**File:** `prompt3.txt`

A clean overhead scene of a plain light-gray tabletop with **exactly 7 identical, non-stacked silver metal paperclips**, plus one yellow sticky note bearing the exact uppercase text **"MEETING AT 3"**. No other text anywhere in the image.

**Purpose:** Targets two of the most commonly cited failure modes in image generation: **exact object counting** and **accurate text rendering**. These tasks require semantic precision that pure visual generation pipelines often struggle with.

---

### Prompt 4 — Style-Transfer Editing (Clay + Watercolour)
**File:** `prompt4.txt`

Edit the provided cartoon base character (`BaseCartoon.png`) into a **hybrid clay stop-motion / watercolour illustration**. Required transformations: visible fingerprints and soft rounded edges on the character (clay), soft studio lighting with a gentle shadow, watercolour paper wash background with visible paper grain and pastel tones, preserved original pose and silhouette, clay-textured clothing matching the original, and no added text or extra elements.

**Purpose:** Tests image-conditioned editing and style-transfer fidelity. The model must simultaneously apply two distinct artistic styles while maintaining compositional and character-level consistency with a reference image.

---

### Prompt 5 — Style-Transfer Editing (Technical Blueprint)
**File:** `prompt5.txt`

Edit the same cartoon base character into a **technical blueprint illustration**: deep blue background, light cyan/white linework with consistent stroke width, exactly two fill tones, three callout arrows pointing to (A) head/face, (B) torso/clothing, and (C) shoes — each ending in a small label box with only a single letter. No extra text, no extra characters, original pose and proportions preserved.

**Purpose:** Tests precise multi-constraint style-transfer with strict structural rules — exact color palette, fixed fill tone count, specific annotation schema, and no extraneous elements.

---

## Folder Structure

```
ImageGeneration/
├── prompt1.txt                        # Prompt definitions (see above)
├── prompt2.txt
├── prompt3.txt
├── prompt4.txt
├── prompt5.txt
├── BaseCartoon.png                    # Reference image used for Prompts 4 & 5
│
├── ChatGPT/                           # One folder per model
│   ├── image1.png  ...  image5.png    # One image per prompt
│   └── overview.txt                   # Model version, settings, generation date
├── FLUX/
├── Gemini/
├── GROK/
├── REVE/
├── StableDiffusion/
│
├── LLM_Judgement/
│   ├── prompt1_LLM_judgement.txt      # Judge verdicts for all models on Prompt 1
│   ├── prompt2_LLM_judgement.txt
│   ├── prompt3_LLM_judgement.txt
│   ├── prompt4_LLM_judgement.txt
│   └── prompt5_LLM_judgement.txt
│
└── AutomatedEvaluationScores/
    ├── image_eval_results_1.csv       # Automated metric scores per prompt
    ├── image_eval_results_2.csv
    ├── image_eval_results_3.csv
    ├── image_eval_results_4.csv
    └── image_eval_results_5.csv
```

> **Note:** FLUX and REVE generated multiple candidate images for Prompt 1 (files named `image1_1.png`, `image1_2.png`, etc.) due to their multi-output generation options. The best candidate was selected for evaluation.

---

## LLM Judge Scoring

Each `LLM_Judgement/promptN_LLM_judgement.txt` file contains per-model scores, a summary paragraph, and lists of strengths and weaknesses generated by an **LLM-as-Judge** (Llama 3.3 70B Versatile via Groq API). Since Groq does not support vision inputs, the evaluation tool generates a detailed programmatic description of each image and passes it alongside the original prompt to the judge.

**Scored dimensions (0–100 each):**

| Dimension | What it measures |
|---|---|
| Prompt Adherence | How faithfully all explicit constraints are followed |
| Technical Quality | Sharpness, noise, resolution, and rendering quality |
| Style Accuracy | Correctness of the requested visual style |
| Composition | Spatial arrangement, balance, and framing |
| Color Accuracy | Match between specified and rendered colors/tones |
| Detail & Realism | Texture richness, fine-grained rendering |
| Overall Quality | Holistic judge assessment |

---

## Key Results Summary

Based on thesis analysis (Chapter 7.5):

- **Flux** leads the LLM judge ranking with a mean of **91.00**, outperforming on photorealism and style-transfer tasks.
- **ChatGPT** leads the automated composite with a mean of **54.20**, partly inflated by the edge-density of its blueprint output on Prompt 5.
- **Stable Diffusion** is the clear underperformer in the judge evaluation (**75.40**), with significant failures on object-manifest compliance (Prompt 2) and style-transfer (Prompt 4).
- **Reve** shows the largest automated-vs-judge discrepancy: lowest automated score (**48.32**) but joint-third in the judge (**90.00**), explained by the automated metrics penalising its smooth, artifact-free outputs as lacking texture.
- **Counting and text rendering** (Prompt 3) proved to be the most discriminating task, exposing failures in Grok (wrong paperclip count, mixed-case text) and Stable Diffusion (object hallucinations).

For full analysis, see **Chapter 7.5** of the thesis.

---

## Evaluation Tool

Automated metrics were computed using the **ImageEvaluationTool** (see `../ImageEvaluationTool/`). The tool implements 12 metric categories using Pillow, OpenCV, NumPy, SciPy, and scikit-learn — no external API calls required for the automated layer.