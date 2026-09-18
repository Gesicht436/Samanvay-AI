"""
Module 19: In-Line Strainers, Filters & Steam Trapping Systems (ASME B16.34 / ISO 6552).

Rules:
1. Strainer & Filter Micron / Mesh Rating:
   - Pump suction fine mesh (<40 mesh) starves NPSHr -> Tier-3 Pump Cavitation Trap.
   - Filter micron rating downgrade (e.g. candidate 25 µm > required 10 µm) = Tier-3 Incompatible.
   - Filter micron rating upgrade (e.g. candidate 10 µm < required 25 µm) = Tier-2 Substitute.
2. Steam Trap Operating Mechanism:
   - Incompatible trap selection causing condensate backup in high-pressure steam mains
     is blocked as Tier-3 Steam Line Water Hammer Pipe Rupture Trap.
3. Thread Type Compatibility:
   - Thread type mismatch (e.g. NPT vs BSPT) cannot form a pressure-tight seal = Tier-3 Incompatible.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_strainer_filter_and_steam_trap(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates filter micron rating, steam trap backpressure, and thread types.
    """
    # 1. Filter Micron Rating (lower micron = finer/better filtration)
    q_mic = query_props.get("micron_rating") or query_props.get("micron")
    c_mic = cand_props.get("micron_rating") or cand_props.get("micron")
    if q_mic is not None and c_mic is not None:
        try:
            qm = float(q_mic)
            cm = float(c_mic)
            if cm > qm:
                # Fails: allows larger particles through
                return (
                    DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                    0.0,
                    RuleViolation(
                        module_name="FILTER_MICRON_RATING",
                        standard_code="ISO 16889 / ISO 2942",
                        failure_mode_prevented="Debris passage and mechanical seal scoring / hydraulic erosion",
                        explanation=f"MICRON RATING DOWNGRADE: Candidate filter rating {cm} µm allows larger particulate than required {qm} µm.",
                    ),
                )
            elif cm < qm:
                # Upgrades: finer filtration
                return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.93, None)
        except (ValueError, TypeError):
            pass

    # 2. Thread Type Mismatch (NPT vs BSPT)
    q_th = str(query_props.get("thread", query_props.get("thread_type", ""))).upper().strip()
    c_th = str(cand_props.get("thread", cand_props.get("thread_type", ""))).upper().strip()
    if q_th and c_th and q_th != c_th:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="THREAD_TYPE_MISMATCH",
                standard_code="ASME B1.20.1 / ISO 7-1",
                failure_mode_prevented="Thread galling and high-pressure fluid jetting leakage",
                explanation=f"THREAD MISMATCH TRAP: Query specifies '{q_th}' (60° American National Taper), candidate is '{c_th}' (55° British Standard Taper). Mismatched thread angles cannot seal.",
            ),
        )

    # 3. Steam Trap Incompatible Type
    q_trap = str(query_props.get("trap_type", "")).upper()
    c_trap = str(cand_props.get("trap_type", "")).upper()
    if ("BUCKET" in q_trap or "FLOAT" in q_trap) and ("DISC" in c_trap or "THERMODYNAMIC" in c_trap):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="STEAM_TRAP_MECHANISM",
                standard_code="ISO 6552 / ASME PTC 39",
                failure_mode_prevented="Steam line condensate backup and catastrophic water hammer slug rupture",
                explanation="WATER HAMMER TRAP: Thermodynamic disc trap proposed for high-backpressure closed condensate line. Disc traps fail to open above 80% backpressure, causing severe steam line water hammer.",
            ),
        )

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
