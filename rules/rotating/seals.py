"""
Module 11 (Part 2): API 682 Mechanical Seals, Piping Flush Plans & Elastomers.

Rules:
1. API 682 Piping Flush Plans (Single vs. Dual Pressurized):
   - Dual pressurized barrier systems (Plan 53A, Plan 53B, Plan 54) maintain barrier fluid > process pressure.
   - Downgrading to a single unpressurized seal (Plan 11, 21, 32) in toxic, carcinogenic, or light hydrocarbon service
     is blocked as Tier-3 Toxic Atmosphere Seal Blowout Trap.
2. Compressor Seal Plans:
   - Downgrading Plan 53B to Plan 52 in pressurized gas service = Tier-3 Incompatible.
3. Elastomer O-Ring Materials:
   - Viton (FKM, up to 200°C, chemical resistant) downgraded to NBR (Nitrile, 100°C max) = Tier-3 Incompatible.
   - NBR upgraded to Viton = Tier-2 Substitute.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


DUAL_PRESSURIZED_PLANS = {"PLAN 53A", "PLAN 53B", "PLAN 53C", "PLAN 54"}
SINGLE_UNPRESSURIZED_PLANS = {"PLAN 11", "PLAN 12", "PLAN 21", "PLAN 23", "PLAN 31", "PLAN 32", "PLAN 52"}

ELASTOMER_RANKING = {
    "NBR": 1,
    "NITRILE": 1,
    "EPDM": 2,
    "VITON": 3,
    "FKM": 3,
    "FFKM": 4,
    "KALREZ": 4,
}


def check_mechanical_seal_and_elastomer(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates API 682 flush plans, compressor barrier plans, and elastomer seal materials.
    """
    # 1. API 682 Flush Plan Downgrade
    import re
    raw_q = str(query_props.get("plan") or query_props.get("seal_plan") or query_props.get("api_plan", "")).upper().strip().replace("_", " ")
    raw_c = str(cand_props.get("plan") or cand_props.get("seal_plan") or cand_props.get("api_plan", "")).upper().strip().replace("_", " ")
    q_plan = re.sub(r'\s+', ' ', raw_q)
    c_plan = re.sub(r'\s+', ' ', raw_c)
    if q_plan and not q_plan.startswith("PLAN"):
        q_plan = f"PLAN {q_plan}"
    if c_plan and not c_plan.startswith("PLAN"):
        c_plan = f"PLAN {c_plan}"

    is_toxic = query_props.get("toxic_service", False) or query_props.get("carcinogenic", False) or query_props.get("category_m", False) or "H2S" in str(query_props).upper()

    if q_plan and c_plan and q_plan != c_plan:
        is_q_dual = any(p in q_plan for p in DUAL_PRESSURIZED_PLANS) or "53" in q_plan or "DUAL" in q_plan
        is_c_single = any(p in c_plan for p in SINGLE_UNPRESSURIZED_PLANS) or "11" in c_plan or "SINGLE" in c_plan

        if is_q_dual and is_c_single:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="API_PLAN_DOWNGRADE",
                    standard_code="API 682 4th Edition",
                    failure_mode_prevented="Toxic or carcinogenic volatile hydrocarbon atmospheric seal blowout due to API plan downgrade",
                    explanation=f"API PLAN DOWNGRADE TRAP: Candidate {c_plan} (single unpressurized seal) proposed for {q_plan} (dual pressurized barrier system). In toxic/VOC hydrocarbon lines, barrier fluid pressure must exceed seal chamber pressure.",
                ),
            )
        elif not is_q_dual and not is_c_single and (any(p in c_plan for p in DUAL_PRESSURIZED_PLANS) or "53" in c_plan):
            return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.90, None)
        elif "53B" in q_plan and "52" in c_plan:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="API_682_COMPRESSOR_PLAN",
                    standard_code="API 682 / API 692",
                    failure_mode_prevented="Compressor barrier fluid pressure loss and gas escape",
                    explanation=f"API PLAN DOWNGRADE TRAP: Candidate {c_plan} cannot replace pressurized accumulator system {q_plan}.",
                ),
            )

    # 2. Elastomer Seal Material (O-Ring)
    q_mat = str(query_props.get("material", query_props.get("seal_material", ""))).upper()
    c_mat = str(cand_props.get("material", cand_props.get("seal_material", ""))).upper()

    q_rank = next((v for k, v in ELASTOMER_RANKING.items() if k in q_mat), None)
    c_rank = next((v for k, v in ELASTOMER_RANKING.items() if k in c_mat), None)

    if q_rank is not None and c_rank is not None:
        if c_rank < q_rank:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="SEAL_MATERIAL_DOWNGRADE",
                    standard_code="API 682 Annex B",
                    failure_mode_prevented="Elastomer thermal degradation, chemical swelling, and seal extrusion",
                    explanation=f"SEAL MATERIAL DOWNGRADE: Candidate material '{c_mat}' is inferior to required '{q_mat}'. Substituting lower-tier elastomer leads to thermal decomposition and fluid release.",
                ),
            )
        elif c_rank > q_rank:
            return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.93, None)

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
