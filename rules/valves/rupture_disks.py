"""
Module 15: Rupture Disks & Overpressure Protection (ASME Sec VIII / ISO 4126-2 / API 520).

Rules:
1. Rupture Disk Type Invariance (Forward-Acting vs. Reverse Buckling):
   - Forward-acting (tension-loaded) disks fatigue prematurely under cyclic pressure.
   - Reverse buckling cannot be replaced with tension-loaded disks in pulsating lines -> Tier-3 Premature Fatigue Rupture.
2. Non-Fragmenting Mandate Upstream of PSVs (ASME Sec VIII Div 1 UG-127 / API 520):
   - Installing fragmenting rupture disk upstream of a PSV is blocked as
     Tier-3 PSV Nozzle Clogging / Catastrophic Vessel Overpressure Trap (metal petals shear off and plug valve nozzle).
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_rupture_disk(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
    upstream_of_psv: bool = False,
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates rupture disk fragmentation type and buckling geometry.
    """
    is_psv_upstream = upstream_of_psv or query_props.get("upstream_of_psv", False)

    q_type = str(query_props.get("disk_type") or query_props.get("type", "")).upper()
    c_type = str(cand_props.get("disk_type") or cand_props.get("type", "")).upper()

    # 1. Non-Fragmenting Mandate upstream of PSV
    c_non_frag = cand_props.get("non_fragmenting", False) or "NON-FRAGMENTING" in c_type or "NON_FRAGMENTING" in c_type or "REVERSE_BUCKLING" in c_type
    is_frag = "FRAGMENTING" in c_type and "NON" not in c_type
    if (is_psv_upstream or cand_props.get("upstream_of_psv")) and (not c_non_frag or is_frag):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_UG127_RUPTURE_DISK",
                standard_code="ASME Section VIII Div 1 UG-127 / API 520",
                failure_mode_prevented="Metal petals shearing off and clogging downstream PSV nozzle",
                explanation="PSV NOZZLE CLOGGING TRAP: Fragmenting rupture disk installed upstream of a PSV. Sheared metal petals will lodge in the valve inlet nozzle upon burst, preventing overpressure relief.",
            ),
        )

    # 2. Reverse Buckling vs Forward Acting in cyclic duty
    if ("REVERSE" in q_type or "BUCKLING" in q_type) and ("FORWARD" in c_type or "TENSION" in c_type):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ISO_4126_2_FATIGUE",
                standard_code="ISO 4126-2",
                failure_mode_prevented="Premature cyclic fatigue rupture of tension-loaded disk",
                explanation="PREMATURE FATIGUE RUPTURE TRAP: Forward-acting tension-loaded disk cannot replace reverse-buckling disk in pulsating process line.",
            ),
        )

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
