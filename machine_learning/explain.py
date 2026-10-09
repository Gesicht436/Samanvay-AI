from typing import Any

from machine_learning.reranker.features import build_features


def explain(query: dict[str, Any], candidate: dict[str, Any], model: Any) -> list[str]:
    import numpy as np
    import xgboost as xgb

    features = build_features(
        query,
        candidate,
        float(candidate.get("cosine", candidate.get("similarity", 0.0))),
        candidate.get("domain_scores"),
    )
    matrix = xgb.DMatrix([features])
    contributions = model.get_booster().predict(matrix, pred_contribs=True)[0]
    model_output = model.get_booster().predict(matrix, output_margin=True)[0]
    assert abs(float(np.sum(contributions)) - float(model_output)) <= 1e-6

    reasons: list[str] = []
    query_size, candidate_size = query.get("size_nb_mm"), candidate.get("size_nb_mm")
    if query_size is not None and candidate_size is not None:
        if float(query_size) == float(candidate_size):
            reasons.append(f"✓ Exact size match ({float(candidate_size):.1f} mm)")
        else:
            reasons.append(f"✗ Size mismatch ({query_size} → {candidate_size} mm)")

    query_pressure = query.get("pressure_class")
    candidate_pressure = candidate.get("pressure_class")
    if query_pressure is not None and candidate_pressure is not None:
        if int(candidate_pressure) < int(query_pressure):
            reasons.append(f"✗ Pressure class downgrade ({query_pressure} → {candidate_pressure})")
        elif int(candidate_pressure) > int(query_pressure):
            reasons.append(f"✓ Pressure class upgrade ({query_pressure} → {candidate_pressure})")
        else:
            reasons.append(f"✓ Exact pressure class match ({query_pressure})")

    query_metal = query.get("metallurgy") or query.get("material_grade")
    candidate_metal = candidate.get("metallurgy") or candidate.get("material_grade")
    if query_metal and candidate_metal:
        from machine_learning.safety import _metallurgy_compatible

        marker = "✓" if _metallurgy_compatible(str(query_metal), str(candidate_metal)) else "✗"
        reasons.append(f"{marker} Metallurgy: {query_metal} → {candidate_metal}")
    return reasons
