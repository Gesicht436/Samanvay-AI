"""
Deterministic Piping Specification Rules (ASME B36.10M, ASME B16.47, ASME B16.20, NACE MR0175, ASTM A193/A194).
Domain engineering invariants for pipe schedules, sour service, large diameter flanges, gaskets, and fasteners.
"""

from typing import Tuple, List, Optional, Dict
from backend.app.contracts.material import ExtractedMaterialAttributes
from backend.app.contracts.matching import ToleranceViolation, ParameterMatchDetail


# -----------------------------------------------------------------------------
# 1. Pipe Schedule & Wall Thickness Ladder (ASME B36.10M & ASME B36.19M)
# -----------------------------------------------------------------------------

SCHEDULE_ORDER: Dict[str, int] = {
    "SCH 5": 5,
    "SCH 5S": 5,
    "SCH 10": 10,
    "SCH 10S": 10,
    "SCH 20": 20,
    "SCH 30": 30,
    "SCH 40": 40,
    "SCH 40S": 40,
    "STD": 40,
    "STANDARD": 40,
    "SCH 60": 60,
    "SCH 80": 80,
    "SCH 80S": 80,
    "XS": 80,
    "EXTRA STRONG": 80,
    "SCH 100": 100,
    "SCH 120": 120,
    "SCH 140": 140,
    "SCH 160": 160,
    "XXS": 200,
    "DOUBLE EXTRA STRONG": 200,
}


def normalize_schedule(sch: Optional[str]) -> Optional[str]:
    """Standardizes schedule representations into canonical designations."""
    if not sch:
        return None
    s = sch.strip().upper().replace("-", " ").replace("SCHEDULE", "SCH")
    s = " ".join(s.split())
    if s in ["STD", "STANDARD"]:
        return "SCH 40 / STD"
    if s in ["XS", "EXTRA STRONG"]:
        return "SCH 80 / XS"
    if s in ["XXS", "DOUBLE EXTRA STRONG"]:
        return "SCH XXS"
    if s.startswith("SCH") and not s.startswith("SCH "):
        s = s.replace("SCH", "SCH ")
    return s


def get_schedule_rank(sch: Optional[str]) -> Optional[int]:
    """Returns integer rank representing pressure containment capacity."""
    if not sch:
        return None
    s = sch.strip().upper().replace("-", " ")
    for k, rank in SCHEDULE_ORDER.items():
        if k in s:
            return rank
    return None


def evaluate_pipe_schedule(
    source: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes
) -> Tuple[List[ToleranceViolation], List[ParameterMatchDetail], bool]:
    """
    Evaluates ASME B36.10M / B36.19M wall thickness schedule compatibility.
    - Heavier schedule = valid functional upgrade (exceeds pressure containment, but restricts internal bore).
    - Lighter schedule = FATAL SAFETY VIOLATION (pipe rupture risk under line pressure).
    """
    violations: List[ToleranceViolation] = []
    parameters: List[ParameterMatchDetail] = []
    is_upgrade = False

    s_sch = source.schedule
    c_sch = candidate.schedule

    if s_sch is None and c_sch is None:
        return violations, parameters, is_upgrade

    norm_s = normalize_schedule(s_sch)
    norm_c = normalize_schedule(c_sch)
    rank_s = get_schedule_rank(s_sch)
    rank_c = get_schedule_rank(c_sch)

    if rank_s is not None and rank_c is not None:
        if rank_s == rank_c:
            parameters.append(ParameterMatchDetail(
                parameter="Pipe Schedule / Wall Thickness",
                matched=True,
                status="EXACT",
                source_value=norm_s or s_sch,
                candidate_value=norm_c or c_sch,
                note="Exact ASME B36.10M wall thickness schedule parity."
            ))
        elif rank_c > rank_s:
            is_upgrade = True
            note_msg = (
                f"Schedule upgrade ({norm_c} > {norm_s}): Heavier wall thickness increases pressure containment capacity; "
                f"note internal bore restriction and line flow velocity."
            )
            parameters.append(ParameterMatchDetail(
                parameter="Pipe Schedule / Wall Thickness",
                matched=True,
                status="UPGRADE",
                source_value=norm_s or s_sch,
                candidate_value=norm_c or c_sch,
                note=note_msg
            ))
        else:
            # Fatal down-schedule
            v_msg = (
                f"ZERO TOLERANCE SAFETY VIOLATION: Wall thickness downgrade from {norm_s} to {norm_c}. "
                f"Thinner pipe wall will fail under design internal pressure according to ASME B31.3 process piping rules."
            )
            violations.append(ToleranceViolation(
                rule_name="ASME B36.10M Pipe Schedule Invariant",
                field="schedule",
                expected=norm_s or s_sch,
                actual=norm_c or c_sch,
                message=v_msg
            ))
            parameters.append(ParameterMatchDetail(
                parameter="Pipe Schedule / Wall Thickness",
                matched=False,
                status="MISMATCH",
                source_value=norm_s or s_sch,
                candidate_value=norm_c or c_sch,
                note=v_msg
            ))
    elif rank_s is not None and rank_c is None:
        v_msg = f"Candidate pipe schedule is unspecified; cannot verify required pressure containment for {norm_s}."
        violations.append(ToleranceViolation(
            rule_name="ASME B36.10M Pipe Schedule Invariant",
            field="schedule",
            expected=norm_s or s_sch,
            actual="UNSPECIFIED",
            message=v_msg
        ))
        parameters.append(ParameterMatchDetail(
            parameter="Pipe Schedule / Wall Thickness",
            matched=False,
            status="MISMATCH",
            source_value=norm_s or s_sch,
            candidate_value="UNSPECIFIED",
            note=v_msg
        ))

    return violations, parameters, is_upgrade


