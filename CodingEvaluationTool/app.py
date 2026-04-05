"""
Code Generation Evaluation Tool — Flask Application
====================================================
MSc Thesis: "Understanding and Comparing Generative AI Models"
Domain: Code Generation / Coding Assistant Evaluation

Routes:
  GET  /             — Main dashboard
  POST /evaluate     — Run deterministic metrics on all model responses
  POST /llm_judge    — Run LLM-as-Judge on a single model response
  POST /export/csv   — Export results as CSV
  POST /export/json  — Export results as JSON
"""

from flask import Flask, render_template, request, jsonify, Response
from evaluators.metrics import evaluate_code, compute_code_similarity
from evaluators.constraint_checker import evaluate_constraints
from evaluators.llm_judge import evaluate_with_gemini
import json
import csv
import io
import traceback

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/evaluate', methods=['POST'])
def evaluate():
    """Run all deterministic metrics on submitted model responses."""
    try:
        data = request.get_json()

        prompt = data.get('prompt', '')
        reference_code = data.get('reference_code', '')
        test_cases = data.get('test_cases', '')
        models = data.get('models', [])
        task_type = data.get('task_type', 'implementation')

        if not models:
            return jsonify({'error': 'No model responses provided.'}), 400

        results = []

        for model in models:
            model_name = model.get('name', 'Unknown')
            model_code = model.get('code', '')

            if not model_code.strip():
                results.append({
                    'model_name': model_name,
                    'error': 'Empty code submission',
                })
                continue

            try:
                # Run all code metrics
                metrics = evaluate_code(model_code, reference_code, test_cases)

                # Run constraint checking
                constraint_eval = evaluate_constraints(prompt, model_code)

                # Cross-model similarity will be computed separately
                model_result = {
                    'model_name': model_name,
                    'metrics': metrics,
                    'constraint_eval': constraint_eval,
                }
                results.append(model_result)

            except Exception as e:
                results.append({
                    'model_name': model_name,
                    'error': f'Evaluation error: {str(e)}',
                    'traceback': traceback.format_exc(),
                })

        # Compute cross-model similarity matrix
        model_codes = [(m.get('name', 'Unknown'), m.get('code', '')) for m in models if m.get('code', '').strip()]
        similarity_matrix = {}
        for i, (name_a, code_a) in enumerate(model_codes):
            for j, (name_b, code_b) in enumerate(model_codes):
                if i < j:
                    sim = compute_code_similarity(code_a, code_b)
                    key = f"{name_a} vs {name_b}"
                    similarity_matrix[key] = sim

        # Build leaderboard
        leaderboard = []
        for r in results:
            if 'error' not in r:
                m = r['metrics']
                entry = {
                    'model_name': r['model_name'],
                    'overall_score': m['quality_score']['overall'],
                    'test_pass_rate': m['test_results'].get('pass_rate', 0),
                    'constraint_score': r['constraint_eval']['check_results']['score'],
                    'maintainability': m['maintainability']['maintainability_index'],
                    'cyclomatic_complexity': m['cyclomatic']['cyclomatic_complexity'],
                    'halstead_volume': m['halstead'].get('halstead_volume', 0),
                    'similarity_to_ref': m['similarity'].get('combined_similarity', None),
                }
                # Composite rank score
                entry['rank_score'] = round(
                    entry['overall_score'] * 0.4 +
                    entry['constraint_score'] * 0.3 +
                    entry['test_pass_rate'] * 0.3,
                    2
                )
                leaderboard.append(entry)
            else:
                leaderboard.append({
                    'model_name': r['model_name'],
                    'overall_score': 0,
                    'test_pass_rate': 0,
                    'constraint_score': 0,
                    'maintainability': 0,
                    'cyclomatic_complexity': 0,
                    'halstead_volume': 0,
                    'similarity_to_ref': 0,
                    'rank_score': 0,
                    'error': r.get('error', 'Unknown error'),
                })

        leaderboard.sort(key=lambda x: x['rank_score'], reverse=True)

        return jsonify({
            'results': results,
            'leaderboard': leaderboard,
            'similarity_matrix': similarity_matrix,
            'task_type': task_type,
        })

    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/llm_judge', methods=['POST'])
def llm_judge():
    """Run LLM-as-Judge evaluation via Groq API."""
    try:
        data = request.get_json()

        api_key = data.get('api_key', '')
        prompt = data.get('prompt', '')
        code = data.get('code', '')
        reference_code = data.get('reference_code', '')
        model_name = data.get('model_name', '')

        if not code.strip():
            return jsonify({'error': 'No code provided for evaluation.'}), 400

        result = evaluate_with_gemini(
            prompt=prompt,
            code=code,
            reference_code=reference_code,
            api_key=api_key,
            model_name=model_name,
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export/csv', methods=['POST'])
def export_csv():
    """Export evaluation results as CSV."""
    try:
        data = request.get_json()
        results = data.get('results', [])
        leaderboard = data.get('leaderboard', [])

        output = io.StringIO()
        writer = csv.writer(output)

        # Leaderboard section
        writer.writerow(['=== LEADERBOARD ==='])
        writer.writerow(['Rank', 'Model', 'Rank Score', 'Overall Score', 'Test Pass Rate',
                          'Constraint Score', 'Maintainability Index', 'Cyclomatic Complexity',
                          'Halstead Volume', 'Similarity to Reference'])
        for i, entry in enumerate(leaderboard, 1):
            writer.writerow([
                i, entry.get('model_name', ''),
                entry.get('rank_score', 0), entry.get('overall_score', 0),
                entry.get('test_pass_rate', 0), entry.get('constraint_score', 0),
                entry.get('maintainability', 0), entry.get('cyclomatic_complexity', 0),
                entry.get('halstead_volume', 0), entry.get('similarity_to_ref', ''),
            ])

        writer.writerow([])
        writer.writerow(['=== DETAILED METRICS ==='])

        for r in results:
            if 'error' in r:
                continue
            m = r['metrics']
            name = r['model_name']

            writer.writerow([])
            writer.writerow([f'--- {name} ---'])

            # Line metrics
            writer.writerow(['Metric', 'Value'])
            lm = m['line_metrics']
            for k, v in lm.items():
                writer.writerow([k, v])

            # Cyclomatic
            for k, v in m['cyclomatic'].items():
                writer.writerow([k, v])

            # Halstead
            for k, v in m['halstead'].items():
                writer.writerow([k, v])

            # Maintainability
            for k, v in m['maintainability'].items():
                writer.writerow([k, v])

            # Structure
            for k, v in m['structure'].items():
                if k != 'parse_success':
                    writer.writerow([k, v])

            # Constraint checks
            cc = r['constraint_eval']['check_results']
            writer.writerow([])
            writer.writerow(['Constraint Check', 'Status', 'Detail'])
            for check in cc['checks']:
                writer.writerow([check['name'], check['status'], check.get('detail', '')])

        csv_content = output.getvalue()
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=code_evaluation_results.csv'}
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export/json', methods=['POST'])
def export_json():
    """Export full evaluation results as JSON."""
    try:
        data = request.get_json()
        json_content = json.dumps(data, indent=2, default=str)
        return Response(
            json_content,
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=code_evaluation_results.json'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
