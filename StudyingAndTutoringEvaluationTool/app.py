"""
Study & Tutoring AI Evaluation Tool
MSc Thesis - Generative AI Model Comparison
Domain: Studying and Tutoring (Direct Instruction)
"""

import json
import math
import re
import os
import csv
import io
import statistics
from collections import Counter
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

# ============================================================
# STORAGE
# ============================================================
evaluations = {}  # model_name -> { prompt_type, response_text, scores... }
eval_history = []  # list of all evaluations for export


# ============================================================
# TEXT UTILITIES (no external NLP libs)
# ============================================================

def tokenize(text):
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r"[A-Za-z0-9]+(?:'[a-z]+)?", text.lower())


def sent_tokenize(text):
    """Sentence splitter using regex."""
    sents = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
    return [s.strip() for s in sents if len(s.strip()) > 5]


def syllable_count(word):
    """Estimate syllable count for readability."""
    word = word.lower().strip()
    if len(word) <= 2:
        return 1
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith('e') and count > 1:
        count -= 1
    return max(1, count)


# ============================================================
# NLP / DATA-SCIENCE METRICS
# ============================================================

def calc_readability(text):
    """Flesch-Kincaid Grade Level and Flesch Reading Ease."""
    words = tokenize(text)
    sents = sent_tokenize(text)
    if not words or not sents:
        return {"fk_grade": 0, "flesch_ease": 0}
    total_syllables = sum(syllable_count(w) for w in words)
    avg_sent_len = len(words) / len(sents)
    avg_syl = total_syllables / len(words)
    fk_grade = 0.39 * avg_sent_len + 11.8 * avg_syl - 15.59
    flesch_ease = 206.835 - 1.015 * avg_sent_len - 84.6 * avg_syl
    return {
        "fk_grade": round(max(0, fk_grade), 2),
        "flesch_ease": round(max(0, min(100, flesch_ease)), 2)
    }


def calc_lexical_diversity(text):
    """Type-Token Ratio, Hapax Legomena Ratio, Vocabulary Richness."""
    words = tokenize(text)
    if not words:
        return {"ttr": 0, "hapax_ratio": 0, "vocab_richness": 0}
    freq = Counter(words)
    types = len(freq)
    tokens = len(words)
    hapax = sum(1 for w, c in freq.items() if c == 1)
    ttr = types / tokens
    hapax_ratio = hapax / types if types else 0
    # Yule's K approximation
    vocab_richness = 10000 * (sum(c * c for c in freq.values()) - tokens) / (tokens * tokens) if tokens > 1 else 0
    return {
        "ttr": round(ttr, 4),
        "hapax_ratio": round(hapax_ratio, 4),
        "vocab_richness": round(vocab_richness, 4)
    }


def calc_structural_metrics(text):
    """Detect structural elements in the response."""
    lines = text.strip().split('\n')
    non_empty = [l for l in lines if l.strip()]

    # Headers / section markers
    header_patterns = [
        r'^#{1,4}\s',            # Markdown headers
        r'^\*\*[^*]+\*\*',       # Bold lines
        r'^[A-Z][^.]{3,60}:$',   # "Section Name:"
        r'^\d+\.\s+[A-Z]',      # "1. Section"
        r'^(?:Key Ideas|Worked Example|Practice Exercise|Solution|Step|Part)', # Domain-specific
    ]
    headers = sum(1 for l in non_empty if any(re.match(p, l.strip()) for p in header_patterns))

    # Bullet / numbered list items
    bullets = sum(1 for l in non_empty if re.match(r'^\s*[-•*]\s', l.strip()))
    numbered = sum(1 for l in non_empty if re.match(r'^\s*\d+[.)]\s', l.strip()))

    # Code blocks
    code_blocks = len(re.findall(r'```', text)) // 2

    # Paragraphs (blocks of text separated by blank lines)
    paragraphs = len(re.split(r'\n\s*\n', text.strip()))

    return {
        "total_lines": len(non_empty),
        "headers": headers,
        "bullets": bullets,
        "numbered_items": numbered,
        "code_blocks": code_blocks,
        "paragraphs": paragraphs
    }


