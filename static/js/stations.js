/**
 * stations.js — Charging Stations Page
 * Renders Leaflet map and handles search/filter on station cards.
 */

'use strict';

let stationsMap = null;

document.addEventListener('DOMContentLoaded', () => {
  initMap();
  setupFilters();
});

// ---- Leaflet Map ----
function initMap() {
  stationsMap = L.map('stations-map');
  getDarkTileLayer().addTo(stationsMap);

  // Read stations from embedded JSON script tag
  const raw = document.getElementById('stationsData');
  if (!raw) return;

  let stations;
  try { stations = JSON.parse(raw.textContent); }
  catch { return; }

  const bounds = [];

  stations.forEach(s => {
    const color = s.available
      ? (s.charger_type.includes('DC') ? '#00d4aa' : '#8c85ff')
      : '#ff6b6b';
    const symbol = s.charger_type.includes('DC') ? '⚡' : '🔌';

    const popup = `
      <div style="min-width:180px">
        <strong style="color:${color}">${s.name}</strong><br>
        <span style="font-size:0.75rem;opacity:0.7">${s.charger_type} · ${s.charging_power} kW</span><br>
        <div style="margin-top:0.5rem;font-size:0.8rem">
          💰 ₹${s.price_per_kwh}/kWh<br>
          🔌 ${s.num_chargers} charger${s.num_chargers > 1 ? 's' : ''}<br>
          ${s.available ? '🟢 Available' : '🔴 Unavailable'}
        </div>
      </div>`;

    const marker = createMarker(s.lat, s.lng, color, symbol, popup);
    marker.addTo(stationsMap);
    bounds.push([s.lat, s.lng]);
  });

  if (bounds.length) {
    stationsMap.fitBounds(L.latLngBounds(bounds), { padding: [30, 30] });
  } else {
    stationsMap.setView([10.0, 76.5], 7);
  }
}

// ---- Filters ----
function setupFilters() {
  ['stationSearch', 'filterType', 'filterAvail', 'filterPrice'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', applyFilters);
  });
}

function applyFilters() {
  const search = document.getElementById('stationSearch').value.toLowerCase();
  const type = document.getElementById('filterType').value;
  const avail = document.getElementById('filterAvail').value;
  const maxPrice = parseFloat(document.getElementById('filterPrice').value) || Infinity;

  const items = document.querySelectorAll('.station-item');
  let visible = 0;

  items.forEach(item => {
    const name = item.dataset.name || '';
    const city = item.dataset.city || '';
    const itemType = item.dataset.type || '';
    const itemAvail = item.dataset.avail || '';
    const price = parseFloat(item.dataset.price) || 0;

    const matchSearch = !search || name.includes(search) || city.includes(search);
    const matchType = !type || itemType === type;
    const matchAvail = !avail || itemAvail === avail;
    const matchPrice = price <= maxPrice;

    const show = matchSearch && matchType && matchAvail && matchPrice;
    item.style.display = show ? '' : 'none';
    if (show) visible++;
  });

  const count = document.getElementById('stationCount');
  if (count) count.innerHTML = `Showing <strong style="color:var(--text-primary)">${visible}</strong> stations`;

  const noMsg = document.getElementById('noStationsMsg');
  if (noMsg) noMsg.style.display = visible === 0 ? 'block' : 'none';
}

function clearFilters() {
  document.getElementById('stationSearch').value = '';
  document.getElementById('filterType').value = '';
  document.getElementById('filterAvail').value = '';
  document.getElementById('filterPrice').value = '';
  applyFilters();
}
