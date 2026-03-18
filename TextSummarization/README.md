# Text Summarization - Prompts

This folder contains evaluation prompts for the **Text Summarization** domain.
The prompts focus on three core qualities:
- **Coverage** (captures key points)
- **Faithfulness** (no invented claims; grounded only in the provided content)
- **Conciseness** (brief, well-structured output)

## Files
- `prompt1.txt` — Paragraph summarization with strict bullet and length constraints
- `prompt2.txt` — Research paper PDF summarization with fixed section schema
- `prompt3.txt` — Technical/lecture PDF summarization with a structured bullet template
- `prompt4.txt` — Webpage summarization with fixed sections and browsing constraint

## Prompt descriptions

### Prompt 1 — Short Paragraph Summarization
**Goal:** Test concise, faithful summarization of a short inline paragraph.

**What it tests**
- Coverage of all key ideas from a short input
- Faithfulness (no extra claims beyond the paragraph)
- Format compliance (exact bullet count and word limits)

**Expected strong output characteristics**
- Exactly 3 bullet points
- Each bullet is 10–14 words
- Neutral phrasing, no opinions
- Captures both benefits and drawbacks plus the “hybrid schedule” mitigation

---

### Prompt 2 — Literature PDF Summarization (Research Paper)
**Goal:** Test summarization of a full research paper with a required section schema.

**What it tests**
- Identification of purpose, method, contributions, results, limitations
- Faithfulness to the PDF (no invented metrics or claims)
- Structured writing and consistency across models

**Expected strong output characteristics**
- Uses the required sections in the correct order
- 2–4 sentences per section
- Mentions only results and details stated in the PDF
- Uses terminology consistent with the paper

**Recommended document**
- "Attention Is All You Need" (Transformer paper): https://arxiv.org/pdf/1706.03762.pdf

---

### Prompt 3 — Technical / Lecture PDF Summarization
**Goal:** Test summarization of technical educational content under a fixed template.

**What it tests**
- Extraction of core concepts and definitions
- Ability to summarize technical material without adding external facts
- Template compliance and handling missing information explicitly

**Expected strong output characteristics**
- Exactly 5 bullets with the required titles:
  Concept, Intuition, Key Terms, Example/Use Case, Common Pitfall
- Each bullet is 1–2 sentences
- Uses “Not specified in the PDF” when required information is absent

**Recommended document source**
- MIT OpenCourseWare lecture notes (choose one lecture PDF and keep it constant across models):
  https://ocw.mit.edu/courses/6-867-machine-learning-fall-2006/resources/lecture-notes/

---

### Prompt 4 — Webpage Summarization (Link-Based)
**Goal:** Test summarization of a webpage with strict section constraints.

**What it tests**
- Ability to identify and structure key themes from a webpage
- Faithfulness to the page content
- Handling of browsing limitations (must state inability to access and stop)

**Expected strong output characteristics**
- Exactly 4 sections:
  Overview, What’s New, Who It’s For, Key Themes
- Each section contains 2–3 bullet points
- No content beyond the page
- If browsing is unavailable, the model explicitly states it cannot access the link

**Recommended webpage**
- NIST Digital Identity Guidelines overview:
  https://www.nist.gov/identity-access-management/projects/nist-special-publication-800-63-digital-identity-guidelines