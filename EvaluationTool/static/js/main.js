/* ═══════════════════════════════════════════════════════════════
   AI Summarization Benchmark Tool — Frontend Logic
   ═══════════════════════════════════════════════════════════════ */

// ── State ──────────────────────────────────────────────────────
const state = {
    sourceType: 'text',   // 'text' | 'pdf' | 'url'
    sourceText: '',
    promptText: '',
    referenceSummary: '',
    models: [],
    results: null,
    judgeResults: null,
    charts: {},
    nextId: 1,
};

const MODEL_COLORS = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#ec4899', '#06b6d4', '#f97316', '#14b8a6', '#6366f1'
];

// Key metrics for display in leaderboard / charts
const DISPLAY_METRICS = {
    'rouge1_f':           { label: 'ROUGE-1 F1',         category: 'Content Overlap' },
    'rouge2_f':           { label: 'ROUGE-2 F1',         category: 'Content Overlap' },
    'rougeL_f':           { label: 'ROUGE-L F1',         category: 'Content Overlap' },
    'bleu':               { label: 'BLEU',               category: 'Content Overlap' },
    'cosine_similarity':  { label: 'Cosine Similarity',  category: 'Content Overlap' },
    'flesch_reading_ease':{ label: 'Flesch Reading Ease', category: 'Readability' },
    'flesch_kincaid_grade':{ label: 'Flesch-Kincaid Grade', category: 'Readability' },
    'gunning_fog':        { label: 'Gunning Fog Index',  category: 'Readability' },
    'compression_ratio':  { label: 'Compression Ratio',  category: 'Informativeness' },
    'lexical_diversity':  { label: 'Lexical Diversity',   category: 'Informativeness' },
    'information_density':{ label: 'Information Density', category: 'Informativeness' },
    'redundancy':         { label: 'Redundancy',         category: 'Informativeness' },
    'coherence':          { label: 'Coherence',          category: 'Coherence' },
    'constraint_adherence':{ label: 'Constraint Adherence', category: 'Constraints' },
};

// Metrics used for radar chart (0-1 scale naturally)
const RADAR_METRICS = [
    'rouge1_f', 'rouge2_f', 'rougeL_f', 'bleu', 'cosine_similarity',
    'lexical_diversity', 'information_density', 'coherence', 'constraint_adherence'
];

// ── Initialization ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    switchStep(1);
    addModel();  // Start with one model slot
});

// ── Step Navigation ────────────────────────────────────────────
function switchStep(n) {
    document.querySelectorAll('.step-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.step-panel').forEach(p => p.classList.remove('active'));
    document.querySelector(`[data-step="${n}"]`).classList.add('active');
    document.getElementById(`step-${n}`).classList.add('active');
}

// ── Source Type Tabs ───────────────────────────────────────────
function selectSourceType(type) {
    state.sourceType = type;
    document.querySelectorAll('.source-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-source="${type}"]`).classList.add('active');
    document.getElementById('source-text-area').style.display = type === 'text' ? 'block' : 'none';
    document.getElementById('source-pdf-area').style.display = type === 'pdf' ? 'block' : 'none';
    document.getElementById('source-url-area').style.display = type === 'url' ? 'block' : 'none';
}

// ── PDF Upload for Source ──────────────────────────────────────
async function handleSourcePDF(input) {
    const file = input.files[0];
    if (!file) return;
    const statusEl = document.getElementById('pdf-status');
    statusEl.textContent = 'Extracting text from PDF...';
    statusEl.className = 'text-sm text-accent';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/extract-pdf', { method: 'POST', body: formData });
        const data = await resp.json();
        if (data.error) throw new Error(data.error);
        state.sourceText = data.text;
        statusEl.textContent = `Extracted ${data.text.split(/\s+/).length} words from "${file.name}"`;
        statusEl.className = 'text-sm text-success';
    } catch (e) {
        statusEl.textContent = `Error: ${e.message}`;
        statusEl.className = 'text-sm text-danger';
    }
}

