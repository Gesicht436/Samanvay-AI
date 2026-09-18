"""
Module 5 (Part 2): API 6D Pipeline Valves - Piggability Invariant.

Rules:
1. Full Bore (FB) vs. Reduced Bore (RB):
   - In operational pipeline transmission manifolds requiring periodic pig scraping,
     substituting a Reduced Bore valve is strictly blocked as Tier-3 Pipeline PIG Blockage Trap.
2. Full Bore can replace Reduced Bore safely (Tier-1 / Tier-2).
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_valve_bore(
    query_bore: Optional[str],
    cand_bore: Optional[str],
    is_piggable: bool = False,
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates API 6D valve bore and piggability.
    """
    if not query_bore and not cand_bore:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    qb = (query_bore or "").upper().replace(" ", "_")
    cb = (cand_bore or "").upper().replace(" ", "_")

    if ("FULL" in qb or is_piggable) and ("REDUCED" in cb or cb == "RB"):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_6D_BORE",
                standard_code="API 6D Section 5.1",
                failure_mode_prevented="Pipeline scraper (PIG) tool trapped in restricted valve bore",
                explanation="PIG BLOCKAGE TRAP: Reduced Bore (RB) valve cannot replace Full Bore (FB) in a piggable pipeline line. Pipeline inspection gauges will lodge in the valve bore.",
            ),
        )

    if qb == cb or (not qb and not cb):
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    if "REDUCED" in qb and "FULL" in cb:
        # Full bore can safely replace reduced bore
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.95, None)

    return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.88, None)