# -----------------------------------------------------------------------------
# 2. Sour Service & NACE MR0175 / ISO 15156 Invariants
# -----------------------------------------------------------------------------

def evaluate_sour_service(
    source: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes
) -> Tuple[List[ToleranceViolation], List[ParameterMatchDetail], bool]:
    """
    Evaluates NACE MR0175 / ISO 15156 sour service compliance for wet H2S environments.
    - Standard non-NACE material CANNOT be placed in sour service (rapid cracking risk).
    - NACE material CAN safely replace standard non-sour material (superior metallurgical control).
    """
    violations: List[ToleranceViolation] = []
    parameters: List[ParameterMatchDetail] = []
    is_upgrade = False

    s_sour = bool(source.is_sour_service)
    c_sour = bool(candidate.is_sour_service)

    if not s_sour and not c_sour:
        return violations, parameters, is_upgrade

    if s_sour and c_sour:
        parameters.append(ParameterMatchDetail(
            parameter="Sour Service (NACE MR0175)",
            matched=True,
            status="EXACT",
            source_value="NACE MR0175 / ISO 15156 Compliant",
            candidate_value="NACE MR0175 / ISO 15156 Compliant",
            note="Full NACE MR0175 / ISO 15156 compliance parity for wet H2S sour service."
        ))
    elif s_sour and not c_sour:
        v_msg = (
            "NACE SOUR SERVICE FATAL VIOLATION: Source requisition specifies NACE MR0175 / ISO 15156 sour service. "
            "Standard commercial material lacks controlled hardness (<= 22 HRC) and heat treatment, risking catastrophic "
            "Sulfide Stress Cracking (SSC) and Hydrogen-Induced Cracking (HIC) in sour hydrocarbon service."
        )
        violations.append(ToleranceViolation(
            rule_name="NACE MR0175 Sour Service Invariant",
            field="is_sour_service",
            expected="NACE MR0175 Compliant",
            actual="Standard / Non-NACE",
            message=v_msg
        ))
        parameters.append(ParameterMatchDetail(
            parameter="Sour Service (NACE MR0175)",
            matched=False,
            status="MISMATCH",
            source_value="NACE MR0175 Compliant",
            candidate_value="Standard / Non-NACE",
            note=v_msg
        ))
    elif not s_sour and c_sour:
        is_upgrade = True
        note_msg = (
            "NACE metallurgical upgrade: Candidate is certified NACE MR0175 / ISO 15156 compliant, "
            "exceeding standard service requirements with rigorous hardness testing and chemistry controls."
        )
        parameters.append(ParameterMatchDetail(
            parameter="Sour Service (NACE MR0175)",
            matched=True,
            status="UPGRADE",
            source_value="Standard Service",
            candidate_value="NACE MR0175 Compliant",
            note=note_msg
        ))

    return violations, parameters, is_upgrade


# -----------------------------------------------------------------------------
# 3. ASME B16.47 Large Flange Series A vs Series B Invariant (NPS 26 to 60)
# -----------------------------------------------------------------------------

