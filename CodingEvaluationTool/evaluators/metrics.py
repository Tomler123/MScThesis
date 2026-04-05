"""
Code Metrics Engine
===================
Comprehensive deterministic metrics for evaluating code quality, complexity,
and structural properties. All metrics are computed using Python's standard
library (ast, tokenize, re, difflib, math) — no external dependencies.

Metrics Computed:
- Lines of Code (LOC, SLOC, blank, comment, docstring)
- Cyclomatic Complexity (McCabe)
- Halstead Metrics (volume, difficulty, effort, vocabulary, length, bugs estimate)
- AST Structural Metrics (depth, node count, branching factor)
- Maintainability Index (Microsoft variant)
- Code Similarity (token-based Jaccard, SequenceMatcher ratio, structural similarity)
- Function / Class / Method counts
- Documentation Coverage (docstrings, type hints)
- Identifier Quality (average length, naming convention adherence)
- Import Analysis
- Error Handling Analysis
- Nesting Depth Analysis
- Code-to-Comment Ratio
- DRY Score (duplicate block detection)
"""

import ast
import re
import math
import tokenize
import io
import difflib
from collections import Counter, defaultdict
from typing import Any


# ─── LINE METRICS ──────────────────────────────────────────────────────────────

def compute_line_metrics(code: str) -> dict:
    """Compute line-based metrics: total LOC, SLOC, blank lines, comment lines, docstring lines."""
    lines = code.split('\n')
    total_loc = len(lines)
    blank_lines = sum(1 for l in lines if l.strip() == '')
    comment_lines = sum(1 for l in lines if l.strip().startswith('#'))

    # Count docstring lines via AST
    docstring_lines = 0
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                if (node.body and isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                    ds_node = node.body[0]
                    docstring_lines += (ds_node.end_lineno - ds_node.lineno + 1)
    except SyntaxError:
        pass

    sloc = total_loc - blank_lines - comment_lines - docstring_lines
    sloc = max(sloc, 0)

    return {
        'total_loc': total_loc,
        'sloc': sloc,
        'blank_lines': blank_lines,
        'comment_lines': comment_lines,
        'docstring_lines': docstring_lines,
        'code_to_comment_ratio': round(sloc / max(comment_lines + docstring_lines, 1), 2),
    }


# ─── CYCLOMATIC COMPLEXITY ─────────────────────────────────────────────────────

DECISION_NODES = (
    ast.If, ast.For, ast.While, ast.And, ast.Or,
    ast.ExceptHandler, ast.With, ast.Assert,
    ast.IfExp,  # ternary
)

def compute_cyclomatic_complexity(code: str) -> dict:
    """Compute McCabe cyclomatic complexity. CC = 1 + decision_points."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {'cyclomatic_complexity': None, 'decision_points': None, 'risk_category': 'parse_error'}

    decision_points = 0
    for node in ast.walk(tree):
        if isinstance(node, DECISION_NODES):
            decision_points += 1
        # comprehensions have implicit loops
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            decision_points += len(node.generators)

    cc = 1 + decision_points

    if cc <= 5:
        risk = 'low'
    elif cc <= 10:
        risk = 'moderate'
    elif cc <= 20:
        risk = 'high'
    else:
        risk = 'very_high'

    return {
        'cyclomatic_complexity': cc,
        'decision_points': decision_points,
        'risk_category': risk,
    }


# ─── HALSTEAD METRICS ──────────────────────────────────────────────────────────

PYTHON_OPERATORS = {
    '+', '-', '*', '/', '//', '**', '%', '@',
    '<<', '>>', '&', '|', '^', '~',
    ':=', '<', '>', '<=', '>=', '==', '!=',
    '=', '+=', '-=', '*=', '/=', '//=', '**=', '%=',
    '@=', '&=', '|=', '^=', '>>=', '<<=',
    '(', ')', '[', ']', '{', '}',
    ',', ':', '.', ';', '->', '...',
}

PYTHON_KEYWORDS_AS_OPERATORS = {
    'and', 'or', 'not', 'in', 'is', 'lambda',
    'if', 'else', 'elif', 'for', 'while',
    'def', 'class', 'return', 'yield', 'import', 'from',
    'try', 'except', 'finally', 'raise', 'with', 'as',
    'pass', 'break', 'continue', 'del', 'assert',
    'global', 'nonlocal', 'async', 'await',
}

def compute_halstead_metrics(code: str) -> dict:
    """Compute Halstead complexity metrics from tokenized code."""
    operators = Counter()
    operands = Counter()

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
    except tokenize.TokenError:
        return {
            'halstead_vocabulary': None, 'halstead_length': None,
            'halstead_volume': None, 'halstead_difficulty': None,
            'halstead_effort': None, 'halstead_time': None,
            'halstead_bugs': None,
        }

    for tok in tokens:
        if tok.type == tokenize.ENDMARKER or tok.type == tokenize.ENCODING:
            continue
        if tok.type == tokenize.NEWLINE or tok.type == tokenize.NL:
            continue
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.INDENT or tok.type == tokenize.DEDENT:
            continue

        val = tok.string

        if tok.type == tokenize.OP or val in PYTHON_OPERATORS:
            operators[val] += 1
        elif tok.type == tokenize.NAME:
            if val in PYTHON_KEYWORDS_AS_OPERATORS:
                operators[val] += 1
            else:
                operands[val] += 1
        elif tok.type in (tokenize.NUMBER, tokenize.STRING):
            operands[val] += 1

    n1 = len(operators)   # unique operators
    n2 = len(operands)    # unique operands
    N1 = sum(operators.values())  # total operators
    N2 = sum(operands.values())   # total operands

    n = n1 + n2  # vocabulary
    N = N1 + N2  # program length

    if n == 0 or n2 == 0:
        return {
            'halstead_vocabulary': n, 'halstead_length': N,
            'halstead_volume': 0, 'halstead_difficulty': 0,
            'halstead_effort': 0, 'halstead_time': 0,
            'halstead_bugs': 0,
            'halstead_unique_operators': n1, 'halstead_unique_operands': n2,
            'halstead_total_operators': N1, 'halstead_total_operands': N2,
        }

    volume = N * math.log2(n) if n > 0 else 0
    difficulty = (n1 / 2) * (N2 / max(n2, 1))
    effort = difficulty * volume
    time_to_program = effort / 18  # seconds (Halstead)
    bugs_estimate = volume / 3000  # Halstead bug prediction

    return {
        'halstead_vocabulary': n,
        'halstead_length': N,
        'halstead_volume': round(volume, 2),
        'halstead_difficulty': round(difficulty, 2),
        'halstead_effort': round(effort, 2),
        'halstead_time': round(time_to_program, 2),
        'halstead_bugs': round(bugs_estimate, 4),
        'halstead_unique_operators': n1,
        'halstead_unique_operands': n2,
        'halstead_total_operators': N1,
        'halstead_total_operands': N2,
    }


# ─── AST STRUCTURAL METRICS ───────────────────────────────────────────────────

def compute_ast_metrics(code: str) -> dict:
    """Compute AST-based structural metrics."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {
            'ast_node_count': None, 'ast_max_depth': None,
            'ast_avg_branching_factor': None, 'ast_node_types': {},
            'parse_success': False,
        }

    node_count = 0
    node_types = Counter()
    max_depth = 0
    children_counts = []

    def walk_depth(node, depth):
        nonlocal node_count, max_depth
        node_count += 1
        node_types[type(node).__name__] += 1
        max_depth = max(max_depth, depth)
        children = list(ast.iter_child_nodes(node))
        if children:
            children_counts.append(len(children))
        for child in children:
            walk_depth(child, depth + 1)

    walk_depth(tree, 0)

    avg_branching = round(sum(children_counts) / max(len(children_counts), 1), 2)

    return {
        'ast_node_count': node_count,
        'ast_max_depth': max_depth,
        'ast_avg_branching_factor': avg_branching,
        'ast_node_types': dict(node_types.most_common(15)),
        'parse_success': True,
    }