def calc_math_formula_metrics(text):
    """Detect mathematical expressions, equations, LaTeX."""
    # LaTeX inline/display
    latex_inline = len(re.findall(r'\$[^$]+\$', text))
    latex_display = len(re.findall(r'\$\$[^$]+\$\$', text))
    latex_env = len(re.findall(r'\\(?:frac|sqrt|sum|int|lim|begin|end|alpha|beta|lambda|omega|theta|pi|Delta|nabla|partial|infty|rightarrow|Rightarrow|leq|geq|neq|approx|equiv|cdot|times|div)', text))

    # Plain-text math patterns
    equations = len(re.findall(r'[a-zA-Z_]\s*=\s*[^,\n]{2,}', text))
    operators = len(re.findall(r'[+\-*/^]=|[≤≥≠±∑∫∏√∞]', text))
    numeric_exprs = len(re.findall(r'\d+\s*[+\-*/^]\s*\d+', text))
    superscripts = len(re.findall(r'\^[{(]?\d+|²|³', text))
    greek_letters = len(re.findall(r'(?:alpha|beta|gamma|delta|epsilon|lambda|omega|theta|phi|psi|sigma|mu|pi|rho|tau|eta|zeta|nu|xi|kappa|chi)', text, re.I))

    total_math = latex_inline + latex_display + latex_env + equations + operators + numeric_exprs + superscripts + greek_letters

    return {
        "latex_expressions": latex_inline + latex_display,
        "latex_commands": latex_env,
        "equations": equations,
        "math_operators": operators,
        "numeric_expressions": numeric_exprs,
        "greek_letters": greek_letters,
        "total_math_elements": total_math
    }


def calc_explanation_depth(text):
    """Measure explanation quality indicators."""
    words = tokenize(text)
    sents = sent_tokenize(text)
    word_count = len(words)
    sent_count = len(sents)

    # Transition / reasoning markers
    reasoning_markers = [
        'therefore', 'thus', 'hence', 'because', 'since', 'so', 'consequently',
        'as a result', 'this means', 'it follows', 'implies', 'leads to',
        'in other words', 'that is', 'namely', 'specifically',
        'first', 'second', 'third', 'next', 'then', 'finally', 'step',
        'note that', 'recall', 'observe', 'notice', 'consider',
        'for example', 'for instance', 'such as', 'e.g.', 'i.e.',
        'in particular', 'importantly', 'crucially', 'key', 'the reason',
        'we can see', 'we get', 'we obtain', 'we find', 'we have',
        'substituting', 'plugging in', 'applying', 'using', 'by',
        'simplifying', 'rearranging', 'solving', 'computing', 'calculating',
        'this gives', 'which gives', 'which yields', 'resulting in'
    ]
    text_lower = text.lower()
    reasoning_count = sum(text_lower.count(m) for m in reasoning_markers)

    # Definition patterns
    definition_patterns = [
        r'is defined as', r'refers to', r'means that', r'is called',
        r'is known as', r'we define', r'definition:', r'denotes'
    ]
    definitions = sum(len(re.findall(p, text_lower)) for p in definition_patterns)

    # Example markers
    example_markers = ['example', 'worked example', 'illustration', 'consider the following',
                       'practice exercise', 'exercise', 'let us', "let's"]
    example_count = sum(text_lower.count(m) for m in example_markers)

    # Step-by-step indicators
    step_patterns = len(re.findall(r'(?:step\s*\d|step\s*[a-z]\b|\(\s*[a-d]\s*\)|\([ivx]+\))', text_lower))

    # Pedagogical density = reasoning markers per sentence
    ped_density = reasoning_count / sent_count if sent_count else 0

    return {
        "word_count": word_count,
        "sentence_count": sent_count,
        "reasoning_markers": reasoning_count,
        "definitions": definitions,
        "examples_mentioned": example_count,
        "step_indicators": step_patterns,
        "pedagogical_density": round(ped_density, 3),
        "avg_sentence_length": round(word_count / sent_count, 1) if sent_count else 0
    }


