"""
routes/api.py — REST API Endpoints
All endpoints return JSON. The frontend JavaScript calls these.

Endpoints:
  GET  /api/stations       – list all charging stations
  GET  /api/graph          – export road graph as JSON
  POST /api/route          – compute EV route (battery-aware A*)
  POST /api/compare        – run all 4 algorithms for comparison
  POST /api/simulate       – EV battery simulation
  POST /api/reroute        – dynamic rerouting after blocking a node/edge
"""

from flask import Blueprint, request, jsonify, current_app

from models.database import db, RoadNode, RoadEdge, ChargingStation
from models.graph import RoadGraph
from models.ev import EV
from models.charging_station import ChargingStationModel
from algorithms.bfs import bfs
from algorithms.dijkstra import dijkstra
from algorithms.greedy import greedy
from algorithms.astar import astar
from algorithms.ev_astar import ev_astar

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ------------------------------------------------------------------
# Helper: build RoadGraph from database
# ------------------------------------------------------------------

def _build_graph(skip_blocked: bool = True) -> RoadGraph:
    """Construct a RoadGraph from the SQLite database."""
    graph = RoadGraph()
    for node in RoadNode.query.all():
        graph.add_node(node.id, node.name, node.lat, node.lng)
    for edge in RoadEdge.query.all():
        if skip_blocked and edge.is_blocked:
            continue
        graph.add_edge(
            edge.from_node, edge.to_node,
            edge.distance, edge.speed, edge.traffic, edge.is_blocked
        )
    return graph


def _get_stations() -> list:
    """Load all available charging stations as domain objects."""
    rows = ChargingStation.query.all()
    return [
        ChargingStationModel(
            station_id=s.id, name=s.name, node_id=s.node_id,
            lat=s.lat, lng=s.lng, charger_type=s.charger_type,
            charging_power=s.charging_power, price_per_kwh=s.price_per_kwh,
            available=s.available, num_chargers=s.num_chargers,
        )
        for s in rows
    ]


def _validate_ev_params(data: dict) -> tuple[dict | None, str | None]:
    """Parse and validate EV parameters from request JSON. Returns (params, error)."""
    try:
        params = {
            "battery_capacity": float(data.get("battery_capacity", 60)),
            "battery_pct": float(data.get("battery_pct", 80)),
            "efficiency": float(data.get("efficiency", 6.0)),
            "max_charge_power": float(data.get("max_charge_power", 150)),
            "min_reserve": float(data.get("min_reserve", 10)),
        }
    except (TypeError, ValueError) as e:
        return None, f"Invalid EV parameter: {e}"

    if params["battery_capacity"] <= 0:
        return None, "Battery capacity must be positive."
    if not (0 <= params["battery_pct"] <= 100):
        return None, "Battery percentage must be between 0 and 100."
    if params["efficiency"] <= 0:
        return None, "Efficiency must be positive."
    if params["max_charge_power"] <= 0:
        return None, "Max charging power must be positive."
    if not (0 <= params["min_reserve"] < 100):
        return None, "Minimum reserve must be between 0 and 100."

    return params, None


# ------------------------------------------------------------------
# GET /api/stations
# ------------------------------------------------------------------

@api_bp.route("/stations", methods=["GET"])
def get_stations():
    """Return all charging stations as JSON."""
    stations = ChargingStation.query.all()
    return jsonify([s.to_dict() for s in stations])


# ------------------------------------------------------------------
# GET /api/graph
# ------------------------------------------------------------------

@api_bp.route("/graph", methods=["GET"])
def get_graph():
    """Export the road graph (nodes + edges) as JSON."""
    graph = _build_graph(skip_blocked=False)
    return jsonify(graph.to_dict())


# ------------------------------------------------------------------
# POST /api/route
# ------------------------------------------------------------------

