import math
from collections.abc import Mapping
from typing import Any

from machine_learning.safety import _metallurgy_compatible
from machine_learning.subvectors import DOMAINS


def _attributes(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, str):
        from machine_learning.ner_tagger import _regex_attributes

        return _regex_attributes(value).model_dump()
    raise TypeError("query and candidate must be mappings, material attributes, or descriptions")


def _value_match(query: Any, candidate: Any) -> float:
    if query is None or candidate is None:
        return 0.5
    return float(str(query).strip().casefold() == str(candidate).strip().casefold())


def _attribute_coverage_feature(query: dict[str, Any], candidate: dict[str, Any]) -> float:
    fields = ("item_type", "size_nb_mm", "pressure_class", "metallurgy", "facing_end", "standard")
    shared_fields = sum(
        query.get(field) is not None
        and candidate.get(field) is not None
        and (not isinstance(query.get(field), str) or bool(query[field].strip()))
        and (not isinstance(candidate.get(field), str) or bool(candidate[field].strip()))
        for field in fields
    )
    return shared_fields / len(fields)


def build_features(
    query: Any,
    candidate: Any,
    cosine: float = 0.0,
    domain_scores: Mapping[str, float] | None = None,
) -> list[float]:
    """Build a 13-value reranker vector with a separate cosine for each domain."""
    query_attributes = _attributes(query)
    candidate_attributes = _attributes(candidate)
    query_size = query_attributes.get("size_nb_mm")
    candidate_size = candidate_attributes.get("size_nb_mm")
    query_pressure = query_attributes.get("pressure_class")
    candidate_pressure = candidate_attributes.get("pressure_class")
    query_metallurgy = query_attributes.get("metallurgy") or query_attributes.get("material_grade")
    candidate_metallurgy = candidate_attributes.get("metallurgy") or candidate_attributes.get("material_grade")

    size_match = 0.5 if query_size is None or candidate_size is None else float(math.isclose(float(query_size), float(candidate_size), abs_tol=1e-6))
    pressure_match = 0.5 if query_pressure is None or candidate_pressure is None else float(query_pressure == candidate_pressure)
    pressure_upgrade = 0.5 if query_pressure is None or candidate_pressure is None else float(candidate_pressure >= query_pressure)
    if query_metallurgy is None or candidate_metallurgy is None:
        metallurgy_compatible = 0.5
    else:
        metallurgy_compatible = float(_metallurgy_compatible(str(query_metallurgy), str(candidate_metallurgy)))

    score = max(0.0, min(1.0, float(cosine)))
    domain_features = [
        max(0.0, min(1.0, float(domain_scores.get(domain, score))))
        if domain_scores is not None
        else score
        for domain in DOMAINS
    ]
    return [
        score,
        size_match,
        pressure_match,
        pressure_upgrade,
        metallurgy_compatible,
        _value_match(query_attributes.get("item_type"), candidate_attributes.get("item_type")),
        _value_match(query_attributes.get("facing_end"), candidate_attributes.get("facing_end")),
        _value_match(query_attributes.get("standard"), candidate_attributes.get("standard")),
        _attribute_coverage_feature(query_attributes, candidate_attributes),
        *domain_features,
    ]