def calc_terminology_accuracy(text, prompt_type):
    """Score domain-specific terminology usage density."""
    text_lower = text.lower()
    words = tokenize(text)

    # General STEM tutoring terms
    general_terms = [
        'equation', 'formula', 'variable', 'constant', 'coefficient', 'function',
        'solution', 'result', 'proof', 'theorem', 'definition', 'property',
        'derive', 'derivation', 'substitute', 'simplify', 'compute', 'calculate',
        'expression', 'inequality', 'identity', 'condition', 'assumption',
        'parameter', 'domain', 'range', 'vector', 'matrix', 'scalar', 'set'
    ]

    # Math-specific
    math_terms = [
        'eigenvalue', 'eigenvector', 'characteristic', 'polynomial', 'determinant',
        'matrix', 'linear', 'algebra', 'null space', 'span', 'basis', 'dimension',
        'diagonal', 'trace', 'transpose', 'inverse', 'rank', 'kernel'
    ]

    # CS-specific
    cs_terms = [
        'big-o', 'complexity', 'asymptotic', 'algorithm', 'runtime', 'recurrence',
        'recursion', 'recursive', 'master theorem', 'merge sort', 'time complexity',
        'worst case', 'logarithmic', 'quadratic', 'linear', 'constant', 'loop',
        'iteration', 'pseudocode', 'input size', 'divide and conquer'
    ]

    # Physics-specific
    physics_terms = [
        'harmonic', 'oscillation', 'frequency', 'angular', 'amplitude', 'period',
        'displacement', 'velocity', 'acceleration', 'spring constant', 'mass',
        'equilibrium', 'restoring force', 'kinetic energy', 'potential energy',
        'differential equation', 'phase', 'friction', 'newton'
    ]

    # Chemistry-specific
    chem_terms = [
        'equilibrium', 'reaction', 'concentration', 'le chatelier', 'ice table',
        'stoichiometry', 'molar', 'products', 'reactants', 'constant', 'shift',
        'exothermic', 'endothermic', 'pressure', 'temperature', 'catalyst'
    ]

    all_domain = math_terms + cs_terms + physics_terms + chem_terms
    found_general = sum(1 for t in general_terms if t in text_lower)
    found_domain = sum(1 for t in all_domain if t in text_lower)
    total_found = found_general + found_domain
    term_density = total_found / len(words) * 100 if words else 0

    return {
        "general_terms_found": found_general,
        "domain_terms_found": found_domain,
        "total_terms_found": total_found,
        "terminology_density": round(term_density, 3)
    }


def calc_coherence_score(text):
    """Estimate textual coherence via adjacent sentence similarity (word overlap)."""
    sents = sent_tokenize(text)
    if len(sents) < 2:
        return {"coherence_score": 1.0, "avg_sentence_overlap": 1.0}

    overlaps = []
    for i in range(len(sents) - 1):
        w1 = set(tokenize(sents[i]))
        w2 = set(tokenize(sents[i + 1]))
        if w1 and w2:
            overlap = len(w1 & w2) / min(len(w1), len(w2))
            overlaps.append(overlap)

    avg_overlap = statistics.mean(overlaps) if overlaps else 0
    # Coherence: moderate overlap is best (too high = repetitive, too low = incoherent)
    # Optimal around 0.15-0.35
    coherence = 1.0 - abs(avg_overlap - 0.25) * 2
    coherence = max(0, min(1, coherence))

    return {
        "coherence_score": round(coherence, 4),
        "avg_sentence_overlap": round(avg_overlap, 4)
    }


