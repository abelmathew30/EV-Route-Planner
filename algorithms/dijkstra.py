"""
algorithms/dijkstra.py — Dijkstra / Uniform-Cost Search
Finds the shortest-distance path in a weighted graph using a min-heap.
Guarantees an optimal (minimum-cost) solution.
"""

import time
import heapq
from models.graph import RoadGraph


def dijkstra(graph: RoadGraph, start: str, goal: str) -> dict:
    """
    Dijkstra's algorithm (Uniform-Cost Search) on the road graph.

    Uses road *distance* as the edge weight. Guarantees the globally
    shortest distance path.

    Parameters
    ----------
    graph : RoadGraph instance
    start : starting node ID
    goal  : destination node ID

    Returns
    -------
    dict with keys:
      path, path_names, total_distance_km, total_time_h, total_time_min,
      nodes_explored, execution_time_ms, found, error
    """
    t_start = time.perf_counter()

    if not graph.node_exists(start):
        return _error(f"Start node '{start}' not found.", t_start)
    if not graph.node_exists(goal):
        return _error(f"Goal node '{goal}' not found.", t_start)
    if start == goal:
        return _success([start], graph, t_start, nodes_explored=1)

    # dist[node] = best known cumulative distance from start
    dist = {node: float("inf") for node in graph.all_node_ids()}
    dist[start] = 0.0

    parent = {start: None}
    nodes_explored = 0

    # Priority queue entries: (cumulative_distance, node_id)
    heap = [(0.0, start)]

    while heap:
        current_dist, current = heapq.heappop(heap)

        # If we already found a shorter path to this node, skip
        if current_dist > dist[current]:
            continue

        nodes_explored += 1

        if current == goal:
            break

        for neighbour, edge in graph.get_neighbours(current).items():
            new_dist = dist[current] + edge["distance"]
            if new_dist < dist[neighbour]:
                dist[neighbour] = new_dist
                parent[neighbour] = current
                heapq.heappush(heap, (new_dist, neighbour))

    if dist[goal] == float("inf"):
        return _error(
            f"No path from '{start}' to '{goal}'. Destination unreachable.",
            t_start,
            nodes_explored=nodes_explored,
        )

    path = _reconstruct_path(parent, start, goal)
    return _success(path, graph, t_start, nodes_explored)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _reconstruct_path(parent: dict, start: str, goal: str) -> list[str]:
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    return path


def _route_metrics(path: list[str], graph: RoadGraph) -> tuple[float, float]:
    total_dist = 0.0
    total_time = 0.0
    for i in range(len(path) - 1):
        edge = graph.adjacency.get(path[i], {}).get(path[i + 1], {})
        dist = edge.get("distance", 0)
        speed = edge.get("speed", 60)
        traffic = edge.get("traffic", 1.0)
        total_dist += dist
        total_time += dist / (speed / traffic)
    return round(total_dist, 2), round(total_time, 4)


def _success(path, graph, t_start, nodes_explored):
    dist, time_h = _route_metrics(path, graph)
    elapsed_ms = (time.perf_counter() - t_start) * 1000
    return {
        "algorithm": "Dijkstra",
        "found": True,
        "path": path,
        "path_names": [graph.get_node(n)["name"] for n in path],
        "total_distance_km": dist,
        "total_time_h": time_h,
        "total_time_min": round(time_h * 60, 1),
        "nodes_explored": nodes_explored,
        "execution_time_ms": round(elapsed_ms, 3),
        "error": None,
    }


def _error(message, t_start, nodes_explored=0):
    elapsed_ms = (time.perf_counter() - t_start) * 1000
    return {
        "algorithm": "Dijkstra",
        "found": False,
        "path": [],
        "path_names": [],
        "total_distance_km": 0,
        "total_time_h": 0,
        "total_time_min": 0,
        "nodes_explored": nodes_explored,
        "execution_time_ms": round(elapsed_ms, 3),
        "error": message,
    }
