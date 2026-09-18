"""
Module 4 (Part 2): ASME B16.47 Large Diameter Flanges (NPS 26 to NPS 60).

Series A (MSS SP-44): Thicker, heavier flanges with larger bolt diameters and fewer bolt holes.
Series B (API 605): Thinner, lighter flanges with smaller bolt diameters and more bolt holes.

Series Incompatibility Invariant:
Series A and Series B flanges CANNOT bolt together due to completely different
bolt circle diameters (BCD) and hole patterns. Any Series A vs. Series B
substitution is strictly blocked as Tier-3 Incompatible.
"""

from typing import Optional, Tuple
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_large_flange_series(
    query_series: Optional[str],
    candidate_series: Optional[str],
    size_nb_mm: Optional[float] = None,
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates ASME B16.47 Series A vs Series B flange compatibility.
    """
    if not query_series and not candidate_series:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    qs = (query_series or "").strip().upper()
    cs = (candidate_series or "").strip().upper()

    # Normalize series indicators
    def _extract_series(s: str) -> Optional[str]:
        if "SERIES A" in s or "MSS SP-44" in s or "SERIES-A" in s:
            return "SERIES_A"
        if "SERIES B" in s or "API 605" in s or "SERIES-B" in s:
            return "SERIES_B"
        return None

    q_ser = _extract_series(qs)
    c_ser = _extract_series(cs)

    if not q_ser or not c_ser:
        if q_ser != c_ser:
            return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    if q_ser == c_ser:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    # Series mismatch
    return (
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        0.0,
        RuleViolation(
            module_name="ASME_B16_47_SERIES",
            standard_code="ASME B16.47 / MSS SP-44 / API 605",
            failure_mode_prevented="Bolt circle & hole pattern mismatch causing joint failure",
            explanation=(
                f"ASME B16.47 SERIES MISMATCH: Query requires {q_ser.replace('_', ' ')}. "
                f"Candidate is {c_ser.replace('_', ' ')}. Series A (MSS SP-44) and Series B (API 605) "
                f"have completely different bolt circle diameters and hole quantities and cannot physically bolt together."
            ),
        ),
    )