// ── URL Fetch Note ─────────────────────────────────────────────
function updateSourceURL() {
    const url = document.getElementById('source-url-input').value.trim();
    document.getElementById('url-status').textContent = url
        ? 'URL saved. Paste the webpage content below as the source text for ROUGE/BLEU comparison.'
        : '';
}

// ── Model Management ───────────────────────────────────────────
function addModel() {
    const id = state.nextId++;
    state.models.push({ id, name: `Model ${id}`, response: '' });
    renderModelList();
}

function removeModel(id) {
    state.models = state.models.filter(m => m.id !== id);
    renderModelList();
}

function renderModelList() {
    const container = document.getElementById('model-list');
    container.innerHTML = state.models.map((m, idx) => `
        <div class="model-entry" id="model-${m.id}">
            <div class="model-header">
                <div class="inline-flex">
                    <span style="color:${MODEL_COLORS[idx % MODEL_COLORS.length]};font-size:1.1rem">●</span>
                    <input type="text" value="${m.name}"
                           onchange="updateModelName(${m.id}, this.value)"
                           placeholder="Model name" />
                </div>
                <button class="btn btn-danger btn-sm" onclick="removeModel(${m.id})">✕ Remove</button>
            </div>
            <div class="model-resp-area">
                <textarea id="mresp-${m.id}" placeholder="Paste the model's summary response here..."
                          onchange="updateModelResponse(${m.id})">${m.response}</textarea>
                <div class="file-upload-area">
                    <label class="file-upload-btn">
                        📄 .txt
                        <input type="file" accept=".txt" onchange="loadModelFile(${m.id}, this)" />
                    </label>
                    <label class="file-upload-btn">
                        📋 .json
                        <input type="file" accept=".json" onchange="loadModelJSON(${m.id}, this)" />
                    </label>
                </div>
            </div>
        </div>
    `).join('');
}

function updateModelName(id, name) {
    const m = state.models.find(m => m.id === id);
    if (m) m.name = name;
}

function updateModelResponse(id) {
    const m = state.models.find(m => m.id === id);
    if (m) m.response = document.getElementById(`mresp-${m.id}`).value;
}

function loadModelFile(id, input) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        const text = e.target.result;
        const m = state.models.find(m => m.id === id);
        if (m) {
            m.response = text;
            document.getElementById(`mresp-${m.id}`).value = text;
        }
    };
    reader.readAsText(file);
}

function loadModelJSON(id, input) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            // Expecting { "response": "..." } or { "text": "..." } or { "summary": "..." }
            const text = data.response || data.text || data.summary || data.content || '';
            const m = state.models.find(m => m.id === id);
            if (m) {
                m.response = text;
                document.getElementById(`mresp-${m.id}`).value = text;
            }
        } catch (err) {
            showToast('Invalid JSON file', 'error');
        }
    };
    reader.readAsText(file);
}

// ── Collect current form data ──────────────────────────────────
function collectData() {
    // Sync responses from DOM
    state.models.forEach(m => {
        const el = document.getElementById(`mresp-${m.id}`);
        if (el) m.response = el.value;
    });

    let sourceText = state.sourceText;
    if (state.sourceType === 'text') {
        sourceText = document.getElementById('source-text-input').value;
    } else if (state.sourceType === 'url') {
        const urlText = document.getElementById('source-url-text').value;
        if (urlText) sourceText = urlText;
    }

    return {
        source_text: sourceText,
        prompt_text: document.getElementById('prompt-input').value,
        reference_summary: document.getElementById('reference-input').value || '',
        use_bert: document.getElementById('use-bert-checkbox').checked,
        models: state.models.map(m => ({ name: m.name, response: m.response })),
    };
}

