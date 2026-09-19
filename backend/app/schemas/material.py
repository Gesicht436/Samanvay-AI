"""
Samanvay-AI Core Pydantic v2 Schemas — Material & Matching Contracts.

These schemas define the OpenAPI contracts for dynamic per-part
compatibility matching, deterministic safety gate results, and
TreeSHAP explainability outputs.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


# ── Dynamic Compatibility Tier (Computed at Runtime per Q↔C Pair) ─────────


class DynamicCompatibilityTier(str, Enum):
    """
    Runtime-computed compatibility tier between a query part Q and candidate part C.
    Never stored statically on inventory items — always a relational computation.
    """

    TIER_1_IDENTICAL = "TIER_1_IDENTICAL"  # >= 95% match, identical dims & metallurgy
    TIER_2_SUBSTITUTE = "TIER_2_SUBSTITUTE"  # 80%-94%, safe upgrade, requires HITL
    TIER_3_INCOMPATIBLE = "TIER_3_INCOMPATIBLE"  # < 80% OR zero-tolerance violation


# ── Extracted Material Attributes (from OCR/NER with graceful degradation) ─


class ExtractedMaterialAttributes(BaseModel):
    """
    Extracted from OCR/MTC with support for graceful degradation on
    sparse/stained scans. Missing non-dimensional fields are set to None
    with is_incomplete=True rather than causing HTTP 500 failures.
    """

    item_type: Optional[str] = Field(None, description="e.g. FLANGE, GATE_VALVE, PIPE, PUMP")
    size_nb_mm: Optional[float] = Field(None, description="Nominal bore in mm (e.g. 100.0 for 4\")")
    pressure_class: Optional[int] = Field(None, description="ASME pressure class (e.g. 150, 300, 600)")
    pressure_rating_psi: Optional[float] = Field(None, description="Operating PSI rating for pipes/tubing")
    schedule: Optional[str] = Field(None, description="Pipe schedule (e.g. SCH 40, SCH 80)")
    metallurgy: Optional[str] = Field(None, description="Material grade (e.g. ASTM A105, A182 F316L)")
    facing_end: Optional[str] = Field(None, description="e.g. RF, RTJ, FF, BW, SW")
    standard: Optional[str] = Field(None, description="e.g. ASME B16.5, API 600, ASTM A269")
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Equipment-specific: trim_no, port_bore, seal_plan, coating, etc.",
    )

    # Graceful Degradation & Sparsity Flags
    is_incomplete: bool = Field(
        default=False,
        description="True if required non-dimensional fields could not be extracted",
    )
    missing_attributes: list[str] = Field(
        default_factory=list,
        description="Names of obscured or unparsed attributes",
    )
    confidence_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Mean OCR/NER extraction confidence"
    )
    requires_hitl: bool = Field(
        default=False,
        description="True if routed to HITL triage queue due to low confidence or sparse data",
    )

    model_config = {"extra": "allow"}

    @classmethod
    def _parse_size(cls, val: Any) -> Optional[float]:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip().upper()
        import re
        m = re.search(r'([\d\.]+)', s)
        if m:
            num = float(m.group(1))
            if 'IN' in s or '"' in s:
                return round(num * 25.4, 2)
            return num
        return None

    @classmethod
    def _parse_int(cls, val: Any) -> Optional[int]:
        if val is None:
            return None
        if isinstance(val, int):
            return val
        s = str(val).strip().upper().replace("#", "").replace("CLASS", "").strip()
        import re
        m = re.search(r'\d+', s)
        return int(m.group(0)) if m else None

    @model_validator(mode="before")
    @classmethod
    def _normalize_dict_input(cls, data: Any) -> Any:
        if isinstance(data, dict):
            obj = dict(data)
            props = dict(obj.get("properties") or {})
            
            # Map shorthand keys
            if "size" in obj and "size_nb_mm" not in obj:
                obj["size_nb_mm"] = cls._parse_size(obj.pop("size"))
            elif "size_nb_mm" in obj:
                obj["size_nb_mm"] = cls._parse_size(obj["size_nb_mm"])

            if "rating" in obj and "pressure_class" not in obj:
                parsed_rating = cls._parse_int(obj.pop("rating"))
                obj["pressure_class"] = parsed_rating
            elif "pressure_class" in obj:
                obj["pressure_class"] = cls._parse_int(obj["pressure_class"])

            if "material" in obj and "metallurgy" not in obj:
                obj["metallurgy"] = obj.pop("material")

            if "facing" in obj and "facing_end" not in obj:
                obj["facing_end"] = obj.pop("facing")

            # Collect unmapped extra keys into properties
            known_fields = {
                "item_type", "size_nb_mm", "pressure_class", "pressure_rating_psi",
                "schedule", "metallurgy", "facing_end", "standard", "properties",
                "is_incomplete", "missing_attributes", "confidence_score", "requires_hitl"
            }
            extra_keys = [k for k in obj.keys() if k not in known_fields]
            for k in extra_keys:
                props[k] = obj.pop(k)
            obj["properties"] = props
            return obj
        return data


# ── Physical Attributes (Query or Inventory Item) ─────────────────────────


class PhysicalAttributes(BaseModel):
    """Typed physical specification of a part (query or candidate)."""

    item_type: str = Field(..., description="e.g. FLANGE, GATE_VALVE, PIPE, PUMP, TUBE")
    size_nb_mm: Optional[float] = Field(None, description="Nominal bore in mm")
    pressure_class: Optional[int] = Field(None, description="ASME pressure class")
    pressure_rating_psi: Optional[float] = Field(None, description="Operating PSI rating")
    schedule: Optional[str] = Field(None, description="Pipe schedule")
    metallurgy: Optional[str] = Field(None, description="Material grade")
    facing_end: Optional[str] = Field(None, description="Flange facing type")
    standard: Optional[str] = Field(None, description="Manufacturing standard")
    properties: dict[str, Any] = Field(default_factory=dict)
    is_incomplete: bool = Field(default=False)
    missing_attributes: list[str] = Field(default_factory=list)


# ── Match Request ─────────────────────────────────────────────────────────


class MatchRequest(BaseModel):
    """Search payload for cross-CPSE spare part discovery."""

    query_text: Optional[str] = Field(None, description="Free-form engineer search prompt")
    source_sku: Optional[str] = Field(None, description="Known SKU being replaced")
    source_attributes: Optional[PhysicalAttributes] = Field(
        None, description="Explicit physical attributes for structured search"
    )
    requesting_depot_id: Optional[str] = Field(
        None, description="Current depot ID for GIS transit calculation"
    )
    target_depots: Optional[list[str]] = Field(
        None, description="Filter candidate search radius to specific depots"
    )
    top_k: int = Field(default=10, ge=1, le=50)


# ── Property-by-Property Evaluation ──────────────────────────────────────


class PropertyEvaluationStatus(str, Enum):
    """Status of a single physical property evaluation."""

    IDENTICAL = "IDENTICAL"  # 100% exact parity
    SAFE_UPGRADE = "SAFE_UPGRADE"  # Exceeds spec safely
    ADAPTABLE = "ADAPTABLE"  # Minor variance requiring HITL
    HARD_REJECT = "HARD_REJECT"  # Dimensional mismatch or fatal violation


class PropertyEvaluation(BaseModel):
    """Evaluation result for a single physical property (Q vs C)."""

    property_name: str  # DIMENSIONS, PRESSURE_RATING, METALLURGY, CONNECTION, etc.
    tier: DynamicCompatibilityTier
    score: float = Field(..., ge=0.0, le=1.0)
    searched_value: Optional[str] = None
    candidate_value: Optional[str] = None
    status: PropertyEvaluationStatus
    comment: str


class PropertyScorecard(BaseModel):
    """Granular multi-property breakdown for a candidate match."""

    dimensions: PropertyEvaluation  # Hard zero-tolerance: Tier 3 if mismatched
    pressure: PropertyEvaluation  # Hard zero-tolerance: Tier 3 if down-rated
    metallurgy: PropertyEvaluation  # Tier 3 if downgraded
    connection: PropertyEvaluation  # Tier 3 if mechanically incompatible
    equipment_specific: dict[str, PropertyEvaluation] = Field(
        default_factory=dict,
        description="Component-specific properties: trim, schedule, port bore, etc.",
    )


# ── Rule Violation ────────────────────────────────────────────────────────


class RuleViolation(BaseModel):
    """A zero-tolerance engineering rule violation detected by the deterministic safety gate."""

    module_name: str  # e.g. "ASME_B16_5", "ASTM_METALLURGY_DAG"
    standard_code: str  # e.g. "ASME B16.5", "NACE MR0175"
    failure_mode_prevented: str  # e.g. "Hydrostatic rupture under operating pressure"
    explanation: str  # Human-readable engineering explanation

    @property
    def rule_name(self) -> str:
        return self.module_name

    @property
    def description(self) -> str:
        return f"{self.failure_mode_prevented}: {self.explanation}"


# ── Candidate Match Result ────────────────────────────────────────────────


class CandidateMatchResult(BaseModel):
    """Complete match result for a single candidate surplus part."""

    sku_code: str
    cpse: str
    depot_id: str
    depot_location: str
    standard_description: str
    available_qty: int
    days_idle: int
    attributes: PhysicalAttributes

    # Granular Physical Property-by-Property Breakdown
    property_scorecard: PropertyScorecard

    # Dynamic Runtime Evaluated Metrics relative to query Q
    compatibility_score: float = Field(
        ..., ge=0.0, le=1.0, description="Runtime ML composite score"
    )
    compatibility_tier: DynamicCompatibilityTier
    is_compatible: bool = Field(
        ..., description="True if Tier 1 or Tier 2; False if Tier 3"
    )
    requires_hitl: bool = Field(
        ..., description="True for Tier 2 substitutes or sparse data"
    )
    engineering_upgrades: list[str] = Field(default_factory=list)
    rule_violations: list[RuleViolation] = Field(default_factory=list)

    # TreeSHAP Attribution Explanations
    shap_explanations: list[str] = Field(default_factory=list)

    # Inter-CPSE Logistics Summary
    cisf_eligible: bool = True
    transit_distance_km: float = 0.0
    transit_lead_hours: int = 0


# ── Match Response ────────────────────────────────────────────────────────


class MatchResponse(BaseModel):
    """Response payload for cross-CPSE spare part discovery."""

    query_id: str
    searched_attributes: PhysicalAttributes
    total_candidates_evaluated: int
    execution_time_ms: float
    candidates: list[CandidateMatchResult]


# ── Compatibility Evaluation Result (from tolerance engine) ───────────────


class CompatibilityResult(BaseModel):
    """Output from the deterministic tolerance evaluation engine."""

    compatibility_tier: DynamicCompatibilityTier
    composite_score: float = Field(..., ge=0.0, le=1.0)
    is_compatible: bool
    requires_hitl: bool = False
    property_scorecard: Optional[PropertyScorecard] = None
    rule_violations: list[RuleViolation] = Field(default_factory=list)
    engineering_upgrades: list[str] = Field(default_factory=list)
    summary: str = ""

    @property
    def tier(self) -> DynamicCompatibilityTier:
        return self.compatibility_tier

    @property
    def score(self) -> float:
        return self.composite_score

    @property
    def explanation(self) -> str:
        if self.rule_violations:
            return self.rule_violations[0].explanation
        if self.engineering_upgrades:
            return "; ".join(self.engineering_upgrades)
        return self.summary or "Direct interchangeable engineering match"
