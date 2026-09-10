/**
 * results.js — Route Results Page
 * Reads route data from sessionStorage and renders:
 *   - Summary metric cards
 *   - Leaflet map with route + markers
 *   - Route path breadcrumb
 *   - Journey timeline
 */

'use strict';

let resultsMap = null;

document.addEventListener('DOMContentLoaded', () => {
  const raw = sessionStorage.getItem('routeResult');

  if (!raw) {
    document.getElementById('noDataState').style.display = 'block';
    return;
  }

  let result;
  try { result = JSON.parse(raw); }
  catch { document.getElementById('noDataState').style.display = 'block'; return; }

  if (!result.found) {
    document.getElementById('resultsError').style.display = 'flex';
    document.getElementById('errorMsg').textContent = result.error || 'Route not found.';
    return;
  }

  renderResults(result);
});

function renderResults(r) {
  document.getElementById('noDataState').style.display = 'none';
  document.getElementById('resultsContent').style.display = 'block';

  // ---- Summary cards ----
  setValue('res_distance', r.total_distance_km + ' km');
  setValue('res_travelTime', formatMinutes(r.total_travel_time_min));
  setValue('res_chargeTime', formatMinutes(r.total_charge_time_min));
  setValue('res_totalTime', formatMinutes(r.total_journey_time_min));
  setValue('res_energy', (r.total_energy_kwh || 0).toFixed(1));
  setValue('res_chargeCost', '₹' + (r.total_charge_cost_inr || 0).toFixed(0));
  setValue('res_stops', (r.charging_stops || []).length);
  setValue('res_finalBattery', (r.final_battery_pct || 0) + '%');

  // ---- Route path breadcrumb ----
  renderRoutePath(r.path_names || []);

  // ---- Journey timeline ----
  renderTimeline(r.step_timeline || [], r.path_names || []);

  // ---- Leaflet map ----
  renderMap(r);
}