// ── Run Automated Evaluation ───────────────────────────────────
async function runEvaluation() {
    const data = collectData();
    if (!data.models.length || !data.models.some(m => m.response.trim())) {
        showToast('Add at least one model with a response', 'error');
        return;
    }

    showLoading('Running NLP evaluation pipeline...');

    try {
        const resp = await fetch('/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await resp.json();
        if (result.error) throw new Error(result.error);

        state.results = result;
        hideLoading();
        switchStep(3);
        renderResults(result);
    } catch (e) {
        hideLoading();
        showToast(`Evaluation error: ${e.message}`, 'error');
    }
}

// ── Run LLM Judge ──────────────────────────────────────────────
async function runLLMJudge() {
    const apiKey = document.getElementById('gemini-api-key').value.trim();
    if (!apiKey) {
        showToast('Enter your Gemini API key first', 'error');
        return;
    }

    const data = collectData();
    showLoading('Gemini is evaluating responses...');

    try {
        const resp = await fetch('/llm-judge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                api_key: apiKey,
                source_text: data.source_text,
                prompt_text: data.prompt_text,
                models: data.models,
            })
        });
        const result = await resp.json();
        if (result.error) throw new Error(result.error);

        state.judgeResults = result;
        hideLoading();
        renderJudgeResults(result);
    } catch (e) {
        hideLoading();
        showToast(`LLM Judge error: ${e.message}`, 'error');
    }
}

// ═══════════════════════════════════════════════════════════════
// RENDERING — Results Dashboard
// ═══════════════════════════════════════════════════════════════

function renderResults(data) {
    const container = document.getElementById('results-container');

    // Destroy previous charts
    Object.values(state.charts).forEach(c => c.destroy && c.destroy());
    state.charts = {};

    container.innerHTML = `
        <!-- Leaderboard -->
        <div class="card" style="grid-column: 1 / -1;">
            <div class="card-title"><span class="icon">🏆</span> Leaderboard — Composite Score Ranking</div>
            <div style="overflow-x:auto;" id="leaderboard-wrap"></div>
        </div>

        <!-- Radar Chart -->
        <div class="chart-container">
            <div class="chart-title"><span class="icon">🕸</span> Radar — Key Metrics</div>
            <canvas id="radar-chart"></canvas>
        </div>

        <!-- Bar Chart -->
        <div class="chart-container">
            <div class="chart-title"><span class="icon">📊</span> Grouped Bar — All Metrics</div>
            <canvas id="bar-chart"></canvas>
        </div>

        <!-- Heatmap -->
        <div class="chart-container" style="grid-column: 1 / -1;">
            <div class="chart-title"><span class="icon">🌡</span> Heatmap — Normalized Metric Scores</div>
            <div id="heatmap-wrap" style="overflow-x:auto;"></div>
        </div>

        <!-- Constraint Details -->
        <div class="card" style="grid-column: 1 / -1;">
            <div class="card-title"><span class="icon">📋</span> Constraint Adherence Details</div>
            <div id="constraint-details-wrap"></div>
        </div>

        <!-- Statistics -->
        <div class="card" style="grid-column: 1 / -1;">
            <div class="card-title"><span class="icon">📈</span> Cross-Model Statistics</div>
            <div id="stats-wrap" style="overflow-x:auto;"></div>
        </div>

        <!-- LLM Judge Section -->
        <div class="card judge-card" style="grid-column: 1 / -1;">
            <div class="card-title"><span class="icon">🧠</span> LLM-as-Judge (Google Gemini) — Optional</div>
            <p class="text-sm text-muted mb-1">Activate Gemini for qualitative evaluation. Requires a free Gemini API key.</p>
            <div class="form-row" style="max-width:600px;">
                <div class="form-group">
                    <label>Gemini API Key</label>
                    <input type="password" id="gemini-api-key" placeholder="AIza..." />
                </div>
                <div class="form-group" style="display:flex;align-items:flex-end;">
                    <button class="btn btn-purple" onclick="runLLMJudge()">🧠 Run LLM Judge</button>
                </div>
            </div>
            <div id="judge-results-wrap"></div>
        </div>

        <!-- Export -->
        <div class="card" style="grid-column: 1 / -1;">
            <div class="btn-group">
                <button class="btn btn-secondary" onclick="exportCSV()">📥 Export CSV</button>
                <button class="btn btn-secondary" onclick="exportJSON()">📥 Export JSON</button>
            </div>
        </div>
    `;

    renderLeaderboard(data.results);
    renderRadarChart(data.results);
    renderBarChart(data.results);
    renderHeatmap(data.results);
    renderConstraintDetails(data.results);
    renderStatistics(data.statistics);
}

