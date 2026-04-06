from flask import Flask, render_template, request, jsonify
import json
import re
import math
import io
import csv
from collections import Counter

app = Flask(__name__)

# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text):
    return re.findall(r'\b\w+\b', text.lower())

# ============================================================
# METRIC: BLEU (1-gram through N-gram)
# ============================================================

def compute_bleu(reference, hypothesis, max_n=4):
    ref_tokens = tokenize(reference)
    hyp_tokens = tokenize(hypothesis)
    if not hyp_tokens or not ref_tokens:
        return 0.0
    scores = []
    for n in range(1, max_n + 1):
        if len(ref_tokens) < n or len(hyp_tokens) < n:
            scores.append(0.0)
            continue
        ref_ngrams = Counter(tuple(ref_tokens[i:i+n]) for i in range(len(ref_tokens)-n+1))
        hyp_ngrams = Counter(tuple(hyp_tokens[i:i+n]) for i in range(len(hyp_tokens)-n+1))
        total_hyp = sum(hyp_ngrams.values())
        if total_hyp == 0:
            scores.append(0.0)
            continue
        clipped = sum(min(count, ref_ngrams[gram]) for gram, count in hyp_ngrams.items())
        scores.append(clipped / total_hyp)
    nonzero = [s for s in scores if s > 0]
    if not nonzero:
        return 0.0
    log_avg = sum(math.log(s) for s in nonzero) / len(nonzero)
    bp = math.exp(min(0.0, 1.0 - len(ref_tokens) / max(len(hyp_tokens), 1)))
    return round(bp * math.exp(log_avg), 4)

# ============================================================
# METRIC: ROUGE-N and ROUGE-L
# ============================================================

def compute_rouge_n(reference, hypothesis, n=1):
    ref_tokens = tokenize(reference)
    hyp_tokens = tokenize(hypothesis)
    if not ref_tokens or not hyp_tokens:
        return {'p': 0.0, 'r': 0.0, 'f1': 0.0}
    ref_ngrams = Counter(tuple(ref_tokens[i:i+n]) for i in range(max(0, len(ref_tokens)-n+1)))
    hyp_ngrams = Counter(tuple(hyp_tokens[i:i+n]) for i in range(max(0, len(hyp_tokens)-n+1)))
    matches = sum(min(ref_ngrams[g], hyp_ngrams[g]) for g in hyp_ngrams)
    recall = matches / max(sum(ref_ngrams.values()), 1)
    precision = matches / max(sum(hyp_ngrams.values()), 1)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {'p': round(precision, 4), 'r': round(recall, 4), 'f1': round(f1, 4)}

def compute_rouge_l(reference, hypothesis):
    ref_tokens = tokenize(reference)
    hyp_tokens = tokenize(hypothesis)
    m, n = len(ref_tokens), len(hyp_tokens)
    if m == 0 or n == 0:
        return {'p': 0.0, 'r': 0.0, 'f1': 0.0, 'lcs': 0}
    # Space-optimised LCS DP
    prev = [0] * (n + 1)
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if ref_tokens[i-1] == hyp_tokens[j-1]:
                curr[j] = prev[j-1] + 1
            else:
                curr[j] = max(prev[j], curr[j-1])
        prev = curr
    lcs = prev[n]
    precision = lcs / n
    recall = lcs / m
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {'p': round(precision, 4), 'r': round(recall, 4), 'f1': round(f1, 4), 'lcs': lcs}

# ============================================================
# METRIC: chrF (character n-gram F-score)
# ============================================================

def compute_chrf(reference, hypothesis, char_n=6, beta=2):
    def char_ngrams(text, n):
        t = re.sub(r'\s+', '', text.lower())
        return Counter(t[i:i+n] for i in range(max(0, len(t)-n+1)))
    total_p, total_r, count = 0.0, 0.0, 0
    for n in range(1, char_n + 1):
        ref_ng = char_ngrams(reference, n)
        hyp_ng = char_ngrams(hypothesis, n)
        if not ref_ng or not hyp_ng:
            continue
        matches = sum(min(ref_ng[c], hyp_ng[c]) for c in hyp_ng)
        total_p += matches / sum(hyp_ng.values())
        total_r += matches / sum(ref_ng.values())
        count += 1
    if count == 0:
        return 0.0
    avg_p = total_p / count
    avg_r = total_r / count
    if avg_p + avg_r == 0:
        return 0.0
    return round((1 + beta**2) * avg_p * avg_r / (beta**2 * avg_p + avg_r), 4)

