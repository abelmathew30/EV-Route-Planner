"""
models/database.py — SQLAlchemy Models
Defines SQLite tables for nodes, edges, and charging stations.
"""

from typing import Any, ClassVar
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class RoadNode(db.Model):  # type: ignore
    """Represents a city/junction in the road network."""
    __tablename__ = "road_nodes"

    query: ClassVar[Any]
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "lat": self.lat,
            "lng": self.lng,
        }


class RoadEdge(db.Model):  # type: ignore
    """Represents a road connection between two nodes."""
    __tablename__ = "road_edges"

    query: ClassVar[Any]
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_node = db.Column(db.String(10), db.ForeignKey("road_nodes.id"), nullable=False)
    to_node = db.Column(db.String(10), db.ForeignKey("road_nodes.id"), nullable=False)
    distance = db.Column(db.Float, nullable=False)   # in km
    speed = db.Column(db.Float, nullable=False)       # in km/h (base speed limit)
    traffic = db.Column(db.Float, default=1.0)        # traffic factor (1.0 = free flow)
    is_blocked = db.Column(db.Boolean, default=False) # for dynamic rerouting

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            "from": self.from_node,
            "to": self.to_node,
            "distance": self.distance,
            "speed": self.speed,
            "traffic": self.traffic,
            "is_blocked": self.is_blocked,
        }


class ChargingStation(db.Model):  # type: ignore
    """Represents an EV charging station."""
    __tablename__ = "charging_stations"

    query: ClassVar[Any]
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    node_id = db.Column(db.String(10), db.ForeignKey("road_nodes.id"), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    charger_type = db.Column(db.String(20), nullable=False)  # "DC Fast" or "AC"
    charging_power = db.Column(db.Float, nullable=False)      # in kW
    price_per_kwh = db.Column(db.Float, nullable=False)       # in INR
    available = db.Column(db.Boolean, default=True)
    num_chargers = db.Column(db.Integer, default=1)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "node_id": self.node_id,
            "lat": self.lat,
            "lng": self.lng,
            "charger_type": self.charger_type,
            "charging_power": self.charging_power,
            "price_per_kwh": self.price_per_kwh,
            "available": self.available,
            "num_chargers": self.num_chargers,
        }