# ─── MAINTAINABILITY INDEX ─────────────────────────────────────────────────────

def compute_maintainability_index(code: str) -> dict:
    """
    Compute Maintainability Index (MI) — Microsoft variant.
    MI = max(0, (171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(LOC)) * 100 / 171)
    Where V = Halstead Volume, CC = Cyclomatic Complexity, LOC = SLOC.
    """
    line_m = compute_line_metrics(code)
    cc_m = compute_cyclomatic_complexity(code)
    h_m = compute_halstead_metrics(code)

    sloc = max(line_m['sloc'], 1)
    cc = cc_m.get('cyclomatic_complexity', 1) or 1
    volume = h_m.get('halstead_volume', 1) or 1

    raw_mi = 171 - 5.2 * math.log(max(volume, 1)) - 0.23 * cc - 16.2 * math.log(max(sloc, 1))
    mi = max(0, raw_mi * 100 / 171)

    if mi >= 85:
        rating = 'highly_maintainable'
    elif mi >= 65:
        rating = 'moderately_maintainable'
    elif mi >= 40:
        rating = 'low_maintainability'
    else:
        rating = 'unmaintainable'

    return {
        'maintainability_index': round(mi, 2),
        'mi_rating': rating,
    }


# ─── CODE SIMILARITY ──────────────────────────────────────────────────────────

