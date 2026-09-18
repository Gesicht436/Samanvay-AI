"""
Module 20: Flange Insulation Kits & Cathodic Protection (NACE SP0286 / NACE SP0169).

Rules:
1. Flange Insulation Kit (FIK) Gasket Configuration (Type E vs Type F):
   - Type F (Raised Face Only): Gasket fits inside bolt circle.
   - Type E (Full Face): Gasket OD matches flange OD with bolt holes pre-punched.
   - Galvanic Bridging Trap: In buried or offshore seawater piping connecting dissimilar metals,
     installing Type F instead of Type E allows conductive mud/water to bridge the outer gap,
     defeating cathodic isolation -> Tier-3 Accelerated Galvanic Perforation Trap.
2. Dielectric Retainer Material Thermal Rating:
   - Phenolic retainers degrade above 100°C.
   - High-temp mandates NEMA G10 (up to 150°C) or NEMA G11 (up to 180°C).
   - Degradation is blocked as Tier-3 Dielectric Breakdown Trap.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_flange_insulation_kit(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
    is_dissimilar_metal: bool = False,
    is_buried_or_subsea: bool = False,
    operating_temp_c: Optional[float] = None,
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates NACE SP0286 Flange Insulation Kit compatibility.
    """
    q_type = str(query_props.get("fik_type") or query_props.get("type", "")).upper()
    c_type = str(cand_props.get("fik_type") or cand_props.get("type", "")).upper()
    is_bimetallic = is_dissimilar_metal or query_props.get("bimetallic", False) or cand_props.get("bimetallic", False)

    # Galvanic bridging check
    if (is_bimetallic or is_buried_or_subsea) and ("TYPE E" in q_type or "FULL_FACE" in q_type or "TYPE_E" in q_type):
        if "TYPE F" in c_type or "RAISED_FACE" in c_type or "TYPE_F" in c_type:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="NACE_SP0286_FIK",
                    standard_code="NACE SP0286",
                    failure_mode_prevented="Conductive debris bridging flange gap causing galvanic perforation",
                    explanation="ACCELERATED GALVANIC PERFORATION TRAP: Type F (raised face) gasket leaves outer flange gap exposed. In buried/subsea dissimilar metal joints, mud bridges the gap, destroying cathodic isolation.",
                ),
            )

    # Dielectric retainer temperature check
    c_retainer = str(cand_props.get("retainer_material", "")).upper()
    temp = operating_temp_c or query_props.get("max_temp_c")
    if temp and float(temp) > 100.0 and ("PHENOLIC" in c_retainer):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="NACE_SP0286_RETAINER",
                standard_code="NACE SP0286",
                failure_mode_prevented="Dielectric retainer thermal breakdown and isolation failure",
                explanation=f"DIELECTRIC BREAKDOWN TRAP: Phenolic retainer degrades above 100°C (service temp is {temp}°C). NEMA G10 or G11 glass epoxy is mandatory.",
            ),
        )

    if q_type == c_type or (not q_type and not c_type):
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.88, None)
