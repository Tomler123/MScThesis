# Coding Assistance (Python) — Prompts (Domain 4)

This folder contains evaluation prompts for the **Coding Assistance (Python)** domain.
The prompts are designed to support **objective correctness checks** (via unit tests) and qualitative scoring for:
- **Readability / maintainability**
- **Explanation quality**
- **Edge case handling**

## Files
- `prompt1.txt` — Implement `split_csv_line` (CSV-style parsing with quotes/escaping) + tests
- `prompt2.txt` — Fix `is_balanced` (brackets balanced, ignore content inside quotes with escape handling) + tests
- `prompt3.txt` — Refactor `score_password` for readability without changing behavior + tests

## Prompt descriptions

### Prompt 1 — CSV Line Parser (Implementation + Tests)
**Goal:** Evaluate algorithmic implementation skill and handling of tricky parsing rules.

**What it tests**
- Correct state-machine style parsing (commas vs quoted commas)
- Handling escaped quotes (`""` inside quoted fields)
- Exact string handling (preserve whitespace inside fields)
- Constraint compliance (no `csv` module; no external libraries)
- Code quality: type hints, docstring, clarity

**Objective evaluation**
- All provided `assert` tests pass exactly.

**Expected strong output characteristics**
- Clear state variables (e.g., `in_quotes`)
- Correct unescaping of `""` → `"`
- Correct splitting only on commas outside quotes
- Clean, readable code and brief explanation of edge cases

---

### Prompt 2 — Balanced Brackets with Quoted-Text Ignoring (Bug Fix + Tests)
**Goal:** Evaluate debugging skill and correctness under special-case rules.

**What it tests**
- Identifying and fixing bugs without changing the signature
- Correct bracket matching with a stack
- Correct handling of quoted regions
- Correct handling of escaped quotes (`\"`) so quoting state is not toggled incorrectly
- Explanation of original bug(s) and reasoning behind the fix

**Objective evaluation**
- All provided `assert` tests pass exactly.

**Expected strong output characteristics**
- Correct detection of escaped quotes (e.g., tracking previous backslash or scanning indices)
- Brackets ignored only inside quotes; validated outside
- Clear explanation of failure modes in the original implementation

---

### Prompt 3 — Refactor for Readability (Behavior-Preserving)
**Goal:** Evaluate code improvement skills while keeping behavior identical.

**What it tests**
- Refactoring without changing outputs
- Readability: naming, structure, reduced nesting
- Adding type hints and docstring
- Preserving all edge cases and exact scoring logic

**Objective evaluation**
- All provided `assert` tests pass exactly.

**Expected strong output characteristics**
- Early returns where appropriate
- Meaningful variable names
- Equivalent logic with cleaner structure
- Brief bullet list explaining improvements