def _tokenize_code(code: str) -> list:
    """Tokenize code into a list of meaningful tokens for comparison."""
    tokens = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE,
                            tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER,
                            tokenize.ENCODING):
                continue
            tokens.append(tok.string)
    except tokenize.TokenError:
        # Fallback: simple word split
        tokens = re.findall(r'\w+|[^\s\w]', code)
    return tokens


def compute_code_similarity(code1: str, code2: str) -> dict:
    """
    Compute multiple code similarity metrics between two code strings.
    - Token-based Jaccard similarity
    - SequenceMatcher ratio (longest common subsequence based)
    - Structural similarity (AST node type sequence comparison)
    """
    # Token-based Jaccard
    tokens1 = set(_tokenize_code(code1))
    tokens2 = set(_tokenize_code(code2))
    if tokens1 or tokens2:
        jaccard = len(tokens1 & tokens2) / len(tokens1 | tokens2)
    else:
        jaccard = 1.0

    # SequenceMatcher ratio
    seq_ratio = difflib.SequenceMatcher(None, code1.strip(), code2.strip()).ratio()

    # Structural similarity (AST node types)
    structural_sim = 0.0
    try:
        tree1 = ast.parse(code1)
        tree2 = ast.parse(code2)
        types1 = [type(n).__name__ for n in ast.walk(tree1)]
        types2 = [type(n).__name__ for n in ast.walk(tree2)]
        structural_sim = difflib.SequenceMatcher(None, types1, types2).ratio()
    except SyntaxError:
        structural_sim = 0.0

    # Token sequence similarity (order-sensitive)
    tok_seq1 = _tokenize_code(code1)
    tok_seq2 = _tokenize_code(code2)
    token_seq_sim = difflib.SequenceMatcher(None, tok_seq1, tok_seq2).ratio()

    # Combined weighted similarity
    combined = 0.25 * jaccard + 0.30 * seq_ratio + 0.25 * structural_sim + 0.20 * token_seq_sim

    return {
        'jaccard_similarity': round(jaccard, 4),
        'sequence_match_ratio': round(seq_ratio, 4),
        'structural_similarity': round(structural_sim, 4),
        'token_sequence_similarity': round(token_seq_sim, 4),
        'combined_similarity': round(combined, 4),
    }


# ─── FUNCTION / CLASS ANALYSIS ────────────────────────────────────────────────

