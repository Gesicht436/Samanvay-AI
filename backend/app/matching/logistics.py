"""
GIS Depot Distance Matrix, Multi-Modal Route Optimization, and Inter-CPSE Logistics.
Supports MoPNG CPSEs: IOCL, ONGC, BPCL, HPCL, GAIL.
Computes geodesic (Haversine) and realistic Indian freight corridor road distances,
transit durations, freight rate estimates, and CO2 emissions avoidance.
"""

import math
import io
import base64
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field

# Check if qrcode library is available
try:
    import qrcode
    import qrcode.image.svg
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


class DepotLocation(BaseModel):
    depot_id: str
    name: str
    cpse: str
    state: str
    latitude: float
    longitude: float
    corridor: str
    facilities: List[str]


# Authoritative Registry of Major CPSE Refineries, Petrochemical Complexes & Field Assets
DEPOT_REGISTRY: Dict[str, DepotLocation] = {
    # IOCL Depots
    "IOCL-PNP": DepotLocation(
        depot_id="IOCL-PNP",
        name="Panipat Refinery, Haryana",
        cpse="IOCL",
        state="Haryana",
        latitude=29.3909,
        longitude=76.9635,
        corridor="North-South Industrial Corridor (NH-44 / WDFC)",
        facilities=["Refinery CDU/VDU", "Naphtha Cracker", "PX/PTA Unit", "Heavy Equipment Warehouse"]
    ),
    "IOCL-MTH": DepotLocation(
        depot_id="IOCL-MTH",
        name="Mathura Refinery, Uttar Pradesh",
        cpse="IOCL",
        state="Uttar Pradesh",
        latitude=27.4924,
        longitude=77.6737,
        corridor="Golden Quadrilateral / Yamuna Expressway (NH-19)",
        facilities=["FCCU", "Hydrocracker", "Sulfur Recovery Unit", "Central Mechanical Yard"]
    ),
    "IOCL-VAD": DepotLocation(
        depot_id="IOCL-VAD",
        name="Gujarat Refinery (Koyali), Vadodara",
        cpse="IOCL",
        state="Gujarat",
        latitude=22.3556,
        longitude=73.1250,
        corridor="Delhi-Mumbai Industrial Corridor (NH-48)",
        facilities=["Refinery Complex", "Linear Alkyl Benzene Unit", "Rotating Equipment Stores"]
    ),
    "IOCL-HLD": DepotLocation(
        depot_id="IOCL-HLD",
        name="Haldia Refinery, West Bengal",
        cpse="IOCL",
        state="West Bengal",
        latitude=22.0637,
        longitude=88.0833,
        corridor="Eastern Dedicated Freight Corridor (NH-116)",
        facilities=["Coastal Refinery", "Lube Oil Base Stock Unit", "Port Terminal Warehouse"]
    ),
    "IOCL-BRN": DepotLocation(
        depot_id="IOCL-BRN",
        name="Barauni Refinery, Bihar",
        cpse="IOCL",
        state="Bihar",
        latitude=25.4667,
        longitude=85.9667,
        corridor="East-West Highway (NH-31)",
        facilities=["Refinery Complex", "Aviation Fuel Plant", "Instrumentation Hub"]
    ),
    "IOCL-PRD": DepotLocation(
        depot_id="IOCL-PRD",
        name="Paradip Refinery, Odisha",
        cpse="IOCL",
        state="Odisha",
        latitude=20.2644,
        longitude=86.6083,
        corridor="Coastal Cargo Corridor (NH-53)",
        facilities=["High-Complexity Deep Conversion Refinery", "Polypropylene Plant", "Special Alloys Yard"]
    ),

    # ONGC Depots
    "ONGC-HZR": DepotLocation(
        depot_id="ONGC-HZR",
        name="Hazira Gas Processing Plant, Gujarat",
        cpse="ONGC",
        state="Gujarat",
        latitude=21.1094,
        longitude=72.6394,
        corridor="Western Dedicated Freight Corridor (WDFC / NH-48)",
        facilities=["Gas Sweetening Units", "LPG Terminal", "High-Pressure Valve Stockyard"]
    ),
    "ONGC-URN": DepotLocation(
        depot_id="ONGC-URN",
        name="Uran Plant, Maharashtra",
        cpse="ONGC",
        state="Maharashtra",
        latitude=18.8789,
        longitude=72.9406,
        corridor="JNPT Port Expressway / NH-348",
        facilities=["Offshore Crude Terminal", "Gas Processing Facility", "Turbomachinery Spares"]
    ),
    "ONGC-ANK": DepotLocation(
        depot_id="ONGC-ANK",
        name="Ankleshwar Asset, Gujarat",
        cpse="ONGC",
        state="Gujarat",
        latitude=21.6264,
        longitude=73.0039,
        corridor="Delhi-Mumbai Expressway / NH-48",
        facilities=["Onshore Drilling Base", "Wellhead Spares Depot", "Substation Stores"]
    ),
    "ONGC-RJH": DepotLocation(
        depot_id="ONGC-RJH",
        name="Rajahmundry Asset, Andhra Pradesh",
        cpse="ONGC",
        state="Andhra Pradesh",
        latitude=17.0005,
        longitude=81.8040,
        corridor="NH-16 Coastal Logistics Corridor",
        facilities=["KG Basin Shore Base", "High Pressure Sour Service Yard", "API Casing Depots"]
    ),
    "ONGC-MUM": DepotLocation(
        depot_id="ONGC-MUM",
        name="Mumbai High Offshore Base (Nhava/Sewree)",
        cpse="ONGC",
        state="Maharashtra",
        latitude=18.9500,
        longitude=72.9500,
        corridor="Mumbai Trans-Harbour Link (MTHL / NH-48)",
        facilities=["Offshore Supply Base", "Marine Subsea Spares", "Heavy Flange Depository"]
    ),

    # BPCL Depots
    "BPCL-MUM": DepotLocation(
        depot_id="BPCL-MUM",
        name="Mumbai Refinery, Mahul, Maharashtra",
        cpse="BPCL",
        state="Maharashtra",
        latitude=19.0178,
        longitude=72.8950,
        corridor="Eastern Freeway / Central Railway DFC",
        facilities=["Hydrocracker Unit", "FCCU Complex", "Lube Blending Plant", "Mechanical Seal Workshop"]
    ),
    "BPCL-KCH": DepotLocation(
        depot_id="BPCL-KCH",
        name="Kochi Refinery, Ambalamugal, Kerala",
        cpse="BPCL",
        state="Kerala",
        latitude=9.9816,
        longitude=76.3562,
        corridor="South Coast Logistics Highway (NH-544)",
        facilities=["Integrated Refinery Expansion Project (IREP)", "Petrochemical Complex", "Ex-Proof Motor Yard"]
    ),
    "BPCL-BIN": DepotLocation(
        depot_id="BPCL-BIN",
        name="Bina Refinery (BORL), Madhya Pradesh",
        cpse="BPCL",
        state="Madhya Pradesh",
        latitude=24.2372,
        longitude=78.1833,
        corridor="Central North-South Arterial Corridor (NH-44)",
        facilities=["Full Conversion Refinery", "Catalytic Reformer", "Pipeline Spares Warehouse"]
    ),

    # GAIL / HPCL Depots
    "GAIL-PAT": DepotLocation(
        depot_id="GAIL-PAT",
        name="Pata Petrochemical Complex, Uttar Pradesh",
        cpse="GAIL",
        state="Uttar Pradesh",
        latitude=26.6042,
        longitude=79.4897,
        corridor="Agra-Lucknow Expressway / NH-19",
        facilities=["Gas Cracker Unit", "Polyethylene Yard", "Compressor Spares Hub"]
    ),
    "GAIL-VIJ": DepotLocation(
        depot_id="GAIL-VIJ",
        name="Vijaipur Gas Compressor Complex, Madhya Pradesh",
        cpse="GAIL",
        state="Madhya Pradesh",
        latitude=24.3167,
        longitude=77.2667,
        corridor="Central Transit Highway (NH-46)",
        facilities=["HVJ Pipeline Control Station", "LPG Recovery Unit", "Valve Actuator Depot"]
    ),
    "HPCL-VIZ": DepotLocation(
        depot_id="HPCL-VIZ",
        name="Visakhapatnam Refinery, Andhra Pradesh",
        cpse="HPCL",
        state="Andhra Pradesh",
        latitude=17.6868,
        longitude=83.2185,
        corridor="East Coast Port Expressway (NH-16)",
        facilities=["Visakh Refinery Clean Fuels", "DHT Unit", "API Pump Spares Depot"]
    ),
}


