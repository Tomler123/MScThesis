"""
Writing & Communication Evaluation Metrics Engine
Implements comprehensive NLP/data-science metrics from scratch.
No external NLP libraries required — uses sklearn, numpy, scipy + stdlib only.
"""

import re
import math
import string
import numpy as np
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy import stats as scipy_stats


# ─────────────────────────────────────────────
# TEXT PROCESSING UTILITIES
# ─────────────────────────────────────────────

def tokenize_sentences(text):
    """Rule-based sentence tokenizer."""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    # Handle common abbreviations
    abbrevs = r'(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|Inc|Ltd|Corp|dept|approx|i\.e|e\.g|a\.m|p\.m|Fig|No|Vol|Rev|Gen|Gov|Sgt|Cpl|Pvt|Capt|Lt|Col|Maj|Brig|Est|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.'
    text = re.sub(abbrevs, lambda m: m.group().replace('.', '<DOT>'), text)
    # Split on sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'])', text)
    sentences = [s.replace('<DOT>', '.').strip() for s in sentences if s.strip()]
    # Post-filter: merge very short fragments
    merged = []
    for s in sentences:
        if merged and len(s.split()) <= 2 and not s.endswith(('.', '!', '?')):
            merged[-1] += ' ' + s
        else:
            merged.append(s)
    return merged if merged else [text]


def tokenize_words(text):
    """Tokenize into lowercase words, stripping punctuation."""
    return re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?", text.lower())


def tokenize_paragraphs(text):
    """Split text into paragraphs. Handles email format, letters, etc."""
    # Primary split on blank lines
    paras = re.split(r'\n\s*\n', text.strip())
    result = []
    for p in paras:
        p = p.strip()
        # Filter out very short lines that are signatures, greetings alone, or formatting
        if not p or len(p) < 3:
            continue
        # Don't count standalone greeting/closing lines as separate paragraphs
        # unless they're part of a paragraph with more content
        lines = [l.strip() for l in p.split('\n') if l.strip()]
        if len(lines) == 1 and len(p.split()) <= 4:
            # Single short line: check if it's a greeting/closing
            if re.match(r'^(?:dear|hi|hello|hey|best|regards|sincerely|cheers|thanks|thank you|subject:|re:)', p.lower()):
                continue
        result.append(p)
    # If no blank-line paragraphs found, fall back to newline splitting
    if len(result) <= 1 and '\n' in text:
        lines = [l.strip() for l in text.strip().split('\n') if l.strip() and len(l.strip()) > 10]
        if len(lines) > 1:
            return lines
    return result if result else [text.strip()]


def count_syllables(word):
    """Estimate syllable count using rule-based approach."""
    word = word.lower().strip()
    if len(word) <= 3:
        return 1
    # Remove trailing e
    if word.endswith('e') and not word.endswith('le') and len(word) > 3:
        word = word[:-1]
    # Count vowel groups
    count = len(re.findall(r'[aeiouy]+', word))
    # Handle special endings
    if word.endswith('le') and len(word) > 2 and word[-3] not in 'aeiouy':
        count += 1
    if word.endswith(('tion', 'sion', 'cian')):
        count = max(count, 2)
    return max(1, count)


def is_complex_word(word):
    """Check if a word is complex (3+ syllables, not common suffixes)."""
    syllables = count_syllables(word)
    if syllables >= 3:
        if word.endswith(('ed', 'es', 'ing', 'ly')):
            return count_syllables(re.sub(r'(ed|es|ing|ly)$', '', word)) >= 3
        return True
    return False


# ─────────────────────────────────────────────
# SENTIMENT & TONE LEXICONS (built-in)
# ─────────────────────────────────────────────

