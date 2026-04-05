"""
Constraint Checker
==================
Parses evaluation prompts to extract code constraints and checks whether
model-generated code adheres to them. Supports constraint types:

- Function signature requirements (name, parameters, return type)
- Docstring presence
- Type hint presence
- No external library usage
- Specific function/class naming
- Edge case handling
- Code style constraints (list comprehensions, inline comments)
- Complexity constraints
- Stability constraints (for debugging tasks: preserve signatures)
- Test case extraction
"""

import ast
import re
from typing import Any


# ─── CONSTRAINT EXTRACTION FROM PROMPTS ────────────────────────────────────────

def extract_constraints(prompt: str) -> dict:
    """
    Parse a prompt to extract all checkable constraints.
    Returns a dict of constraint categories with their details.
    """
    constraints = {
        'function_signatures': [],
        'class_names': [],
        'must_have_docstrings': False,
        'must_have_type_hints': False,
        'no_external_libs': False,
        'allowed_stdlib': [],
        'forbidden_functions': [],
        'required_patterns': [],
        'must_handle_edge_cases': False,
        'must_be_stable_sort': False,
        'must_preserve_signatures': False,
        'must_have_inline_comments': False,
        'must_use_list_comprehensions': False,
        'must_not_use': [],
        'must_raise_errors': [],
        'task_type': 'implementation',
        'test_cases_raw': '',
        'expected_complexity': None,
    }

    prompt_lower = prompt.lower()

    # --- Detect task type ---
    if any(kw in prompt_lower for kw in ['fix', 'bug', 'debug', 'broken', 'incorrect']):
        constraints['task_type'] = 'debugging'
    elif any(kw in prompt_lower for kw in ['refactor', 'optimize', 'rewrite', 'improve']):
        constraints['task_type'] = 'optimization'
    elif any(kw in prompt_lower for kw in ['class ', 'design', 'implement a python class']):
        constraints['task_type'] = 'design'
    else:
        constraints['task_type'] = 'implementation'

    # --- Extract function signatures ---
    sig_patterns = [
        r'def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?',
        r'`(\w+)\(`',
        r'function\s+called?\s+`?(\w+)`?',
    ]
    for pattern in sig_patterns[:1]:  # Use the precise one
        for match in re.finditer(pattern, prompt):
            sig = {
                'name': match.group(1),
                'params_raw': match.group(2).strip() if match.group(2) else '',
                'return_type': match.group(3).strip() if len(match.groups()) >= 3 and match.group(3) else None,
            }
            constraints['function_signatures'].append(sig)

    # --- Extract class names ---
    for match in re.finditer(r'class\s+(\w+)', prompt):
        constraints['class_names'].append(match.group(1))

    # --- Docstrings ---
    if any(kw in prompt_lower for kw in ['add a docstring', 'add docstring', 'include docstring',
                                          'add type hints and a docstring', 'add type hints and docstrings',
                                          'add docstrings']):
        constraints['must_have_docstrings'] = True

    # --- Type hints ---
    if any(kw in prompt_lower for kw in ['type hint', 'type hints', 'add type hints',
                                          'include type hints']):
        constraints['must_have_type_hints'] = True

    # --- No external libraries ---
    if any(kw in prompt_lower for kw in ['do not use external libraries',
                                          'no external libraries',
                                          'without external libraries',
                                          'do not use external']):
        constraints['no_external_libs'] = True

    # Allowed stdlib
    stdlib_match = re.findall(r'(?:stdlib\s+)?`(\w+)`\s+(?:is|are)\s+(?:allowed|fine|ok)', prompt_lower)
    constraints['allowed_stdlib'] = stdlib_match

    # Also extract from patterns like "(stdlib `re`, `collections` are fine)"
    paren_match = re.findall(r'\((?:stdlib\s+)?([^)]*(?:are|is)\s+(?:fine|allowed|ok))\)', prompt_lower)
    for pm in paren_match:
        for m in re.findall(r'`(\w+)`', pm):
            if m not in constraints['allowed_stdlib']:
                constraints['allowed_stdlib'].append(m)

    # --- Forbidden functions ---
    forbidden_patterns = [
        r'do not use\s+`?(\w+(?:\.\w+)?)`?',
        r'don\'t use\s+`?(\w+(?:\.\w+)?)`?',
        r'not use\s+`?(\w+(?:\.\w+)?)\(\)`?',
        r'without using\s+`?(\w+(?:\.\w+)?)`?',
    ]
    for pattern in forbidden_patterns:
        for match in re.finditer(pattern, prompt_lower):
            val = match.group(1)
            if val not in ('external', 'libraries', 'external libraries'):
                constraints['forbidden_functions'].append(val)

    # Specific: no eval, exec, sort, etc.
    if 'do not use `eval()`' in prompt_lower or 'do not use eval' in prompt_lower:
        constraints['forbidden_functions'].append('eval')
    if 'do not use `exec()`' in prompt_lower:
        constraints['forbidden_functions'].append('exec')
    if 'do not use built-in sort' in prompt_lower or 'do not use `sort`' in prompt_lower:
        constraints['forbidden_functions'].extend(['sort', 'sorted'])

    # --- Edge cases ---
    if any(kw in prompt_lower for kw in ['edge case', 'edge cases', 'handle edge',
                                          'corner case', 'empty input', 'empty list']):
        constraints['must_handle_edge_cases'] = True

    # --- Stable sort ---
    if 'stable' in prompt_lower and 'sort' in prompt_lower:
        constraints['must_be_stable_sort'] = True

    # --- Preserve signatures ---
    if any(kw in prompt_lower for kw in ['do not change the function signature',
                                          'preserve the original function name',
                                          'do not change the external api',
                                          'don\'t change the function signature']):
        constraints['must_preserve_signatures'] = True

    # --- Inline comments ---
    if any(kw in prompt_lower for kw in ['inline comment', 'add inline comments',
                                          'add comments explaining']):
        constraints['must_have_inline_comments'] = True

    # --- List comprehensions ---
    if 'list comprehension' in prompt_lower:
        constraints['must_use_list_comprehensions'] = True

    # --- Must raise errors ---
    if 'raise valueerror' in prompt_lower or 'raise `valueerror`' in prompt_lower:
        constraints['must_raise_errors'].append('ValueError')
    if 'raise typeerror' in prompt_lower:
        constraints['must_raise_errors'].append('TypeError')

    # --- Expected complexity ---
    complexity_match = re.search(r'[oO]\(([^)]+)\)', prompt)
    if complexity_match:
        constraints['expected_complexity'] = f"O({complexity_match.group(1)})"

    # --- Extract test cases ---
    test_block = _extract_test_cases(prompt)
    constraints['test_cases_raw'] = test_block

    return constraints


