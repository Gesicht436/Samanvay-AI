"""
Samanvay-AI Master Tolerance Evaluation Engine.

Receives extracted physical attributes from query Q and candidate C,
applies the immutable set of 21 codified engineering safety rules,
and returns a CompatibilityResult with property scorecard, violations,
and the final dynamic compatibility tier.

Probabilistic AI vector similarity is mathematically prohibited from
overriding any deterministic rule returned by this engine.
"""

from typing import Optional

from backend.app.schemas.material import (
    CompatibilityResult,
    DynamicCompatibilityTier,
    ExtractedMaterialAttributes,
    PropertyEvaluation,
    PropertyEvaluationStatus,
    PropertyScorecard,
    RuleViolation,
)
from rules.asme.pressure_class import check_pressure_class, check_pressure_rating_psi
from rules.astm.metallurgy_dag import check_metallurgy


# ── Schedule Hierarchy ────────────────────────────────────────────────────
SCHEDULE_ORDER = [
    "SCH 5", "SCH 5S", "SCH 10", "SCH 10S", "SCH 20", "SCH 30",
    "STD", "SCH 40", "SCH 40S", "SCH 60",
    "XS", "SCH 80", "SCH 80S",
    "SCH 100", "SCH 120", "SCH 140", "SCH 160", "XXS",
]


def _normalize_schedule(sch: str | None) -> str | None:
    if not sch:
        return None
    return sch.strip().upper().replace("SCHEDULE ", "SCH ").replace("  ", " ")


def _schedule_index(sch: str) -> int:
    norm = _normalize_schedule(sch)
    if not norm:
        return -1
    for i, s in enumerate(SCHEDULE_ORDER):
        if norm == s:
            return i
    return -1


# ── Facing Compatibility ─────────────────────────────────────────────────
_COMPATIBLE_FACINGS = {
    ("RF", "RF"), ("RTJ", "RTJ"), ("FF", "FF"), ("BW", "BW"),
    ("SW", "SW"), ("NPT", "NPT"), ("BE", "BE"),
}


def _check_facing(query_facing: str | None, candidate_facing: str | None) -> tuple[
    DynamicCompatibilityTier, float, RuleViolation | None
]:
    if not query_facing or not candidate_facing:
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)

    qf = query_facing.strip().upper()
    cf = candidate_facing.strip().upper()

    if qf == cf:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    if (qf, cf) not in _COMPATIBLE_FACINGS and (cf, qf) not in _COMPATIBLE_FACINGS:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B16_5_FACING",
                standard_code="ASME B16.5",
                failure_mode_prevented="Joint seal failure due to incompatible flange facing geometry",
                explanation=(
                    f"FACING MISMATCH: Query requires '{qf}' facing. "
                    f"Candidate has '{cf}' facing. These facing types are mechanically "
                    f"incompatible and cannot seal properly."
                ),
            ),
        )

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)


def _check_dimensions(
    query: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes,
) -> tuple[DynamicCompatibilityTier, float, RuleViolation | None]:
    """
    Zero-tolerance dimensional check. If primary dimensions differ,
    FORCE Tier 3 with 0% compatibility. No exceptions.
    """
    q_size = query.size_nb_mm
    c_size = candidate.size_nb_mm

    if q_size is None or c_size is None:
        # Cannot verify dimensions — HITL required
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)

    if abs(q_size - c_size) < 0.01:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    return (
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        0.0,
        RuleViolation(
            module_name="DIMENSIONAL_ZERO_TOLERANCE",
            standard_code="ASME B16.5 / B36.10M",
            failure_mode_prevented="Physical dimensional mismatch — part does not fit line",
            explanation=(
                f"DIMENSIONAL MISMATCH: Query requires {q_size:.1f} mm NB. "
                f"Candidate is {c_size:.1f} mm NB. Parts with different nominal "
                f"bore dimensions cannot physically mate and are strictly incompatible."
            ),
        ),
    )


def _check_schedule(
    query: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes,
) -> tuple[DynamicCompatibilityTier, float, RuleViolation | None]:
    """ASME B36.10M/B36.19M schedule check."""
    q_sch = query.schedule
    c_sch = candidate.schedule

    if not q_sch or not c_sch:
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)

    q_idx = _schedule_index(q_sch)
    c_idx = _schedule_index(c_sch)

    if q_idx < 0 or c_idx < 0:
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.82, None)

    if q_idx == c_idx:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    if c_idx < q_idx:
        # Down-scheduling — burst hazard
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B36_10M",
                standard_code="ASME B36.10M",
                failure_mode_prevented="Thin-wall pipe burst under hoop stress",
                explanation=(
                    f"SCHEDULE DOWN-RATING: Candidate '{_normalize_schedule(c_sch)}' has thinner "
                    f"wall than required '{_normalize_schedule(q_sch)}'. Down-scheduling risks "
                    f"burst under operating hoop stress."
                ),
            ),
        )

    # Schedule upgrade — Tier 2 (check flow reduction vs. pressure safety)
    return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.90, None)


