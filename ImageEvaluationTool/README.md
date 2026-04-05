# Image Generation Evaluation Tool

**MSc Thesis: Understanding and Comparing Generative AI Models**  
**Domain: Image Generation**

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5000` in your browser.

## Features

### Deterministic Metrics (12 categories, no LLM needed)
1. **Resolution & Aspect Ratio** — dimensions, megapixels, standard ratio matching
2. **Color Histogram Analysis** — per-channel stats, color entropy, diversity score
3. **Brightness / Contrast / Saturation** — mean brightness, RMS contrast, Michelson contrast, dynamic range, saturation stats
4. **Edge Density & Detail Complexity** — Canny edge density, Sobel gradient magnitude, texture complexity (local std dev)
5. **Sharpness / Blur Detection** — Laplacian variance, Tenengrad, Brenner focus measure, frequency domain high-freq ratio
6. **Composition Analysis** — rule of thirds adherence, horizontal/vertical symmetry, visual center of mass, quadrant balance
7. **Color Palette Extraction** — K-Means dominant colors, color harmony score, named color mapping
8. **Perceptual Hashing** — Average hash (aHash), Difference hash (dHash), DCT-based perceptual hash (pHash)
9. **Noise Estimation** — Immerkaer noise sigma, SNR estimate
10. **SSIM** (reference-based) — custom implementation with Gaussian windowing
11. **Reference Comparison Suite** — MSE, PSNR, histogram correlation, perceptual hash distance, ORB feature matching
12. **Prompt Constraint Adherence** — parses background color, required colors, style keywords, composition type, lighting, count requirements; checks image against extracted constraints

### LLM-as-Judge (Optional)
- Uses **Groq API** (Llama 3.3 70B Versatile) — free tier
- Since Groq doesn't support vision, the tool generates a detailed programmatic description of each image and sends it with the original prompt
- Scores: Prompt Adherence, Technical Quality, Style Accuracy, Composition, Color Accuracy, Detail & Realism, Overall Quality
- Returns strengths, weaknesses, and a summary

### Visualization & Export
- **Radar chart** — category score comparison across models
- **Bar charts** — overall scores, grouped category breakdown
- **Polar area chart** — technical quality comparison
- **Heatmap** — score matrix with color coding
- **Detailed breakdowns** — per-model metric cards with color palette swatches
- **Export** — JSON and CSV

## Architecture

```
ImageEvalTool/
├── app.py              # Flask backend + all metric computations
├── templates/
│   └── index.html      # Dark-themed dashboard UI
├── requirements.txt
├── prompts/            # Input prompts used for evaluation
├── uploads/            # Temporary uploaded files
└── exports/            # Generated export files
```

## Metrics Summary Table

| Metric | Type | Library | Score Range |
|--------|------|---------|-------------|
| Resolution Score | Reference-free | Pillow | 0-100 |
| Color Diversity | Reference-free | NumPy | 0-100 |
| Brightness Score | Reference-free | OpenCV, NumPy | 0-100 |
| Contrast Score | Reference-free | OpenCV, NumPy | 0-100 |
| Saturation Score | Reference-free | OpenCV, NumPy | 0-100 |
| Edge/Detail Score | Reference-free | OpenCV, SciPy | 0-100 |
| Sharpness Score | Reference-free | OpenCV, NumPy | 0-100 |
| Noise Score | Reference-free | SciPy | 0-100 |
| Composition Score | Reference-free | OpenCV, NumPy | 0-100 |
| Color Harmony | Reference-free | sklearn, OpenCV | 0-100 |
| SSIM | Reference-based | OpenCV, NumPy | 0-1 |
| PSNR | Reference-based | NumPy | dB |
| Histogram Correlation | Reference-based | OpenCV | -1 to 1 |
| Perceptual Hash Similarity | Reference-based | Pillow, OpenCV | 0-1 |
| Feature Match Score | Reference-based | OpenCV (ORB) | 0-1 |
| Constraint Adherence | Prompt-based | Regex + CV | 0-100 |
