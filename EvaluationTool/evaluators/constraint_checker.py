"""
constraint_checker.py — Prompt Constraint Adherence Scoring

Automatically parses evaluation prompts to extract structural constraints
(bullet counts, word ranges, section presence/order, sentence limits) and
scores a model's response against each constraint.

Supports both automatic regex-based constraint detection and manual
constraint profiles for the four standard prompt types.
"""

import re
from collections import OrderedDict


# ═══════════════════════════════════════════════════════════════════════════
# Sentence / bullet detection helpers
# ═══════════════════════════════════════════════════════════════════════════

def _count_bullets(text: str) -> int:
    """Count bullet points (lines starting with - or * or • or numbered)."""
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    count = 0
    for line in lines:
        if re.match(r'^[-*•►▸▹●◦‣⁃]\s', line):
            count += 1
        elif re.match(r'^\d+[\.\)]\s', line):
            count += 1
    return count


def _extract_bullets(text: str) -> list:
    """Extract bullet point texts."""
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    bullets = []
    for line in lines:
        m = re.match(r'^[-*•►▸▹●◦‣⁃]\s*(.*)', line)
        if m:
            bullets.append(m.group(1).strip())
        else:
            m2 = re.match(r'^\d+[\.\)]\s*(.*)', line)
            if m2:
                bullets.append(m2.group(1).strip())
    return bullets


def _count_words(text: str) -> int:
    """Count words in a text."""
    return len(re.findall(r'\b\w+\b', text))


def _count_sentences(text: str) -> int:
    """Count sentences in a text."""
    sents = re.split(r'[.!?]+', text)
    return len([s for s in sents if s.strip()])


def _extract_sections(text: str) -> OrderedDict:
    """
    Extract named sections from text.
    Looks for patterns like "Section Name:" or "**Section Name**" or "## Section Name"
    """
    sections = OrderedDict()
    # Pattern: Header followed by content (Markdown bold, heading, or plain "Title:")
    pattern = r'(?:^|\n)\s*(?:\*\*|#{1,3}\s*)?([A-Z][A-Za-z\s/\'\-&]+?)(?:\*\*)?:\s*(.*?)(?=\n\s*(?:\*\*|#{1,3}\s*)?[A-Z][A-Za-z\s/\'\-&]+?(?:\*\*)?:|\Z)'
    matches = re.finditer(pattern, text, re.DOTALL)
    for m in matches:
        name = m.group(1).strip().rstrip(':')
        content = m.group(2).strip()
        sections[name.lower()] = content

    # If no sections found, try simpler pattern with bold/heading markers
    if not sections:
        pattern2 = r'(?:\*\*|#{1,3}\s*)([^*#\n]+?)(?:\*\*|)\s*[\n:](.+?)(?=(?:\*\*|#{1,3}\s*)[^*#\n]+?(?:\*\*|)\s*[\n:]|\Z)'
        matches2 = re.finditer(pattern2, text, re.DOTALL)
        for m in matches2:
            name = m.group(1).strip().rstrip(':')
            content = m.group(2).strip()
            sections[name.lower()] = content

    return sections


# ═══════════════════════════════════════════════════════════════════════════
# Constraint types and checkers
# ═══════════════════════════════════════════════════════════════════════════

def check_exact_bullet_count(response: str, expected: int) -> dict:
    """Check if the response has exactly N bullet points."""
    actual = _count_bullets(response)
    passed = actual == expected
    return {
        'name': f'Exactly {expected} bullet points',
        'expected': expected,
        'actual': actual,
        'passed': passed,
        'score': 1.0 if passed else max(0, 1.0 - abs(actual - expected) / expected),
        'detail': f'Found {actual} bullets, expected {expected}'
    }


