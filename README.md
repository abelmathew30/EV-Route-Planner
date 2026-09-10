# ⚡ EV Charging Route Planner

> **AI-Based EV Charging Route Optimization Using Heuristic Search**  


A full-stack web application that finds the optimal electric vehicle route with automated charging stop planning, using real AI search algorithms on a simulated Kerala road network.

---

## 🚀 Features

- **Real AI Search Algorithms**: BFS, Dijkstra, Greedy Best-First, A*, Battery-Aware A*
- **Battery-Aware Routing**: State = (location, battery%) — never strands you without charge
- **Automatic Charging Stops**: Algorithm plans when and where to charge
- **Multi-Objective Optimization**: Fastest / Cheapest / Eco / Balanced modes
- **Dynamic Rerouting**: Simulate station outages and road closures
- **Traffic Simulation**: Adjustable traffic factors on road segments
- **Interactive Maps**: Leaflet.js with real-time route rendering
- **Algorithm Comparison**: Run all algorithms on the same route and compare metrics
- **EV Simulator**: Test battery feasibility for any journey
- **Analytics Dashboard**: Chart.js comparisons across optimization modes

---

## 🏗️ Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, Flask 3 |
| ORM | SQLAlchemy + SQLite |
| Frontend | HTML5, CSS3, Vanilla JS |
| UI Framework | Bootstrap 5 |
| Maps | Leaflet.js + OpenStreetMap |
| Charts | Chart.js 4 |
| Algorithms | Pure Python (BFS, Dijkstra, Greedy, A*, EV A*) |

---

## 📁 Project Structure

```
ev_route_planner/
├── app.py                    # Flask app factory + seed loader
├── config.py                 # Configuration
├── requirements.txt
├── data/
│   └── seed_data.json        # 40 nodes, 92 edges, 15 charging stations
├── models/
│   ├── database.py           # SQLAlchemy ORM models
│   ├── graph.py              # Road network weighted graph
│   ├── ev.py                 # EV battery domain model
│   └── charging_station.py  # Charging station domain model
├── algorithms/
│   ├── bfs.py                # Breadth-First Search
│   ├── dijkstra.py           # Dijkstra / Uniform-Cost Search
│   ├── greedy.py             # Greedy Best-First Search
│   ├── astar.py              # A* Search
│   ├── ev_astar.py           # Battery-Aware A* (core algorithm)
│   └── cost.py               # Multi-objective cost function
├── routes/
│   ├── main.py               # Page routes (8 pages)
│   └── api.py                # REST API endpoints
├── templates/                # Jinja2 HTML templates
│   ├── base.html             # Layout with navbar
│   ├── index.html            # Home page
│   ├── planner.html          # Route Planner
│   ├── results.html          # Route Results
│   ├── stations.html         # Charging Stations
│   ├── ev_simulator.html     # EV Battery Simulator
│   ├── algorithms.html       # Algorithm Explanations
│   ├── comparison.html       # Algorithm Comparison
│   ├── analytics.html        # Analytics Dashboard
│   └── about.html            # About / How It Works
├── static/
│   ├── css/style.css         # Dark-mode custom CSS
│   └── js/                   # Page-specific JavaScript
└── tests/                    # 46 unit tests
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+
- pip

### Steps

```bash
# 1. Navigate to the project directory
cd ev_route_planner

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py
```

The app will start at `http://127.0.0.1:5000`.

On first run, it automatically seeds the SQLite database with the Kerala road network data.

---

## 🌐 Pages

| URL | Page |
|-----|------|
| `/` | Home — project intro, feature cards, flow visual |
| `/planner` | Route Planner — EV config + algorithm selector |
| `/results` | Route Results — map, timeline, metrics |
| `/stations` | Charging Stations — filterable list + map |
| `/ev-simulator` | EV Simulator — battery visualisation + journey check |
| `/algorithms` | Algorithm Explanations — BFS/Dijkstra/Greedy/A* |
| `/comparison` | Algorithm Comparison — side-by-side charts |
| `/analytics` | Analytics — optimization mode trade-offs |
| `/about` | About — architecture, methodology, future scope |

---

## 🔌 API Endpoints

### `GET /api/stations`
Returns all 15 charging stations as JSON.

### `GET /api/graph`
Returns the full road graph (nodes + edges) as JSON.

### `POST /api/route`
Compute battery-aware A* route.

**Request:**
```json
{
  "start": "KCH",
  "goal": "TVM",
  "battery_capacity": 60,
  "battery_pct": 80,
  "efficiency": 6.0,
  "max_charge_power": 150,
  "min_reserve": 10,
  "mode": "balanced"
}
```

**Response:** Path, charging stops, step timeline, all metrics.

### `POST /api/compare`
Run BFS, Dijkstra, Greedy, A* on the same route. Returns all results.

**Request:** `{"start": "KCH", "goal": "TVM"}`

### `POST /api/simulate`
Simulate battery consumption for a given distance.

### `POST /api/reroute`
Dynamic rerouting with blocked nodes/edges.

**Request:**
```json
{
  "start": "KCH", "goal": "TVM",
  "blocked_nodes": ["ATN"],
  "blocked_edges": [["CLR", "ATN"]]
}
```

---

## 🤖 Algorithms

### BFS (Breadth-First Search)
- Explores nodes layer by layer
- Optimal for hop-count only
- Ignores edge weights

### Dijkstra
- Min-heap priority queue on accumulated distance
- Guaranteed shortest distance path
- Complexity: O((V+E) log V)

### Greedy Best-First
- Uses only h(n) = haversine distance to goal
- Very fast, not optimal

### A*
- f(n) = g(n) + h(n)
- Optimal + efficient
- Haversine heuristic is admissible (never overestimates)

### Battery-Aware A* *(core algorithm)*
- State = (node_id, battery_percentage)
- Actions: DRIVE + CHARGE
- Multi-objective cost function with 4 presets
- Auto-plans charging stops

---

## 💰 Optimization Modes

| Mode | α (Time) | β (Charge Time) | γ (Cost) | δ (Energy) |
|------|----------|-----------------|----------|------------|
| Fastest | 0.7 | 0.3 | 0.0 | 0.0 |
| Cheapest | 0.1 | 0.1 | 0.8 | 0.0 |
| Eco | 0.1 | 0.0 | 0.0 | 0.9 |
| Balanced | 0.4 | 0.2 | 0.2 | 0.2 |

All metrics are normalised to [0,1] before weighting.

---

## 📊 Dataset

Fixed seed data (reproducible):
- **40 road nodes** — Kerala cities/junctions with real GPS coordinates
- **92 directed edges** — Distance (km), speed (km/h), traffic factor
- **15 charging stations** — DC Fast & AC, with realistic prices (₹12–₹20/kWh)

---

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

**46 tests covering:**
- Graph construction, neighbours, metrics, blocking
- EV energy, range, charging, validation
- Dijkstra shortest path, no-path, edge cases
- A* optimality vs Dijkstra, fewer nodes explored
- Battery-Aware A*: charging required, impossible journey, dynamic rerouting

---

## 🔮 Future Improvements

1. OpenStreetMap full integration (overpass API)
2. Real charging station API (PlugShare / OCPP)
3. Real-time traffic data
4. Battery degradation model
5. Machine learning for travel time prediction
6. Multi-EV fleet routing
7. Live electricity prices per region
8. Weather-based efficiency adjustment

---

## 📄 License

MIT License — Educational use encouraged.
