"""
models/charging_station.py — Charging Station Model
Domain object (not SQLAlchemy) used by search algorithms.
"""


class ChargingStationModel:
    """
    Pure-Python domain object representing a charging station.
    Decoupled from SQLAlchemy so algorithms can use it independently.

    Parameters
    ----------
    station_id      : unique identifier (e.g. "CS001")
    name            : human-readable name
    node_id         : road-graph node where the station is located
    lat, lng        : GPS coordinates
    charger_type    : "DC Fast" or "AC"
    charging_power  : kW output of the station
    price_per_kwh   : cost in INR per kWh
    available       : whether the station is currently operational
    num_chargers    : total charging ports
    """

    def __init__(
        self,
        station_id: str,
        name: str,
        node_id: str,
        lat: float,
        lng: float,
        charger_type: str,
        charging_power: float,
        price_per_kwh: float,
        available: bool = True,
        num_chargers: int = 1,
    ):
        self.id = station_id
        self.name = name
        self.node_id = node_id
        self.lat = lat
        self.lng = lng
        self.charger_type = charger_type
        self.charging_power = charging_power   # kW
        self.price_per_kwh = price_per_kwh     # INR
        self.available = available
        self.num_chargers = num_chargers

    # ------------------------------------------------------------------
    # Charging calculations
    # ------------------------------------------------------------------

    def calculate_charging_time_hours(
        self, energy_kwh: float, ev_max_power_kw: float
    ) -> float:
        """
        Charging time in hours to add *energy_kwh* to the battery.

        The effective rate is limited by both the EV's onboard charger
        and the station's output power.
        """
        effective_power = min(self.charging_power, ev_max_power_kw)
        if effective_power <= 0:
            return float("inf")
        return energy_kwh / effective_power

    def calculate_charging_cost_inr(self, energy_kwh: float) -> float:
        """Total cost in INR to add *energy_kwh*."""
        return energy_kwh * self.price_per_kwh

    def charging_session(
        self,
        from_pct: float,
        to_pct: float,
        battery_capacity_kwh: float,
        ev_max_power_kw: float,
    ) -> dict:
        """
        Full charging session summary.

        Parameters
        ----------
        from_pct            : starting battery %
        to_pct              : target battery %
        battery_capacity_kwh: EV's total battery capacity
        ev_max_power_kw     : EV's maximum accepted charging rate

        Returns
        -------
        dict with energy_added_kwh, time_hours, time_minutes, cost_inr
        """
        energy_added = battery_capacity_kwh * ((to_pct - from_pct) / 100.0)
        if energy_added <= 0:
            return {
                "energy_added_kwh": 0.0,
                "time_hours": 0.0,
                "time_minutes": 0.0,
                "cost_inr": 0.0,
            }
        time_hours = self.calculate_charging_time_hours(energy_added, ev_max_power_kw)
        cost_inr = self.calculate_charging_cost_inr(energy_added)
        return {
            "energy_added_kwh": round(energy_added, 3),
            "time_hours": round(time_hours, 4),
            "time_minutes": round(time_hours * 60, 2),
            "cost_inr": round(cost_inr, 2),
        }

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
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

    def __repr__(self):
        status = "Available" if self.available else "Unavailable"
        return (
            f"<ChargingStation {self.id} | {self.name} | "
            f"{self.charger_type} {self.charging_power}kW | {status}>"
        )