// ── Leaderboard Table ──────────────────────────────────────────
function renderLeaderboard(results) {
    const metricKeys = Object.keys(DISPLAY_METRICS);
    let html = `<table class="leaderboard-table"><thead><tr>
        <th>Rank</th><th>Model</th><th>Composite</th>`;
    metricKeys.forEach(k => {
        html += `<th title="${DISPLAY_METRICS[k].category}">${DISPLAY_METRICS[k].label}</th>`;
    });
    html += `</tr></thead><tbody>`;

    results.forEach(r => {
        const rankClass = r.rank <= 3 ? `rank-${r.rank}` : 'rank-other';
        html += `<tr>
            <td><span class="rank-badge ${rankClass}">${r.rank}</span></td>
            <td style="font-family:'Outfit';font-weight:600;font-size:0.85rem;">${r.model_name}</td>
            <td>
                <span class="composite-score" style="font-size:1.1rem;color:${scoreColor(r.composite_score, 100)}">${r.composite_score}</span>
                <span class="text-muted text-xs">/100</span>
            </td>`;
        metricKeys.forEach(k => {
            const v = r.metrics[k];
            const display = v !== undefined && v !== null ? (typeof v === 'number' ? v.toFixed(4) : v) : '—';
            html += `<td>${display}</td>`;
        });
        html += `</tr>`;
    });

    html += `</tbody></table>`;
    document.getElementById('leaderboard-wrap').innerHTML = html;
}

// ── Radar Chart ────────────────────────────────────────────────
function renderRadarChart(results) {
    const ctx = document.getElementById('radar-chart').getContext('2d');
    const labels = RADAR_METRICS.map(k => DISPLAY_METRICS[k]?.label || k);
    const datasets = results.map((r, i) => ({
        label: r.model_name,
        data: RADAR_METRICS.map(k => r.metrics[k] || 0),
        borderColor: MODEL_COLORS[i % MODEL_COLORS.length],
        backgroundColor: MODEL_COLORS[i % MODEL_COLORS.length] + '20',
        borderWidth: 2,
        pointRadius: 3,
    }));

    state.charts.radar = new Chart(ctx, {
        type: 'radar',
        data: { labels, datasets },
        options: {
            responsive: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 1,
                    grid: { color: 'rgba(255,255,255,0.06)' },
                    angleLines: { color: 'rgba(255,255,255,0.06)' },
                    pointLabels: { color: '#94a3b8', font: { size: 10, family: 'Outfit' } },
                    ticks: { display: false },
                }
            },
            plugins: {
                legend: { labels: { color: '#e2e8f0', font: { family: 'Outfit' } } }
            }
        }
    });
}

// ── Bar Chart ──────────────────────────────────────────────────
function renderBarChart(results) {
    const ctx = document.getElementById('bar-chart').getContext('2d');
    const keys = Object.keys(DISPLAY_METRICS);
    const labels = keys.map(k => DISPLAY_METRICS[k].label);
    const datasets = results.map((r, i) => ({
        label: r.model_name,
        data: keys.map(k => {
            const v = r.metrics[k];
            return v !== undefined && v !== null ? v : 0;
        }),
        backgroundColor: MODEL_COLORS[i % MODEL_COLORS.length] + 'AA',
        borderColor: MODEL_COLORS[i % MODEL_COLORS.length],
        borderWidth: 1,
    }));

    state.charts.bar = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#e2e8f0', font: { family: 'Outfit' } } }
            },
            scales: {
                x: {
                    ticks: { color: '#94a3b8', font: { size: 9, family: 'Outfit' }, maxRotation: 45 },
                    grid: { color: 'rgba(255,255,255,0.04)' },
                },
                y: {
                    ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono' } },
                    grid: { color: 'rgba(255,255,255,0.04)' },
                }
            }
        }
    });
}

