/**
 * planner.js — Route Planner Page
 * Handles form interaction, live EV summary, and routing API call.
 */

'use strict';

// ---- Live EV summary update ----
function updateEVSummary() {
  const capacity = parseFloat(document.getElementById('batteryCapacity').value) || 60;
  const pct = parseInt(document.getElementById('batteryPct').value) || 75;
  const efficiency = parseFloat(document.getElementById('efficiency').value) || 6.0;
  const reserve = parseInt(document.getElementById('minReserve').value) || 10;

  document.getElementById('batteryPctDisplay').textContent = pct + '%';
  document.getElementById('reserveDisplay').textContent = reserve + '%';

  const currentEnergy = capacity * (pct / 100);
  const reserveEnergy = capacity * (reserve / 100);
  const usableEnergy = Math.max(0, currentEnergy - reserveEnergy);
  const range = usableEnergy * efficiency;

  document.getElementById('summaryRange').textContent = Math.round(range);
  document.getElementById('summaryEnergy').textContent = usableEnergy.toFixed(1);
  document.getElementById('summaryBattery').textContent = pct + '%';

  // Battery bar
  const bar = document.getElementById('batteryBar');
  bar.style.width = pct + '%';
  bar.style.background = pct >= 50
    ? 'linear-gradient(90deg,#00d4aa,#00f0c0)'
    : pct >= 25
    ? 'linear-gradient(90deg,#ffc107,#ff9800)'
    : 'linear-gradient(90deg,#ff6b6b,#ff3b3b)';
}

// ---- Show algorithm info card ----
function showAlgoInfo(key) {
  document.querySelectorAll('.algo-info-card').forEach(el => el.style.display = 'none');
  const card = document.getElementById('info_' + key);
  if (card) card.style.display = 'block';

  // Update hint text
  const hints = {
    astar: 'A* is optimal and efficient — best for EV routing.',
    dijkstra: 'Dijkstra guarantees the shortest distance but explores more nodes than A*.',
    greedy: 'Greedy is very fast but may not return the shortest path.',
    bfs: 'BFS ignores edge weights. Included for educational comparison only.'
  };
  document.getElementById('algoHint').textContent = hints[key] || '';
}

// ---- Form submission → call API → store result → navigate ----
document.getElementById('routeForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const errorDiv = document.getElementById('formError');
  const errorMsg = document.getElementById('formErrorMsg');
  errorDiv.classList.add('d-none');

  const start = document.getElementById('startNode').value;
  const goal = document.getElementById('goalNode').value;

  if (!start) { showError('Please select a start location.'); return; }
  if (!goal) { showError('Please select a destination.'); return; }
  if (start === goal) { showError('Start and destination cannot be the same city.'); return; }

  const payload = {
    start,
    goal,
    battery_capacity: parseFloat(document.getElementById('batteryCapacity').value),
    battery_pct: parseInt(document.getElementById('batteryPct').value),
    efficiency: parseFloat(document.getElementById('efficiency').value),
    max_charge_power: parseFloat(document.getElementById('maxChargePower').value),
    min_reserve: parseInt(document.getElementById('minReserve').value),
    mode: document.querySelector('input[name="mode"]:checked').value,
  };

  const btn = document.getElementById('findRouteBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Calculating…';

  try {
    const result = await apiPost('/api/route', payload);
    // Store result in sessionStorage to pass to results page
    sessionStorage.setItem('routeResult', JSON.stringify(result));
    window.location.href = '/results';
  } catch (err) {
    showError(err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-search me-2"></i> Find Optimal Route';
  }

  function showError(msg) {
    errorMsg.textContent = msg;
    errorDiv.classList.remove('d-none');
  }
});

// ---- Radio buttons for mode selection ----
document.querySelectorAll('input[name="mode"]').forEach(radio => {
  radio.addEventListener('change', () => {
    document.querySelectorAll('label[for^="mode_"]').forEach(lbl => {
      lbl.style.borderColor = 'var(--border)';
      lbl.style.color = 'var(--text-secondary)';
      lbl.style.background = 'var(--bg-input)';
    });
    const label = document.querySelector(`label[for="mode_${radio.value}"]`);
    if (label) {
      label.style.borderColor = 'var(--primary)';
      label.style.color = 'var(--primary)';
      label.style.background = 'rgba(0,212,170,0.08)';
    }
  });
});

// ---- Algorithm select → show info ----
document.getElementById('algorithm').addEventListener('change', function () {
  showAlgoInfo(this.value);
});

// ---- Slider inputs ----
['batteryPct', 'minReserve', 'batteryCapacity', 'efficiency'].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener('input', updateEVSummary);
});

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => {
  updateEVSummary();
  showAlgoInfo('astar');
  // Highlight default mode
  const defaultLabel = document.querySelector('label[for="mode_balanced"]');
  if (defaultLabel) {
    defaultLabel.style.borderColor = 'var(--primary)';
    defaultLabel.style.color = 'var(--primary)';
    defaultLabel.style.background = 'rgba(0,212,170,0.08)';
  }
});