function setValue(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ---- Route path breadcrumb ----
function renderRoutePath(names) {
  const container = document.getElementById('routePathDisplay');
  container.innerHTML = '';
  names.forEach((name, i) => {
    const chip = document.createElement('div');
    chip.style.cssText = 'background:rgba(0,212,170,0.1);border:1px solid rgba(0,212,170,0.2);border-radius:20px;padding:0.3rem 0.75rem;font-size:0.8rem;font-weight:600;color:var(--primary)';
    chip.textContent = name;
    container.appendChild(chip);
    if (i < names.length - 1) {
      const arrow = document.createElement('span');
      arrow.textContent = '→';
      arrow.style.cssText = 'color:var(--text-muted);font-size:0.85rem;padding:0 0.1rem';
      container.appendChild(arrow);
    }
  });
}

// ---- Journey timeline ----
function renderTimeline(steps, pathNames) {
  const container = document.getElementById('journeyTimeline');
  container.innerHTML = '';

  if (!steps.length) {
    // Simple path timeline
    pathNames.forEach((name, i) => {
      const item = document.createElement('div');
      item.className = 'timeline-item drive-step';
      item.innerHTML = `
        <div class="timeline-content">
          <span class="timeline-badge ${i === 0 ? 'badge-start' : i === pathNames.length - 1 ? 'badge-end' : 'badge-drive'}">
            ${i === 0 ? 'Start' : i === pathNames.length - 1 ? 'Destination' : 'Drive'}
          </span>
          <div class="fw-bold" style="font-size:0.9rem">${name}</div>
        </div>`;
      container.appendChild(item);
    });
    return;
  }

  steps.forEach((step, idx) => {
    const item = document.createElement('div');
    const isCharge = step.type === 'charge';
    item.className = `timeline-item ${isCharge ? 'charge-stop' : 'drive-step'}`;
    item.style.animationDelay = `${idx * 0.05}s`;

    const badge = isCharge ? 'badge-charge' : 'badge-drive';
    const label = isCharge ? '⚡ Charge' : '🚗 Drive';

    let details = '';
    if (isCharge) {
      details = `
        <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:0.35rem">${step.description}</div>
        <div class="d-flex gap-2 mt-1 flex-wrap">
          <span style="font-size:0.72rem;background:rgba(0,212,170,0.1);color:var(--primary);border-radius:20px;padding:0.15rem 0.5rem">+${step.energy_added_kwh} kWh</span>
          <span style="font-size:0.72rem;background:rgba(255,193,7,0.1);color:#ffc107;border-radius:20px;padding:0.15rem 0.5rem">${step.charge_time_min} min</span>
          <span style="font-size:0.72rem;background:rgba(108,99,255,0.1);color:#8c85ff;border-radius:20px;padding:0.15rem 0.5rem">₹${step.charge_cost_inr}</span>
        </div>`;
    } else {
      details = `
        <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:0.35rem">${step.description}</div>
        <div class="d-flex gap-2 mt-1 flex-wrap">
          <span style="font-size:0.72rem;background:rgba(108,99,255,0.1);color:#8c85ff;border-radius:20px;padding:0.15rem 0.5rem">${step.distance_km} km</span>
          <span style="font-size:0.72rem;background:rgba(0,0,0,0.2);color:var(--text-secondary);border-radius:20px;padding:0.15rem 0.5rem">${step.travel_time_min} min</span>
          <span style="font-size:0.72rem;background:rgba(255,107,107,0.1);color:#ff8080;border-radius:20px;padding:0.15rem 0.5rem">${step.energy_kwh} kWh</span>
          <span style="font-size:0.72rem;background:rgba(0,212,170,0.08);color:var(--primary);border-radius:20px;padding:0.15rem 0.5rem">🔋${step.battery_after_pct}%</span>
        </div>`;
    }

    item.innerHTML = `
      <div class="timeline-content">
        <span class="timeline-badge ${badge}">${label}</span>
        ${details}
      </div>`;
    container.appendChild(item);
  });
}

// ---- Leaflet map ----
function renderMap(r) {
  if (resultsMap) {
    resultsMap.remove();
    resultsMap = null;
  }

  resultsMap = L.map('results-map', { zoomControl: true });
  getDarkTileLayer().addTo(resultsMap);

  const nodeCoords = r.node_coords || {};
  const stationCoords = r.station_coords || {};
  const path = r.path || [];
  const chargeNodeIds = new Set((r.charging_stops || []).map(s => s.node_id));

  const latlngs = [];
  path.forEach((nodeId, idx) => {
    const coord = nodeCoords[nodeId];
    if (!coord) return;
    latlngs.push([coord.lat, coord.lng]);

    let color = '#6c63ff';
    let symbol = '📍';
    let popupContent = `<strong>${coord.name}</strong>`;

    if (idx === 0) {
      color = '#28a745'; symbol = '🚗';
      popupContent += '<br><em>Start</em>';
    } else if (idx === path.length - 1) {
      color = '#ff6b6b'; symbol = '🏁';
      popupContent += '<br><em>Destination</em>';
    } else if (chargeNodeIds.has(nodeId)) {
      const s = stationCoords[nodeId];
      color = '#00d4aa'; symbol = '⚡';
      if (s) popupContent += `<br>⚡ ${s.name}<br>${s.type} · ${s.power} kW · ₹${s.price}/kWh`;
      else popupContent += '<br><em>Charging Stop</em>';
    }

    createMarker(coord.lat, coord.lng, color, symbol, popupContent).addTo(resultsMap);
  });

  // Draw route polyline
  if (latlngs.length >= 2) {
    L.polyline(latlngs, {
      color: '#00d4aa',
      weight: 4,
      opacity: 0.85,
      dashArray: null,
      lineJoin: 'round',
    }).addTo(resultsMap);
    resultsMap.fitBounds(L.latLngBounds(latlngs), { padding: [40, 40] });
  } else if (latlngs.length === 1) {
    resultsMap.setView(latlngs[0], 10);
  } else {
    resultsMap.setView([10.0, 76.5], 7);
  }
}
