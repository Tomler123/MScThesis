"""
app.py — AI Summarization Benchmark Tool (Flask Backend)

Routes:
  GET  /                 → Main evaluation dashboard
  POST /evaluate         → Run automated NLP metrics + constraint checks
  POST /llm-judge        → Run Gemini LLM-as-Judge evaluation
  POST /extract-pdf      → Extract text from uploaded PDF
"""

from flask import Flask, render_template, request, jsonify
import os
import json
import numpy as np

from evaluators.metrics import (
    compute_all_metrics, compute_composite_score,
    z_score_normalize, DEFAULT_WEIGHTS
)
from evaluators.constraint_checker import check_constraints
from evaluators.llm_judge import evaluate_with_gemini

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/evaluate', methods=['POST'])
def evaluate():
    """
    Run ALL automated evaluation metrics on each model response.

    Expected JSON body:
    {
        "source_text": "...",
        "prompt_text": "...",
        "reference_summary": "..." (optional),
        "use_bert": false,
        "weights": { ... } (optional),
        "models": [
            {"name": "GPT-4", "response": "..."},
            {"name": "Claude", "response": "..."}
        ]
    }
    """
    data = request.json
    source_text = data.get('source_text', '')
    prompt_text = data.get('prompt_text', '')
    reference_summary = data.get('reference_summary', '')
    use_bert = data.get('use_bert', False)
    custom_weights = data.get('weights', None)
    models = data.get('models', [])

    if not models:
        return jsonify({'error': 'No model responses provided'}), 400

    results = []
    for model in models:
        name = model.get('name', 'Unknown')
        resp = model.get('response', '')

        if not resp.strip():
            results.append({
                'model_name': name,
                'metrics': {},
                'constraint_result': {'overall_score': 0, 'details': []},
                'composite_score': 0,
                'error': 'Empty response'
            })
            continue

        # 1. Compute NLP metrics
        metrics = compute_all_metrics(
            source_text=source_text,
            summary=resp,
            reference=reference_summary,
            use_bert=use_bert
        )

        # 2. Check constraint adherence
        constraint_result = check_constraints(prompt_text, resp, source_text)
        metrics['constraint_adherence'] = constraint_result['overall_score']

        # 3. Composite score
        composite = compute_composite_score(metrics, custom_weights)
        metrics['composite_score'] = composite

        results.append({
            'model_name': name,
            'metrics': metrics,
            'constraint_result': constraint_result,
            'composite_score': composite,
        })

    # 4. Z-score normalization across models
    metric_keys_for_z = [
        'rouge1_f', 'rouge2_f', 'rougeL_f', 'bleu', 'cosine_similarity',
        'flesch_reading_ease', 'compression_ratio', 'lexical_diversity',
        'information_density', 'coherence', 'redundancy', 'constraint_adherence',
        'composite_score'
    ]
    results = z_score_normalize(results, metric_keys_for_z)

    # 5. Rank models by composite score
    ranked = sorted(results, key=lambda x: x.get('composite_score', 0), reverse=True)
    for i, r in enumerate(ranked):
        r['rank'] = i + 1

    # 6. Compute cross-model statistics
    stats = {}
    for key in metric_keys_for_z:
        vals = [r['metrics'].get(key, 0) for r in results if r['metrics'].get(key) is not None]
        if vals:
            stats[key] = {
                'mean': round(float(np.mean(vals)), 4),
                'std': round(float(np.std(vals)), 4),
                'min': round(float(np.min(vals)), 4),
                'max': round(float(np.max(vals)), 4),
            }

    return jsonify({
        'results': ranked,
        'statistics': stats,
        'weights_used': custom_weights or DEFAULT_WEIGHTS
    })


@app.route('/llm-judge', methods=['POST'])
def llm_judge():
    """
    Run Gemini LLM-as-Judge evaluation.

    Expected JSON body:
    {
        "api_key": "...",
        "source_text": "...",
        "prompt_text": "...",
        "models": [{"name": "...", "response": "..."}]
    }
    """
    data = request.json
    api_key = data.get('api_key', '')
    source_text = data.get('source_text', '')
    prompt_text = data.get('prompt_text', '')
    models = data.get('models', [])

    if not api_key:
        return jsonify({'error': 'Gemini API key is required'}), 400

    results = []
    for model in models:
        judge_result = evaluate_with_gemini(
            api_key=api_key,
            prompt=prompt_text,
            source=source_text,
            response=model.get('response', ''),
            model_name=model.get('name', 'Unknown')
        )
        results.append({
            'model_name': model.get('name', 'Unknown'),
            'judge': judge_result
        })

    return jsonify({'results': results})


@app.route('/extract-pdf', methods=['POST'])
def extract_pdf():
    """Extract text from an uploaded PDF file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400

    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text() or ''
            text += '\n'
        return jsonify({'text': text.strip()})
    except Exception as e:
        return jsonify({'error': f'PDF extraction failed: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
