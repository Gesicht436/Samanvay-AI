"""
Module 13: Centrifugal Process Pumps & Critical Internals (API 610 / ISO 13709).

Rules:
1. Pump Mounting Configuration (OH1 vs. OH2):
   - For hydrocarbon service > 150°C, substituting an OH1 foot-mounted pump for an OH2
     centerline-mounted pump is blocked as Tier-3 Thermal Shaft Misalignment Trap.
2. API 610 Material Classes:
   - S-1 (Cast Iron) < S-3 (CS) < S-5 (CS/12%Cr) < S-6 (CS/12%Cr sour) < C-6 < A-8 (SS316) < D-1 (Duplex) < D-2 (Super Duplex).
   - Material class downgrade is blocked as Tier-3 Incompatible.
3. Wear Ring Hardness Differential Rule:
   - Per API 610 clause 6.7.2, impeller and casing wear rings must maintain >= 50 HB differential
     to prevent Tier-3 Galling Seizure / Rotor Lockup.
4. Pump Hydraulic & Mechanical Parameters:
   - Flow rate down-rating (flow_rate_m3h candidate < query) = Tier-3 Incompatible.
   - Coupling type mismatch (e.g. Flexible vs Rigid) = Tier-3 Incompatible.
"""

import re
from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


PUMP_MATERIAL_CLASSES = ["S-1", "S-3", "S-5", "S-6", "C-6", "A-8", "D-1", "D-2"]


def _parse_num(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    m = re.search(r'[-+]?\d*\.?\d+', str(val))
    return float(m.group(0)) if m else None


def check_centrifugal_pump(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
    service_temp_c: Optional[float] = None,
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates API 610 pump configuration, material class, wear ring differential, flow rate, and coupling.
    """
    # 1. Flow Rate Down-Rating
    q_flow = _parse_num(query_props.get("flow_rate_m3h") or query_props.get("capacity_m3h"))
    c_flow = _parse_num(cand_props.get("flow_rate_m3h") or cand_props.get("capacity_m3h"))
    if q_flow and c_flow and c_flow < q_flow:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="PUMP_FLOW_RATE",
                standard_code="API 610 Section 6",
                failure_mode_prevented="Process starvation and pump cavitation under undersized delivery rate",
                explanation=f"PUMP FLOW RATE DOWN-RATING: Candidate flow rate {c_flow} m³/h is below required {q_flow} m³/h.",
            ),
        )

    # 2. Coupling Type Mismatch (Flexible vs Rigid)
    q_cpl = str(query_props.get("coupling", "")).upper()
    c_cpl = str(cand_props.get("coupling", "")).upper()
    if q_cpl and c_cpl and q_cpl != c_cpl:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="PUMP_COUPLING",
                standard_code="API 671 / API 610",
                failure_mode_prevented="Shaft misalignment vibration and bearing failure",
                explanation=f"COUPLING TYPE MISMATCH: Query requires '{q_cpl}', candidate has '{c_cpl}'.",
            ),
        )

    # 3. OH1 vs OH2 Centerline Mounting
    q_mount = str(query_props.get("api610_type") or query_props.get("api_mount") or query_props.get("pump_type", "")).upper()
    c_mount = str(cand_props.get("api610_type") or cand_props.get("api_mount") or cand_props.get("pump_type", "")).upper()
    temp = service_temp_c or _parse_num(query_props.get("temp_c")) or _parse_num(query_props.get("operating_temp_c")) or _parse_num(query_props.get("temp"))

    if temp and temp > 150.0 and "OH2" in q_mount and "OH1" in c_mount:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_610_MOUNTING",
                standard_code="API 610 Clause 6.3.3",
                failure_mode_prevented="Thermal shaft misalignment and mechanical seal destruction",
                explanation=f"THERMAL MISALIGNMENT TRAP: Operating temperature is {temp}°C (> 150°C). Foot-mounted pump (OH1) suffers thermal casing growth that shears couplings. Centerline-mounted (OH2) pump is mandatory.",
            ),
        )

    # 4. Material Class Downgrade
    q_mat = str(query_props.get("api_class", "")).upper()
    c_mat = str(cand_props.get("api_class", "")).upper()
    if q_mat in PUMP_MATERIAL_CLASSES and c_mat in PUMP_MATERIAL_CLASSES:
        q_idx = PUMP_MATERIAL_CLASSES.index(q_mat)
        c_idx = PUMP_MATERIAL_CLASSES.index(c_mat)
        if c_idx < q_idx:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="API_610_MATERIAL_CLASS",
                    standard_code="API 610 Annex H",
                    failure_mode_prevented="Pump casing erosion and toxic fluid release",
                    explanation=f"PUMP MATERIAL DOWNGRADE: Candidate Class '{c_mat}' is lower than required Class '{q_mat}'.",
                ),
            )

    # 5. Wear Ring Hardness Differential
    imp_hb = _parse_num(cand_props.get("impeller_wear_ring_hb"))
    cas_hb = _parse_num(cand_props.get("casing_wear_ring_hb"))
    delta_hb = _parse_num(cand_props.get("hardness_delta_hb"))
    if delta_hb is not None and delta_hb < 50.0:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_610_WEAR_RING",
                standard_code="API 610 Clause 6.7.2",
                failure_mode_prevented="Rotating/stationary wear ring galling seizure and rotor lockup",
                explanation=f"WEAR RING GALLING TRAP: Wear ring hardness differential is only {delta_hb} HB. API 610 mandates minimum 50 HB differential.",
            ),
        )

    if imp_hb and cas_hb and abs(imp_hb - cas_hb) < 50.0:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_610_WEAR_RING",
                standard_code="API 610 Clause 6.7.2",
                failure_mode_prevented="Rotating/stationary wear ring galling seizure and rotor lockup",
                explanation=f"WEAR RING GALLING TRAP: Impeller ring ({imp_hb} HB) and casing ring ({cas_hb} HB) differential is only {abs(imp_hb - cas_hb)} HB. API 610 mandates minimum 50 HB differential.",
            ),
        )

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
