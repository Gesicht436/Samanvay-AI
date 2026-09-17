"""
ASTM Metallurgy Directed Acyclic Graph & High-Temperature Creep Rules.

Implements the complete safe-upgrade hierarchy for corrosion resistance,
yield strength, and temperature capabilities. Downgrades are blocked
as fatal corrosion/creep/embrittlement failure traps.
"""

from typing import Optional

from backend.app.schemas.material import (
    DynamicCompatibilityTier,
    RuleViolation,
)

# ── ASTM Metallurgy Directed Acyclic Graph ────────────────────────────────
# Each key can safely replace any material in its set of allowed downward targets.
# Movement DOWN the hierarchy (replacing a higher material with a lower one) is BLOCKED.

# Canonical material family names (normalized)
_CARBON_STEEL = frozenset([
    "ASTM A105", "A105", "ASTM A216 WCB", "A216 WCB", "WCB",
    "ASTM A106 GR.B", "ASTM A106-B", "A106 GR.B", "A106-B", "A106 B",
    "ASTM A234 WPB", "A234 WPB", "WPB",
    "ASTM A216 WCC", "WCC",
])

_LOW_TEMP_CS = frozenset([
    "ASTM A350 LF2", "A350 LF2", "LF2", "LTCS",
    "ASTM A352 LCB", "A352 LCB", "LCB",
    "ASTM A333 GR.6", "A333-6", "A333 GR.6",
    "ASTM A420 WPL6", "A420 WPL6",
])

_SS_304 = frozenset([
    "ASTM A182 F304", "A182 F304", "F304",
    "ASTM A351 CF8", "A351 CF8", "CF8",
    "ASTM A312 TP304", "A312 TP304", "TP304",
    "SS304", "304",
])

_SS_304L = frozenset([
    "ASTM A182 F304L", "A182 F304L", "F304L",
    "ASTM A351 CF3", "A351 CF3", "CF3",
    "ASTM A312 TP304L", "A312 TP304L", "TP304L",
    "SS304L", "304L",
])

_SS_316 = frozenset([
    "ASTM A182 F316", "A182 F316", "F316",
    "ASTM A351 CF8M", "A351 CF8M", "CF8M",
    "ASTM A312 TP316", "A312 TP316", "TP316",
    "SS316", "316",
])

_SS_316L = frozenset([
    "ASTM A182 F316L", "A182 F316L", "F316L",
    "ASTM A351 CF3M", "A351 CF3M", "CF3M",
    "ASTM A312 TP316L", "A312 TP316L", "TP316L",
    "SS316L", "316L",
])

_SS_321 = frozenset(["ASTM A182 F321", "F321", "SS321", "321", "TP321"])
_SS_347 = frozenset(["ASTM A182 F347", "F347", "SS347", "347", "TP347"])

_DUPLEX_2205 = frozenset([
    "ASTM A182 F51", "A182 F51", "F51",
    "ASTM A815 S31803", "S31803", "UNS S31803",
    "DUPLEX STAINLESS STEEL", "DUPLEX 2205", "DSS",
])

_SUPER_DUPLEX_2507 = frozenset([
    "ASTM A182 F53", "A182 F53", "F53",
    "ASTM A815 S32750", "S32750", "UNS S32750",
    "SUPER DUPLEX STAINLESS", "SUPER DUPLEX 2507", "SDSS",
])

_NICKEL_ALLOYS = frozenset([
    "INCONEL 625", "ALLOY 625", "INCO 625", "UNS N06625",
    "HASTELLOY C-276", "HAST-C", "C-276", "UNS N10276",
    "MONEL 400", "MONEL K-500",
])

# Cr-Mo Creep Steels (high-temperature service hierarchy)
_CR_MO_F11 = frozenset(["ASTM A182 F11", "A182 F11", "F11", "ASTM A217 WC6", "WC6", "1.25CR-0.5MO"])
_CR_MO_F22 = frozenset(["ASTM A182 F22", "A182 F22", "F22", "ASTM A217 WC9", "WC9", "2.25CR-1MO"])
_CR_MO_F5 = frozenset(["ASTM A182 F5", "A182 F5", "F5", "ASTM A217 C5", "C5", "5CR-0.5MO"])
_CR_MO_F91 = frozenset(["ASTM A182 F91", "A182 F91", "F91", "ASTM A217 C12A", "C12A", "9CR-1MO-V"])

# ── Hierarchy Level Assignment ────────────────────────────────────────────
# Higher level = more capable material (safe to upgrade to)
_MATERIAL_LEVELS: list[tuple[frozenset[str], int, str]] = [
    (_CARBON_STEEL, 0, "CARBON_STEEL"),
    (_LOW_TEMP_CS, 1, "LOW_TEMP_CARBON_STEEL"),
    (_SS_304, 2, "AUSTENITIC_SS_304"),
    (_SS_304L, 2, "AUSTENITIC_SS_304L"),  # Same level as 304 (stabilized variant)
    (_SS_321, 2, "STABILIZED_SS_321"),
    (_SS_347, 2, "STABILIZED_SS_347"),
    (_SS_316, 3, "MOLYBDENUM_SS_316"),
    (_SS_316L, 3, "MOLYBDENUM_SS_316L"),
    (_DUPLEX_2205, 4, "DUPLEX_2205"),
    (_SUPER_DUPLEX_2507, 5, "SUPER_DUPLEX_2507"),
    (_NICKEL_ALLOYS, 6, "NICKEL_ALLOYS"),
    # Cr-Mo creep steels (separate hierarchy branch)
    (_CR_MO_F11, 10, "CR_MO_1_25CR"),
    (_CR_MO_F22, 11, "CR_MO_2_25CR"),
    (_CR_MO_F5, 12, "CR_MO_5CR"),
    (_CR_MO_F91, 13, "CR_MO_9CR"),
]