def calc_passive_voice_ratio(text):
    """Estimate passive voice usage (approximation without POS tagger)."""
    passive_patterns = [
        r'\b(?:is|are|was|were|be|been|being)\s+\w+ed\b',
        r'\b(?:is|are|was|were|be|been|being)\s+\w+en\b',
        r'\b(?:is|are|was|were)\s+(?:known|given|defined|called|determined|found|shown|obtained|derived|computed|calculated)\b'
    ]
    sents = sent_tokenize(text)
    passive_count = 0
    for s in sents:
        for p in passive_patterns:
            if re.search(p, s, re.I):
                passive_count += 1
                break
    ratio = passive_count / len(sents) if sents else 0
    return {
        "passive_sentences": passive_count,
        "total_sentences": len(sents),
        "passive_ratio": round(ratio, 4)
    }


def calc_information_density(text):
    """Information density metrics: content words ratio, unique bigrams, etc."""
    words = tokenize(text)
    if not words:
        return {"content_word_ratio": 0, "unique_bigram_ratio": 0, "info_density_score": 0}

    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
        'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'out', 'off', 'up',
        'down', 'and', 'but', 'or', 'nor', 'not', 'so', 'yet', 'both',
        'either', 'neither', 'each', 'every', 'all', 'any', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'only', 'own', 'same', 'than',
        'too', 'very', 'just', 'about', 'this', 'that', 'these', 'those',
        'it', 'its', 'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he',
        'him', 'his', 'she', 'her', 'they', 'them', 'their', 'what', 'which',
        'who', 'whom', 'when', 'where', 'why', 'how', 'if', 'then', 'else',
        'also', 'here', 'there'
    }

    content_words = [w for w in words if w not in stop_words]
    content_ratio = len(content_words) / len(words)

    bigrams = [(words[i], words[i + 1]) for i in range(len(words) - 1)]
    unique_bigrams = len(set(bigrams))
    bigram_ratio = unique_bigrams / len(bigrams) if bigrams else 0

    info_density = (content_ratio * 0.5 + bigram_ratio * 0.5)

    return {
        "content_word_ratio": round(content_ratio, 4),
        "unique_bigram_ratio": round(bigram_ratio, 4),
        "info_density_score": round(info_density, 4)
    }


# ============================================================
# CONSTRAINT CHECKER
# ============================================================

