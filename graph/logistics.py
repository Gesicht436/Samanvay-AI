"""
Logistics & Spatial Routing Utilities for CPSE Depots across India.
Provides Haversine GIS calculation, road tortuosity distance, transit SLA,
freight cost estimation, and carbon footprint reduction models.

Coordinate Deduplication Policy
--------------------------------
DEPOT_COORDINATES intentionally stores multiple entries that share identical
GPS coordinates (e.g. "OIL Duliajan" and "Duliajan" both resolve to the same
physical depot). These aliases exist to allow callers to look up a depot by
any of its recognised names.

``get_nearest_depots`` deduplicates results using a (lat, lon) key rounded to
4 decimal places (~11 m precision), so that aliases of the same physical
location appear at most once in the output. The entry whose name appears
earliest in the dictionary is kept (insertion-order priority), which makes
the result deterministic across Python 3.7+.

CO₂ Calculation Units
----------------------
``compute_co2_saved_per_tonne`` returns CO₂ savings in **kg CO₂ per tonne of
cargo** for one specific domestic road leg compared with an equivalent
international sea-freight leg of 10,000 km.

Assumptions (not invented — matching the pre-existing formula):
  - International sea freight emission factor:  10 g CO₂ / tonne-km
  - Domestic road freight emission factor:      60 g CO₂ / tonne-km
  - Baseline international leg distance:        10,000 km

Formula:
  savings_per_tonne = max(0, (10_000 km × 10 g/t-km) − (dist_km × 60 g/t-km)) / 1000
                    = max(0, 100 kg − dist_km × 0.06 kg) kg CO₂ / tonne

For long domestic distances (> 1,666 km) the savings become negative (road
transport emits more than the equivalent sea leg). The function clamps to 0.0
in that case rather than returning a negative value.  Callers that need total
savings for a shipment must multiply by the shipment weight in tonnes.

The backward-compatible alias ``compute_co2_saved`` is preserved but deprecated.
"""

import math
import warnings
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Coordinate deduplication precision: round to 4 decimal places (~11 m).
# ---------------------------------------------------------------------------
_COORD_ROUND_DIGITS: int = 4


