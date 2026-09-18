"""
Module 16: Positive Isolation Line Blinds & Spacers (ASME B16.48 / ASME B31.3).

Rules:
1. Certified Blinds vs. Uncertified Field Fabrication:
   - Substituting shop-cut uncalculated flat plate in place of certified ASME B16.48 paddle blind
     is blocked as Tier-3 Positive Isolation Blowout Trap (unreinforced plate yields under design pressure).
2. Spade vs. Spacer Geometry:
   - Paddle Spade (Blind): Solid disk with solid rectangular handle.
   - Paddle Spacer (Open): Open bore with hole drilled through handle.
   - Unmarked/reversed handles are flagged as Tier-2 HITL mandatory.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_line_blind_compatibility(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates ASME B16.48 line blind compliance.
    """
    cand_std = str(cand_props.get("certified_standard", "")).upper()
    is_certified = cand_props.get("asme_b16_48_certified", True) and "SHOP_CUT" not in cand_std and "UNCERTIFIED" not in cand_std
    is_shop_cut = cand_props.get("is_shop_fabricated", False) or cand_props.get("shop_cut_plate", False) or "SHOP_CUT" in cand_std or "UNCERTIFIED" in cand_std

    if (is_shop_cut and not is_certified) or "SHOP_CUT" in cand_std:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B16_48_BLIND",
                standard_code="ASME B16.48",
                failure_mode_prevented="Unreinforced flat plate plastic yield blowout under pressure",
                explanation="POSITIVE ISOLATION BLOWOUT TRAP: Shop-cut uncalculated flat plate proposed for ASME B16.48 certified paddle blind. Uncalculated plates fail under line design pressure.",
            ),
        )

    # Check handle geometry marking
    unmarked_handle = cand_props.get("unmarked_handle", False)
    if unmarked_handle:
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.82, None)

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
