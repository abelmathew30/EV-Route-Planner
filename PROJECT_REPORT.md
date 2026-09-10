# PROJECT REPORT

## EV Charging Route Planner
### AI-Based EV Charging Route Optimization Using Heuristic Search

---

## 1. Abstract

This project presents the design and implementation of an AI-powered Electric Vehicle (EV) Charging Route Planner — a full-stack web application that solves the problem of optimal route planning for EVs under battery constraints. The system implements five search algorithms: Breadth-First Search (BFS), Dijkstra's Algorithm, Greedy Best-First Search, A* Search, and a novel Battery-Aware A* algorithm that extends A* to handle the (location, battery) state space with automatic charging stop selection. A multi-objective cost function with four optimization presets (Fastest, Cheapest, Eco, Balanced) allows users to trade off between journey time, charging cost, and energy consumption. The system is built with Python 3 / Flask for the backend, SQLAlchemy for data persistence, and HTML5 / Leaflet.js / Chart.js for the interactive frontend. A simulated Kerala road network (40 nodes, 92 edges, 15 charging stations) serves as the test dataset. All 46 unit tests pass.

---

## 2. Introduction

Electric vehicles are rapidly becoming mainstream, but their limited range and longer refuelling time compared to petrol vehicles introduce unique navigation challenges. A driver must not only find the shortest or fastest path but must also plan charging stops to avoid running out of battery — a situation colloquially called "range anxiety."

Traditional GPS navigation systems (Google Maps, etc.) are not designed for this problem. They treat the vehicle as having unlimited range. A true EV navigation system must model the battery as part of the search state, reason about when and where to charge, and optimise for a combination of travel time, charging time, electricity cost, and energy consumption.

This project addresses all of these requirements using classical AI search algorithms and a multi-objective optimisation framework.

---

## 3. Problem Statement

**Given:**
- A road network G = (V, E) where each edge has distance (km), speed (km/h), and traffic factor
- An EV with: battery capacity (kWh), current battery %, efficiency (km/kWh), max charging rate (kW), minimum reserve %
- A set of charging stations, each with: location (node), charging power (kW), price (₹/kWh), availability
- A start node and goal node

**Find:**
- A sequence of (drive, charge) actions from start to goal
- That respects battery constraints at every step
- That minimises a multi-objective cost function

**Constraints:**
- Battery must never drop below the minimum reserve
- Charging can only occur at available stations
- All edges must be traversable (not blocked)

---

## 4. Objectives

1. Implement a working road network graph from a realistic dataset
2. Implement BFS, Dijkstra, Greedy, A*, and Battery-Aware A* algorithms
3. Demonstrate the superiority of A* over other algorithms in terms of nodes explored vs. optimality
4. Build a multi-objective cost function with four optimization modes
5. Implement dynamic rerouting when stations or roads become unavailable
6. Create a professional multi-page web interface connected to a Flask REST API
7. Write comprehensive unit tests

---

## 5. Existing Systems

Existing EV routing solutions include:
- **Google Maps EV routing**: Requires API fees and does not expose algorithm details
- **ABRP (A Better Route Planner)**: Excellent but proprietary, does not allow academic inspection
- **Academic papers**: Several papers propose EV-specific search algorithms, but few have open implementations

This project fills the gap by providing a fully transparent, educational, open implementation of EV route planning algorithms.

---

## 6. Proposed System

A self-contained web application with:
- A simulated road network (Kerala, India)
- Real implemented search algorithms (not mocked)
- A battery-aware state space extending A* to (location, battery%)
- Multi-objective cost optimisation
- Interactive web interface with maps, charts, and algorithm comparison

---

## 7. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Browser (User)                    │
│         HTML + CSS + JS + Leaflet + Chart.js             │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP / JSON
┌───────────────────────▼─────────────────────────────────┐
│                Flask Application (Python)                │
│  routes/main.py (pages) + routes/api.py (REST API)       │
└─────┬──────────┬──────────────────────────┬─────────────┘
      │          │                          │