def compute_structure_metrics(code: str) -> dict:
    """Analyze function, class, and method counts and properties."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {
            'function_count': 0, 'class_count': 0, 'method_count': 0,
            'async_function_count': 0, 'lambda_count': 0,
            'functions_with_docstrings': 0, 'functions_with_type_hints': 0,
            'functions_with_return_type': 0, 'docstring_coverage': 0,
            'type_hint_coverage': 0, 'parse_success': False,
        }

    functions = []
    classes = []
    methods = []
    async_funcs = []
    lambdas = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if it's a method (inside a class)
            functions.append(node)
        elif isinstance(node, ast.AsyncFunctionDef):
            async_funcs.append(node)
            functions.append(node)
        elif isinstance(node, ast.ClassDef):
            classes.append(node)
        elif isinstance(node, ast.Lambda):
            lambdas.append(node)

    # Separate methods from top-level functions
    for cls_node in classes:
        for item in ast.walk(cls_node):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item in functions:
                methods.append(item)

    top_level_funcs = [f for f in functions if f not in methods]

    # Docstring analysis
    all_defs = functions + [c for c in classes]
    funcs_with_docstrings = 0
    for node in all_defs:
        if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, (ast.Constant, ast.Str))):
            funcs_with_docstrings += 1

    # Type hint analysis
    funcs_with_hints = 0
    funcs_with_return = 0
    for func in functions:
        has_hints = any(arg.annotation is not None for arg in func.args.args)
        if has_hints:
            funcs_with_hints += 1
        if func.returns is not None:
            funcs_with_return += 1

    total_defs = max(len(all_defs), 1)

    return {
        'function_count': len(top_level_funcs),
        'class_count': len(classes),
        'method_count': len(methods),
        'async_function_count': len(async_funcs),
        'lambda_count': len(lambdas),
        'functions_with_docstrings': funcs_with_docstrings,
        'functions_with_type_hints': funcs_with_hints,
        'functions_with_return_type': funcs_with_return,
        'docstring_coverage': round(funcs_with_docstrings / total_defs * 100, 1),
        'type_hint_coverage': round(funcs_with_hints / max(len(functions), 1) * 100, 1),
        'parse_success': True,
    }


# ─── NESTING DEPTH ANALYSIS ──────────────────────────────────────────────────

NESTING_NODES = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler)

def compute_nesting_metrics(code: str) -> dict:
    """Compute maximum and average nesting depth of control structures."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {'max_nesting_depth': None, 'avg_nesting_depth': None}

    depths = []

    def walk(node, depth):
        if isinstance(node, NESTING_NODES):
            depth += 1
            depths.append(depth)
        for child in ast.iter_child_nodes(node):
            walk(child, depth)

    walk(tree, 0)

    return {
        'max_nesting_depth': max(depths) if depths else 0,
        'avg_nesting_depth': round(sum(depths) / max(len(depths), 1), 2) if depths else 0,
    }


# ─── IDENTIFIER QUALITY ──────────────────────────────────────────────────────

def compute_identifier_metrics(code: str) -> dict:
    """Analyze identifier naming quality."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {
            'total_identifiers': 0, 'avg_identifier_length': 0,
            'single_char_identifiers': 0, 'snake_case_ratio': 0,
        }

    identifiers = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            identifiers.append(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            identifiers.append(node.name)
        elif isinstance(node, ast.ClassDef):
            identifiers.append(node.name)
        elif isinstance(node, ast.arg):
            identifiers.append(node.arg)

    # Filter out builtins and dunder
    filtered = [i for i in identifiers if not i.startswith('__')]

    if not filtered:
        return {
            'total_identifiers': 0, 'avg_identifier_length': 0,
            'single_char_identifiers': 0, 'snake_case_ratio': 0,
        }

    avg_len = sum(len(i) for i in filtered) / len(filtered)
    single_char = sum(1 for i in filtered if len(i) == 1)
    snake_case = sum(1 for i in filtered if re.match(r'^[a-z_][a-z0-9_]*$', i))

    return {
        'total_identifiers': len(filtered),
        'avg_identifier_length': round(avg_len, 2),
        'single_char_identifiers': single_char,
        'single_char_ratio': round(single_char / len(filtered) * 100, 1),
        'snake_case_ratio': round(snake_case / len(filtered) * 100, 1),
    }


# ─── IMPORT ANALYSIS ──────────────────────────────────────────────────────────

def compute_import_metrics(code: str) -> dict:
    """Analyze imports in the code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {'import_count': 0, 'from_import_count': 0, 'external_libs': [], 'stdlib_imports': []}

    STDLIB = {
        'os', 'sys', 'math', 'json', 'csv', 're', 'ast', 'io', 'copy',
        'collections', 'itertools', 'functools', 'operator', 'string',
        'textwrap', 'unicodedata', 'datetime', 'time', 'calendar',
        'hashlib', 'hmac', 'secrets', 'random', 'statistics',
        'pathlib', 'glob', 'shutil', 'tempfile',
        'typing', 'types', 'abc', 'dataclasses', 'enum',
        'unittest', 'doctest', 'pytest',
        'logging', 'warnings', 'traceback',
        'threading', 'multiprocessing', 'concurrent', 'asyncio',
        'socket', 'http', 'urllib', 'email',
        'struct', 'codecs', 'pprint', 'dis',
        'tokenize', 'difflib', 'heapq', 'bisect',
        'contextlib', 'decimal', 'fractions',
    }

    imports = []
    from_imports = []
    external = []
    stdlib = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
                root = alias.name.split('.')[0]
                if root in STDLIB:
                    stdlib.append(root)
                else:
                    external.append(root)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                from_imports.append(node.module)
                root = node.module.split('.')[0]
                if root in STDLIB:
                    stdlib.append(root)
                else:
                    external.append(root)

    return {
        'import_count': len(imports),
        'from_import_count': len(from_imports),
        'total_imports': len(imports) + len(from_imports),
        'external_libs': list(set(external)),
        'stdlib_imports': list(set(stdlib)),
        'uses_external_libs': len(external) > 0,
    }