# ============================================================
# METRIC: WER and CER (edit distance based)
# ============================================================

def _edit_distance(seq_r, seq_h):
    m, n = len(seq_r), len(seq_h)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        new_dp = [i] + [0] * n
        for j in range(1, n + 1):
            if seq_r[i-1] == seq_h[j-1]:
                new_dp[j] = dp[j-1]
            else:
                new_dp[j] = 1 + min(dp[j], new_dp[j-1], dp[j-1])
        dp = new_dp
    return dp[n]

def compute_wer(reference, hypothesis):
    r = tokenize(reference)
    h = tokenize(hypothesis)
    if not r:
        return 0.0
    return round(_edit_distance(r, h) / len(r), 4)

def compute_cer(reference, hypothesis):
    r = list(reference.lower().replace(' ', ''))
    h = list(hypothesis.lower().replace(' ', ''))
    if not r:
        return 0.0
    return round(_edit_distance(r, h) / len(r), 4)

# ============================================================
# METRIC: TF-IDF Cosine Similarity
# ============================================================

def compute_tfidf_cosine(doc1, doc2):
    t1 = tokenize(doc1)
    t2 = tokenize(doc2)
    vocab = set(t1) | set(t2)
    if not vocab:
        return 0.0
    def tf(tokens, w):
        return tokens.count(w) / len(tokens) if tokens else 0.0
    def idf(w):
        containing = (1 if w in t1 else 0) + (1 if w in t2 else 0)
        return math.log((3) / (containing + 1)) + 1  # smoothed IDF
    vec1 = {w: tf(t1, w) * idf(w) for w in vocab}
    vec2 = {w: tf(t2, w) * idf(w) for w in vocab}
    dot = sum(vec1[w] * vec2[w] for w in vocab)
    mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
    if mag1 * mag2 == 0:
        return 0.0
    return round(dot / (mag1 * mag2), 4)

# ============================================================
# METRIC: Jaccard Similarity
# ============================================================

def compute_jaccard(text1, text2):
    s1 = set(tokenize(text1))
    s2 = set(tokenize(text2))
    if not s1 and not s2:
        return 1.0
    return round(len(s1 & s2) / len(s1 | s2), 4)

# ============================================================
# METRIC: Length Analysis
# ============================================================

def compute_length_ratio(reference, hypothesis):
    r_len = len(tokenize(reference))
    h_len = len(tokenize(hypothesis))
    if r_len == 0:
        return 0.0
    return round(h_len / r_len, 4)

def compute_length_ratio_score(ratio):
    return round(max(0.0, 1.0 - abs(1.0 - ratio)), 4)

# ============================================================
# METRIC: Lexical Diversity (Type-Token Ratio)
# ============================================================

def compute_lexical_diversity(text):
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    return round(len(set(tokens)) / len(tokens), 4)

# ============================================================
# METRIC: Content Word Overlap (stopword-filtered Jaccard)
# ============================================================

STOPWORDS = {
    'the','a','an','is','are','was','were','be','been','being','have','has','had',
    'do','does','did','will','would','could','should','may','might','shall','can',
    'to','of','in','on','at','by','for','with','from','as','it','its','this','that',
    'these','those','and','or','but','not','so','if','then','than','when','where',
    'which','who','what','how','all','each','every','both','few','more','most','i',
    'we','you','he','she','they','me','us','him','her','them','my','our','your',
    'his','their','its','about','up','out','into','just','also','very','such'
}

def compute_content_word_overlap(text1, text2):
    t1 = set(w for w in tokenize(text1) if w not in STOPWORDS and len(w) > 3)
    t2 = set(w for w in tokenize(text2) if w not in STOPWORDS and len(w) > 3)
    if not t1 and not t2:
        return 1.0
    if not t1 or not t2:
        return 0.0
    return round(len(t1 & t2) / len(t1 | t2), 4)

# ============================================================
# METRIC: Bigram Overlap (meaning-preserving structure)
# ============================================================

def compute_bigram_overlap(text1, text2):
    t1 = tokenize(text1)
    t2 = tokenize(text2)
    if len(t1) < 2 or len(t2) < 2:
        return 0.0
    bg1 = set(tuple(t1[i:i+2]) for i in range(len(t1)-1))
    bg2 = set(tuple(t2[i:i+2]) for i in range(len(t2)-1))
    if not bg1 and not bg2:
        return 1.0
    return round(len(bg1 & bg2) / len(bg1 | bg2), 4)

