"""
Writing & Communication Evaluation Tool — Flask Application
MSc Thesis: Comparing Generative AI Models
"""

from flask import Flask, render_template, request, jsonify
import json
import csv
import io
import numpy as np

from metrics_engine import (
    evaluate_model,
    compute_category_scores,
    compute_composite_score,
    compute_z_scores,
    compute_cross_model_statistics,
    DEFAULT_WEIGHTS,
)
from constraint_parser import extract_constraints, evaluate_constraints

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/evaluate', methods=['POST'])
def evaluate():
    """Main evaluation endpoint. Receives prompt, context, and model responses."""
    try:
        data = request.get_json()
        prompt_text = data.get('prompt', '')
        context_text = data.get('context', '')
        models = data.get('models', [])  # [{name, response}, ...]
        weights = data.get('weights', DEFAULT_WEIGHTS)

        if not prompt_text:
            return jsonify({'error': 'Prompt text is required'}), 400
        if not models:
            return jsonify({'error': 'At least one model response is required'}), 400

        # 1. Parse constraints from prompt
        constraints = extract_constraints(prompt_text)

        # 2. Evaluate each model
        all_results = {}
        all_category_scores = {}

        for model in models:
            name = model['name']
            response = model['response']

            if not response.strip():
                continue

            # Evaluate constraints
            constraint_results = evaluate_constraints(response, constraints)

            # Run all metrics
            metrics = evaluate_model(response, prompt_text, context_text, constraint_results)

            # Compute category scores
            cat_scores = compute_category_scores(metrics)
            all_category_scores[name] = cat_scores

            # Compute composite score
            composite = compute_composite_score(cat_scores, weights)

            all_results[name] = {
                'metrics': metrics,
                'category_scores': cat_scores,
                'composite_score': composite,
                'constraint_details': constraint_results,
            }

        # 3. Cross-model analysis
        z_scores = compute_z_scores(all_category_scores)
        cross_stats = compute_cross_model_statistics(all_category_scores)

        # 4. Build leaderboard
        leaderboard = sorted(
            [{'name': n, 'composite': r['composite_score']} for n, r in all_results.items()],
            key=lambda x: x['composite'],
            reverse=True
        )
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1

        return jsonify({
            'results': all_results,
            'z_scores': z_scores,
            'cross_model_stats': cross_stats,
            'leaderboard': leaderboard,
            'parsed_constraints': [c['description'] for c in constraints],
            'weights': weights,
            'model_count': len(all_results)
        })

    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@app.route('/export/csv', methods=['POST'])
def export_csv():
    """Export results as CSV."""
    try:
        data = request.get_json()
        results = data.get('results', {})

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        categories = list(DEFAULT_WEIGHTS.keys())
        header = ['Model', 'Composite Score'] + [c.replace('_', ' ').title() for c in categories]
        writer.writerow(header)

        for name, r in results.items():
            row = [name, r['composite_score']]
            for cat in categories:
                row.append(r['category_scores'].get(cat, 0))
            writer.writerow(row)

        return jsonify({'csv': output.getvalue()})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export/json', methods=['POST'])
def export_json():
    """Export full results as JSON."""
    try:
        data = request.get_json()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
