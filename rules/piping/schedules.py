"""
Module 3: ASME B36.10M / B36.19M Pipe Schedules & Wall Thickness Invariants.

Schedule Ladder:
SCH 5 < SCH 10 < SCH 20 < SCH 30 < STD / SCH 40 < SCH 60 < XS / SCH 80 < SCH 100 < SCH 120 < SCH 140 < SCH 160 < XXS

Rules:
1. Down-Schedule Prohibition (Burst Hazard):
   - Thinner wall than required is rejected as Tier-3 Incompatible.
2. Schedule Upgrade:
   - Upgrading to a heavier schedule (e.g. Sch 40 -> Sch 80) is permitted as Tier-2 Substitute.
3. Pipe Coating Thickness:
   - Coating thickness downgrade is Tier-3 Incompatible.
   - Coating thickness upgrade is Tier-2 Substitute.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


SCHEDULE_LADDER = [
    "SCH 5", "SCH 5S", "SCH 10", "SCH 10S", "SCH 20", "SCH 30",
    "STD", "SCH 40", "SCH 40S", "SCH 60",
    "XS", "SCH 80", "SCH 80S",
    "SCH 100", "SCH 120", "SCH 140", "SCH 160", "XXS",
]

EQUIVALENCES = {
    "40": "SCH 40",
    "80": "SCH 80",
    "10": "SCH 10",
    "20": "SCH 20",
    "30": "SCH 30",
    "60": "SCH 60",
    "100": "SCH 100",
    "120": "SCH 120",
    "140": "SCH 140",
    "160": "SCH 160",
    "SCHEDULE 40": "SCH 40",
    "SCHEDULE 80": "SCH 80",
    "SCHEDULE 160": "SCH 160",
    "STANDARD": "STD",
    "EXTRA STRONG": "XS",
    "DOUBLE EXTRA STRONG": "XXS",
}


def normalize_schedule(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    s = str(val).strip().upper().replace("  ", " ")
    if s in EQUIVALENCES:
        return EQUIVALENCES[s]
    if s in SCHEDULE_LADDER:
        return s
    if not s.startswith("SCH") and not s in ("STD", "XS", "XXS"):
        # e.g. "40" -> "SCH 40"
        cand = f"SCH {s}"
        if cand in SCHEDULE_LADDER:
            return cand
    return s


def check_pipe_schedule(
    query_sch: Optional[str],
    cand_sch: Optional[str],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates ASME B36.10M / B36.19M pipe schedule wall thickness.
    """
    if not query_sch and not cand_sch:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
    if not query_sch or not cand_sch:
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)

    qs = normalize_schedule(query_sch)
    cs = normalize_schedule(cand_sch)

    if qs == cs:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    q_idx = SCHEDULE_LADDER.index(qs) if qs in SCHEDULE_LADDER else -1
    c_idx = SCHEDULE_LADDER.index(cs) if cs in SCHEDULE_LADDER else -1

    if q_idx < 0 or c_idx < 0:
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)

    if c_idx < q_idx:
        # Down-scheduling
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B36_10M_SCHEDULE",
                standard_code="ASME B36.10M",
                failure_mode_prevented="Thin-wall pipe burst under hoop stress",
                explanation=f"SCHEDULE DOWN-RATING: Candidate '{cs}' has thinner wall than required '{qs}'. Burst hazard under operating hoop stress.",
            ),
        )

    # Schedule upgrade is safe upgrade
    return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.90, None)


def check_coating_thickness(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates anti-corrosion coating thickness (e.g. 3LPE, FBE, epoxy).
    """
    q_th = query_props.get("coating_thickness_um")
    c_th = cand_props.get("coating_thickness_um")

    if q_th is not None and c_th is not None:
        try:
            qt = float(q_th)
            ct = float(c_th)
            if ct < qt:
                return (
                    DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                    0.0,
                    RuleViolation(
                        module_name="COATING_THICKNESS",
                        standard_code="ISO 21809 / NACE SP0188",
                        failure_mode_prevented="Premature external corrosion and pinhole leakage from under-gauge coating",
                        explanation=f"COATING THICKNESS DOWNGRADE: Candidate coating thickness {ct} µm is below required {qt} µm.",
                    ),
                )
            elif ct > qt:
                return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.92, None)
        except (ValueError, TypeError):
            pass

    # Coating type upgrade (e.g. BARE -> 3LPE_COATED)
    q_coat = str(query_props.get("coating", "")).upper()
    c_coat = str(cand_props.get("coating", "")).upper()
    if q_coat and c_coat and q_coat != c_coat:
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.90, None)

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