POSITIVE_WORDS = set("""
good great excellent wonderful fantastic amazing outstanding superb brilliant
perfect beautiful delightful exceptional magnificent marvelous spectacular
terrific fabulous incredible awesome remarkable impressive splendid wonderful
happy pleased glad satisfied grateful thankful hopeful optimistic confident
excited enthusiastic eager passionate inspired motivated encouraged proud
successful effective efficient productive beneficial valuable helpful useful
important significant meaningful substantial considerable noteworthy
creative innovative inventive resourceful talented skilled competent capable
reliable trustworthy dependable consistent dedicated committed devoted loyal
friendly warm kind generous compassionate caring supportive understanding
""".split())

NEGATIVE_WORDS = set("""
bad terrible awful horrible dreadful appalling atrocious deplorable disastrous
poor weak inadequate insufficient unsatisfactory disappointing mediocre
sad unhappy depressed miserable sorrowful gloomy dismal distressed troubled
angry furious enraged hostile aggressive confrontational accusatory harsh
difficult problematic challenging troublesome complicated complex confusing
dangerous hazardous risky threatening harmful destructive damaging detrimental
ugly unpleasant disagreeable offensive repulsive revolting disgusting
failed unsuccessful ineffective inefficient wasteful useless pointless
unreliable undependable inconsistent careless negligent irresponsible
rude impolite disrespectful inconsiderate insensitive thoughtless unkind
worried anxious nervous fearful scared frightened concerned alarmed
broken damaged flawed defective faulty imperfect incomplete missing
urgent desperate critical severe extreme excessive overwhelming unbearable
""".split())

SUBJECTIVE_WORDS = set("""
think believe feel opinion personally seems appears likely probably
perhaps maybe possibly somewhat rather quite fairly pretty actually
honestly frankly truly genuinely certainly definitely absolutely
obviously clearly evidently apparently supposedly presumably
best worst better worse favorite preferred recommended
love hate prefer enjoy dislike appreciate value admire
beautiful ugly amazing terrible wonderful horrible fantastic awful
interesting boring exciting dull fascinating tedious remarkable ordinary
important trivial significant meaningless crucial unnecessary essential
easy difficult simple complicated straightforward confusing
""".split())

FORMAL_INDICATORS = set("""
therefore furthermore moreover consequently subsequently accordingly hence
nevertheless nonetheless notwithstanding albeit whereas whilst
pursuant herein therein thereof whereby wherein henceforth
shall endeavor facilitate implement utilize commence terminate
regarding concerning pertaining respective aforementioned
acknowledge ascertain constitute demonstrate exemplify
substantiate corroborate elucidate delineate articulate
comprehensive preliminary subsequent supplementary
""".split())

INFORMAL_INDICATORS = set("""
gonna wanna gotta kinda sorta yeah nah yep nope ok okay
hey hi hello guys stuff things lot lots pretty really very
awesome cool nice great sweet sick dope lit
can't won't don't isn't aren't wasn't weren't hasn't haven't
shouldn't wouldn't couldn't wouldn't i'm you're we're they're
it's that's what's who's where's there's here's
btw fyi asap lol omg tbh imo imho fwiw
""".split())

TRANSITION_WORDS = set("""
however therefore furthermore moreover additionally consequently
subsequently accordingly nevertheless nonetheless meanwhile
specifically particularly notably significantly importantly
similarly likewise conversely alternatively comparatively
firstly secondly thirdly finally ultimately eventually
in addition in contrast in conclusion in summary for example
for instance as a result on the other hand in particular
to begin with in other words that said above all after all
""".split())

