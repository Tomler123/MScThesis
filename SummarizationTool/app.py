"""
Text Summarization Evaluation Tool
MSc Thesis: Understanding and Comparing Generative AI Models
"""
from flask import Flask, render_template, request, jsonify
import json, math, re, string
from collections import Counter

app = Flask(__name__)

def tokenize(text):
    return [t for t in re.sub(r'[^\w\s]',' ',text.lower()).split() if t]

def sent_tokenize(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]

def get_ngrams(tokens, n):
    return [tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def get_char_ngrams(text, n):
    t = text.lower().strip()
    return [t[i:i+n] for i in range(len(t)-n+1)]

STOP = set("a an the is are was were be been being have has had do does did will would shall should may might can could of in to for on with at by from as into through during before after above below between out off over under again further then once here there when where why how all both each few more most other some such no nor not only own same so than too very and but if or because until while about against it its he she they them their his her this that these those i me my we our you your who whom which what".split())

def content_words(tokens):
    return [t for t in tokens if t not in STOP and len(t) > 1]

def prf(matches, hlen, rlen):
    p = matches/hlen if hlen else 0; r = matches/rlen if rlen else 0
    f = 2*p*r/(p+r) if p+r else 0
    return round(p,4), round(r,4), round(f,4)

def rouge_n(hyp, ref, n=1):
    ht, rt = tokenize(hyp), tokenize(ref)
    hng, rng = Counter(get_ngrams(ht,n)), Counter(get_ngrams(rt,n))
    m = sum(min(c, rng.get(ng,0)) for ng,c in hng.items())
    return prf(m, sum(hng.values()), sum(rng.values()))

def lcs_len(x, y):
    m, n = len(x), len(y)
    if not m or not n: return 0
    prev = [0]*(n+1); curr = [0]*(n+1)
    for i in range(1,m+1):
        for j in range(1,n+1):
            curr[j] = prev[j-1]+1 if x[i-1]==y[j-1] else max(curr[j-1],prev[j])
        prev, curr = curr, [0]*(n+1)
    return prev[n]

def rouge_l(hyp, ref):
    ht, rt = tokenize(hyp), tokenize(ref)
    if not ht or not rt: return (0,0,0)
    return prf(lcs_len(ht,rt), len(ht), len(rt))

def bleu_score(hyp, ref, max_n=4):
    ht, rt = tokenize(hyp), tokenize(ref)
    if not ht or not rt: return 0.0
    bp = math.exp(1-len(rt)/len(ht)) if len(ht)<len(rt) else 1.0
    la = 0.0; en = 0
    for n in range(1, max_n+1):
        hng = get_ngrams(ht,n); rng = get_ngrams(rt,n)
        if not hng: break
        rc = Counter(rng); hc = Counter(hng)
        cl = sum(min(c,rc.get(ng,0)) for ng,c in hc.items())
        p = cl/len(hng)
        if p == 0: return 0.0
        la += math.log(p); en += 1
    return round(bp*math.exp(la/en),4) if en else 0.0

def chrf_score(hyp, ref, max_n=6, beta=2):
    tp = tr = 0.0; cnt = 0
    for n in range(1, max_n+1):
        hc = get_char_ngrams(hyp,n); rc = get_char_ngrams(ref,n)
        if not hc or not rc: continue
        hcn, rcn = Counter(hc), Counter(rc)
        m = sum(min(c,rcn.get(ng,0)) for ng,c in hcn.items())
        tp += m/len(hc); tr += m/len(rc); cnt += 1
    if not cnt: return 0.0
    ap, ar = tp/cnt, tr/cnt
    if ap+ar == 0: return 0.0
    b2 = beta**2
    return round((1+b2)*ap*ar/(b2*ap+ar), 4)

def tfidf_cosine(a, b):
    ta, tb = tokenize(a), tokenize(b)
    at = set(ta)|set(tb)
    if not at: return 0.0
    d = [Counter(ta), Counter(tb)]
    idf = {t: math.log(3/(sum(1 for x in d if t in x)+1))+1 for t in at}
    def vec(c):
        tot = sum(c.values()) or 1
        return {t:(c[t]/tot)*idf[t] for t in at}
    va, vb = vec(d[0]), vec(d[1])
    dot = sum(va[t]*vb[t] for t in at)
    ma = math.sqrt(sum(v**2 for v in va.values())) or 1
    mb = math.sqrt(sum(v**2 for v in vb.values())) or 1
    return round(dot/(ma*mb), 4)

def jaccard(a,b):
    sa,sb = set(tokenize(a)),set(tokenize(b))
    return round(len(sa&sb)/len(sa|sb),4) if sa|sb else 0.0

def cw_overlap(a,b):
    sa,sb = set(content_words(tokenize(a))),set(content_words(tokenize(b)))
    return round(len(sa&sb)/len(sa|sb),4) if sa and sb else 0.0

def bi_overlap(a,b):
    sa,sb = set(get_ngrams(tokenize(a),2)),set(get_ngrams(tokenize(b),2))
    return round(len(sa&sb)/len(sa|sb),4) if sa and sb else 0.0

def compress_ratio(s,r):
    sl,rl = len(tokenize(s)),len(tokenize(r))
    return round(sl/rl,4) if rl else 0.0

def coverage(s,r):
    rc = set(content_words(tokenize(r)))
    return round(len(rc&set(tokenize(s)))/len(rc),4) if rc else 0.0

def redundancy(text, n=3):
    ng = get_ngrams(tokenize(text),n)
    if not ng: return 0.0
    c = Counter(ng)
    return round(sum(v-1 for v in c.values() if v>1)/len(ng), 4)

def sent_overlap(s, r):
    ss, rs = sent_tokenize(s), sent_tokenize(r)
    if not ss or not rs: return 0.0
    ov = 0
    for x in ss:
        xt = set(tokenize(x))
        for y in rs:
            yt = set(tokenize(y))
            if xt and yt and len(xt&yt)/len(xt|yt)>0.3: ov+=1; break
    return round(ov/len(ss),4)

def edit_dist(a,b):
    m,n = len(a),len(b)
    dp = list(range(n+1))
    for i in range(1,m+1):
        prev=dp[0]; dp[0]=i
        for j in range(1,n+1):
            tmp=dp[j]
            dp[j] = prev if a[i-1]==b[j-1] else 1+min(prev,dp[j],dp[j-1])
            prev=tmp
    return dp[n]

def wer(h,r):
    ht,rt = tokenize(h),tokenize(r)
    return round(edit_dist(ht,rt)/len(rt),4) if rt else 0.0

def cer(h,r):
    hl,rl = list(h.lower()),list(r.lower())
    return round(edit_dist(hl,rl)/len(rl),4) if rl else 0.0

def lex_div(t):
    tk=tokenize(t); return round(len(set(tk))/len(tk),4) if tk else 0.0

def info_dens(t):
    tk=tokenize(t); return round(len(content_words(tk))/len(tk),4) if tk else 0.0

def key_sents(src, n=5):
    ss=sent_tokenize(src)
    if not ss: return []
    at=tokenize(src); tf=Counter(at); tot=len(at) or 1
    sc=[]
    for s in ss:
        st=content_words(tokenize(s))
        if st: sc.append((sum(tf[t]/tot for t in st)/len(st),s))
    sc.sort(key=lambda x:-x[0])
    return [s for _,s in sc[:n]]

def novel_ng(s,r,n=2):
    sng=set(get_ngrams(tokenize(s),n)); rng=set(get_ngrams(tokenize(r),n))
    return round(len(sng-rng)/len(sng),4) if sng else 0.0

def analyze_pf(prompt, summary):
    pl, sl = prompt.lower(), summary.lower()
    sig = {}; scores = []

    bk = ['bullet','bullets','bullet point','bullet points']
    if any(k in pl for k in bk):
        has = bool(re.search(r'(^|\n)\s*[-•*]\s', summary))
        cnt = len(re.findall(r'(^|\n)\s*[-•*]\s', summary))
        sig['bullet_points_requested']=True; sig['bullet_points_found']=has; sig['bullet_count']=cnt
        scores.append(1.0 if has else 0.0)
        m = re.search(r'(?:exactly\s+)?(\d+)\s*bullet', pl)
        if m:
            exp=int(m.group(1)); sig['expected_bullet_count']=exp
            scores.append(1.0 if cnt==exp else max(0,1-abs(cnt-exp)/exp))

    if any(k in pl for k in ['numbered','number the']):
        has=bool(re.search(r'(^|\n)\s*\d+[.)]\s',summary))
        sig['numbered_list_requested']=True; sig['numbered_list_found']=has
        scores.append(1.0 if has else 0.0)

    m = re.search(r'(\d+)\s*(?:words?)\s*(?:or\s*(?:less|fewer))?', pl)
    if not m: m = re.search(r'(?:max|under|no more than|at most)\s*(\d+)\s*words?', pl)
    if m:
        lim=int(m.group(1)); wc=len(tokenize(summary))
        sig['word_limit']=lim; sig['actual_word_count']=wc; sig['word_limit_respected']=wc<=lim
        scores.append(1.0 if wc<=lim else max(0,1-(wc-lim)/lim))

    m = re.search(r'(?:exactly\s+)?(\d+)\s*sentences?', pl)
    if m:
        lim=int(m.group(1)); sc=len(sent_tokenize(summary))
        sig['sentence_limit']=lim; sig['actual_sentence_count']=sc
        scores.append(1.0 if sc==lim else max(0,1-abs(sc-lim)/lim))

    sm = re.search(r'(?:sections?|order)\s*[:\s]*((?:[A-Z][A-Za-z /&]*(?:,\s*)?){2,})', prompt)
    if sm:
        expected = [s.strip().lower() for s in sm.group(1).split(',') if s.strip()]
        sig['expected_sections']=expected; sig['sections_requested']=True
        found=sum(1 for s in expected if s in sl); sig['sections_found_count']=found
        scores.append(found/len(expected) if expected else 0)
    elif any(k in pl for k in ['sections','section','headings']):
        sig['sections_requested']=True
        has=bool(re.search(r'(^|\n)\s*(?:[A-Z][^.!?\n]{2,}:|\*\*[^*]+\*\*|#+\s)',summary))
        sig['headers_found']=has; scores.append(1.0 if has else 0.0)

    tm = re.search(r'titled\s*:\s*((?:[A-Z][A-Za-z /&]*(?:,\s*)?){2,})', prompt)
    if tm:
        expected=[s.strip().lower() for s in tm.group(1).split(',') if s.strip()]
        sig['expected_titled_bullets']=expected
        found=sum(1 for s in expected if s in sl); sig['titled_bullets_found']=found
        scores.append(found/len(expected) if expected else 0)

    if any(k in pl for k in ['brief','concise','short','succinct']):
        wc=len(tokenize(summary)); sig['brevity_requested']=True; sig['summary_word_count']=wc
        scores.append(1.0 if wc<200 else max(0,1-(wc-200)/300))
    if any(k in pl for k in ['detailed','comprehensive','thorough']):
        wc=len(tokenize(summary)); sig['detail_requested']=True; sig['summary_word_count']=wc
        scores.append(1.0 if wc>100 else wc/100)
    if 'paragraph' in pl:
        pc=len([p for p in summary.split('\n\n') if p.strip()])
        sig['paragraph_format_requested']=True; sig['paragraph_count']=pc
        scores.append(1.0 if pc>=1 else 0.0)

    negs = re.findall(r'do\s+not\s+([^.!?\n]+)', pl)
    if negs: sig['negative_constraints']=negs

    sig['overall_adherence']=round(sum(scores)/len(scores),4) if scores else None
    return sig

def evaluate_entry(prompt, source, summary, url=None):
    r = {}; hs = bool(source and source.strip())
    r['lexical_diversity']=lex_div(summary); r['information_density']=info_dens(summary)
    r['redundancy']=redundancy(summary); r['summary_word_count']=len(tokenize(summary))
    r['summary_sent_count']=len(sent_tokenize(summary))
    if hs:
        r1=rouge_n(summary,source,1); r['rouge1_p'],r['rouge1_r'],r['rouge1_f1']=r1
        r2=rouge_n(summary,source,2); r['rouge2_p'],r['rouge2_r'],r['rouge2_f1']=r2
        rl=rouge_l(summary,source); r['rougeL_p'],r['rougeL_r'],r['rougeL_f1']=rl
        r['bleu']=bleu_score(summary,source); r['chrf']=chrf_score(summary,source)
        r['tfidf_cosine']=tfidf_cosine(summary,source); r['jaccard']=jaccard(summary,source)
        r['content_word_overlap']=cw_overlap(summary,source); r['bigram_overlap']=bi_overlap(summary,source)
        r['compression_ratio']=compress_ratio(summary,source); r['coverage']=coverage(summary,source)
        r['sentence_overlap']=sent_overlap(summary,source)
        ks=key_sents(source,3)
        if ks: kt=' '.join(ks); r['wer_vs_key']=wer(summary,kt); r['cer_vs_key']=cer(summary,kt)
        else: r['wer_vs_key']=r['cer_vs_key']=None
        r['novel_bigram_ratio']=novel_ng(summary,source,2); r['abstractivity']=novel_ng(summary,source,3)
        r['source_word_count']=len(tokenize(source))
    else:
        for k in ['rouge1_p','rouge1_r','rouge1_f1','rouge2_p','rouge2_r','rouge2_f1','rougeL_p','rougeL_r','rougeL_f1','bleu','chrf','tfidf_cosine','jaccard','content_word_overlap','bigram_overlap','compression_ratio','coverage','sentence_overlap','wer_vs_key','cer_vs_key','novel_bigram_ratio','abstractivity','source_word_count']:
            r[k]=None
        r['no_source_warning']=True
    r['prompt_faithfulness']=analyze_pf(prompt,summary)
    if url: r['url_provided']=url
    return r

PRESETS = {
    'balanced':{'rouge1_f1':.15,'rouge2_f1':.10,'rougeL_f1':.10,'bleu':.05,'chrf':.05,'tfidf_cosine':.10,'coverage':.10,'compression_ratio':.05,'lexical_diversity':.05,'information_density':.05,'redundancy':-.05,'prompt_adherence':.15},
    'coverage_heavy':{'rouge1_f1':.10,'rouge2_f1':.05,'rougeL_f1':.05,'bleu':.05,'chrf':.10,'tfidf_cosine':.15,'coverage':.25,'compression_ratio':0,'lexical_diversity':.05,'information_density':.05,'redundancy':-.05,'prompt_adherence':.15},
    'conciseness_heavy':{'rouge1_f1':.10,'rouge2_f1':.10,'rougeL_f1':.10,'bleu':.05,'chrf':.05,'tfidf_cosine':.05,'coverage':.05,'compression_ratio':.15,'lexical_diversity':.10,'information_density':.10,'redundancy':-.10,'prompt_adherence':.10}
}

def compute_composite(entry, weights):
    s=0;tw=0
    for k,w in weights.items():
        if k=='prompt_adherence': val=entry.get('prompt_faithfulness',{}).get('overall_adherence')
        elif k=='compression_ratio': raw=entry.get(k); val=1-min(raw,1.0) if raw is not None else None
        elif k=='redundancy': raw=entry.get('redundancy'); val=1-raw if raw is not None else None
        else: val=entry.get(k)
        if val is not None: s+=w*val; tw+=abs(w)
    return round(s/tw,4) if tw else 0.0

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    d=request.json
    if not d.get('prompt') or not d.get('summary'): return jsonify({'error':'Prompt and summary required'}),400
    return jsonify(evaluate_entry(d['prompt'],d.get('source',''),d['summary'],d.get('url','')))

@app.route('/api/analytics', methods=['POST'])
def api_analytics():
    d=request.json; entries=d.get('entries',[]); weights=d.get('weights',PRESETS['balanced'])
    p=d.get('preset'); 
    if p and p in PRESETS: weights=PRESETS[p]
    mk=['rouge1_f1','rouge2_f1','rougeL_f1','bleu','chrf','tfidf_cosine','jaccard','content_word_overlap','bigram_overlap','compression_ratio','coverage','redundancy','sentence_overlap','lexical_diversity','information_density','novel_bigram_ratio','abstractivity']
    for e in entries: e['composite_score']=compute_composite(e,weights)
    zs,zst=compute_z_scores(entries,mk) if len(entries)>1 else ([],{})
    stats=cross_model_stats(entries,mk)
    lb=sorted([{'model':e.get('model','?'),'composite':e['composite_score'],'idx':i} for i,e in enumerate(entries)],key=lambda x:-x['composite'])
    return jsonify({'z_scores':zs,'z_stats':zst,'cross_model_stats':stats,'leaderboard':lb,'composite_scores':[e['composite_score'] for e in entries],'presets':PRESETS,'active_weights':weights})

def cross_model_stats(em,keys):
    st={}
    for k in keys:
        vs=[e.get(k) for e in em if e.get(k) is not None]
        if not vs: st[k]={'mean':None,'std':None,'min':None,'max':None}; continue
        m=sum(vs)/len(vs); s=math.sqrt(sum((v-m)**2 for v in vs)/len(vs)) if len(vs)>1 else 0
        st[k]={'mean':round(m,4),'std':round(s,4),'min':round(min(vs),4),'max':round(max(vs),4)}
    return st

def compute_z_scores(em,keys):
    st={}
    for k in keys:
        vs=[e.get(k) for e in em if e.get(k) is not None]
        if len(vs)<2: st[k]={'mean':vs[0] if vs else 0,'std':0}; continue
        m=sum(vs)/len(vs); s=math.sqrt(sum((v-m)**2 for v in vs)/len(vs))
        st[k]={'mean':round(m,4),'std':round(s,4)}
    zs=[]
    for e in em:
        z={}
        for k in keys:
            v=e.get(k)
            if v is None: z[k]=None; continue
            z[k]=round((v-st[k]['mean'])/st[k]['std'],4) if st[k]['std'] else 0.0
        zs.append(z)
    return zs,st

@app.route('/api/extract-pdf', methods=['POST'])
def api_extract_pdf():
    """Extract text from an uploaded PDF file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    f = request.files['file']
    if not f.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400
    import tempfile, subprocess, os
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    try:
        f.save(tmp.name)
        tmp.close()
        # Try pdftotext first (poppler-utils) — best quality
        try:
            result = subprocess.run(
                ['pdftotext', '-layout', tmp.name, '-'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return jsonify({'text': result.stdout.strip(), 'method': 'pdftotext'})
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        # Fallback: pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(tmp.name)
            text = '\n'.join(page.extract_text() or '' for page in reader.pages)
            if text.strip():
                return jsonify({'text': text.strip(), 'method': 'pypdf'})
        except Exception:
            pass
        # Last resort: pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(tmp.name) as pdf:
                text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
            if text.strip():
                return jsonify({'text': text.strip(), 'method': 'pdfplumber'})
        except Exception:
            pass
        return jsonify({'error': 'Could not extract text from PDF. It may be a scanned document.'}), 400
    finally:
        os.unlink(tmp.name)

@app.route('/api/llm-prompt', methods=['POST'])
def api_llm_prompt():
    d=request.json
    src=""
    if d.get('source'):
        sd=d['source'][:3000]+('...' if len(d['source'])>3000 else '')
        src=f"\n## Source Text\n{sd}\n"
    elif d.get('url'): src=f"\n## Source URL\n{d['url']}\n"
    prompt=f"""You are an expert evaluator of text summaries. Score 0-10 with short justification on each:

1. Factual Accuracy 2. Completeness 3. Conciseness 4. Coherence & Fluency 5. Prompt Faithfulness 6. Overall

## Prompt Given
{d.get('prompt','')}
{src}
## Summary
{d.get('summary','')}

Respond ONLY with this JSON (no markdown fences):
{{"factual_accuracy":{{"score":N,"justification":"..."}},"completeness":{{"score":N,"justification":"..."}},"conciseness":{{"score":N,"justification":"..."}},"coherence_fluency":{{"score":N,"justification":"..."}},"prompt_faithfulness":{{"score":N,"justification":"..."}},"overall":{{"score":N,"justification":"..."}}}}"""
    return jsonify({'llm_prompt':prompt})

@app.route('/api/export', methods=['POST'])
def api_export():
    d=request.json; fmt=d.get('format','json'); entries=d.get('entries',[])
    if fmt=='csv':
        if not entries: return jsonify({'csv':''})
        rows=[]
        for e in entries:
            f={}
            for k,v in e.items():
                if isinstance(v,dict):
                    for sk,sv in v.items(): f[f"{k}_{sk}"]=sv
                else: f[k]=v
            rows.append(f)
        ak=list(dict.fromkeys(k for r in rows for k in r))
        lines=[','.join(ak)]
        for r in rows:
            ln=[]
            for k in ak:
                sv=str(r.get(k,'') or '')
                if ',' in sv or '"' in sv or '\n' in sv: sv='"'+sv.replace('"','""')+'"'
                ln.append(sv)
            lines.append(','.join(ln))
        return jsonify({'csv':'\n'.join(lines)})
    return jsonify({'data':entries})

if __name__=='__main__': app.run(debug=True,port=5000)