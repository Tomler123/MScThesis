# Coding Assistant — Prompts & Evaluation Data

This folder contains the prompts, model responses, automated evaluation scores, and LLM judge verdicts for the **Coding Assistance** domain of the thesis:

> *Understanding and Comparing Generative AI Models: Capabilities, Domains, and Identifying the Best Models for Specific Use Cases*

---

## Models Evaluated

- **ChatGPT** (GPT-4 / GPT-5 via chatgpt.com free tier with Thinking)
- **Claude** (claude.ai)
- **Gemini** (Google Gemini)
- **GLM** (Zhipu AI GLM)
- **MiniMax** (MiniMax)

Model versions and UI features used during evaluation are documented in `ModelsDescriptions/`.

---

## Folder Structure

```
CodingAssistant/
├── prompt_01_*.txt                       # 10 prompt definitions (see below)
├── ...
├── prompt_10_*.txt
│
├── Responses_Prompt1/                    # Per-model responses for Prompt 1
│   ├── ChatGPT/
│   │   ├── chatgpt_response.txt          # Full model response (explanation + code)
│   │   └── main.py                       # Extracted code file
│   ├── Claude/
│   ├── Gemini/
│   ├── GLM/
│   └── MiniMax/
│
├── Responses_Prompt2/ ... Responses_Prompt10/   # Same structure for all 10 prompts
│
├── AutomatedScores/                      # CSV output from the Code Evaluation Tool
│   ├── code_evaluation_results_1.csv
│   ├── ...
│   └── code_evaluation_results_10.csv
│
├── LLM_Judge/                            # LLM-as-Judge verdicts (Groq / Llama-3.3-70B)
│   ├── prompt1_LLM_Judge.txt
│   ├── ...
│   └── prompt10_LLM_Judge.txt
│
└── ModelsDescriptions/                   # Notes on model versions and UI features used
    ├── chatgpt_response.txt
    ├── claude_response.txt
    ├── gemini_response.txt
    ├── glm_response.txt
    └── minimax_response.txt
```

---

## Prompts

The 10 prompts span **3 task types** and **3 difficulty tiers**, designed to test different aspects of code generation capability.

### Task Types

| Type | Description |
|---|---|
| **Implementation** | Write a function/class from scratch meeting a detailed specification |
| **Debugging** | Find and fix all bugs in a provided broken implementation |
| **Optimization** | Rewrite a correct but inefficient solution to meet a complexity target |

### Difficulty Tiers

| Tier | Prompts |
|---|---|
| **Easy** | 1–2 |
| **Medium** | 3–6 |
| **Hard** | 7–10 |

---

### Prompt 1 — Flatten Nested Dictionary *(Easy / Implementation)*
Implement `flatten_dict(d, sep)` that recursively flattens nested dictionaries by joining keys with a separator. Must handle deep nesting, non-dict values, empty nested dicts, and custom separators. Includes 10 assertion-based test cases.

---

### Prompt 2 — Run-Length Encoding & Decoding *(Easy / Implementation)*
Implement `rle_encode(s)` and `rle_decode(s)` for run-length compression. Must support multi-digit counts, the roundtrip property `rle_decode(rle_encode(s)) == s`, and handle empty strings. Includes 12 test cases plus roundtrip property checks.

---

### Prompt 3 — Fix Buggy Merge Sort *(Medium / Debugging)*
A broken `merge_sort` + `merge` pair is provided with two deliberate bugs. Models must identify and fix all bugs without changing the function signatures, preserve sort stability, and explain each bug found. Includes 10 test cases covering edge cases (empty, duplicates, negatives, already sorted).

---

### Prompt 4 — Merge Overlapping Intervals *(Medium / Implementation)*
Implement `merge_intervals(intervals)` that merges all overlapping `(start, end)` tuples into a sorted non-overlapping list. Must handle unsorted input, fully nested intervals, point intervals, and duplicate intervals. Includes 12 test cases. Requires a time complexity explanation.

---

### Prompt 5 — EventEmitter Class *(Medium / Design / OOP)*
Implement an `EventEmitter` class with `on`, `off`, `once`, and `emit` methods. Key requirements include: duplicate callback registration, one-at-a-time removal via `off`, auto-removal after `once` fires during live iteration, and no error on unknown events. Includes 9 multi-step test scenarios.

---

### Prompt 6 — Optimize Group Anagrams *(Medium–Hard / Optimization)*
A brute-force O(n² · k) `group_anagrams_brute` is provided. Models must rewrite it to O(n · k log k) using a hash-map approach while preserving input order within groups and across group first-appearances. Case-sensitive matching required. Includes 8 test cases plus a complexity explanation requirement.

