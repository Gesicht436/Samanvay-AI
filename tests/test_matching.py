from backend.app.contracts.matching import CandidateMatch, ExtractedMaterialAttributes, Tier
from backend.app.matching.tolerance import classify_candidate


def test_higher_pressure_is_safe_substitute():
    result = classify_candidate(ExtractedMaterialAttributes(raw_description="x", size_nb_mm=100, pressure_class=150), CandidateMatch(canonical_id="c1", similarity=0.92, size_nb_mm=100, pressure_class=300))
    assert result.tier == Tier.TIER_1
    assert result.routing == "auto-link"


def test_size_mismatch_is_incompatible():
    result = classify_candidate(ExtractedMaterialAttributes(raw_description="x", size_nb_mm=100), CandidateMatch(canonical_id="c1", similarity=0.99, size_nb_mm=150))
    assert result.tier == Tier.TIER_4_REJECT
    assert result.confidence == 0