def check_constraints(text, prompt_type):
    """Parse structural requirements from prompt type and check compliance."""
    checks = []
    text_lower = text.lower()

    # Common to both prompt types:
    # 1. Must have "Key Ideas" or conceptual explanation section
    # 2. Must have worked example (Teach) or complete solution (Solve)
    # 3. Must have exactly 2 practice exercises with solutions

    if prompt_type == "teach":
        # Check for Key Ideas section
        has_key_ideas = bool(re.search(r'key\s*ideas?|concept|definition|what\s+(is|are)', text_lower))
        checks.append({
            "requirement": "Contains Key Ideas / Conceptual Explanation section",
            "met": has_key_ideas,
            "detail": "Found" if has_key_ideas else "Missing 'Key Ideas' or concept explanation section"
        })

        # Check for Worked Example
        has_worked = bool(re.search(r'worked\s*example|example|step[\s-]*by[\s-]*step|let\s+us\s+(?:find|compute|solve|calculate)', text_lower))
        checks.append({
            "requirement": "Contains Worked Example with step-by-step solution",
            "met": has_worked,
            "detail": "Found" if has_worked else "Missing worked example"
        })

    elif prompt_type == "solve":
        # Check for complete solution
        has_solution = bool(re.search(r'solution|solve|solving|we\s+(?:find|get|obtain|compute|have)|result|answer', text_lower))
        checks.append({
            "requirement": "Contains complete solution / derivation",
            "met": has_solution,
            "detail": "Found" if has_solution else "Missing complete solution"
        })

        # Check for step labeling (a), (b), (c)...
        part_labels = re.findall(r'\(\s*[a-d]\s*\)', text_lower)
        has_parts = len(part_labels) >= 2
        checks.append({
            "requirement": "Solution addresses labeled parts (a), (b), etc.",
            "met": has_parts,
            "detail": f"Found {len(part_labels)} labeled parts" if has_parts else "Missing part labels"
        })

        # Check for verification step
        has_verify = bool(re.search(r'verif|check|confirm|substitut.*back|plug.*back', text_lower))
        checks.append({
            "requirement": "Includes verification / checking step",
            "met": has_verify,
            "detail": "Found" if has_verify else "No verification step detected"
        })

    # Check for practice exercises (both types)
    exercise_patterns = [
        r'practice\s*exercise', r'exercise\s*\d', r'follow[\s-]*up\s*exercise',
        r'try\s+(this|these)', r'(?:exercise|problem)\s*(?:#?\s*)?[12]',
        r'(?:^|\n)\s*(?:\d+[\.\)]|[-•])\s*(?:find|compute|solve|determine|calculate|prove|show)',
    ]
    exercise_count = 0
    for p in exercise_patterns:
        exercise_count += len(re.findall(p, text_lower, re.MULTILINE))
    exercise_count = min(exercise_count, 10)  # cap
    has_exercises = exercise_count >= 2

    checks.append({
        "requirement": "Contains 2 practice exercises",
        "met": has_exercises,
        "detail": f"Detected ~{exercise_count} exercise indicators" if has_exercises else f"Only {exercise_count} exercise indicators found (need 2)"
    })

    # Check exercises have solutions
    solution_indicators = len(re.findall(r'solution|answer|result\s*[:=]|therefore.*=', text_lower))
    has_solutions = solution_indicators >= 2
    checks.append({
        "requirement": "Practice exercises include solutions",
        "met": has_solutions,
        "detail": f"Found {solution_indicators} solution indicators" if has_solutions else "Missing solutions for exercises"
    })

    # No Socratic questioning check
    question_to_student = re.findall(r'\?\s*$', text, re.MULTILINE)
    # Filter out rhetorical / setup questions
    direct_questions = [q for q in question_to_student if not re.search(r'what if|why does|how does|can we', text_lower)]
    excessive_questions = len(question_to_student) > 5
    checks.append({
        "requirement": "Avoids Socratic questioning (Direct Instruction style)",
        "met": not excessive_questions,
        "detail": "Good - direct instruction style" if not excessive_questions else f"Too many questions ({len(question_to_student)}) - may be Socratic"
    })

    # Mathematical content present
    math_metrics = calc_math_formula_metrics(text)
    has_math = math_metrics["total_math_elements"] >= 3
    checks.append({
        "requirement": "Contains mathematical expressions / equations",
        "met": has_math,
        "detail": f"{math_metrics['total_math_elements']} math elements found" if has_math else "Very few mathematical expressions"
    })

    # Adequate length
    word_count = len(tokenize(text))
    adequate_length = word_count >= 200
    checks.append({
        "requirement": "Response has adequate length (≥200 words)",
        "met": adequate_length,
        "detail": f"{word_count} words" if adequate_length else f"Only {word_count} words - too short"
    })

    met = sum(1 for c in checks if c["met"])
    total = len(checks)

    return {
        "checks": checks,
        "met": met,
        "total": total,
        "score": round(met / total * 100, 1) if total else 0
    }


# ============================================================
# COMPOSITE SCORING
# ============================================================

