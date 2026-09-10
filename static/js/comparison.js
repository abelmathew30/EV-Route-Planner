/**
 * comparison.js — Algorithm Comparison Page
 * Calls /api/compare and renders results table + Chart.js charts.
 */

'use strict';

let chartNodes = null, chartTime = null, chartDist = null;

async function runComparison() {
  const start = document.getElementById('cmpStart').value;
  const goal = document.getElementById('cmpGoal').value;

  if (!start || !goal) { alert('Please select both start and destination.'); return; }
  if (start === goal) { alert('Start and destination cannot be the same.'); return; }

  const btn = document.getElementById('runCmpBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Running…';
  document.getElementById('cmpLoading').style.display = 'block';
  document.getElementById('cmpResults').style.display = 'none';

  try {
    const results = await apiPost('/api/compare', { start, goal });
    renderComparison(results);
    document.getElementById('cmpResults').style.display = 'block';
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-play-fill me-2"></i> Run Comparison';
    document.getElementById('cmpLoading').style.display = 'none';
  }
}

function renderComparison(results) {
  const order = ['BFS', 'Dijkstra', 'Greedy Best-First', 'A*'];
  const keys = Object.keys(results);

  // ---- Summary cards ----
  const cardsContainer = document.getElementById('algoCards');
  cardsContainer.innerHTML = '';
  const badgeClasses = { BFS: 'badge-bfs', Dijkstra: 'badge-dijkstra', 'Greedy Best-First': 'badge-greedy', 'A*': 'badge-astar' };
  const icons = { BFS: '🔍', Dijkstra: '📐', 'Greedy Best-First': '🎯', 'A*': '⭐' };

  keys.forEach(algo => {
    const r = results[algo];
    const col = document.createElement('div');
    col.className = 'col-md-3';
    col.innerHTML = `
      <div class="card text-center py-3 px-2 ${r.is_optimal ? '' : ''}" style="${r.is_optimal ? 'border-color:rgba(0,212,170,0.4)' : ''}">
        <div style="font-size:1.5rem;margin-bottom:0.3rem">${icons[algo] || '🔧'}</div>
        <div style="font-size:0.85rem;font-weight:700;margin-bottom:0.25rem">${algo}</div>
        <div style="font-size:1.2rem;font-weight:800;color:${r.found ? 'var(--primary)' : '#ff6b6b'}">${r.found ? r.total_distance_km + ' km' : 'No path'}</div>
        <div style="font-size:0.68rem;color:var(--text-muted)">Distance</div>
        ${r.is_optimal ? '<span style="font-size:0.68rem;color:var(--primary);background:rgba(0,212,170,0.1);padding:0.1rem 0.4rem;border-radius:10px;margin-top:0.3rem;display:inline-block">⭐ Optimal</span>' : ''}
      </div>`;
    cardsContainer.appendChild(col);
  });

  // ---- Table ----
  const tbody = document.getElementById('cmpTableBody');
  tbody.innerHTML = '';
  const badgeMap = {
    'BFS': 'badge-bfs', 'Dijkstra': 'badge-dijkstra',
    'Greedy Best-First': 'badge-greedy', 'A*': 'badge-astar'
  };

  keys.forEach(algo => {
    const r = results[algo];
    const tr = document.createElement('tr');
    if (r.is_optimal) tr.className = 'optimal-row';
    tr.innerHTML = `
      <td><span class="algo-badge ${badgeMap[algo] || ''}">${icons[algo] || ''} ${algo}</span></td>
      <td>${r.found ? r.nodes_explored : '—'}</td>
      <td>${r.found ? r.execution_time_ms + ' ms' : '—'}</td>
      <td>${r.found ? r.total_distance_km + ' km' : '<span style="color:#ff6b6b">No path</span>'}</td>
      <td>${r.found ? formatMinutes(r.total_time_min) : '—'}</td>
      <td>${r.is_optimal ? '<span style="color:var(--primary);font-weight:700">✅ Optimal</span>' : (r.found ? '<span style="color:var(--text-muted)">Sub-optimal</span>' : '<span style="color:#ff6b6b">No path</span>')}</td>`;
    tbody.appendChild(tr);
  });

  // ---- Charts ----
  const labels = keys;
  const colors = ['rgba(255,193,7,0.7)', 'rgba(108,99,255,0.7)', 'rgba(255,107,107,0.7)', 'rgba(0,212,170,0.7)'];
  const borderColors = ['#ffc107', '#8c85ff', '#ff6b6b', '#00d4aa'];

  const nodesData = keys.map(k => results[k].found ? results[k].nodes_explored : 0);
  const timeData = keys.map(k => results[k].found ? results[k].execution_time_ms : 0);
  const distData = keys.map(k => results[k].found ? results[k].total_distance_km : 0);

  buildChart('chartNodes', chartNodes, labels, nodesData, colors, borderColors, 'Nodes');
  buildChart('chartTime', chartTime, labels, timeData, colors, borderColors, 'ms');
  buildChart('chartDist', chartDist, labels, distData, colors, borderColors, 'km');

  // ---- Path display ----
  const pathCards = document.getElementById('pathCards');
  pathCards.innerHTML = '';
  keys.forEach((algo, i) => {
    const r = results[algo];
    if (!r.found) return;
    const col = document.createElement('div');
    col.className = 'col-md-6';
    col.innerHTML = `
      <div class="card">
        <div class="card-body">
          <div class="d-flex align-items-center gap-2 mb-2">
            <span class="algo-badge ${badgeMap[algo]}">${icons[algo]} ${algo}</span>
            <span style="font-size:0.75rem;color:var(--text-muted)">${r.path.length} nodes · ${r.total_distance_km} km</span>
          </div>
          <div style="font-size:0.8rem;color:var(--text-secondary);line-height:1.8">
            ${r.path_names.join(' → ')}
          </div>
        </div>
      </div>`;
    pathCards.appendChild(col);
  });

  // ---- Recommendation ----
  const astarResult = results['A*'];
  const recText = astarResult && astarResult.found
    ? `<div><strong>⭐ A* is recommended for EV route planning.</strong><br>
       A* explored only <strong>${astarResult.nodes_explored}</strong> nodes in <strong>${astarResult.execution_time_ms} ms</strong>
       and found the ${astarResult.is_optimal ? 'optimal' : 'a'} route of <strong>${astarResult.total_distance_km} km</strong>.
       It beats Dijkstra in speed while maintaining optimality.</div>`
    : '<div>No optimal algorithm could find a path for this route.</div>';
  document.getElementById('recommendationText').innerHTML = recText;
}

function buildChart(canvasId, chartRef, labels, data, bgColors, borderColors, unit) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  if (chartRef) chartRef.destroy();
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: bgColors,
        borderColor: borderColors,
        borderWidth: 2,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: ctx => `${ctx.raw} ${unit}` }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255,255,255,0.06)' },
          ticks: { color: '#8b95a6' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#8b95a6' }
        }
      }
    }
  });
}

// Auto-run on page load if KCH→TVM selected
document.addEventListener('DOMContentLoaded', () => {
  // Don't auto-run; wait for user click
});
