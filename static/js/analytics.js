/**
 * analytics.js — Analytics Page
 * Weight distribution radar chart + live mode comparison runner.
 */

'use strict';

const MODE_COLORS = {
  fastest: '#00d4aa',
  cheapest: '#ffc107',
  eco: '#4caf70',
  balanced: '#8c85ff'
};
const MODE_LABELS = { fastest: '⚡ Fastest', cheapest: '💰 Cheapest', eco: '🌿 Eco', balanced: '⚖️ Balanced' };

// ---- Weight radar chart (static) ----
document.addEventListener('DOMContentLoaded', () => {
  renderWeightChart();
});

function renderWeightChart() {
  const ctx = document.getElementById('chartWeights');
  if (!ctx) return;

  new Chart(ctx.getContext('2d'), {
    type: 'radar',
    data: {
      labels: ['Travel Time (α)', 'Charge Time (β)', 'Charge Cost (γ)', 'Energy (δ)'],
      datasets: [
        { label: '⚡ Fastest',  data: [0.7, 0.3, 0.0, 0.0], borderColor: '#00d4aa', backgroundColor: 'rgba(0,212,170,0.1)', borderWidth: 2, pointBackgroundColor: '#00d4aa' },
        { label: '💰 Cheapest', data: [0.1, 0.1, 0.8, 0.0], borderColor: '#ffc107', backgroundColor: 'rgba(255,193,7,0.1)', borderWidth: 2, pointBackgroundColor: '#ffc107' },
        { label: '🌿 Eco',      data: [0.1, 0.0, 0.0, 0.9], borderColor: '#4caf70', backgroundColor: 'rgba(76,175,80,0.1)', borderWidth: 2, pointBackgroundColor: '#4caf70' },
        { label: '⚖️ Balanced', data: [0.4, 0.2, 0.2, 0.2], borderColor: '#8c85ff', backgroundColor: 'rgba(140,133,255,0.1)', borderWidth: 2, pointBackgroundColor: '#8c85ff' },
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: '#8b95a6', font: { size: 11 } } }
      },
      scales: {
        r: {
          min: 0, max: 1,
          ticks: { stepSize: 0.2, color: '#55626e', backdropColor: 'transparent' },
          grid: { color: 'rgba(255,255,255,0.08)' },
          angleLines: { color: 'rgba(255,255,255,0.08)' },
          pointLabels: { color: '#8b95a6', font: { size: 11 } }
        }
      }
    }
  });
}

// ---- Live mode comparison ----
const modeCharts = {};

async function runAnalytics() {
  const start = document.getElementById('analStart').value;
  const goal = document.getElementById('analGoal').value;
  const battPct = parseFloat(document.getElementById('analBattery').value) || 80;

  if (start === goal) { alert('Start and destination must differ.'); return; }

  const btn = document.getElementById('analRunBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Running…';
  document.getElementById('analLoading').style.display = 'block';
  document.getElementById('analCharts').style.display = 'none';

  const modes = ['fastest', 'cheapest', 'eco', 'balanced'];
  const results = {};

  try {
    // Run all 4 modes in parallel
    const promises = modes.map(mode =>
      apiPost('/api/route', {
        start, goal,
        battery_capacity: 60,
        battery_pct: battPct,
        efficiency: 6.0,
        max_charge_power: 150,
        min_reserve: 10,
        mode
      }).catch(e => ({ found: false, error: e.message, mode }))
    );
    const allResults = await Promise.all(promises);
    modes.forEach((mode, i) => { results[mode] = allResults[i]; });

    renderAnalyticsCharts(results);
    document.getElementById('analCharts').style.display = 'block';
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-bar-chart-fill me-2"></i> Compare Modes';
    document.getElementById('analLoading').style.display = 'none';
  }
}

function renderAnalyticsCharts(results) {
  const modes = ['fastest', 'cheapest', 'eco', 'balanced'];
  const labels = modes.map(m => MODE_LABELS[m]);
  const colors = modes.map(m => MODE_COLORS[m]);
  const alphas = modes.map(m => MODE_COLORS[m].replace(')', ',0.6)').replace('rgb', 'rgba').replace('#', 'rgba(').split('rgba(')[1]);

  const getVal = (mode, key, fallback = 0) => {
    const r = results[mode];
    return (r && r.found) ? (r[key] || fallback) : fallback;
  };

  const journeyTimes = modes.map(m => getVal(m, 'total_journey_time_min'));
  const costs = modes.map(m => getVal(m, 'total_charge_cost_inr'));
  const energies = modes.map(m => getVal(m, 'total_energy_kwh'));
  const stops = modes.map(m => getVal(m, 'charging_stops', []).length || 0);

  function buildBar(id, key, dataArr, unit) {
    const ctx = document.getElementById(id);
    if (!ctx) return;
    if (modeCharts[id]) modeCharts[id].destroy();
    modeCharts[id] = new Chart(ctx.getContext('2d'), {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          data: dataArr,
          backgroundColor: colors.map(c => c + '99'),
          borderColor: colors,
          borderWidth: 2,
          borderRadius: 8,
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => `${ctx.raw} ${unit}` } }
        },
        scales: {
          y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#8b95a6' } },
          x: { grid: { display: false }, ticks: { color: '#8b95a6' } }
        }
      }
    });
  }

  buildBar('chartJourneyTime', 'total_journey_time_min', journeyTimes, 'min');
  buildBar('chartCost', 'total_charge_cost_inr', costs, '₹');
  buildBar('chartEnergy', 'total_energy_kwh', energies, 'kWh');
  buildBar('chartStops', 'stops', stops, 'stops');

  // Render table
  const tbody = document.getElementById('analTableBody');
  tbody.innerHTML = '';
  modes.forEach(mode => {
    const r = results[mode];
    const found = r && r.found;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="color:${MODE_COLORS[mode]};font-weight:700">${MODE_LABELS[mode]}</td>
      <td>${found ? formatMinutes(r.total_journey_time_min) : '—'}</td>
      <td>${found ? formatMinutes(r.total_travel_time_min) : '—'}</td>
      <td>${found ? formatMinutes(r.total_charge_time_min) : '—'}</td>
      <td>${found ? (r.total_energy_kwh || 0).toFixed(1) : '—'}</td>
      <td>${found ? '₹' + (r.total_charge_cost_inr || 0).toFixed(0) : '—'}</td>
      <td>${found ? (r.charging_stops || []).length : '—'}</td>
      <td>${found ? r.total_distance_km + ' km' : '—'}</td>`;
    tbody.appendChild(tr);
  });
}
