"""
Pydantic v2 Contracts for Matching, Equivalence Tiers, and Safety Validations.
Defines the Tier Distribution System taxonomy (Tier-1, Tier-2, Tier-3) and evaluation outputs.
"""

from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator
from backend.app.contracts.material import ExtractedMaterialAttributes


class EquivalenceTier(str, Enum):
    TIER_1_IDENTICAL = "TIER_1_IDENTICAL"          # 100% specification parity (exact drop-in)
    TIER_2_SUBSTITUTE = "TIER_2_SUBSTITUTE"        # Valid functional upgrade meeting or exceeding specs
    TIER_3_INCOMPATIBLE = "TIER_3_INCOMPATIBLE"    # Hard safety reject (unsafe down-rating, size mismatch, etc.)


class ToleranceViolation(BaseModel):
    """Specific engineering rule or tolerance failure."""
    rule_name: str = Field(..., description="Name of the evaluated engineering rule")
    field: str = Field(..., description="Violated attribute (e.g. size_nb_mm, pressure_class)")
    expected: str = Field(..., description="Required value or condition")
    actual: str = Field(..., description="Evaluated candidate value")
    message: str = Field(..., description="Human-readable safety explanation")


class ParameterMatchDetail(BaseModel):
    """Detailed inspection status for a single physical attribute."""
    parameter: str = Field(..., description="Attribute name (e.g. Size, Pressure, Metallurgy)")
    matched: bool = Field(..., description="True if compatible, False if violating safety")
    status: str = Field(..., description="EXACT, UPGRADE, or MISMATCH")
    source_value: Optional[str] = Field(default=None)
    candidate_value: Optional[str] = Field(default=None)
    note: Optional[str] = Field(default=None)


class MatchEvaluationResult(BaseModel):
    """
    Complete evaluation result produced by the ASME/ASTM Tier Distribution Engine.
    """
    model_config = ConfigDict(extra="ignore")

    tier: EquivalenceTier = Field(..., description="Assigned safety tier (Tier-1, Tier-2, Tier-3)")
    is_compatible: bool = Field(..., description="True if safe for installation (Tier-1 or Tier-2)")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall matching confidence")
    violations: List[ToleranceViolation] = Field(default_factory=list, description="List of safety violations, if any")
    parameter_checks: List[ParameterMatchDetail] = Field(default_factory=list, description="Per-attribute evaluation breakdown")
    rationale: str = Field(..., description="Clear engineering rationale explaining tier assignment")
    requires_hitl: bool = Field(default=False, description="True if human-in-the-loop review is required (e.g. Tier-2 or borderline)")
    source_description: Optional[str] = Field(default=None)
    candidate_description: Optional[str] = Field(default=None)
    candidate_canonical_id: Optional[str] = Field(default=None)
    canonical_id: Optional[str] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def sync_canonical_ids(cls, data: Any) -> Any:
        if isinstance(data, dict):
            cid = data.get("candidate_canonical_id") or data.get("canonical_id")
            if cid:
                data["candidate_canonical_id"] = cid
                data["canonical_id"] = cid
        return data


class MatchCandidate(BaseModel):
    """Candidate SKU retrieved by semantic vector search for rule verification."""
    canonical_id: str
    description: str
    vector_score: float
    attributes: ExtractedMaterialAttributes
