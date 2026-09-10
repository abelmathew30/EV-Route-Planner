"""
tests/test_graph.py — Unit tests for the RoadGraph model
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import math
import pytest
from models.graph import RoadGraph


def make_simple_graph() -> RoadGraph:
    """Create a small test graph:
        A --(10km, 60km/h)--> B --(20km, 80km/h)--> C
        A --(25km, 50km/h)--> C  (direct, longer)
    """
    g = RoadGraph()
    g.add_node("A", "Alpha", lat=10.0, lng=76.0)
    g.add_node("B", "Beta",  lat=10.1, lng=76.2)
    g.add_node("C", "Gamma", lat=10.2, lng=76.4)
    g.add_edge("A", "B", distance=10, speed=60, traffic=1.0)
    g.add_edge("B", "C", distance=20, speed=80, traffic=1.0)
    g.add_edge("A", "C", distance=25, speed=50, traffic=1.0)
    return g


def test_add_nodes():
    g = make_simple_graph()
    assert g.node_exists("A")
    assert g.node_exists("B")
    assert g.node_exists("C")
    assert not g.node_exists("D")


def test_add_edges():
    g = make_simple_graph()
    assert "B" in g.adjacency["A"]
    assert "C" in g.adjacency["B"]
    assert g.adjacency["A"]["B"]["distance"] == 10


def test_get_neighbours():
    g = make_simple_graph()
    nbrs = g.get_neighbours("A")
    assert "B" in nbrs
    assert "C" in nbrs
    assert "A" not in nbrs


def test_travel_time():
    g = make_simple_graph()
    # A→B: 10km / (60km/h / 1.0) = 0.1667h
    t = g.travel_time_hours("A", "B")
    assert abs(t - 10/60) < 1e-9


def test_energy_consumed():
    g = make_simple_graph()
    # A→B: 10km / 5km/kWh = 2 kWh
    e = g.energy_consumed_kwh("A", "B", efficiency_km_per_kwh=5.0)
    assert abs(e - 2.0) < 1e-9


def test_haversine_distance():
    g = make_simple_graph()
    dist = g.haversine_distance_km("A", "C")
    assert dist > 0
    # A and C are close: roughly sqrt((0.2*111)^2 + (0.4*95)^2) ≈ 43 km
    assert dist < 100  # reasonable upper bound for this test graph


def test_block_and_unblock_edge():
    g = make_simple_graph()
    g.block_edge("A", "B")
    nbrs = g.get_neighbours("A", skip_blocked=True)
    assert "B" not in nbrs
    assert "C" in nbrs

    g.unblock_edge("A", "B")
    nbrs = g.get_neighbours("A", skip_blocked=True)
    assert "B" in nbrs


def test_block_node():
    g = make_simple_graph()
    g.block_node("B")
    # A's neighbours: B should be blocked
    nbrs_a = g.get_neighbours("A", skip_blocked=True)
    assert "B" not in nbrs_a


def test_all_node_ids():
    g = make_simple_graph()
    ids = g.all_node_ids()
    assert set(ids) == {"A", "B", "C"}


def test_to_dict():
    g = make_simple_graph()
    d = g.to_dict()
    assert "nodes" in d
    assert "edges" in d
    assert len(d["nodes"]) == 3
    assert len(d["edges"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
