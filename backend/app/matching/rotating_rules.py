"""
Deterministic Engineering Tolerance Matrices for Rotating & Electrical Equipment:
  - IEC 60034 & IS/IEC 60079: Flameproof Electric Motors (Hazardous Zone 1/2)
  - API 682 & ISO 21049: Mechanical Seals & Flush Piping Plans
  - ISO 15 & DIN 625: Industrial Bearings & Radial Clearance Classes
  - API 610 & ISO 13709: Hydrocarbon Centrifugal Pumps
"""

from typing import Tuple, List, Optional, Dict
from backend.app.contracts.material import ExtractedMaterialAttributes
from backend.app.contracts.matching import ToleranceViolation, ParameterMatchDetail


# Motor synchronous pole speed ladder at 50 Hz India Grid
POLE_TO_RPM = {
    2: 3000,
    4: 1500,
    6: 1000,
    8: 750,
}

# Hazardous area flameproof protection hierarchy
# Ex d (Flameproof, Zone 1) > Ex e (Increased safety, Zone 2) > Non-Ex (Safe Area)
HAZARDOUS_ZONE_RANK = {
    "NON-EX": 0,
    "SAFE_AREA": 0,
    "EX E": 1,
    "EX-E": 1,
    "EX D": 2,
    "EX-D": 2,
    "EX D IIC T4": 2,
    "EX D IIC T4 GB": 2,
}

# API 682 Mechanical Seal Flush Plan Safety Hierarchy
# Dual pressurized barrier (Plan 53A/54) > Dual unpressurized buffer (Plan 52) > Single flush (Plan 11/23)
SEAL_PLAN_RANK = {
    "PLAN 11": 1,
    "PLAN 23": 2,
    "PLAN 52": 3,
    "PLAN 53A": 4,
    "PLAN 54": 4,
}

# Bearing Radial Internal Clearance Ranking
# C4 > C3 > CN (Normal / C0) > C2
CLEARANCE_RANK = {
    "C2": 1,
    "CN": 2,
    "C0": 2,
    "NORMAL": 2,
    "C3": 3,
    "C4": 4,
}