def _extract_test_cases(prompt: str) -> str:
    """Extract test assertion blocks from prompt."""
    lines = prompt.split('\n')
    test_lines = []
    in_test_block = False
    in_code_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```'):
            if in_code_block:
                in_code_block = False
                in_test_block = False
                continue
            else:
                in_code_block = True
                continue

        if in_code_block:
            if stripped.startswith('assert ') or stripped.startswith('# ') or in_test_block:
                if stripped.startswith('assert ') or stripped.startswith('try:') or stripped.startswith('except '):
                    in_test_block = True
                if in_test_block:
                    test_lines.append(line)
            # Skip non-test code lines in code blocks
            elif stripped and not stripped.startswith('#') and not stripped.startswith('from ') and not stripped.startswith('import '):
                # Could be continuation of test setup
                if test_lines and (stripped.startswith('results') or stripped.startswith('em') or
                                    stripped.startswith('idx') or stripped.startswith('def ') or
                                    stripped.startswith('result')):
                    test_lines.append(line)

    return '\n'.join(test_lines)


# ─── CONSTRAINT CHECKING ──────────────────────────────────────────────────────

def check_constraints(code: str, constraints: dict) -> dict:
    """
    Check code against extracted constraints.
    Returns pass/fail/na for each constraint with details.
    """
    results = []
    total = 0
    passed = 0

    try:
        tree = ast.parse(code)
        parse_ok = True
    except SyntaxError as e:
        return {
            'checks': [{'name': 'Syntax Valid', 'status': 'fail', 'detail': str(e)}],
            'total': 1, 'passed': 0, 'score': 0,
        }

    # 1. Syntax validity
    results.append({'name': 'Syntax Valid', 'status': 'pass', 'detail': 'Code parses without errors'})
    total += 1
    passed += 1

    # 2. Function signatures
    if constraints['function_signatures']:
        defined_funcs = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [arg.arg for arg in node.args.args]
                defined_funcs[node.name] = {
                    'args': args,
                    'has_return_annotation': node.returns is not None,
                    'has_arg_annotations': any(a.annotation is not None for a in node.args.args),
                }

        for sig in constraints['function_signatures']:
            total += 1
            name = sig['name']
            if name in defined_funcs:
                passed += 1
                results.append({
                    'name': f'Function `{name}` defined',
                    'status': 'pass',
                    'detail': f'Found with args: {defined_funcs[name]["args"]}'
                })
            else:
                results.append({
                    'name': f'Function `{name}` defined',
                    'status': 'fail',
                    'detail': f'Function `{name}` not found in code'
                })

    # 3. Class names
    if constraints['class_names']:
        defined_classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        for cls_name in constraints['class_names']:
            total += 1
            if cls_name in defined_classes:
                passed += 1
                results.append({'name': f'Class `{cls_name}` defined', 'status': 'pass', 'detail': 'Found'})
            else:
                results.append({'name': f'Class `{cls_name}` defined', 'status': 'fail',
                                'detail': f'Class `{cls_name}` not found'})

    # 4. Docstrings
    if constraints['must_have_docstrings']:
        total += 1
        all_defs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        with_docstrings = 0
        without_docstrings = []
        for node in all_defs:
            if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                with_docstrings += 1
            else:
                without_docstrings.append(node.name)

        if not without_docstrings:
            passed += 1
            results.append({'name': 'Docstrings present', 'status': 'pass',
                            'detail': f'All {len(all_defs)} definitions have docstrings'})
        else:
            results.append({'name': 'Docstrings present', 'status': 'fail',
                            'detail': f'Missing docstrings: {", ".join(without_docstrings[:5])}'})

    # 5. Type hints
    if constraints['must_have_type_hints']:
        total += 1
        funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        funcs_with_hints = 0
        funcs_without = []
        for func in funcs:
            has_any = any(arg.annotation is not None for arg in func.args.args if arg.arg != 'self')
            if has_any or func.returns is not None:
                funcs_with_hints += 1
            else:
                funcs_without.append(func.name)

        if not funcs_without:
            passed += 1
            results.append({'name': 'Type hints present', 'status': 'pass',
                            'detail': f'All {len(funcs)} functions have type hints'})
        else:
            results.append({'name': 'Type hints present', 'status': 'fail',
                            'detail': f'Missing type hints: {", ".join(funcs_without[:5])}'})

    # 6. No external libraries
    if constraints['no_external_libs']:
        total += 1
        STDLIB = {
            'os', 'sys', 'math', 'json', 'csv', 're', 'ast', 'io', 'copy',
            'collections', 'itertools', 'functools', 'operator', 'string',
            'typing', 'types', 'abc', 'dataclasses', 'enum', 'heapq', 'bisect',
            'datetime', 'time', 'hashlib', 'random', 'statistics',
            'pathlib', 'unittest', 'doctest', 'logging', 'warnings',
            'tokenize', 'difflib', 'textwrap', 'contextlib', 'decimal',
        }
        # Add specifically allowed
        for lib in constraints['allowed_stdlib']:
            STDLIB.add(lib)

        external_found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split('.')[0]
                    if root not in STDLIB:
                        external_found.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split('.')[0]
                    if root not in STDLIB:
                        external_found.append(node.module)

        if not external_found:
            passed += 1
            results.append({'name': 'No external libraries', 'status': 'pass',
                            'detail': 'Only stdlib imports found'})
        else:
            results.append({'name': 'No external libraries', 'status': 'fail',
                            'detail': f'External imports found: {", ".join(external_found)}'})

    # 7. Forbidden functions
    if constraints['forbidden_functions']:
        code_lower = code.lower()
        for func in constraints['forbidden_functions']:
            total += 1
            # Check both call and reference
            patterns = [
                rf'\b{re.escape(func)}\s*\(',
                rf'\.{re.escape(func)}\s*\(',
            ]
            found = any(re.search(p, code) for p in patterns)
            if not found:
                passed += 1
                results.append({'name': f'Does not use `{func}`', 'status': 'pass',
                                'detail': f'No usage of `{func}` found'})
            else:
                results.append({'name': f'Does not use `{func}`', 'status': 'fail',
                                'detail': f'Found usage of forbidden function `{func}`'})

    # 8. Inline comments (for debugging tasks)
    if constraints['must_have_inline_comments']:
        total += 1
        inline_comments = sum(1 for line in code.split('\n')
                              if '#' in line and not line.strip().startswith('#') and line.strip())
        if inline_comments >= 2:
            passed += 1
            results.append({'name': 'Inline comments', 'status': 'pass',
                            'detail': f'Found {inline_comments} inline comments'})
        else:
            results.append({'name': 'Inline comments', 'status': 'fail',
                            'detail': f'Only {inline_comments} inline comment(s) found; expected more'})

    # 9. List comprehensions
    if constraints['must_use_list_comprehensions']:
        total += 1
        has_comp = any(isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))
                       for n in ast.walk(tree))
        if has_comp:
            passed += 1
            results.append({'name': 'Uses comprehensions', 'status': 'pass',
                            'detail': 'Found list/set/dict comprehensions'})
        else:
            results.append({'name': 'Uses comprehensions', 'status': 'fail',
                            'detail': 'No comprehensions found'})

    # 10. Must raise errors
    if constraints['must_raise_errors']:
        for err_type in constraints['must_raise_errors']:
            total += 1
            has_raise = False
            for node in ast.walk(tree):
                if isinstance(node, ast.Raise) and node.exc:
                    if isinstance(node.exc, ast.Call):
                        if isinstance(node.exc.func, ast.Name) and node.exc.func.id == err_type:
                            has_raise = True
                    elif isinstance(node.exc, ast.Name) and node.exc.id == err_type:
                        has_raise = True
            if has_raise:
                passed += 1
                results.append({'name': f'Raises `{err_type}`', 'status': 'pass',
                                'detail': f'Found raise {err_type}'})
            else:
                results.append({'name': f'Raises `{err_type}`', 'status': 'fail',
                                'detail': f'No `raise {err_type}` found'})

    # 11. Preserve signatures (debugging tasks)
    if constraints['must_preserve_signatures'] and constraints['function_signatures']:
        for sig in constraints['function_signatures']:
            total += 1
            name = sig['name']
            found = False
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                    found = True
                    break
            if found:
                passed += 1
                results.append({'name': f'Signature preserved: `{name}`', 'status': 'pass',
                                'detail': 'Original function signature maintained'})
            else:
                results.append({'name': f'Signature preserved: `{name}`', 'status': 'fail',
                                'detail': f'Function `{name}` not found or renamed'})

    # 12. Edge case handling check (heuristic)
    if constraints['must_handle_edge_cases']:
        total += 1
        edge_indicators = 0
        code_text = code.lower()

        # Check for empty input handling
        if any(p in code_text for p in ['len(', '== []', '== ""', 'is none', 'not ', '== {}', '== ()']):
            edge_indicators += 1
        # Check for boundary checks
        if any(p in code_text for p in ['<= 0', '<= 1', '== 0', '== 1', 'len('] ):
            edge_indicators += 1
        # Check for early returns
        if 'return' in code_text and ('if not' in code_text or 'if len' in code_text):
            edge_indicators += 1

        if edge_indicators >= 2:
            passed += 1
            results.append({'name': 'Edge case handling', 'status': 'pass',
                            'detail': f'Found {edge_indicators} edge case handling patterns'})
        else:
            results.append({'name': 'Edge case handling', 'status': 'partial',
                            'detail': f'Only {edge_indicators} edge case pattern(s) detected'})

    score = round(passed / max(total, 1) * 100, 1)

    return {
        'checks': results,
        'total': total,
        'passed': passed,
        'score': score,
    }


# ─── MASTER FUNCTION ──────────────────────────────────────────────────────────

def evaluate_constraints(prompt: str, code: str) -> dict:
    """
    Extract constraints from prompt and check code against them.
    Returns both the extracted constraints and the check results.
    """
    constraints = extract_constraints(prompt)
    check_results = check_constraints(code, constraints)

    return {
        'extracted_constraints': constraints,
        'check_results': check_results,
    }
