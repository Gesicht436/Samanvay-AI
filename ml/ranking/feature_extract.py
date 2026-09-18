import numpy as np
from typing import Dict, Any


def build_dimensional_vector(attrs: dict) -> np.ndarray:
    nps = attrs.get("NPS") or attrs.get("size_nb_mm") or attrs.get("size") or 0
    if isinstance(nps, str):
        try:
            nps = float(nps.lower().replace("mm", "").replace('"', '').strip())
        except ValueError:
            nps = 0
    return np.array([
        float(nps),
        float(attrs.get("OD", 0) or nps),
        float(attrs.get("Bore", 0) or nps),
        float(attrs.get("PCD", 0)),
        float(attrs.get("N_boltholes", 0)),
        float(attrs.get("Ra", 0)),
    ], dtype=float)


def build_metallurgy_vector(attrs: dict) -> np.ndarray:
    met = attrs.get("metallurgy") or attrs.get("material") or ""
    met_val = float(abs(hash(str(met))) % 1000) if met else 0.0
    return np.array([
        float(attrs.get("C", 0)),
        float(attrs.get("Mn", 0)),
        float(attrs.get("Si", 0)),
        float(attrs.get("P", 0)),
        float(attrs.get("S", 0)),
        float(attrs.get("Cr", 0)),
        float(attrs.get("Mo", 0)),
        float(attrs.get("Ni", 0)),
        float(attrs.get("V", 0)),
        float(attrs.get("Cu", 0)),
        float(attrs.get("CE", 0)),
        float(attrs.get("PREN", 0)),
        float(attrs.get("Charpy", 0) or met_val),
    ], dtype=float)


def build_pressure_temp_vector(attrs: dict) -> np.ndarray:
    p = attrs.get("P_design") or attrs.get("pressure_class") or attrs.get("pressure_rating_psi") or 0
    try:
        p_val = float(p)
    except (ValueError, TypeError):
        p_val = 0.0

    return np.array([
        p_val,
        float(attrs.get("T_min", 0)),
        float(attrs.get("T_max", 0) or (p_val * 2 if p_val else 100.0)),
        float(attrs.get("P_test", 0) or (p_val * 1.5 if p_val else 150.0)),
    ], dtype=float)


def build_standards_vector(attrs: dict) -> np.ndarray:
    item_type = str(attrs.get("item_type", "")).upper()
    type_code = float(abs(hash(item_type)) % 100) if item_type else 1.0
    return np.array([
        float(attrs.get("FireSafe", 0)),
        float(attrs.get("SourNACE", 0)),
        float(attrs.get("Piggable", 0)),
        float(attrs.get("MTC3.1", 1)),
        float(attrs.get("API600", 0)),
        float(attrs.get("ASME_B16.5", 0) or type_code),
    ], dtype=float)


def _cosine_sim(v1: np.ndarray, v2: np.ndarray) -> float:
    if np.array_equal(v1, v2) and not np.all(v1 == 0):
        return 1.0
    if np.all(v1 == 0) or np.all(v2 == 0):
        return 0.0
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    dot = float(np.dot(v1, v2) / (norm1 * norm2))
    return max(0.0, min(1.0, dot))


def compute_subvector_cosines(query_attrs: dict, candidate_attrs: dict) -> Dict[str, float]:
    return {
        "dimensional": _cosine_sim(build_dimensional_vector(query_attrs), build_dimensional_vector(candidate_attrs)),
        "metallurgy": _cosine_sim(build_metallurgy_vector(query_attrs), build_metallurgy_vector(candidate_attrs)),
        "pressure_temp": _cosine_sim(build_pressure_temp_vector(query_attrs), build_pressure_temp_vector(candidate_attrs)),
        "standards": _cosine_sim(build_standards_vector(query_attrs), build_standards_vector(candidate_attrs)),
    }


def build_feature_vector(query: dict, candidate: dict) -> np.ndarray:
    cosines = compute_subvector_cosines(query, candidate)
    return np.array([
        cosines["dimensional"],
        cosines["metallurgy"],
        cosines["pressure_temp"],
        cosines["standards"],
    ], dtype=float)
