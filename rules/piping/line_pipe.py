"""
Module 9: Process Piping Fluid Service Categories & Line Pipe (ASME B31.3 / API 5L).

Rules:
1. API 5L Product Specification Level (PSL 1 vs. PSL 2):
   - PSL 1 lacks mandatory fracture toughness testing.
   - PSL 2 mandates Charpy V-notch toughness, CE ceiling <= 0.43, and traceability.
   - Substituting PSL 1 for PSL 2 in high-pressure transmission gas lines = Tier-3 Brittle Pipeline Rupture Trap.
2. ASME B31.3 Category M Fluid Service (Lethal / Toxic Duty):
   - Threaded joints and commercial non-Cat M components prohibited.
   - Proposing non-Category M components in Category M lines = Tier-3 Lethal Toxic Escape Trap.
3. Manufacturing Method (Seamless vs. Welded):
   - Welded pipe (ERW, LSAW) cannot replace Seamless (SMLS) in high-pressure lethal or hydrogen lines -> Tier-3 Incompatible.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_line_pipe_quality(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates API 5L PSL level, Category M service, and Seamless vs Welded parity.
    """
    # 1. API 5L PSL 1 vs PSL 2
    q_psl = str(query_props.get("psl", "")).upper()
    c_psl = str(cand_props.get("psl", "")).upper()
    if ("PSL 2" in q_psl or "PSL2" in q_psl) and ("PSL 1" in c_psl or "PSL1" in c_psl):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_5L_PSL",
                standard_code="API 5L / ASME B31.8",
                failure_mode_prevented="Brittle pipeline fracture in high-pressure gas grid",
                explanation="BRITTLE PIPELINE RUPTURE TRAP: PSL 1 pipe lacks mandatory fracture toughness testing and cannot replace PSL 2 in gas transmission lines.",
            ),
        )

    # 2. Category M Toxic Fluid Service
    q_cat_m = query_props.get("category_m", False) or query_props.get("lethal_service", False) or "CATEGORY_M" in str(query_props.get("service", "")).upper()
    c_cat_m = cand_props.get("category_m_certified", True)
    q_joint = str(query_props.get("joint", "")).upper()
    c_joint = str(cand_props.get("joint", "")).upper()

    if q_cat_m and ("THREAD" in c_joint or "NPT" in c_joint):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B31_3_CAT_M",
                standard_code="ASME B31.3 Chapter VIII M300",
                failure_mode_prevented="Lethal toxic atmospheric gas escape via threaded joint",
                explanation="CATEGORY M JOINT PROHIBITION: Threaded NPT joints are strictly prohibited in ASME B31.3 Category M lethal fluid service. Full penetration buttweld with 100% radiographic examination is mandatory.",
            ),
        )

    if q_cat_m and not c_cat_m:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B31_3_CAT_M",
                standard_code="ASME B31.3 Chapter VIII",
                failure_mode_prevented="Lethal toxic atmospheric gas escape",
                explanation="LETHAL TOXIC ESCAPE TRAP: Non-Category M component proposed for Category M toxic fluid line. 100% radiographic examination and certified materials are mandatory.",
            ),
        )

    # 3. Seamless vs Welded
    q_mfg = str(query_props.get("mfg") or query_props.get("mfg_method") or query_props.get("manufacturing_method") or "").upper()
    c_mfg = str(cand_props.get("mfg") or cand_props.get("mfg_method") or cand_props.get("manufacturing_method") or "").upper()
    if ("SEAMLESS" in q_mfg or "SMLS" in q_mfg) and ("WELDED" in c_mfg or "ERW" in c_mfg or "LSAW" in c_mfg):
        is_critical = q_cat_m or "H2" in str(query_props.get("service", "")).upper() or "HYDROGEN" in str(query_props.get("service", "")).upper() or query_props.get("hydrogen_service", False) or query_props.get("high_pressure", False)
        if is_critical:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="PIPE_MFG_METHOD",
                    standard_code="ASME B31.3 Section 300",
                    failure_mode_prevented="Longitudinal weld seam rupture in lethal/hydrogen service",
                    explanation="WELD SEAM RUPTURE TRAP: Welded (ERW/LSAW) pipe cannot substitute for Seamless (SMLS) in critical hydrogen or Category M lines.",
                ),
            )
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)

    # Safe upgrade from PSL1 to PSL2
    if ("PSL 1" in q_psl or "PSL1" in q_psl) and ("PSL 2" in c_psl or "PSL2" in c_psl):
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.90, None)

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
