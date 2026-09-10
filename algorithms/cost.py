"""
algorithms/cost.py — Multi-Objective Cost Function
Combines travel time, charging time, charging cost, and energy consumption
into a single weighted scalar that the search algorithms minimise.

Optimisation presets:
  FASTEST   — minimise travel time
  CHEAPEST  — minimise charging cost
  ECO       — minimise energy consumption
  BALANCED  — balanced trade-off
"""


# ------------------------------------------------------------------
# Normalisation constants (used to scale metrics to ~[0, 1])
# These are typical values for the Kerala road dataset.
# ------------------------------------------------------------------
NORM_TRAVEL_TIME_H = 10.0       # max expected driving time (hours)
NORM_CHARGE_TIME_H = 3.0        # max expected total charging time (hours)
NORM_CHARGE_COST_INR = 2000.0   # max expected charging cost (INR)
NORM_ENERGY_KWH = 150.0         # max expected energy use (kWh)


# ------------------------------------------------------------------
# Weight presets  {alpha, beta, gamma, delta}
#   alpha  → travel time weight
#   beta   → charging time weight
#   gamma  → charging cost weight
#   delta  → energy consumption weight
# ------------------------------------------------------------------
PRESETS = {
    "fastest": {
        "alpha": 0.70,
        "beta":  0.30,
        "gamma": 0.00,
        "delta": 0.00,
    },
    "cheapest": {
        "alpha": 0.10,
        "beta":  0.10,
        "gamma": 0.80,
        "delta": 0.00,
    },
    "eco": {
        "alpha": 0.10,
        "beta":  0.00,
        "gamma": 0.00,
        "delta": 0.90,
    },
    "balanced": {
        "alpha": 0.40,
        "beta":  0.20,
        "gamma": 0.20,
        "delta": 0.20,
    },
}


def get_weights(mode: str) -> dict:
    """Return weight dict for a given optimisation mode string."""
    mode = mode.lower().strip()
    if mode not in PRESETS:
        raise ValueError(
            f"Unknown optimisation mode '{mode}'. "
            f"Choose from: {list(PRESETS.keys())}"
        )
    return PRESETS[mode]


def compute_edge_cost(
    travel_time_h: float,
    charging_time_h: float,
    charging_cost_inr: float,
    energy_kwh: float,
    weights: dict,
) -> float:
    """
    Compute the weighted multi-objective cost for a single step/edge.

    All metrics are normalised to [0, 1] before weighting so that
    no single dimension dominates purely because of its unit scale.

    Parameters
    ----------
    travel_time_h    : hours of driving for this step
    charging_time_h  : hours spent charging at this stop (0 if no charging)
    charging_cost_inr: INR spent at this stop (0 if no charging)
    energy_kwh       : kWh consumed during this step
    weights          : dict with keys alpha, beta, gamma, delta

    Returns
    -------
    float : scalar cost ≥ 0
    """
    norm_tt   = travel_time_h    / NORM_TRAVEL_TIME_H
    norm_ct   = charging_time_h  / NORM_CHARGE_TIME_H
    norm_cc   = charging_cost_inr / NORM_CHARGE_COST_INR
    norm_eng  = energy_kwh       / NORM_ENERGY_KWH

    return (
        weights["alpha"]  * norm_tt
        + weights["beta"]   * norm_ct
        + weights["gamma"]  * norm_cc
        + weights["delta"]  * norm_eng
    )


def compute_route_cost(route_stats: dict, mode: str = "balanced") -> float:
    """
    Compute total route cost from a route statistics dictionary.

    route_stats keys (same as returned by ev_astar):
      total_travel_time_h, total_charge_time_h,
      total_charge_cost_inr, total_energy_kwh
    """
    weights = get_weights(mode)
    return compute_edge_cost(
        travel_time_h=route_stats.get("total_travel_time_h", 0),
        charging_time_h=route_stats.get("total_charge_time_h", 0),
        charging_cost_inr=route_stats.get("total_charge_cost_inr", 0),
        energy_kwh=route_stats.get("total_energy_kwh", 0),
        weights=weights,
    )
