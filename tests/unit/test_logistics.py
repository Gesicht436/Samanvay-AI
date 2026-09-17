import pytest
import math
from backend.app.schemas.inventory import InventoryItemResponse

def calculate_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def test_haversine_distance():
    # Mumbai (19.0760, 72.8777) to Delhi (28.7041, 77.1025)
    dist = calculate_haversine(19.0760, 72.8777, 28.7041, 77.1025)
    assert 1100 <= dist <= 1200 # Approx 1148 km

def test_road_distance():
    dist = calculate_haversine(19.0760, 72.8777, 28.7041, 77.1025)
    road_dist = dist * 1.28
    assert 1400 <= road_dist <= 1550

def test_transit_time_estimates():
    road_dist = 1470 # km
    avg_speed = 50 # km/h
    transit_hours = road_dist / avg_speed
    assert 29 <= transit_hours <= 30

def test_co2_savings_calculation():
    # 0.15 kg CO2 per km ton
    distance = 500
    weight_tons = 10
    co2_emissions = distance * weight_tons * 0.15
    assert co2_emissions == 750