// ── Heatmap ────────────────────────────────────────────────────
function renderHeatmap(results) {
    const keys = Object.keys(DISPLAY_METRICS);

    // Normalize each metric across models to 0-1 for coloring
    const normalized = {};
    keys.forEach(k => {
        const vals = results.map(r => r.metrics[k] ?? 0);
        const min = Math.min(...vals);
        const max = Math.max(...vals);
        const range = max - min || 1;
        normalized[k] = vals.map(v => (v - min) / range);
    });

    let html = `<table class="heatmap-table"><thead><tr><th>Model</th>`;
    keys.forEach(k => { html += `<th>${DISPLAY_METRICS[k].label}</th>`; });
    html += `</tr></thead><tbody>`;

    results.forEach((r, i) => {
        html += `<tr><td style="font-family:Outfit;font-weight:600;color:${MODEL_COLORS[i % MODEL_COLORS.length]}">${r.model_name}</td>`;
        keys.forEach((k, ki) => {
            const raw = r.metrics[k];
            const norm = normalized[k][i];
            const bg = heatmapColor(norm);
            const display = raw !== undefined && raw !== null ? (typeof raw === 'number' ? raw.toFixed(3) : raw) : '—';
            html += `<td style="background:${bg};color:#fff;">${display}</td>`;
        });
        html += `</tr>`;
    });

    html += `</tbody></table>`;
    document.getElementById('heatmap-wrap').innerHTML = html;
}

function heatmapColor(value) {
    // Red (0) → Yellow (0.5) → Green (1)
    const r = value < 0.5 ? 200 : Math.round(200 - (value - 0.5) * 2 * 160);
    const g = value < 0.5 ? Math.round(60 + value * 2 * 140) : 200;
    const b = 60;
    return `rgba(${r},${g},${b},0.7)`;
}

// ── Constraint Details ─────────────────────────────────────────
function renderConstraintDetails(results) {
    let html = '';
    results.forEach((r, i) => {
        const cr = r.constraint_result;
        html += `<div style="margin-bottom:1rem;">
            <div style="font-weight:600;color:${MODEL_COLORS[i % MODEL_COLORS.length]};margin-bottom:0.5rem;">
                ${r.model_name}
                <span class="tag ${cr.overall_score >= 0.8 ? 'tag-green' : cr.overall_score >= 0.5 ? 'tag-blue' : 'tag-purple'}">${(cr.overall_score * 100).toFixed(1)}%</span>
                <span class="text-muted text-xs">${cr.num_passed}/${cr.num_constraints} constraints passed</span>
            </div>`;

        if (cr.details && cr.details.length) {
            cr.details.forEach(d => {
                const icon = d.passed ? '✅' : '❌';
                html += `<div class="constraint-item">
                    <span class="constraint-icon">${icon}</span>
                    <span class="constraint-name">${d.name}</span>
                    <span class="constraint-score" style="color:${d.passed ? 'var(--success)' : 'var(--danger)'}">${(d.score * 100).toFixed(0)}%</span>
                    <span class="text-muted text-xs" style="max-width:300px;">${d.detail}</span>
                </div>`;
            });
        } else {
            html += `<div class="text-muted text-sm">No structural constraints detected in prompt.</div>`;
        }
        html += `</div>`;
    });
    document.getElementById('constraint-details-wrap').innerHTML = html;
}

