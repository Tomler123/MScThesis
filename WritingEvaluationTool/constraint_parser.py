"""
Constraint Parser for Writing & Communication Evaluation Tool.
Automatically parses writing prompts to extract constraints,
then evaluates how well each model response follows them.
"""

import re
from metrics_engine import tokenize_sentences, tokenize_words, tokenize_paragraphs


# ─────────────────────────────────────────────
# CONSTRAINT EXTRACTION
# ─────────────────────────────────────────────

def extract_constraints(prompt_text):
    """Parse a writing prompt and extract all identifiable constraints."""
    constraints = []
    text = prompt_text.strip()
    lines = text.split('\n')
    full_lower = text.lower()

    # 1. Word count constraints
    # Patterns: "X-Y words", "X–Y words", "max X words", "at least X words", "exactly X words"
    # Word count patterns — only match general document word counts, not subject-line-specific ones
    wc_patterns = [
        (r'(?:body|total|length|text)\s+(?:must be\s+)?(\d+)\s*[-–—]\s*(\d+)\s*words', 'word_count_range'),
        (r'(?<!subject\s)(?<!line\s)(\d+)\s*[-–—]\s*(\d+)\s*words', 'word_count_range'),
        (r'total\s+(?:length\s+)?(?:must be\s+)?(\d+)\s*[-–—]\s*(\d+)\s*words', 'word_count_range'),
    ]
    seen_wc = False
    for pattern, ctype in wc_patterns:
        if seen_wc:
            break
        matches = re.finditer(pattern, full_lower)
        for match_obj in matches:
            # Skip if this match is within a "subject line" context (look at surrounding text)
            start = max(0, match_obj.start() - 40)
            context_before = full_lower[start:match_obj.start()]
            if 'subject' in context_before:
                continue
            m = match_obj.groups()
            if ctype == 'word_count_range' and not seen_wc:
                constraints.append({
                    'type': 'word_count_range',
                    'min': int(m[0]),
                    'max': int(m[1]),
                    'description': f'Word count must be {m[0]}–{m[1]}'
                })
                seen_wc = True
                break

    # 2. Sentence count constraints
    sc_patterns = [
        (r'(?:exactly|precisely|total[^.]*?=\s*)\s*(\d+)\s*sentences', 'sentence_count_exact'),
        (r'(\d+)\s*[-–—]\s*(\d+)\s*sentences', 'sentence_count_range'),
        (r'(?:exactly|precisely)\s+(\d+)\s+sentences', 'sentence_count_exact'),
        (r'total\s*=\s*(\d+)\s+sentences', 'sentence_count_exact'),
    ]
    for pattern, ctype in sc_patterns:
        matches = re.findall(pattern, full_lower)
        for match in matches:
            if ctype == 'sentence_count_exact':
                count = int(match) if isinstance(match, str) else int(match[0])
                constraints.append({
                    'type': 'sentence_count_exact',
                    'count': count,
                    'description': f'Exactly {count} sentences'
                })
            elif ctype == 'sentence_count_range':
                constraints.append({
                    'type': 'sentence_count_range',
                    'min': int(match[0]),
                    'max': int(match[1]),
                    'description': f'{match[0]}–{match[1]} sentences'
                })

    # 3. Paragraph count constraints
    pc_patterns = [
        (r'(?:exactly|precisely|use)\s+(\d+)\s+paragraphs?', 'paragraph_count_exact'),
        (r'(\d+)\s*[-–—]\s*(\d+)\s*paragraphs?', 'paragraph_count_range'),
    ]
    for pattern, ctype in pc_patterns:
        matches = re.findall(pattern, full_lower)
        for match in matches:
            if ctype == 'paragraph_count_exact':
                count = int(match) if isinstance(match, str) else int(match[0])
                constraints.append({
                    'type': 'paragraph_count_exact',
                    'count': count,
                    'description': f'Exactly {count} paragraphs'
                })
            elif ctype == 'paragraph_count_range':
                constraints.append({
                    'type': 'paragraph_count_range',
                    'min': int(match[0]),
                    'max': int(match[1]),
                    'description': f'{match[0]}–{match[1]} paragraphs'
                })

    # 4. Required phrases / keywords
    # "must include", "include the phrase", "must contain"
    # But skip phrases that are examples (preceded by "e.g.")
    phrase_patterns = [
        r'(?:must |should )?include (?:the )?(?:phrase|text|words?|statement):?\s*["""\']([^"""\']+)["""\']',
        r'must (?:mention|include|contain)[^.]*?["""\']([^"""\']+)["""\']',
    ]
    for pattern in phrase_patterns:
        for match_obj in re.finditer(pattern, text, re.IGNORECASE):
            phrase = match_obj.group(1).strip()
            # Check if this is an example (preceded by e.g.)
            start = max(0, match_obj.start() - 20)
            preceding = text[start:match_obj.start()].lower()
            if 'e.g.' in preceding or 'for example' in preceding or 'such as' in preceding:
                continue
            if len(phrase) > 2 and len(phrase) < 100:
                constraints.append({
                    'type': 'required_phrase',
                    'phrase': phrase,
                    'description': f'Must include phrase: "{phrase}"'
                })

    # Also check for inline required phrases like: include one explicit deadline: "by 5 PM today"
    inline_phrases = re.finditer(r'include[^.]*?[:\s]["""]([^"""]+)["""]', text, re.IGNORECASE)
    for match_obj in inline_phrases:
        phrase = match_obj.group(1).strip()
        # Skip examples
        start = max(0, match_obj.start() - 20)
        preceding = text[start:match_obj.start()].lower()
        if 'e.g.' in preceding or 'for example' in preceding or 'such as' in preceding:
            continue
        if len(phrase) > 2 and len(phrase) < 100:
            if not any(c['type'] == 'required_phrase' and c['phrase'] == phrase for c in constraints):
                constraints.append({
                    'type': 'required_phrase',
                    'phrase': phrase,
                    'description': f'Must include: "{phrase}"'
                })

    # 5. Forbidden words
    # "Do not use the words: urgent, ASAP, need."
    forbidden_match = re.search(
        r'(?:do not|don\'t|avoid|must not|should not|never)\s+use\s+(?:the\s+)?words?:\s*(.+?)(?:\.\s|\.$|\n)',
        text, re.IGNORECASE
    )
    if forbidden_match:
        raw = forbidden_match.group(1)
        # Split by comma, semicolon, "and", "or"
        words = re.split(r'[,;]|\band\b|\bor\b', raw)
        for w in words:
            w = w.strip().strip('"\'""" ').strip()
            if w and 1 <= len(w) <= 20 and not w.startswith('the '):
                constraints.append({
                    'type': 'forbidden_word',
                    'word': w.lower(),
                    'description': f'Must NOT use word: "{w}"'
                })

    # 6. Required sections/headings
    heading_patterns = [
        r'(?:use|include)\s+(?:exactly\s+)?these\s+headings?[^:]*:\s*(.+?)(?:\n\n|\nConstraints|\n[A-Z])',
        r'headings?[^:]*?in\s+this\s+order:\s*(.+?)(?:\n\n|\nConstraints)',
    ]
    for pattern in heading_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            # Split headings by comma, newline, or period
            headings = re.split(r'[,\n.]', match)
            for h in headings:
                h = h.strip().strip('.-•*123456789)').strip()
                if h and 1 < len(h) < 50 and not h.lower().startswith('constraint'):
                    constraints.append({
                        'type': 'required_heading',
                        'heading': h,
                        'description': f'Must include heading: "{h}"'
                    })

    # 7. Format constraints (no bullet points, specific format)
    if re.search(r'no\s+bullet\s*points?', full_lower):
        constraints.append({
            'type': 'no_bullet_points',
            'description': 'No bullet points allowed'
        })

    if re.search(r'(?:include|add)\s+(?:a\s+)?subject\s+line', full_lower):
        constraints.append({
            'type': 'requires_subject_line',
            'description': 'Must include a subject line'
        })

    # Subject line word limit
    subj_match = re.search(r'subject\s+line\s*\(?\s*(?:max(?:imum)?|up to)\s+(\d+)\s+words?\s*\)?', full_lower)
    if subj_match:
        constraints.append({
            'type': 'subject_line_max_words',
            'max': int(subj_match.group(1)),
            'description': f'Subject line max {subj_match.group(1)} words'
        })

    # 8. Tone requirements
    tone_keywords = ['professional', 'formal', 'informal', 'casual', 'neutral',
                     'friendly', 'persuasive', 'academic', 'informative',
                     'non-accusatory', 'non accusatory', 'warm', 'empathetic']
    tone_found = set()
    for kw in tone_keywords:
        if kw in full_lower:
            # Check it's in a tone-related context
            tone_ctx = re.search(rf'(?:tone|keep|maintain|style|voice)[^.]*?{re.escape(kw)}', full_lower)
            if tone_ctx or re.search(rf'{re.escape(kw)}[^.]*?(?:tone|style)', full_lower):
                tone_found.add(kw)
    for tone in tone_found:
        constraints.append({
            'type': 'tone_requirement',
            'tone': tone,
            'description': f'Tone must be: {tone}'
        })

    # 9. Required number of specific items (e.g., "exactly 3 actions")
    item_patterns = [
        (r'(?:exactly|precisely)\s+(\d+)\s+(actions?|steps?|items?|points?|reasons?|examples?|benefits?)', 'exact_item_count'),
        (r'include\s+(?:exactly\s+)?(\d+)\s+(actions?|steps?|items?|points?|reasons?|examples?|benefits?)', 'exact_item_count'),
    ]
    for pattern, ctype in item_patterns:
        matches = re.findall(pattern, full_lower)
        for match in matches:
            constraints.append({
                'type': 'item_count',
                'count': int(match[0]),
                'item_type': match[1],
                'description': f'Must include exactly {match[0]} {match[1]}'
            })

    # 10. Sentences per section constraint
    sps_match = re.search(r'each\s+(?:heading|section)\s+(?:must\s+)?(?:have|contain)\s+(?:exactly\s+)?(\d+)\s+sentences?', full_lower)
    if sps_match:
        constraints.append({
            'type': 'sentences_per_section',
            'count': int(sps_match.group(1)),
            'description': f'Each section must have exactly {sps_match.group(1)} sentences'
        })

    # 11. Required email/placeholder
    email_matches = re.findall(r'(?:include|must contain)[^.]*?([\w.]+@[\w.]+\.\w+)', text, re.IGNORECASE)
    for email in email_matches:
        constraints.append({
            'type': 'required_email',
            'email': email,
            'description': f'Must include email: {email}'
        })
    # Also check direct mention
    if 'support@example.com' in text and not any(c.get('email') == 'support@example.com' for c in constraints):
        constraints.append({
            'type': 'required_email',
            'email': 'support@example.com',
            'description': 'Must include email: support@example.com'
        })

    # 12. Technical term constraints
    tech_match = re.search(r'(?:must\s+)?include\s+(?:exactly\s+)?(\w+)\s+technical\s+terms?\s+from\s+(?:this\s+)?list:\s*\{([^}]+)\}', text, re.IGNORECASE)
    if tech_match:
        count_word = tech_match.group(1).strip()
        terms = [t.strip() for t in tech_match.group(2).split(',')]
        count_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                     'zero': 0, 'no': 0, 'none': 0}
        count = count_map.get(count_word.lower(), None)
        if count is None:
            try:
                count = int(count_word)
            except:
                count = None
        if count is not None:
            constraints.append({
                'type': 'technical_terms_required',
                'count': count,
                'terms': terms,
                'description': f'Must include exactly {count} technical terms from: {", ".join(terms)}'
            })

    # Check for zero technical terms requirement
    zero_tech = re.search(r'(?:must\s+)?include\s+zero\s+technical\s+terms?\s+from\s+(?:that|this)\s+list', text, re.IGNORECASE)
    if zero_tech:
        # Find the term list from a previous reference
        term_list_match = re.search(r'\{([^}]+)\}', text)
        if term_list_match:
            terms = [t.strip() for t in term_list_match.group(1).split(',')]
            constraints.append({
                'type': 'technical_terms_forbidden',
                'terms': terms,
                'description': f'Must include ZERO technical terms from: {", ".join(terms)}'
            })

    # 13. Output format
    format_match = re.search(r'output\s+format\s+must\s+be:\s*\n(.+?)(?:\n\n|$)', text, re.IGNORECASE | re.DOTALL)
    if format_match:
        constraints.append({
            'type': 'output_format',
            'format': format_match.group(1).strip(),
            'description': f'Output format: {format_match.group(1).strip()}'
        })

    # 14. Apology constraint
    if re.search(r'(?:do not|don\'t)\s+include\s+apolog', full_lower):
        constraints.append({
            'type': 'no_apologies',
            'description': 'Must not include apologies'
        })

    # 15. Semicolon-separated actions
    if re.search(r'separated\s+by\s+semicolons?', full_lower):
        constraints.append({
            'type': 'semicolon_separated',
            'description': 'Items must be separated by semicolons (not bullets)'
        })

    # 16. "next step" requirement
    if re.search(r'(?:clear\s+)?next\s+step', full_lower):
        constraints.append({
            'type': 'requires_next_step',
            'description': 'Must include a clear next step'
        })

    # 17. Confidence statement
    conf_match = re.search(r'(?:confidence|confident)\s+statement\s*\(?["""]?([^""")\n]*)["""]?\)?', text, re.IGNORECASE)
    if conf_match:
        constraints.append({
            'type': 'confidence_statement',
            'example': conf_match.group(1).strip(),
            'description': f'Must include a confidence statement (e.g., "{conf_match.group(1).strip()}")'
        })
    elif re.search(r'confidence\s+statement', full_lower):
        constraints.append({
            'type': 'confidence_statement',
            'example': 'We are confident',
            'description': 'Must include a confidence statement'
        })

    # 18. Duration/time mentions
    dur_matches = re.findall(r'(?:include|mention)[^.]*?["""]([^"""]*(?:hours?|minutes?|days?)[^"""]*)["""]', text, re.IGNORECASE)
    for d in dur_matches:
        if not any(c.get('phrase') == d for c in constraints):
            constraints.append({
                'type': 'required_phrase',
                'phrase': d,
                'description': f'Must include: "{d}"'
            })

    # Check for specific time-related phrases
    for phrase in ['next tuesday', '2 hours', 'next Monday', 'next Wednesday']:
        pattern = re.compile(rf'must\s+include[^.]*?{re.escape(phrase)}', re.IGNORECASE)
        if pattern.search(text) or (f'"{phrase}"' in full_lower) or (f'"{phrase}"' in full_lower):
            if not any(c.get('phrase', '').lower() == phrase.lower() for c in constraints):
                constraints.append({
                    'type': 'required_phrase',
                    'phrase': phrase,
                    'description': f'Must include phrase: "{phrase}"'
                })

    # Deduplicate constraints
    seen = set()
    unique = []
    for c in constraints:
        key = (c['type'], c.get('description', ''))
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


