import numpy as np
from typing import Dict

def build_dimensional_vector(attrs: dict) -> np.ndarray:
    return np.array([
        attrs.get("NPS", 0),
        attrs.get("OD", 0),
        attrs.get("Bore", 0),
        attrs.get("PCD", 0),
        attrs.get("N_boltholes", 0),
        attrs.get("Ra", 0)
    ], dtype=float)

def build_metallurgy_vector(attrs: dict) -> np.ndarray:
    return np.array([
        attrs.get("C", 0), attrs.get("Mn", 0), attrs.get("Si", 0),
        attrs.get("P", 0), attrs.get("S", 0), attrs.get("Cr", 0),
        attrs.get("Mo", 0), attrs.get("Ni", 0), attrs.get("V", 0),
        attrs.get("Cu", 0), attrs.get("CE", 0), attrs.get("PREN", 0),
        attrs.get("Charpy", 0)
    ], dtype=float)

def build_pressure_temp_vector(attrs: dict) -> np.ndarray:
    return np.array([
        attrs.get("P_design", 0),
        attrs.get("T_min", 0),
        attrs.get("T_max", 0),
        attrs.get("P_test", 0)
    ], dtype=float)

def build_standards_vector(attrs: dict) -> np.ndarray:
    return np.array([
        attrs.get("FireSafe", 0),
        attrs.get("SourNACE", 0),
        attrs.get("Piggable", 0),
        attrs.get("MTC3.1", 0),
        attrs.get("API600", 0),
        attrs.get("ASME_B16.5", 0)
    ], dtype=float)

def _cosine_sim(v1: np.ndarray, v2: np.ndarray) -> float:
    if np.all(v1 == 0) or np.all(v2 == 0):
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

def compute_subvector_cosines(query_attrs: dict, candidate_attrs: dict) -> Dict[str, float]:
    return {
        "dimensional": _cosine_sim(build_dimensional_vector(query_attrs), build_dimensional_vector(candidate_attrs)),
        "metallurgy": _cosine_sim(build_metallurgy_vector(query_attrs), build_metallurgy_vector(candidate_attrs)),
        "pressure_temp": _cosine_sim(build_pressure_temp_vector(query_attrs), build_pressure_temp_vector(candidate_attrs)),
        "standards": _cosine_sim(build_standards_vector(query_attrs), build_standards_vector(candidate_attrs))
    }

def build_feature_vector(query: dict, candidate: dict) -> np.ndarray:
    cosines = compute_subvector_cosines(query, candidate)
    return np.array([
        cosines["dimensional"],
        cosines["metallurgy"],
        cosines["pressure_temp"],
        cosines["standards"]
    ])
