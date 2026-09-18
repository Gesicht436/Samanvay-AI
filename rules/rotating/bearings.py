"""
Module 11 (Part 3): ISO 15 Rolling Element Bearings & Internal Clearances.

Clearance Ladder:
C2 (tight) < CN (normal) < C3 (increased) < C4 (extra increased)

Rules:
1. High-Temperature Radial Internal Clearance (C3 vs. CN):
   - In process pumps and motors, operating heat expands shaft and inner ring.
   - Replacing C3 clearance bearing with normal CN clearance eliminates running clearance,
     causing thermal expansion lockup -> Tier-3 Bearing Seizure / Shaft Snap.
2. Bearing Construction Type:
   - Substituting a ball bearing for a roller bearing or vice versa in heavy radial/thrust load duty
     is blocked as Tier-3 Incompatible.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


CLEARANCE_LADDER = ["C2", "CN", "C3", "C4", "C5"]


def check_bearing_compatibility(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates ISO 15 bearing clearance and construction type.
    """
    # 1. Bearing Type (Roller vs Ball)
    q_type = str(query_props.get("type", query_props.get("bearing_type", ""))).upper()
    c_type = str(cand_props.get("type", cand_props.get("bearing_type", ""))).upper()

    if q_type and c_type and q_type != c_type:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ISO_15_BEARING_TYPE",
                standard_code="ISO 15 / ABMA Standard 20",
                failure_mode_prevented="Bearing fatigue spalling and dynamic load mismatch",
                explanation=f"BEARING TYPE MISMATCH: Query specifies '{q_type}', candidate is '{c_type}'. Roller and ball bearings have fundamentally different radial/axial load capacities.",
            ),
        )

    # 2. Radial Internal Clearance (C3 vs CN)
    q_clr = str(query_props.get("clearance", "")).upper()
    c_clr = str(cand_props.get("clearance", "")).upper()

    if q_clr in CLEARANCE_LADDER and c_clr in CLEARANCE_LADDER:
        q_idx = CLEARANCE_LADDER.index(q_clr)
        c_idx = CLEARANCE_LADDER.index(c_clr)

        if c_idx < q_idx:
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="ISO_15_CLEARANCE",
                    standard_code="ISO 5753-1 / ISO 15",
                    failure_mode_prevented="Shaft thermal expansion bearing seizure and catastrophic shaft snap",
                    explanation=f"BEARING SEIZURE TRAP: Candidate clearance '{c_clr}' is tighter than required '{q_clr}'. In high-temperature pump duty, thermal expansion consumes radial room, causing premature seizure.",
                ),
            )
        elif c_idx > q_idx:
            return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.90, None)

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
