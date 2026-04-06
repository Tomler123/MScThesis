"""
metrics.py — NLP Evaluation Metrics for Summarization Quality

Implements reference-based and reference-free metrics spanning four
evaluation dimensions:
  1. Content Overlap  (ROUGE, BLEU, Cosine Similarity, BERTScore)
  2. Readability       (Flesch RE, Flesch-Kincaid, Gunning Fog)
  3. Informativeness   (Compression Ratio, Lexical Diversity, Information Density)
  4. Coherence         (Inter-sentence Cosine Coherence)
"""

import re
import math
import numpy as np
from collections import Counter

# ── Optional heavy imports (graceful fallback) ────────────────────────────
try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except ImportError:
    ROUGE_AVAILABLE = False

try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as sk_cosine
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from bert_score import score as bert_score_fn
    BERT_AVAILABLE = True
except ImportError:
    BERT_AVAILABLE = False

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    # Ensure punkt data is available
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', quiet=True)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════
# Helper utilities
# ═══════════════════════════════════════════════════════════════════════════

def _tokenize_words(text: str) -> list:
    """Tokenize text into words."""
    if NLTK_AVAILABLE:
        return word_tokenize(text.lower())
    return re.findall(r'\b\w+\b', text.lower())


def _tokenize_sentences(text: str) -> list:
    """Tokenize text into sentences."""
    if NLTK_AVAILABLE:
        return sent_tokenize(text)
    return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]


def _get_stopwords() -> set:
    """Return English stopwords."""
    if NLTK_AVAILABLE:
        from nltk.corpus import stopwords
        return set(stopwords.words('english'))
    # Fallback minimal set
    return {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
        'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
        'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'between', 'out', 'off', 'over', 'under', 'again', 'further', 'then',
        'once', 'and', 'but', 'or', 'nor', 'not', 'so', 'yet', 'both',
        'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
        'only', 'own', 'same', 'than', 'too', 'very', 'just', 'because',
        'this', 'that', 'these', 'those', 'i', 'me', 'my', 'we', 'our',
        'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it', 'its',
        'they', 'them', 'their', 'what', 'which', 'who', 'whom',
    }


def _ngrams(tokens: list, n: int) -> list:
    """Generate n-grams from a token list."""
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


# ═══════════════════════════════════════════════════════════════════════════
# 1. CONTENT OVERLAP METRICS (reference-based)
# ═══════════════════════════════════════════════════════════════════════════

def compute_rouge(reference: str, summary: str) -> dict:
    """ROUGE-1, ROUGE-2, ROUGE-L (precision, recall, F1 each)."""
    if not ROUGE_AVAILABLE or not reference.strip() or not summary.strip():
        return {
            'rouge1_f': 0.0, 'rouge1_p': 0.0, 'rouge1_r': 0.0,
            'rouge2_f': 0.0, 'rouge2_p': 0.0, 'rouge2_r': 0.0,
            'rougeL_f': 0.0, 'rougeL_p': 0.0, 'rougeL_r': 0.0,
        }
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(reference, summary)
    return {
        'rouge1_f': round(scores['rouge1'].fmeasure, 4),
        'rouge1_p': round(scores['rouge1'].precision, 4),
        'rouge1_r': round(scores['rouge1'].recall, 4),
        'rouge2_f': round(scores['rouge2'].fmeasure, 4),
        'rouge2_p': round(scores['rouge2'].precision, 4),
        'rouge2_r': round(scores['rouge2'].recall, 4),
        'rougeL_f': round(scores['rougeL'].fmeasure, 4),
        'rougeL_p': round(scores['rougeL'].precision, 4),
        'rougeL_r': round(scores['rougeL'].recall, 4),
    }