def _normalize_material(name: str | None) -> str:
    """Normalize a material name for lookup."""
    if not name:
        return ""
    return name.strip().upper().replace("  ", " ")


def _find_material_info(name: str) -> tuple[int, str] | None:
    """Find the hierarchy level and family of a material name."""
    norm = _normalize_material(name)
    if not norm:
        return None
    for family_set, level, family_name in _MATERIAL_LEVELS:
        if norm in {m.upper() for m in family_set}:
            return level, family_name
    return None


def _is_cryogenic_material(name: str) -> bool:
    """Check if a material is certified for cryogenic service (-46°C impact tested)."""
    norm = _normalize_material(name)
    return norm in {m.upper() for m in _LOW_TEMP_CS}


def _is_stabilized_grade(name: str) -> bool:
    """Check if material is a low-carbon stabilized grade (L-grade, 321, 347)."""
    norm = _normalize_material(name)
    for family in [_SS_304L, _SS_316L, _SS_321, _SS_347]:
        if norm in {m.upper() for m in family}:
            return True
    return False


def _is_standard_non_stabilized(name: str) -> bool:
    """Check if material is standard (non-L, non-stabilized) austenitic SS."""
    norm = _normalize_material(name)
    for family in [_SS_304, _SS_316]:
        if norm in {m.upper() for m in family}:
            return True
    return False


def check_metallurgy(
    query_mat: str | None,
    candidate_mat: str | None,
) -> tuple[DynamicCompatibilityTier, float, RuleViolation | None]:
    """
    Evaluate metallurgy compatibility between query and candidate materials.

    Returns:
        (tier, score, violation_or_none)
    """
    if not query_mat or not candidate_mat:
        # Cannot evaluate — force HITL review
        return (
            DynamicCompatibilityTier.TIER_2_SUBSTITUTE,
            0.85,
            None,
        )

    query_info = _find_material_info(query_mat)
    candidate_info = _find_material_info(candidate_mat)

    if not query_info or not candidate_info:
        # Unknown material — cannot auto-evaluate, require HITL
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.82, None)

    q_level, q_family = query_info
    c_level, c_family = candidate_info

    # ── EXACT MATCH ────────────────────────────────────────────────
    if q_family == c_family:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    # ── CRYOGENIC SAFETY TRAP ──────────────────────────────────────
    # Replacing cryogenic-certified LF2 with standard A105 = FATAL
    if _is_cryogenic_material(query_mat) and not _is_cryogenic_material(candidate_mat):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASTM_METALLURGY_DAG",
                standard_code="ASTM A350 LF2",
                failure_mode_prevented="Cryogenic brittle fracture at -46°C due to lack of Charpy impact testing",
                explanation=(
                    f"CRYOGENIC BRITTLE FRACTURE TRAP: Query requires cryogenic-rated "
                    f"'{query_mat}' (impact-tested at -46°C). Candidate '{candidate_mat}' "
                    f"is standard carbon steel without low-temperature impact certification. "
                    f"Thermal shock at cryogenic temperatures causes instantaneous brittle shattering."
                ),
            ),
        )

    # ── INTERGRANULAR CORROSION TRAP ───────────────────────────────
    # Standard 304/316 cannot replace stabilized 304L/316L/321/347 in acid duty
    if _is_stabilized_grade(query_mat) and _is_standard_non_stabilized(candidate_mat):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASTM_METALLURGY_DAG",
                standard_code="ASTM A182 (L-grade)",
                failure_mode_prevented="Intergranular stress corrosion cracking from sensitization",
                explanation=(
                    f"INTERGRANULAR CORROSION TRAP: Query requires stabilized low-carbon grade "
                    f"'{query_mat}'. Candidate '{candidate_mat}' is standard (non-L) grade "
                    f"susceptible to carbide precipitation and intergranular cracking in "
                    f"polythionic/nitric acid service."
                ),
            ),
        )

    # ── DOWNGRADE PROHIBITION ──────────────────────────────────────
    # Check hierarchy levels are in same branch
    both_cr_mo = q_level >= 10 and c_level >= 10
    both_general = q_level < 10 and c_level < 10

    if both_general or both_cr_mo:
        if c_level < q_level:
            # Downgrade detected
            return (
                DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                0.0,
                RuleViolation(
                    module_name="ASTM_METALLURGY_DAG",
                    standard_code="ASTM Metallurgy DAG",
                    failure_mode_prevented="Corrosion, creep, or mechanical failure from metallurgy downgrade",
                    explanation=(
                        f"METALLURGY DOWNGRADE TRAP: Query requires '{query_mat}' "
                        f"(family: {q_family}, level: {q_level}). Candidate '{candidate_mat}' "
                        f"(family: {c_family}, level: {c_level}) is a lower-grade material. "
                        f"Downward substitution violates the ASTM metallurgy hierarchy."
                    ),
                ),
            )
        elif c_level > q_level:
            # Safe upgrade — Tier 2 (requires HITL for welding filler verification)
            score = max(0.80, 1.0 - 0.05 * (c_level - q_level))
            return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, score, None)

    # Cross-branch substitution (e.g. Cr-Mo for austenitic) — require HITL
    return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.82, None)
