import re
from typing import Any

_METALLURGY_RANKS = {
    "CARBON": 0,
    "A105": 0,
    "A105N": 0,
    "WCB": 0,
    "A216": 0,
    "LF2": 1,
    "F11": 1,
    "F22": 1,
    "304": 2,
    "304L": 2,
    "SS304": 2,
    "SS304L": 2,
    "316": 2,
    "316L": 2,
    "SS316": 2,
    "SS316L": 2,
    "DUPLEX": 3,
    "2205": 3,
    "SUPER DUPLEX": 4,
    "2507": 4,
    "INCONEL": 5,
    "HASTELLOY": 5,
}


def _metallurgy_rank(value: str) -> int | None:
    normalized = re.sub(r"[^A-Z0-9 ]", " ", value.upper())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    for grade, rank in sorted(_METALLURGY_RANKS.items(), key=lambda item: len(item[0]), reverse=True):
        normalized_grade = re.sub(r"[^A-Z0-9 ]", " ", grade)
        normalized_grade = re.sub(r"\s+", " ", normalized_grade).strip()
        if re.search(rf"(?<![A-Z0-9]){re.escape(normalized_grade)}(?![A-Z0-9])", normalized):
            return rank
    if re.search(r"(?<![A-Z0-9])STAINLESS(?![A-Z0-9])", normalized):
        return 2
    return None


def _metallurgy_compatible(q: str, c: str) -> bool:
    if q.strip().casefold() == c.strip().casefold():
        return True
    query_rank = _metallurgy_rank(q)
    candidate_rank = _metallurgy_rank(c)
    return query_rank is None or candidate_rank is None or candidate_rank >= query_rank


_VALVE_STANDARD_FAMILIES = {
    "594": "check",
    "600": "gate",
    "602": "gate",
    "603": "gate",
    "604": "plug",
    "608": "ball",
    "609": "butterfly",
    "623": "globe",
    "6D": "pipeline",
}


def _valve_standard_family(value: str) -> str | None:
    standard = re.search(r"\bAPI\s*[-.]?\s*(594|600|602|603|604|608|609|623|6D)\b", value, re.IGNORECASE)
    if standard is None:
        return None
    return _VALVE_STANDARD_FAMILIES[standard.group(1).upper()]


def _standard_incompatible(q: str, c: str) -> bool:
    query_family = _valve_standard_family(q)
    candidate_family = _valve_standard_family(c)
    return (
        query_family is not None
        and candidate_family is not None
        and query_family != candidate_family
    )


def _item_type_family(value: str) -> str:
    normalized = re.sub(r"[^A-Z0-9]", "", value.upper())
    if normalized.startswith("FLANGE") or normalized == "FLG":
        return "FLANGE"
    if normalized.startswith("VALVE") or normalized.endswith("VALVE"):
        return "VALVE"
    return normalized


def safety_violations(query: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    query_size, candidate_size = query.get("size_nb_mm"), candidate.get("size_nb_mm")
    if query_size is not None and candidate_size is not None and float(query_size) != float(candidate_size):
        violations.append(f"size mismatch: {query_size} mm vs {candidate_size} mm")

    query_pressure, candidate_pressure = query.get("pressure_class"), candidate.get("pressure_class")
    if query_pressure is not None and candidate_pressure is not None and int(candidate_pressure) < int(query_pressure):
        violations.append(f"pressure downgrade: {query_pressure} to {candidate_pressure}")

    query_metal = query.get("metallurgy") or query.get("material_grade")
    candidate_metal = candidate.get("metallurgy") or candidate.get("material_grade")
    if query_metal and candidate_metal and not _metallurgy_compatible(str(query_metal), str(candidate_metal)):
        violations.append(f"metallurgy downgrade: {query_metal} to {candidate_metal}")

    query_type, candidate_type = query.get("item_type"), candidate.get("item_type")
    if query_type and candidate_type and _item_type_family(str(query_type)) != _item_type_family(str(candidate_type)):
        violations.append(f"item type mismatch: {query_type} vs {candidate_type}")

    query_standard, candidate_standard = query.get("standard"), candidate.get("standard")
    is_valve = any("VALVE" in str(value).upper() for value in (query_type, candidate_type) if value)
    if is_valve and query_standard and candidate_standard and _standard_incompatible(str(query_standard), str(candidate_standard)):
        violations.append(f"incompatible standards: {query_standard} vs {candidate_standard}")
    return violations


def is_safe(query: dict[str, Any], candidate: dict[str, Any]) -> bool:
    return not safety_violations(query, candidate)
