"""
Module 10: Instrumentation Small-Bore Tubing & Compression Fittings (ASTM A269).

Rules:
1. Dimensional System Invariance (Fractional Imperial vs. Metric OD):
   - Mating a 12 mm compression tube fitting onto 1/2" (12.7 mm) tubing or vice versa
     causes under-swaging and violent tube blowout under high impulse pressure (up to 6,000 PSI).
   - Mismatched tubing system = Tier-3 Tube Blow-Off Disaster Trap.
2. Metallurgical Hardness Differential Rule:
   - Tubing must be fully annealed with maximum hardness <= 90 HRB.
   - Hardness > 90 HRB prevents ferrule coining, leading to joint separation under vibration.
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_instrumentation_tubing(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates ASTM A269 instrument tubing and compression ferrule compatibility.
    """
    q_sys = str(query_props.get("unit_system", "")).upper()
    c_sys = str(cand_props.get("unit_system", "")).upper()

    q_od_mm = query_props.get("od_mm")
    c_od_mm = cand_props.get("od_mm")

    if q_od_mm and c_od_mm:
        try:
            q_val = float(q_od_mm)
            c_val = float(c_od_mm)
            if abs(q_val - c_val) > 0.05:
                # E.g. 12.0 mm vs 12.7 mm
                return (
                    DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                    0.0,
                    RuleViolation(
                        module_name="ASTM_A269_TUBING_OD",
                        standard_code="ASTM A269",
                        failure_mode_prevented="Tubing compression ferrule blowout under impulse pressure",
                        explanation=f"TUBE BLOW-OFF DISASTER TRAP: Outside diameter mismatch ({q_val} mm vs {c_val} mm). Fractional imperial (1/2\" = 12.7 mm) and metric (12.0 mm) tubing cannot cross-mate in compression fittings.",
                    ),
                )
        except (ValueError, TypeError):
            pass

    # Tube hardness check
    c_hrb = cand_props.get("hardness_hrb")
    if c_hrb is not None:
        try:
            if float(c_hrb) > 90.0:
                return (
                    DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                    0.0,
                    RuleViolation(
                        module_name="ASTM_A269_HARDNESS",
                        standard_code="ASTM A269 / Swagelok Standards",
                        failure_mode_prevented="Ferrule slippage and joint vibration separation due to excessive tube hardness",
                        explanation=f"TUBE HARDNESS TRAP: Candidate hardness is {c_hrb} HRB, exceeding the 90 HRB ceiling. Hard tubing prevents ferrule coining and grip.",
                    ),
                )
        except (ValueError, TypeError):
            pass

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
