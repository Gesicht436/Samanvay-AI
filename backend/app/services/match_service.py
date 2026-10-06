"""
Match Service: Zero-Mock Matching & Compatibility Pipeline.

Orchestrates the full material matching lifecycle:
1. Query normalization and parameter extraction
2. Multi-strategy candidate retrieval from PostgreSQL
3. Deterministic safety rule evaluation (21 codified rules)
4. ML-based continuous compatibility scoring
5. Logistics computation (Haversine distance, transit time)
6. Attribute-Level Privacy enforcement for cross-CPSE candidates
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union

from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.models.tables import InventoryItem
from ml.ner.normalizer import DialectNormalizer
from ml.ranking.ranker import CompatibilityRanker
from ml.active_learning.cache import ActiveLearningCache
from rules.tolerance import evaluate_pair, ToleranceResult
from graph.logistics import (
    road_distance,
    estimate_transit_hours,
    DEPOT_COORDINATES,
)

logger = logging.getLogger("samanvay.match_service")

# ── Singleton ML instances ─────────────────────────────────────────────────
normalizer = DialectNormalizer()
ranker = CompatibilityRanker()
active_cache = ActiveLearningCache()


# ── 1. Query Normalization ─────────────────────────────────────────────────

def parse_query(payload: Union[Dict[str, Any], Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Normalizes raw search payload into structured query attributes.

    Returns:
        (query_part, normalized_query) where query_part is the fully resolved
        attribute dict for the tolerance engine, and normalized_query is the
        raw NER extraction output for response metadata.
    """
    if hasattr(payload, "model_dump"):
        data = payload.model_dump(exclude_unset=False)
    else:
        data = dict(payload)

    query_text = data.get("query_text", "")
    normalized_query = normalizer.normalize(query_text) if query_text else {}

    raw_item_type = data.get("item_type") or normalized_query.get("item_type")

    # Dimensions & Pressure
    raw_size = data.get("size_nb_mm") or normalized_query.get("size_nb_mm")
    size_nb_mm = float(raw_size) if raw_size is not None and str(raw_size).strip() != "" else None

    raw_pclass = data.get("pressure_class") or normalized_query.get("pressure_class")
    pressure_class = int(raw_pclass) if raw_pclass is not None and str(raw_pclass).strip() != "" else None

    raw_pbar = data.get("pressure_rating_bar")
    pressure_rating_bar = float(raw_pbar) if raw_pbar is not None and str(raw_pbar).strip() != "" else None

    schedule = data.get("schedule") or normalized_query.get("schedule")
    metallurgy = data.get("metallurgy") or normalized_query.get("metallurgy")
    facing_end = data.get("facing_end") or normalized_query.get("facing_end")
    attachment = data.get("attachment")
    standard = data.get("standard") or normalized_query.get("standard")
    indian_standard = data.get("indian_standard") or normalized_query.get("indian_standard")
    oil_std_spec = data.get("oil_std_spec")

    q_props = dict(data.get("properties") or {})

    # Weldability & Chemistry
    weldability_class = data.get("weldability_class")
    if weldability_class == "HIGH_WELDABILITY":
        q_props["ce_max"] = 0.40
        q_props["weldability"] = True
    elif weldability_class == "STANDARD":
        q_props["ce_max"] = 0.43
        q_props["weldability"] = True
    elif weldability_class == "NON_WELDABLE":
        q_props["weldability"] = False

    # Sour Service (NACE MR0175 / ISO 15156)
    if data.get("sour_service"):
        q_props["nace_mr0175"] = True
        q_props["sour_service"] = True
        q_props["hardness_max_hrc"] = 22.0

    # Manufacturing Method
    mfg_method = data.get("mfg_method")
    if mfg_method:
        q_props["mfg"] = mfg_method
        q_props["manufacturing_method"] = mfg_method

    if attachment:
        q_props["attachment"] = attachment
    if data.get("severe_cyclic"):
        q_props["severe_cyclic"] = True

    if data.get("trim_no") is not None and str(data.get("trim_no")).strip() != "":
        try:
            q_props["trim_no"] = int(data.get("trim_no"))
        except (ValueError, TypeError):
            pass
    if data.get("port_bore"):
        q_props["port_bore"] = data.get("port_bore")
    if data.get("piggable"):
        q_props["piggable"] = True
    if data.get("fire_safe_required"):
        q_props["fire_safe"] = True

    query_part = {
        "item_type": raw_item_type or "GENERAL",
        "size_nb_mm": size_nb_mm,
        "pressure_class": pressure_class,
        "pressure_rating_bar": pressure_rating_bar,
        "schedule": schedule,
        "metallurgy": metallurgy,
        "facing_end": facing_end,
        "standard": standard,
        "indian_standard": indian_standard,
        "oil_std_spec": oil_std_spec,
        "properties": q_props,
    }

    return query_part, normalized_query


