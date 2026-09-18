"""
Samanvay-AI Master Tolerance Evaluation Engine.

Orchestrates the 21 codified deterministic engineering safety modules:
- Module 1: ASME B16.5 / B16.34 Pressure Class Hierarchy & P-T Ratings
- Module 2: ASTM Metallurgy Directed Acyclic Graph & High-Temperature Creep
- Module 3: ASME B36.10M / B36.19M Pipe Schedules & Wall Thickness Invariants
- Module 4: NACE MR0175 / ISO 15156 Sour Service & ASME B16.47 Large Flanges
- Module 5: Valve Standards, Trim Ladders, Piggability & Fire-Safe Certification
- Module 6: Forged & Buttweld Piping Fittings (ASME B16.9 / B16.11)
- Module 7: Flange Facings, Serrations & Joint Mechanical Invariants
- Module 8: Gaskets & Fasteners Integrity (ASME B16.20 / ASTM A193 / A194 / LME)
- Module 9: Process Piping Fluid Service Categories & Line Pipe (ASME B31.3 / API 5L)
- Module 10: Instrumentation Small-Bore Tubing & Compression Fittings (ASTM A269)
- Module 11: Rotating & Electrical Equipment (IS/IEC 60079 / API 682 / ISO 15)
- Module 12: Heat Exchanger Bundles & Tubing (TEMA & ASME Sec VIII)
- Module 13: Centrifugal Pumps & Critical Internals (API 610)
- Module 14: Reciprocating & Centrifugal Compressors (API 618 / 617 / 692)
- Module 15: Rupture Disks & Overpressure Protection (ASME Sec VIII / ISO 4126-2)
- Module 16: Positive Isolation Line Blinds & Spacers (ASME B16.48)
- Module 17: Atmospheric & Low-Pressure Tank Storage Safety (API 2000 / ISO 16852)
- Module 18: Metallic Expansion Joints & Flexible Hoses (EJMA / ISO 10380)
- Module 19: In-Line Strainers, Filters & Steam Trapping (ASME B16.34 / ISO 6552)
- Module 20: Flange Insulation Kits & Cathodic Protection (NACE SP0286)
- Module 21: Thermal Insulation, CUI & Passive Fireproofing (ASTM C795 / C552)

Probabilistic AI vector similarity is mathematically prohibited from overriding any rule.
"""

from typing import Optional, List, Dict, Any, Tuple
from backend.app.schemas.material import (
    DynamicCompatibilityTier,
    ExtractedMaterialAttributes,
    PropertyEvaluation,
    PropertyEvaluationStatus,
    PropertyScorecard,
    RuleViolation,
    CompatibilityResult,
)

# ASME Rules
from rules.asme.pressure_class import check_pressure_class, check_pressure_rating_psi
from rules.asme.large_flanges import check_large_flange_series
from rules.asme.fittings import check_forged_fittings_rating, check_buttweld_elbow_radius
from rules.asme.facings import check_flange_facing
from rules.asme.gaskets import check_gasket_compatibility
from rules.asme.line_blinds import check_line_blind_compatibility
from rules.asme.flange_insulation import check_flange_insulation_kit

# ASTM Rules
from rules.astm.metallurgy_dag import check_metallurgy
from rules.astm.fasteners import check_fastener_integrity

# Piping Rules
from rules.piping.schedules import check_pipe_schedule, check_coating_thickness
from rules.piping.nace import check_nace_sour_service
from rules.piping.line_pipe import check_line_pipe_quality
from rules.piping.tubing import check_instrumentation_tubing
from rules.piping.expansion_joints import check_expansion_joint_and_hose

# Valve Rules
from rules.valves.trim import check_valve_trim
from rules.valves.bore import check_valve_bore
from rules.valves.fire_safe import check_fire_safe_and_categories
from rules.valves.psv import check_psv_orifice_and_pressure
from rules.valves.rupture_disks import check_rupture_disk

# Rotating Equipment Rules
from rules.rotating.motors import check_motor_compatibility
from rules.rotating.seals import check_mechanical_seal_and_elastomer
from rules.rotating.bearings import check_bearing_compatibility
from rules.rotating.pumps import check_centrifugal_pump
from rules.rotating.compressors import check_compressor_compatibility