def evaluate_large_flange_series(
    source: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes
) -> Tuple[List[ToleranceViolation], List[ParameterMatchDetail], bool]:
    """
    Evaluates ASME B16.47 Series A (MSS SP-44) vs Series B (API 605) for large diameter flanges (NPS 26-60).
    Series A and Series B have completely different bolt circles, bolt hole counts, and dimensions.
    They are STRICTLY NON-INTERCHANGEABLE.
    """
    violations: List[ToleranceViolation] = []
    parameters: List[ParameterMatchDetail] = []
    is_upgrade = False

    # Check if item is a large flange (>= 26 inches = 650 mm NB) or specifies series
    s_size = source.size_nb_mm or 0.0
    c_size = candidate.size_nb_mm or 0.0
    is_large = (s_size >= 650.0 or c_size >= 650.0)

    s_series = source.flange_series
    c_series = candidate.flange_series

    if not is_large and not s_series and not c_series:
        return violations, parameters, is_upgrade

    if s_series and c_series:
        if s_series.upper() == c_series.upper():
            series_label = "Series A (MSS SP-44)" if "A" in s_series.upper() else "Series B (API 605)"
            parameters.append(ParameterMatchDetail(
                parameter="ASME B16.47 Flange Series",
                matched=True,
                status="EXACT",
                source_value=series_label,
                candidate_value=series_label,
                note="Exact ASME B16.47 large diameter flange series parity."
            ))
        else:
            v_msg = (
                f"BOLT CIRCLE MISALIGNMENT: Cannot substitute ASME B16.47 {s_series} with {c_series}. "
                f"Series A (MSS SP-44) and Series B (API 605) have completely different bolt circle diameters (BCD), "
                f"bolt hole counts, and flange thicknesses. They will not bolt together."
            )
            violations.append(ToleranceViolation(
                rule_name="ASME B16.47 Series Invariant",
                field="flange_series",
                expected=s_series,
                actual=c_series,
                message=v_msg
            ))
            parameters.append(ParameterMatchDetail(
                parameter="ASME B16.47 Flange Series",
                matched=False,
                status="MISMATCH",
                source_value=s_series,
                candidate_value=c_series,
                note=v_msg
            ))
    elif s_series and not c_series and is_large:
        v_msg = (
            f"Candidate large diameter flange (NPS >= 26) lacks required ASME B16.47 {s_series} specification; "
            f"cannot verify bolt circle alignment."
        )
        violations.append(ToleranceViolation(
            rule_name="ASME B16.47 Series Invariant",
            field="flange_series",
            expected=s_series,
            actual="UNSPECIFIED",
            message=v_msg
        ))
        parameters.append(ParameterMatchDetail(
            parameter="ASME B16.47 Flange Series",
            matched=False,
            status="MISMATCH",
            source_value=s_series,
            candidate_value="UNSPECIFIED",
            note=v_msg
        ))

    return violations, parameters, is_upgrade


# -----------------------------------------------------------------------------
# 4. ASME B16.20 Gasket & ASTM A193/A194 Fastener Rules
# -----------------------------------------------------------------------------

GASKET_FILLER_SAFETY: Dict[Tuple[str, str], Tuple[bool, bool, str]] = {
    ("GRAPHITE", "GRAPHITE"): (True, False, "Flexible graphite filler parity (rated to 650°C, fire-safe)."),
    ("PTFE", "PTFE"): (True, False, "PTFE filler parity (chemical resistant, max 260°C)."),
    ("GRAPHITE", "PTFE"): (
        False,
        False,
        "GASKET TEMPERATURE HAZARD: PTFE filler has a maximum temperature limit of 260°C and suffers cold flow; "
        "cannot replace fire-safe flexible graphite in high-temperature hydrocarbon service."
    ),
    ("PTFE", "GRAPHITE"): (
        True,
        True,
        "Thermal upgrade: Flexible graphite filler withstands higher operating temperatures and fire-safe conditions than PTFE."
    ),
}

FASTENER_BOLT_HIERARCHY: Dict[str, int] = {
    "ASTM A193 B7": 1,
    "ASTM A320 L7": 2,      # Cryogenic impact tested at -101°C
    "ASTM A193 B8M": 3,     # SS316 Stainless Steel
}