def _check_equipment_specific(
    query: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes,
) -> list[tuple[str, DynamicCompatibilityTier, float, RuleViolation | None]]:
    """Check equipment-specific properties from the properties dict."""
    results: list[tuple[str, DynamicCompatibilityTier, float, RuleViolation | None]] = []
    q_props = query.properties or {}
    c_props = candidate.properties or {}

    # ── Valve Trim Check (API 600) ───────────────────────────────
    q_trim = q_props.get("trim_no")
    c_trim = c_props.get("trim_no")
    if q_trim is not None and c_trim is not None:
        trim_order = [1, 8, 5, 12, 16]
        q_ti = trim_order.index(q_trim) if q_trim in trim_order else -1
        c_ti = trim_order.index(c_trim) if c_trim in trim_order else -1
        if q_ti >= 0 and c_ti >= 0:
            if c_ti < q_ti:
                results.append((
                    "TRIM",
                    DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                    0.0,
                    RuleViolation(
                        module_name="API_600_TRIM",
                        standard_code="API 600",
                        failure_mode_prevented="Rapid seat washout in erosive/corrosive service",
                        explanation=f"TRIM DOWNGRADE: Candidate Trim {c_trim} < required Trim {q_trim}.",
                    ),
                ))
            elif c_ti == q_ti:
                results.append(("TRIM", DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None))
            else:
                results.append(("TRIM", DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.92, None))

    # ── Port Bore Check (API 6D) ─────────────────────────────────
    q_bore = q_props.get("port_bore")
    c_bore = c_props.get("port_bore")
    q_piggable = q_props.get("piggable", False)
    if q_bore and c_bore:
        if q_bore == "FULL_BORE" and c_bore == "REDUCED_BORE" and q_piggable:
            results.append((
                "PORT_BORE",
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="API_6D_BORE",
                    standard_code="API 6D",
                    failure_mode_prevented="Pipeline PIG inspection tool trapped in pipeline",
                    explanation="PIG BLOCKAGE: Reduced bore valve blocks pipeline pigging tools.",
                ),
            ))
        elif q_bore == c_bore:
            results.append(("PORT_BORE", DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None))

    # ── Fire-Safe Check (API 607) ────────────────────────────────
    q_fire = q_props.get("fire_safe_required", False)
    c_fire = c_props.get("fire_safe_certified", False)
    if q_fire and not c_fire:
        results.append((
            "FIRE_SAFE",
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_607",
                standard_code="API 607 / API 6FA",
                failure_mode_prevented="Seat melting and hydrocarbon fire feeding",
                explanation="FIRE DISASTER: Non-fire-safe valve in hydrocarbon service.",
            ),
        ))

    # ── Ex Motor Check (IS/IEC 60079) ────────────────────────────
    q_ex = q_props.get("ex_rating")
    c_ex = c_props.get("ex_rating")
    q_zone = q_props.get("zone")
    if q_ex and not c_ex and q_zone in (1, 2):
        results.append((
            "EX_RATING",
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="IEC_60079",
                standard_code="IS/IEC 60079",
                failure_mode_prevented="Electric spark igniting explosive vapor atmosphere",
                explanation="FATAL EXPLOSION TRAP: Non-Ex motor proposed for hazardous Zone 1/2.",
            ),
        ))

    # ── Seal Plan Check (API 682) ────────────────────────────────
    q_seal = q_props.get("seal_plan")
    c_seal = c_props.get("seal_plan")
    q_toxic = q_props.get("toxic_service", False)
    dual_plans = {"Plan 53A", "Plan 53B", "Plan 54"}
    single_plans = {"Plan 11", "Plan 21", "Plan 32"}
    if q_seal in dual_plans and c_seal in single_plans and q_toxic:
        results.append((
            "SEAL_PLAN",
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="API_682",
                standard_code="API 682",
                failure_mode_prevented="Toxic atmosphere seal blowout",
                explanation=f"SEAL DOWNGRADE: Dual barrier {q_seal} downgraded to single {c_seal} in toxic service.",
            ),
        ))

    # ── NACE Sour Service Check ──────────────────────────────────
    q_nace = q_props.get("nace_required", False)
    c_nace = c_props.get("nace_compliant", True)
    if q_nace and not c_nace:
        results.append((
            "NACE_SOUR",
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="NACE_MR0175",
                standard_code="NACE MR0175 / ISO 15156",
                failure_mode_prevented="Sulfide stress corrosion cracking catastrophic blowout",
                explanation="SOUR SERVICE VIOLATION: Non-NACE material in wet H2S environment.",
            ),
        ))

    # ── LME Coating Check ────────────────────────────────────────
    q_temp = q_props.get("temp_c", 0)
    c_coating = (c_props.get("coating") or "").upper()
    if q_temp and float(q_temp) > 200 and c_coating in ("GALVANIZED", "CADMIUM", "ZINC"):
        results.append((
            "LME_COATING",
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="FASTENER_LME",
                standard_code="ASTM A193 / LME Prevention",
                failure_mode_prevented="Liquid metal embrittlement cracking from zinc/cadmium at elevated temperature",
                explanation=(
                    f"LIQUID METAL EMBRITTLEMENT TRAP: {c_coating} coating prohibited "
                    f"above 200°C. Service temperature is {q_temp}°C."
                ),
            ),
        ))

    # ── Pressure Rating PSI Check ────────────────────────────────
    q_psi = q_props.get("pressure_rating_psi")
    c_psi = c_props.get("pressure_rating_psi")
    if q_psi is not None and c_psi is not None:
        tier, score, viol = check_pressure_rating_psi(float(q_psi), float(c_psi))
        results.append(("PRESSURE_RATING_PSI", tier, score, viol))

    return results