def compute_bleu(reference: str, summary: str, max_n: int = 4) -> dict:
    """
    BLEU score (1-gram through max_n-gram) with brevity penalty.
    Custom implementation — no external dependency beyond tokenization.
    """
    ref_tokens = _tokenize_words(reference)
    hyp_tokens = _tokenize_words(summary)

    if not ref_tokens or not hyp_tokens:
        return {'bleu': 0.0, 'bleu_1': 0.0, 'bleu_2': 0.0,
                'bleu_3': 0.0, 'bleu_4': 0.0, 'brevity_penalty': 0.0}

    # Brevity penalty
    bp = 1.0 if len(hyp_tokens) >= len(ref_tokens) else \
        math.exp(1 - len(ref_tokens) / max(len(hyp_tokens), 1))

    precisions = {}
    for n in range(1, max_n + 1):
        ref_ng = Counter(_ngrams(ref_tokens, n))
        hyp_ng = Counter(_ngrams(hyp_tokens, n))
        clipped = sum(min(hyp_ng[ng], ref_ng[ng]) for ng in hyp_ng)
        total = max(sum(hyp_ng.values()), 1)
        precisions[n] = clipped / total

    # Geometric mean of precisions (with smoothing)
    log_avg = 0.0
    for n in range(1, max_n + 1):
        p = precisions.get(n, 0)
        log_avg += math.log(max(p, 1e-10)) / max_n

    bleu = bp * math.exp(log_avg)

    return {
        'bleu': round(bleu, 4),
        'bleu_1': round(precisions.get(1, 0), 4),
        'bleu_2': round(precisions.get(2, 0), 4),
        'bleu_3': round(precisions.get(3, 0), 4),
        'bleu_4': round(precisions.get(4, 0), 4),
        'brevity_penalty': round(bp, 4),
    }


def compute_cosine_similarity(reference: str, summary: str) -> float:
    """TF-IDF cosine similarity between source and summary."""
    if not SKLEARN_AVAILABLE or not reference.strip() or not summary.strip():
        return 0.0
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf = vectorizer.fit_transform([reference, summary])
        sim = sk_cosine(tfidf[0:1], tfidf[1:2])[0][0]
        return round(float(sim), 4)
    except Exception:
        return 0.0


def compute_bert_score(reference: str, summary: str) -> dict:
    """BERTScore (precision, recall, F1) — requires torch + bert-score."""
    if not BERT_AVAILABLE or not reference.strip() or not summary.strip():
        return {'bertscore_p': 0.0, 'bertscore_r': 0.0, 'bertscore_f': 0.0,
                'bertscore_available': False}
    try:
        P, R, F1 = bert_score_fn(
            [summary], [reference],
            lang='en', verbose=False,
            model_type='distilbert-base-uncased'  # lighter model
        )
        return {
            'bertscore_p': round(P.item(), 4),
            'bertscore_r': round(R.item(), 4),
            'bertscore_f': round(F1.item(), 4),
            'bertscore_available': True,
        }
    except Exception:
        return {'bertscore_p': 0.0, 'bertscore_r': 0.0, 'bertscore_f': 0.0,
                'bertscore_available': False}


# ═══════════════════════════════════════════════════════════════════════════
# 2. READABILITY METRICS (reference-free)
# ═══════════════════════════════════════════════════════════════════════════

def compute_readability(text: str) -> dict:
    """Flesch Reading Ease, Flesch-Kincaid Grade, Gunning Fog Index."""
    if not text.strip():
        return {'flesch_reading_ease': 0.0, 'flesch_kincaid_grade': 0.0,
                'gunning_fog': 0.0}
    if TEXTSTAT_AVAILABLE:
        return {
            'flesch_reading_ease': round(textstat.flesch_reading_ease(text), 2),
            'flesch_kincaid_grade': round(textstat.flesch_kincaid_grade(text), 2),
            'gunning_fog': round(textstat.gunning_fog(text), 2),
        }
    # Manual fallback
    words = _tokenize_words(text)
    sents = _tokenize_sentences(text)
    n_words = max(len(words), 1)
    n_sents = max(len(sents), 1)
    n_syllables = sum(_count_syllables(w) for w in words)
    n_complex = sum(1 for w in words if _count_syllables(w) >= 3)

    fre = 206.835 - 1.015 * (n_words / n_sents) - 84.6 * (n_syllables / n_words)
    fkg = 0.39 * (n_words / n_sents) + 11.8 * (n_syllables / n_words) - 15.59
    gf = 0.4 * ((n_words / n_sents) + 100 * (n_complex / n_words))

    return {
        'flesch_reading_ease': round(fre, 2),
        'flesch_kincaid_grade': round(fkg, 2),
        'gunning_fog': round(gf, 2),
    }


