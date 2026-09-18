"""
Module 18: Metallic Expansion Joints & Flexible Hoses (EJMA / ISO 10380 / BS 6501).

Rules:
1. EJMA Expansion Joint Restraint Invariance (Tied vs. Unrestrained):
   - Tied expansion joints contain pressure thrust force (F = P * A).
   - Substituting an unrestrained bellows where tied joints are specified is blocked
     as Tier-3 Pipe Anchor Shearing / Bellows Tensile Rupture Trap.
2. ISO 10380 Corrugated Hose Braid Integrity:
   - High-pressure pulsation applications requiring double-braided construction
     cannot be substituted with single-braided hoses -> Tier-3 Hose Braid Tensile Rupture Trap.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_expansion_joint_and_hose(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates EJMA metallic expansion joints and ISO 10380 flexible metal hoses.
    """
    # 1. Tied vs Unrestrained Bellows
    q_tied = query_props.get("tied_joint", False) or query_props.get("restrained_bellows", False)
    c_tied = cand_props.get("tied_joint", True)
    if "tied_joint" not in cand_props and "unrestrained" in str(cand_props).lower():
        c_tied = False

    if q_tied and not c_tied:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="EJMA_RESTRAINT",
                standard_code="EJMA Standards Section C",
                failure_mode_prevented="Hydrostatic pressure thrust anchor shearing and bellows tensile rupture",
                explanation="BELLOWS RUPTURE TRAP: Unrestrained bellows proposed where tied expansion joint is required. Internal pressure thrust will pull bellows apart and shear piping guides.",
            ),
        )

    # 2. Corrugated Hose Braid Integrity
    q_braid = str(query_props.get("braid_type", "")).upper()
    c_braid = str(cand_props.get("braid_type", "")).upper()
    if ("DOUBLE" in q_braid or "2-BRAID" in q_braid) and ("SINGLE" in c_braid or "1-BRAID" in c_braid):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ISO_10380_HOSE_BRAID",
                standard_code="ISO 10380",
                failure_mode_prevented="Hose braid tensile fatigue rupture and fluid jetting",
                explanation="HOSE BRAID RUPTURE TRAP: Single-braided hose cannot handle high-pressure cyclic impulse duty where double-braided construction is specified.",
            ),
        )

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
