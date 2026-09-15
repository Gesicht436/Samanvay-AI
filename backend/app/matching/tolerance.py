"""
Deterministic ASME B16.5 & ASTM Tolerance Engine (Tier Distribution System).
Applies deterministic safety checks to classify candidates into:
- Tier-1: IDENTICAL (100% specification parity, safe automatic drop-in)
- Tier-2: SUBSTITUTE (Valid engineering upgrade meeting or exceeding specs, requires review)
- Tier-3: INCOMPATIBLE (Hard safety reject: size mismatch, down-rating, bad metallurgy)
"""

from typing import List, Optional
from backend.app.contracts.material import ExtractedMaterialAttributes
from backend.app.contracts.matching import (
    EquivalenceTier,
    ToleranceViolation,
    ParameterMatchDetail,
    MatchEvaluationResult,
    MatchCandidate,
)
from backend.app.matching.asme_rules import (
    evaluate_metallurgy_compatibility,
    evaluate_pressure_class,
    evaluate_facing_compatibility,
    normalize_metallurgy,
)
from backend.app.matching.rotating_rules import (
    evaluate_flameproof_motor,
    evaluate_mechanical_seal,
    evaluate_industrial_bearing,
)
from backend.app.matching.piping_spec_rules import (
    evaluate_pipe_schedule,
    evaluate_sour_service,
    evaluate_large_flange_series,
    evaluate_gasket_spec,
    evaluate_fastener_spec,
    evaluate_ibr_certification,
)