def evaluate_flameproof_motor(
    source: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes
) -> Tuple[List[ToleranceViolation], List[ParameterMatchDetail], bool]:
    """
    Evaluates flameproof induction motor interchangeability under IEC 60034 and IS/IEC 60079.
    Returns (violations, parameter_checks, is_upgrade).
    """
    violations: List[ToleranceViolation] = []
    checks: List[ParameterMatchDetail] = []
    is_upgrade = False

    # 1. Hazardous Area Flameproof Protection (Zero Tolerance Explosion Invariant)
    s_cert = (source.hazardous_cert or "EX D").strip().upper()
    c_cert = (candidate.hazardous_cert or "NON-EX").strip().upper()

    s_rank = HAZARDOUS_ZONE_RANK.get(s_cert, 2)
    c_rank = HAZARDOUS_ZONE_RANK.get(c_cert, 0)

    if c_rank < s_rank:
        violations.append(ToleranceViolation(
            rule_name="IS/IEC 60079 Hazardous Area Explosion Invariant",
            field="hazardous_cert",
            expected=s_cert,
            actual=c_cert,
            message=f"CATASTROPHIC EXPLOSION TRAP: Non-flameproof motor ({c_cert}) proposed for hazardous hydrocarbon zone requiring {s_cert}. Electrical arcing risks plant explosion."
        ))
        checks.append(ParameterMatchDetail(
            parameter="Hazardous Enclosure Protection",
            matched=False,
            status="MISMATCH",
            source_value=s_cert,
            candidate_value=c_cert,
            note="Uncertified safe-area motor cannot enter Zone 1/2 explosive atmosphere."
        ))
    elif c_rank > s_rank:
        is_upgrade = True
        checks.append(ParameterMatchDetail(
            parameter="Hazardous Enclosure Protection",
            matched=True,
            status="UPGRADE",
            source_value=s_cert,
            candidate_value=c_cert,
            note=f"Flameproof protection upgrade: {c_cert} exceeds required {s_cert} classification."
        ))
    else:
        checks.append(ParameterMatchDetail(
            parameter="Hazardous Enclosure Protection",
            matched=True,
            status="EXACT",
            source_value=s_cert,
            candidate_value=c_cert,
            note="Certified flameproof Ex-d explosion protection parity."
        ))

    # 2. Power Rating (kW) Ladder
    s_kw = source.power_kw
    c_kw = candidate.power_kw

    if s_kw is not None and c_kw is not None:
        if c_kw < s_kw:
            violations.append(ToleranceViolation(
                rule_name="IEC 60034 Motor Overload Rule",
                field="power_kw",
                expected=f"{s_kw} kW minimum",
                actual=f"{c_kw} kW",
                message=f"MOTOR OVERLOAD TRAP: Proposed {c_kw} kW motor is under-rated for driven {s_kw} kW load. Will cause continuous thermal tripping and winding burnout."
            ))
            checks.append(ParameterMatchDetail(
                parameter="Shaft Power Rating",
                matched=False,
                status="MISMATCH",
                source_value=f"{s_kw} kW",
                candidate_value=f"{c_kw} kW",
                note="Under-rated driver motor."
            ))
        elif c_kw > s_kw:
            is_upgrade = True
            checks.append(ParameterMatchDetail(
                parameter="Shaft Power Rating",
                matched=True,
                status="UPGRADE",
                source_value=f"{s_kw} kW",
                candidate_value=f"{c_kw} kW",
                note=f"Functional power upgrade: {c_kw} kW motor safely drives {s_kw} kW pump load with thermal margin."
            ))
        else:
            checks.append(ParameterMatchDetail(
                parameter="Shaft Power Rating",
                matched=True,
                status="EXACT",
                source_value=f"{s_kw} kW",
                candidate_value=f"{c_kw} kW",
                note="Exact motor shaft power parity."
            ))

    # 3. Synchronous Speed & Pole Count Invariant
    s_poles = source.poles
    c_poles = candidate.poles

    if s_poles is not None and c_poles is not None:
        if s_poles != c_poles:
            s_rpm = POLE_TO_RPM.get(s_poles, 1500)
            c_rpm = POLE_TO_RPM.get(c_poles, 3000)
            violations.append(ToleranceViolation(
                rule_name="Synchronous Speed / Pole Count Invariant",
                field="poles",
                expected=f"{s_poles}-Pole ({s_rpm} RPM)",
                actual=f"{c_poles}-Pole ({c_rpm} RPM)",
                message=f"PUMP HYDRAULIC COLLAPSE TRAP: Motor pole count mismatch ({s_poles}P vs {c_poles}P). Driven pump head (H ~ N^2) and flow will fail process requirements."
            ))
            checks.append(ParameterMatchDetail(
                parameter="Motor Pole Count & Speed",
                matched=False,
                status="MISMATCH",
                source_value=f"{s_poles}-Pole ({s_rpm} RPM)",
                candidate_value=f"{c_poles}-Pole ({c_rpm} RPM)",
                note="Incompatible rotational speed."
            ))
        else:
            checks.append(ParameterMatchDetail(
                parameter="Motor Pole Count & Speed",
                matched=True,
                status="EXACT",
                source_value=f"{s_poles}-Pole",
                candidate_value=f"{c_poles}-Pole",
                note=f"Exact synchronous speed match ({POLE_TO_RPM.get(s_poles, 1500)} RPM)."
            ))

    return violations, checks, is_upgrade


def evaluate_mechanical_seal(
    source: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes
) -> Tuple[List[ToleranceViolation], List[ParameterMatchDetail], bool]:
    """
    Evaluates API 682 mechanical seal interchangeability for pump shafts.
    """
    violations: List[ToleranceViolation] = []
    checks: List[ParameterMatchDetail] = []
    is_upgrade = False

    # 1. Shaft Bore Diameter (Zero Tolerance Journal Invariant)
    s_bore = source.bearing_bore_mm or source.size_nb_mm
    c_bore = candidate.bearing_bore_mm or candidate.size_nb_mm

    if s_bore is not None and c_bore is not None:
        if abs(s_bore - c_bore) > 0.05:
            violations.append(ToleranceViolation(
                rule_name="Mechanical Seal Shaft Sleeve Invariant",
                field="size_nb_mm",
                expected=f"{s_bore} mm sleeve",
                actual=f"{c_bore} mm sleeve",
                message=f"SHAFT SLEEVE MISMATCH: Mechanical seal sleeve diameter mismatch ({s_bore}mm != {c_bore}mm). Seal cannot fit pump shaft."
            ))
            checks.append(ParameterMatchDetail(
                parameter="Shaft Sleeve Bore",
                matched=False,
                status="MISMATCH",
                source_value=f"{s_bore} mm",
                candidate_value=f"{c_bore} mm",
                note="Dimensional shaft diameter mismatch."
            ))
        else:
            checks.append(ParameterMatchDetail(
                parameter="Shaft Sleeve Bore",
                matched=True,
                status="EXACT",
                source_value=f"{s_bore} mm",
                candidate_value=f"{c_bore} mm",
                note="Exact pump shaft sleeve diameter parity."
            ))

    # 2. Flush Piping Plan (API 682 Safety Level)
    s_plan = (source.seal_plan or "").strip().upper()
    c_plan = (candidate.seal_plan or "").strip().upper()

    if s_plan and c_plan:
        s_rank = SEAL_PLAN_RANK.get(s_plan, 2)
        c_rank = SEAL_PLAN_RANK.get(c_plan, 2)

        if c_rank < s_rank:
            violations.append(ToleranceViolation(
                rule_name="API 682 Seal Flush Plan Safety Rule",
                field="seal_plan",
                expected=s_plan,
                actual=c_plan,
                message=f"TOXIC SEAL BLOWOUT TRAP: Cannot downgrade from pressurized barrier {s_plan} to unpressurized {c_plan} on hazardous hydrocarbon service."
            ))
            checks.append(ParameterMatchDetail(
                parameter="API 682 Flush Plan",
                matched=False,
                status="MISMATCH",
                source_value=s_plan,
                candidate_value=c_plan,
                note="Unsafe barrier fluid plan downgrade."
            ))
        elif c_rank > s_rank:
            is_upgrade = True
            checks.append(ParameterMatchDetail(
                parameter="API 682 Flush Plan",
                matched=True,
                status="UPGRADE",
                source_value=s_plan,
                candidate_value=c_plan,
                note=f"Enhanced seal reliability upgrade: {c_plan} exceeds required {s_plan} flush configuration."
            ))
        else:
            checks.append(ParameterMatchDetail(
                parameter="API 682 Flush Plan",
                matched=True,
                status="EXACT",
                source_value=s_plan,
                candidate_value=c_plan,
                note=f"Identical API 682 flush arrangement ({s_plan})."
            ))

    return violations, checks, is_upgrade


