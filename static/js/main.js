/**
 * main.js — Global JavaScript Utilities
 * Shared across all pages.
 */

'use strict';

// ---- Chart.js global dark theme defaults ----
if (typeof Chart !== 'undefined') {
  Chart.defaults.color = '#8b95a6';
  Chart.defaults.borderColor = 'rgba(255,255,255,0.08)';
  Chart.defaults.font.family = "'Inter', sans-serif";
}

// ---- Utility: format minutes into "Xh Ym" ----
function formatMinutes(totalMin) {
  if (totalMin === null || totalMin === undefined || isNaN(totalMin)) return '—';
  const h = Math.floor(totalMin / 60);
  const m = Math.round(totalMin % 60);
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

// ---- Utility: show/hide spinner overlay ----
function showLoading(show, elementId) {
  const el = document.getElementById(elementId);
  if (el) el.style.display = show ? 'block' : 'none';
}

// ---- Utility: POST JSON to Flask API ----
async function apiPost(url, payload) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Server error');
  }
  return data;
}

// ---- Utility: GET from Flask API ----
async function apiGet(url) {
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Server error');
  return data;
}

// ---- Battery level colour ----
function batteryColor(pct) {
  if (pct >= 50) return '#00d4aa';
  if (pct >= 25) return '#ffc107';
  return '#ff6b6b';
}

function batteryClass(pct) {
  if (pct >= 50) return 'high';
  if (pct >= 25) return 'medium';
  return 'low';
}

// ---- Leaflet dark tile layer ----
function getDarkTileLayer() {
  return L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
  });
}

// ---- Create a styled Leaflet marker ----
function createMarker(lat, lng, color, symbol, popupHtml) {
  const icon = L.divIcon({
    className: '',
    html: `<div style="
      background:${color};
      width:32px;height:32px;border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);border:2px solid rgba(255,255,255,0.5);
      display:flex;align-items:center;justify-content:center;
      box-shadow:0 4px 12px rgba(0,0,0,0.4)
    ">
      <span style="transform:rotate(45deg);font-size:14px">${symbol}</span>
    </div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -35],
  });
  const marker = L.marker([lat, lng], { icon });
  if (popupHtml) marker.bindPopup(popupHtml);
  return marker;
}

// ---- Navbar active state fix (for client-side nav) ----
document.addEventListener('DOMContentLoaded', () => {
  // Highlight active nav link based on current path
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
});
