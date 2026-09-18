"""
Module 8 (Part 2): ASTM Fasteners Integrity & Liquid Metal Embrittlement (ASTM A193 / A194 / A320).

Rules:
1. High-Temperature Alloy Bolting Parity:
   - Stud ASTM A193 Gr. B7 requires matching Nut ASTM A194 Gr. 2H.
   - High-Creep Duty: A193 B16 (450°C-540°C) requires A194 Gr. 7 or Gr. 4 nuts.
   - Low-Temperature Duty: A320 Gr. L7 (-101°C) requires A194 Gr. 7 nuts.
   - Sour Service (NACE MR0175): B7 exceeds 22 HRC; mandates A193 B7M paired with A194 2HM.
   - Nut Mismatch Trap: Pairing low-carbon mild steel nuts (Gr. 2) with B7 alloy studs is Tier-3 Thread Shear Trap.
2. Fastener Coating & Liquid Metal Embrittlement (LME):
   - Above 200°C - 250°C, Cadmium/Zinc-plated or Galvanized bolts suffer LME cracking.
   - Blocked as Tier-3 Liquid Metal Embrittlement Trap.
3. Yield Strength Integrity:
   - Candidate yield strength < required yield strength = Tier-3 Incompatible.
"""

import re
from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


STUD_NUT_PAIRS = {
    "B7": "2H",
    "B7M": "2HM",
    "B16": "7",
    "L7": "7",
    "L7M": "7M",
}


def _parse_temp(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace("°C", "").replace("C", "").strip()
    m = re.search(r'[-+]?\d*\.?\d+', s)
    return float(m.group(0)) if m else None


def check_fastener_integrity(
    query_stud: Optional[str],
    cand_stud: Optional[str],
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates fastener stud-nut metallurgy, temperature LME, and yield strength.
    """
    qs = (query_stud or "").upper()
    cs = (cand_stud or "").upper()

    # 1. Temperature & Liquid Metal Embrittlement (LME)
    temp_val = query_props.get("temp") or query_props.get("temp_c") or cand_props.get("temp") or cand_props.get("temp_c")
    temp_c = _parse_temp(temp_val)

    cand_coating = str(cand_props.get("coating", "")).upper()
    if temp_c is not None and temp_c > 200.0:
        if any(c in cand_coating for c in ["GALV", "ZINC", "CADMIUM", "CAD"]):
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="ASTM_A193_LME",
                    standard_code="ASTM A193 / LME Invariant",
                    failure_mode_prevented="Liquid metal embrittlement cracking from molten zinc/cadmium",
                    explanation=(
                        f"LIQUID METAL EMBRITTLEMENT TRAP: Service temperature is {temp_c}°C. "
                        f"Galvanized/Zinc/Cadmium coated alloy studs suffer catastrophic liquid metal "
                        f"grain boundary cracking above 200°C. Bare or Xylan/PTFE coating is mandatory."
                    ),
                ),
            )

    # 2. Yield Strength Check
    q_ys = query_props.get("yield_strength_mpa")
    c_ys = cand_props.get("yield_strength_mpa")
    if q_ys is not None and c_ys is not None:
        try:
            qy = float(q_ys)
            cy = float(c_ys)
            if cy < qy:
                return (
                    DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                    0.0,
                    RuleViolation(
                        module_name="FASTENER_STRENGTH",
                        standard_code="ASTM A193 / ASTM A320",
                        failure_mode_prevented="Bolt yield elongation and joint flange blowout under operating load",
                        explanation=f"FASTENER STRENGTH DOWN-RATING: Candidate yield strength {cy} MPa is below required {qy} MPa.",
                    ),
                )
        except (ValueError, TypeError):
            pass

    # 3. Low-Temp Cryogenic L7 vs High-Temp B7
    if "L7" in qs and "L7" not in cs:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASTM_A320_CRYOGENIC",
                standard_code="ASTM A320 Gr. L7",
                failure_mode_prevented="Low-temperature brittle fracture of bolt under cryogenic thermal shock",
                explanation="CRYOGENIC BOLTING TRAP: Standard B7 bolts lack -101°C Charpy V-notch impact certification and shatter under cryogenic duty.",
            ),
        )

    # 4. Nut Pairing Check
    cand_nut = str(cand_props.get("nut_grade", "")).upper()
    if "B7" in cs and cand_nut and cand_nut in ["GR.2", "GR 2", "CLASS 4.6", "2"]:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASTM_A194_NUT",
                standard_code="ASTM A194 Gr. 2H",
                failure_mode_prevented="Commercial nut thread stripping under high bolt preload",
                explanation="THREAD SHEAR TRAP: Commercial mild steel nuts cannot handle high-strength B7 alloy bolt preload. ASTM A194 Gr. 2H heavy hex nuts are mandatory.",
            ),
        )

    if qs == cs or (not qs and not cs):
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.88, None)
