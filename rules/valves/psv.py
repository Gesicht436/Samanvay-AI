"""
Module 5 (Part 5): API 520 / API 526 Pressure Safety Relief Valves (PSV).

Orifice Area Hierarchy (Standard API 526 Letter Designations):
D < E < F < G < H < J < K < L < M < N < P < Q < R < T

Rules:
1. Orifice Area Sizing Invariant:
   - Substituting a smaller orifice area (e.g. Orifice D for Orifice F) is blocked
     as Tier-3 Overpressure Vessel Detonation Trap.
2. Cold Differential Test Pressure (CDTP):
   - Lower CDTP than specified leads to premature lifting; higher prevents relief.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


API_526_ORIFICES = ["D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "Q", "R", "T"]


def check_psv_orifice_and_pressure(
    query_orifice: Optional[str],
    cand_orifice: Optional[str],
    query_cdtp_bar: Optional[float] = None,
    cand_cdtp_bar: Optional[float] = None,
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates API 526 PSV orifice area and set pressure.
    """
    if not query_orifice and not cand_orifice:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    qo = (query_orifice or "").strip().upper()
    co = (cand_orifice or "").strip().upper()

    if qo in API_526_ORIFICES and co in API_526_ORIFICES:
        q_idx = API_526_ORIFICES.index(qo)
        c_idx = API_526_ORIFICES.index(co)

        if c_idx < q_idx:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="API_526_ORIFICE",
                    standard_code="API 526 Section 2",
                    failure_mode_prevented="Vessel overpressure detonation from undersized relief orifice",
                    explanation=f"OVERPRESSURE VESSEL DETONATION TRAP: Candidate Orifice '{co}' has smaller relief area than required Orifice '{qo}'. Insufficient emergency venting capacity.",
                ),
            )
        elif c_idx > q_idx:
            return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.90, None)

    # CDTP check
    if query_cdtp_bar and cand_cdtp_bar:
        if abs(query_cdtp_bar - cand_cdtp_bar) > 0.1:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="API_520_CDTP",
                    standard_code="API 520 Part I",
                    failure_mode_prevented="PSV set pressure mismatch",
                    explanation=f"CDTP MISMATCH: Candidate set pressure {cand_cdtp_bar} bar != required {query_cdtp_bar} bar.",
                ),
            )

    if qo == co:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)