@api_bp.route("/route", methods=["POST"])
def compute_route():
    """
    Compute an EV route using the battery-aware A* algorithm.

    Request JSON:
      start            : node ID (e.g. "KCH")
      goal             : node ID (e.g. "TVM")
      battery_capacity : kWh (default 60)
      battery_pct      : % (default 80)
      efficiency       : km/kWh (default 6.0)
      max_charge_power : kW (default 150)
      min_reserve      : % (default 10)
      mode             : "fastest"|"cheapest"|"eco"|"balanced" (default "balanced")
    """
    data = request.get_json(force=True, silent=True) or {}

    start = data.get("start", "").strip().upper()
    goal = data.get("goal", "").strip().upper()
    mode = data.get("mode", "balanced").lower()

    if not start:
        return jsonify({"error": "Start location is required."}), 400
    if not goal:
        return jsonify({"error": "Destination is required."}), 400
    if start == goal:
        return jsonify({"error": "Start and destination cannot be the same."}), 400

    ev_params, err = _validate_ev_params(data)
    if err:
        return jsonify({"error": err}), 400

    graph = _build_graph()
    stations = _get_stations()

    result = ev_astar(
        graph=graph,
        start=start,
        goal=goal,
        battery_capacity_kwh=ev_params["battery_capacity"],
        battery_pct=ev_params["battery_pct"],
        efficiency_km_per_kwh=ev_params["efficiency"],
        max_charge_power_kw=ev_params["max_charge_power"],
        min_reserve_pct=ev_params["min_reserve"],
        stations=stations,
        mode=mode,
    )

    if not result["found"]:
        return jsonify({"error": result["error"]}), 422

    # Attach node coordinates for map rendering
    result["node_coords"] = {
        nid: {"lat": n.lat, "lng": n.lng, "name": n.name}
        for nid, n in [(n.id, n) for n in RoadNode.query.all()]
        if nid in result["path"]
    }
    station_nodes = {s.node_id for s in ChargingStation.query.all()}
    result["station_coords"] = {
        s.node_id: {
            "lat": s.lat, "lng": s.lng,
            "name": s.name, "type": s.charger_type,
            "power": s.charging_power, "price": s.price_per_kwh,
        }
        for s in ChargingStation.query.all()
        if s.node_id in result["path"]
    }

    return jsonify(result)


# ------------------------------------------------------------------
# POST /api/compare
# ------------------------------------------------------------------

@api_bp.route("/compare", methods=["POST"])
def compare_algorithms():
    """
    Run BFS, Dijkstra, Greedy, and A* on the same route and return
    all results for side-by-side comparison.

    Request JSON:
      start : node ID
      goal  : node ID
    """
    data = request.get_json(force=True, silent=True) or {}
    start = data.get("start", "").strip().upper()
    goal = data.get("goal", "").strip().upper()

    if not start or not goal:
        return jsonify({"error": "Both start and goal are required."}), 400
    if start == goal:
        return jsonify({"error": "Start and goal cannot be the same."}), 400

    graph = _build_graph()

    results = {
        "BFS": bfs(graph, start, goal),
        "Dijkstra": dijkstra(graph, start, goal),
        "Greedy": greedy(graph, start, goal),
        "A*": astar(graph, start, goal),
    }

    # Determine the optimal (minimum distance) among found routes
    best_dist = min(
        (r["total_distance_km"] for r in results.values() if r["found"]),
        default=None,
    )
    for algo, r in results.items():
        r["is_optimal"] = r["found"] and r["total_distance_km"] == best_dist

    return jsonify(results)


# ------------------------------------------------------------------
# POST /api/simulate
# ------------------------------------------------------------------

