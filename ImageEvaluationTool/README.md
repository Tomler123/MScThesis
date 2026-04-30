# Image Generation Evaluation Tool

**MSc Thesis: Understanding and Comparing Generative AI Models: Capabilities, Domains, and Identifying the Best Models for Specific Use Cases**  
**Domain: Image Generation**

---

## Overview

A Flask-based evaluation dashboard for comparing AI-generated images across multiple models. The tool computes **12 categories of deterministic metrics** entirely from image data (no external APIs) and optionally runs an **LLM-as-Judge** pass via Groq. Results are visualised through interactive charts and can be exported as CSV or JSON.

It was built as the empirical backbone for the Image Generation domain of the thesis, which evaluated ChatGPT (DALL·E 3), FLUX, Gemini, Grok, REVE, and Stable Diffusion across five constraint-heavy prompts.

---

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` in your browser.

For LLM judge scoring, you will need a **Groq API key** (free tier). Enter it directly in the browser UI when prompted — no environment variables required.

---

## Architecture

```
ImageEvaluationTool/
├── app.py              # Flask backend — all metric computations + API routes
├── templates/
│   └── index.html      # Dark-themed dashboard UI (Chart.js visualisations)
├── requirements.txt
├── uploads/            # Temporary uploaded images (cleared between sessions)
└── exports/            # CSV and JSON export files
```

The entire metric computation stack is implemented in pure Python inside `app.py` with no calls to external scoring services — only Pillow, OpenCV, NumPy, SciPy, and scikit-learn are required.

---

## Workflow

1. **Upload images** — Upload one image per model being evaluated, along with the original generation prompt.
2. **Optionally upload a reference image** — Required for reference-based metrics (SSIM, PSNR, feature matching). Used for editing prompts where a source image exists.
3. **Run automated evaluation** — All 12 metric categories are computed immediately in the browser.
4. **Run LLM judge (optional)** — Enter your Groq API key. The tool generates a programmatic image description and sends it with the prompt to the judge model.
5. **Compare and export** — View radar charts, bar charts, heatmaps, and per-model breakdowns. Export to CSV or JSON.

---

## Metric Categories

### Reference-Free Metrics (no reference image needed)

**1. Resolution & Aspect Ratio**  
Reports image dimensions, megapixel count, orientation (portrait/landscape), and the nearest standard aspect ratio (e.g. 16:9, 4:3, 1:1). Calculates a deviation score from the closest standard ratio. A resolution score of 100 is assigned when the image meets or exceeds a defined quality threshold.

**2. Color Histogram Analysis**  
Per-channel (R, G, B) mean and standard deviation. Computes color entropy from the luminance histogram and a color diversity score reflecting how broadly the palette is distributed across the histogram range.

**3. Brightness / Contrast / Saturation**  
Mean brightness and luminance, RMS contrast, Michelson contrast, dynamic range (max − min pixel value), and mean/std saturation in HSV space. Produces normalised 0–100 scores for brightness, contrast, and saturation relative to ideal photographic targets.

**4. Edge Density & Detail Complexity**  
Canny edge detector pixel density, mean Sobel gradient magnitude, and local standard deviation texture complexity. Combined into a detail score that reflects how much high-frequency visual information the image contains.

**5. Sharpness / Blur Detection**  
Four independent focus measures: Laplacian variance (primary), Tenengrad gradient energy, Brenner focus measure, and high-frequency ratio from the DCT spectrum. A blur flag is set when the Laplacian variance falls below an empirical threshold. Results are combined into a single sharpness score (0–100).

**6. Composition Analysis**  
Rule-of-thirds adherence (how close the visual centre of mass is to the 1/3 gridlines), horizontal and vertical symmetry scores, quadrant luminance balance, and a centre-of-mass deviation from the image centre. Combined into a composition score (0–100).

**7. Color Palette Extraction**  
K-Means clustering (k=6) in RGB space to extract dominant colours. Each cluster centroid is mapped to an approximate colour name via nearest-neighbour lookup in a named colour table. Computes a colour harmony score based on the angular spread and balance of hues around the colour wheel.

**8. Perceptual Hashing**  
Three hash algorithms implemented from scratch: average hash (aHash), difference hash (dHash), and DCT-based perceptual hash (pHash). Hashes are used to compute similarity distances between images — primarily useful for comparing model outputs to a reference.

**9. Noise Estimation**  
Immerkær noise estimation (sigma of Laplacian residual on a smooth region) and a signal-to-noise ratio estimate. Combined into a noise score (0–100) where higher means cleaner.

**10. Prompt Constraint Adherence**  
Parses the plain-text prompt to extract verifiable constraints, then checks the image against them using computer vision heuristics. See [Constraint Adherence Details](#constraint-adherence-details) below.

### Reference-Based Metrics (require a reference image)

**11. SSIM — Structural Similarity**  
Custom implementation using Gaussian windowing (window size 11, sigma 1.5). Computes luminance, contrast, and structural similarity components. Returns a score in [0, 1].

**12. Reference Comparison Suite**  
Five metrics computed between the generated image and the reference:

| Metric | Description |
|---|---|
| MSE | Mean squared pixel error |
| PSNR | Peak signal-to-noise ratio (dB) |
| Histogram Correlation | OpenCV histogram correlation across all three channels |
| Perceptual Hash Similarity | Normalised Hamming distance between pHash values |
| Feature Match Score | ORB keypoint detector + Brute-Force matcher; ratio of good matches to total keypoints, normalised to 0–1 |

---

## Constraint Adherence Details

The `parse_prompt_constraints()` function uses regex pattern matching to extract the following constraint types from the raw prompt text:

- **Background color** — detects `white/black/gray/blue/deep blue background` and related patterns
- **Required colors** — scans for a fixed list of color keywords (matte-black, stainless-steel, silver, cyan, pastel, etc.)
- **Required objects** — matches `must include`, `include exactly these objects`, and `place exactly N [object]` patterns; supplements with a keyword list (laptop, notebook, bottle, paperclip, arrow, etc.)
- **Forbidden elements** — matches `no [x]`, `do not add [x]`, and `without [x]` patterns
- **Style keywords** — matches photorealistic, blueprint, clay animation, flat lay, top-down, technical, line art, and 20+ other styles
- **Composition type** — detects centered, overhead/top-down/flat-lay, or 3/4 angle
- **Text content** — extracts exact text strings from `write this text: "..."` and `containing only letter: A, B, C` patterns
- **Count requirements** — extracts `exactly N [object]` pairs (e.g. `exactly 7 paperclips`, `3 callout arrows`)
- **Lighting type** — classifies as studio (softbox), natural (daylight), or soft

The `check_constraint_adherence()` function then evaluates the image against these parsed constraints using colour sampling, edge detection, and histogram analysis, returning an overall constraint score (0–100).

> **Limitation noted in thesis:** The constraint adherence metric approximates compliance using structural visual properties. It cannot reliably verify exact object counts or text content — these failure modes are detected only inconsistently and require human or LLM-level semantic verification.

---

## LLM-as-Judge

Because Groq's API does not support vision inputs, the judge pipeline works as follows:

1. The tool calls `_generate_image_description()`, which programmatically summarises all computed metric values into a structured natural-language description of the image (dominant colours, brightness, contrast, composition, edge density, palette, etc.).
2. This description is sent alongside the original prompt to **Llama 3.3 70B Versatile** (Groq API) with a structured scoring instruction.
3. The judge returns seven dimension scores (0–100), a summary paragraph, and separate strengths/weaknesses lists.

**Judge dimensions:**

| Dimension | What it measures |
|---|---|
| Prompt Adherence | How faithfully all explicit constraints are followed |
| Technical Quality | Sharpness, noise, resolution, and rendering quality |
| Style Accuracy | Correctness of the requested visual style |
| Composition | Spatial arrangement, balance, and framing |
| Color Accuracy | Match between specified and rendered colors/tones |
| Detail & Realism | Texture richness and fine-grained rendering |
| Overall Quality | Holistic judge assessment |

---

## Scoring Summary

| Metric | Type | Libraries | Range |
|---|---|---|---|
| Resolution Score | Reference-free | Pillow | 0–100 |
| Color Diversity | Reference-free | NumPy | 0–100 |
| Brightness Score | Reference-free | OpenCV, NumPy | 0–100 |
| Contrast Score | Reference-free | OpenCV, NumPy | 0–100 |
| Saturation Score | Reference-free | OpenCV, NumPy | 0–100 |
| Edge / Detail Score | Reference-free | OpenCV, SciPy | 0–100 |
| Sharpness Score | Reference-free | OpenCV, NumPy | 0–100 |
| Noise Score | Reference-free | SciPy | 0–100 |
| Composition Score | Reference-free | OpenCV, NumPy | 0–100 |
| Color Harmony | Reference-free | scikit-learn, OpenCV | 0–100 |
| Constraint Adherence | Prompt-based | Regex + OpenCV | 0–100 |
| SSIM | Reference-based | OpenCV, NumPy | 0–1 |
| PSNR | Reference-based | NumPy | dB |
| Histogram Correlation | Reference-based | OpenCV | −1 to 1 |
| Perceptual Hash Similarity | Reference-based | Pillow, OpenCV | 0–1 |
| Feature Match Score | Reference-based | OpenCV (ORB) | 0–1 |

The **automated composite score** shown in the UI is a weighted average of five category groups: Color & Tone, Composition, Constraint Adherence, Detail & Texture, and Technical Quality.

---

## Visualisations

All charts are rendered client-side using Chart.js:

- **Radar chart** — category score comparison across all models simultaneously
- **Bar charts** — overall scores and grouped category breakdowns per model
- **Polar area chart** — technical quality dimension comparison
- **Heatmap** — full score matrix with colour coding (green = high, red = low)
- **Per-model metric cards** — individual breakdowns including colour palette swatches from K-Means clustering

---

## Export

Results can be exported from the UI in two formats:

- **CSV** — one row per model, one column per metric (flat structure)
- **JSON** — full nested result objects including all sub-metrics, colour palette data, and perceptual hashes

Export files are saved to the `exports/` directory with a timestamp filename (e.g. `image_eval_results_20260407_005045.json`).

---

## Dependencies

```
flask
numpy
opencv-python
Pillow
scipy
scikit-learn
```

No GPU required. All metric computations run on CPU.