DEPOT_COORDINATES: Dict[str, Tuple[float, float]] = {
    # OIL India Limited Major Depots
    # "Duliajan" and the long-form alias share coordinates — deduplication
    # inside get_nearest_depots keeps the first entry by insertion order.
    "OIL Duliajan": (27.3575, 95.3188),
    "Duliajan": (27.3575, 95.3188),
    "OIL Central Materials Warehouse, Duliajan, Assam": (27.3575, 95.3188),
    "OIL Moran": (27.1856, 94.9282),
    "Moran": (27.1856, 94.9282),
    "OIL Moran Drilling & Production Supply Base, Charaideo, Assam": (27.1856, 94.9282),
    "OIL Digboi": (27.3826, 95.6262),
    "OIL Digboi Exploration Support Depot, Tinsukia, Assam": (27.3826, 95.6262),
    "OIL Guwahati": (26.1855, 91.8214),
    "OIL Guwahati Pipeline Operations HQ, Kamrup, Assam": (26.1855, 91.8214),
    "OIL Jorhat": (26.7509, 94.2037),
    "Jorhat": (26.7509, 94.2037),
    "OIL Jorhat Subsurface & Logistics Base, Jorhat, Assam": (26.7509, 94.2037),
    "OIL Jodhpur": (26.2389, 73.0243),
    "Jodhpur": (26.2389, 73.0243),
    "OIL Jodhpur Heavy Oil Project Base, Rajasthan": (26.2389, 73.0243),
    "OIL Kakinada": (16.9891, 82.2475),
    "Kakinada": (16.9891, 82.2475),
    "OIL Kakinada KG Basin Offshore Supply Base, Andhra Pradesh": (16.9891, 82.2475),

    # Partner CPSEs (ONGC, IOCL, BPCL, HPCL, GAIL, NRL)
    "NRL Numaligarh": (26.5982, 93.7543),
    "Numaligarh": (26.5982, 93.7543),
    "ONGC Nazira": (26.9183, 94.7342),
    "Nazira": (26.9183, 94.7342),
    "Panipat": (29.3909, 76.9635),
    "Mathura": (27.4924, 77.6737),
    "Koyali": (22.3217, 73.1384),
    "Paradip": (20.3164, 86.6085),
    "Barauni": (25.4714, 85.9990),
    "Guwahati": (26.1445, 91.7362),
    "Digboi": (27.3834, 95.6228),
    "Hazira": (21.1000, 72.6500),
    "Ankleshwar": (21.6263, 73.0025),
    "Uran": (18.8789, 72.9341),
    "Mumbai High": (19.3700, 71.3800),
    "Rajahmundry": (17.0005, 81.8040),
    "Mumbai Mahul": (19.0252, 72.8890),
    "Kochi": (9.9312, 76.2673),
    "Bina": (24.1814, 78.1292),
    "Mumbai": (19.0176, 72.8562),
    "Visakh": (17.6868, 83.2185),
    "Pata": (26.4600, 80.5400),
    "Vijaipur": (24.1084, 77.2905),
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0  # Earth radius in km
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.asin(math.sqrt(a))
    return r * c


def road_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Estimates real-world Indian road distance applying the standard 1.28 tortuosity factor."""
    return haversine_distance(lat1, lon1, lat2, lon2) * 1.28


def estimate_transit_hours(distance_km: float) -> float:
    """Estimates interstate freight transit duration at 40 km/h average + 4 hours logistics/check-post buffer."""
    return (distance_km / 40.0) + 4.0


def estimate_freight_cost_inr(distance_km: float, weight_kg: float) -> float:
    """Estimates freight cost in INR based on CONCOR standard tariff rates (approx INR 5/ton-km)."""
    weight_tonnes = weight_kg / 1000.0
    return distance_km * weight_tonnes * 5.0


def compute_co2_saved_per_tonne(distance_km: float) -> float:
    """
    Computes net CO₂ savings per tonne of cargo (kg CO₂ / tonne) achieved by
    mobilizing domestic CPSE surplus instead of importing via international
    sea freight.

    Assumptions
    -----------
    - Baseline international sea-freight leg: 10,000 km
    - International sea freight emission factor: 10 g CO₂ / tonne-km
    - Domestic road freight emission factor:    60 g CO₂ / tonne-km

    Formula
    -------
    savings_per_tonne = max(0, (10_000 × 10) − (distance_km × 60)) / 1000  [kg CO₂/tonne]

    For distances beyond ~1,667 km the domestic leg emits more than the
    equivalent sea leg; the function clamps to 0.0 (no negative savings).
    To compute total shipment savings multiply by shipment weight in tonnes:
        total_co2_saved_kg = compute_co2_saved_per_tonne(dist_km) * weight_tonnes
    """
    return max(0.0, (10_000.0 * 10.0) - (distance_km * 60.0)) / 1000.0


def compute_co2_saved(distance_km: float) -> float:
    """
    Deprecated alias for ``compute_co2_saved_per_tonne``.

    .. deprecated::
        Use ``compute_co2_saved_per_tonne`` instead. This alias will be
        removed in a future release.
    """
    warnings.warn(
        "compute_co2_saved is deprecated. Use compute_co2_saved_per_tonne instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return compute_co2_saved_per_tonne(distance_km)


def _coord_key(lat: float, lon: float) -> Tuple[float, float]:
    """Returns a rounded (lat, lon) key used for depot deduplication."""
    return (round(lat, _COORD_ROUND_DIGITS), round(lon, _COORD_ROUND_DIGITS))


def get_nearest_depots(depot_id: str, top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Returns the top_n nearest *distinct physical depots* to a given depot_id
    by estimated road distance.

    Deduplication
    -------------
    Multiple dictionary entries that share the same rounded (lat, lon) key
    (see ``_COORD_ROUND_DIGITS``) represent aliases of the same physical depot.
    Only the first alias encountered (insertion order) is included in the
    output to avoid inflating the nearest-depot list with duplicate entries.

    Parameters
    ----------
    depot_id : str
        Key in DEPOT_COORDINATES to use as the origin.
    top_n : int
        Maximum number of distinct neighbouring depots to return.

    Returns
    -------
    List of dicts, each with ``depot_id`` (str) and ``distance_km`` (float),
    sorted ascending by distance. At most ``top_n`` entries are returned.
    Returns an empty list if ``depot_id`` is not found.
    """
    if depot_id not in DEPOT_COORDINATES:
        return []

    target_lat, target_lon = DEPOT_COORDINATES[depot_id]
    target_key = _coord_key(target_lat, target_lon)

    seen_keys: set = {target_key}  # exclude the origin itself
    distances = []

    for d_id, (lat, lon) in DEPOT_COORDINATES.items():
        key = _coord_key(lat, lon)
        if key in seen_keys:
            # Same physical location (either the origin or a duplicate alias)
            continue
        seen_keys.add(key)
        dist = road_distance(target_lat, target_lon, lat, lon)
        distances.append({"depot_id": d_id, "distance_km": round(dist, 2)})

    distances.sort(key=lambda x: (x["distance_km"], x["depot_id"]))
    return distances[:top_n]


def compute_route_summary(
    source_depot_id: str,
    target_depot_id: str,
    weight_kg: float = 1000.0,
) -> Dict[str, Any]:
    """
    Generates route summary metrics between two known CPSE depots.

    The ``co2_saved_kg`` field represents total CO₂ savings for the shipment
    (i.e. savings-per-tonne × shipment weight in tonnes).
    """
    if source_depot_id not in DEPOT_COORDINATES or target_depot_id not in DEPOT_COORDINATES:
        return {}

    lat1, lon1 = DEPOT_COORDINATES[source_depot_id]
    lat2, lon2 = DEPOT_COORDINATES[target_depot_id]

    dist_km = road_distance(lat1, lon1, lat2, lon2)
    transit_hrs = estimate_transit_hours(dist_km)
    cost = estimate_freight_cost_inr(dist_km, weight_kg)
    # Multiply per-tonne savings by shipment weight in tonnes for total savings
    co2 = compute_co2_saved_per_tonne(dist_km) * (weight_kg / 1000.0)

    return {
        "source": source_depot_id,
        "target": target_depot_id,
        "road_distance_km": round(dist_km, 2),
        "estimated_transit_hours": round(transit_hrs, 2),
        "estimated_freight_cost_inr": round(cost, 2),
        "co2_saved_kg": round(co2, 2),
    }