def check_word_count_per_bullet(response: str, min_w: int, max_w: int) -> dict:
    """Check if each bullet is within word count range."""
    bullets = _extract_bullets(response)
    if not bullets:
        # Try line-by-line as fallback
        bullets = [l.strip() for l in response.strip().split('\n') if l.strip()]

    results = []
    for i, b in enumerate(bullets):
        wc = _count_words(b)
        ok = min_w <= wc <= max_w
        results.append({'bullet': i+1, 'words': wc, 'in_range': ok})

    n_pass = sum(1 for r in results if r['in_range'])
    total = max(len(results), 1)

    return {
        'name': f'Words per bullet: {min_w}–{max_w}',
        'expected': f'{min_w}-{max_w} words each',
        'actual': results,
        'passed': n_pass == total and total > 0,
        'score': round(n_pass / total, 4),
        'detail': f'{n_pass}/{total} bullets within {min_w}–{max_w} words'
    }


def check_section_presence(response: str, expected_sections: list) -> dict:
    """Check if all expected sections are present."""
    text_lower = response.lower()
    found = []
    missing = []
    for sec in expected_sections:
        # Check both "Section:" and "**Section**" patterns
        patterns = [
            sec.lower() + r'\s*:',
            r'\*\*' + re.escape(sec.lower()) + r'\*\*',
            r'#{1,3}\s*' + re.escape(sec.lower()),
        ]
        sec_found = any(re.search(p, text_lower) for p in patterns)
        if sec_found:
            found.append(sec)
        else:
            missing.append(sec)

    n_found = len(found)
    total = len(expected_sections)
    return {
        'name': 'Required sections present',
        'expected': expected_sections,
        'actual': {'found': found, 'missing': missing},
        'passed': n_found == total,
        'score': round(n_found / max(total, 1), 4),
        'detail': f'{n_found}/{total} sections found. Missing: {missing}' if missing else f'All {total} sections present'
    }


def check_section_order(response: str, expected_order: list) -> dict:
    """Check if sections appear in the expected order."""
    text_lower = response.lower()
    positions = []
    for sec in expected_order:
        match = re.search(re.escape(sec.lower()), text_lower)
        pos = match.start() if match else -1
        positions.append(pos)

    # Filter out not-found sections
    found_positions = [(i, p) for i, p in enumerate(positions) if p >= 0]
    if len(found_positions) < 2:
        return {
            'name': 'Section order correct',
            'expected': expected_order,
            'actual': 'Not enough sections found to check order',
            'passed': len(found_positions) <= 1,
            'score': 1.0 if len(found_positions) <= 1 else 0.0,
            'detail': 'Too few sections found to verify order'
        }

    # Check if found positions are in ascending order
    ordered = all(found_positions[i][1] <= found_positions[i+1][1]
                  for i in range(len(found_positions)-1))

    # Kendall tau-like score: fraction of correctly ordered pairs
    n_pairs = 0
    n_correct = 0
    for i in range(len(found_positions)):
        for j in range(i+1, len(found_positions)):
            n_pairs += 1
            if found_positions[i][1] < found_positions[j][1]:
                n_correct += 1

    score = round(n_correct / max(n_pairs, 1), 4)

    return {
        'name': 'Section order correct',
        'expected': expected_order,
        'actual': ordered,
        'passed': ordered,
        'score': score,
        'detail': 'Sections in correct order' if ordered else f'Order score: {score} ({n_correct}/{n_pairs} pairs correct)'
    }


def check_sentence_count_per_section(response: str, expected_sections: list,
                                      min_s: int, max_s: int) -> dict:
    """Check sentence count per section is within range."""
    sections = _extract_sections(response)
    results = []
    for sec_name in expected_sections:
        sec_key = sec_name.lower()
        content = sections.get(sec_key, '')
        if content:
            sc = _count_sentences(content)
            ok = min_s <= sc <= max_s
            results.append({'section': sec_name, 'sentences': sc, 'in_range': ok})
        else:
            results.append({'section': sec_name, 'sentences': 0, 'in_range': False})

    n_pass = sum(1 for r in results if r['in_range'])
    total = max(len(results), 1)

    return {
        'name': f'Sentences per section: {min_s}–{max_s}',
        'expected': f'{min_s}-{max_s} sentences each',
        'actual': results,
        'passed': n_pass == total and total > 0,
        'score': round(n_pass / total, 4),
        'detail': f'{n_pass}/{total} sections within {min_s}–{max_s} sentences'
    }


