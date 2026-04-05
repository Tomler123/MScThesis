/* ═══════════════════════════════════════════════════════════════════════
   Code Generation Evaluation Tool — Frontend Logic
   ═══════════════════════════════════════════════════════════════════════ */

// ─── STATE ──────────────────────────────────────────────────────────────

let currentStep = 1;
let modelCount = 0;
let evaluationData = null;
let chartInstances = {};

const MODEL_COLORS = [
    'rgba(88, 166, 255, 0.85)',    // blue
    'rgba(63, 185, 80, 0.85)',     // green
    'rgba(188, 140, 255, 0.85)',   // purple
    'rgba(240, 136, 62, 0.85)',    // orange
    'rgba(57, 210, 192, 0.85)',    // cyan
    'rgba(247, 120, 186, 0.85)',   // pink
    'rgba(210, 153, 34, 0.85)',    // yellow
];

const MODEL_COLORS_SOLID = [
    '#58a6ff', '#3fb950', '#bc8cff', '#f0883e',
    '#39d2c0', '#f778ba', '#d29922',
];


// ─── STEP NAVIGATION ───────────────────────────────────────────────────

function goToStep(step) {
    if (step === 3 && !evaluationData) {
        // Don't go to results without data unless coming from evaluation
        if (currentStep !== 2) return;
    }

    document.querySelectorAll('.step-panel').forEach(p => p.classList.remove('active'));
    document.getElementById(`step-${step}`).classList.add('active');

    document.querySelectorAll('.steps-bar .step').forEach(s => {
        const sNum = parseInt(s.dataset.step);
        s.classList.remove('active', 'completed');
        if (sNum === step) s.classList.add('active');
        else if (sNum < step) s.classList.add('completed');
    });

    currentStep = step;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}


// ─── MODEL MANAGEMENT ──────────────────────────────────────────────────

function addModel(name = '', code = '') {
    const container = document.getElementById('models-container');
    const idx = modelCount;
    modelCount++;

    const card = document.createElement('div');
    card.className = 'model-card';
    card.id = `model-${idx}`;
    card.innerHTML = `
        <div class="model-card-header">
            <span class="model-num c${idx % 7}">${idx + 1}</span>
            <input type="text" class="model-name" placeholder="Model name (e.g., GPT-4o, Claude 3.5, Gemini)"
                   value="${escapeHtml(name)}" />
            <button class="btn btn-danger btn-sm" onclick="removeModel(${idx})">✕ Remove</button>
        </div>
        <textarea class="model-code" placeholder="Paste the model's code output here...">${escapeHtml(code)}</textarea>
    `;

    container.appendChild(card);
}

function removeModel(idx) {
    const card = document.getElementById(`model-${idx}`);
    if (card) card.remove();
}

function getModels() {
    const cards = document.querySelectorAll('.model-card');
    const models = [];
    cards.forEach(card => {
        const name = card.querySelector('.model-name').value.trim() || `Model ${models.length + 1}`;
        const code = card.querySelector('.model-code').value;
        if (code.trim()) {
            models.push({ name, code });
        }
    });
    return models;
}


// ─── EVALUATION ─────────────────────────────────────────────────────────

async function runEvaluation() {
    const models = getModels();
    if (models.length === 0) {
        showError('Add at least one model response with code.');
        return;
    }

    const prompt = document.getElementById('prompt-input').value;
    const referenceCode = document.getElementById('reference-code').value;
    const testCases = document.getElementById('test-cases').value;
    const taskType = document.getElementById('task-type').value;

    // Switch to results step
    goToStep(3);
    document.getElementById('loading-indicator').style.display = 'flex';
    document.getElementById('results-content').style.display = 'none';

    try {
        const response = await fetch('/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt, reference_code: referenceCode,
                test_cases: testCases, models, task_type: taskType,
            }),
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        evaluationData = await response.json();

        if (evaluationData.error) {
            showError(evaluationData.error);
            return;
        }

        renderResults(evaluationData);

    } catch (err) {
        showError(`Evaluation failed: ${err.message}`);
    } finally {
        document.getElementById('loading-indicator').style.display = 'none';
    }
}


// ─── RENDER RESULTS ─────────────────────────────────────────────────────