# ============================================================
# METRIC: Sentence-Level Overlap (paragraph similarity)
# ============================================================

def compute_sentence_overlap(text1, text2):
    def split_sentences(text):
        return [s.strip().lower() for s in re.split(r'[.!?]+', text) if s.strip()]
    sents1 = split_sentences(text1)
    sents2 = split_sentences(text2)
    if not sents1 or not sents2:
        return 0.0
    # For each sentence in ref, find best jaccard match in hypothesis
    total = 0.0
    for s1 in sents1:
        best = max(
            compute_jaccard(s1, s2) for s2 in sents2
        )
        total += best
    return round(total / len(sents1), 4)

# ============================================================
# COMPOSITE SCORE
# ============================================================

COMPOSITE_METRICS = {
    'bleu_4':              ('positive', 'Meaning Preservation'),
    'rouge_1_f1':          ('positive', 'Meaning Preservation'),
    'rouge_l_f1':          ('positive', 'Meaning Preservation'),
    'chrf':                ('positive', 'Meaning Preservation'),
    'tfidf_cosine':        ('positive', 'Semantic Similarity'),
    'jaccard':             ('positive', 'Semantic Similarity'),
    'content_word_overlap':('positive', 'Semantic Similarity'),
    'bigram_overlap':      ('positive', 'Structural'),
    'wer':                 ('negative', 'Fluency'),
    'cer':                 ('negative', 'Fluency'),
    'length_score':        ('positive', 'Structural'),
}

WEIGHT_PROFILES = {
    'balanced': {
        'bleu_4': 0.10, 'rouge_1_f1': 0.08, 'rouge_l_f1': 0.10, 'chrf': 0.10,
        'tfidf_cosine': 0.12, 'jaccard': 0.08, 'content_word_overlap': 0.08,
        'bigram_overlap': 0.08, 'wer': 0.13, 'cer': 0.07, 'length_score': 0.06
    },
    'meaning_heavy': {
        'bleu_4': 0.18, 'rouge_1_f1': 0.10, 'rouge_l_f1': 0.15, 'chrf': 0.15,
        'tfidf_cosine': 0.12, 'jaccard': 0.10, 'content_word_overlap': 0.10,
        'bigram_overlap': 0.06, 'wer': 0.02, 'cer': 0.01, 'length_score': 0.01
    },
    'fluency_heavy': {
        'bleu_4': 0.05, 'rouge_1_f1': 0.04, 'rouge_l_f1': 0.05, 'chrf': 0.06,
        'tfidf_cosine': 0.06, 'jaccard': 0.05, 'content_word_overlap': 0.05,
        'bigram_overlap': 0.04, 'wer': 0.35, 'cer': 0.15, 'length_score': 0.10
    }
}

def compute_composite_score(metrics, weights):
    score = 0.0
    total_w = 0.0
    for key, w in weights.items():
        if key not in metrics:
            continue
        direction = COMPOSITE_METRICS.get(key, ('positive', ''))[0]
        val = metrics[key]
        if direction == 'negative':
            val = max(0.0, 1.0 - min(val, 1.0))
        score += w * val
        total_w += w
    if total_w == 0:
        return 0.0
    return round(score / total_w, 4)

# ============================================================
# Z-SCORE NORMALIZATION
# ============================================================

def compute_z_scores(entries, metric_keys):
    z_map = {}
    for key in metric_keys:
        values = []
        for e in entries:
            v = e.get('metrics', {}).get(key)
            if v is not None:
                values.append(v)
        if len(values) < 2:
            for e in entries:
                z_map.setdefault(e['id'], {})[key] = 0.0
            continue
        mean = sum(values) / len(values)
        std = math.sqrt(sum((v - mean)**2 for v in values) / len(values))
        for e in entries:
            v = e.get('metrics', {}).get(key, mean)
            z = (v - mean) / std if std > 0 else 0.0
            z_map.setdefault(e['id'], {})[key] = round(z, 4)
    return z_map

# ============================================================
# MASTER COMPUTE FUNCTION
# ============================================================

