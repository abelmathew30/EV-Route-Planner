"""
models/graph.py — Road Network Graph
Represents the road network as a weighted adjacency-list graph.
Supports adding nodes/edges, getting neighbours, and computing travel metrics.
"""

import math


class RoadGraph:
    """
    Weighted directed graph for the road network.

    Internal structure:
        adjacency[node_id] = {
            neighbour_id: {
                "distance": km,
                "speed": km/h,
                "traffic": float (≥1.0),
                "is_blocked": bool
            }
        }

    Node metadata:
        nodes[node_id] = {"id", "name", "lat", "lng"}
    """

    def __init__(self):
        self.adjacency: dict[str, dict] = {}  # graph edges
        self.nodes: dict[str, dict] = {}       # node metadata

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def add_node(self, node_id: str, name: str, lat: float, lng: float):
        """Add a city/junction node to the graph."""
        self.nodes[node_id] = {"id": node_id, "name": name, "lat": lat, "lng": lng}
        if node_id not in self.adjacency:
            self.adjacency[node_id] = {}

    def add_edge(self, from_id: str, to_id: str, distance: float,
                 speed: float, traffic: float = 1.0, is_blocked: bool = False):
        """
        Add a directed road edge.

        Parameters
        ----------
        from_id  : source node
        to_id    : destination node
        distance : road length in km
        speed    : base speed limit in km/h
        traffic  : traffic multiplier (1.0 = free flow, >1.0 = congestion)
        is_blocked: marks road as impassable (dynamic rerouting)
        """
        if from_id not in self.adjacency:
            self.adjacency[from_id] = {}
        self.adjacency[from_id][to_id] = {
            "distance": distance,
            "speed": speed,
            "traffic": traffic,
            "is_blocked": is_blocked,
        }

    # ------------------------------------------------------------------
    # Graph queries
    # ------------------------------------------------------------------

    def get_neighbours(self, node_id: str, skip_blocked: bool = True) -> dict:
        """
        Return {neighbour_id: edge_data} for all reachable neighbours.

        Parameters
        ----------
        skip_blocked : if True, blocked roads are not returned
        """
        neighbours = {}
        for nbr, edge in self.adjacency.get(node_id, {}).items():
            if skip_blocked and edge.get("is_blocked", False):
                continue
            neighbours[nbr] = edge
        return neighbours

    def get_node(self, node_id: str) -> dict | None:
        """Return node metadata dict or None."""
        return self.nodes.get(node_id)

    def node_exists(self, node_id: str) -> bool:
        return node_id in self.nodes

    def all_node_ids(self) -> list[str]:
        return list(self.nodes.keys())

    # ------------------------------------------------------------------
    # Travel metric calculations
    # ------------------------------------------------------------------

    def travel_time_hours(self, from_id: str, to_id: str) -> float:
        """Return travel time in hours for a direct edge (accounting for traffic)."""
        edge = self.adjacency.get(from_id, {}).get(to_id)
        if edge is None:
            return float("inf")
        effective_speed = edge["speed"] / edge["traffic"]
        return edge["distance"] / effective_speed

    def energy_consumed_kwh(self, from_id: str, to_id: str,
                            efficiency_km_per_kwh: float) -> float:
        """
        Energy consumed driving one edge (kWh).

        energy = distance / efficiency
        """
        edge = self.adjacency.get(from_id, {}).get(to_id)
        if edge is None:
            return float("inf")
        return edge["distance"] / efficiency_km_per_kwh

    # ------------------------------------------------------------------
    # Heuristic (admissible) for A*
    # ------------------------------------------------------------------

    def haversine_distance_km(self, node_a: str, node_b: str) -> float:
        """
        Great-circle distance between two nodes (km).
        Used as the A* heuristic — always ≤ road distance, so admissible.
        """
        a = self.nodes.get(node_a)
        b = self.nodes.get(node_b)
        if a is None or b is None:
            return 0.0
        R = 6371.0  # Earth radius in km
        lat1, lon1 = math.radians(a["lat"]), math.radians(a["lng"])
        lat2, lon2 = math.radians(b["lat"]), math.radians(b["lng"])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        inner = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(inner))

    # ------------------------------------------------------------------
    # Dynamic rerouting helpers
    # ------------------------------------------------------------------

    def block_edge(self, from_id: str, to_id: str):
        """Mark a road as blocked (simulates road closure / station outage)."""
        if from_id in self.adjacency and to_id in self.adjacency[from_id]:
            self.adjacency[from_id][to_id]["is_blocked"] = True

    def unblock_edge(self, from_id: str, to_id: str):
        """Remove road block."""
        if from_id in self.adjacency and to_id in self.adjacency[from_id]:
            self.adjacency[from_id][to_id]["is_blocked"] = False

    def block_node(self, node_id: str):
        """
        Block all incoming and outgoing edges of a node.
        Useful for simulating a charging station going offline.
        """
        # Block all outgoing
        for nbr in self.adjacency.get(node_id, {}):
            self.adjacency[node_id][nbr]["is_blocked"] = True
        # Block all incoming
        for src in self.adjacency:
            if node_id in self.adjacency[src]:
                self.adjacency[src][node_id]["is_blocked"] = True

    def unblock_node(self, node_id: str):
        """Restore all edges of a node."""
        for nbr in self.adjacency.get(node_id, {}):
            self.adjacency[node_id][nbr]["is_blocked"] = False
        for src in self.adjacency:
            if node_id in self.adjacency[src]:
                self.adjacency[src][node_id]["is_blocked"] = False

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Export graph as a JSON-serialisable dictionary."""
        return {
            "nodes": list(self.nodes.values()),
            "edges": [
                {"from": src, "to": dst, **data}
                for src, nbrs in self.adjacency.items()
                for dst, data in nbrs.items()
            ],
        }
