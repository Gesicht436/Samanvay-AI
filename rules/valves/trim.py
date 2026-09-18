"""
Module 5 (Part 1): API 600 Steel Gate Valve Trim Ladder.

Trim Ladder:
- Trim 1: 410 Stainless Steel (13% Cr) - Standard utility service.
- Trim 8: 410 + Stellite Hardface - Universal refinery standard trim.
- Trim 5: Full Stellite (Co-Cr-A) - Severe high-pressure/temp erosive slurry.
- Trim 12: 316 + Stellite Hardface - Corrosive sour service.
- Trim 16: Monel - Hydrofluoric acid (HF) alkylation.

Rules:
1. Trim Downgrade Prohibition:
   - Demoting a Trim 5 or Trim 8 valve to Trim 1 in abrasive/erosive slurry is blocked as
     Tier-3 Rapid Seat Washout Trap.
2. Trim Upgrade:
   - Upgrading from Trim 1 to Trim 8 (hardfaced seats) is permitted as Tier-2 or Tier-1.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


TRIM_ORDER = [1, 8, 5, 12, 16]


def check_valve_trim(
    query_trim: Optional[int],
    cand_trim: Optional[int],
    is_erosive_or_slurry: bool = False,
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates API 600 valve trim metallurgy compatibility.
    """
    if query_trim is None and cand_trim is None:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
    if query_trim is None or cand_trim is None:
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)

    qt = int(query_trim)
    ct = int(cand_trim)

    if qt == ct:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    q_idx = TRIM_ORDER.index(qt) if qt in TRIM_ORDER else -1
    c_idx = TRIM_ORDER.index(ct) if ct in TRIM_ORDER else -1

    if q_idx < 0 or c_idx < 0:
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.82, None)

    if c_idx < q_idx:
        # Trim downgrade
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_600_TRIM",
                standard_code="API 600 Table 3",
                failure_mode_prevented="Rapid seat washout and wire-drawing erosion in erosive fluid",
                explanation=f"TRIM DOWNGRADE TRAP: Candidate Trim {ct} is inferior to required Trim {qt}. Downgrading trim metallurgy in process duty leads to rapid seat washout and internal leakage.",
            ),
        )

    # Safe upgrade (e.g. Trim 8 over Trim 1)
    return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.92, None)
