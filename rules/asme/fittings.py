"""
Module 6: Forged & Buttweld Piping Fittings (ASME B16.9 / B16.11 / MSS SP-97 / MSS SP-75).

Rules:
1. ASME B16.11 Forged Fittings:
   - Threaded ratings: 2000# < 3000# < 6000#
   - Socket-weld ratings: 3000# < 6000# < 9000#
   - Down-rating is Tier-3 Incompatible.
2. ASME B16.9 Buttweld Fittings:
   - Long Radius (LR, 1.5D) vs Short Radius (SR, 1.0D): SR in piggable line = Tier-3 Restriction Trap.
3. MSS SP-75 High-Yield Pipeline Fittings:
   - High-yield pipeline fittings (WPHY 42, 52, 60, 65, 70) cannot be downgraded to A234 WPB.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


THREADED_RATINGS = [2000, 3000, 6000]
SOCKET_WELD_RATINGS = [3000, 6000, 9000]


def check_forged_fittings_rating(
    query_rating: Optional[int],
    cand_rating: Optional[int],
    connection_type: str = "SOCKET_WELD",
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates ASME B16.11 pressure class rating for forged fittings.
    """
    if query_rating is None and cand_rating is None:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
    if query_rating is None or cand_rating is None:
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)

    conn = connection_type.upper()
    ladder = THREADED_RATINGS if "THREAD" in conn or "NPT" in conn else SOCKET_WELD_RATINGS

    if query_rating not in ladder or cand_rating not in ladder:
        # Standard comparison
        if cand_rating < query_rating:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="ASME_B16_11",
                    standard_code="ASME B16.11",
                    failure_mode_prevented="Socket-weld or threaded fitting rupture under pressure",
                    explanation=f"FITTING DOWN-RATING: Candidate {cand_rating}# is lower than required {query_rating}#.",
                ),
            )
        elif cand_rating == query_rating:
            return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
        else:
            return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 0.96, None)

    q_idx = ladder.index(query_rating)
    c_idx = ladder.index(cand_rating)

    if c_idx < q_idx:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B16_11",
                standard_code="ASME B16.11",
                failure_mode_prevented="Fitting joint pressure containment failure",
                explanation=f"FATAL FITTING DOWN-RATING: Class {cand_rating}# cannot replace Class {query_rating}#.",
            ),
        )
    elif c_idx == q_idx:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
    else:
        # Safe upgrade
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 0.97, None)


def check_buttweld_elbow_radius(
    query_radius: Optional[str],
    cand_radius: Optional[str],
    is_piggable: bool = False,
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates ASME B16.9 bend radius (LR 1.5D vs SR 1.0D).
    """
    if not query_radius and not cand_radius:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    qr = (query_radius or "").upper()
    cr = (cand_radius or "").upper()

    is_q_lr = "LR" in qr or "1.5D" in qr or "LONG" in qr
    is_c_sr = "SR" in cr or "1.0D" in cr or "SHORT" in cr

    if is_q_lr and is_c_sr and is_piggable:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B16_9_ELBOW",
                standard_code="ASME B16.9",
                failure_mode_prevented="Pipeline scraper (PIG) stuck in short radius elbow",
                explanation="PIGGING RESTRICTION TRAP: Short Radius (SR, 1.0D) elbow proposed for Long Radius (LR, 1.5D) in piggable pipeline.",
            ),
        )

    if qr == cr or (not qr and not cr):
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.88, None)