def compute_all_metrics(original, back_translation):
    bleu1  = compute_bleu(original, back_translation, max_n=1)
    bleu2  = compute_bleu(original, back_translation, max_n=2)
    bleu4  = compute_bleu(original, back_translation, max_n=4)
    rouge1 = compute_rouge_n(original, back_translation, 1)
    rouge2 = compute_rouge_n(original, back_translation, 2)
    rougeL = compute_rouge_l(original, back_translation)
    chrf   = compute_chrf(original, back_translation)
    wer    = compute_wer(original, back_translation)
    cer    = compute_cer(original, back_translation)
    tfidf  = compute_tfidf_cosine(original, back_translation)
    jaccard = compute_jaccard(original, back_translation)
    len_ratio = compute_length_ratio(original, back_translation)
    len_score = compute_length_ratio_score(len_ratio)
    lex_orig  = compute_lexical_diversity(original)
    lex_bt    = compute_lexical_diversity(back_translation)
    content   = compute_content_word_overlap(original, back_translation)
    bigram    = compute_bigram_overlap(original, back_translation)
    sent_ov   = compute_sentence_overlap(original, back_translation)

    orig_word_count = len(tokenize(original))
    bt_word_count   = len(tokenize(back_translation))

    return {
        'bleu_1': bleu1, 'bleu_2': bleu2, 'bleu_4': bleu4,
        'rouge_1_p': rouge1['p'], 'rouge_1_r': rouge1['r'], 'rouge_1_f1': rouge1['f1'],
        'rouge_2_p': rouge2['p'], 'rouge_2_r': rouge2['r'], 'rouge_2_f1': rouge2['f1'],
        'rouge_l_p': rougeL['p'], 'rouge_l_r': rougeL['r'], 'rouge_l_f1': rougeL['f1'],
        'chrf': chrf,
        'wer': wer, 'cer': cer,
        'tfidf_cosine': tfidf,
        'jaccard': jaccard,
        'length_ratio': len_ratio, 'length_score': len_score,
        'lex_div_original': lex_orig, 'lex_div_backtranslation': lex_bt,
        'content_word_overlap': content,
        'bigram_overlap': bigram,
        'sentence_overlap': sent_ov,
        'orig_word_count': orig_word_count,
        'bt_word_count': bt_word_count,
    }

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    original        = data.get('original', '').strip()
    back_translation = data.get('back_translation', '').strip()
    if not original or not back_translation:
        return jsonify({'error': 'Missing required fields: original and back_translation'}), 400
    metrics = compute_all_metrics(original, back_translation)
    return jsonify({'metrics': metrics})


@app.route('/api/composite', methods=['POST'])
def composite():
    data    = request.get_json()
    entries = data.get('entries', [])   # [{id, metrics}, ...]
    weights = data.get('weights', {})
    profile = data.get('profile', 'balanced')
    if not weights:
        weights = WEIGHT_PROFILES.get(profile, WEIGHT_PROFILES['balanced'])

    results = []
    for entry in entries:
        cs = compute_composite_score(entry['metrics'], weights)
        results.append({'id': entry['id'], 'composite': cs})

    z_keys = list(COMPOSITE_METRICS.keys())
    z_scores = compute_z_scores(entries, z_keys)

    # Cross-model statistics per language pair
    lang_groups = {}
    for entry in entries:
        lp = entry.get('language_pair', 'Unknown')
        lang_groups.setdefault(lp, []).append(entry)

    lang_stats = {}
    for lp, group in lang_groups.items():
        for key in z_keys:
            vals = [e['metrics'].get(key, 0) for e in group if key in e.get('metrics', {})]
            if not vals:
                continue
            mean = sum(vals) / len(vals)
            std  = math.sqrt(sum((v - mean)**2 for v in vals) / len(vals)) if len(vals) > 1 else 0
            lang_stats.setdefault(lp, {})[key] = {
                'mean': round(mean, 4),
                'std':  round(std, 4),
                'min':  round(min(vals), 4),
                'max':  round(max(vals), 4),
            }

    return jsonify({
        'composite_scores': results,
        'z_scores': z_scores,
        'lang_stats': lang_stats,
        'weights_used': weights,
        'profile': profile,
    })