def _count_syllables(word: str) -> int:
    """Estimate syllable count."""
    word = word.lower().strip()
    if len(word) <= 3:
        return 1
    word = re.sub(r'e$', '', word)
    vowel_groups = re.findall(r'[aeiouy]+', word)
    return max(len(vowel_groups), 1)


# ═══════════════════════════════════════════════════════════════════════════
# 3. INFORMATIVENESS METRICS
# ═══════════════════════════════════════════════════════════════════════════

def compute_compression_ratio(source: str, summary: str) -> float:
    """Ratio of summary length to source length (lower = more compressed)."""
    src_words = len(_tokenize_words(source))
    sum_words = len(_tokenize_words(summary))
    if src_words == 0:
        return 0.0
    return round(sum_words / src_words, 4)


def compute_lexical_diversity(text: str) -> float:
    """Type-Token Ratio (TTR) — unique words / total words."""
    words = _tokenize_words(text)
    if not words:
        return 0.0
    return round(len(set(words)) / len(words), 4)


def compute_information_density(text: str) -> float:
    """Ratio of content words (non-stopwords) to total words."""
    words = _tokenize_words(text)
    if not words:
        return 0.0
    stopwords = _get_stopwords()
    content_words = [w for w in words if w not in stopwords and len(w) > 1]
    return round(len(content_words) / len(words), 4)


def compute_redundancy_score(text: str) -> float:
    """
    Measures n-gram repetition (lower = less redundant = better).
    Computes ratio of repeated bigrams to total bigrams.
    """
    words = _tokenize_words(text)
    if len(words) < 3:
        return 0.0
    bigrams = _ngrams(words, 2)
    if not bigrams:
        return 0.0
    counts = Counter(bigrams)
    repeated = sum(c - 1 for c in counts.values() if c > 1)
    return round(repeated / len(bigrams), 4)


# ═══════════════════════════════════════════════════════════════════════════
# 4. COHERENCE METRIC
# ═══════════════════════════════════════════════════════════════════════════

def compute_coherence(text: str) -> float:
    """
    Average cosine similarity between consecutive sentence pairs.
    Higher score → smoother sentence-to-sentence flow.
    Uses TF-IDF vectors for each sentence.
    """
    sents = _tokenize_sentences(text)
    if len(sents) < 2 or not SKLEARN_AVAILABLE:
        return 1.0  # Single-sentence summaries are trivially coherent
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf = vectorizer.fit_transform(sents)
        similarities = []
        for i in range(len(sents) - 1):
            sim = sk_cosine(tfidf[i:i+1], tfidf[i+1:i+2])[0][0]
            similarities.append(float(sim))
        return round(np.mean(similarities), 4) if similarities else 1.0
    except Exception:
        return 1.0


# ═══════════════════════════════════════════════════════════════════════════
# 5. STATISTICAL NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════

def z_score_normalize(scores_by_model: list, metric_keys: list) -> list:
    """
    Z-score normalization across models for each metric.
    Enables fair cross-metric comparison on a common scale.
    Returns list of dicts with '_z' suffix keys.
    """
    if len(scores_by_model) < 2:
        # Need ≥2 models for meaningful z-scores
        for entry in scores_by_model:
            for k in metric_keys:
                entry['metrics'][f'{k}_z'] = 0.0
        return scores_by_model

    for key in metric_keys:
        values = [m['metrics'].get(key, 0) for m in scores_by_model]
        mean = np.mean(values)
        std = np.std(values)
        for entry in scores_by_model:
            raw = entry['metrics'].get(key, 0)
            entry['metrics'][f'{key}_z'] = round((raw - mean) / std, 4) if std > 0 else 0.0

    return scores_by_model


