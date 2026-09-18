"""
Module 17: Atmospheric & Low-Pressure Tank Storage Safety (API 2000 / API 650 / ISO 16852).

Rules:
1. API 2000 Breather Valves / PVRV Sizing:
   - In-breathing flow capacity (Nm³/hr) below calculated liquid pump-out rate
     is blocked as Tier-3 Atmospheric Tank Vacuum Implosion Trap.
2. ISO 16852 Flame & Detonation Arrestors:
   - Substituting an End-of-Line deflagration arrestor inside an in-line flare/vapor recovery header
     is blocked as Tier-3 Supersonic Flame Shock Penetration Trap.
3. Tank Painting / Protective Coating Systems:
   - Painting system mismatch (e.g. Epoxy-Phenolic chemical resistant vs Alkyd utility)
     causes chemical blister and tank corrosion -> Tier-3 Incompatible.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_tank_safety_and_paint(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates API 2000 PVRV venting capacity, ISO 16852 detonation arrestors, and paint systems.
    """
    # 1. API 2000 In-Breathing Flow Capacity
    q_vent = query_props.get("required_scfh") or query_props.get("inbreathing_capacity_nm3h") or query_props.get("venting_capacity_nm3h")
    c_vent = cand_props.get("required_scfh") or cand_props.get("inbreathing_capacity_nm3h") or cand_props.get("venting_capacity_nm3h")
    if q_vent and c_vent:
        try:
            if float(c_vent) < float(q_vent):
                return (
                    DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                    0.0,
                    RuleViolation(
                        module_name="API_2000_PVRV",
                        standard_code="API 2000 7th Edition",
                        failure_mode_prevented="Atmospheric storage tank shell vacuum implosion collapse",
                        explanation=f"TANK VACUUM IMPLOSION TRAP: Candidate in-breathing capacity {c_vent} < required {q_vent}. Liquid pump-out creates vacuum that buckles atmospheric tank walls.",
                    ),
                )
        except (ValueError, TypeError):
            pass

    # 2. ISO 16852 Detonation vs Deflagration Arrestors
    q_arr = str(query_props.get("zone") or query_props.get("arrestor_type", "")).upper()
    c_arr = str(cand_props.get("zone") or cand_props.get("arrestor_type", "")).upper()
    if ("DETONATION" in q_arr or "IN_LINE" in q_arr or "IN-LINE" in q_arr) and ("DEFLAGRATION" in c_arr or "END_OF_LINE" in c_arr or "END-OF-LINE" in c_arr):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ISO_16852_ARRESTOR",
                standard_code="ISO 16852 / EN 12874",
                failure_mode_prevented="Supersonic detonation shock wave propagating into storage tank vapor space",
                explanation="SUPERSONIC FLAME PENETRATION TRAP: End-of-line deflagration arrestor cannot quench supersonic detonation shock waves in closed vapor headers. In-line detonation arrestor is mandatory.",
            ),
        )

    # 3. Tank Painting System Mismatch
    q_paint = str(query_props.get("paint_sys", query_props.get("paint_system", ""))).upper()
    c_paint = str(cand_props.get("paint_sys", cand_props.get("paint_system", ""))).upper()
    if q_paint and c_paint and q_paint != c_paint:
        # Severe mismatch e.g. Epoxy Phenolic vs Alkyd
        if ("EPOXY" in q_paint or "PHENOLIC" in q_paint or "VINYL" in q_paint) and ("ALKYD" in c_paint or "PRIMER" in c_paint):
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="TANK_PAINT_SYSTEM",
                    standard_code="ISO 12944 / NACE SP0108",
                    failure_mode_prevented="Atmospheric corrosion and internal tank lining chemical attack",
                    explanation=f"PAINT SYSTEM MISMATCH: Query specifies chemical-grade '{q_paint}', candidate provides commercial '{c_paint}'. Alkyd coatings dissolve in hydrocarbon/acid vapor.",
                ),
            )
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
