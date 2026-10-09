from backend.app.contracts.matching import CandidateMatch, ExtractedMaterialAttributes, MatchResult
from machine_learning.safety import safety_violations
from machine_learning.tiers import Tier, assign_tier

from .asme_rules import metallurgy_substitutes, pressure_substitutes, size_matches


def classify_candidate(attributes: ExtractedMaterialAttributes, candidate: CandidateMatch) -> MatchResult:
    decisions = [
        size_matches(attributes.size_nb_mm, candidate.size_nb_mm),
        pressure_substitutes(attributes.pressure_class, candidate.pressure_class),
        metallurgy_substitutes(attributes.metallurgy or attributes.material_grade, candidate.metallurgy),
    ]
    violations = list(dict.fromkeys([
        *candidate.violations,
        *safety_violations(attributes.model_dump(), candidate.model_dump()),
        *(decision.reason for decision in decisions if not decision.allowed),
    ]))
    tier = assign_tier(candidate.similarity, violations)
    reasons = [decision.reason for decision in decisions] + violations
    confidence = candidate.similarity if tier != Tier.TIER_4_REJECT else 0.0
    routing = (
        "auto-link"
        if tier == Tier.TIER_1
        else "manual-entry"
        if tier == Tier.TIER_4_REJECT
        else "hitl"
    )
    return MatchResult(raw_description=attributes.raw_description, tier=tier, confidence=confidence, candidate=candidate, routing=routing, reasons=reasons)