def evaluate_gasket_spec(
    source: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes
) -> Tuple[List[ToleranceViolation], List[ParameterMatchDetail], bool]:
    """
    Evaluates ASME B16.20 metallic gasket specifications (Spiral Wound vs Ring Joint, fillers).
    """
    violations: List[ToleranceViolation] = []
    parameters: List[ParameterMatchDetail] = []
    is_upgrade = False

    s_type = source.gasket_type or ""
    c_type = candidate.gasket_type or ""

    if not s_type and not c_type:
        return violations, parameters, is_upgrade

    if s_type and c_type:
        if s_type.upper() == c_type.upper():
            parameters.append(ParameterMatchDetail(
                parameter="Gasket Profile",
                matched=True,
                status="EXACT",
                source_value=s_type,
                candidate_value=c_type,
                note=f"Exact ASME B16.20 {s_type} gasket profile parity."
            ))
        elif "OVAL" in s_type.upper() and "OCTAGONAL" in c_type.upper():
            is_upgrade = True
            parameters.append(ParameterMatchDetail(
                parameter="Gasket Profile",
                matched=True,
                status="UPGRADE",
                source_value=s_type,
                candidate_value=c_type,
                note="Octagonal RTJ ring provides superior sealing efficiency over legacy oval profile."
            ))
        else:
            v_msg = f"Gasket profile mismatch: Cannot substitute {s_type} with {c_type}."
            violations.append(ToleranceViolation(
                rule_name="ASME B16.20 Gasket Profile Invariant",
                field="gasket_type",
                expected=s_type,
                actual=c_type,
                message=v_msg
            ))
            parameters.append(ParameterMatchDetail(
                parameter="Gasket Profile",
                matched=False,
                status="MISMATCH",
                source_value=s_type,
                candidate_value=c_type,
                note=v_msg
            ))

    # Filler evaluation
    s_fill = (source.gasket_filler or "").upper()
    c_fill = (candidate.gasket_filler or "").upper()

    if s_fill and c_fill:
        key = (s_fill, c_fill)
        if key in GASKET_FILLER_SAFETY:
            is_ok, fill_up, fill_msg = GASKET_FILLER_SAFETY[key]
            if not is_ok:
                violations.append(ToleranceViolation(
                    rule_name="ASME B16.20 Gasket Filler Safety Rule",
                    field="gasket_filler",
                    expected=s_fill,
                    actual=c_fill,
                    message=fill_msg
                ))
                parameters.append(ParameterMatchDetail(
                    parameter="Gasket Filler Material",
                    matched=False,
                    status="MISMATCH",
                    source_value=s_fill,
                    candidate_value=c_fill,
                    note=fill_msg
                ))
            elif fill_up:
                is_upgrade = True
                parameters.append(ParameterMatchDetail(
                    parameter="Gasket Filler Material",
                    matched=True,
                    status="UPGRADE",
                    source_value=s_fill,
                    candidate_value=c_fill,
                    note=fill_msg
                ))
            else:
                parameters.append(ParameterMatchDetail(
                    parameter="Gasket Filler Material",
                    matched=True,
                    status="EXACT",
                    source_value=s_fill,
                    candidate_value=c_fill,
                    note=fill_msg
                ))

    return violations, parameters, is_upgrade


