"""
Module 14: Reciprocating & Centrifugal Compressors (API 618 / API 617 / API 692).

Rules:
1. API 618 Cylinder Valves (Suction vs. Discharge):
   - Installing a discharge valve into a suction port prevents gas intake and triggers
     extreme re-compression heating -> Tier-3 Cylinder Head Detonation Trap.
2. API 617 Impeller Metallurgy (Wet H2S Sour Gas):
   - High-strength precipitation-hardened steels (e.g. 17-4PH) without H1150M double aging
     suffer rapid sulfide stress cracking -> Tier-3 Impeller Burst / Casing Destruction Trap.
3. API 692 Dry Gas Seals (DGS) & Buffer Systems:
   - Downgrading tandem dry gas seal to single seal in toxic or flammable gas service
     is blocked as Tier-3 Explosive Gas Escape / Compressor Bay Fire Trap.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_compressor_compatibility(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates API 618 cylinder valves, API 617 sour impellers, and API 692 dry gas seals.
    """
    # 1. API 618 Suction vs Discharge Cylinder Valve
    q_vlv_type = str(query_props.get("valve_function") or query_props.get("valve_role") or query_props.get("valve_type", "")).upper()
    c_vlv_type = str(cand_props.get("valve_function") or cand_props.get("valve_role") or cand_props.get("valve_type", "")).upper()

    if ("SUCTION" in q_vlv_type and "DISCHARGE" in c_vlv_type) or ("DISCHARGE" in q_vlv_type and "SUCTION" in c_vlv_type):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_618_CYLINDER_VALVE",
                standard_code="API 618 5th Edition",
                failure_mode_prevented="Inverted valve cylinder re-compression heating and cylinder head detonation",
                explanation=f"CYLINDER VALVE INVERSION TRAP: Query specifies '{q_vlv_type}', candidate is '{c_vlv_type}'. Installing discharge valve in suction port blocks flow and causes catastrophic head overpressure.",
            ),
        )

    # 2. API 692 Dry Gas Seal (Tandem vs Single)
    q_dgs = str(query_props.get("dgs_type") or query_props.get("seal_type", "")).upper()
    c_dgs = str(cand_props.get("dgs_type") or cand_props.get("seal_type", "")).upper()

    if "TANDEM" in q_dgs and "SINGLE" in c_dgs:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_692_DGS",
                standard_code="API 692",
                failure_mode_prevented="Explosive gas escape and compressor bay fire blowout",
                explanation="DRY GAS SEAL DOWNGRADE TRAP: Tandem dry gas seal with intermediate N2 buffer downgraded to single seal in pressurized gas duty.",
            ),
        )

    # 3. API 617 Impeller Sour Service Heat Treatment
    is_sour = query_props.get("sour_gas", False) or query_props.get("nace", False)
    cand_ht = str(cand_props.get("heat_treatment", "")).upper()
    cand_mat = str(cand_props.get("impeller_material", "")).upper()
    if is_sour and ("17-4PH" in cand_mat or "AISI 630" in cand_mat) and "H1150M" not in cand_ht:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_617_IMPELLER_METALLURGY",
                standard_code="API 617 / NACE MR0175",
                failure_mode_prevented="High-speed impeller burst from sulfide stress cracking in sour gas",
                explanation="IMPELLER BURST TRAP: 17-4PH stainless impeller requires H1150M double-age heat treatment for wet H2S sour gas compliance.",
            ),
        )

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
