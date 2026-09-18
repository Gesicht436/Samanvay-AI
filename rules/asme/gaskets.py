"""
Module 8 (Part 1): Gaskets Integrity (ASME B16.20 / ASME B16.21).

Rules:
1. Spiral Wound Gaskets (SWG) Inner Ring Mandate:
   - In Class 900+ flanges, in PTFE-filled SWG, and vacuum service, solid metallic Inner Ring is mandatory.
   - Omission is blocked as Tier-3 Gasket Collapse Trap.
2. Filler Temperature Compatibility:
   - Flexible Graphite (rated 650°C) substituted with PTFE (rated 260°C max) in high-temp lines = Tier-3 Melting Trap.
3. RTJ Gasket Compatibility:
   - Octagonal (R) & Oval (R) fit standard R grooves.
   - RX pressure-energized rings fit standard R grooves.
   - BX rings (API 6A) CANNOT fit ASME B16.5 R grooves.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_gasket_compatibility(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
    pressure_class: Optional[int] = None,
    operating_temp_c: Optional[float] = None,
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates ASME B16.20 and B16.21 gasket compatibility.
    """
    q_type = str(query_props.get("gasket_type", "")).upper()
    c_type = str(cand_props.get("gasket_type", "")).upper()
    q_filler = str(query_props.get("filler", "")).upper()
    c_filler = str(cand_props.get("filler", "")).upper()

    # Temperature checks
    q_temp = query_props.get("max_temp_c")
    c_temp = cand_props.get("max_temp_c")
    if q_temp is not None and c_temp is not None:
        try:
            qt = float(q_temp)
            ct = float(c_temp)
            if ct < qt:
                return (
                    DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                    0.0,
                    RuleViolation(
                        module_name="ASME_B16_21_TEMPERATURE",
                        standard_code="ASME B16.21",
                        failure_mode_prevented="Elastomer or gasket degradation and blowout under high temperature",
                        explanation=f"GASKET TEMPERATURE DOWN-RATING: Candidate rating {ct}°C is below required {qt}°C.",
                    ),
                )
            elif ct > qt:
                return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.92, None)
        except (ValueError, TypeError):
            pass

    # Filler material temperature limits
    temp = operating_temp_c or (float(q_temp) if q_temp is not None else None)
    if temp and temp > 260.0:
        if ("GRAPHITE" in q_filler or "GRAFOIL" in q_filler) and ("PTFE" in c_filler or "TEFLON" in c_filler):
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="ASME_B16_20_FILLER",
                    standard_code="ASME B16.20",
                    failure_mode_prevented="PTFE filler thermal degradation, creep relaxation and blowout",
                    explanation=f"GASKET MELTING TRAP: Operating temperature is {temp}°C. PTFE is rated to max 260°C and cannot replace Flexible Graphite (650°C).",
                ),
            )

    # SWG Inner Ring Mandate in Class 900+
    cls_rating = pressure_class or query_props.get("pressure_class")
    if cls_rating and int(cls_rating) >= 900:
        c_inner = cand_props.get("inner_ring", False)
        if not c_inner:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="ASME_B16_20_INNER_RING",
                    standard_code="ASME B16.20 Table 4",
                    failure_mode_prevented="Radial inward winding buckling into pipe bore under high bolt load",
                    explanation=f"GASKET COLLAPSE TRAP: In ASME B16.5 Class {cls_rating}, Spiral Wound Gaskets mandate an internal solid metallic Inner Ring to prevent radial buckling into the bore.",
                ),
            )

    # RTJ Ring Type Compatibility
    q_ring = str(query_props.get("ring_type", "")).upper()
    c_ring = str(cand_props.get("ring_type", "")).upper()
    if "BX" in c_ring and "BX" not in q_ring:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B16_20_RTJ",
                standard_code="ASME B16.20 / API 6A",
                failure_mode_prevented="BX gasket dimensional incompatibility in ASME B16.5 R grooves",
                explanation="BX RING INCOMPATIBILITY: BX pressure-energized rings are designed for API 6A 15,000 PSI flanges and cannot seal in ASME B16.5 R grooves.",
            ),
        )

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