# Equipment & Insulation Rules
from rules.equipment.heat_exchangers import check_heat_exchanger_tubes
from rules.equipment.tank_safety import check_tank_safety_and_paint
from rules.equipment.strainers_traps import check_strainer_filter_and_steam_trap
from rules.equipment.thermal_insulation import check_thermal_insulation_cui


def _build_evaluation(
    name: str,
    tier: DynamicCompatibilityTier,
    score: float,
    searched_val: Optional[str],
    candidate_val: Optional[str],
    violation: Optional[RuleViolation] = None,
) -> PropertyEvaluation:
    if tier == DynamicCompatibilityTier.TIER_1_IDENTICAL:
        status = PropertyEvaluationStatus.IDENTICAL if score >= 0.99 else PropertyEvaluationStatus.SAFE_UPGRADE
        comment = f"{name}: Parity verified" if score >= 0.99 else f"{name}: Safe over-rating"
    elif tier == DynamicCompatibilityTier.TIER_2_SUBSTITUTE:
        status = PropertyEvaluationStatus.ADAPTABLE
        comment = f"{name}: Substitute requires engineering review"
    else:
        status = PropertyEvaluationStatus.HARD_REJECT
        comment = violation.description if violation else f"{name}: Zero-tolerance violation"

    return PropertyEvaluation(
        property_name=name,
        tier=tier,
        score=score,
        searched_value=searched_val,
        candidate_value=candidate_val,
        status=status,
        comment=comment,
    )


