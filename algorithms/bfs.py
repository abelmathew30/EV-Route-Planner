"""
algorithms/bfs.py — Breadth-First Search
Finds the shortest path in terms of *number of hops* (ignores edge weights).
Included for educational comparison — not optimal for weighted EV routing.
"""

import time
from collections import deque
from models.graph import RoadGraph


def bfs(graph: RoadGraph, start: str, goal: str) -> dict:
    """
    Breadth-First Search on the road graph.

    Explores nodes layer by layer, guaranteeing the fewest hops
    but NOT the shortest distance or lowest cost.

    Parameters
    ----------
    graph : RoadGraph instance
    start : starting node ID
    goal  : destination node ID

    Returns
    -------
    dict with keys:
      path            – list of node IDs from start to goal
      path_names      – list of human-readable city names
      total_distance  – total route distance in km
      total_time_h    – total travel time in hours
      nodes_explored  – how many nodes BFS visited
      execution_time_ms – wall-clock time in milliseconds
      found           – True if a path was found
      error           – error message if not found
    """
    t_start = time.perf_counter()

    # Input validation
    if not graph.node_exists(start):
        return _error(f"Start node '{start}' not found in graph.", t_start)
    if not graph.node_exists(goal):
        return _error(f"Goal node '{goal}' not found in graph.", t_start)
    if start == goal:
        node_name = graph.get_node(start)["name"]
        return _success([start], graph, t_start, nodes_explored=1)

    # BFS data structures
    queue = deque()
    queue.append(start)
    visited = {start}          # set of already-explored nodes
    parent = {start: None}     # to reconstruct path
    nodes_explored = 0

    found = False
    while queue:
        current = queue.popleft()
        nodes_explored += 1

        if current == goal:
            found = True
            break

        for neighbour in graph.get_neighbours(current):
            if neighbour not in visited:
                visited.add(neighbour)
                parent[neighbour] = current
                queue.append(neighbour)

    if not found:
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
    """Walk the parent map back from goal to start, then reverse."""
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    return path


def _route_metrics(path: list[str], graph: RoadGraph) -> tuple[float, float]:
    """Compute total distance (km) and travel time (h) for a path."""
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


def _success(path: list[str], graph: RoadGraph, t_start: float,
             nodes_explored: int) -> dict:
    dist, time_h = _route_metrics(path, graph)
    elapsed_ms = (time.perf_counter() - t_start) * 1000
    return {
        "algorithm": "BFS",
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


def _error(message: str, t_start: float, nodes_explored: int = 0) -> dict:
    elapsed_ms = (time.perf_counter() - t_start) * 1000
    return {
        "algorithm": "BFS",
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
