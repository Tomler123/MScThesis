# Image Generation — Prompts

This folder contains evaluation prompts for the **Image Generation** domain.
The prompts focus on:
- **Prompt adherence** (required elements present; forbidden elements absent)
- **Visual quality** (realism/stylization quality, coherence, artifacts)
- **Composition control** (camera angle, layout, lighting)
- **Fine-grained control** (exact object counts; minimal text rendering)

## Files
- `prompt1.txt` — Studio product photo (high constraint adherence)
- `prompt2.txt` — Desk scene (multi-object composition, flat lay)
- `prompt3.txt` — Exact-count objects + short text on sticky note
- `prompt4.txt` — **TODO** (reserved for photo editing / image-to-image evaluation)

## Prompt descriptions

### Prompt 1 — Studio Product Photo (Photorealistic)
**Goal:** Test photorealism and strict constraint following in a controlled studio setting.

**What it tests**
- Visual realism (materials, lighting, shadow)
- Composition control (3/4 angle, centered framing, camera height)
- Constraint compliance (no branding/text, single shadow, matte surface)
- Fine details (cap material, grip ridge, subtle water droplets)

**Expected strong output characteristics**
- Plain seamless white background (no texture/gradient)
- Matte-black bottle with stainless screw cap + brushed-metal look
- Subtle water droplets visible and realistic
- One soft shadow; no glare/hotspots; no logos/text

---

### Prompt 2 — Desk Scene (Flat Lay, Multi-Object)
**Goal:** Test multi-object placement and composition in a realistic top-down scene.

**What it tests**
- Object presence and completeness (all required objects included)
- Layout control (no overlaps; all fully visible)
- Lighting consistency (soft daylight, coherent shadows)
- Cleanliness constraints (no logos, no readable brand text)

**Expected strong output characteristics**
- Clear top-down view on light wooden desk
- Exactly the specified objects (no extras)
- Tidy, realistic arrangement; all objects separated and fully visible

---

### Prompt 3 — Exact Count + Minimal Text
**Goal:** Test fine-grained prompt adherence: exact object counting and minimal text rendering.

**What it tests**
- Exact-count constraint (exactly 7 visible paperclips)
- Separation and visibility (not stacked; clearly separable)
- Minimal text accuracy (sticky note text, uppercase, no extra text)
- Controlled background and lighting

**Expected strong output characteristics**
- Exactly 7 identical silver paperclips, all visible and separate
- One yellow sticky note
- Sticky note text exactly: `MEETING AT 3` (uppercase)
- No other text anywhere in the image

---

### Prompt 4 — TODO: Photo Editing / Image-to-Image Evaluation
**Purpose (planned):** Evaluate image editing capability (e.g., background removal, object removal, lighting correction) on a provided input image.

**TODO**
- Select a single input photo (product photo on cluttered background is recommended for objective scoring).
- Define a deterministic edit task (e.g., replace background with pure white + preserve realistic shadow).
- Add pass/fail checks (subject preserved, no added objects/text, clean edges, natural shadow).