┌─────▼──┐  ┌───▼────────┐          ┌──────▼──────────┐
│SQLite  │  │Road Graph  │          │ Algorithm Layer │
│SQLAlch │  │(models/    │          │ bfs, dijkstra,  │
│  emy   │  │ graph.py)  │          │ greedy, astar,  │
└────────┘  └───┬────────┘          │ ev_astar        │
                │                   └──────┬──────────┘
           ┌────▼──────┐                  │
           │ EV Model  │◄─────────────────┘
           │(models/   │     Multi-Objective
           │  ev.py)   │     Cost Function
           └───────────┘
```

---

## 8. Methodology

### 8.1 Graph Representation
The road network is stored as a weighted directed graph using an adjacency list:
```
adjacency[node_id][neighbour_id] = {distance, speed, traffic, is_blocked}
```
Node metadata (id, name, lat, lng) is stored separately.

### 8.2 EV State Space
Standard search: `State = location`
EV search: `State = (node_id, battery_percentage)`

Battery is discretised to 5% increments to keep the state space finite.

### 8.3 Actions
- **DRIVE**: Move along an edge if energy_required ≤ usable_energy
- **CHARGE**: At a node with an available station, increase battery to a target level (60%, 70%, 80%, 90%, 100%)

---

## 9. Search Algorithms

### 9.1 BFS (Breadth-First Search)
- Data structure: Queue (FIFO)
- Cost: hop-count only
- Optimality: optimal for unweighted graphs only
- Completeness: complete

**Why it is not ideal for EV routing**: It ignores edge weights (distance, time, energy). A path with 3 hops but 400 km may rank above a path with 5 hops but 150 km.

### 9.2 Dijkstra's Algorithm (Uniform-Cost Search)
- Data structure: Min-heap priority queue
- Cost: accumulated road distance from start g(n)
- Optimality: guaranteed optimal
- Completeness: complete
- Complexity: O((V + E) log V)

### 9.3 Greedy Best-First Search
- Data structure: Min-heap on h(n) only
- Cost: heuristic only (haversine distance to goal)
- Optimality: not guaranteed
- Speed: very fast (explores fewest nodes)

### 9.4 A* Search
`f(n) = g(n) + h(n)`
- g(n) = actual accumulated cost
- h(n) = haversine distance to goal (admissible — never overestimates)
- Optimality: guaranteed (when h is admissible)
- Completeness: complete
- Explores far fewer nodes than Dijkstra due to heuristic guidance

### 9.5 Battery-Aware A* (Core Algorithm)
Extends A* to the (location, battery%) state space.

State transitions:
- DRIVE: `(n, b%) → (n', b' = b - energy/capacity × 100)`
- CHARGE: `(n, b%) → (n, target_b%)`

Heuristic:
`h(state) = haversine_cost(node, goal)` — computed using multi-objective weights, ignoring battery (optimistic, thus admissible)

The algorithm produces a step-by-step timeline:
`Start → Drive → [Charge] → Drive → [Charge] → Destination`

---

## 10. EV Battery Model

```python
class EV:
    battery_capacity    # kWh
    battery_percentage  # %
    efficiency          # km/kWh
    max_charging_power  # kW
    min_reserve         # %

    get_current_energy()    # = capacity × (pct/100)
    get_usable_energy()     # = current - reserve
    get_remaining_range()   # = usable × efficiency
    energy_required(dist)   # = dist / efficiency
    can_travel(dist)        # = usable ≥ energy_required
    charge(target, power)   # returns time + cost
    simulate_drive(dist)    # non-mutating preview
```

---

## 11. Charging Station Model

Each station has:
- `node_id`: which road node it is located at
- `charger_type`: "DC Fast" or "AC"
- `charging_power`: kW output
- `price_per_kwh`: ₹ per kWh

Charging session calculation:
```
effective_power = min(ev.max_charging_power, station.charging_power)
time_h = energy_to_add / effective_power
cost_inr = energy_to_add × price_per_kwh
```

---

## 12. Multi-Objective Cost Function

```
cost = α × (travel_time / T_norm)
     + β × (charge_time / C_norm)
     + γ × (charge_cost / P_norm)
     + δ × (energy / E_norm)
