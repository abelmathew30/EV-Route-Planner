import json
import os
from typing import Any

from flask import Flask
from flask_cors import CORS

from config import Config
from models.database import db, RoadNode, RoadEdge, ChargingStation
from routes.main import main_bp
from routes.api import api_bp


def create_app(config_class: Any = Config) -> Flask:
    """Application factory function."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions
    db.init_app(app)
    CORS(app)

    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Database + seed data initialisation
    with app.app_context():
        db.create_all()
        _seed_database_if_empty(app)

    return app


def _seed_database_if_empty(app: Flask) -> None:
    """
    Load seed data from data/seed_data.json into the SQLite database
    only if the database is empty (first run).
    """
    if db.session.query(RoadNode).count() > 0:
        return  # Already seeded

    seed_path: str = app.config["SEED_DATA_PATH"]
    if not os.path.exists(seed_path):
        print(f"[WARNING] Seed data file not found at {seed_path}")
        return

    with open(seed_path, encoding="utf-8") as f:
        data = json.load(f)

    # Seed nodes
    for n in data.get("nodes", []):
        db.session.add(RoadNode(id=n["id"], name=n["name"], lat=n["lat"], lng=n["lng"]))

    # Seed edges
    for e in data.get("edges", []):
        db.session.add(RoadEdge(
            from_node=e["from"],
            to_node=e["to"],
            distance=e["distance"],
            speed=e["speed"],
            traffic=e.get("traffic", 1.0),
            is_blocked=False,
        ))

    # Seed charging stations
    for s in data.get("charging_stations", []):
        db.session.add(ChargingStation(
            id=s["id"],
            name=s["name"],
            node_id=s["node_id"],
            lat=s["lat"],
            lng=s["lng"],
            charger_type=s["charger_type"],
            charging_power=s["charging_power"],
            price_per_kwh=s["price_per_kwh"],
            available=s["available"],
            num_chargers=s["num_chargers"],
        ))

    db.session.commit()
    print(f"[INFO] Database seeded with {db.session.query(RoadNode).count()} nodes, "
          f"{db.session.query(RoadEdge).count()} edges, "
          f"{db.session.query(ChargingStation).count()} charging stations.")


# Run directly
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)