# ═══════════════════════════════════════════════════════════════════════════
# MASTER EVALUATION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

# Default weights for composite score (all sum to 1.0)
DEFAULT_WEIGHTS = {
    'rouge1_f':           0.10,
    'rouge2_f':           0.08,
    'rougeL_f':           0.08,
    'bleu':               0.06,
    'cosine_similarity':  0.08,
    'flesch_reading_ease': 0.06,
    'compression_ratio':  0.06,
    'lexical_diversity':  0.06,
    'information_density': 0.06,
    'coherence':          0.06,
    'redundancy':         0.05,
    'constraint_adherence': 0.25,
}

# Metrics where lower is better (will be inverted for composite)
LOWER_IS_BETTER = {'compression_ratio', 'gunning_fog', 'flesch_kincaid_grade', 'redundancy'}

# Normalization ranges for each metric to bring to 0-1 scale
METRIC_RANGES = {
    'rouge1_f': (0, 1), 'rouge2_f': (0, 1), 'rougeL_f': (0, 1),
    'bleu': (0, 1), 'cosine_similarity': (0, 1),
    'flesch_reading_ease': (0, 100), 'flesch_kincaid_grade': (0, 18),
    'gunning_fog': (0, 20), 'compression_ratio': (0, 1),
    'lexical_diversity': (0, 1), 'information_density': (0, 1),
    'coherence': (0, 1), 'redundancy': (0, 1),
    'constraint_adherence': (0, 1),
}


def normalize_metric(value: float, key: str) -> float:
    """Normalize a metric to 0–1 scale."""
    lo, hi = METRIC_RANGES.get(key, (0, 1))
    if hi == lo:
        return 0.0
    normed = (value - lo) / (hi - lo)
    normed = max(0.0, min(1.0, normed))
    if key in LOWER_IS_BETTER:
        normed = 1.0 - normed
    return round(normed, 4)


def compute_composite_score(metrics: dict, weights: dict = None) -> float:
    """Weighted composite score from normalized metrics."""
    w = weights or DEFAULT_WEIGHTS
    total_weight = 0.0
    score = 0.0
    for key, weight in w.items():
        if key in metrics:
            normed = normalize_metric(metrics[key], key)
            score += normed * weight
            total_weight += weight
    return round((score / total_weight) * 100, 2) if total_weight > 0 else 0.0


def compute_all_metrics(source_text: str, summary: str,
                        reference: str = '', use_bert: bool = False) -> dict:
    """
    Master function: compute ALL metrics for a single model response.

    Parameters
    ----------
    source_text : str
        The original text/document that was summarized.
    summary : str
        The model's summary output.
    reference : str, optional
        Gold-standard reference summary (if available).
        Falls back to source_text for reference-based metrics.
    use_bert : bool
        Whether to compute BERTScore (slow, requires torch).

    Returns
    -------
    dict with all metric values.
    """
    ref = reference.strip() if reference.strip() else source_text

    results = {}

    # Content overlap
    results.update(compute_rouge(ref, summary))
    results.update(compute_bleu(ref, summary))
    results['cosine_similarity'] = compute_cosine_similarity(ref, summary)

    if use_bert:
        results.update(compute_bert_score(ref, summary))
    else:
        results['bertscore_p'] = None
        results['bertscore_r'] = None
        results['bertscore_f'] = None
        results['bertscore_available'] = False

    # Readability
    results.update(compute_readability(summary))

    # Informativeness
    results['compression_ratio'] = compute_compression_ratio(source_text, summary)
    results['lexical_diversity'] = compute_lexical_diversity(summary)
    results['information_density'] = compute_information_density(summary)
    results['redundancy'] = compute_redundancy_score(summary)

    # Coherence
    results['coherence'] = compute_coherence(summary)

    # Word / sentence counts (metadata)
    results['word_count'] = len(_tokenize_words(summary))
    results['sentence_count'] = len(_tokenize_sentences(summary))

    return results