# ── 2. Candidate Retrieval ─────────────────────────────────────────────────

def _resolve_item_type(raw_item_type: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Maps user-supplied item type to canonical DB enum and optional sub-type filter."""
    if not raw_item_type or raw_item_type == "ALL":
        return None, None

    raw_upper = raw_item_type.upper()
    base_item_type = None
    sub_type_filter = None

    if "VALVE" in raw_upper:
        base_item_type = "VALVE"
        for sub in ("GATE", "BALL", "GLOBE", "CHECK", "BUTTERFLY"):
            if sub in raw_upper:
                sub_type_filter = sub
                break
    elif "FLANGE" in raw_upper:
        base_item_type = "FLANGE"
        for sub in ("WN", "BLIND", "SO"):
            if sub in raw_upper:
                sub_type_filter = sub
                break
    elif "PIPE" in raw_upper:
        base_item_type = "PIPE"
    elif "GASKET" in raw_upper:
        base_item_type = "GASKET"
    elif "FASTENER" in raw_upper or "BOLT" in raw_upper:
        base_item_type = "STUD_BOLT"
    elif "FITTING" in raw_upper:
        base_item_type = "FITTING"
    else:
        base_item_type = raw_upper

    return base_item_type, sub_type_filter


def retrieve_candidates(
    db: Session,
    query_part: Dict[str, Any],
    query_text: str,
    max_candidates: int = 50,
    cpse: Optional[str] = None,
) -> List[InventoryItem]:
    """
    Multi-strategy candidate retrieval using combined OR query instead of
    sequential N+1 queries. Deduplication is handled at the SQL level.

    The caller's CPSE is applied server-authoritatively so that operational
    results are never returned across CPSE boundaries. Client-supplied CPSE
    values (X-CPSE-ID, body fields) are never consulted.
    """
    raw_item_type = query_part.get("item_type")
    size_nb_mm = query_part.get("size_nb_mm")
    metallurgy = query_part.get("metallurgy")
    pressure_class = query_part.get("pressure_class")

    base_item_type, sub_type_filter = _resolve_item_type(raw_item_type)

    # Server-authoritative CPSE boundary (derived by verify_cpse_access).
    # Never client-controlled or tenant-derived from the request payload.
    db_query = db.query(InventoryItem).filter(InventoryItem.cpse == cpse)

    if base_item_type:
        db_query = db_query.filter(InventoryItem.item_type == base_item_type)
    if sub_type_filter:
        db_query = db_query.filter(InventoryItem.description.ilike(f"%{sub_type_filter}%"))

    # Build combined OR filter for multi-strategy retrieval in one query
    or_filters = []
    if size_nb_mm is not None:
        or_filters.append(InventoryItem.size_nb_mm == size_nb_mm)
    if metallurgy:
        or_filters.append(InventoryItem.metallurgy.ilike(f"%{metallurgy}%"))
    if pressure_class:
        or_filters.append(InventoryItem.pressure_class >= pressure_class)
    if query_text and query_text.strip():
        clean_word = query_text.strip().split()[0]
        if len(clean_word) >= 3:
            or_filters.append(InventoryItem.description.ilike(f"%{clean_word}%"))

    if or_filters:
        candidates = db_query.filter(or_(*or_filters)).limit(max_candidates).all()
    else:
        candidates = []

    # Fallback: if too few candidates, fill from general pool
    if len(candidates) < 30:
        seen_skus = {c.sku_code for c in candidates}
        remaining = max_candidates - len(candidates)
        fallback = db_query.limit(remaining + len(seen_skus)).all()
        for item in fallback:
            if item.sku_code not in seen_skus:
                candidates.append(item)
                seen_skus.add(item.sku_code)
                if len(candidates) >= max_candidates:
                    break

    return candidates


# ── 3. Scoring & Evaluation ───────────────────────────────────────────────

def _check_cross_standard_equivalence(
    query_text: str, item: InventoryItem
) -> bool:
    """Detects Indian Standard ↔ International Standard equivalences (BIS/IS ↔ ASTM/ASME/API)."""
    q_upper = query_text.upper() if query_text else ""
    cand_is = item.indian_standard or ""
    cand_met = item.metallurgy or ""
    cand_std = item.standard or ""

    equivalence_map = [
        (("IS 1239", "IS 3589"), ("A106", "API 5L", "IS 1239", "IS 3589")),
        (("IS 2062",), ("A105", "IS 2062")),
        (("IS 14846",), ("API 600", "WCB", "IS 14846")),
        (("IS 1367",), ("B7", "IS 1367")),
    ]

    for query_markers, cand_markers in equivalence_map:
        if any(qm in q_upper for qm in query_markers):
            if any(cm in cand_met or cm in cand_is or cm in cand_std for cm in cand_markers):
                return True

    return False


def _compute_mii_scoring(item: InventoryItem) -> Tuple[float, str, bool, Optional[str]]:
    """
    Computes Make-in-India (PPP-MII) scoring boost and compliance badge.

    Returns:
        (boost, mii_class, mii_compliant, mii_warning)
    """
    local_pct = float(item.local_content_percentage) if item.local_content_percentage is not None else 75.0
    mii_class = item.make_in_india_class or ("Class-I" if local_pct >= 50.0 else "Class-II")
    mii_compliant = local_pct >= 50.0 or mii_class == "Class-I"

    boost = 0.03 if mii_compliant else 0.0
    warning = None if mii_compliant else "Make in India Alert: Local content is below 50% (Class-II / Non-Local)"

    return boost, mii_class, mii_compliant, warning


def _resolve_tier(combined_score: float, is_compatible: bool) -> str:
    """Assigns dynamic compatibility tier from score and rule compatibility."""
    if not is_compatible:
        return "Tier 3"
    if combined_score >= 0.95:
        return "Tier 1"
    if combined_score >= 0.80:
        return "Tier 2"
    return "Tier 3"


def score_candidate(
    query_part: Dict[str, Any],
    query_text: str,
    item: InventoryItem,
) -> Dict[str, Any]:
    """
    Evaluates a single candidate against the query using:
    - 21 deterministic safety rules (70% weight)
    - ML compatibility ranker (30% weight)
    - Indian cross-standard equivalence bonus
    - Make-in-India soft scoring
    - Active Learning cache overrides
    """
    cand_props = dict(item.properties or {})
    cand_part = {
        "item_type": item.item_type,
        "size_nb_mm": float(item.size_nb_mm) if item.size_nb_mm else None,
        "pressure_class": item.pressure_class,
        "pressure_rating_bar": float(item.pressure_rating_bar) if item.pressure_rating_bar else None,
        "pressure_rating_psi": float(item.pressure_rating_psi) if item.pressure_rating_psi else None,
        "schedule": item.schedule,
        "metallurgy": item.metallurgy,
        "facing_end": item.facing_end,
        "standard": item.standard,
        "indian_standard": item.indian_standard,
        "oil_std_spec": item.oil_std_spec,
        "properties": cand_props,
    }

    # 1. Deterministic Safety Evaluation via Rules Core
    rule_eval: ToleranceResult = evaluate_pair(query_part, cand_part)

    # 2. Continuous ML Compatibility Score
    ml_score = ranker.predict(query_part, cand_part)
    combined_score = (rule_eval.score * 0.7) + (ml_score * 0.3)

    # 3. Indian Cross-Standard Equivalence Bonus
    is_equiv = _check_cross_standard_equivalence(query_text, item)
    if is_equiv and rule_eval.is_compatible:
        combined_score = max(combined_score, 0.95)

    # 4. Make in India (PPP-MII) Soft Scoring
    mii_boost, mii_class, mii_compliant, mii_warning = _compute_mii_scoring(item)
    combined_score = min(1.0, combined_score + mii_boost)

    # Invariant: Any zero-tolerance rule violation forces Tier 3
    if not rule_eval.is_compatible:
        combined_score = min(combined_score, 0.74)

    dynamic_tier = _resolve_tier(combined_score, rule_eval.is_compatible)

    # 5. Active Learning Cache Lookup
    cache_entry = active_cache.lookup(query_text, item.sku_code)
    explanation_note = rule_eval.explanation
    if is_equiv:
        explanation_note += " | Dual-Certified: BIS/IS & ASTM/ASME Equivalent"
    if cache_entry:
        explanation_note += f" | {active_cache.sku_stamps.get(item.sku_code, '')}"
        if cache_entry.decision == "APPROVE":
            dynamic_tier = cache_entry.tier_override

    return {
        "combined_score": combined_score,
        "dynamic_tier": dynamic_tier,
        "rule_eval": rule_eval,
        "is_equiv": is_equiv,
        "mii_class": mii_class,
        "mii_compliant": mii_compliant,
        "mii_warning": mii_warning,
        "explanation": explanation_note,
        "local_pct": float(item.local_content_percentage) if item.local_content_percentage is not None else 75.0,
    }


# ── 4. Logistics ──────────────────────────────────────────────────────────

def _resolve_source_coord(cpse: str) -> Tuple[float, float]:
    """Returns the origin depot coordinates for a given CPSE."""
    if cpse == "OIL":
        return DEPOT_COORDINATES.get("OIL Duliajan", (27.3575, 95.3188))
    return DEPOT_COORDINATES.get("Panipat", (29.3909, 76.9635))


def _resolve_target_coord(item: InventoryItem) -> Tuple[float, float]:
    """Returns the target depot coordinates for a candidate item."""
    target_depot = item.depot_location or item.depot_id or "Panipat"
    for name, coord in DEPOT_COORDINATES.items():
        if name.lower() in target_depot.lower():
            return coord
    if "oil" in target_depot.lower() or "duliajan" in target_depot.lower():
        return (27.3575, 95.3188)
    return (22.3217, 73.1384)


def compute_logistics(
    source_coord: Tuple[float, float], item: InventoryItem
) -> Dict[str, float]:
    """Computes road distance and estimated transit hours between depots."""
    target_coord = _resolve_target_coord(item)
    dist = road_distance(source_coord[0], source_coord[1], target_coord[0], target_coord[1])
    transit_hrs = estimate_transit_hours(dist)
    return {"distance_km": round(dist, 1), "transit_hours": round(transit_hrs, 1)}


# ── 5. Response Serialization & Privacy ────────────────────────────────────

def build_candidate_response(
    item: InventoryItem,
    scoring: Dict[str, Any],
    logistics: Dict[str, float],
    requester_cpse: str,
) -> Dict[str, Any]:
    """
    Serializes a scored candidate into the API response format.
    Enforces Attribute-Level Privacy: strips commercial prices for cross-CPSE parts.
    """
    rule_eval = scoring["rule_eval"]

    cand_data = {
        "sku_code": item.sku_code,
        "cpse": item.cpse,
        "depot_id": item.depot_id,
        "depot_location": item.depot_location,
        "description": item.description,
        "item_type": item.item_type,
        "size_nb_mm": float(item.size_nb_mm) if item.size_nb_mm else None,
        "pressure_class": item.pressure_class,
        "pressure_rating_bar": float(item.pressure_rating_bar) if item.pressure_rating_bar else (
            round(item.pressure_class * 0.0689476 * 1.45, 1) if item.pressure_class else None
        ),
        "metallurgy": item.metallurgy,
        "standard": item.standard,
        "indian_standard": item.indian_standard,
        "oil_std_spec": item.oil_std_spec,
        "oil_material_code": item.oil_material_code,
        "gem_category_id": item.gem_category_id,
        "gem_product_id": item.gem_product_id,
        "cppp_tender_ref": item.cppp_tender_ref,
        "make_in_india_class": scoring["mii_class"],
        "local_content_percentage": scoring["local_pct"],
        "mii_compliant": scoring["mii_compliant"],
        "mii_warning": scoring["mii_warning"],
        "quantity": item.quantity,
        "days_idle": item.days_idle,
        "compatibility_score": round(scoring["combined_score"] * 100, 1),
        "tier": scoring["dynamic_tier"],
        "tier_level": 1 if scoring["dynamic_tier"] == "Tier 1" else (2 if scoring["dynamic_tier"] == "Tier 2" else 3),
        "is_compatible": rule_eval.is_compatible,
        "violation_code": rule_eval.rule_violations[0].module_name if rule_eval.rule_violations else None,
        "rule_violations": [
            {
                "module_name": getattr(v, "module_name", "SAFETY_GATE"),
                "standard_code": getattr(v, "standard_code", "ASME/API"),
                "failure_mode": getattr(v, "failure_mode_prevented", "Engineering safety violation"),
                "explanation": getattr(v, "explanation", str(v)),
            }
            for v in rule_eval.rule_violations
        ] if getattr(rule_eval, "rule_violations", None) else [],
        "distance_km": logistics["distance_km"],
        "transit_hours": logistics["transit_hours"],
        "explanation": scoring["explanation"],
    }

    # Strict Attribute-Level Privacy: only expose prices to same-CPSE requesters
    if item.cpse == requester_cpse:
        cand_data["unit_cost_inr"] = float(item.unit_cost_inr) if item.unit_cost_inr else 0.0
        cand_data["total_value_inr"] = float(item.total_value_inr) if item.total_value_inr else 0.0

    return cand_data


# ── 6. Pipeline Orchestrator ──────────────────────────────────────────────

def search_matches(
    payload: Union[Dict[str, Any], Any],
    cpse: str,
    db: Session,
) -> Dict[str, Any]:
    """
    Full Zero-Mock Matching & Compatibility Pipeline orchestrator.

    Steps:
        1. Normalize query text and extract structured specifications.
        2. Retrieve candidates via multi-strategy DB query.
        3. Score each candidate (rules + ML + cross-standard + MII).
        4. Compute logistics for each candidate.
        5. Apply privacy filtering and serialize results.
        6. Sort by compatibility score descending.
    """
    if hasattr(payload, "model_dump"):
        data = payload.model_dump(exclude_unset=False)
    else:
        data = dict(payload)

    query_text = data.get("query_text", "")

    # 1. Parse and normalize
    query_part, normalized_query = parse_query(data)

    # 2. Retrieve candidates
    candidates = retrieve_candidates(db, query_part, query_text, cpse=cpse)

    # 3-5. Score, compute logistics, and serialize
    source_coord = _resolve_source_coord(cpse)
    matched_results = []

    for item in candidates:
        scoring = score_candidate(query_part, query_text, item)
        logistics = compute_logistics(source_coord, item)
        result = build_candidate_response(item, scoring, logistics, cpse)
        matched_results.append(result)

    # 6. Sort descending by compatibility score
    matched_results.sort(key=lambda x: x["compatibility_score"], reverse=True)

    return {
        "query": query_text,
        "normalized_spec": normalized_query,
        "total_candidates_evaluated": len(candidates),
        "candidates": matched_results,
    }