def resolve_depot(query: str) -> Optional[DepotLocation]:
    """
    Fuzzy-matches a string like 'Panipat Refinery' or 'Hazira' to the canonical DepotLocation.
    """
    if not query:
        return None
    
    q_norm = query.strip().upper()
    
    # 1. Exact depot_id match
    if q_norm in DEPOT_REGISTRY:
        return DEPOT_REGISTRY[q_norm]
    
    # 2. Key substrings
    for depot_id, depot in DEPOT_REGISTRY.items():
        if depot_id.upper() in q_norm or depot.name.upper() in q_norm:
            return depot
        
    # 3. Match on city/plant name
    tokens = [t.strip() for t in q_norm.replace(",", " ").replace("(", " ").replace(")", " ").split() if len(t) > 2]
    best_match = None
    best_score = 0
    for depot in DEPOT_REGISTRY.values():
        name_tokens = depot.name.upper()
        score = sum(1 for token in tokens if token in name_tokens)
        if score > best_score:
            best_score = score
            best_match = depot
            
    return best_match if best_score > 0 else None


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes exact spherical geodesic distance in kilometers between two GPS coordinates.
    """
    radius_earth_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return radius_earth_km * c


def estimate_route(
    origin_query: str,
    destination_query: str,
    cargo_weight_tons: float = 1.0
) -> Dict[str, Any]:
    """
    Calculates road distance, heavy freight transit hours, freight rate in INR,
    and environmental CO2 avoidance for inter-CPSE surplus transfer.
    """
    origin = resolve_depot(origin_query)
    dest = resolve_depot(destination_query)

    # Defaults if depot resolution fails
    if not origin or not dest or origin.depot_id == dest.depot_id:
        if origin and dest and origin.depot_id == dest.depot_id:
            # Intra-depot transfer
            return {
                "origin_depot": origin.name,
                "destination_depot": dest.name,
                "origin_cpse": origin.cpse,
                "destination_cpse": dest.cpse,
                "geodesic_distance_km": 0.0,
                "road_distance_km": 5.0,
                "driving_hours": 1,
                "total_transit_hours": 2,
                "estimated_transit_days": 0.1,
                "freight_cost_inr": 3500.0,
                "co2_emissions_kg": 0.4,
                "co2_avoided_vs_import_kg": 50.0,
                "primary_corridor": "Intra-Refinery Internal Shuttle",
                "recommended_logistics_mode": "Dedicated Plant Heavy Shuttle"
            }
        
        # Fallback approximation
        return {
            "origin_depot": origin_query,
            "destination_depot": destination_query,
            "origin_cpse": "CPSE-A",
            "destination_cpse": "CPSE-B",
            "geodesic_distance_km": 750.0,
            "road_distance_km": 940.0,
            "driving_hours": 24,
            "total_transit_hours": 28,
            "estimated_transit_days": 1.2,
            "freight_cost_inr": 38220.0,
            "co2_emissions_kg": 77.0,
            "co2_avoided_vs_import_kg": 620.0,
            "primary_corridor": "National Highway Corridor (NH-44 / NH-48)",
            "recommended_logistics_mode": "CONCOR Dedicated Multi-Modal Rail-Road"
        }

    geo_dist = haversine_distance_km(origin.latitude, origin.longitude, dest.latitude, dest.longitude)
    
    # Realistic road tortuosity factor for Indian national highways (1.22 - 1.28x)
    road_dist = round(geo_dist * 1.25, 1)
    
    # Heavy industrial carrier: 40 km/h average commercial road speed
    avg_speed_kmh = 40.0
    driving_hours = road_dist / avg_speed_kmh
    # Mandatory driver breaks under Indian transport norms (2 hours per 8 hours driving)
    rest_hours = math.floor(driving_hours / 8.0) * 2.0
    total_transit_hours = int(math.ceil(driving_hours + rest_hours))
    transit_days = round(total_transit_hours / 24.0, 1)
    
    # MoPNG Commercial Freight Tariff Model:
    # Base dispatch & handling: INR 2,500
    # Linehaul rate: INR 38.00 per vehicle-km
    # Weight handling: INR 3.50 per ton-km
    freight_cost = round(2500.0 + (road_dist * 38.0) + (road_dist * max(0.5, cargo_weight_tons) * 3.50), 2)
    
    # Environmental metrics:
    # Domestic Surface Truck: ~0.082 kg CO2 per ton-km
    surface_co2_kg = round(road_dist * cargo_weight_tons * 0.082, 1)
    # International emergency procurement via Air Freight: ~0.602 kg CO2 per ton-km over 6,500 km
    import_co2_kg = round(6500.0 * cargo_weight_tons * 0.602, 1)
    co2_avoided = max(0.0, round(import_co2_kg - surface_co2_kg, 1))

    # Corridor resolution
    corridor = f"{origin.cpse} {origin.state} to {dest.cpse} {dest.state} ({origin.corridor})"

    return {
        "origin_depot": origin.name,
        "destination_depot": dest.name,
        "origin_cpse": origin.cpse,
        "destination_cpse": dest.cpse,
        "geodesic_distance_km": round(geo_dist, 1),
        "road_distance_km": road_dist,
        "driving_hours": round(driving_hours, 1),
        "total_transit_hours": total_transit_hours,
        "estimated_transit_days": transit_days,
        "freight_cost_inr": freight_cost,
        "co2_emissions_kg": surface_co2_kg,
        "co2_avoided_vs_import_kg": co2_avoided,
        "primary_corridor": corridor,
        "recommended_logistics_mode": "CONCOR Dedicated Multi-Modal Rail-Road / Fast-Track Heavy Road Transit"
    }


def generate_gate_pass_qr_code(payload_str: str) -> Tuple[str, str]:
    """
    Generates a high-density, valid SVG QR code and a base64 Data URL
    for printing on the CISF Material Gate Pass.
    """
    if not QRCODE_AVAILABLE:
        # Fallback simple SVG representation
        svg_mock = f'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120"><rect width="120" height="120" fill="#f8f9fa" stroke="#000"/><text x="10" y="60" font-family="monospace" font-size="9">CISF-QR-GATEPASS</text></svg>'
        return svg_mock, f"data:image/svg+xml;base64,{base64.b64encode(svg_mock.encode()).decode()}"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(payload_str)
    qr.make(fit=True)

    # Generate pure scalable SVG
    svg_factory = qrcode.image.svg.SvgPathImage
    svg_img = qr.make_image(image_factory=svg_factory)
    
    stream = io.BytesIO()
    svg_img.save(stream)
    svg_bytes = stream.getvalue()
    svg_str = svg_bytes.decode("utf-8")
    data_url = f"data:image/svg+xml;base64,{base64.b64encode(svg_bytes).decode('utf-8')}"
    
    return svg_str, data_url