def evaluate_material_compatibility(
    query: ExtractedMaterialAttributes,
    candidate: ExtractedMaterialAttributes,
) -> CompatibilityResult:
    """
    Evaluates cross-CPSE material compatibility across all 21 engineering safety modules.
    """
    violations: List[RuleViolation] = []
    upgrades: List[str] = []
    equip_evals: Dict[str, PropertyEvaluation] = {}

    q_props = dict(query.properties or {})
    c_props = dict(candidate.properties or {})

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Primary Dimensions: Zero-Tolerance Check
    # ─────────────────────────────────────────────────────────────────────────
    q_size = query.size_nb_mm
    c_size = candidate.size_nb_mm

    if q_size is not None and c_size is not None:
        if abs(q_size - c_size) < 0.01:
            dim_tier = DynamicCompatibilityTier.TIER_1_IDENTICAL
            dim_score = 1.0
            dim_viol = None
        else:
            dim_tier = DynamicCompatibilityTier.TIER_3_INCOMPATIBLE
            dim_score = 0.0
            dim_viol = RuleViolation(
                module_name="DIMENSIONAL_ZERO_TOLERANCE",
                standard_code="ASME B16.5 / B36.10M",
                failure_mode_prevented="Physical dimensional mismatch — part cannot mate or bolt",
                explanation=f"DIMENSION MISMATCH: Query requires {q_size} mm NB, candidate is {c_size} mm NB. Mismatched nominal diameters cannot mate.",
            )
            violations.append(dim_viol)
    else:
        dim_tier = DynamicCompatibilityTier.TIER_1_IDENTICAL
        dim_score = 1.0
        dim_viol = None

    dim_eval = _build_evaluation(
        "DIMENSIONS", dim_tier, dim_score,
        str(q_size) if q_size else None, str(c_size) if c_size else None, dim_viol
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Pressure Evaluation (ASME B16.5 / B16.34 Class & PSI)
    # ─────────────────────────────────────────────────────────────────────────
    p_tier, p_score, p_viol = check_pressure_class(
        query.pressure_class, candidate.pressure_class, query.item_type
    )
    if p_viol:
        violations.append(p_viol)

    # Operating PSI
    psi_q = query.pressure_rating_psi or q_props.get("pressure_rating_psi")
    psi_c = candidate.pressure_rating_psi or c_props.get("pressure_rating_psi")
    if psi_q is not None or psi_c is not None:
        psi_t, psi_s, psi_v = check_pressure_rating_psi(
            float(psi_q) if psi_q is not None else None,
            float(psi_c) if psi_c is not None else None
        )
        if psi_v:
            violations.append(psi_v)
            p_tier, p_score, p_viol = psi_t, psi_s, psi_v
        elif p_tier == DynamicCompatibilityTier.TIER_1_IDENTICAL and psi_t == DynamicCompatibilityTier.TIER_1_IDENTICAL:
            p_score = max(p_score, psi_s)

    prs_eval = _build_evaluation(
        "PRESSURE_RATING", p_tier, p_score,
        f"Class {query.pressure_class}" if query.pressure_class else (f"{psi_q} PSI" if psi_q else None),
        f"Class {candidate.pressure_class}" if candidate.pressure_class else (f"{psi_c} PSI" if psi_c else None),
        p_viol,
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Metallurgy (ASTM Metallurgy DAG)
    # ─────────────────────────────────────────────────────────────────────────
    q_mat = query.metallurgy or q_props.get("material")
    c_mat = candidate.metallurgy or c_props.get("material")

    if q_mat or c_mat:
        m_tier, m_score, m_viol = check_metallurgy(q_mat, c_mat)
        if m_viol:
            violations.append(m_viol)
        if m_tier == DynamicCompatibilityTier.TIER_2_SUBSTITUTE and q_mat != c_mat:
            upgrades.append(f"METALLURGY UPGRADE: {q_mat} -> {c_mat}")
    else:
        m_tier = DynamicCompatibilityTier.TIER_1_IDENTICAL
        m_score = 1.0
        m_viol = None

    met_eval = _build_evaluation(
        "METALLURGY", m_tier, m_score, q_mat, c_mat, m_viol
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Connection / Flange Facing (ASME B16.5)
    # ─────────────────────────────────────────────────────────────────────────
    q_face = query.facing_end or q_props.get("facing") or q_props.get("end_conn")
    c_face = candidate.facing_end or c_props.get("facing") or c_props.get("end_conn")

    if q_face or c_face:
        f_tier, f_score, f_viol = check_flange_facing(
            q_face, c_face, body_material=c_mat
        )
        if f_viol:
            violations.append(f_viol)
    else:
        f_tier = DynamicCompatibilityTier.TIER_1_IDENTICAL
        f_score = 1.0
        f_viol = None

    con_eval = _build_evaluation(
        "CONNECTION", f_tier, f_score, q_face, c_face, f_viol
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Pipe Schedules (ASME B36.10M / B36.19M)
    # ─────────────────────────────────────────────────────────────────────────
    q_sch = query.schedule or q_props.get("schedule")
    c_sch = candidate.schedule or c_props.get("schedule")
    if q_sch or c_sch:
        sch_t, sch_s, sch_v = check_pipe_schedule(q_sch, c_sch)
        if sch_v:
            violations.append(sch_v)
        if sch_t == DynamicCompatibilityTier.TIER_2_SUBSTITUTE:
            upgrades.append(f"SCHEDULE UPGRADE: {q_sch} -> {c_sch}")
        equip_evals["SCHEDULE"] = _build_evaluation("SCHEDULE", sch_t, sch_s, q_sch, c_sch, sch_v)

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Specialized Domain Modules Evaluations
    # ─────────────────────────────────────────────────────────────────────────
    def _run_rule(name: str, rule_res: Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]):
        rt, rs, rv = rule_res
        if rv:
            violations.append(rv)
        if rt != DynamicCompatibilityTier.TIER_1_IDENTICAL or rs < 1.0 or rv:
            equip_evals[name] = _build_evaluation(name, rt, rs, None, None, rv)

    # NACE Sour Service
    _run_rule("NACE_SOUR", check_nace_sour_service(q_props, c_props))

    # Fasteners, Studs, LME, and Yield Strength
    _run_rule("FASTENERS_LME", check_fastener_integrity(q_mat, c_mat, q_props, c_props))

    # Gaskets & Temperature
    if str(query.item_type).upper() in ("GASKET", "O_RING") or "gasket" in str(query.item_type).lower() or "max_temp_c" in q_props:
        _run_rule("GASKETS", check_gasket_compatibility(q_props, c_props, query.pressure_class))

    # Valves (Trim, Bore, Fire-Safe, PSV, Rupture Disks)
    is_pig = q_props.get("piggable", False)
    is_valve = "VALVE" in str(query.item_type).upper()
    if is_valve or "trim_no" in q_props or "operation" in q_props or "end_conn" in q_props or "port_bore" in q_props:
        q_trim = q_props.get("trim_no")
        c_trim = c_props.get("trim_no")
        if q_trim is not None or c_trim is not None:
            _run_rule("VALVE_TRIM", check_valve_trim(q_trim, c_trim))

        q_bore = q_props.get("port_bore") or q_props.get("bore")
        c_bore = c_props.get("port_bore") or c_props.get("bore")
        if q_bore or c_bore or is_pig:
            _run_rule("VALVE_BORE", check_valve_bore(q_bore, c_bore, is_pig))

        _run_rule("FIRE_SAFE_VALVES", check_fire_safe_and_categories(q_props, c_props))

    if "orifice" in str(q_props) or "orifice" in str(c_props) or query.item_type in ("PSV", "RELIEF_VALVE"):
        _run_rule("PSV_RELIEF", check_psv_orifice_and_pressure(
            q_props.get("orifice"), c_props.get("orifice"),
            q_props.get("cdtp_bar"), c_props.get("cdtp_bar")
        ))

    if "disk_type" in q_props or "disk_type" in c_props or "rupture_disk" in str(query.item_type).lower():
        _run_rule("RUPTURE_DISK", check_rupture_disk(q_props, c_props))

    # Large Flanges (ASME B16.47 Series A vs B)
    if (query.size_nb_mm and query.size_nb_mm >= 650.0) or "series" in str(q_props) or "series" in str(c_props):
        _run_rule("LARGE_FLANGES", check_large_flange_series(q_props.get("series"), c_props.get("series")))

    # Fittings (ASME B16.9 / B16.11)
    if "FITTING" in str(query.item_type).upper() or "ELBOW" in str(query.item_type).upper() or "TEE" in str(query.item_type).upper():
        q_fit_rat = q_props.get("rating")
        c_fit_rat = c_props.get("rating")
        if q_fit_rat or c_fit_rat:
            _run_rule("FORGED_FITTINGS", check_forged_fittings_rating(q_fit_rat, c_fit_rat))
        _run_rule("ELBOW_RADIUS", check_buttweld_elbow_radius(q_props.get("radius"), c_props.get("radius"), is_pig))

    # Rotating Equipment (Motors, Seals, Bearings, Pumps, Compressors)
    if query.item_type == "MOTOR" or "ex_rating" in q_props or "ip_rating" in q_props or "voltage" in q_props:
        _run_rule("MOTOR_EQUIPMENT", check_motor_compatibility(q_props, c_props))

    if query.item_type in ("PUMP", "COMPRESSOR", "SEAL", "O_RING") or "seal_plan" in q_props or "api_plan" in q_props or "material" in q_props:
        _run_rule("SEALS_ELASTOMERS", check_mechanical_seal_and_elastomer(q_props, c_props))

    if query.item_type == "BEARING" or "bearing" in str(query.item_type).lower() or "clearance" in q_props or "type" in q_props:
        _run_rule("BEARINGS", check_bearing_compatibility(q_props, c_props))

    if query.item_type == "PUMP" or "flow_rate_m3h" in q_props or "coupling" in q_props or "api_mount" in q_props:
        _run_rule("PUMP_EQUIPMENT", check_centrifugal_pump(q_props, c_props))

    if query.item_type == "COMPRESSOR" or "valve_role" in q_props or "dgs_type" in q_props:
        _run_rule("COMPRESSOR_EQUIPMENT", check_compressor_compatibility(q_props, c_props))

    # Line Pipe & Fluid Service
    if query.item_type == "PIPE" or "psl" in q_props or "category_m" in q_props:
        _run_rule("LINE_PIPE", check_line_pipe_quality(q_props, c_props))

    # Tubing
    if query.item_type == "TUBE" or query.item_type == "TUBING" or "od_mm" in q_props:
        _run_rule("INSTRUMENT_TUBING", check_instrumentation_tubing(q_props, c_props))

    # Expansion Joints
    if "bellows" in str(query.item_type).lower() or "hose" in str(query.item_type).lower() or "tied_joint" in q_props:
        _run_rule("EXPANSION_JOINTS", check_expansion_joint_and_hose(q_props, c_props))

    # Equipment & Tank Safety
    if "TANK" in str(query.item_type).upper() or "paint_sys" in q_props or "venting" in str(q_props):
        _run_rule("TANK_SAFETY", check_tank_safety_and_paint(q_props, c_props))

    # Strainers, Filters & Traps
    if query.item_type in ("FILTER", "STRAINER", "STEAM_TRAP") or "micron_rating" in q_props or "thread" in q_props:
        _run_rule("STRAINERS_FILTERS_TRAPS", check_strainer_filter_and_steam_trap(q_props, c_props))

    # Coating Thickness
    if "coating_thickness_um" in q_props or "coating_thickness_um" in c_props:
        _run_rule("COATING_THICKNESS", check_coating_thickness(q_props, c_props))

    # Insulation (ASTM C795 / C552)
    if "insulation" in str(query.item_type).lower() or "astm_c795" in str(q_props) or "cui" in str(q_props):
        _run_rule("THERMAL_INSULATION", check_thermal_insulation_cui(q_props, c_props, substrate_material=c_mat))

    # Heat Exchangers
    if "EXCHANGER" in str(query.item_type).upper() or "TUBE_BUNDLE" in str(query.item_type).upper() or "tema_class" in q_props:
        _run_rule("HEAT_EXCHANGERS", check_heat_exchanger_tubes(q_props, c_props))

    # Line Blinds & Flange Insulation
    if "BLIND" in str(query.item_type).upper() or "SPACER" in str(query.item_type).upper():
        _run_rule("LINE_BLINDS", check_line_blind_compatibility(q_props, c_props))

    if "FIK" in str(query.item_type).upper() or "INSULATION_KIT" in str(query.item_type).upper() or "fik_type" in q_props:
        _run_rule("FLANGE_INSULATION_KIT", check_flange_insulation_kit(q_props, c_props))

    # ─────────────────────────────────────────────────────────────────────────
    # 7. Assemble Property Scorecard & Compute Final Dynamic Tier
    # ─────────────────────────────────────────────────────────────────────────
    scorecard = PropertyScorecard(
        dimensions=dim_eval,
        pressure=prs_eval,
        metallurgy=met_eval,
        connection=con_eval,
        equipment_specific=equip_evals,
    )

    all_evals = [dim_eval, prs_eval, met_eval, con_eval] + list(equip_evals.values())

    # Hard Zero-Tolerance Check: ANY Tier 3 implies overall Tier 3 Incompatible
    has_tier_3 = any(e.tier == DynamicCompatibilityTier.TIER_3_INCOMPATIBLE for e in all_evals) or bool(violations)

    if has_tier_3:
        summary_msg = f"INCOMPATIBLE: {violations[0].failure_mode_prevented}" if violations else "Safety invariant violated"
        return CompatibilityResult(
            compatibility_tier=DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            composite_score=0.0,
            is_compatible=False,
            requires_hitl=False,
            property_scorecard=scorecard,
            rule_violations=violations,
            engineering_upgrades=upgrades,
            summary=summary_msg,
        )

    # Compute composite score
    valid_scores = [e.score for e in all_evals if e.score > 0.0]
    composite = sum(valid_scores) / len(valid_scores) if valid_scores else 1.0

    # Tier 1 Identical: >= 0.95 and all evaluations are Tier 1 Identical
    all_tier_1 = all(e.tier == DynamicCompatibilityTier.TIER_1_IDENTICAL for e in all_evals)
    if composite >= 0.95 and all_tier_1:
        return CompatibilityResult(
            compatibility_tier=DynamicCompatibilityTier.TIER_1_IDENTICAL,
            composite_score=round(composite, 4),
            is_compatible=True,
            requires_hitl=False,
            property_scorecard=scorecard,
            rule_violations=[],
            engineering_upgrades=upgrades,
            summary="Direct Interchangeable Drop-In Replacement",
        )

    # Tier 2 Substitute: >= 0.80 (Functional Substitute / Safe Upgrade)
    if composite >= 0.80:
        return CompatibilityResult(
            compatibility_tier=DynamicCompatibilityTier.TIER_2_SUBSTITUTE,
            composite_score=round(composite, 4),
            is_compatible=True,
            requires_hitl=True,
            property_scorecard=scorecard,
            rule_violations=[],
            engineering_upgrades=upgrades,
            summary="Functional Substitute / Safe Upgrade (Requires HITL Review)",
        )

    # Fallback to Tier 3 if composite score < 0.80
    return CompatibilityResult(
        compatibility_tier=DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        composite_score=round(composite, 4),
        is_compatible=False,
        requires_hitl=False,
        property_scorecard=scorecard,
        rule_violations=violations,
        engineering_upgrades=upgrades,
        summary="Incompatible Replacement (Composite Score Below 80%)",
    )
