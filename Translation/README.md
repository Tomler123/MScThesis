# Translation — Prompts

This folder contains evaluation prompts for the **Translation** domain.
The prompts focus on:
- **Meaning preservation** (no omissions, additions, or distortions)
- **Fluency** (natural, grammatical output in the target language)
- **Tone preservation** (professional and polite register)
- **Consistency of named entities and time expressions** (e.g., keeping “Beta Research”, “5 PM today”, “tomorrow morning”)

## Files
- `prompt1.txt` — English → Russian
- `prompt2.txt` — Russian → English
- `prompt3.txt` — English → Italian
- `prompt4.txt` — Italian → English
- `prompt5.txt` — English → Georgian
- `prompt6.txt` — Georgian → English

## Shared template text (English source)
All **English → Foreign Language** prompts use the same English input to ensure comparability:

> Please confirm whether you can send the revised document by 5 PM today. If that is not possible, suggest an alternative time and briefly explain the reason for the delay. This update is needed for a meeting with the Beta Research team tomorrow morning, so clarity is important.

All **Foreign Language → English** prompts use translations of the same template text in the corresponding language.

## Prompt design rationale
Each prompt includes constraints intended to make evaluation more objective:
- Preserve meaning without introducing new information
- Keep the register professional/polite
- Preserve time expressions and the proper noun **Beta Research** exactly