CONTENT_WORDS_POS = set("""
achieve acquire adapt address adjust advance advocate affirm align allocate
analyze apply approach approve arrange assess assign assist assume attach
authorize balance build calculate capture categorize challenge champion
change clarify classify collaborate collect combine communicate compare
compile complete compose compute concentrate conclude conduct configure
confirm connect consider consolidate construct consult contain contribute
control convert coordinate correct create customize define delegate deliver
demonstrate deploy describe design detect determine develop differentiate
discover discuss distribute document draft drive edit elaborate eliminate
emphasize enable encourage engineer enhance ensure establish evaluate
examine execute expand experiment explain explore extend extract facilitate
finalize forecast formulate generate guide identify illustrate implement
improve incorporate indicate influence inform initialize innovate inspect
install integrate interpret introduce investigate isolate justify launch
leverage link locate maintain manage manufacture map maximize measure merge
migrate minimize model modify monitor motivate navigate negotiate normalize
observe obtain operate optimize orchestrate organize outline oversee parse
participate perform persist persuade plan position predict prepare present
preserve prevent prioritize process produce program promote propose protect
provide publish pursue qualify quantify query realize recommend reconcile
record reduce refine register regulate reinforce release relocate remove
repair replace report represent request require research resolve respond
restore restructure retrieve review revise schedule secure select separate
sequence serve simplify simulate solve specify standardize stimulate
strategize streamline strengthen structure submit suggest summarize supervise
support sustain synchronize synthesize target test track train transfer
transform translate troubleshoot uncover understand update upgrade utilize
validate verify visualize volunteer write yield
""".split())


# ─────────────────────────────────────────────
# METRIC COMPUTATION FUNCTIONS
# ─────────────────────────────────────────────

