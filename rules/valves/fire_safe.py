"""
Module 5 (Part 3 & 4): Valve Fire-Safe Certification, Butterfly Valve Categories & Check Valves.

Standards:
- API 607 / API 6FA / ISO 10497 (Fire Testing)
- API 609 (Butterfly Valves Category A vs Category B)
- API 594 (Check Valves Retainerless Design)
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_fire_safe_and_categories(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
    is_hydrocarbon: bool = False,
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates fire-safe certification, butterfly valve categories, and check valve designs.
    """
    # 1. Fire-Safe Certification (API 607 / API 6FA)
    q_fire = query_props.get("fire_safe", query_props.get("fire_safe_required", is_hydrocarbon))
    c_fire = cand_props.get("fire_safe", cand_props.get("fire_safe_certified", False))
    if "fire_safe" not in cand_props and "api 607" in str(cand_props).lower():
        c_fire = True

    if q_fire and not c_fire:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_607_FIRE_SAFE",
                standard_code="API 607 / API 6FA",
                failure_mode_prevented="Polymer seat melting and fueling refinery hydrocarbon fire",
                explanation=(
                    "HYDROCARBON FIRE DISASTER TRAP: Flammable hydrocarbon service mandates fire-safe "
                    "certified construction (retaining metal-to-metal seal after 30 min at 750°C-1000°C). "
                    "Non-fire-safe soft seated valve proposed."
                ),
            ),
        )

    # 2. API 609 Butterfly Valves (Category A vs Category B)
    q_cat = str(query_props.get("category", "")).upper()
    c_cat = str(cand_props.get("category", "")).upper()
    if "CATEGORY B" in q_cat and "CATEGORY A" in c_cat:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_609_CATEGORY",
                standard_code="API 609",
                failure_mode_prevented="Resilient rubber liner blowout in refinery process service",
                explanation="ELASTOMER BLOWOUT TRAP: Category A concentric resilient-seated valve proposed for Category B high-performance offset duty.",
            ),
        )

    # 3. Check Valve Retainerless Design in Toxic Service (API 594)
    q_toxic = query_props.get("toxic_service", False) or query_props.get("category_m", False)
    c_retainer = cand_props.get("retainerless", True)
    if q_toxic and not c_retainer:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_594_RETAINERLESS",
                standard_code="API 594 clause 4.2",
                failure_mode_prevented="Fugitive pin leak of toxic media through valve body penetrations",
                explanation="FUGITIVE EMISSION TRAP: Toxic fluid service mandates retainerless dual plate check valve design.",
            ),
        )

    # 4. Valve Operation Mismatch (Pneumatic vs Manual)
    q_op = str(query_props.get("operation", "")).upper()
    c_op = str(cand_props.get("operation", "")).upper()
    if q_op and c_op and q_op != c_op:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="VALVE_OPERATION",
                standard_code="API 600 / ISO 5211",
                failure_mode_prevented="Actuator / automation operation mismatch",
                explanation=f"VALVE OPERATION MISMATCH: Query requires '{q_op}', candidate is '{c_op}'.",
            ),
        )

    # 5. End Connection Mismatch
    q_end = str(query_props.get("end_conn", "")).upper()
    c_end = str(cand_props.get("end_conn", "")).upper()
    if q_end and c_end and q_end != c_end:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="VALVE_END_CONNECTION",
                standard_code="ASME B16.5 / B16.25",
                failure_mode_prevented="End connection geometric incompatibility",
                explanation=f"END CONNECTION MISMATCH: Query requires '{q_end}', candidate is '{c_end}'.",
            ),
        )

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
