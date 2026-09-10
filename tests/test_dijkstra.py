"""
tests/test_dijkstra.py — Unit tests for Dijkstra's algorithm
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from models.graph import RoadGraph
from algorithms.dijkstra import dijkstra


def make_graph() -> RoadGraph:
    g = RoadGraph()
    g.add_node("A", "Alpha", 10.0, 76.0)
    g.add_node("B", "Beta",  10.1, 76.2)
    g.add_node("C", "Gamma", 10.2, 76.4)
    g.add_node("D", "Delta", 10.3, 76.6)
    # A→B (10km), B→C (20km), A→C (25km), C→D (15km)
    g.add_edge("A", "B", 10, 60)
    g.add_edge("B", "C", 20, 60)
    g.add_edge("A", "C", 25, 60)  # direct but longer
    g.add_edge("C", "D", 15, 60)
    return g


def test_shortest_path():
    g = make_graph()
    result = dijkstra(g, "A", "D")
    assert result["found"] is True
    # Optimal: A→C→D = 25+15 = 40km (shorter than A→B→C→D = 45km)
    assert result["total_distance_km"] == 40.0
    assert result["path"] == ["A", "C", "D"]


def test_direct_shorter():
    g = make_graph()
    # Ask for A→C: should take direct (25km) vs A→B→C (30km)
    result = dijkstra(g, "A", "C")
    assert result["found"] is True
    assert result["total_distance_km"] == 25.0
    assert result["path"] == ["A", "C"]


def test_same_node():
    g = make_graph()
    result = dijkstra(g, "A", "A")
    assert result["found"] is True
    assert result["total_distance_km"] == 0


def test_no_path():
    g = make_graph()
    # D has no outgoing edges in this graph
    result = dijkstra(g, "D", "A")
    assert result["found"] is False
    assert result["error"] is not None


def test_invalid_start():
    g = make_graph()
    result = dijkstra(g, "Z", "A")
    assert result["found"] is False


def test_nodes_explored_positive():
    g = make_graph()
    result = dijkstra(g, "A", "D")
    assert result["nodes_explored"] >= 1


def test_execution_time_positive():
    g = make_graph()
    result = dijkstra(g, "A", "D")
    assert result["execution_time_ms"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