def compute_content_quality(response_text, prompt_text, context_text=""):
    """Compute content quality metrics using TF-IDF and keyword analysis."""
    metrics = {}

    # Combine prompt + context as reference
    reference = prompt_text
    if context_text:
        reference += " " + context_text

    # 1. Cosine Similarity to reference (TF-IDF)
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        tfidf_matrix = vectorizer.fit_transform([reference, response_text])
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        metrics['context_similarity'] = round(float(sim) * 100, 2)
    except:
        metrics['context_similarity'] = 0.0

    # 2. Information Coverage — key terms from reference found in response
    ref_words = set(tokenize_words(reference))
    resp_words = set(tokenize_words(response_text))
    stop_words = set("a an the is are was were be been being have has had do does did will would shall should may might can could and but or nor for so yet at by to from in on with as of".split())
    ref_content = ref_words - stop_words
    if ref_content:
        coverage = len(ref_content & resp_words) / len(ref_content) * 100
        metrics['information_coverage'] = round(coverage, 2)
    else:
        metrics['information_coverage'] = 0.0

    # 3. Key Entity Retention
    # Extract capitalized terms / important nouns from reference
    ref_entities = set(re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', reference))
    if ref_entities:
        retained = sum(1 for e in ref_entities if e.lower() in response_text.lower())
        metrics['entity_retention'] = round(retained / len(ref_entities) * 100, 2)
    else:
        metrics['entity_retention'] = 100.0

    # 4. Relevance Score (combined)
    metrics['relevance_score'] = round(
        0.5 * metrics['context_similarity'] +
        0.3 * metrics['information_coverage'] +
        0.2 * metrics['entity_retention'], 2
    )

    return metrics


def compute_tone_sentiment(text):
    """Compute tone and sentiment metrics using lexicon-based approach."""
    metrics = {}
    words = tokenize_words(text)
    sentences = tokenize_sentences(text)
    total_words = max(len(words), 1)

    # 1. Sentiment Polarity (-1 to 1 range, normalized to 0-100)
    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    if (pos_count + neg_count) > 0:
        polarity = (pos_count - neg_count) / (pos_count + neg_count)
    else:
        polarity = 0.0
    metrics['sentiment_polarity'] = round((polarity + 1) * 50, 2)  # Map to 0-100

    # 2. Subjectivity (ratio of subjective words)
    subj_count = sum(1 for w in words if w in SUBJECTIVE_WORDS)
    subjectivity = min(subj_count / total_words * 10, 1.0)  # Scale up
    metrics['subjectivity'] = round(subjectivity * 100, 2)

    # 3. Formality Score
    formal_count = sum(1 for w in words if w in FORMAL_INDICATORS)
    informal_count = sum(1 for w in words if w in INFORMAL_INDICATORS)
    contraction_count = len(re.findall(r"\b\w+'\w+\b", text))
    informal_count += contraction_count

    if (formal_count + informal_count) > 0:
        formality = formal_count / (formal_count + informal_count)
    else:
        # Check other indicators
        avg_word_len = np.mean([len(w) for w in words]) if words else 5
        formality = min(avg_word_len / 8, 1.0)  # Longer words = more formal
    metrics['formality_score'] = round(formality * 100, 2)

    # 4. Tone Consistency (variance of per-sentence sentiment)
    if len(sentences) >= 2:
        sentence_sentiments = []
        for sent in sentences:
            sent_words = tokenize_words(sent)
            pos = sum(1 for w in sent_words if w in POSITIVE_WORDS)
            neg = sum(1 for w in sent_words if w in NEGATIVE_WORDS)
            total = max(pos + neg, 1)
            sentence_sentiments.append((pos - neg) / total)
        variance = np.var(sentence_sentiments)
        # Low variance = high consistency
        metrics['tone_consistency'] = round(max(0, (1 - variance)) * 100, 2)
    else:
        metrics['tone_consistency'] = 80.0

    # 5. Emotional Range
    emotion_words = pos_count + neg_count
    metrics['emotional_range'] = round(min(emotion_words / total_words * 20, 1.0) * 100, 2)

    return metrics


def compute_readability(text):
    """Compute standard readability metrics."""
    metrics = {}
    sentences = tokenize_sentences(text)
    words = tokenize_words(text)

    total_sentences = max(len(sentences), 1)
    total_words = max(len(words), 1)
    total_syllables = sum(count_syllables(w) for w in words)
    complex_words = sum(1 for w in words if is_complex_word(w))

    avg_sentence_len = total_words / total_sentences
    avg_syllables_per_word = total_syllables / total_words

    # 1. Flesch Reading Ease (0-100, higher = easier)
    fre = 206.835 - (1.015 * avg_sentence_len) - (84.6 * avg_syllables_per_word)
    metrics['flesch_reading_ease'] = round(max(0, min(100, fre)), 2)

    # 2. Flesch-Kincaid Grade Level
    fkgl = (0.39 * avg_sentence_len) + (11.8 * avg_syllables_per_word) - 15.59
    metrics['flesch_kincaid_grade'] = round(max(0, fkgl), 2)

    # 3. Gunning Fog Index
    complex_ratio = complex_words / total_words if total_words > 0 else 0
    fog = 0.4 * (avg_sentence_len + 100 * complex_ratio)
    metrics['gunning_fog_index'] = round(max(0, fog), 2)

    # 4. Coleman-Liau Index
    chars = sum(len(w) for w in words)
    L = (chars / total_words) * 100  # avg letters per 100 words
    S = (total_sentences / total_words) * 100  # avg sentences per 100 words
    cli = 0.0588 * L - 0.296 * S - 15.8
    metrics['coleman_liau_index'] = round(max(0, cli), 2)

    # 5. Automated Readability Index
    ari = 4.71 * (chars / total_words) + 0.5 * avg_sentence_len - 21.43
    metrics['automated_readability_index'] = round(max(0, ari), 2)

    # 6. SMOG Grade (requires 30+ sentences ideally, but we approximate)
    if total_sentences >= 3:
        smog = 1.043 * math.sqrt(complex_words * (30 / total_sentences)) + 3.1291
    else:
        smog = fkgl  # Fallback
    metrics['smog_grade'] = round(max(0, smog), 2)

    # Composite readability score (normalized to 0-100, where 100 = optimally readable)
    # Target: FRE around 60-70 for professional writing
    target_fre = 60
    fre_score = max(0, 100 - abs(fre - target_fre) * 1.5)
    metrics['readability_score'] = round(fre_score, 2)

    return metrics


def compute_lexical_analysis(text):
    """Compute lexical richness and sophistication metrics."""
    metrics = {}
    words = tokenize_words(text)
    total_words = max(len(words), 1)
    unique_words = set(words)
    word_freq = Counter(words)

    # 1. Type-Token Ratio (TTR)
    ttr = len(unique_words) / total_words
    metrics['type_token_ratio'] = round(ttr * 100, 2)

    # 2. Root TTR (Guiraud's Index) — more stable across text lengths
    root_ttr = len(unique_words) / math.sqrt(total_words)
    metrics['root_ttr'] = round(min(root_ttr / 15 * 100, 100), 2)  # Normalize

    # 3. Hapax Legomena Ratio (words appearing exactly once)
    hapax = sum(1 for w, c in word_freq.items() if c == 1)
    metrics['hapax_legomena_ratio'] = round(hapax / max(len(unique_words), 1) * 100, 2)

    # 4. Yule's K (vocabulary richness — lower = richer)
    freq_spectrum = Counter(word_freq.values())
    M1 = total_words
    M2 = sum(i * i * freq for i, freq in freq_spectrum.items())
    if M1 > 0 and M2 > M1:
        K = 10000 * (M2 - M1) / (M1 * M1)
    else:
        K = 0
    # Invert and normalize: lower K = richer vocabulary = higher score
    metrics['yules_k'] = round(K, 2)
    metrics['vocabulary_richness'] = round(max(0, min(100, 100 - K * 0.5)), 2)

    # 5. Average Word Length
    avg_len = np.mean([len(w) for w in words]) if words else 0
    metrics['avg_word_length'] = round(avg_len, 2)

    # 6. Lexical Sophistication (% of low-frequency / advanced words)
    # Words with 3+ syllables and 7+ characters
    sophisticated = sum(1 for w in words if count_syllables(w) >= 3 and len(w) >= 7)
    metrics['lexical_sophistication'] = round(sophisticated / total_words * 100, 2)

    # 7. Information Density (content words vs function words)
    content_word_count = sum(1 for w in words if w in CONTENT_WORDS_POS or len(w) > 5)
    metrics['information_density'] = round(content_word_count / total_words * 100, 2)

    # 8. Brunet's W (another vocabulary richness measure)
    if total_words > 0 and len(unique_words) > 0:
        W = total_words ** (len(unique_words) ** -0.172)
        metrics['brunets_w'] = round(W, 2)
    else:
        metrics['brunets_w'] = 0

    # 9. Honore's R
    if total_words > 0 and hapax > 0 and len(unique_words) > hapax:
        R = 100 * math.log(total_words) / (1 - hapax / len(unique_words))
        metrics['honores_r'] = round(R, 2)
    else:
        metrics['honores_r'] = 0

    return metrics


def compute_structural_analysis(text):
    """Compute structural metrics of the text."""
    metrics = {}
    sentences = tokenize_sentences(text)
    paragraphs = tokenize_paragraphs(text)
    words = tokenize_words(text)

    # 1. Basic counts
    metrics['word_count'] = len(words)
    metrics['sentence_count'] = len(sentences)
    metrics['paragraph_count'] = len(paragraphs)
    metrics['character_count'] = len(text)
    metrics['character_count_no_spaces'] = len(text.replace(' ', ''))

    # 2. Sentence length statistics
    sent_lengths = [len(tokenize_words(s)) for s in sentences]
    if sent_lengths:
        metrics['avg_sentence_length'] = round(np.mean(sent_lengths), 2)
        metrics['min_sentence_length'] = int(np.min(sent_lengths))
        metrics['max_sentence_length'] = int(np.max(sent_lengths))
        metrics['sentence_length_std'] = round(float(np.std(sent_lengths)), 2)
        metrics['sentence_length_variance'] = round(float(np.var(sent_lengths)), 2)
        # Coefficient of variation
        if np.mean(sent_lengths) > 0:
            metrics['sentence_length_cv'] = round(float(np.std(sent_lengths) / np.mean(sent_lengths)) * 100, 2)
        else:
            metrics['sentence_length_cv'] = 0
    else:
        for k in ['avg_sentence_length', 'min_sentence_length', 'max_sentence_length',
                   'sentence_length_std', 'sentence_length_variance', 'sentence_length_cv']:
            metrics[k] = 0

    # 3. Paragraph length statistics
    para_lengths = [len(tokenize_words(p)) for p in paragraphs]
    if para_lengths:
        metrics['avg_paragraph_length'] = round(np.mean(para_lengths), 2)
        metrics['paragraph_length_std'] = round(float(np.std(para_lengths)), 2)
    else:
        metrics['avg_paragraph_length'] = 0
        metrics['paragraph_length_std'] = 0

    # 4. Sentence Type Variety
    questions = sum(1 for s in sentences if s.strip().endswith('?'))
    exclamations = sum(1 for s in sentences if s.strip().endswith('!'))
    declaratives = len(sentences) - questions - exclamations
    total = max(len(sentences), 1)
    metrics['question_ratio'] = round(questions / total * 100, 2)
    metrics['exclamation_ratio'] = round(exclamations / total * 100, 2)
    metrics['declarative_ratio'] = round(declaratives / total * 100, 2)

    # Sentence variety score
    types_used = sum(1 for x in [questions, exclamations, declaratives] if x > 0)
    metrics['sentence_type_variety'] = round(types_used / 3 * 100, 2)

    # 5. Text Density
    if metrics['word_count'] > 0:
        metrics['words_per_paragraph'] = round(metrics['word_count'] / max(len(paragraphs), 1), 2)
    else:
        metrics['words_per_paragraph'] = 0

    return metrics


def compute_coherence_flow(text):
    """Compute coherence and flow metrics using inter-sentence similarity."""
    metrics = {}
    sentences = tokenize_sentences(text)
    words = tokenize_words(text)

    # 1. Inter-sentence Cosine Similarity (consecutive sentences)
    if len(sentences) >= 2:
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf = vectorizer.fit_transform(sentences)
            similarities = []
            for i in range(len(sentences) - 1):
                sim = cosine_similarity(tfidf[i:i+1], tfidf[i+1:i+2])[0][0]
                similarities.append(float(sim))
            metrics['avg_inter_sentence_similarity'] = round(np.mean(similarities) * 100, 2)
            metrics['min_inter_sentence_similarity'] = round(np.min(similarities) * 100, 2)
            metrics['coherence_variance'] = round(float(np.var(similarities)) * 100, 2)
        except:
            metrics['avg_inter_sentence_similarity'] = 50.0
            metrics['min_inter_sentence_similarity'] = 50.0
            metrics['coherence_variance'] = 0.0
    else:
        metrics['avg_inter_sentence_similarity'] = 50.0
        metrics['min_inter_sentence_similarity'] = 50.0
        metrics['coherence_variance'] = 0.0

    # 2. Transition Word Usage
    transition_count = 0
    text_lower = text.lower()
    for tw in TRANSITION_WORDS:
        if tw in text_lower:
            transition_count += 1
    total_sentences = max(len(sentences), 1)
    metrics['transition_density'] = round(transition_count / total_sentences * 100, 2)

    # 3. Topic Consistency (global coherence via pairwise similarity)
    if len(sentences) >= 3:
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf = vectorizer.fit_transform(sentences)
            all_sims = cosine_similarity(tfidf)
            upper_tri = all_sims[np.triu_indices(len(sentences), k=1)]
            metrics['global_coherence'] = round(float(np.mean(upper_tri)) * 100, 2)
        except:
            metrics['global_coherence'] = 50.0
    else:
        metrics['global_coherence'] = 50.0

    # 4. Flow Score (combined)
    metrics['flow_score'] = round(
        0.4 * metrics['avg_inter_sentence_similarity'] +
        0.3 * min(metrics['transition_density'] * 10, 100) +
        0.3 * metrics['global_coherence'],
        2
    )

    return metrics


def compute_redundancy(text):
    """Detect redundancy through n-gram repetition analysis."""
    metrics = {}
    words = tokenize_words(text)
    sentences = tokenize_sentences(text)
    total_words = max(len(words), 1)

    # 1. Bigram Repetition
    bigrams = [tuple(words[i:i+2]) for i in range(len(words)-1)]
    if bigrams:
        bigram_counts = Counter(bigrams)
        repeated_bigrams = sum(c - 1 for c in bigram_counts.values() if c > 1)
        bigram_rep_rate = repeated_bigrams / len(bigrams) * 100
        metrics['bigram_repetition_rate'] = round(bigram_rep_rate, 2)
    else:
        metrics['bigram_repetition_rate'] = 0

    # 2. Trigram Repetition
    trigrams = [tuple(words[i:i+3]) for i in range(len(words)-2)]
    if trigrams:
        trigram_counts = Counter(trigrams)
        repeated_trigrams = sum(c - 1 for c in trigram_counts.values() if c > 1)
        trigram_rep_rate = repeated_trigrams / len(trigrams) * 100
        metrics['trigram_repetition_rate'] = round(trigram_rep_rate, 2)
    else:
        metrics['trigram_repetition_rate'] = 0

    # 3. Sentence-level Similarity (detect near-duplicate sentences)
    if len(sentences) >= 2:
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf = vectorizer.fit_transform(sentences)
            sim_matrix = cosine_similarity(tfidf)
            # Check for high similarity pairs (excluding diagonal)
            np.fill_diagonal(sim_matrix, 0)
            max_sim = float(np.max(sim_matrix))
            avg_sim = float(np.mean(sim_matrix[np.triu_indices(len(sentences), k=1)]))
            metrics['max_sentence_similarity'] = round(max_sim * 100, 2)
            metrics['avg_cross_sentence_similarity'] = round(avg_sim * 100, 2)
        except:
            metrics['max_sentence_similarity'] = 0
            metrics['avg_cross_sentence_similarity'] = 0
    else:
        metrics['max_sentence_similarity'] = 0
        metrics['avg_cross_sentence_similarity'] = 0

    # 4. Word Repetition Rate
    word_counts = Counter(words)
    stop_words = set("a an the is are was were be been being have has had do does did will would shall should may might can could and but or nor for so yet at by to from in on with as of it its i me my we our you your he she they them their this that these those".split())
    content_words = [w for w in words if w not in stop_words]
    if content_words:
        content_counts = Counter(content_words)
        repeated = sum(c - 1 for c in content_counts.values() if c > 1)
        metrics['content_word_repetition'] = round(repeated / len(content_words) * 100, 2)
    else:
        metrics['content_word_repetition'] = 0

    # 5. Redundancy Score (lower repetition = higher score)
    metrics['redundancy_score'] = round(max(0, 100 - (
        metrics['bigram_repetition_rate'] * 2 +
        metrics['trigram_repetition_rate'] * 3 +
        metrics['content_word_repetition'] * 0.5
    )), 2)

    return metrics


# ─────────────────────────────────────────────
# COMPOSITE SCORING
# ─────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    'content_quality': 20,
    'tone_sentiment': 15,
    'readability': 15,
    'lexical_analysis': 10,
    'structural': 10,
    'constraint_adherence': 20,
    'coherence_flow': 5,
    'redundancy': 5
}