def evaluate_compatibility(
    source: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes,
    candidate_id: Optional[str] = None
) -> MatchEvaluationResult:
    """
    Evaluates engineering compatibility between a requested source component
    and a candidate inventory item.
    """
    violations: List[ToleranceViolation] = []
    parameter_checks: List[ParameterMatchDetail] = []
    is_upgrade = False
    notes: List[str] = []

    # -------------------------------------------------------------------------
    # 1. ITEM TYPE CHECK (Mechanical Function Invariant)
    # -------------------------------------------------------------------------
    s_type = (source.item_type or "").strip().upper()
    c_type = (candidate.item_type or "").strip().upper()
    
    if s_type and c_type:
        if s_type == c_type:
            parameter_checks.append(ParameterMatchDetail(
                parameter="Item Type",
                matched=True,
                status="EXACT",
                source_value=s_type,
                candidate_value=c_type,
                note="Identical mechanical component type."
            ))
        else:
            violations.append(ToleranceViolation(
                rule_name="Item Type Invariant",
                field="item_type",
                expected=s_type,
                actual=c_type,
                message=f"Functional type mismatch: Cannot substitute {s_type} with {c_type}."
            ))
            parameter_checks.append(ParameterMatchDetail(
                parameter="Item Type",
                matched=False,
                status="MISMATCH",
                source_value=s_type,
                candidate_value=c_type,
                note=f"Incompatible equipment category ({s_type} != {c_type})."
            ))
    elif s_type and not c_type:
        violations.append(ToleranceViolation(
            rule_name="Item Type Invariant",
            field="item_type",
            expected=s_type,
            actual="UNSPECIFIED",
            message=f"Candidate equipment type is unspecified; cannot verify mechanical parity with requested {s_type}."
        ))
        parameter_checks.append(ParameterMatchDetail(
            parameter="Item Type",
            matched=False,
            status="MISMATCH",
            source_value=s_type,
            candidate_value="UNSPECIFIED",
            note="Missing candidate equipment type."
        ))

    # -------------------------------------------------------------------------
    # 1B. ROTATING & ELECTRICAL DOMAIN SPECIFIC CHECKS
    # -------------------------------------------------------------------------
    is_rotating_or_electrical = False

    if "MOTOR" in s_type or "MOTOR" in c_type:
        is_rotating_or_electrical = True
        r_v, r_p, r_up = evaluate_flameproof_motor(source, candidate)
        violations.extend(r_v)
        parameter_checks.extend(r_p)
        if r_up:
            is_upgrade = True
            notes.append("Flameproof motor power / enclosure upgrade.")

    elif "SEAL" in s_type or "SEAL" in c_type:
        is_rotating_or_electrical = True
        r_v, r_p, r_up = evaluate_mechanical_seal(source, candidate)
        violations.extend(r_v)
        parameter_checks.extend(r_p)
        if r_up:
            is_upgrade = True
            notes.append("API 682 mechanical seal arrangement upgrade.")

    elif "BEARING" in s_type or "BEARING" in c_type:
        is_rotating_or_electrical = True
        r_v, r_p, r_up = evaluate_industrial_bearing(source, candidate)
        violations.extend(r_v)
        parameter_checks.extend(r_p)
        if r_up:
            is_upgrade = True
            notes.append("High-temperature thermal expansion clearance upgrade.")

    # -------------------------------------------------------------------------
    # 2. NOMINAL BORE SIZE CHECK (Zero Tolerance Physical Invariant)
    # -------------------------------------------------------------------------
    s_size = source.size_nb_mm
    c_size = candidate.size_nb_mm

    if not is_rotating_or_electrical:
        if s_size is not None and c_size is not None:
            if abs(s_size - c_size) < 0.1:
                parameter_checks.append(ParameterMatchDetail(
                    parameter="Size (NB mm)",
                    matched=True,
                    status="EXACT",
                    source_value=f"{s_size} mm",
                    candidate_value=f"{c_size} mm",
                    note="Exact dimensional bore diameter match."
                ))
            else:
                violations.append(ToleranceViolation(
                    rule_name="Nominal Bore Physical Invariant",
                    field="size_nb_mm",
                    expected=f"{s_size} mm",
                    actual=f"{c_size} mm",
                    message=f"ZERO TOLERANCE VIOLATION: Pipe bore size mismatch ({s_size} mm != {c_size} mm). Mating pipe flanges will not fit."
                ))
                parameter_checks.append(ParameterMatchDetail(
                    parameter="Size (NB mm)",
                    matched=False,
                    status="MISMATCH",
                    source_value=f"{s_size} mm",
                    candidate_value=f"{c_size} mm",
                    note=f"Dimensional bore mismatch ({s_size}mm != {c_size}mm)."
                ))
        elif s_size is not None and c_size is None:
            violations.append(ToleranceViolation(
                rule_name="Nominal Bore Physical Invariant",
                field="size_nb_mm",
                expected=f"{s_size} mm",
                actual="UNSPECIFIED",
                message="Candidate nominal bore size is unspecified; cannot verify physical mating dimensions."
            ))
            parameter_checks.append(ParameterMatchDetail(
                parameter="Size (NB mm)",
                matched=False,
                status="MISMATCH",
                source_value=f"{s_size} mm",
                candidate_value="UNSPECIFIED",
                note="Missing candidate nominal bore."
            ))

    # -------------------------------------------------------------------------
    # 3. PRESSURE CLASS RATING (ASME B16.5 Unidirectional Invariant)
    # -------------------------------------------------------------------------
    s_press = source.pressure_class
    c_press = candidate.pressure_class

    if s_press is not None and c_press is not None:
        p_ok, p_is_upgrade, p_msg = evaluate_pressure_class(s_press, c_press)
        if not p_ok:
            violations.append(ToleranceViolation(
                rule_name="ASME B16.5 Pressure Rating Rule",
                field="pressure_class",
                expected=f"Class {s_press} minimum",
                actual=f"Class {c_press}",
                message=p_msg
            ))
            parameter_checks.append(ParameterMatchDetail(
                parameter="Pressure Class",
                matched=False,
                status="MISMATCH",
                source_value=f"Class {s_press}",
                candidate_value=f"Class {c_press}",
                note=p_msg
            ))
        elif p_is_upgrade:
            is_upgrade = True
            notes.append(p_msg)
            parameter_checks.append(ParameterMatchDetail(
                parameter="Pressure Class",
                matched=True,
                status="UPGRADE",
                source_value=f"Class {s_press}",
                candidate_value=f"Class {c_press}",
                note=p_msg
            ))
        else:
            parameter_checks.append(ParameterMatchDetail(
                parameter="Pressure Class",
                matched=True,
                status="EXACT",
                source_value=f"Class {s_press}",
                candidate_value=f"Class {c_press}",
                note="Exact ASME pressure rating parity."
            ))
    elif s_press is not None and c_press is None:
        violations.append(ToleranceViolation(
            rule_name="ASME B16.5 Pressure Rating Rule",
            field="pressure_class",
            expected=f"Class {s_press} minimum",
            actual="UNSPECIFIED",
            message="Candidate pressure class rating is unspecified; cannot certify pressure containment."
        ))
        parameter_checks.append(ParameterMatchDetail(
            parameter="Pressure Class",
            matched=False,
            status="MISMATCH",
            source_value=f"Class {s_press}",
            candidate_value="UNSPECIFIED",
            note="Missing candidate pressure rating."
        ))

    # -------------------------------------------------------------------------
    # 4. METALLURGY SPECIFICATION (ASTM Directed Compatibility Graph)
    # -------------------------------------------------------------------------
    s_mat = source.metallurgy
    c_mat = candidate.metallurgy

    if s_mat and c_mat:
        m_ok, m_is_upgrade, m_msg = evaluate_metallurgy_compatibility(s_mat, c_mat)
        if not m_ok:
            violations.append(ToleranceViolation(
                rule_name="ASTM Metallurgy Safety Rule",
                field="metallurgy",
                expected=normalize_metallurgy(s_mat),
                actual=normalize_metallurgy(c_mat),
                message=m_msg
            ))
            parameter_checks.append(ParameterMatchDetail(
                parameter="Metallurgy",
                matched=False,
                status="MISMATCH",
                source_value=normalize_metallurgy(s_mat),
                candidate_value=normalize_metallurgy(c_mat),
                note=m_msg
            ))
        elif m_is_upgrade:
            is_upgrade = True
            notes.append(m_msg)
            parameter_checks.append(ParameterMatchDetail(
                parameter="Metallurgy",
                matched=True,
                status="UPGRADE",
                source_value=normalize_metallurgy(s_mat),
                candidate_value=normalize_metallurgy(c_mat),
                note=m_msg
            ))
        else:
            parameter_checks.append(ParameterMatchDetail(
                parameter="Metallurgy",
                matched=True,
                status="EXACT",
                source_value=normalize_metallurgy(s_mat),
                candidate_value=normalize_metallurgy(c_mat),
                note="Exact metallurgical specification match."
            ))
    elif s_mat and not c_mat:
        violations.append(ToleranceViolation(
            rule_name="ASTM Metallurgy Safety Rule",
            field="metallurgy",
            expected=normalize_metallurgy(s_mat),
            actual="UNSPECIFIED",
            message=f"Candidate metallurgy is unspecified; cannot verify compatibility with requested {normalize_metallurgy(s_mat)}."
        ))
        parameter_checks.append(ParameterMatchDetail(
            parameter="Metallurgy",
            matched=False,
            status="MISMATCH",
            source_value=normalize_metallurgy(s_mat),
            candidate_value="UNSPECIFIED",
            note="Missing candidate metallurgy."
        ))

    # -------------------------------------------------------------------------
    # 5. FACING & END CONNECTION (Mating Surface Integrity)
    # -------------------------------------------------------------------------
    s_face = source.facing_end
    c_face = candidate.facing_end

    if s_face and c_face:
        f_ok, f_msg = evaluate_facing_compatibility(s_face, c_face)
        if not f_ok:
            violations.append(ToleranceViolation(
                rule_name="Mating Facing Integrity",
                field="facing_end",
                expected=s_face.upper(),
                actual=c_face.upper(),
                message=f_msg
            ))
            parameter_checks.append(ParameterMatchDetail(
                parameter="Facing / End",
                matched=False,
                status="MISMATCH",
                source_value=s_face.upper(),
                candidate_value=c_face.upper(),
                note=f_msg
            ))
        else:
            parameter_checks.append(ParameterMatchDetail(
                parameter="Facing / End",
                matched=True,
                status="EXACT",
                source_value=s_face.upper(),
                candidate_value=c_face.upper(),
                note=f_msg
            ))
    elif s_face and not c_face:
        if s_face.upper() in ["RTJ", "BW", "SW"]:
            violations.append(ToleranceViolation(
                rule_name="Mating Facing Integrity",
                field="facing_end",
                expected=s_face.upper(),
                actual="UNSPECIFIED",
                message=f"Specialty end connection {s_face.upper()} cannot be assumed on candidate."
            ))
            parameter_checks.append(ParameterMatchDetail(
                parameter="Facing / End",
                matched=False,
                status="MISMATCH",
                source_value=s_face.upper(),
                candidate_value="UNSPECIFIED",
                note=f"Unspecified candidate facing cannot satisfy {s_face.upper()}."
            ))

    # -------------------------------------------------------------------------
    # 6. PIPE SCHEDULE & WALL THICKNESS INVARIANT (ASME B36.10M / B36.19M)
    # -------------------------------------------------------------------------
    sch_v, sch_p, sch_up = evaluate_pipe_schedule(source, candidate)
    violations.extend(sch_v)
    parameter_checks.extend(sch_p)
    if sch_up:
        is_upgrade = True
        notes.append("Heavier pipe wall thickness schedule upgrade.")

    # -------------------------------------------------------------------------
    # 7. SOUR SERVICE & NACE MR0175 / ISO 15156 INVARIANT
    # -------------------------------------------------------------------------
    sour_v, sour_p, sour_up = evaluate_sour_service(source, candidate)
    violations.extend(sour_v)
    parameter_checks.extend(sour_p)
    if sour_up:
        is_upgrade = True
        notes.append("NACE MR0175 / ISO 15156 sour service metallurgy upgrade.")

    # -------------------------------------------------------------------------
    # 8. ASME B16.47 LARGE FLANGE SERIES A vs SERIES B INVARIANT (NPS 26-60)
    # -------------------------------------------------------------------------
    ser_v, ser_p, ser_up = evaluate_large_flange_series(source, candidate)
    violations.extend(ser_v)
    parameter_checks.extend(ser_p)

    # -------------------------------------------------------------------------
    # 9. ASME B16.20 GASKET & ASTM A193/A194 FASTENER COMPLIANCE
    # -------------------------------------------------------------------------
    if source.item_type == "SPIRAL_WOUND_GASKET" or candidate.item_type == "SPIRAL_WOUND_GASKET":
        gsk_v, gsk_p, gsk_up = evaluate_gasket_spec(source, candidate)
        violations.extend(gsk_v)
        parameter_checks.extend(gsk_p)
        if gsk_up:
            is_upgrade = True
            notes.append("Gasket profile or flexible graphite thermal upgrade.")

    if source.item_type == "STUD_BOLT" or candidate.item_type == "STUD_BOLT":
        fast_v, fast_p, fast_up = evaluate_fastener_spec(source, candidate)
        violations.extend(fast_v)
        parameter_checks.extend(fast_p)
        if fast_up:
            is_upgrade = True
            notes.append("Fastener impact toughness / stainless metallurgy upgrade.")

    # -------------------------------------------------------------------------
    # 10. STATUTORY INDIAN BOILER REGULATIONS (IBR 1950) INVARIANT
    # -------------------------------------------------------------------------
    ibr_v, ibr_p, ibr_up = evaluate_ibr_certification(source, candidate)
    violations.extend(ibr_v)
    parameter_checks.extend(ibr_p)
    if ibr_up:
        is_upgrade = True
        notes.append("IBR Form III-C statutory certification upgrade.")

    # -------------------------------------------------------------------------
    # TIER DETERMINATION & CONFIDENCE SCORING
    # -------------------------------------------------------------------------
    if violations:
        tier = EquivalenceTier.TIER_3_INCOMPATIBLE
        is_compatible = False
        confidence_score = 0.0
        requires_hitl = False
        primary_violation = violations[0].message
        rationale = f"REJECTED (Tier-3 Incompatible): {primary_violation}"
    elif is_upgrade:
        tier = EquivalenceTier.TIER_2_SUBSTITUTE
        is_compatible = True
        confidence_score = 0.88
        requires_hitl = True # Tier-2 substitutions recommended for procurement review
        rationale = f"ACCEPT AS SUBSTITUTE (Tier-2 Upgrade): Safe engineering upgrade. {'; '.join(notes)}"
    else:
        tier = EquivalenceTier.TIER_1_IDENTICAL
        is_compatible = True
        confidence_score = 1.0
        requires_hitl = False
        rationale = "ACCEPT (Tier-1 Identical): 100% specification parity across size, rating, metallurgy, and mating interfaces."

    return MatchEvaluationResult(
        tier=tier,
        is_compatible=is_compatible,
        confidence_score=confidence_score,
        violations=violations,
        parameter_checks=parameter_checks,
        rationale=rationale,
        requires_hitl=requires_hitl,
        source_description=source.raw_description,
        candidate_description=candidate.raw_description,
        candidate_canonical_id=candidate_id
    )


def evaluate_candidate_pool(
    source: ExtractedMaterialAttributes,
    candidates: List[MatchCandidate]
) -> List[MatchEvaluationResult]:
    """
    Evaluates an entire candidate pool retrieved from vector search.
    Sorts results with Tier-1 first, then Tier-2, then Tier-3.
    """
    results: List[MatchEvaluationResult] = []
    for cand in candidates:
        res = evaluate_compatibility(
            source=source,
            candidate=cand.attributes,
            candidate_id=cand.canonical_id
        )
        res.candidate_description = cand.description
        # Blend vector similarity score with rule confidence for ranking
        if res.is_compatible:
            res.confidence_score = round(0.5 * cand.vector_score + 0.5 * res.confidence_score, 3)
        results.append(res)

    # Sort order: Tier-1 (0) -> Tier-2 (1) -> Tier-3 (2), then highest confidence first
    tier_priority = {
        EquivalenceTier.TIER_1_IDENTICAL: 0,
        EquivalenceTier.TIER_2_SUBSTITUTE: 1,
        EquivalenceTier.TIER_3_INCOMPATIBLE: 2
    }
    results.sort(key=lambda r: (tier_priority[r.tier], -r.confidence_score))
    return results
