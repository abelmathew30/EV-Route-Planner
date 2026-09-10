"""
tests/test_ev_astar.py — Unit tests for Battery-Aware A*
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from models.graph import RoadGraph
from models.charging_station import ChargingStationModel
from algorithms.ev_astar import ev_astar


def make_ev_graph() -> RoadGraph:
    """
    Linear graph: A --(40km)--> B --(40km)--> C --(40km)--> D
    Charging station at B.
    """
    g = RoadGraph()
    g.add_node("A", "Start",   10.00, 76.00)
    g.add_node("B", "Middle",  10.00, 76.40)
    g.add_node("C", "Junction",10.00, 76.80)
    g.add_node("D", "End",     10.00, 77.20)
    g.add_edge("A", "B", 40, 80, traffic=1.0)
    g.add_edge("B", "C", 40, 80, traffic=1.0)
    g.add_edge("C", "D", 40, 80, traffic=1.0)
    return g


def make_station_at_b():
    return [ChargingStationModel(
        station_id="S1", name="B Charger", node_id="B",
        lat=10.0, lng=76.4, charger_type="DC Fast",
        charging_power=150, price_per_kwh=15, available=True
    )]


def test_short_journey_no_charge_needed():
    """Battery is ample — should reach B without charging."""
    g = make_ev_graph()
    g2 = RoadGraph()
    g2.add_node("A", "Start", 10.00, 76.00)
    g2.add_node("B", "End",   10.00, 76.40)
    g2.add_edge("A", "B", 40, 80)
    result = ev_astar(
        graph=g2, start="A", goal="B",
        battery_capacity_kwh=60, battery_pct=80,
        efficiency_km_per_kwh=6, max_charge_power_kw=150,
        min_reserve_pct=10, stations=[], mode="balanced"
    )
    assert result["found"] is True
    assert result["total_distance_km"] == 40.0
    assert len(result["charging_stops"]) == 0


def test_long_journey_requires_charging():
    """120 km journey at 6 km/kWh needs 20 kWh; battery at 30% → usable=12 kWh → must charge."""
    g = make_ev_graph()
    result = ev_astar(
        graph=g, start="A", goal="D",
        battery_capacity_kwh=60, battery_pct=30,
        efficiency_km_per_kwh=6, max_charge_power_kw=150,
        min_reserve_pct=10, stations=make_station_at_b(), mode="balanced"
    )
    assert result["found"] is True
    # Should stop to charge (12 kWh usable < 20 kWh needed for 120 km)
    assert len(result["charging_stops"]) >= 1


def test_impossible_journey_no_stations():
    """Very low battery, no stations — should fail."""
    g = make_ev_graph()
    result = ev_astar(
        graph=g, start="A", goal="D",
        battery_capacity_kwh=30, battery_pct=20,
        efficiency_km_per_kwh=6, max_charge_power_kw=150,
        min_reserve_pct=10, stations=[], mode="balanced"
    )
    assert result["found"] is False
    assert result["error"] is not None


def test_station_unavailable():
    """Station exists but is unavailable — algorithm should still fail if battery is insufficient."""
    g = make_ev_graph()
    unavailable_station = [ChargingStationModel(
        station_id="S1", name="B Charger", node_id="B",
        lat=10.0, lng=76.4, charger_type="DC Fast",
        charging_power=150, price_per_kwh=15, available=False  # UNAVAILABLE
    )]
    result = ev_astar(
        graph=g, start="A", goal="D",
        battery_capacity_kwh=30, battery_pct=20,
        efficiency_km_per_kwh=6, max_charge_power_kw=150,
        min_reserve_pct=10, stations=unavailable_station, mode="balanced"
    )
    assert result["found"] is False


def test_dynamic_rerouting():
    """Block node B (with charging station) — force route through alternate path or fail."""
    g = RoadGraph()
    g.add_node("A", "Start",    10.00, 76.00)
    g.add_node("B", "Blocked",  10.00, 76.40)
    g.add_node("C", "Bypass",   10.10, 76.40)
    g.add_node("D", "End",      10.00, 76.80)
    g.add_edge("A", "B", 40, 80)
    g.add_edge("B", "D", 40, 80)
    g.add_edge("A", "C", 42, 75)  # bypass
    g.add_edge("C", "D", 42, 75)

    g.block_node("B")  # simulate B going offline

    result = ev_astar(
        graph=g, start="A", goal="D",
        battery_capacity_kwh=60, battery_pct=80,
        efficiency_km_per_kwh=6, max_charge_power_kw=150,
        min_reserve_pct=10, stations=[], mode="balanced"
    )
    assert result["found"] is True
    assert "B" not in result["path"]


def test_charging_cost_positive():
    g = make_ev_graph()
    result = ev_astar(
        graph=g, start="A", goal="D",
        battery_capacity_kwh=60, battery_pct=40,
        efficiency_km_per_kwh=6, max_charge_power_kw=150,
        min_reserve_pct=10, stations=make_station_at_b(), mode="cheapest"
    )
    if result["found"] and result["charging_stops"]:
        assert result["total_charge_cost_inr"] > 0


def test_battery_below_reserve():
    """Starting battery below min reserve — should error immediately."""
    g = make_ev_graph()
    result = ev_astar(
        graph=g, start="A", goal="D",
        battery_capacity_kwh=60, battery_pct=5,
        efficiency_km_per_kwh=6, max_charge_power_kw=150,
        min_reserve_pct=10, stations=[], mode="balanced"
    )
    assert result["found"] is False


def test_result_has_timeline():
    g = make_ev_graph()
    result = ev_astar(
        graph=g, start="A", goal="D",
        battery_capacity_kwh=60, battery_pct=80,
        efficiency_km_per_kwh=6, max_charge_power_kw=150,
        min_reserve_pct=10, stations=make_station_at_b(), mode="balanced"
    )
    if result["found"]:
        assert isinstance(result["step_timeline"], list)
        assert len(result["step_timeline"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