def compute_all_metrics(text, prompt_type):
    """Run all metrics and return a unified result dict."""
    readability = calc_readability(text)
    lexical = calc_lexical_diversity(text)
    structure = calc_structural_metrics(text)
    math = calc_math_formula_metrics(text)
    depth = calc_explanation_depth(text)
    terminology = calc_terminology_accuracy(text, prompt_type)
    coherence = calc_coherence_score(text)
    passive = calc_passive_voice_ratio(text)
    info_density = calc_information_density(text)
    constraints = check_constraints(text, prompt_type)

    # ---- Composite sub-scores (each 0-100) ----

    # 1. Readability Score: FK grade 10-16 is ideal for undergrad, ease 30-60
    fk = readability["fk_grade"]
    if 10 <= fk <= 16:
        read_score = 100
    elif fk < 10:
        read_score = max(0, 50 + (fk - 5) * 10)
    else:
        read_score = max(0, 100 - (fk - 16) * 15)

    # 2. Depth Score based on word count, reasoning markers, definitions, examples
    wc = depth["word_count"]
    depth_score = min(100, (
        min(30, wc / 30) +  # up to 30pts for length (900+ words)
        min(25, depth["reasoning_markers"] * 1.5) +
        min(15, depth["definitions"] * 5) +
        min(15, depth["examples_mentioned"] * 5) +
        min(15, depth["step_indicators"] * 3)
    ))

    # 3. Structure Score
    struct_score = min(100, (
        min(25, structure["headers"] * 6) +
        min(20, (structure["bullets"] + structure["numbered_items"]) * 2) +
        min(20, structure["paragraphs"] * 3) +
        min(15, math["total_math_elements"] * 2) +
        min(20, structure["code_blocks"] * 10 if prompt_type == "solve" else 0)
    ))

    # 4. Terminology Score
    term_score = min(100, terminology["total_terms_found"] * 4)

    # 5. Coherence Score (already 0-1, scale to 0-100)
    coh_score = coherence["coherence_score"] * 100

    # 6. Clarity Score: low passive voice + good info density + moderate sentence length
    clarity = 100
    if passive["passive_ratio"] > 0.4:
        clarity -= 20
    avg_sl = depth["avg_sentence_length"]
    if avg_sl > 35:
        clarity -= 15
    elif avg_sl < 8:
        clarity -= 10
    clarity = max(0, min(100, clarity + info_density["info_density_score"] * 30))

    # 7. Constraint compliance
    constraint_score = constraints["score"]

    # 8. Lexical diversity
    lex_score = min(100, lexical["ttr"] * 200)  # TTR of 0.5 = 100

    # ---- Weighted composite ----
    weights = {
        "depth": 0.20,
        "structure": 0.15,
        "terminology": 0.10,
        "coherence": 0.10,
        "readability": 0.10,
        "clarity": 0.10,
        "constraints": 0.15,
        "lexical_diversity": 0.10
    }

    sub_scores = {
        "depth": round(depth_score, 1),
        "structure": round(struct_score, 1),
        "terminology": round(term_score, 1),
        "coherence": round(coh_score, 1),
        "readability": round(read_score, 1),
        "clarity": round(clarity, 1),
        "constraints": round(constraint_score, 1),
        "lexical_diversity": round(lex_score, 1)
    }

    composite = sum(sub_scores[k] * weights[k] for k in weights)

    return {
        "sub_scores": sub_scores,
        "weights": weights,
        "composite_score": round(composite, 2),
        "readability": readability,
        "lexical_diversity": lexical,
        "structural_metrics": structure,
        "math_formula_metrics": math,
        "explanation_depth": depth,
        "terminology": terminology,
        "coherence": coherence,
        "passive_voice": passive,
        "information_density": info_density,
        "constraint_check": constraints
    }


def compute_cross_model_stats(all_evals):
    """Z-score normalization and ranking across models."""
    if len(all_evals) < 2:
        return None

    composites = {name: e["composite_score"] for name, e in all_evals.items()}
    sub_score_keys = list(next(iter(all_evals.values()))["sub_scores"].keys())

    # Z-scores for composite
    vals = list(composites.values())
    mu = statistics.mean(vals)
    sigma = statistics.stdev(vals) if len(vals) > 1 else 1

    z_scores = {}
    for name, val in composites.items():
        z_scores[name] = round((val - mu) / sigma, 3) if sigma > 0 else 0

    # Per-dimension z-scores
    dim_z = {k: {} for k in sub_score_keys}
    for k in sub_score_keys:
        dim_vals = [e["sub_scores"][k] for e in all_evals.values()]
        d_mu = statistics.mean(dim_vals)
        d_sigma = statistics.stdev(dim_vals) if len(dim_vals) > 1 else 1
        for name, e in all_evals.items():
            dim_z[k][name] = round((e["sub_scores"][k] - d_mu) / d_sigma, 3) if d_sigma > 0 else 0

    # Rankings
    ranked = sorted(composites.items(), key=lambda x: x[1], reverse=True)
    rankings = {name: rank + 1 for rank, (name, _) in enumerate(ranked)}

    return {
        "composite_z_scores": z_scores,
        "dimension_z_scores": dim_z,
        "rankings": rankings,
        "mean": round(mu, 2),
        "std": round(sigma, 2)
    }