def compute_category_scores(all_metrics):
    """Convert detailed metrics to category scores (0-100)."""
    scores = {}

    # Content Quality
    cq = all_metrics.get('content_quality', {})
    scores['content_quality'] = cq.get('relevance_score', 50)

    # Tone & Sentiment
    ts = all_metrics.get('tone_sentiment', {})
    scores['tone_sentiment'] = round(
        0.3 * ts.get('formality_score', 50) +
        0.3 * ts.get('tone_consistency', 50) +
        0.2 * ts.get('sentiment_polarity', 50) +
        0.2 * (100 - ts.get('subjectivity', 50)),
        2
    )

    # Readability
    rd = all_metrics.get('readability', {})
    scores['readability'] = rd.get('readability_score', 50)

    # Lexical Analysis
    lx = all_metrics.get('lexical_analysis', {})
    scores['lexical_analysis'] = round(
        0.3 * lx.get('vocabulary_richness', 50) +
        0.25 * min(lx.get('type_token_ratio', 50), 100) +
        0.25 * min(lx.get('lexical_sophistication', 50) * 3, 100) +
        0.2 * min(lx.get('information_density', 50), 100),
        2
    )

    # Structural
    st = all_metrics.get('structural', {})
    # Sentence variety contributes
    variety_score = st.get('sentence_type_variety', 33)
    # CV of sentence length (moderate variation is good)
    cv = st.get('sentence_length_cv', 0)
    cv_score = max(0, 100 - abs(cv - 40) * 2)  # 40% CV is ideal
    scores['structural'] = round(0.5 * variety_score + 0.5 * cv_score, 2)

    # Constraint Adherence
    scores['constraint_adherence'] = all_metrics.get('constraint_adherence', {}).get('total_score', 50)

    # Coherence & Flow
    cf = all_metrics.get('coherence_flow', {})
    scores['coherence_flow'] = cf.get('flow_score', 50)

    # Redundancy
    rd2 = all_metrics.get('redundancy', {})
    scores['redundancy'] = rd2.get('redundancy_score', 50)

    return scores


