"""
tests/test_astar.py — Unit tests for A* algorithm
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from models.graph import RoadGraph
from algorithms.astar import astar
from algorithms.dijkstra import dijkstra


def make_graph() -> RoadGraph:
    g = RoadGraph()
    g.add_node("A", "Alpha",   10.00, 76.00)
    g.add_node("B", "Beta",    10.05, 76.15)
    g.add_node("C", "Gamma",   10.10, 76.30)
    g.add_node("D", "Delta",   10.20, 76.50)
    g.add_node("E", "Epsilon", 10.00, 76.40)
    # Edges
    g.add_edge("A", "B", 15, 60)
    g.add_edge("B", "C", 15, 60)
    g.add_edge("C", "D", 20, 60)
    g.add_edge("A", "E", 40, 60)
    g.add_edge("E", "D", 20, 60)
    return g


def test_finds_optimal_path():
    g = make_graph()
    res_astar = astar(g, "A", "D")
    res_dijkstra = dijkstra(g, "A", "D")
    assert res_astar["found"] is True
    # A* should find the same optimal distance as Dijkstra
    assert res_astar["total_distance_km"] == res_dijkstra["total_distance_km"]


def test_astar_explores_fewer_nodes_than_dijkstra():
    g = make_graph()
    res_astar = astar(g, "A", "D")
    res_dijkstra = dijkstra(g, "A", "D")
    # A* should explore ≤ nodes than Dijkstra (usually fewer)
    assert res_astar["nodes_explored"] <= res_dijkstra["nodes_explored"]


def test_same_node():
    g = make_graph()
    result = astar(g, "A", "A")
    assert result["found"] is True
    assert result["total_distance_km"] == 0


def test_no_path():
    g = make_graph()
    result = astar(g, "D", "A")  # no edges back to A
    assert result["found"] is False


def test_invalid_start_node():
    g = make_graph()
    result = astar(g, "X", "D")
    assert result["found"] is False
    assert "not found" in result["error"].lower()


def test_path_is_connected():
    g = make_graph()
    result = astar(g, "A", "D")
    path = result["path"]
    for i in range(len(path) - 1):
        assert path[i + 1] in g.adjacency[path[i]]


def test_execution_time_logged():
    g = make_graph()
    result = astar(g, "A", "D")
    assert result["execution_time_ms"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
