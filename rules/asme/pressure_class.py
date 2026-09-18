"""
ASME B16.5 / B16.34 Pressure Class Hierarchy & P-T Ratings.

Class Hierarchy: 150 < 300 < 600 < 900 < 1500 < 2500
PN Equivalents: PN20=150, PN50=300, PN100=600, PN150=900, PN250=1500, PN420=2500
"""

from typing import Optional

from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation

# ── Pressure Class Hierarchy ──────────────────────────────────────────────

PRESSURE_CLASS_HIERARCHY = [150, 300, 600, 900, 1500, 2500]

PN_TO_CLASS: dict[int, int] = {
    16: 150,
    20: 150,
    40: 300,
    50: 300,
    100: 600,
}

# Flanged component types where upgrading pressure changes bolt circle dimensions
FLANGED_COMPONENT_TYPES = frozenset([
    "FLANGE", "GATE_VALVE", "GLOBE_VALVE", "CHECK_VALVE",
    "BALL_VALVE", "BUTTERFLY_VALVE", "PLUG_VALVE",
])

# In-line component types where pressure upgrade preserves dimensions
INLINE_COMPONENT_TYPES = frozenset([
    "PIPE", "TUBE", "FITTING", "ELBOW", "TEE", "REDUCER",
    "COUPLING", "UNION", "CAP", "NIPPLE", "SOCKET_FITTING",
    "FITTING_SW", "FITTING_THD", "PIPELINE_FITTING",
])


def _normalize_class(value: int | None) -> int | None:
    """Normalize a pressure class value, converting PN to ASME Class if needed."""
    if value is None:
        return None
    if value in PRESSURE_CLASS_HIERARCHY:
        return value
    if value in PN_TO_CLASS:
        return PN_TO_CLASS[value]
    # Handle hash notation (e.g. 300# stored as 300)
    return value


def check_pressure_class(
    query_class: int | None,
    candidate_class: int | None,
    item_type: str | None = None,
    is_spool_adapter: bool = False,
) -> tuple[DynamicCompatibilityTier, float, RuleViolation | None]:
    """
    Evaluate pressure class compatibility.

    Rules:
    - Down-rating is ALWAYS Tier 3 (fatal rupture risk)
    - Equal rating = Tier 1
    - Up-rating with spool adapter = Tier 2 (acceptable via engineered spool)
    - Up-rating for in-line components = Tier 1 (dimension-preserving)
    - Up-rating for flanged components = Tier 3 (bolt circle mismatch)
    """
    q_class = _normalize_class(query_class)
    c_class = _normalize_class(candidate_class)

    if q_class is None and c_class is None:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
    if q_class is None or c_class is None:
        # One specified, one missing — HITL required
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)

    # ── EXACT MATCH ────────────────────────────────────────────────
    if c_class == q_class:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    # ── DOWN-RATING PROHIBITION ────────────────────────────────────
    # If candidate < query rating, this is ALWAYS a fatal rupture trap
    if c_class < q_class:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B16_5",
                standard_code="ASME B16.5 Table 2",
                failure_mode_prevented="Hydrostatic rupture under operating design pressure",
                explanation=(
                    f"FATAL PRESSURE DOWN-RATING: Candidate rating {c_class} is below "
                    f"required rating {q_class}. Installing a lower-rated component risks "
                    f"rupture under operating design pressure per ASME B16.5 / EN 1092-1."
                ),
            ),
        )

    # ── UP-RATING (candidate is higher) ───────────────────────────
    if is_spool_adapter:
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)

    normalized_type = (item_type or "").upper().replace(" ", "_")

    if normalized_type in FLANGED_COMPONENT_TYPES:
        # Flanged: bolt circle changes with class — mating dimension mismatch
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B16_5",
                standard_code="ASME B16.5 Bolt Circle Invariant",
                failure_mode_prevented="Flange mating dimension mismatch (bolt circle, OD, bolt holes differ)",
                explanation=(
                    f"PRESSURE UPGRADE FLANGE MISMATCH: Candidate Class {c_class} flange "
                    f"has different bolt circle diameter, OD, and bolt hole count vs "
                    f"Class {q_class}. They cannot physically bolt together per ASME B16.5."
                ),
            ),
        )

    # In-line, piping, fittings, or unclassified types: safe over-rating = Tier 1
    q_idx = PRESSURE_CLASS_HIERARCHY.index(q_class) if q_class in PRESSURE_CLASS_HIERARCHY else 0
    c_idx = PRESSURE_CLASS_HIERARCHY.index(c_class) if c_class in PRESSURE_CLASS_HIERARCHY else 0
    score = max(0.95, 1.0 - 0.01 * max(0, c_idx - q_idx))
    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, score, None)


def check_pressure_rating_psi(
    query_psi: float | None,
    candidate_psi: float | None,
) -> tuple[DynamicCompatibilityTier, float, RuleViolation | None]:
    """
    Evaluate operating PSI pressure rating for pipes and tubing.
    Down-rating = Tier 3. Equal or over-rating = Tier 1.
    """
    if query_psi is None and candidate_psi is None:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
    if query_psi is None or candidate_psi is None:
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.85, None)

    if abs(candidate_psi - query_psi) < 0.01:
        return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)

    if candidate_psi < query_psi:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="ASME_B16_5",
                standard_code="ASME B16.5 / B31.3",
                failure_mode_prevented="Pressure containment failure and rupture risk",
                explanation=(
                    f"PRESSURE DOWN-RATING: Candidate rated {candidate_psi:.0f} PSI < "
                    f"required {query_psi:.0f} PSI. Insufficient pressure containment."
                ),
            ),
        )

    # Safe over-rating
    score = min(1.0, 0.95 + 0.05 * (1.0 - (candidate_psi - query_psi) / query_psi))
    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, max(0.95, score), None)
