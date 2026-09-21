import math
from typing import List, Dict, Any

DEPOT_COORDINATES = {
    "OIL Duliajan": (27.3575, 95.3188),
    "Duliajan": (27.3575, 95.3188),
    "OIL Moran": (27.1856, 94.9282),
    "Moran": (27.1856, 94.9282),
    "OIL Digboi": (27.3826, 95.6262),
    "NRL Numaligarh": (26.5982, 93.7543),
    "Numaligarh": (26.5982, 93.7543),
    "ONGC Nazira": (26.9183, 94.7342),
    "Nazira": (26.9183, 94.7342),
    "OIL Guwahati": (26.1855, 91.8214),
    "OIL Jorhat": (26.7509, 94.2037),
    "Jorhat": (26.7509, 94.2037),
    "OIL Jodhpur": (26.2389, 73.0243),
    "Jodhpur": (26.2389, 73.0243),
    "OIL Kakinada": (16.9891, 82.2475),
    "Kakinada": (16.9891, 82.2475),
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
    "Vijaipur": (24.1084, 77.2905)
}

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0 # Earth radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def road_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # 1.28 tortuosity factor
    return haversine_distance(lat1, lon1, lat2, lon2) * 1.28

def estimate_transit_hours(distance_km: float) -> float:
    # 40 km/h average + 4 hours border/loading delays
    return (distance_km / 40.0) + 4.0

def estimate_freight_cost_inr(distance_km: float, weight_kg: float) -> float:
    # CONCOR approx rates: base cost + per km per kg cost
    # Assuming approx 5 INR per km per ton
    weight_tonnes = weight_kg / 1000.0
    return distance_km * weight_tonnes * 5.0

def compute_co2_saved(distance_km: float) -> float:
    # Assuming overseas import is approx 10000 km by sea
    # Sea freight CO2 ~ 10g per ton-km
    # Local road freight CO2 ~ 60g per ton-km
    return max(0.0, (10000 * 10) - (distance_km * 60)) / 1000.0

def get_nearest_depots(depot_id: str, top_n: int = 5) -> List[Dict[str, Any]]:
    if depot_id not in DEPOT_COORDINATES:
        return []
    
    target_lat, target_lon = DEPOT_COORDINATES[depot_id]
    
    distances = []
    for d_id, (lat, lon) in DEPOT_COORDINATES.items():
        if d_id != depot_id:
            dist = road_distance(target_lat, target_lon, lat, lon)
            distances.append({"depot_id": d_id, "distance_km": dist})
            
    distances.sort(key=lambda x: x["distance_km"])
    return distances[:top_n]

def compute_route_summary(source_depot_id: str, target_depot_id: str, weight_kg: float = 1000.0) -> Dict[str, Any]:
    if source_depot_id not in DEPOT_COORDINATES or target_depot_id not in DEPOT_COORDINATES:
        return {}
        
    lat1, lon1 = DEPOT_COORDINATES[source_depot_id]
    lat2, lon2 = DEPOT_COORDINATES[target_depot_id]
    
    dist_km = road_distance(lat1, lon1, lat2, lon2)
    transit_hrs = estimate_transit_hours(dist_km)
    cost = estimate_freight_cost_inr(dist_km, weight_kg)
    co2 = compute_co2_saved(dist_km) * (weight_kg / 1000.0)
    
    return {
        "source": source_depot_id,
        "target": target_depot_id,
        "road_distance_km": round(dist_km, 2),
        "estimated_transit_hours": round(transit_hrs, 2),
        "estimated_freight_cost_inr": round(cost, 2),
        "co2_saved_kg": round(co2, 2)
    }