// ── Statistics Table ───────────────────────────────────────────
function renderStatistics(stats) {
    if (!stats || !Object.keys(stats).length) {
        document.getElementById('stats-wrap').innerHTML = '<div class="text-muted text-sm">Need ≥2 models for cross-model statistics.</div>';
        return;
    }

    let html = `<table class="leaderboard-table"><thead><tr>
        <th>Metric</th><th>Mean</th><th>Std Dev</th><th>Min</th><th>Max</th><th>Spread</th>
    </tr></thead><tbody>`;

    Object.entries(stats).forEach(([key, s]) => {
        const label = DISPLAY_METRICS[key]?.label || key;
        const spread = (s.max - s.min).toFixed(4);
        html += `<tr>
            <td style="font-family:Outfit;">${label}</td>
            <td>${s.mean.toFixed(4)}</td>
            <td>${s.std.toFixed(4)}</td>
            <td>${s.min.toFixed(4)}</td>
            <td>${s.max.toFixed(4)}</td>
            <td>${spread}</td>
        </tr>`;
    });

    html += `</tbody></table>`;
    document.getElementById('stats-wrap').innerHTML = html;
}

// ── LLM Judge Results ──────────────────────────────────────────
function renderJudgeResults(data) {
    const container = document.getElementById('judge-results-wrap');
    if (!data.results || !data.results.length) {
        container.innerHTML = '<div class="text-muted">No results.</div>';
        return;
    }

    let html = '<div class="results-grid mt-2">';
    data.results.forEach((r, i) => {
        const j = r.judge;
        if (j.error) {
            html += `<div class="card"><div class="text-danger">${r.model_name}: ${j.error}</div></div>`;
            return;
        }

        const dims = ['faithfulness', 'constraint_following', 'completeness', 'clarity', 'conciseness'];
        html += `<div class="card">
            <div class="card-title" style="color:${MODEL_COLORS[i % MODEL_COLORS.length]}">
                ${r.model_name}
                <span class="tag tag-purple">Avg: ${j.scores.average}/10</span>
            </div>`;

        dims.forEach(d => {
            const score = j.scores[d] || 0;
            const rat = j.rationales[d] || '';
            const barWidth = score * 10;
            html += `<div class="judge-dimension">
                <div>
                    <div class="judge-dim-name">${d.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
                    <div class="judge-rationale">${rat}</div>
                </div>
                <div class="judge-dim-score" style="color:${scoreColor(score, 10)}">${score}/10</div>
            </div>`;
        });

        if (j.overall_comment) {
            html += `<div class="mt-1 text-sm text-muted" style="font-style:italic;">"${j.overall_comment}"</div>`;
        }
        html += `</div>`;
    });
    html += '</div>';
    container.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════
// EXPORT
// ═══════════════════════════════════════════════════════════════

function exportCSV() {
    if (!state.results) { showToast('Run evaluation first', 'error'); return; }
    const results = state.results.results;
    const keys = Object.keys(DISPLAY_METRICS);
    let csv = 'Model,Rank,Composite Score,' + keys.map(k => DISPLAY_METRICS[k].label).join(',') + '\n';
    results.forEach(r => {
        csv += `"${r.model_name}",${r.rank},${r.composite_score},`;
        csv += keys.map(k => r.metrics[k] ?? '').join(',');
        csv += '\n';
    });
    downloadFile(csv, 'evaluation_results.csv', 'text/csv');
}

function exportJSON() {
    if (!state.results) { showToast('Run evaluation first', 'error'); return; }
    const exported = {
        timestamp: new Date().toISOString(),
        results: state.results.results,
        statistics: state.results.statistics,
        judge_results: state.judgeResults?.results || null,
    };
    downloadFile(JSON.stringify(exported, null, 2), 'evaluation_results.json', 'application/json');
}

function downloadFile(content, filename, mime) {
    const blob = new Blob([content], { type: mime });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
}

// ═══════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════

function scoreColor(value, max) {
    const ratio = value / max;
    if (ratio >= 0.75) return '#10b981';
    if (ratio >= 0.5) return '#f59e0b';
    return '#ef4444';
}

function showLoading(msg) {
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        document.body.appendChild(overlay);
    }
    overlay.innerHTML = `<div class="spinner"></div><div class="loading-text">${msg || 'Processing...'}</div>`;
    overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'none';
}

function showToast(msg, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}