---

### Prompt 7 — Math Expression Evaluator *(Medium–Hard / Multi-Step Reasoning)*
Implement `evaluate(expression)` that evaluates arithmetic strings with `+`, `-`, `*`, `/`, parentheses, and unary minus — without using `eval()`, `exec()`, or any parsing library. Must respect standard operator precedence, left-to-right associativity, and raise `ValueError` for malformed input and division by zero. Includes 16 valid expressions and 4 error cases.

---

### Prompt 8 — Fix Buggy Dependency Task Scheduler *(Hard / Debugging)*
A DFS-based topological sort with multiple subtle bugs — including incorrect cycle detection (no distinction between "in progress" and "fully visited" states) and wrong execution order — is provided. Models must fix all bugs, handle tasks not explicitly in the dict, deduplicate output, and explain the two-color DFS states. Includes 10 test scenarios including cycle detection and diamond dependency patterns.

---

### Prompt 9 — In-Memory Text Search Index *(Hard / Design / Algorithm)*
Implement a `SearchIndex` class with `add`, `search`, and `remove` methods backed by an inverted index. `search` must support AND multi-term queries, rank results by total term frequency (descending), break ties lexicographically, and handle document replacement. Tokenization splits on non-alphanumeric characters and lowercases. Includes 15 test assertions covering edge cases, case insensitivity, and tie-breaking.

---

### Prompt 10 — Configuration Parser with Inheritance *(Hard / Ambiguous Specification)*
Implement `parse_config(text)` that parses an INI-like configuration language with sections, nested sections via `[parent.child]`, section inheritance via `[section : parent]`, type auto-conversion (int, float, bool, null, string), comment handling, and duplicate key resolution (last wins). The specification is intentionally partially ambiguous to test model judgment. Includes 7 test configurations.

---

## Evaluation Data

### Automated Scores (`AutomatedScores/`)

Each CSV file corresponds to one prompt and contains per-model metric scores computed by the Code Evaluation Tool. The leaderboard section at the top of each file ranks models by a composite rank score. Metrics include:

| Category | Metrics |
|---|---|
| **Test Execution** | Pass rate (%), passed / failed / error counts per assertion |
| **Complexity** | Cyclomatic complexity (McCabe), risk category |
| **Halstead** | Volume, difficulty, effort, time, bug estimate, vocabulary, length |
| **Maintainability** | Maintainability Index (Microsoft variant), MI rating |
| **AST Structure** | Node count, max depth, avg branching factor, node type distribution |
| **Lines of Code** | Total LOC, SLOC, blank lines, comment lines, docstring lines, code-to-comment ratio |
| **Nesting** | Max and avg nesting depth of control structures |
| **Documentation** | Docstring coverage (%), type hint coverage (%) |
| **Identifiers** | Total count, avg length, single-char ratio, snake_case ratio |
| **Imports** | Import count, external vs stdlib classification |
| **Error Handling** | Try/except blocks, raise statements, bare excepts, asserts |
| **DRY Score** | Duplicate block detection, duplicate line count |
| **Similarity** | Token Jaccard, SequenceMatcher ratio, AST structural similarity (vs reference) |
| **Constraint Adherence** | Auto-parsed constraint checks (signatures, docstrings, type hints, forbidden functions, etc.) |
| **Composite / Quality Score** | Weighted composite across test pass rate, maintainability, complexity, documentation, DRY, similarity |

### LLM Judgements (`LLM_Judge/`)

Each file contains the LLM-as-Judge evaluation (via Groq API, `llama-3.3-70b-versatile`) for all models on a given prompt. Each model is scored on 8 dimensions (1–10):

1. Correctness
2. Completeness
3. Code Quality
4. Edge Case Handling
5. Documentation
6. Efficiency
7. Error Handling
8. Adherence to Constraints

Plus an overall score, a 2–3 sentence summary, and lists of strengths, weaknesses, and suggestions.

---

## Key Design Decisions

- Each `Responses_PromptN/` folder contains both the **raw model response** (explanation + code as returned) and the **extracted `main.py`** used for automated metric computation. This separation allows evaluating the code independently of the surrounding explanation.
- The 3-task-type × 3-difficulty grid was designed so that no domain skill is tested only once — each type appears at multiple difficulty levels.
- Prompt 10's intentional ambiguity was included to test whether models acknowledge and resolve unclear specifications explicitly.
- Models are evaluated on the same prompts without any system-level customization to ensure comparability.