# ============================================================
# LLM-AS-JUDGE (Groq)
# ============================================================

def llm_judge_evaluate(text, prompt_type, api_key, prompt_text=""):
    """Call Groq API for LLM-as-Judge evaluation."""
    import requests as req_lib

    judge_prompt = f"""You are an expert educational content evaluator. You are evaluating an AI model's response to a {"teaching/explanation" if prompt_type == "teach" else "problem-solving"} prompt in a STEM tutoring context.

The model was asked to use Direct Instruction style (clear, step-by-step, no Socratic questioning).

{"Original prompt: " + prompt_text if prompt_text else ""}

=== MODEL RESPONSE ===
{text[:6000]}
=== END RESPONSE ===

Evaluate the response on these 8 dimensions. For each, give a score from 1-10 and a one-sentence justification.

1. **Accuracy**: Are all facts, formulas, computations, and derivations correct?
2. **Pedagogical Clarity**: Is the explanation clear, well-organized, and easy for an undergraduate to follow?
3. **Completeness**: Does the response address all parts of the prompt (key ideas, worked example/solution, 2 practice exercises with solutions)?
4. **Step-by-Step Correctness**: Are all intermediate steps shown, logically ordered, and error-free?
5. **Appropriate Difficulty**: Is the content at the right undergraduate level — not too trivial, not too advanced?
6. **Example Quality**: Are the worked example and practice exercises well-chosen, non-trivial, and pedagogically useful?
7. **Mathematical Rigor**: Are equations, notation, and symbolic manipulations handled correctly and precisely?
8. **Direct Instruction Style**: Does the response avoid Socratic questioning and instead teach directly and explicitly?

Respond ONLY with valid JSON (no markdown, no backticks). Format:
{{"accuracy":{{"score":N,"reason":"..."}},"pedagogical_clarity":{{"score":N,"reason":"..."}},"completeness":{{"score":N,"reason":"..."}},"step_by_step_correctness":{{"score":N,"reason":"..."}},"appropriate_difficulty":{{"score":N,"reason":"..."}},"example_quality":{{"score":N,"reason":"..."}},"mathematical_rigor":{{"score":N,"reason":"..."}},"direct_instruction_style":{{"score":N,"reason":"..."}},"overall_score":N,"overall_comment":"..."}}"""

    try:
        resp = req_lib.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": judge_prompt}],
                "temperature": 0.3,
                "max_tokens": 1500
            },
            timeout=30
        )
        if resp.status_code != 200:
            return {"error": f"Groq API {resp.status_code}: {resp.text[:300]}"}
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        content = re.sub(r'^```(?:json)?\s*', '', content.strip())
        content = re.sub(r'\s*```$', '', content.strip())
        return json.loads(content)
    except req_lib.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except (json.JSONDecodeError, KeyError) as e:
        return {"error": f"Parse error: {str(e)}"}


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    data = request.json
    model_name = data.get('model_name', '').strip()
    response_text = data.get('response_text', '').strip()
    prompt_type = data.get('prompt_type', 'teach')  # 'teach' or 'solve'
    prompt_text = data.get('prompt_text', '')

    if not model_name or not response_text:
        return jsonify({"error": "Model name and response text are required"}), 400

    metrics = compute_all_metrics(response_text, prompt_type)

    entry = {
        "model_name": model_name,
        "prompt_type": prompt_type,
        "response_text": response_text,
        "prompt_text": prompt_text,
        "timestamp": datetime.now().isoformat(),
        **metrics
    }

    evaluations[model_name] = entry
    eval_history.append(entry)

    # Cross-model stats
    cross_model = compute_cross_model_stats(
        {n: e for n, e in evaluations.items()}
    ) if len(evaluations) >= 2 else None

    return jsonify({
        "evaluation": entry,
        "cross_model": cross_model,
        "all_models": {n: {
            "composite_score": e["composite_score"],
            "sub_scores": e["sub_scores"],
            "prompt_type": e["prompt_type"]
        } for n, e in evaluations.items()}
    })