def check_bullet_count_per_section(response: str, expected_sections: list,
                                    min_b: int, max_b: int) -> dict:
    """Check bullet count per section is within range."""
    sections = _extract_sections(response)
    results = []
    for sec_name in expected_sections:
        sec_key = sec_name.lower()
        content = sections.get(sec_key, '')
        if content:
            bc = _count_bullets(content)
            if bc == 0:
                # Count lines as pseudo-bullets
                bc = len([l for l in content.strip().split('\n') if l.strip()])
            ok = min_b <= bc <= max_b
            results.append({'section': sec_name, 'bullets': bc, 'in_range': ok})
        else:
            results.append({'section': sec_name, 'bullets': 0, 'in_range': False})

    n_pass = sum(1 for r in results if r['in_range'])
    total = max(len(results), 1)

    return {
        'name': f'Bullets per section: {min_b}–{max_b}',
        'expected': f'{min_b}-{max_b} bullets each',
        'actual': results,
        'passed': n_pass == total,
        'score': round(n_pass / total, 4),
        'detail': f'{n_pass}/{total} sections within {min_b}–{max_b} bullets'
    }


def check_no_external_info_heuristic(response: str, source: str) -> dict:
    """
    Heuristic check: flag potential external information by looking for
    named entities or specific claims in the response that don't appear
    in the source text. This is approximate — LLM judge is more reliable.
    """
    if not source.strip():
        return {
            'name': 'No external information (heuristic)',
            'passed': True,
            'score': 1.0,
            'detail': 'No source text provided for comparison'
        }

    source_lower = source.lower()
    resp_words = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', response))
    src_words = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', source))

    new_entities = resp_words - src_words
    # Filter common words that are capitalized due to sentence start
    common = {'the', 'this', 'that', 'these', 'however', 'many', 'some', 'it',
              'they', 'not', 'also', 'while', 'although', 'both', 'each',
              'several', 'various', 'overall', 'additionally', 'furthermore',
              'moreover', 'nevertheless', 'consequently', 'therefore'}
    new_entities = {e for e in new_entities if e.lower() not in common and len(e) > 2}

    score = 1.0 if len(new_entities) == 0 else max(0.0, 1.0 - len(new_entities) * 0.15)

    return {
        'name': 'No external information (heuristic)',
        'passed': len(new_entities) == 0,
        'score': round(score, 4),
        'detail': f'Potential external entities: {list(new_entities)[:5]}' if new_entities else 'No external entities detected'
    }


# ═══════════════════════════════════════════════════════════════════════════
# Automatic constraint parser
# ═══════════════════════════════════════════════════════════════════════════