function renderResults(data) {
    document.getElementById('results-content').style.display = 'block';

    renderLeaderboard(data.leaderboard);
    renderRankScoresChart(data.leaderboard);
    renderRadarChart(data.results);
    renderMetricsComparisonChart(data.results);
    renderHalsteadChart(data.results);
    renderHeatmap(data.similarity_matrix, data.results);
    renderConstraintDetails(data.results);
    renderDetailedMetrics(data.results);
    renderLLMJudgeButtons(data.results);
}


// ─── LEADERBOARD ────────────────────────────────────────────────────────

function renderLeaderboard(leaderboard) {
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '';

    leaderboard.forEach((entry, i) => {
        const rank = i + 1;
        const tr = document.createElement('tr');
        tr.className = rank <= 3 ? `rank-${rank}` : '';

        const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `#${rank}`;

        tr.innerHTML = `
            <td>${medal}</td>
            <td><strong>${escapeHtml(entry.model_name)}</strong>${entry.error ? ' ⚠️' : ''}</td>
            <td>${scoreBadge(entry.rank_score)}</td>
            <td>${scoreBadge(entry.overall_score)}</td>
            <td>${scoreBadge(entry.test_pass_rate)}%</td>
            <td>${scoreBadge(entry.constraint_score)}%</td>
            <td>${entry.maintainability?.toFixed(1) || '—'}</td>
            <td>${entry.cyclomatic_complexity || '—'}</td>
        `;
        tbody.appendChild(tr);
    });
}

function scoreBadge(value) {
    const num = parseFloat(value) || 0;
    const cls = num >= 75 ? 'score-high' : num >= 50 ? 'score-mid' : 'score-low';
    return `<span class="score-badge ${cls}">${num.toFixed(1)}</span>`;
}


// ─── CHARTS ─────────────────────────────────────────────────────────────

function destroyChart(key) {
    if (chartInstances[key]) {
        chartInstances[key].destroy();
        delete chartInstances[key];
    }
}

function renderRankScoresChart(leaderboard) {
    destroyChart('rank');
    const ctx = document.getElementById('chart-rank-scores').getContext('2d');

    const labels = leaderboard.map(e => e.model_name);
    const rankScores = leaderboard.map(e => e.rank_score);
    const colors = leaderboard.map((_, i) => MODEL_COLORS[i % MODEL_COLORS.length]);

    chartInstances['rank'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Rank Score',
                data: rankScores,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.85', '1')),
                borderWidth: 1,
                borderRadius: 6,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(48, 54, 61, 0.5)' },
                    ticks: { color: '#8b949e' },
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#8b949e' },
                },
            },
        },
    });
}

function renderRadarChart(results) {
    destroyChart('radar');
    const ctx = document.getElementById('chart-radar').getContext('2d');

    const validResults = results.filter(r => !r.error && r.metrics);
    if (!validResults.length) return;

    const labels = [
        'Maintainability', 'Test Pass Rate', 'Constraint Adherence',
        'Documentation', 'DRY Score', 'Structure', 'Complexity (inv.)',
    ];

    const datasets = validResults.map((r, i) => {
        const m = r.metrics;
        const qs = m.quality_score.breakdown;
        return {
            label: r.model_name,
            data: [
                qs.maintainability,
                qs.test_pass_rate,
                r.constraint_eval.check_results.score,
                qs.documentation,
                qs.dry,
                qs.structure,
                qs.complexity,
            ],
            borderColor: MODEL_COLORS_SOLID[i % MODEL_COLORS_SOLID.length],
            backgroundColor: MODEL_COLORS[i % MODEL_COLORS.length].replace('0.85', '0.15'),
            borderWidth: 2,
            pointRadius: 3,
        };
    });

    chartInstances['radar'] = new Chart(ctx, {
        type: 'radar',
        data: { labels, datasets },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: '#8b949e', padding: 12 },
                },
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(48, 54, 61, 0.4)' },
                    angleLines: { color: 'rgba(48, 54, 61, 0.4)' },
                    pointLabels: { color: '#8b949e', font: { size: 11 } },
                    ticks: { color: '#6e7681', backdropColor: 'transparent' },
                },
            },
        },
    });
}