def evaluate_fastener_spec(
    source: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes
) -> Tuple[List[ToleranceViolation], List[ParameterMatchDetail], bool]:
    """
    Evaluates ASTM A193 / A194 / A320 fastener grades for high-temp, cryogenic, and corrosive service.
    """
    violations: List[ToleranceViolation] = []
    parameters: List[ParameterMatchDetail] = []
    is_upgrade = False

    s_bolt = source.bolt_grade
    c_bolt = candidate.bolt_grade

    if not s_bolt and not c_bolt:
        return violations, parameters, is_upgrade

    if s_bolt and c_bolt:
        if s_bolt == c_bolt:
            parameters.append(ParameterMatchDetail(
                parameter="Fastener Stud Grade",
                matched=True,
                status="EXACT",
                source_value=s_bolt,
                candidate_value=c_bolt,
                note=f"Exact stud bolt grade match: {s_bolt}."
            ))
        elif "L7" in s_bolt and "B7" in c_bolt:
            v_msg = (
                "CRYOGENIC FASTENER FATAL VIOLATION: ASTM A320 L7 is Charpy impact tested at -101°C. "
                "Standard ASTM A193 B7 lacks cryogenic toughness and risks catastrophic brittle failure in sub-zero service."
            )
            violations.append(ToleranceViolation(
                rule_name="ASTM Fastener Temperature Rule",
                field="bolt_grade",
                expected=s_bolt,
                actual=c_bolt,
                message=v_msg
            ))
            parameters.append(ParameterMatchDetail(
                parameter="Fastener Stud Grade",
                matched=False,
                status="MISMATCH",
                source_value=s_bolt,
                candidate_value=c_bolt,
                note=v_msg
            ))
        elif "B8M" in s_bolt and "B7" in c_bolt:
            v_msg = "CORROSION FASTENER VIOLATION: Stainless Steel A193 B8M cannot be replaced by Carbon Steel B7."
            violations.append(ToleranceViolation(
                rule_name="ASTM Fastener Metallurgy Rule",
                field="bolt_grade",
                expected=s_bolt,
                actual=c_bolt,
                message=v_msg
            ))
            parameters.append(ParameterMatchDetail(
                parameter="Fastener Stud Grade",
                matched=False,
                status="MISMATCH",
                source_value=s_bolt,
                candidate_value=c_bolt,
                note=v_msg
            ))
        elif "B7" in s_bolt and "L7" in c_bolt:
            is_upgrade = True
            parameters.append(ParameterMatchDetail(
                parameter="Fastener Stud Grade",
                matched=True,
                status="UPGRADE",
                source_value=s_bolt,
                candidate_value=c_bolt,
                note="Cryogenic grade L7 exceeds standard B7 impact toughness specifications."
            ))
        elif "B7" in s_bolt and "B8M" in c_bolt:
            is_upgrade = True
            parameters.append(ParameterMatchDetail(
                parameter="Fastener Stud Grade",
                matched=True,
                status="UPGRADE",
                source_value=s_bolt,
                candidate_value=c_bolt,
                note="Stainless B8M provides superior chemical and corrosion resistance over standard B7."
            ))

    return violations, parameters, is_upgrade


# -----------------------------------------------------------------------------
# 6. Indian Boiler Regulations (IBR 1950) Statutory Compliance Invariant
# -----------------------------------------------------------------------------

def evaluate_ibr_certification(
    source: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes
) -> Tuple[List[ToleranceViolation], List[ParameterMatchDetail], bool]:
    """
    Evaluates statutory Indian Boiler Regulations (IBR 1950) certification requirements.
    Steam piping and pressure parts under IBR jurisdiction strictly require IBR Form III-C certification.
    Deploying a non-IBR certified component into an IBR system is an illegal statutory violation.
    """
    violations: List[ToleranceViolation] = []
    parameters: List[ParameterMatchDetail] = []
    is_upgrade = False

    s_ibr = source.is_ibr_certified
    c_ibr = candidate.is_ibr_certified

    if s_ibr is None and c_ibr is None:
        return violations, parameters, is_upgrade

    if s_ibr and c_ibr:
        parameters.append(ParameterMatchDetail(
            parameter="IBR Certification",
            matched=True,
            status="EXACT",
            source_value="IBR Certified (Form III-C)",
            candidate_value="IBR Certified (Form III-C)",
            note="Both items are certified under Indian Boiler Regulations (IBR 1950)."
        ))
    elif s_ibr and (c_ibr is False or c_ibr is None):
        v_msg = (
            "STATUTORY IBR VIOLATION: Source requires Indian Boiler Regulations (IBR 1950) certification. "
            "Candidate lacks valid IBR Form III-C certification and cannot be legally installed in boiler/steam duty."
        )
        violations.append(ToleranceViolation(
            rule_name="Indian Boiler Regulations (IBR) Invariant",
            field="is_ibr_certified",
            expected="IBR Certified",
            actual="Non-IBR / Uncertified",
            message=v_msg
        ))
        parameters.append(ParameterMatchDetail(
            parameter="IBR Certification",
            matched=False,
            status="MISMATCH",
            source_value="IBR Certified",
            candidate_value="Non-IBR / Uncertified",
            note=v_msg
        ))
    elif not s_ibr and c_ibr:
        is_upgrade = True
        note_msg = (
            "IBR certification upgrade: Candidate has statutory Indian Boiler Regulations (IBR) Form III-C certification, "
            "exceeding standard industrial service requirements."
        )
        parameters.append(ParameterMatchDetail(
            parameter="IBR Certification",
            matched=True,
            status="UPGRADE",
            source_value="Standard Non-IBR",
            candidate_value="IBR Certified",
            note=note_msg
        ))

    return violations, parameters, is_upgrade
