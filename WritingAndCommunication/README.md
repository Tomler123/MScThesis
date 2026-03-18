# Writing & Communication - Prompts

This folder contains evaluation prompts for the **Writing & Communication** domain.
Each prompt is designed to test controlled writing quality under explicit constraints.

## Files
- `prompt1.txt` — Professional email rewrite with strict constraints
- `prompt2.txt` — Audience adaptation (technical teammate vs non-technical manager)
- `prompt3.txt` — Internal maintenance announcement with fixed headings and hard rules

## Prompt descriptions

### Prompt 1 — Professional Email (Polite but Firm)
**Goal:** Assess professional tone, concision, and strict constraint compliance in email writing.

**What it tests**
- Tone control (polite, firm, non-accusatory language)
- Structure control (subject line, paragraph count, word limits)
- Instruction following (forbidden words, required deadline phrase, required next step)
- Clarity and actionability (clear ask + deadline)

**Expected strong output characteristics**
- Subject ≤ 8 words; body 110–130 words
- Exactly 3 paragraphs, no bullets
- Includes "by 5 PM today" and one clear next step
- Professional tone; no banned words; no blame

---

### Prompt 2 — Audience Adaptation (Two Audiences)
**Goal:** Assess the model’s ability to communicate the same update to two audiences with different language constraints.

**What it tests**
- Audience awareness (technical vs non-technical phrasing)
- Controlled vocabulary (exactly two allowed technical terms in A; zero in B)
- Consistency of meaning (both communicate the same core update)
- Structure and length control (90–110 words each, no bullets)
- Actionability + confidence statement inclusion

**Expected strong output characteristics**
- Both messages meet word limits
- A includes exactly two terms from: {regression, deployment, patch, QA, rollback}
- B includes none of those terms
- Each message includes exactly one sentence explaining the reason for delay
- Both include a next step and a confidence statement

---

### Prompt 3 — Maintenance Announcement (Fixed Headings)
**Goal:** Assess structured communication with rigid formatting and content placement rules.

**What it tests**
- Schema compliance (exact headings in order)
- Sentence counting (exactly 2 sentences per heading)
- Content placement (time window phrase, duration, impact details, contact)
- Action formatting (exactly 3 actions in one sentence separated by semicolons)
- Word count control (150–190 words), neutral tone, no apologies

**Expected strong output characteristics**
- Exactly 5 headings in the required order
- Exactly 2 sentences per heading (10 total)
- "Time Window" contains "next Tuesday" and "2 hours"
- "Impact" mentions unavailability and slow performance
- "Action Required" has exactly 3 semicolon-separated actions (no bullets)
- "Contact" includes `support@example.com`