# ─────────────────────────────────────────────
# CONSTRAINT EVALUATION
# ─────────────────────────────────────────────

def evaluate_constraints(response_text, constraints):
    """Evaluate how well a response follows parsed constraints."""
    results = []
    text_lower = response_text.lower()
    words = tokenize_words(response_text)
    sentences = tokenize_sentences(response_text)
    paragraphs = tokenize_paragraphs(response_text)
    word_count = len(words)

    for constraint in constraints:
        ctype = constraint['type']
        result = {
            'description': constraint['description'],
            'type': ctype,
            'passed': False,
            'actual': None,
            'expected': None,
            'score': 0  # 0-100
        }

        if ctype == 'word_count_range':
            cmin, cmax = constraint['min'], constraint['max']
            result['expected'] = f'{cmin}–{cmax} words'
            result['actual'] = f'{word_count} words'
            if cmin <= word_count <= cmax:
                result['passed'] = True
                result['score'] = 100
            else:
                # Partial credit based on how close
                if word_count < cmin:
                    result['score'] = max(0, round(100 - (cmin - word_count) / cmin * 200))
                else:
                    result['score'] = max(0, round(100 - (word_count - cmax) / cmax * 200))

        elif ctype == 'word_count_max':
            cmax = constraint['max']
            result['expected'] = f'≤ {cmax} words'
            result['actual'] = f'{word_count} words'
            result['passed'] = word_count <= cmax
            result['score'] = 100 if result['passed'] else max(0, round(100 - (word_count - cmax) / cmax * 200))

        elif ctype == 'word_count_min':
            cmin = constraint['min']
            result['expected'] = f'≥ {cmin} words'
            result['actual'] = f'{word_count} words'
            result['passed'] = word_count >= cmin
            result['score'] = 100 if result['passed'] else max(0, round(100 - (cmin - word_count) / cmin * 200))

        elif ctype == 'word_count_exact':
            count = constraint['count']
            result['expected'] = f'Exactly {count} words'
            result['actual'] = f'{word_count} words'
            result['passed'] = word_count == count
            result['score'] = 100 if result['passed'] else max(0, round(100 - abs(word_count - count) / count * 200))

        elif ctype == 'sentence_count_exact':
            count = constraint['count']
            actual = len(sentences)
            result['expected'] = f'Exactly {count} sentences'
            result['actual'] = f'{actual} sentences'
            result['passed'] = actual == count
            result['score'] = 100 if result['passed'] else max(0, round(100 - abs(actual - count) / max(count, 1) * 200))

        elif ctype == 'sentence_count_range':
            cmin, cmax = constraint['min'], constraint['max']
            actual = len(sentences)
            result['expected'] = f'{cmin}–{cmax} sentences'
            result['actual'] = f'{actual} sentences'
            result['passed'] = cmin <= actual <= cmax
            result['score'] = 100 if result['passed'] else max(0, 50)

        elif ctype == 'paragraph_count_exact':
            count = constraint['count']
            actual = len(paragraphs)
            result['expected'] = f'Exactly {count} paragraphs'
            result['actual'] = f'{actual} paragraphs'
            result['passed'] = actual == count
            result['score'] = 100 if result['passed'] else max(0, round(100 - abs(actual - count) / max(count, 1) * 150))

        elif ctype == 'paragraph_count_range':
            cmin, cmax = constraint['min'], constraint['max']
            actual = len(paragraphs)
            result['expected'] = f'{cmin}–{cmax} paragraphs'
            result['actual'] = f'{actual} paragraphs'
            result['passed'] = cmin <= actual <= cmax
            result['score'] = 100 if result['passed'] else max(0, 50)

        elif ctype == 'required_phrase':
            phrase = constraint['phrase']
            result['expected'] = f'Contains: "{phrase}"'
            found = phrase.lower() in text_lower
            result['actual'] = 'Found' if found else 'Not found'
            result['passed'] = found
            result['score'] = 100 if found else 0

        elif ctype == 'forbidden_word':
            word = constraint['word']
            result['expected'] = f'Does NOT contain: "{word}"'
            # Check for whole word match
            found = bool(re.search(rf'\b{re.escape(word)}\b', text_lower))
            result['actual'] = 'Found (violation!)' if found else 'Not found (good)'
            result['passed'] = not found
            result['score'] = 100 if not found else 0

        elif ctype == 'required_heading':
            heading = constraint['heading']
            result['expected'] = f'Contains heading: "{heading}"'
            # Check for heading as a line or bold/formatted text
            heading_found = bool(re.search(
                rf'(?:^|\n)\s*(?:#+\s*|(?:\*\*|__))?{re.escape(heading)}(?:\*\*|__)?[\s:]*(?:\n|$)',
                response_text, re.IGNORECASE | re.MULTILINE
            ))
            # Also check plain presence
            if not heading_found:
                heading_found = heading.lower() in text_lower
            result['actual'] = 'Found' if heading_found else 'Not found'
            result['passed'] = heading_found
            result['score'] = 100 if heading_found else 0

        elif ctype == 'no_bullet_points':
            result['expected'] = 'No bullet points'
            has_bullets = bool(re.search(r'^\s*[-•*]\s+\S', response_text, re.MULTILINE))
            # Also check numbered lists
            has_numbered = bool(re.search(r'^\s*\d+[.)]\s+\S', response_text, re.MULTILINE))
            violations = has_bullets or has_numbered
            result['actual'] = 'Has bullet points (violation!)' if violations else 'No bullet points (good)'
            result['passed'] = not violations
            result['score'] = 100 if not violations else 0

        elif ctype == 'requires_subject_line':
            result['expected'] = 'Has subject line'
            has_subject = bool(re.search(r'(?:^|\n)\s*(?:subject|re|subj)[\s:]+.+', response_text, re.IGNORECASE))
            result['actual'] = 'Found' if has_subject else 'Not found'
            result['passed'] = has_subject
            result['score'] = 100 if has_subject else 0

        elif ctype == 'subject_line_max_words':
            cmax = constraint['max']
            subject_match = re.search(r'(?:^|\n)\s*(?:subject|re|subj)[\s:]+(.+)', response_text, re.IGNORECASE)
            if subject_match:
                subject_words = len(tokenize_words(subject_match.group(1)))
                result['expected'] = f'Subject line ≤ {cmax} words'
                result['actual'] = f'{subject_words} words'
                result['passed'] = subject_words <= cmax
                result['score'] = 100 if result['passed'] else max(0, round(100 - (subject_words - cmax) * 30))
            else:
                result['expected'] = f'Subject line ≤ {cmax} words'
                result['actual'] = 'No subject line found'
                result['passed'] = False
                result['score'] = 0

        elif ctype == 'tone_requirement':
            tone = constraint['tone']
            result['expected'] = f'Tone: {tone}'
            # Basic tone detection
            tone_scores = _detect_tone(response_text)
            if tone in tone_scores:
                score = tone_scores[tone]
                result['actual'] = f'Tone score: {score}/100'
                result['passed'] = score >= 50
                result['score'] = score
            else:
                result['actual'] = 'Tone not evaluated'
                result['score'] = 50
                result['passed'] = True  # Give benefit of doubt

        elif ctype == 'technical_terms_required':
            count = constraint['count']
            terms = constraint['terms']
            found_terms = [t for t in terms if t.lower() in text_lower]
            result['expected'] = f'Exactly {count} terms from {terms}'
            result['actual'] = f'Found {len(found_terms)}: {found_terms}'
            result['passed'] = len(found_terms) == count
            if count > 0:
                result['score'] = 100 if result['passed'] else max(0, round(100 - abs(len(found_terms) - count) / count * 100))
            else:
                result['score'] = 100 if result['passed'] else 0

        elif ctype == 'technical_terms_forbidden':
            terms = constraint['terms']
            found_terms = [t for t in terms if t.lower() in text_lower]
            result['expected'] = f'Zero terms from {terms}'
            result['actual'] = f'Found {len(found_terms)}: {found_terms}' if found_terms else 'None found (good)'
            result['passed'] = len(found_terms) == 0
            result['score'] = 100 if result['passed'] else max(0, round(100 - len(found_terms) * 30))

        elif ctype == 'item_count':
            count = constraint['count']
            item_type = constraint['item_type']
            result['expected'] = f'Exactly {count} {item_type}'
            # Try to count semicolon-separated items or numbered items
            semicolon_items = len([x for x in response_text.split(';') if x.strip()])
            result['actual'] = f'~{semicolon_items} items (semicolon-separated)'
            result['passed'] = semicolon_items == count
            result['score'] = 100 if result['passed'] else max(0, round(100 - abs(semicolon_items - count) * 30))

        elif ctype == 'sentences_per_section':
            count = constraint['count']
            result['expected'] = f'{count} sentences per section'
            # Try to detect sections and count sentences in each
            sections = re.split(r'\n(?=[A-Z\*#])', response_text)
            if len(sections) > 1:
                issues = []
                for sec in sections:
                    sec_sentences = tokenize_sentences(sec)
                    if len(sec_sentences) != count and len(sec.strip()) > 10:
                        issues.append(f'{len(sec_sentences)} sentences')
                result['actual'] = f'{len(issues)} sections with wrong count' if issues else 'All sections correct'
                result['passed'] = len(issues) == 0
                result['score'] = 100 if result['passed'] else max(0, round(100 - len(issues) * 20))
            else:
                result['actual'] = 'Could not detect sections'
                result['score'] = 50

        elif ctype == 'no_apologies':
            result['expected'] = 'No apologies'
            apology_found = bool(re.search(r'\b(?:sorry|apolog|regret|inconvenience)\b', text_lower))
            result['actual'] = 'Apology found (violation!)' if apology_found else 'No apologies (good)'
            result['passed'] = not apology_found
            result['score'] = 100 if not apology_found else 0

        elif ctype == 'semicolon_separated':
            result['expected'] = 'Items separated by semicolons'
            has_semicolons = ';' in response_text
            result['actual'] = 'Uses semicolons' if has_semicolons else 'No semicolons found'
            result['passed'] = has_semicolons
            result['score'] = 100 if has_semicolons else 0

        elif ctype == 'requires_next_step':
            result['expected'] = 'Includes a next step'
            next_step_patterns = [
                r'please\s+(?:reply|send|confirm|let|share|provide|submit|review|reach)',
                r'next\s+step',
                r'(?:our|your)\s+(?:next|immediate)\s+(?:action|step)',
                r'(?:will|going to|plan to)\s+\w+',
                r'(?:follow up|update|check in|circle back)',
            ]
            found = any(re.search(p, text_lower) for p in next_step_patterns)
            result['actual'] = 'Next step found' if found else 'No clear next step'
            result['passed'] = found
            result['score'] = 100 if found else 0

        elif ctype == 'confidence_statement':
            result['expected'] = 'Includes confidence statement'
            conf_patterns = [
                r'(?:we are|i am|we\'re|i\'m)\s+confident',
                r'(?:we|i)\s+(?:firmly\s+)?believe',
                r'(?:confident|sure|certain|assured)\s+that',
                r'rest\s+assured',
            ]
            found = any(re.search(p, text_lower) for p in conf_patterns)
            result['actual'] = 'Confidence statement found' if found else 'Not found'
            result['passed'] = found
            result['score'] = 100 if found else 0

        elif ctype == 'required_email':
            email = constraint['email']
            result['expected'] = f'Contains: {email}'
            found = email.lower() in text_lower
            result['actual'] = 'Found' if found else 'Not found'
            result['passed'] = found
            result['score'] = 100 if found else 0

        elif ctype == 'output_format':
            fmt = constraint['format']
            result['expected'] = f'Format: {fmt}'
            # Check if A) and B) format is present
            if 'A)' in fmt or 'a)' in fmt.lower():
                has_a = bool(re.search(r'\bA\)', response_text))
                has_b = bool(re.search(r'\bB\)', response_text))
                result['actual'] = f'A)={has_a}, B)={has_b}'
                result['passed'] = has_a and has_b
                result['score'] = 100 if result['passed'] else (50 if has_a or has_b else 0)
            else:
                result['actual'] = 'Format check not specific'
                result['score'] = 50

        results.append(result)

    # Compute total constraint adherence score
    if results:
        total_score = round(sum(r['score'] for r in results) / len(results), 2)
    else:
        total_score = 100  # No constraints = full score

    return {
        'constraints': results,
        'total_score': total_score,
        'total_constraints': len(results),
        'passed_count': sum(1 for r in results if r['passed']),
        'failed_count': sum(1 for r in results if not r['passed'])
    }