def evaluate_industrial_bearing(
    source: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes
) -> Tuple[List[ToleranceViolation], List[ParameterMatchDetail], bool]:
    """
    Evaluates industrial rolling bearing interchangeability under ISO 15 / DIN 625.
    """
    violations: List[ToleranceViolation] = []
    checks: List[ParameterMatchDetail] = []
    is_upgrade = False

    # 1. Bearing Journal Bore Diameter (Zero Tolerance)
    s_bore = source.bearing_bore_mm or source.size_nb_mm
    c_bore = candidate.bearing_bore_mm or candidate.size_nb_mm

    if s_bore is not None and c_bore is not None:
        if abs(s_bore - c_bore) > 0.01:
            violations.append(ToleranceViolation(
                rule_name="Bearing Inner Ring Bore Invariant",
                field="bearing_bore_mm",
                expected=f"{s_bore} mm",
                actual=f"{c_bore} mm",
                message=f"BEARING FIT VIOLATION: Inner ring bore mismatch ({s_bore}mm != {c_bore}mm). Cannot press-fit onto pump shaft journal."
            ))
            checks.append(ParameterMatchDetail(
                parameter="Bearing Bore Diameter",
                matched=False,
                status="MISMATCH",
                source_value=f"{s_bore} mm",
                candidate_value=f"{c_bore} mm",
                note="Dimensional press-fit bore mismatch."
            ))
        else:
            checks.append(ParameterMatchDetail(
                parameter="Bearing Bore Diameter",
                matched=True,
                status="EXACT",
                source_value=f"{s_bore} mm",
                candidate_value=f"{c_bore} mm",
                note="Precision shaft journal press-fit match."
            ))

    # 2. Internal Radial Clearance (Thermal Expansion Allowance)
    s_clr = (source.bearing_clearance or "C3").strip().upper()
    c_clr = (candidate.bearing_clearance or "CN").strip().upper()

    s_rank = CLEARANCE_RANK.get(s_clr, 3)
    c_rank = CLEARANCE_RANK.get(c_clr, 2)

    if c_rank < s_rank:
        violations.append(ToleranceViolation(
            rule_name="Radial Internal Clearance Rule",
            field="bearing_clearance",
            expected=s_clr,
            actual=c_clr,
            message=f"BEARING SEIZURE TRAP: Hot rotating equipment requiring {s_clr} clearance will seize if installed with normal {c_clr} clearance due to shaft thermal expansion."
        ))
        checks.append(ParameterMatchDetail(
            parameter="Internal Radial Clearance",
            matched=False,
            status="MISMATCH",
            source_value=s_clr,
            candidate_value=c_clr,
            note="Insufficient thermal expansion clearance."
        ))
    elif c_rank > s_rank:
        is_upgrade = True
        checks.append(ParameterMatchDetail(
            parameter="Internal Radial Clearance",
            matched=True,
            status="UPGRADE",
            source_value=s_clr,
            candidate_value=c_clr,
            note=f"High-temperature clearance margin: {c_clr} exceeds required {s_clr} clearance."
        ))
    else:
        checks.append(ParameterMatchDetail(
            parameter="Internal Radial Clearance",
            matched=True,
            status="EXACT",
            source_value=s_clr,
            candidate_value=c_clr,
            note=f"Exact radial clearance match ({s_clr})."
        ))

    return violations, checks, is_upgrade