def parse_and_check_constraints(prompt_text: str, response: str,
                                 source_text: str = '') -> dict:
    """
    Parse the prompt for structural constraints using regex patterns,
    then check each against the response.

    Returns { overall_score: float, details: list[dict], parsed_constraints: list }
    """
    checks = []
    prompt_lower = prompt_text.lower()

    # ── Detect bullet count constraints ──────────────────────────────
    m = re.search(r'(?:exactly|output)\s+(\d+)\s+bullet\s*point', prompt_lower)
    if m:
        n = int(m.group(1))
        checks.append(check_exact_bullet_count(response, n))

    # ── Detect word count per bullet ─────────────────────────────────
    m = re.search(r'(?:each\s+bullet\s+(?:must\s+be|should\s+be)?)\s*(\d+)[–\-to]+(\d+)\s+words', prompt_lower)
    if m:
        checks.append(check_word_count_per_bullet(response, int(m.group(1)), int(m.group(2))))
    else:
        m2 = re.search(r'(\d+)[–\-]+(\d+)\s+words', prompt_lower)
        if m2 and 'bullet' in prompt_lower:
            checks.append(check_word_count_per_bullet(response, int(m2.group(1)), int(m2.group(2))))

    # ── Detect section requirements ──────────────────────────────────
    m = re.search(r'(?:sections?\s+(?:in\s+)?(?:this\s+)?(?:exact\s+)?order|output\s+sections?\s+in\s+this\s+exact\s+order)\s*:\s*(.*?)(?:\.\s|$)', prompt_lower)
    if m:
        secs = [s.strip().strip('.') for s in re.split(r',\s*', m.group(1)) if s.strip()]
        if secs:
            checks.append(check_section_presence(response, secs))
            checks.append(check_section_order(response, secs))

    # Look for section names listed explicitly
    sec_match = re.findall(r'(?:titled|named)\s*:\s*(.*?)(?:\.|$)', prompt_lower)
    if not sec_match:
        # Try to find comma-separated capitalized names after "order:"
        sec_match2 = re.search(r'order:\s*([A-Z][^.]+)', prompt_text)
        if sec_match2:
            raw_secs = [s.strip().rstrip('.') for s in re.split(r',\s*', sec_match2.group(1)) if s.strip()]
            if len(raw_secs) >= 2:
                checks.append(check_section_presence(response, raw_secs))
                checks.append(check_section_order(response, raw_secs))

    # ── Detect sentence count per section ────────────────────────────
    m = re.search(r'(?:each\s+section\s+(?:must\s+be|should\s+be)?)\s*(\d+)[–\-to]+(\d+)\s+sentence', prompt_lower)
    if m:
        # Find section names from above
        secs_for_sent = [c['expected'] for c in checks
                         if 'sections present' in c.get('name', '') and isinstance(c['expected'], list)]
        if secs_for_sent:
            checks.append(check_sentence_count_per_section(
                response, secs_for_sent[0], int(m.group(1)), int(m.group(2))))
    else:
        m2 = re.search(r'(\d+)[–\-]+(\d+)\s+sentence', prompt_lower)
        if m2:
            secs_for_sent = [c['expected'] for c in checks
                             if 'sections present' in c.get('name', '') and isinstance(c['expected'], list)]
            if secs_for_sent:
                checks.append(check_sentence_count_per_section(
                    response, secs_for_sent[0], int(m2.group(1)), int(m2.group(2))))

    # ── Detect "no external info" constraint ─────────────────────────
    if re.search(r'do\s+not\s+(?:add|include|invent|introduce)\s+(?:any\s+)?(?:information|content|results)', prompt_lower):
        checks.append(check_no_external_info_heuristic(response, source_text))

    # ── Detect bullets-per-section constraint ────────────────────────
    m = re.search(r'(\d+)[–\-]+(\d+)\s+bullet\s*point', prompt_lower)
    if m and 'section' in prompt_lower:
        secs_for_bul = [c['expected'] for c in checks
                        if 'sections present' in c.get('name', '') and isinstance(c['expected'], list)]
        if secs_for_bul:
            checks.append(check_bullet_count_per_section(
                response, secs_for_bul[0], int(m.group(1)), int(m.group(2))))

    # ── Detect specific bullet titles (like prompt3) ─────────────────
    titled_match = re.search(r'bullet\s*points?\s+titled\s*:\s*(.*?)(?:\.\s|\n)', prompt_lower)
    if titled_match:
        titles = [t.strip() for t in re.split(r',\s*', titled_match.group(1)) if t.strip()]
        if titles:
            checks.append(check_section_presence(response, titles))

    # ── Compute overall score ────────────────────────────────────────
    if checks:
        overall = round(sum(c['score'] for c in checks) / len(checks), 4)
    else:
        overall = 1.0  # No constraints detected → full score

    return {
        'overall_score': overall,
        'num_constraints': len(checks),
        'num_passed': sum(1 for c in checks if c['passed']),
        'details': checks
    }


# Alias for backward compatibility
check_constraints = parse_and_check_constraints