@api_bp.route("/simulate", methods=["POST"])
def simulate():
    """
    Simulate EV battery for a given distance.

    Request JSON: EV params + distance_km
    """
    data = request.get_json(force=True, silent=True) or {}

    ev_params, err = _validate_ev_params(data)
    if err:
        return jsonify({"error": err}), 400

    try:
        distance_km = float(data.get("distance_km", 0))
        if distance_km < 0:
            return jsonify({"error": "Distance cannot be negative."}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid distance value."}), 400

    ev = EV(
        battery_capacity=ev_params["battery_capacity"],
        battery_percentage=ev_params["battery_pct"],
        efficiency=ev_params["efficiency"],
        max_charging_power=ev_params["max_charge_power"],
        min_reserve=ev_params["min_reserve"],
    )

    sim_result = ev.simulate_drive(distance_km)
    ev_info = ev.to_dict()

    return jsonify({**ev_info, **sim_result})


# ------------------------------------------------------------------
# POST /api/reroute
# ------------------------------------------------------------------

@api_bp.route("/reroute", methods=["POST"])
def reroute():
    """
    Dynamic rerouting: block a node or edge, then recompute the route.

    Request JSON:
      start, goal, EV params, mode (same as /api/route)
      blocked_nodes : list of node IDs to block (e.g. ["ATN"])
      blocked_edges : list of [from, to] pairs to block
    """
    data = request.get_json(force=True, silent=True) or {}

    start = data.get("start", "").strip().upper()
    goal = data.get("goal", "").strip().upper()
    mode = data.get("mode", "balanced").lower()
    blocked_nodes = data.get("blocked_nodes", [])
    blocked_edges = data.get("blocked_edges", [])

    if not start or not goal:
        return jsonify({"error": "Both start and goal are required."}), 400

    ev_params, err = _validate_ev_params(data)
    if err:
        return jsonify({"error": err}), 400

    graph = _build_graph()

    # Apply blocks
    for node_id in blocked_nodes:
        if graph.node_exists(node_id):
            graph.block_node(node_id)
    for edge_pair in blocked_edges:
        if len(edge_pair) == 2:
            graph.block_edge(edge_pair[0], edge_pair[1])

    stations = _get_stations()
    # Also mark stations at blocked nodes as unavailable
    blocked_set = set(blocked_nodes)
    stations = [s for s in stations if s.node_id not in blocked_set]

    result = ev_astar(
        graph=graph,
        start=start,
        goal=goal,
        battery_capacity_kwh=ev_params["battery_capacity"],
        battery_pct=ev_params["battery_pct"],
        efficiency_km_per_kwh=ev_params["efficiency"],
        max_charge_power_kw=ev_params["max_charge_power"],
        min_reserve_pct=ev_params["min_reserve"],
        stations=stations,
        mode=mode,
    )

    result["blocked_nodes"] = blocked_nodes
    result["blocked_edges"] = blocked_edges
    result["rerouted"] = True

    if not result["found"]:
        return jsonify({
            "error": result["error"],
            "blocked_nodes": blocked_nodes,
            "blocked_edges": blocked_edges,
            "rerouted": True,
        }), 422

    return jsonify(result)


# ------------------------------------------------------------------
# POST /api/update-traffic
# ------------------------------------------------------------------

@api_bp.route("/update-traffic", methods=["POST"])
def update_traffic():
    """
    Update traffic factor for an edge (for demo purposes).

    Request JSON:
      from_node : node ID
      to_node   : node ID
      traffic   : float (1.0 = free, 1.2 = moderate, 1.5 = heavy)
    """
    data = request.get_json(force=True, silent=True) or {}
    from_node = data.get("from_node", "").upper()
    to_node = data.get("to_node", "").upper()
    try:
        traffic = float(data.get("traffic", 1.0))
        if traffic < 1.0 or traffic > 3.0:
            return jsonify({"error": "Traffic factor must be between 1.0 and 3.0."}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid traffic value."}), 400

    edge = RoadEdge.query.filter_by(from_node=from_node, to_node=to_node).first()
    if not edge:
        return jsonify({"error": f"Edge {from_node}→{to_node} not found."}), 404

    edge.traffic = traffic
    db.session.commit()
    return jsonify({"message": f"Traffic on {from_node}→{to_node} updated to {traffic}."})
