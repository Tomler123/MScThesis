# Code Generation Evaluation Tool

A Flask-based dashboard for evaluating and comparing AI-generated Python code. Built as part of the MSc thesis:

> *Understanding and Comparing Generative AI Models: Capabilities, Domains, and Identifying the Best Models for Specific Use Cases*

All code metrics are computed using **Python's standard library only** (`ast`, `tokenize`, `re`, `difflib`, `math`) — no external analysis libraries.

---

## Quick Start

```bash
pip install flask requests
python app.py
# Open http://localhost:5000
```

---

## Project Structure

```
CodingEvaluationTool/
├── app.py                          # Flask backend + API routes
├── requirements.txt                # flask, requests
├── evaluators/
│   ├── metrics.py                  # All deterministic code metrics
│   ├── constraint_checker.py       # Prompt constraint extraction & checking
│   └── llm_judge.py                # LLM-as-Judge via Groq API
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    └── index.html                  # Single-page dark dashboard UI
```

---

## Metrics (`evaluators/metrics.py`)

### Lines of Code

| Metric | Description |
|---|---|
| `total_loc` | Total line count |
| `sloc` | Source lines (excluding blank, comment, docstring) |
| `blank_lines` | Blank line count |
| `comment_lines` | Lines starting with `#` |
| `docstring_lines` | Lines inside docstrings (detected via AST) |
| `code_to_comment_ratio` | SLOC / (comment + docstring lines) |

### Cyclomatic Complexity (McCabe)

Counts decision points: `if`, `for`, `while`, `and`, `or`, `ExceptHandler`, `with`, `Assert`, ternary expressions, and comprehension generators. CC = 1 + decision_points.

Risk categories: `low` (≤5), `moderate` (≤10), `high` (≤20), `very_high` (>20).

### Halstead Metrics

Computed from tokenized code (operators and operands extracted via `tokenize`):

| Metric | Formula |
|---|---|
| Vocabulary (n) | n₁ + n₂ (unique operators + operands) |
| Length (N) | N₁ + N₂ (total operators + operands) |
| Volume | N × log₂(n) |
| Difficulty | (n₁/2) × (N₂/n₂) |
| Effort | Difficulty × Volume |
| Time | Effort / 18 (seconds) |
| Bug Estimate | Volume / 3000 |

### AST Structural Metrics

Full AST traversal via `ast.walk`:

- `ast_node_count` — total AST nodes
- `ast_max_depth` — maximum tree depth
- `ast_avg_branching_factor` — mean children per non-leaf node
- `ast_node_types` — top-15 node type frequency distribution

### Maintainability Index (Microsoft variant)

```
MI = max(0, (171 − 5.2·ln(V) − 0.23·CC − 16.2·ln(LOC)) × 100 / 171)
```

Ratings: `highly_maintainable` (≥85), `moderately_maintainable` (≥65), `low_maintainability` (≥40), `unmaintainable` (<40).

### Code Similarity (vs. reference solution)

| Metric | Method |
|---|---|
| `jaccard_similarity` | Token set intersection / union |
| `sequence_match_ratio` | `difflib.SequenceMatcher` on raw source |
| `structural_similarity` | `SequenceMatcher` on AST node type sequences |
| `token_sequence_similarity` | `SequenceMatcher` on ordered token lists |
| `combined_similarity` | Weighted average (0.25/0.30/0.25/0.20) |

### Structure Metrics

- Function, class, method, async function, lambda counts
- `docstring_coverage` — % of definitions with docstrings
- `type_hint_coverage` — % of functions with parameter or return annotations

### Nesting Depth

Tracks depth of `if`, `for`, `while`, `with`, `try`, `ExceptHandler` nesting. Reports max and average depth.

### Identifier Quality

- `avg_identifier_length` — mean length of all non-dunder identifiers
- `single_char_ratio` — % of identifiers with length 1
- `snake_case_ratio` — % of identifiers matching `[a-z_][a-z0-9_]*`