def _build_property_evaluation(
    name: str,
    tier: DynamicCompatibilityTier,
    score: float,
    q_val: str | None,
    c_val: str | None,
    violation: RuleViolation | None,
) -> PropertyEvaluation:
    """Build a PropertyEvaluation from evaluation results."""
    if tier == DynamicCompatibilityTier.TIER_1_IDENTICAL:
        status = PropertyEvaluationStatus.IDENTICAL if score >= 0.99 else PropertyEvaluationStatus.SAFE_UPGRADE
        comment = f"{name}: Exact match" if score >= 0.99 else f"{name}: Safe over-rating"
    elif tier == DynamicCompatibilityTier.TIER_2_SUBSTITUTE:
        status = PropertyEvaluationStatus.ADAPTABLE
        comment = f"{name}: Minor variance — requires HITL review"
    else:
        status = PropertyEvaluationStatus.HARD_REJECT
        comment = violation.explanation if violation else f"{name}: Incompatible"

    return PropertyEvaluation(
        property_name=name,
        tier=tier,
        score=score,
        searched_value=q_val,
        candidate_value=c_val,
        status=status,
        comment=comment,
    )


def evaluate_material_compatibility(
    query: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes,
) -> CompatibilityResult:
    """
    Master tolerance evaluation. Evaluates ALL physical properties
    and returns a final composite compatibility result.

    This is the DETERMINISTIC SAFETY GATE that AI cannot override.
    """
    violations: list[RuleViolation] = []
    upgrades: list[str] = []

    # ── Step 1: Dimensional Zero-Tolerance ─────────────────────────
    dim_tier, dim_score, dim_viol = _check_dimensions(query, candidate)
    dim_eval = _build_property_evaluation(
        "DIMENSIONS", dim_tier, dim_score,
        f"{query.size_nb_mm} mm" if query.size_nb_mm else None,
        f"{candidate.size_nb_mm} mm" if candidate.size_nb_mm else None,
        dim_viol,
    )
    if dim_viol:
        violations.append(dim_viol)

    # ── Step 2: Pressure Class / Rating ────────────────────────────
    prs_tier, prs_score, prs_viol = check_pressure_class(
        query.pressure_class, candidate.pressure_class, query.item_type
    )
    # Also check PSI rating if present
    psi_tier, psi_score, psi_viol = check_pressure_rating_psi(
        query.pressure_rating_psi, candidate.pressure_rating_psi
    )
    # Take the worse of class and PSI
    if psi_tier == DynamicCompatibilityTier.TIER_3_INCOMPATIBLE:
        prs_tier, prs_score, prs_viol = psi_tier, psi_score, psi_viol

    prs_eval = _build_property_evaluation(
        "PRESSURE", prs_tier, prs_score,
        f"Class {query.pressure_class}" if query.pressure_class else str(query.pressure_rating_psi),
        f"Class {candidate.pressure_class}" if candidate.pressure_class else str(candidate.pressure_rating_psi),
        prs_viol,
    )
    if prs_viol:
        violations.append(prs_viol)

    # ── Step 3: Metallurgy ─────────────────────────────────────────
    met_tier, met_score, met_viol = check_metallurgy(query.metallurgy, candidate.metallurgy)
    met_eval = _build_property_evaluation(
        "METALLURGY", met_tier, met_score,
        query.metallurgy, candidate.metallurgy, met_viol,
    )
    if met_viol:
        violations.append(met_viol)
    if met_tier == DynamicCompatibilityTier.TIER_2_SUBSTITUTE and query.metallurgy != candidate.metallurgy:
        upgrades.append(f"METALLURGY UPGRADE: {query.metallurgy} → {candidate.metallurgy}")

    # ── Step 4: Connection / Facing ────────────────────────────────
    con_tier, con_score, con_viol = _check_facing(query.facing_end, candidate.facing_end)
    con_eval = _build_property_evaluation(
        "CONNECTION", con_tier, con_score,
        query.facing_end, candidate.facing_end, con_viol,
    )
    if con_viol:
        violations.append(con_viol)

    # ── Step 5: Schedule ───────────────────────────────────────────
    equip_evals: dict[str, PropertyEvaluation] = {}
    if query.schedule or candidate.schedule:
        sch_tier, sch_score, sch_viol = _check_schedule(query, candidate)
        equip_evals["SCHEDULE"] = _build_property_evaluation(
            "SCHEDULE", sch_tier, sch_score,
            query.schedule, candidate.schedule, sch_viol,
        )
        if sch_viol:
            violations.append(sch_viol)
        if sch_tier == DynamicCompatibilityTier.TIER_2_SUBSTITUTE:
            upgrades.append(f"SCHEDULE UPGRADE: {query.schedule} → {candidate.schedule}")

    # ── Step 6: Equipment-Specific Properties ──────────────────────
    equip_results = _check_equipment_specific(query, candidate)
    for prop_name, eq_tier, eq_score, eq_viol in equip_results:
        equip_evals[prop_name] = _build_property_evaluation(
            prop_name, eq_tier, eq_score, None, None, eq_viol,
        )
        if eq_viol:
            violations.append(eq_viol)

    # ── Step 7: Build Property Scorecard ───────────────────────────
    scorecard = PropertyScorecard(
        dimensions=dim_eval,
        pressure=prs_eval,
        metallurgy=met_eval,
        connection=con_eval,
        equipment_specific=equip_evals,
    )

    # ── Step 8: Aggregate Final Tier ───────────────────────────────
    all_evals = [dim_eval, prs_eval, met_eval, con_eval] + list(equip_evals.values())

    # Any Tier 3 → Force Tier 3
    if any(e.tier == DynamicCompatibilityTier.TIER_3_INCOMPATIBLE for e in all_evals):
        return CompatibilityResult(
            compatibility_tier=DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            composite_score=0.0,
            is_compatible=False,
            requires_hitl=False,
            property_scorecard=scorecard,
            rule_violations=violations,
            engineering_upgrades=upgrades,
            summary="INCOMPATIBLE: " + (violations[0].failure_mode_prevented if violations else "Safety invariant violated"),
        )

    # Compute composite score
    scores = [e.score for e in all_evals if e.score > 0]
    composite = sum(scores) / len(scores) if scores else 0.0

    # All Tier 1 and score >= 0.95 → Tier 1
    if (
        composite >= 0.95
        and all(e.tier == DynamicCompatibilityTier.TIER_1_IDENTICAL for e in all_evals)
    ):
        return CompatibilityResult(
            compatibility_tier=DynamicCompatibilityTier.TIER_1_IDENTICAL,
            composite_score=composite,
            is_compatible=True,
            requires_hitl=False,
            property_scorecard=scorecard,
            rule_violations=[],
            engineering_upgrades=upgrades,
            summary="Direct Interchangeable Drop-In Replacement",
        )

    # Otherwise → Tier 2
    if composite >= 0.80:
        return CompatibilityResult(
            compatibility_tier=DynamicCompatibilityTier.TIER_2_SUBSTITUTE,
            composite_score=composite,
            is_compatible=True,
            requires_hitl=True,
            property_scorecard=scorecard,
            rule_violations=[],
            engineering_upgrades=upgrades,
            summary="Functional Substitute / Safe Upgrade (Requires HITL Review)",
        )

    # Score below 80% → Tier 3
    return CompatibilityResult(
        compatibility_tier=DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        composite_score=composite,
        is_compatible=False,
        requires_hitl=False,
        property_scorecard=scorecard,
        rule_violations=violations,
        engineering_upgrades=upgrades,
        summary="Incompatible Replacement (Score Below Threshold)",
    )
