"""
Module 12: Heat Exchanger Bundles & Tubing (TEMA Standards & ASME Section VIII Div 1/2).

Rules:
1. TEMA Construction Class Hierarchy:
   - TEMA R (Severe petroleum processing) > TEMA C (General commercial) > TEMA B (Chemical process).
   - Proposing TEMA C or B for TEMA R is blocked as Tier-3 Heat Exchanger Premature Failure Trap.
2. Seamless vs. Welded Heat Exchanger Tubing:
   - Welded tubes (ASTM A249) cannot replace Seamless (ASTM A213) in reboilers and critical exchangers
     -> Tier-3 Weld Seam Fatigue / Corrosion Rupture Trap.
3. Wall Thickness Gauge (BWG) Minimum Wall (MW) vs. Average Wall (AW):
   - Substituting AW when MW is specified causes local under-gauge thin spots -> Tier-3 Tube Buckling Trap.
4. U-Bend Solution Annealing (TEMA R RCB-2.31):
   - Un-annealed cold-worked U-bends suffer residual forming stress -> Tier-3 Chloride Stress Corrosion Cracking (Cl-SCC).
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


TEMA_HIERARCHY = ["TEMA B", "TEMA C", "TEMA R"]


def check_heat_exchanger_tubes(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates TEMA class, seamless tubing, BWG wall specification, and U-bend heat treatment.
    """
    # 1. TEMA Class
    q_tema = str(query_props.get("tema_class", "")).upper()
    c_tema = str(cand_props.get("tema_class", "")).upper()
    if q_tema in TEMA_HIERARCHY and c_tema in TEMA_HIERARCHY:
        if TEMA_HIERARCHY.index(c_tema) < TEMA_HIERARCHY.index(q_tema):
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="TEMA_CLASS_DOWNGRADE",
                    standard_code="TEMA Standards 10th Edition",
                    failure_mode_prevented="Heat exchanger bundle erosion, baffle clearance bypass and premature failure",
                    explanation=f"TEMA CLASS DOWNGRADE TRAP: Candidate '{c_tema}' is inferior to required '{q_tema}' refinery standard.",
                ),
            )

    # 2. Seamless vs Welded Exchanger Tubes
    q_tube_mfg = str(query_props.get("tube_mfg", query_props.get("mfg_method", ""))).upper()
    c_tube_mfg = str(cand_props.get("tube_mfg", cand_props.get("mfg_method", ""))).upper()
    if ("SEAMLESS" in q_tube_mfg or "A213" in q_tube_mfg) and ("WELDED" in c_tube_mfg or "A249" in c_tube_mfg):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="HE_SEAMLESS_TUBE",
                standard_code="ASME Section VIII Div 1 / TEMA",
                failure_mode_prevented="Longitudinal weld seam stress corrosion cracking and shell-side blowout",
                explanation="WELD SEAM RUPTURE TRAP: Welded tubes (ASTM A249) cannot substitute for seamless (ASTM A213) in refinery reboilers.",
            ),
        )

    # 3. BWG Minimum Wall vs Average Wall
    q_bwg_type = str(query_props.get("wall_basis", "")).upper()
    c_bwg_type = str(cand_props.get("wall_basis", "")).upper()
    if ("MIN" in q_bwg_type or "MW" in q_bwg_type) and ("AVG" in c_bwg_type or "AW" in c_bwg_type):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="TUBE_BWG_MIN_WALL",
                standard_code="TEMA Standards RCB-2.21",
                failure_mode_prevented="External tube buckling collapse from under-gauge wall thickness",
                explanation="TUBE BUCKLING TRAP: Average Wall (AW) tubing creates local under-gauge spots where Minimum Wall (MW) is specified.",
            ),
        )

    # 4. U-Bend Solution Annealing
    is_u_tube = query_props.get("u_tube", False) or "U-TUBE" in str(query_props).upper()
    c_annealed = cand_props.get("u_bend_annealed", True)
    if is_u_tube and not c_annealed:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="TEMA_U_BEND_ANNEALING",
                standard_code="TEMA R RCB-2.31 / ASTM A688",
                failure_mode_prevented="Chloride stress corrosion cracking in residual stress U-bend zone",
                explanation="CL-SCC U-BEND TRAP: Cold-worked stainless U-bends mandate solution heat treatment to relieve residual forming stress.",
            ),
        )

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
