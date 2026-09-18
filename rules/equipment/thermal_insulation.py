"""
Module 21: Thermal Insulation, CUI & Passive Fireproofing (ASTM C795 / ASTM C552 / API 936).

Rules:
1. ASTM C795 Leachable Chloride Invariance (CUI Prevention over Stainless Steel):
   - In environments between 50°C and 150°C, thermal insulation applied over austenitic stainless steel
     or duplex alloys must comply with ASTM C795 (leachable chlorides < 50 ppm with silicate inhibitors).
   - Non-inhibited insulation is blocked as Tier-3 Chloride External Stress Corrosion Cracking (Cl-ESCC) Trap.
2. ASTM C552 Cellular Glass for Cryogenic Duty:
   - Cryogenic liquid piping (-162°C LNG / -42°C Propane) requires 100% closed-cell cellular glass insulation.
   - Fibrous or permeable insulation is blocked as Tier-3 Cryogenic Insulation Shattering Trap.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_thermal_insulation_cui(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
    substrate_material: Optional[str] = None,
    service_temp_c: Optional[float] = None,
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates ASTM C795 CUI leachable chloride compliance and ASTM C552 cryogenic cellular glass.
    """
    mat = (substrate_material or "").upper()
    is_ss_or_duplex = any(m in mat for m in ["SS304", "SS316", "304", "316", "DUPLEX", "2205", "2507"])
    temp = service_temp_c or query_props.get("operating_temp_c")

    # 1. ASTM C795 CUI Prevention
    c_astm_c795 = cand_props.get("astm_c795_compliant", False) or "C795" in str(cand_props).upper()
    c_chlorides = cand_props.get("leachable_chlorides_ppm")

    if is_ss_or_duplex and not c_astm_c795:
        if c_chlorides and float(c_chlorides) > 50.0:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="ASTM_C795_CUI",
                    standard_code="ASTM C795 / NACE SP0198",
                    failure_mode_prevented="Corrosion Under Insulation (CUI) and chloride stress cracking of stainless steel",
                    explanation=f"CL-ESCC CORROSION TRAP: Insulation has {c_chlorides} ppm leachable chlorides without silicate inhibitor. Chloride leaching over austenitic stainless steel causes catastrophic external stress corrosion cracking.",
                ),
            )

    # 2. ASTM C552 Cellular Glass for Cryogenic
    is_cryo = (temp is not None and float(temp) < -29.0) or query_props.get("cryogenic", False)
    c_ins_type = str(cand_props.get("insulation_type", "")).upper()
    if is_cryo and ("MINERAL WOOL" in c_ins_type or "FIBERGLASS" in c_ins_type or "CALCIUM SILICATE" in c_ins_type):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASTM_C552_CRYOGENIC",
                standard_code="ASTM C552",
                failure_mode_prevented="Atmospheric vapor condensation ice-jacking and thermal boil-off runaway",
                explanation="CRYOGENIC INSULATION SHATTERING TRAP: Permeable fibrous insulation allows water vapor ingress at cryogenic temperatures, freezing into ice and destroying thermal insulation.",
            ),
        )

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
