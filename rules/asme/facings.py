"""
Module 7: Flange Facings, Serrations & Joint Mechanical Invariants (ASME B16.5 / B31.3 / MSS SP-6).

Rules:
1. Facing Geometry Parity:
   - RF <-> RF: Compatible.
   - RTJ <-> RTJ: Compatible.
   - RF <-> RTJ: Strictly Incompatible (Tier-3). An RF flange cannot compress or seal inside an RTJ ring groove.
   - FF <-> FF: Compatible.
2. Cast Iron Equipment Flange Invariant (Flat Face vs. Raised Face):
   - Bolting a Raised Face (RF) steel flange to a Flat Face (FF) cast iron flange cracks brittle flange ears.
   - RF-to-FF on brittle bodies is blocked as Tier-3 Flange Fracture Trap (ASME B31.3 Section 312.2).
3. Flange Attachment Type (Weld Neck vs. Slip-On):
   - In ASME B31.3 Severe Cyclic Conditions or cryogenic service, Slip-On flanges are prohibited.
   - Substituting Slip-On for Weld Neck is blocked as Tier-3 Fatigue Fracture Trap.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


COMPATIBLE_FACING_PAIRS = {
    ("RF", "RF"), ("RTJ", "RTJ"), ("FF", "FF"),
    ("BW", "BW"), ("SW", "SW"), ("NPT", "NPT"), ("BE", "BE")
}


def check_flange_facing(
    query_facing: Optional[str],
    candidate_facing: Optional[str],
    body_material: Optional[str] = None,
    severe_cyclic: bool = False,
    query_flange_type: Optional[str] = None,
    cand_flange_type: Optional[str] = None,
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates flange facing and attachment geometry compatibility.
    """
    if not query_facing and not candidate_facing:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    qf = (query_facing or "").strip().upper()
    cf = (candidate_facing or "").strip().upper()

    # Exact match
    if qf == cf:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    # RF vs RTJ Incompatibility
    if (qf == "RF" and cf == "RTJ") or (qf == "RTJ" and cf == "RF"):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B16_5_FACING",
                standard_code="ASME B16.5",
                failure_mode_prevented="Joint seal failure from incompatible gasket seating face geometry",
                explanation=f"FACING MISMATCH: '{qf}' cannot mate with '{cf}'. An RF flange cannot compress or seal inside an RTJ ring groove.",
            ),
        )

    # Cast Iron FF vs RF Invariant
    mat = (body_material or "").upper()
    is_cast_iron = "CAST IRON" in mat or "CI" in mat or "A126" in mat or "GRAY IRON" in mat
    if is_cast_iron and ((qf == "FF" and cf == "RF") or (qf == "RF" and cf == "FF")):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B31_3_CAST_IRON",
                standard_code="ASME B31.3 Section 312.2",
                failure_mode_prevented="Brittle cast iron flange ear bending moment cracking",
                explanation="CAST IRON FLANGE FRACTURE TRAP: Bolting Raised Face (RF) steel to Flat Face (FF) cast iron concentrates bolt bending stress and fractures the flange.",
            ),
        )

    # General facing mismatch
    if (qf, cf) not in COMPATIBLE_FACING_PAIRS and (cf, qf) not in COMPATIBLE_FACING_PAIRS:
        if qf and cf:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="FACING_AND_CONNECTION_MISMATCH",
                    standard_code="ASME B16.5 / B16.25",
                    failure_mode_prevented="Joint seal and connection mismatch preventing assembly",
                    explanation=f"CONNECTION / FACING MISMATCH: Query requires '{qf}', candidate provides '{cf}'.",
                ),
            )

    # Flange Attachment Type: Slip-On vs Weld Neck in severe cyclic
    qt = (query_flange_type or "").upper()
    ct = (cand_flange_type or "").upper()
    if severe_cyclic and ("WELD NECK" in qt or "WN" in qt) and ("SLIP ON" in ct or "SO" in ct):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B31_3_CYCLIC",
                standard_code="ASME B31.3 Severe Cyclic Service",
                failure_mode_prevented="Slip-on flange fillet weld fatigue fracture",
                explanation="FATIGUE FRACTURE TRAP: Slip-On flanges are prohibited in Severe Cyclic Service. Weld Neck with full penetration butt weld is mandatory.",
            ),
        )

    return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)
