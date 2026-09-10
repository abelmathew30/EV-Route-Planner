"""
routes/main.py — Page Routes
Serves all 8 multi-page HTML templates.
"""

from flask import Blueprint, render_template
from models.database import RoadNode, ChargingStation

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Home page."""
    return render_template("index.html")


@main_bp.route("/planner")
def planner():
    """Route planner input page."""
    nodes = RoadNode.query.order_by(RoadNode.name).all()
    return render_template("planner.html", nodes=nodes)


@main_bp.route("/results")
def results():
    """Route results page (populated by JavaScript from API)."""
    return render_template("results.html")


@main_bp.route("/stations")
def stations():
    """Charging stations listing page."""
    import json
    all_stations = ChargingStation.query.all()
    # Pre-serialize to dicts for both the template loop and the JS JSON embed
    stations_data = [s.to_dict() for s in all_stations]
    return render_template("stations.html",
                           stations=stations_data,
                           stations_json=json.dumps(stations_data))


@main_bp.route("/ev-simulator")
def ev_simulator():
    """EV battery simulator page."""
    return render_template("ev_simulator.html")


@main_bp.route("/algorithms")
def algorithms():
    """Algorithm explanations page."""
    return render_template("algorithms.html")


@main_bp.route("/comparison")
def comparison():
    """Algorithm comparison page."""
    nodes = RoadNode.query.order_by(RoadNode.name).all()
    return render_template("comparison.html", nodes=nodes)


@main_bp.route("/analytics")
def analytics():
    """Analytics dashboard page."""
    return render_template("analytics.html")


@main_bp.route("/about")
def about():
    """About / How It Works page."""
    return render_template("about.html")