```

| Mode | α | β | γ | δ |
|------|---|---|---|---|
| Fastest | 0.7 | 0.3 | 0.0 | 0.0 |
| Cheapest | 0.1 | 0.1 | 0.8 | 0.0 |
| Eco | 0.1 | 0.0 | 0.0 | 0.9 |
| Balanced | 0.4 | 0.2 | 0.2 | 0.2 |

Normalisation constants ensure no metric dominates due to unit differences.

---

## 13. Implementation

### Backend (Python + Flask)
- `app.py`: Application factory, database seeding
- `routes/api.py`: REST endpoints for route, compare, simulate, reroute
- `routes/main.py`: HTML page routes
- SQLAlchemy ORM with SQLite (easily upgradeable to PostgreSQL)

### Frontend
- Jinja2 template inheritance from `base.html`
- Bootstrap 5 for responsive grid
- Leaflet.js for interactive maps (OpenStreetMap tiles)
- Chart.js for analytics and comparison charts
- Pure Vanilla JS (no React/Vue) for maximum clarity

### Dataset
40 cities in Kerala:
- Kochi, Thrissur, Kozhikode, Thiruvananthapuram, Kottayam, Alappuzha, Kollam, etc.
- 92 directed road connections with realistic distances, speed limits, and traffic factors
- 15 charging stations including DC Fast (up to 200 kW) and AC (11–22 kW)

---

## 14. Results

### Sample Route: Kochi → Thiruvananthapuram (Balanced Mode)

```
Route: Kochi → Alappuzha → Kollam → Attingal → Thiruvananthapuram
Distance: 204 km
Journey Time: ~3h 29m
Charging Stops: 0 (sufficient battery at 80%)
Nodes Explored: 38
Execution Time: 1.6 ms
```

With lower battery (40%), the algorithm automatically adds a charging stop:
```
Route: Kochi → ... → Kollam [Charge: 43%→80%] → ... → Thiruvananthapuram
```

---

## 15. Algorithm Comparison (Kochi → Thiruvananthapuram)

| Algorithm | Nodes Explored | Execution Time | Distance | Optimal? |
|-----------|---------------|----------------|----------|---------|
| BFS | ~38 | ~2 ms | varies | ✗ (hop count only) |
| Dijkstra | ~35 | ~1.5 ms | 204 km | ✅ |
| Greedy | ~15 | ~0.8 ms | varies | ✗ |
| A* | ~30 | ~1.2 ms | 204 km | ✅ |

*A* achieves the same optimal distance as Dijkstra while exploring fewer nodes.*

---

## 16. Testing

46 unit tests across 5 test files:

| File | Tests |
|------|-------|
| test_graph.py | 10 — node/edge creation, neighbours, blocking, haversine |
| test_battery.py | 13 — energy, range, charging, validation |
| test_dijkstra.py | 7 — shortest path, edge cases |
| test_astar.py | 7 — optimality vs Dijkstra, fewer nodes |
| test_ev_astar.py | 9 — charging required, impossible journey, dynamic rerouting |

**Result: 46/46 PASSED**

---

## 17. Limitations

1. Road network is simulated — not a live map
2. Charging station availability is static (no real OCPP integration)
3. Battery discretisation (5% steps) introduces minor suboptimality
4. No user account system
5. Traffic factors are fixed (no real-time traffic)

---

## 18. Future Scope

1. **OpenStreetMap Integration**: Use the Overpass API to load real road networks
2. **OCPP/PlugShare API**: Real-time station availability and pricing
3. **Real-time Traffic**: Google Maps or HERE API for live traffic data
4. **Battery Degradation**: Model capacity loss over charge cycles
5. **Machine Learning**: Predict travel time from historical data
6. **Multi-EV Routing**: Fleet management with shared charging resources
7. **Mobile App**: React Native frontend using the same Flask backend API
8. **Cloud Deployment**: Docker + Gunicorn + PostgreSQL

---

## 19. Conclusion

This project successfully demonstrates the application of classical AI search algorithms to a real-world engineering problem: EV route planning with battery constraints. The battery-aware A* algorithm — the core contribution — correctly plans routes including charging stops, respecting all physical battery constraints, while minimising a configurable multi-objective cost function.

The implementation is clean, modular, and well-tested, making it suitable both as an academic demonstration and as a foundation for a production EV navigation system with real map and API integrations.

The key insight of the project is that EV routing is fundamentally a different problem from standard shortest-path planning: the state space must include the battery level, and the search must reason about charging as a first-class action alongside driving.

---