@app.route('/api/llm-prompt', methods=['POST'])
def llm_prompt():
    """Build and return the judge prompt so the browser can call Groq directly."""
    data             = request.get_json()
    original         = data.get('original', '')
    translation      = data.get('translation', '')
    back_translation = data.get('back_translation', '')
    lang_pair        = data.get('lang_pair', 'EN→?')
    model_name       = data.get('model_name', 'Unknown')

    src_lang = lang_pair.split('→')[0].strip() if '→' in lang_pair else 'English'
    tgt_lang = lang_pair.split('→')[1].strip() if '→' in lang_pair else 'Unknown'

    prompt = (
        f"You are an expert computational linguist and translation quality evaluator "
        f"specializing in back-translation analysis.\n\n"
        f"MODEL: {model_name}\n"
        f"LANGUAGE PAIR: {lang_pair} (back-translation method)\n\n"
        f"ORIGINAL {src_lang} TEXT (A):\n\"\"\"\n{original[:2500]}\n\"\"\"\n\n"
        f"MODEL TRANSLATION \u2192 {tgt_lang} (B):\n\"\"\"\n{translation[:2500]}\n\"\"\"\n\n"
        f"BACK-TRANSLATION \u2192 {src_lang} (C):\n\"\"\"\n{back_translation[:2500]}\n\"\"\"\n\n"
        f"Evaluate translation quality across these 5 dimensions. Score 0-10 (10 = perfect).\n\n"
        f"1. Translation Accuracy: How faithfully does (B) convey the meaning and nuances of (A)?\n"
        f"2. Fluency: How natural, fluid, and readable is the back-translation (C) in {src_lang}?\n"
        f"3. Meaning Preservation: After the full A\u2192B\u2192C round-trip, how much original meaning survived?\n"
        f"4. Naturalness: How natural does (B) likely read to a native {tgt_lang} speaker?\n"
        f"5. Grammatical Correctness: Grammatical quality of the back-translation (C).\n\n"
        f"Respond ONLY in raw JSON (no markdown, no backticks, no preamble):\n"
        f'{{\"translation_accuracy\":{{\"score\":0,\"justification\":\"\"}},\"fluency\":{{\"score\":0,\"justification\":\"\"}},\"meaning_preservation\":{{\"score\":0,\"justification\":\"\"}},\"naturalness\":{{\"score\":0,\"justification\":\"\"}},\"grammatical_correctness\":{{\"score\":0,\"justification\":\"\"}},\"overall_score\":0,\"overall_assessment\":\"\"}}'
    )

    return jsonify({'prompt': prompt})


@app.route('/api/export', methods=['POST'])
def export():
    data       = request.get_json()
    fmt        = data.get('format', 'csv')
    entries    = data.get('entries', [])

    if fmt == 'json':
        return jsonify({'data': json.dumps(entries, indent=2, ensure_ascii=False),
                        'filename': 'translation_evaluation.json'})

    # CSV export
    fieldnames = [
        'id', 'model_name', 'language_pair', 'composite_score',
        'bleu_1', 'bleu_2', 'bleu_4',
        'rouge_1_f1', 'rouge_2_f1', 'rouge_l_f1',
        'chrf', 'wer', 'cer',
        'tfidf_cosine', 'jaccard',
        'length_ratio', 'length_score',
        'content_word_overlap', 'bigram_overlap', 'sentence_overlap',
        'lex_div_original', 'lex_div_backtranslation',
        'orig_word_count', 'bt_word_count',
        'llm_overall_score', 'llm_translation_accuracy',
        'llm_fluency', 'llm_meaning_preservation',
        'llm_naturalness', 'llm_grammatical_correctness'
    ]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for entry in entries:
        row = {
            'id': entry.get('id'),
            'model_name': entry.get('model_name'),
            'language_pair': entry.get('language_pair'),
            'composite_score': entry.get('composite_score', ''),
        }
        row.update(entry.get('metrics', {}))
        judge = entry.get('judge', {})
        if judge:
            row['llm_overall_score']         = judge.get('overall_score', '')
            row['llm_translation_accuracy']  = judge.get('translation_accuracy', {}).get('score', '')
            row['llm_fluency']               = judge.get('fluency', {}).get('score', '')
            row['llm_meaning_preservation']  = judge.get('meaning_preservation', {}).get('score', '')
            row['llm_naturalness']           = judge.get('naturalness', {}).get('score', '')
            row['llm_grammatical_correctness']= judge.get('grammatical_correctness', {}).get('score', '')
        writer.writerow(row)
    return jsonify({'data': out.getvalue(), 'filename': 'translation_evaluation.csv'})


@app.route('/api/weight-profiles', methods=['GET'])
def weight_profiles():
    return jsonify(WEIGHT_PROFILES)

if __name__ == '__main__':
    app.run(debug=True, port=5000)