function renderMetricsComparisonChart(results) {
    destroyChart('metrics');
    const ctx = document.getElementById('chart-metrics-comparison').getContext('2d');

    const validResults = results.filter(r => !r.error && r.metrics);
    if (!validResults.length) return;

    const labels = validResults.map(r => r.model_name);

    const datasets = [
        {
            label: 'SLOC',
            data: validResults.map(r => r.metrics.line_metrics.sloc),
            backgroundColor: 'rgba(88, 166, 255, 0.7)',
        },
        {
            label: 'Cyclomatic Complexity',
            data: validResults.map(r => r.metrics.cyclomatic.cyclomatic_complexity || 0),
            backgroundColor: 'rgba(240, 136, 62, 0.7)',
        },
        {
            label: 'AST Depth',
            data: validResults.map(r => r.metrics.ast_metrics.ast_max_depth || 0),
            backgroundColor: 'rgba(188, 140, 255, 0.7)',
        },
        {
            label: 'Max Nesting',
            data: validResults.map(r => r.metrics.nesting.max_nesting_depth || 0),
            backgroundColor: 'rgba(63, 185, 80, 0.7)',
        },
    ];

    chartInstances['metrics'] = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#8b949e' } },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(48, 54, 61, 0.5)' },
                    ticks: { color: '#8b949e' },
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#8b949e' },
                },
            },
        },
    });
}

function renderHalsteadChart(results) {
    destroyChart('halstead');
    const ctx = document.getElementById('chart-halstead').getContext('2d');

    const validResults = results.filter(r => !r.error && r.metrics);
    if (!validResults.length) return;

    const labels = validResults.map(r => r.model_name);

    const datasets = [
        {
            label: 'Volume',
            data: validResults.map(r => r.metrics.halstead.halstead_volume || 0),
            borderColor: '#58a6ff',
            backgroundColor: 'rgba(88, 166, 255, 0.15)',
            fill: true,
        },
        {
            label: 'Difficulty',
            data: validResults.map(r => r.metrics.halstead.halstead_difficulty || 0),
            borderColor: '#f0883e',
            backgroundColor: 'rgba(240, 136, 62, 0.15)',
            fill: true,
        },
    ];

    chartInstances['halstead'] = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#8b949e' } },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(48, 54, 61, 0.5)' },
                    ticks: { color: '#8b949e' },
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#8b949e' },
                },
            },
        },
    });
}


// ─── HEATMAP ────────────────────────────────────────────────────────────

