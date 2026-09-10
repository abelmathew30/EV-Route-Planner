"""
algorithms/ev_astar.py — Battery-Aware A* Search
Extends standard A* to a state space of (location, battery_level).

State  : (node_id, battery_percentage)
Actions:
  1. DRIVE  — move along a road edge (deducts energy)
  2. CHARGE — charge at a station on the current node (adds energy)

The algorithm finds the minimum-cost route from start to goal
while respecting battery constraints at every step.
"""

import time
import heapq
import math
from models.graph import RoadGraph
from models.charging_station import ChargingStationModel
from algorithms.cost import compute_edge_cost, get_weights


# Battery is discretised to nearest integer % for the state space.
# This keeps the state space finite and manageable.
BATTERY_STEP = 5  # % granularity for charging decisions


def ev_astar(
    graph: RoadGraph,
    start: str,
    goal: str,
    battery_capacity_kwh: float,
    battery_pct: float,
    efficiency_km_per_kwh: float,
    max_charge_power_kw: float,
    min_reserve_pct: float,
    stations: list,          # list of ChargingStationModel
    mode: str = "balanced",  # cost optimisation mode
) -> dict:
    """
    Battery-Aware A* that plans charging stops automatically.

    State: (node_id, battery_pct_rounded)

    Transitions:
      DRIVE  : move to adjacent node if energy available
      CHARGE : at any node with a station, jump battery up to next target level

    Parameters
    ----------
    graph               : RoadGraph
    start, goal         : node IDs
    battery_capacity_kwh: total battery (kWh)
    battery_pct         : starting battery (%)
    efficiency_km_per_kwh: km per kWh
    max_charge_power_kw : max EV charger input (kW)
    min_reserve_pct     : minimum battery % to keep
    stations            : list of ChargingStationModel objects
    mode                : "fastest" | "cheapest" | "eco" | "balanced"

    Returns
    -------
    dict with:
      found, path, path_names, charging_stops, step_timeline,
      total_distance_km, total_travel_time_h, total_charge_time_h,
      total_charge_cost_inr, total_energy_kwh, final_battery_pct,
      nodes_explored, execution_time_ms, error
    """
    t_start = time.perf_counter()

    # -- Validation -------------------------------------------------------
    if not graph.node_exists(start):
        return _error(f"Start node '{start}' not found.", t_start)
    if not graph.node_exists(goal):
        return _error(f"Goal node '{goal}' not found.", t_start)
    if battery_pct < min_reserve_pct:
        return _error(
            f"Starting battery ({battery_pct}%) is below minimum reserve ({min_reserve_pct}%).",
            t_start,
        )

    weights = get_weights(mode)

    # -- Station index (node_id → ChargingStationModel) -------------------
    station_at: dict[str, ChargingStationModel] = {}
    for s in stations:
        if s.available:
            station_at[s.node_id] = s

    # -- State space -------------------------------------------------------
    # state = (node_id, battery_pct_rounded_to_BATTERY_STEP)
    def round_pct(pct):
        return round(pct / BATTERY_STEP) * BATTERY_STEP

    start_pct = round_pct(battery_pct)
    start_state = (start, start_pct)

    # g_cost[state] = best accumulated multi-objective cost
    g_cost: dict = {start_state: 0.0}

    # For path reconstruction
    parent: dict = {start_state: None}
    action_log: dict = {}  # state -> action description

    closed = set()
    nodes_explored = 0

    def heuristic(node, bpct):
        """
        Admissible heuristic: minimum driving cost to reach goal.
        Ignores battery constraints (optimistic lower bound).
        """
        dist_km = graph.haversine_distance_km(node, goal)
        energy_kwh = dist_km / efficiency_km_per_kwh
        # Use a very rough time estimate based on 80 km/h average
        time_h = dist_km / 80.0
        h = compute_edge_cost(
            travel_time_h=time_h,
            charging_time_h=0,
            charging_cost_inr=0,
            energy_kwh=energy_kwh,
            weights=weights,
        )
        return h

    h0 = heuristic(start, start_pct)
    # heap: (f, g, node_id, battery_pct)
    heap = [(h0, 0.0, start, start_pct)]

    found_state = None

    while heap:
        f, g, current_node, current_bpct = heapq.heappop(heap)
        state = (current_node, current_bpct)

        if state in closed:
            continue
        closed.add(state)
        nodes_explored += 1

        # Check goal
        if current_node == goal:
            found_state = state
            break

        current_energy = battery_capacity_kwh * (current_bpct / 100.0)
        reserve_energy = battery_capacity_kwh * (min_reserve_pct / 100.0)
        usable_energy = current_energy - reserve_energy

        # --- Action 1: DRIVE to each neighbour ---------------------------
        for neighbour, edge in graph.get_neighbours(current_node).items():
            dist_km = edge["distance"]
            energy_needed = dist_km / efficiency_km_per_kwh

            if energy_needed > usable_energy + 1e-6:
                continue  # not enough battery — skip

            # Compute metrics for this edge
            speed = edge["speed"]
            traffic = edge["traffic"]
            travel_h = dist_km / (speed / traffic)
            new_energy = current_energy - energy_needed
            new_pct = round_pct(max(min_reserve_pct, (new_energy / battery_capacity_kwh) * 100))

            edge_cost = compute_edge_cost(
                travel_time_h=travel_h,
                charging_time_h=0,
                charging_cost_inr=0,
                energy_kwh=energy_needed,
                weights=weights,
            )
            new_g = g_cost[state] + edge_cost
            new_state = (neighbour, new_pct)

            if new_g < g_cost.get(new_state, float("inf")):
                g_cost[new_state] = new_g
                parent[new_state] = state
                action_log[new_state] = {
                    "type": "drive",
                    "from": current_node,
                    "to": neighbour,
                    "distance_km": round(dist_km, 2),
                    "energy_kwh": round(energy_needed, 3),
                    "travel_time_h": round(travel_h, 4),
                    "battery_before_pct": current_bpct,
                    "battery_after_pct": new_pct,
                }
                h = heuristic(neighbour, new_pct)
                heapq.heappush(heap, (new_g + h, new_g, neighbour, new_pct))

        # --- Action 2: CHARGE at station on current node -----------------
        if current_node in station_at:
            station = station_at[current_node]
            # Offer charging to several target levels
            targets = [t for t in [60, 70, 80, 90, 100] if t > current_bpct + 5]
            for target_pct in targets:
                energy_to_add = battery_capacity_kwh * ((target_pct - current_bpct) / 100.0)
                effective_power = min(station.charging_power, max_charge_power_kw)
                charge_time_h = energy_to_add / effective_power
                charge_cost = energy_to_add * station.price_per_kwh

                charge_cost_val = compute_edge_cost(
                    travel_time_h=0,
                    charging_time_h=charge_time_h,
                    charging_cost_inr=charge_cost,
                    energy_kwh=0,
                    weights=weights,
                )
                new_g = g_cost[state] + charge_cost_val
                new_bpct = round_pct(target_pct)
                new_state = (current_node, new_bpct)

                if new_g < g_cost.get(new_state, float("inf")):
                    g_cost[new_state] = new_g
                    parent[new_state] = state
                    action_log[new_state] = {
                        "type": "charge",
                        "node": current_node,
                        "station_name": station.name,
                        "station_id": station.id,
                        "charger_type": station.charger_type,
                        "energy_added_kwh": round(energy_to_add, 3),
                        "charge_time_h": round(charge_time_h, 4),
                        "charge_time_min": round(charge_time_h * 60, 2),
                        "charge_cost_inr": round(charge_cost, 2),
                        "battery_before_pct": current_bpct,
                        "battery_after_pct": new_bpct,
                    }
                    h = heuristic(current_node, new_bpct)
                    heapq.heappush(heap, (new_g + h, new_g, current_node, new_bpct))

    # -- No path found -----------------------------------------------------
    if found_state is None:
        return _error(
            "No feasible route found. Battery may be insufficient even with charging stops. "
            "Try increasing battery capacity or starting charge percentage.",
            t_start,
            nodes_explored=nodes_explored,
        )

    # -- Reconstruct path and build timeline --------------------------------
    state_path = _reconstruct_state_path(parent, start_state, found_state)
    timeline, charging_stops, totals = _build_timeline(
        state_path, action_log, graph
    )

    elapsed_ms = (time.perf_counter() - t_start) * 1000

    node_path = _extract_node_path(state_path)

    return {
        "algorithm": "Battery-Aware A*",
        "found": True,
        "path": node_path,
        "path_names": [graph.get_node(n)["name"] for n in node_path],
        "charging_stops": charging_stops,
        "step_timeline": timeline,
        "total_distance_km": round(totals["distance"], 2),
        "total_travel_time_h": round(totals["travel_h"], 4),
        "total_travel_time_min": round(totals["travel_h"] * 60, 1),
        "total_charge_time_h": round(totals["charge_h"], 4),
        "total_charge_time_min": round(totals["charge_h"] * 60, 1),
        "total_journey_time_h": round(totals["travel_h"] + totals["charge_h"], 4),
        "total_journey_time_min": round((totals["travel_h"] + totals["charge_h"]) * 60, 1),
        "total_charge_cost_inr": round(totals["charge_cost"], 2),
        "total_energy_kwh": round(totals["energy"], 3),
        "final_battery_pct": found_state[1],
        "nodes_explored": nodes_explored,
        "execution_time_ms": round(elapsed_ms, 3),
        "mode": mode,
        "error": None,
    }


