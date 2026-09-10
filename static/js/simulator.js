/**
 * simulator.js — EV Simulator Page
 * Handles battery visualisation, journey simulation, and charging estimator.
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
  setupSliders();
  updateBatteryDisplay();
});

function setupSliders() {
  const simBattery = document.getElementById('simBattery');
  const simReserve = document.getElementById('simReserve');
  const simCapacity = document.getElementById('simCapacity');
  const simEfficiency = document.getElementById('simEfficiency');

  [simBattery, simReserve, simCapacity, simEfficiency].forEach(el => {
    if (el) el.addEventListener('input', updateBatteryDisplay);
  });
}

function updateBatteryDisplay() {
  const pct = parseInt(document.getElementById('simBattery').value) || 0;
  const capacity = parseFloat(document.getElementById('simCapacity').value) || 60;
  const efficiency = parseFloat(document.getElementById('simEfficiency').value) || 6;
  const reserve = parseInt(document.getElementById('simReserve').value) || 10;

  document.getElementById('simBattLabel').textContent = pct + '%';
  document.getElementById('simReserveLabel').textContent = reserve + '%';

  const currentEnergy = capacity * (pct / 100);
  const reserveEnergy = capacity * (reserve / 100);
  const usableEnergy = Math.max(0, currentEnergy - reserveEnergy);
  const range = usableEnergy * efficiency;

  // Battery bar
  const fill = document.getElementById('simBatteryFill');
  const text = document.getElementById('simBatteryText');
  fill.style.width = pct + '%';
  fill.className = 'battery-fill ' + batteryClass(pct);
  text.textContent = pct + '%';

  // Display values
  document.getElementById('dispCurrentEnergy').textContent = currentEnergy.toFixed(1) + ' kWh';
  document.getElementById('dispUsableEnergy').textContent = usableEnergy.toFixed(1) + ' kWh';
  document.getElementById('dispRange').textContent = Math.round(range) + ' km';

  // Color the values
  document.getElementById('dispCurrentEnergy').style.color = '#00d4aa';
  document.getElementById('dispRange').style.color = batteryColor(pct);
}

async function runSimulation() {
  const btn = document.getElementById('simBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Simulating…';

  const payload = {
    battery_capacity: parseFloat(document.getElementById('simCapacity').value),
    battery_pct: parseInt(document.getElementById('simBattery').value),
    efficiency: parseFloat(document.getElementById('simEfficiency').value),
    max_charge_power: parseFloat(document.getElementById('simMaxPower').value),
    min_reserve: parseInt(document.getElementById('simReserve').value),
    distance_km: parseFloat(document.getElementById('simDistance').value),
  };

  try {
    const result = await apiPost('/api/simulate', payload);
    renderSimResult(result, payload.battery_pct);
  } catch (err) {
    const statusEl = document.getElementById('simStatus');
    statusEl.className = 'status-strip status-error mb-4';
    statusEl.innerHTML = `<i class="bi bi-exclamation-triangle-fill fs-5"></i> <div>${err.message}</div>`;
    document.getElementById('simResult').style.display = 'block';
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-play-circle-fill me-2"></i> Run Simulation';
  }
}

function renderSimResult(result, startPct) {
  document.getElementById('simResult').style.display = 'block';

  const possible = result.possible;
  const statusEl = document.getElementById('simStatus');
  const statusIcon = possible ? '✅' : '🔴';
  const statusClass = possible ? 'status-success' : 'status-error';
  const statusText = result.status || (possible ? 'Journey possible' : 'Charging required');

  statusEl.className = `status-strip ${statusClass} mb-4`;
  statusEl.innerHTML = `
    <span style="font-size:1.5rem">${statusIcon}</span>
    <div>
      <strong>${statusText}</strong>
      <div style="font-size:0.82rem;opacity:0.8">
        Distance: ${result.distance_km} km · Energy needed: ${result.energy_required_kwh} kWh
      </div>
    </div>`;

  document.getElementById('resEnergyReq').textContent = result.energy_required_kwh + ' kWh';
  document.getElementById('resEnergyReq').style.color = possible ? '#00d4aa' : '#ff6b6b';

  if (possible && result.remaining_battery_pct !== null) {
    document.getElementById('resRemaining').textContent = result.remaining_battery_pct + '%';
    document.getElementById('resRemaining').style.color = batteryColor(result.remaining_battery_pct);
  } else {
    document.getElementById('resRemaining').textContent = 'N/A';
    document.getElementById('resRemaining').style.color = '#ff6b6b';
  }

  const kwPer100 = result.distance_km > 0
    ? ((result.energy_required_kwh / result.distance_km) * 100).toFixed(1)
    : '—';
  document.getElementById('resConsumption').textContent = kwPer100;

  // After-journey battery bar
  const afterBar = document.getElementById('afterBatteryBar');
  const afterLabel = document.getElementById('afterBatteryLabel');
  const afterPct = possible && result.remaining_battery_pct !== null ? result.remaining_battery_pct : 0;
  afterBar.style.width = afterPct + '%';
  afterBar.style.background = batteryColor(afterPct);
  afterLabel.textContent = possible ? afterPct + '%' : 'Insufficient battery';
}

function calcCharge() {
  const currentPct = parseInt(document.getElementById('simBattery').value) || 0;
  const targetPct = parseInt(document.getElementById('chargeTarget').value) || 80;
  const capacity = parseFloat(document.getElementById('simCapacity').value) || 60;
  const evMaxPower = parseFloat(document.getElementById('simMaxPower').value) || 150;
  const stationPower = parseFloat(document.getElementById('stationPower').value) || 150;
  const pricePerKwh = 16; // default

  if (targetPct <= currentPct) {
    showChargeResult('warning', 'Target battery must be higher than current battery.', '');
    return;
  }

  const energyToAdd = capacity * ((targetPct - currentPct) / 100);
  const effectivePower = Math.min(evMaxPower, stationPower);
  const timeHours = energyToAdd / effectivePower;
  const timeMinutes = timeHours * 60;
  const cost = energyToAdd * pricePerKwh;

  showChargeResult('info',
    `Charge from <strong>${currentPct}%</strong> → <strong>${targetPct}%</strong>`,
    `⚡ +${energyToAdd.toFixed(1)} kWh · ⏱ ${Math.round(timeMinutes)} min · 💰 ₹${cost.toFixed(0)} (at ₹${pricePerKwh}/kWh)`
  );
}

function showChargeResult(type, main, detail) {
  const el = document.getElementById('chargeResult');
  const classMap = { info: 'status-info', warning: 'status-warning', success: 'status-success' };
  el.className = `status-strip ${classMap[type] || 'status-info'} mt-3`;
  el.innerHTML = `<i class="bi bi-lightning-charge-fill fs-5"></i><div><div>${main}</div><div style="font-size:0.82rem;opacity:0.8;margin-top:0.2rem">${detail}</div></div>`;
  el.style.display = 'flex';
}
