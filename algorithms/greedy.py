"""
algorithms/greedy.py — Greedy Best-First Search
Uses only the heuristic h(n) to choose which node to expand next.
Fast, but NOT guaranteed to find the optimal (shortest) path.
"""

import time
import heapq
from models.graph import RoadGraph


def greedy(graph: RoadGraph, start: str, goal: str) -> dict:
    """
    Greedy Best-First Search on the road graph.

    At each step, expands the node whose straight-line (haversine)
    distance to the goal is smallest.  It ignores actual accumulated
    cost, so it can find a sub-optimal path very quickly.

    Parameters
    ----------
    graph : RoadGraph instance
    start : starting node ID
    goal  : destination node ID

    Returns
    -------
    Standard result dict (see bfs.py for field descriptions).
    """
    t_start = time.perf_counter()

    if not graph.node_exists(start):
        return _error(f"Start node '{start}' not found.", t_start)
    if not graph.node_exists(goal):
        return _error(f"Goal node '{goal}' not found.", t_start)
    if start == goal:
        return _success([start], graph, t_start, 1)

    visited = set()
    parent = {start: None}
    nodes_explored = 0

    # Heap entries: (heuristic_distance_to_goal, node_id)
    h_start = graph.haversine_distance_km(start, goal)
    heap = [(h_start, start)]

    found = False
    while heap:
        _, current = heapq.heappop(heap)

        if current in visited:
            continue
        visited.add(current)
        nodes_explored += 1

        if current == goal:
            found = True
            break

        for neighbour in graph.get_neighbours(current):
            if neighbour not in visited:
                if neighbour not in parent:
                    parent[neighbour] = current
                h = graph.haversine_distance_km(neighbour, goal)
                heapq.heappush(heap, (h, neighbour))

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

def _reconstruct_path(parent, start, goal):
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path


def _route_metrics(path, graph):
    total_dist = 0.0
    total_time = 0.0
    for i in range(len(path) - 1):
        edge = graph.adjacency.get(path[i], {}).get(path[i + 1], {})
        d = edge.get("distance", 0)
        s = edge.get("speed", 60)
        t = edge.get("traffic", 1.0)
        total_dist += d
        total_time += d / (s / t)
    return round(total_dist, 2), round(total_time, 4)


def _success(path, graph, t_start, nodes_explored):
    dist, time_h = _route_metrics(path, graph)
    elapsed_ms = (time.perf_counter() - t_start) * 1000
    return {
        "algorithm": "Greedy Best-First",
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
        "algorithm": "Greedy Best-First",
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