function renderHeatmap(similarityMatrix, results) {
    const container = document.getElementById('heatmap-container');
    const validResults = results.filter(r => !r.error);

    if (validResults.length < 2) {
        container.innerHTML = '<p style="color: var(--text-muted);">Need at least 2 models for similarity comparison.</p>';
        return;
    }

    const names = validResults.map(r => r.model_name);

    let html = '<table class="heatmap-table"><thead><tr><th></th>';
    names.forEach(n => { html += `<th>${escapeHtml(n)}</th>`; });
    html += '</tr></thead><tbody>';

    names.forEach((nameA, i) => {
        html += `<tr><th>${escapeHtml(nameA)}</th>`;
        names.forEach((nameB, j) => {
            if (i === j) {
                html += '<td style="background: rgba(88,166,255,0.25); color: var(--accent);">1.00</td>';
            } else {
                const key1 = `${nameA} vs ${nameB}`;
                const key2 = `${nameB} vs ${nameA}`;
                const sim = similarityMatrix[key1] || similarityMatrix[key2];
                const val = sim ? sim.combined_similarity : 0;
                const hue = Math.round(val * 120); // 0=red, 120=green
                const bg = `hsla(${hue}, 60%, 40%, 0.3)`;
                const color = `hsl(${hue}, 70%, 65%)`;
                html += `<td style="background: ${bg}; color: ${color};" title="${JSON.stringify(sim || {}).replace(/"/g, '&quot;')}">${val.toFixed(2)}</td>`;
            }
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}


// ─── CONSTRAINT DETAILS ─────────────────────────────────────────────────

function renderConstraintDetails(results) {
    const container = document.getElementById('constraint-details');
    container.innerHTML = '';

    results.forEach(r => {
        if (r.error) return;

        const block = document.createElement('div');
        block.className = 'constraint-model-block';

        const checks = r.constraint_eval.check_results;
        let checksHtml = '';
        checks.checks.forEach(c => {
            const cls = c.status === 'pass' ? 'check-pass' : c.status === 'fail' ? 'check-fail' : 'check-partial';
            const icon = c.status === 'pass' ? '✓' : c.status === 'fail' ? '✗' : '◐';
            checksHtml += `
                <div class="check-item ${cls}">
                    <span class="check-icon">${icon}</span>
                    <span>${escapeHtml(c.name)}</span>
                </div>
                <div class="check-detail">${escapeHtml(c.detail || '')}</div>
            `;
        });

        block.innerHTML = `
            <div class="constraint-model-name">${escapeHtml(r.model_name)} — ${scoreBadge(checks.score)}% (${checks.passed}/${checks.total})</div>
            ${checksHtml}
        `;
        container.appendChild(block);
    });
}


// ─── DETAILED METRICS ───────────────────────────────────────────────────

function renderDetailedMetrics(results) {
    const container = document.getElementById('detailed-metrics');
    container.innerHTML = '';

    results.forEach((r, idx) => {
        if (r.error) return;

        const m = r.metrics;
        const acc = document.createElement('div');
        acc.className = 'metrics-accordion';

        const categories = [
            { title: 'Line Metrics', data: m.line_metrics },
            { title: 'Cyclomatic Complexity', data: m.cyclomatic },
            { title: 'Halstead Metrics', data: m.halstead },
            { title: 'AST Structural', data: m.ast_metrics, skip: ['ast_node_types'] },
            { title: 'Maintainability', data: m.maintainability },
            { title: 'Code Structure', data: m.structure, skip: ['parse_success'] },
            { title: 'Nesting Depth', data: m.nesting },
            { title: 'Identifier Quality', data: m.identifiers },
            { title: 'Imports', data: m.imports, skip: ['external_libs', 'stdlib_imports'] },
            { title: 'Error Handling', data: m.error_handling },
            { title: 'DRY Score', data: m.dry },
            { title: 'Similarity to Reference', data: m.similarity },
            { title: 'Test Results', data: { total: m.test_results.total, passed: m.test_results.passed, failed: m.test_results.failed, errors: m.test_results.errors, pass_rate: m.test_results.pass_rate } },
            { title: 'Quality Score Breakdown', data: m.quality_score.breakdown },
        ];

        let metricsHtml = '';
        categories.forEach(cat => {
            if (!cat.data) return;
            const skip = cat.skip || [];
            const items = Object.entries(cat.data)
                .filter(([k, v]) => !skip.includes(k) && v !== null && typeof v !== 'object')
                .map(([k, v]) => `
                    <div class="metric-item">
                        <div class="metric-label">${k.replace(/_/g, ' ')}</div>
                        <div class="metric-value">${formatMetricValue(v)}</div>
                    </div>
                `).join('');

            if (items) {
                metricsHtml += `
                    <div class="metrics-accordion-header" onclick="this.nextElementSibling.classList.toggle('open')">
                        <span>${cat.title}</span>
                        <span style="color: var(--text-muted);">▼</span>
                    </div>
                    <div class="metrics-accordion-body">
                        <div class="metrics-grid">${items}</div>
                    </div>
                `;
            }
        });

        acc.innerHTML = `
            <div class="constraint-model-name" style="margin-bottom: 0.8rem;">${escapeHtml(r.model_name)}</div>
            ${metricsHtml}
        `;
        container.appendChild(acc);
    });
}

function formatMetricValue(v) {
    if (typeof v === 'number') {
        return v % 1 === 0 ? v.toString() : v.toFixed(2);
    }
    if (typeof v === 'boolean') return v ? '✓ Yes' : '✗ No';
    return escapeHtml(String(v));
}


// ─── LLM JUDGE ──────────────────────────────────────────────────────────

function renderLLMJudgeButtons(results) {
    const container = document.getElementById('llm-judge-models');
    container.innerHTML = '';

    results.forEach((r, i) => {
        if (r.error) return;
        const row = document.createElement('div');
        row.className = 'llm-model-row';
        row.innerHTML = `
            <span class="model-num c${i % 7}" style="width:24px;height:24px;font-size:0.7rem;">${i + 1}</span>
            <span class="model-label">${escapeHtml(r.model_name)}</span>
            <button class="btn btn-secondary btn-sm" onclick="runLLMJudge('${escapeHtml(r.model_name)}', ${i})">
                🧠 Run LLM Judge
            </button>
        `;
        container.appendChild(row);
    });
}

async function runLLMJudge(modelName, modelIdx) {
    const apiKey = document.getElementById('groq-api-key').value.trim();
    if (!apiKey) {
        showError('Enter your Groq API key first.');
        return;
    }

    const models = getModels();
    const modelData = models[modelIdx];
    if (!modelData) {
        showError('Model data not found.');
        return;
    }

    const prompt = document.getElementById('prompt-input').value;
    const referenceCode = document.getElementById('reference-code').value;

    // Show loading
    const resultsContainer = document.getElementById('llm-judge-results');
    const loadingId = `llm-loading-${modelIdx}`;
    const existingLoading = document.getElementById(loadingId);
    if (existingLoading) existingLoading.remove();

    const loading = document.createElement('div');
    loading.id = loadingId;
    loading.className = 'llm-result-card';
    loading.innerHTML = `<div class="loading-state" style="padding:1rem;"><div class="spinner"></div><p>Querying Llama 3.3 70B for ${escapeHtml(modelName)}...</p></div>`;
    resultsContainer.appendChild(loading);

    try {
        const response = await fetch('/llm_judge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                api_key: apiKey,
                prompt,
                code: modelData.code,
                reference_code: referenceCode,
                model_name: modelName,
            }),
        });

        const result = await response.json();
        loading.remove();

        if (result.error) {
            showError(`LLM Judge error: ${result.error}`);
            return;
        }

        renderLLMResult(result, modelIdx);

    } catch (err) {
        loading.remove();
        showError(`LLM Judge failed: ${err.message}`);
    }
}

function renderLLMResult(result, modelIdx) {
    const container = document.getElementById('llm-judge-results');

    // Remove existing result for this model
    const existingId = `llm-result-${modelIdx}`;
    const existing = document.getElementById(existingId);
    if (existing) existing.remove();

    const card = document.createElement('div');
    card.id = existingId;
    card.className = 'llm-result-card';

    // Scores grid
    const scores = result.scores || {};
    let scoresHtml = '';
    Object.entries(scores).forEach(([key, val]) => {
        const color = val >= 8 ? 'var(--green)' : val >= 5 ? 'var(--yellow)' : 'var(--red)';
        scoresHtml += `
            <div class="llm-score-item">
                <div class="llm-score-label">${key.replace(/_/g, ' ')}</div>
                <div class="llm-score-value" style="color: ${color};">${val}/10</div>
            </div>
        `;
    });

    // Overall
    const overallColor = result.overall_score >= 8 ? 'var(--green)' : result.overall_score >= 5 ? 'var(--yellow)' : 'var(--red)';

    // Feedback lists
    const listItems = (arr) => (arr || []).map(s => `<li>${escapeHtml(s)}</li>`).join('');

    card.innerHTML = `
        <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.8rem;">
            <span class="model-num c${modelIdx % 7}" style="width:24px;height:24px;font-size:0.7rem;">${modelIdx + 1}</span>
            <strong>${escapeHtml(result.model_evaluated || '')}</strong>
            <span style="margin-left:auto; font-size:1.5rem; font-weight:700; font-family:var(--font-mono); color:${overallColor};">
                ${result.overall_score}/10
            </span>
        </div>
        <p style="color:var(--text-secondary);font-size:0.85rem;">${escapeHtml(result.summary || '')}</p>
        <div class="llm-scores-grid">${scoresHtml}</div>
        <div class="llm-feedback">
            <h4>💪 Strengths</h4>
            <ul>${listItems(result.strengths)}</ul>
            <h4>⚠️ Weaknesses</h4>
            <ul>${listItems(result.weaknesses)}</ul>
            <h4>💡 Suggestions</h4>
            <ul>${listItems(result.suggestions)}</ul>
        </div>
        <div style="margin-top:0.5rem;color:var(--text-muted);font-size:0.75rem;">
            Judge: ${escapeHtml(result.judge_model || '')} via ${escapeHtml(result.provider || '')}
        </div>
    `;

    container.appendChild(card);
}


// ─── EXPORT ─────────────────────────────────────────────────────────────

async function exportCSV() {
    if (!evaluationData) return;
    try {
        const response = await fetch('/export/csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(evaluationData),
        });
        const blob = await response.blob();
        downloadBlob(blob, 'code_evaluation_results.csv');
    } catch (err) {
        showError(`Export failed: ${err.message}`);
    }
}

async function exportJSON() {
    if (!evaluationData) return;
    try {
        const response = await fetch('/export/json', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(evaluationData),
        });
        const blob = await response.blob();
        downloadBlob(blob, 'code_evaluation_results.json');
    } catch (err) {
        showError(`Export failed: ${err.message}`);
    }
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}


// ─── UTILITIES ──────────────────────────────────────────────────────────

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function showError(msg) {
    const toast = document.createElement('div');
    toast.className = 'error-toast';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}


// ─── INIT ───────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    // Start with 2 model slots
    addModel();
    addModel();
});