def _detect_tone(text):
    """Basic tone detection for constraint checking."""
    words = tokenize_words(text)
    text_lower = text.lower()
    scores = {}

    # Professional tone indicators
    from metrics_engine import FORMAL_INDICATORS, INFORMAL_INDICATORS
    formal_count = sum(1 for w in words if w in FORMAL_INDICATORS)
    informal_count = sum(1 for w in words if w in INFORMAL_INDICATORS)
    contractions = len(re.findall(r"\b\w+'\w+\b", text))

    scores['professional'] = min(100, max(0, 50 + formal_count * 10 - informal_count * 10 - contractions * 5))
    scores['formal'] = scores['professional']
    scores['neutral'] = 70 if formal_count < 5 and informal_count < 3 else 50
    scores['informative'] = min(100, 50 + len(words) // 10)

    # Non-accusatory
    accusatory_words = ['blame', 'fault', 'failed', 'neglect', 'irresponsible', 'unacceptable']
    accusatory_count = sum(1 for w in words if w in accusatory_words)
    scores['non-accusatory'] = max(0, 100 - accusatory_count * 30)

    scores['friendly'] = min(100, max(0, 50 + informal_count * 5 - formal_count * 3))
    scores['persuasive'] = min(100, max(0, 50 + sum(1 for w in words if w in {'should', 'must', 'consider', 'recommend', 'strongly', 'important', 'essential', 'crucial'})) * 10)

    return scores