def compute_composite_score(category_scores, weights=None):
    """Compute weighted composite score."""
    if weights is None:
        weights = DEFAULT_WEIGHTS

    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0

    weighted_sum = sum(
        category_scores.get(cat, 0) * (w / total_weight)
        for cat, w in weights.items()
    )
    return round(weighted_sum, 2)


def compute_z_scores(all_models_category_scores):
    """Compute z-score normalized scores across models."""
    categories = list(DEFAULT_WEIGHTS.keys())
    z_scores = {}

    for cat in categories:
        values = [m.get(cat, 0) for m in all_models_category_scores.values()]
        if len(values) >= 2:
            mean = np.mean(values)
            std = np.std(values)
            if std > 0:
                for model_name, scores in all_models_category_scores.items():
                    if model_name not in z_scores:
                        z_scores[model_name] = {}
                    z_scores[model_name][cat] = round((scores.get(cat, 0) - mean) / std, 3)
            else:
                for model_name in all_models_category_scores:
                    if model_name not in z_scores:
                        z_scores[model_name] = {}
                    z_scores[model_name][cat] = 0.0
        else:
            for model_name in all_models_category_scores:
                if model_name not in z_scores:
                    z_scores[model_name] = {}
                z_scores[model_name][cat] = 0.0

    return z_scores


def compute_cross_model_statistics(all_models_category_scores):
    """Compute cross-model statistics."""
    categories = list(DEFAULT_WEIGHTS.keys())
    stats = {}

    for cat in categories:
        values = [m.get(cat, 0) for m in all_models_category_scores.values()]
        if values:
            stats[cat] = {
                'mean': round(float(np.mean(values)), 2),
                'std': round(float(np.std(values)), 2),
                'min': round(float(np.min(values)), 2),
                'max': round(float(np.max(values)), 2),
                'range': round(float(np.max(values) - np.min(values)), 2),
                'median': round(float(np.median(values)), 2)
            }

    return stats


def evaluate_model(response_text, prompt_text, context_text, constraint_results):
    """Run all metrics for a single model response."""
    results = {
        'content_quality': compute_content_quality(response_text, prompt_text, context_text),
        'tone_sentiment': compute_tone_sentiment(response_text),
        'readability': compute_readability(response_text),
        'lexical_analysis': compute_lexical_analysis(response_text),
        'structural': compute_structural_analysis(response_text),
        'coherence_flow': compute_coherence_flow(response_text),
        'redundancy': compute_redundancy(response_text),
        'constraint_adherence': constraint_results
    }
    return results
