"""
tests/test_battery.py — Unit tests for the EV model
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from models.ev import EV


def test_current_energy():
    ev = EV(battery_capacity=60, battery_percentage=80)
    assert abs(ev.get_current_energy() - 48.0) < 1e-9


def test_usable_energy():
    ev = EV(battery_capacity=60, battery_percentage=80, min_reserve=10)
    # usable = 48 - 6 = 42 kWh
    assert abs(ev.get_usable_energy() - 42.0) < 1e-9


def test_remaining_range():
    ev = EV(battery_capacity=60, battery_percentage=80, efficiency=6.0, min_reserve=10)
    # range = 42 kWh × 6 km/kWh = 252 km
    assert abs(ev.get_remaining_range() - 252.0) < 1e-9


def test_energy_required():
    ev = EV(efficiency=5.0)
    assert abs(ev.energy_required(100) - 20.0) < 1e-9


def test_can_travel_yes():
    ev = EV(battery_capacity=60, battery_percentage=80, efficiency=6.0, min_reserve=10)
    # usable = 42 kWh, can cover 100 km (= 16.7 kWh)
    assert ev.can_travel(100) is True


def test_can_travel_no():
    ev = EV(battery_capacity=60, battery_percentage=20, efficiency=6.0, min_reserve=10)
    # usable = 60*(20-10)/100 = 6 kWh → range = 36 km
    assert ev.can_travel(100) is False


def test_simulate_drive_possible():
    ev = EV(battery_capacity=60, battery_percentage=80, efficiency=6.0, min_reserve=10)
    result = ev.simulate_drive(100)
    assert result["possible"] is True
    assert result["status"] == "Journey possible"


def test_simulate_drive_impossible():
    ev = EV(battery_capacity=60, battery_percentage=15, efficiency=6.0, min_reserve=10)
    result = ev.simulate_drive(200)
    assert result["possible"] is False
    assert result["status"] == "Charging required"


def test_charge():
    ev = EV(battery_capacity=60, battery_percentage=40, max_charging_power=150)
    result = ev.charge(target_percentage=80, station_power_kw=150)
    assert abs(result["energy_added_kwh"] - 24.0) < 1e-6
    assert ev.battery_percentage == 80.0


def test_charge_limited_by_ev_power():
    ev = EV(battery_capacity=60, battery_percentage=40, max_charging_power=50)
    # Effective power = min(50, 150) = 50 kW
    result = ev.charge(target_percentage=80, station_power_kw=150)
    expected_time_h = 24.0 / 50
    assert abs(result["charge_time_hours"] - expected_time_h) < 1e-6


def test_validation_negative_capacity():
    with pytest.raises(ValueError):
        EV(battery_capacity=-10)


def test_validation_battery_pct_over_100():
    with pytest.raises(ValueError):
        EV(battery_percentage=110)


def test_validation_negative_efficiency():
    with pytest.raises(ValueError):
        EV(efficiency=-1)


def test_to_dict():
    ev = EV(battery_capacity=60, battery_percentage=75)
    d = ev.to_dict()
    assert d["battery_capacity"] == 60
    assert d["battery_percentage"] == 75.0
    assert "remaining_range_km" in d


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