@app.route('/api/llm_judge', methods=['POST'])
def llm_judge():
    data = request.json
    model_name = data.get('model_name', '').strip()
    api_key = data.get('api_key', '').strip()

    if not api_key:
        return jsonify({"error": "Groq API key required"}), 400

    if model_name not in evaluations:
        return jsonify({"error": f"Model '{model_name}' not evaluated yet"}), 404

    entry = evaluations[model_name]
    result = llm_judge_evaluate(
        entry["response_text"],
        entry["prompt_type"],
        api_key,
        entry.get("prompt_text", "")
    )

    if "error" in result:
        return jsonify({"error": result["error"]}), 500

    evaluations[model_name]["llm_judge"] = result
    return jsonify({"llm_judge": result, "model_name": model_name})


@app.route('/api/export/csv')
def export_csv():
    if not eval_history:
        return jsonify({"error": "No evaluations to export"}), 404
    output = io.StringIO()
    flat = []
    for e in eval_history:
        row = {
            "model_name": e["model_name"],
            "prompt_type": e["prompt_type"],
            "timestamp": e["timestamp"],
            "composite_score": e["composite_score"],
        }
        for k, v in e["sub_scores"].items():
            row[f"sub_{k}"] = v
        row["word_count"] = e["explanation_depth"]["word_count"]
        row["sentence_count"] = e["explanation_depth"]["sentence_count"]
        row["fk_grade"] = e["readability"]["fk_grade"]
        row["flesch_ease"] = e["readability"]["flesch_ease"]
        row["ttr"] = e["lexical_diversity"]["ttr"]
        row["coherence"] = e["coherence"]["coherence_score"]
        row["constraint_score"] = e["constraint_check"]["score"]
        row["math_elements"] = e["math_formula_metrics"]["total_math_elements"]
        row["terminology_density"] = e["terminology"]["terminology_density"]
        row["reasoning_markers"] = e["explanation_depth"]["reasoning_markers"]
        row["pedagogical_density"] = e["explanation_depth"]["pedagogical_density"]
        if "llm_judge" in e and "error" not in e.get("llm_judge", {}):
            for dim in ["accuracy", "pedagogical_clarity", "completeness", "step_by_step_correctness",
                        "appropriate_difficulty", "example_quality", "mathematical_rigor", "direct_instruction_style"]:
                row[f"llm_{dim}"] = e["llm_judge"].get(dim, {}).get("score", "")
            row["llm_overall"] = e["llm_judge"].get("overall_score", "")
        flat.append(row)

    writer = csv.DictWriter(output, fieldnames=flat[0].keys())
    writer.writeheader()
    writer.writerows(flat)
    mem = io.BytesIO(output.getvalue().encode())
    return send_file(mem, mimetype='text/csv', as_attachment=True,
                     download_name=f'tutoring_eval_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')


@app.route('/api/export/json')
def export_json():
    if not eval_history:
        return jsonify({"error": "No evaluations to export"}), 404
    export_data = {
        "export_date": datetime.now().isoformat(),
        "domain": "Study & Tutoring",
        "evaluations": eval_history,
        "cross_model": compute_cross_model_stats(evaluations) if len(evaluations) >= 2 else None
    }
    mem = io.BytesIO(json.dumps(export_data, indent=2).encode())
    return send_file(mem, mimetype='application/json', as_attachment=True,
                     download_name=f'tutoring_eval_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')


@app.route('/api/reset', methods=['POST'])
def reset():
    evaluations.clear()
    eval_history.clear()
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
