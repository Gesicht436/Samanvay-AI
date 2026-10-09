from enum import StrEnum

from pydantic import BaseModel, Field


class EquivalenceTier(StrEnum):
    TIER_1 = "Tier-1"
    TIER_2 = "Tier-2"
    TIER_3 = "Tier-3"


class Tier(StrEnum):
    TIER_1 = "Tier-1"
    TIER_2 = "Tier-2"
    TIER_3 = "Tier-3"
    TIER_4_REJECT = "Tier-4-Reject"


class ExtractedMaterialAttributes(BaseModel):
    raw_description: str = ""
    item_type: str | None = None
    size_nb_mm: float | None = None
    pressure_class: int | None = None
    metallurgy: str | None = None
    facing_end: str | None = None
    standard: str | None = None
    material_grade: str | None = None
    indian_standard: str | None = None
    oisd_standard: str | None = None
    eil_specification: str | None = None
    gem_category: str | None = None
    gem_bid_number: str | None = None
    cppp_tender_id: str | None = None
    mesc_code: str | None = None
    manufacturer: str | None = None
    product_form: str | None = None
    coating: str | None = None
    inspection_class: str | None = None
    document_number: str | None = None
    project: str | None = None
    end_connection: str | None = None
    temperature_rating: float | None = None
    purchase_order: str | None = None
    certificate_number: str | None = None
    bid_number: str | None = None
    inspection_agency: str | None = None


class CandidateMatch(BaseModel):
    canonical_id: str
    similarity: float = Field(ge=0, le=1)
    item_type: str | None = None
    size_nb_mm: float | None = None
    pressure_class: int | None = None
    metallurgy: str | None = None
    facing_end: str | None = None
    standard: str | None = None
    canonical_description: str | None = None
    indian_standard: str | None = None
    oisd_standard: str | None = None
    eil_specification: str | None = None
    gem_category: str | None = None
    gem_bid_number: str | None = None
    cppp_tender_id: str | None = None
    mesc_code: str | None = None
    manufacturer: str | None = None
    product_form: str | None = None
    coating: str | None = None
    inspection_class: str | None = None
    document_number: str | None = None
    project: str | None = None
    end_connection: str | None = None
    temperature_rating: float | None = None
    purchase_order: str | None = None
    certificate_number: str | None = None
    bid_number: str | None = None
    inspection_agency: str | None = None
    tier: Tier = Tier.TIER_3
    violations: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    domain_scores: dict[str, float] = Field(default_factory=dict)


class MatchResult(BaseModel):
    raw_description: str
    tier: Tier
    confidence: float = Field(ge=0, le=1)
    candidate: CandidateMatch | None = None
    matches: list[CandidateMatch] = Field(default_factory=list)
    routing: str
    reasons: list[str] = Field(default_factory=list)
