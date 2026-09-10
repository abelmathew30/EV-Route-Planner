"""
algorithms/astar.py — A* Search
Optimal heuristic search: f(n) = g(n) + h(n)

g(n) = actual accumulated cost (distance) from start to n
h(n) = admissible heuristic: haversine straight-line distance to goal

Because h(n) never overestimates the true cost, A* is both complete
and optimal — it finds the shortest-distance path while exploring
far fewer nodes than Dijkstra on average.
"""

import time
import heapq
from models.graph import RoadGraph


def astar(graph: RoadGraph, start: str, goal: str) -> dict:
    """
    A* Search on the road graph (distance optimisation).

    Parameters
    ----------
    graph : RoadGraph instance
    start : starting node ID
    goal  : destination node ID

    Returns
    -------
    Standard result dict with path, metrics, nodes_explored, time.
    """
    t_start = time.perf_counter()

    if not graph.node_exists(start):
        return _error(f"Start node '{start}' not found.", t_start)
    if not graph.node_exists(goal):
        return _error(f"Goal node '{goal}' not found.", t_start)
    if start == goal:
        return _success([start], graph, t_start, 1)

    # g_cost[node] = best known cost (distance) from start
    g_cost = {node: float("inf") for node in graph.all_node_ids()}
    g_cost[start] = 0.0

    parent = {start: None}
    closed = set()
    nodes_explored = 0

    # Heap entries: (f = g + h, g, node_id)
    # We include g as secondary key to break ties consistently
    h_start = graph.haversine_distance_km(start, goal)
    heap = [(h_start, 0.0, start)]

    found = False
    while heap:
        f, g, current = heapq.heappop(heap)

        if current in closed:
            continue
        closed.add(current)
        nodes_explored += 1

        if current == goal:
            found = True
            break

        for neighbour, edge in graph.get_neighbours(current).items():
            if neighbour in closed:
                continue
            new_g = g_cost[current] + edge["distance"]
            if new_g < g_cost[neighbour]:
                g_cost[neighbour] = new_g
                parent[neighbour] = current
                h = graph.haversine_distance_km(neighbour, goal)
                heapq.heappush(heap, (new_g + h, new_g, neighbour))

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
        "algorithm": "A*",
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
        "algorithm": "A*",
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