# ─── ERROR HANDLING ANALYSIS ──────────────────────────────────────────────────

def compute_error_handling_metrics(code: str) -> dict:
    """Analyze error handling patterns."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {'try_blocks': 0, 'except_handlers': 0, 'raise_statements': 0,
                'bare_excepts': 0, 'assert_statements': 0}

    try_blocks = 0
    except_handlers = 0
    raise_stmts = 0
    bare_excepts = 0
    assert_stmts = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            try_blocks += 1
        elif isinstance(node, ast.ExceptHandler):
            except_handlers += 1
            if node.type is None:
                bare_excepts += 1
        elif isinstance(node, ast.Raise):
            raise_stmts += 1
        elif isinstance(node, ast.Assert):
            assert_stmts += 1

    return {
        'try_blocks': try_blocks,
        'except_handlers': except_handlers,
        'raise_statements': raise_stmts,
        'bare_excepts': bare_excepts,
        'assert_statements': assert_stmts,
    }


# ─── DUPLICATE CODE DETECTION (DRY SCORE) ─────────────────────────────────────

def compute_dry_score(code: str, min_block_size: int = 3) -> dict:
    """
    Simple duplicate block detection. Checks for repeated sequences
    of consecutive lines (ignoring blanks/comments).
    """
    lines = [l.strip() for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]

    if len(lines) < min_block_size * 2:
        return {'duplicate_blocks': 0, 'duplicate_lines': 0, 'dry_score': 100.0}

    duplicates = 0
    dup_lines = set()

    for size in range(min_block_size, len(lines) // 2 + 1):
        seen = {}
        for i in range(len(lines) - size + 1):
            block = tuple(lines[i:i + size])
            if block in seen:
                duplicates += 1
                for j in range(i, i + size):
                    dup_lines.add(j)
                for j in range(seen[block], seen[block] + size):
                    dup_lines.add(j)
            else:
                seen[block] = i

    total = max(len(lines), 1)
    dry_score = max(0, 100 - (len(dup_lines) / total * 100))

    return {
        'duplicate_blocks': duplicates,
        'duplicate_lines': len(dup_lines),
        'dry_score': round(dry_score, 2),
    }


# ─── TEST CASE EXECUTION (SAFE) ───────────────────────────────────────────────

def run_test_cases(code: str, test_code: str) -> dict:
    """
    Safely execute test assertions against submitted code.
    Returns pass/fail counts and details.
    """
    results = {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0, 'details': []}

    if not test_code.strip():
        return results

    # Parse test assertions
    test_lines = []
    current_block = []
    for line in test_code.split('\n'):
        stripped = line.strip()
        if stripped.startswith('assert ') or stripped.startswith('try:'):
            if current_block:
                test_lines.append('\n'.join(current_block))
            current_block = [line]
        elif current_block:
            current_block.append(line)
    if current_block:
        test_lines.append('\n'.join(current_block))

    # Execute each test
    namespace = {}
    try:
        exec(code, namespace)
    except Exception as e:
        results['errors'] = 1
        results['details'].append({'test': 'code_execution', 'status': 'error', 'message': str(e)})
        return results

    # Also need math for isclose
    namespace['__builtins__'] = __builtins__
    import math as _math
    namespace['math'] = _math
    namespace['isclose'] = _math.isclose

    for test_block in test_lines:
        if not test_block.strip():
            continue
        results['total'] += 1
        try:
            exec(test_block, namespace)
            results['passed'] += 1
            results['details'].append({
                'test': test_block.strip()[:80],
                'status': 'passed'
            })
        except AssertionError as e:
            results['failed'] += 1
            results['details'].append({
                'test': test_block.strip()[:80],
                'status': 'failed',
                'message': str(e)
            })
        except Exception as e:
            results['errors'] += 1
            results['details'].append({
                'test': test_block.strip()[:80],
                'status': 'error',
                'message': str(e)
            })

    if results['total'] > 0:
        results['pass_rate'] = round(results['passed'] / results['total'] * 100, 1)
    else:
        results['pass_rate'] = 0

    return results


# ─── MASTER EVALUATION FUNCTION ───────────────────────────────────────────────

def evaluate_code(code: str, reference_code: str = '', test_cases: str = '') -> dict:
    """
    Run ALL metrics on a code submission.
    Returns a comprehensive dictionary of all computed metrics.
    """
    result = {}

    # Basic metrics
    result['line_metrics'] = compute_line_metrics(code)
    result['cyclomatic'] = compute_cyclomatic_complexity(code)
    result['halstead'] = compute_halstead_metrics(code)
    result['ast_metrics'] = compute_ast_metrics(code)
    result['maintainability'] = compute_maintainability_index(code)
    result['structure'] = compute_structure_metrics(code)
    result['nesting'] = compute_nesting_metrics(code)
    result['identifiers'] = compute_identifier_metrics(code)
    result['imports'] = compute_import_metrics(code)
    result['error_handling'] = compute_error_handling_metrics(code)
    result['dry'] = compute_dry_score(code)

    # Similarity to reference (if provided)
    if reference_code.strip():
        result['similarity'] = compute_code_similarity(code, reference_code)
    else:
        result['similarity'] = {
            'jaccard_similarity': None, 'sequence_match_ratio': None,
            'structural_similarity': None, 'token_sequence_similarity': None,
            'combined_similarity': None,
        }

    # Test execution (if test cases provided)
    if test_cases.strip():
        result['test_results'] = run_test_cases(code, test_cases)
    else:
        result['test_results'] = {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0, 'pass_rate': 0, 'details': []}

    # Compute overall quality score (weighted composite)
    result['quality_score'] = _compute_quality_score(result)

    return result


def _compute_quality_score(metrics: dict) -> dict:
    """
    Compute a weighted composite quality score from 0–100.
    Breakdown by category for transparency.
    """
    scores = {}

    # Maintainability (20%)
    mi = metrics['maintainability'].get('maintainability_index', 50)
    scores['maintainability'] = min(mi, 100)

    # Complexity (15%) — lower is better
    cc = metrics['cyclomatic'].get('cyclomatic_complexity', 10) or 10
    scores['complexity'] = max(0, 100 - (cc - 1) * 5)

    # Documentation (15%)
    doc_cov = metrics['structure'].get('docstring_coverage', 0)
    hint_cov = metrics['structure'].get('type_hint_coverage', 0)
    scores['documentation'] = (doc_cov * 0.6 + hint_cov * 0.4)

    # Code structure (10%)
    nesting = metrics['nesting'].get('max_nesting_depth', 0) or 0
    scores['structure'] = max(0, 100 - nesting * 15)

    # DRY (10%)
    scores['dry'] = metrics['dry'].get('dry_score', 100)

    # Test pass rate (20%)
    scores['test_pass_rate'] = metrics['test_results'].get('pass_rate', 0)

    # Similarity to reference (10%)
    sim = metrics['similarity'].get('combined_similarity', None)
    if sim is not None:
        scores['similarity'] = sim * 100
    else:
        scores['similarity'] = 50  # neutral if no reference

    # Weighted composite
    weights = {
        'maintainability': 0.15,
        'complexity': 0.10,
        'documentation': 0.15,
        'structure': 0.05,
        'dry': 0.05,
        'test_pass_rate': 0.35,
        'similarity': 0.15,
    }

    total = sum(scores[k] * weights[k] for k in weights)

    return {
        'overall': round(total, 2),
        'breakdown': {k: round(v, 2) for k, v in scores.items()},
        'weights': weights,
    }