# ------------------------------------------------------------------
# Path reconstruction helpers
# ------------------------------------------------------------------

def _reconstruct_state_path(parent, start_state, goal_state):
    path = []
    cur = goal_state
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)
    path.reverse()
    return path


def _extract_node_path(state_path):
    """Deduplicate consecutive same-node states (charging actions)."""
    nodes = []
    for node, _ in state_path:
        if not nodes or nodes[-1] != node:
            nodes.append(node)
    return nodes


def _build_timeline(state_path, action_log, graph):
    """
    Convert the state path + action log into:
      - A human-readable step timeline
      - A list of charging stop dicts
      - Aggregate totals
    """
    timeline = []
    charging_stops = []
    totals = {"distance": 0, "travel_h": 0, "charge_h": 0,
              "charge_cost": 0, "energy": 0}

    step_num = 1
    for state in state_path[1:]:
        action = action_log.get(state)
        if action is None:
            continue

        if action["type"] == "drive":
            from_name = graph.get_node(action["from"])["name"]
            to_name = graph.get_node(action["to"])["name"]
            timeline.append({
                "step": step_num,
                "type": "drive",
                "description": (
                    f"Drive from {from_name} → {to_name} "
                    f"({action['distance_km']} km, "
                    f"{round(action['travel_time_h'] * 60, 1)} min)"
                ),
                "from_node": action["from"],
                "to_node": action["to"],
                "distance_km": action["distance_km"],
                "energy_kwh": action["energy_kwh"],
                "travel_time_min": round(action["travel_time_h"] * 60, 1),
                "battery_before_pct": action["battery_before_pct"],
                "battery_after_pct": action["battery_after_pct"],
            })
            totals["distance"] += action["distance_km"]
            totals["travel_h"] += action["travel_time_h"]
            totals["energy"] += action["energy_kwh"]

        elif action["type"] == "charge":
            node_name = graph.get_node(action["node"])["name"]
            timeline.append({
                "step": step_num,
                "type": "charge",
                "description": (
                    f"Charge at {action['station_name']} in {node_name}: "
                    f"{action['battery_before_pct']}% → {action['battery_after_pct']}% "
                    f"(+{action['energy_added_kwh']} kWh, "
                    f"{action['charge_time_min']} min, "
                    f"₹{action['charge_cost_inr']})"
                ),
                "node": action["node"],
                "station_name": action["station_name"],
                "station_id": action["station_id"],
                "charger_type": action["charger_type"],
                "energy_added_kwh": action["energy_added_kwh"],
                "charge_time_min": action["charge_time_min"],
                "charge_cost_inr": action["charge_cost_inr"],
                "battery_before_pct": action["battery_before_pct"],
                "battery_after_pct": action["battery_after_pct"],
            })
            charging_stops.append({
                "node_id": action["node"],
                "station_name": action["station_name"],
                "station_id": action["station_id"],
                "energy_added_kwh": action["energy_added_kwh"],
                "charge_time_min": action["charge_time_min"],
                "charge_cost_inr": action["charge_cost_inr"],
                "battery_before_pct": action["battery_before_pct"],
                "battery_after_pct": action["battery_after_pct"],
            })
            totals["charge_h"] += action["charge_time_h"]
            totals["charge_cost"] += action["charge_cost_inr"]

        step_num += 1

    return timeline, charging_stops, totals


# ------------------------------------------------------------------
# Error helper
# ------------------------------------------------------------------

def _error(message, t_start, nodes_explored=0):
    elapsed_ms = (time.perf_counter() - t_start) * 1000
    return {
        "algorithm": "Battery-Aware A*",
        "found": False,
        "path": [],
        "path_names": [],
        "charging_stops": [],
        "step_timeline": [],
        "total_distance_km": 0,
        "total_travel_time_h": 0,
        "total_travel_time_min": 0,
        "total_charge_time_h": 0,
        "total_charge_time_min": 0,
        "total_journey_time_h": 0,
        "total_journey_time_min": 0,
        "total_charge_cost_inr": 0,
        "total_energy_kwh": 0,
        "final_battery_pct": 0,
        "nodes_explored": nodes_explored,
        "execution_time_ms": round(elapsed_ms, 3),
        "mode": "unknown",
        "error": message,
    }