### Import Analysis

Classifies all `import` and `from ... import` statements as stdlib or external using a built-in stdlib allowlist. Reports `uses_external_libs` flag.

### Error Handling

Counts `try` blocks, `except` handlers, bare `except` clauses, `raise` statements, and `assert` statements.

### DRY Score

Detects duplicate consecutive line blocks (minimum size 3) using a sliding window. `dry_score = 100 − (duplicate_lines / total_lines × 100)`.

### Test Case Execution

Executes assertion blocks extracted from the prompt directly against the submitted code in an isolated `exec` namespace. Reports:
- `total` — assertions attempted
- `passed` / `failed` / `errors` — counts
- `pass_rate` — percentage
- `details` — per-assertion status and error message

### Quality Score (Composite)

Weighted composite across categories (0–100):

| Category | Weight |
|---|---|
| Test Pass Rate | 35% |
| Maintainability Index | 15% |
| Documentation Coverage | 15% |
| Similarity to Reference | 15% |
| Cyclomatic Complexity (inverted) | 10% |
| Code Structure (nesting penalty) | 5% |
| DRY Score | 5% |

---

## Constraint Checker (`evaluators/constraint_checker.py`)

Parses the original prompt text to extract checkable constraints and then verifies them against the submitted code.

### Extracted Constraint Types

| Constraint | Detection Method |
|---|---|
| **Function signatures** | Regex on `def name(params) -> type:` patterns in prompt |
| **Class names** | Regex on `class Name` in prompt |
| **Docstrings required** | Keyword match (`"add a docstring"`, `"add docstrings"`, etc.) |
| **Type hints required** | Keyword match (`"type hint"`, `"add type hints"`, etc.) |
| **No external libraries** | Keyword match + AST import check |
| **Forbidden functions** | Patterns like `"do not use eval()"`, `"don't use sort"` |
| **Must raise ValueError** | Keyword match → AST `ast.Raise` node verification |
| **Preserve signatures** | Keyword match (`"do not change the function signature"`) |
| **Edge case handling** | Heuristic: empty-input guards, boundary checks, early returns |
| **Stable sort** | Keyword match (`"stable"` + `"sort"` in prompt) |
| **Test case extraction** | Extracts assertion blocks from fenced code sections |

### Task Type Detection

Automatically classifies the prompt as: `implementation`, `debugging`, `optimization`, or `design` based on keyword presence.

### Check Results

Returns per-constraint `pass` / `fail` / `partial` status with detail messages, plus an overall constraint score (passed / total × 100).

---

## LLM-as-Judge (`evaluators/llm_judge.py`)

Uses **Groq API** (`llama-3.3-70b-versatile`) for qualitative code evaluation. The function is named `evaluate_with_gemini` for historical compatibility but calls Groq exclusively.

### Evaluation Dimensions (1–10)

1. Correctness
2. Completeness
3. Code Quality
4. Edge Case Handling
5. Documentation
6. Efficiency
7. Error Handling
8. Adherence to Constraints

Returns `overall_score`, `summary`, `strengths`, `weaknesses`, and `suggestions` as structured JSON.

An optional **reference solution** can be included in the evaluation context.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the dashboard UI |
| `POST` | `/api/evaluate` | Evaluates a single code submission (all metrics) |
| `POST` | `/api/llm-judge` | Calls LLM-as-Judge for a code submission |
| `POST` | `/api/export` | Exports results as CSV or JSON |

---

## Notes

- The tool uses a **3-step wizard** in the UI: (1) enter prompt + code, (2) view automated metrics, (3) run LLM judge.
- The Groq API key (starting with `gsk_`) is entered in the browser and is never stored server-side.
- All test execution happens in an isolated `exec` namespace; `math` and `isclose` are injected automatically for prompts that require them.
- The `constraint_checker` is best-effort — it uses regex and keyword matching, so highly unconventional prompt phrasings may not be detected.