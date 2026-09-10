"""
models/ev.py — Electric Vehicle Battery Model
Encapsulates battery capacity, efficiency, and range computations.
"""


class EV:
    """
    Models the battery state and energy dynamics of an electric vehicle.

    Parameters
    ----------
    battery_capacity    : total battery capacity in kWh
    battery_percentage  : current state of charge (0–100 %)
    efficiency          : km per kWh the vehicle achieves
    max_charging_power  : maximum AC/DC charging rate accepted (kW)
    min_reserve         : minimum battery % the driver wants to keep (safety buffer)
    """

    def __init__(
        self,
        battery_capacity: float = 60.0,
        battery_percentage: float = 80.0,
        efficiency: float = 6.0,
        max_charging_power: float = 150.0,
        min_reserve: float = 10.0,
    ):
        if battery_capacity <= 0:
            raise ValueError("Battery capacity must be positive.")
        if not (0 <= battery_percentage <= 100):
            raise ValueError("Battery percentage must be between 0 and 100.")
        if efficiency <= 0:
            raise ValueError("Efficiency must be positive.")
        if max_charging_power <= 0:
            raise ValueError("Maximum charging power must be positive.")
        if not (0 <= min_reserve < 100):
            raise ValueError("Minimum reserve must be between 0 and 100.")

        self.battery_capacity = battery_capacity        # kWh
        self.battery_percentage = battery_percentage    # %
        self.efficiency = efficiency                    # km/kWh
        self.max_charging_power = max_charging_power    # kW
        self.min_reserve = min_reserve                  # %

    # ------------------------------------------------------------------
    # Energy state helpers
    # ------------------------------------------------------------------

    def get_current_energy(self) -> float:
        """Current available energy in kWh."""
        return self.battery_capacity * (self.battery_percentage / 100.0)

    def get_usable_energy(self) -> float:
        """Usable energy above the minimum reserve (kWh)."""
        reserve_energy = self.battery_capacity * (self.min_reserve / 100.0)
        return max(0.0, self.get_current_energy() - reserve_energy)

    def get_remaining_range(self) -> float:
        """Maximum range available using *usable* energy (km)."""
        return self.get_usable_energy() * self.efficiency

    def get_total_range(self) -> float:
        """Maximum range from full charge (km)."""
        return self.battery_capacity * self.efficiency

    def energy_required(self, distance_km: float) -> float:
        """Energy (kWh) required to drive a given distance."""
        if distance_km < 0:
            raise ValueError("Distance cannot be negative.")
        return distance_km / self.efficiency

    def can_travel(self, distance_km: float) -> bool:
        """True if the vehicle has enough usable energy for the distance."""
        return self.get_usable_energy() >= self.energy_required(distance_km)

    # ------------------------------------------------------------------
    # State mutation
    # ------------------------------------------------------------------

    def consume_energy(self, kwh: float):
        """
        Reduce battery by the given kWh.
        Raises an error if this would go below the minimum reserve.
        """
        new_energy = self.get_current_energy() - kwh
        min_energy = self.battery_capacity * (self.min_reserve / 100.0)
        if new_energy < min_energy - 1e-6:  # 1e-6 tolerance for floating point
            raise ValueError(
                f"Insufficient energy. Need {kwh:.2f} kWh but only "
                f"{self.get_usable_energy():.2f} kWh usable."
            )
        self.battery_percentage = max(
            self.min_reserve, (new_energy / self.battery_capacity) * 100.0
        )

    def charge(self, target_percentage: float, station_power_kw: float) -> dict:
        """
        Charge battery to a target percentage.

        Returns a dict with:
          - energy_added_kwh
          - charge_time_hours
          - charge_time_minutes
          - cost_inr (requires price_per_kwh to be passed separately)
        """
        if target_percentage <= self.battery_percentage:
            return {
                "energy_added_kwh": 0.0,
                "charge_time_hours": 0.0,
                "charge_time_minutes": 0.0,
            }
        target_percentage = min(target_percentage, 100.0)
        energy_needed = self.battery_capacity * (
            (target_percentage - self.battery_percentage) / 100.0
        )
        # Effective charging rate is limited by both the EV and the station
        effective_power = min(self.max_charging_power, station_power_kw)
        charge_time_hours = energy_needed / effective_power
        self.battery_percentage = target_percentage
        return {
            "energy_added_kwh": round(energy_needed, 3),
            "charge_time_hours": round(charge_time_hours, 4),
            "charge_time_minutes": round(charge_time_hours * 60, 2),
        }

    def simulate_drive(self, distance_km: float) -> dict:
        """
        Simulate driving a distance without mutating state.

        Returns a dict describing the outcome.
        """
        energy_req = self.energy_required(distance_km)
        current = self.get_current_energy()
        usable = self.get_usable_energy()
        possible = usable >= energy_req
        new_percentage = (
            max(self.min_reserve, ((current - energy_req) / self.battery_capacity) * 100)
            if possible
            else None
        )
        return {
            "distance_km": distance_km,
            "energy_required_kwh": round(energy_req, 3),
            "current_energy_kwh": round(current, 3),
            "usable_energy_kwh": round(usable, 3),
            "possible": possible,
            "remaining_battery_pct": round(new_percentage, 2) if possible else None,
            "status": "Journey possible" if possible else "Charging required",
        }

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "battery_capacity": self.battery_capacity,
            "battery_percentage": round(self.battery_percentage, 2),
            "efficiency": self.efficiency,
            "max_charging_power": self.max_charging_power,
            "min_reserve": self.min_reserve,
            "current_energy_kwh": round(self.get_current_energy(), 3),
            "usable_energy_kwh": round(self.get_usable_energy(), 3),
            "remaining_range_km": round(self.get_remaining_range(), 2),
        }
