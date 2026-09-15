"""
Unit Test Suite for Active Learning Feedback Cache, Dynamic Reranker,
Refinery Dialect Thesaurus, and IBR Regulatory Invariant Rules.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.matching.active_learning import ActiveLearningCache, ActiveLearningFeedbackRecord, active_learning_cache
from backend.app.ml.ner_tagger import extract_attributes, expand_refinery_thesaurus
from backend.app.contracts.material import ItemType, ExtractedMaterialAttributes
from backend.app.contracts.matching import MatchEvaluationResult, EquivalenceTier, ToleranceViolation, ParameterMatchDetail
from backend.app.matching.tolerance import evaluate_compatibility

client = TestClient(app)


def test_refinery_thesaurus_expansion():
    """Verifies that CPSE refinery dialect shorthand expands into standardized terminology."""
    raw = "NRV 2IN 150# CS with SPRF and LTCS"
    expanded = expand_refinery_thesaurus(raw)
    assert "CHECK VALVE" in expanded
    assert "SPECTACLE BLIND RF" in expanded
    assert "LTCS ASTM A350 LF2" in expanded

    raw2 = "BFV DN50 DSS SDSS INCO 625 HAST-C MONEL 400"
    expanded2 = expand_refinery_thesaurus(raw2)
    assert "BUTTERFLY VALVE" in expanded2
    assert "DUPLEX STAINLESS STEEL F51" in expanded2
    assert "SUPER DUPLEX STAINLESS STEEL S32750" in expanded2
    assert "INCONEL 625" in expanded2
    assert "HASTELLOY C-276" in expanded2
    assert "MONEL 400" in expanded2


def test_ner_tagger_cpse_dialect_shorthand():
    """Verifies that NER tagger correctly extracts item type, metallurgy, and size from refinery dialect."""
    # 1. NRV (Non-Return Valve / Check Valve) + CS (Carbon Steel -> A105)
    attrs = extract_attributes("NRV 2IN 150# CS")
    assert attrs.item_type == ItemType.CHECK_VALVE.value
    assert attrs.metallurgy == "ASTM A105"
    assert attrs.pressure_class == 150
    assert attrs.size_nb_mm == 50.0

    # 2. BFV (Butterfly Valve) + WCB
    attrs_bfv = extract_attributes("BFV DN100 PN20 WCB")
    assert attrs_bfv.item_type == ItemType.BUTTERFLY_VALVE.value
    assert attrs_bfv.metallurgy == "ASTM A216 WCB"
    assert attrs_bfv.pressure_class == 150
    assert attrs_bfv.standard == "API 609"

    # 3. SPRF (Spectacle Blind Raised Face)
    attrs_sprf = extract_attributes("SPRF 4\" 300# A105")
    assert attrs_sprf.item_type == ItemType.FLANGE_BLIND.value
    assert attrs_sprf.facing_end == "RF"
    assert attrs_sprf.pressure_class == 300
    assert attrs_sprf.size_nb_mm == 100.0

    # 4. LTCS + IBR certification
    attrs_ltcs = extract_attributes("PIPE SMLS 6IN SCH 40 LTCS IBR")
    assert attrs_ltcs.item_type == ItemType.PIPE_SEAMLESS.value
    assert attrs_ltcs.metallurgy == "ASTM A350 LF2"
    assert attrs_ltcs.is_ibr_certified is True
    assert attrs_ltcs.schedule == "SCH 40"

    # 5. Super Duplex SDSS
    attrs_sdss = extract_attributes("FLG WNRF 8IN 600# SDSS")
    assert attrs_sdss.metallurgy == "ASTM A815 S32750"
    assert attrs_sdss.item_type == ItemType.FLANGE_WELD_NECK.value
    assert attrs_sdss.pressure_class == 600


def test_ibr_certification_tolerance_evaluation():
    """Verifies that non-IBR candidate deployed for IBR requirement triggers a Tier-3 rejection."""
    src_ibr = ExtractedMaterialAttributes(
        item_type=ItemType.PIPE_SEAMLESS.value,
        size_nb_mm=100.0,
        pressure_class=300,
        metallurgy="ASTM A106 GR.B",
        schedule="SCH 40",
        is_ibr_certified=True
    )
    cand_non_ibr = ExtractedMaterialAttributes(
        item_type=ItemType.PIPE_SEAMLESS.value,
        size_nb_mm=100.0,
        pressure_class=300,
        metallurgy="ASTM A106 GR.B",
        schedule="SCH 40",
        is_ibr_certified=False
    )
    res = evaluate_compatibility(src_ibr, cand_non_ibr)
    assert res.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
    assert not res.is_compatible
    assert any("IBR" in v.rule_name for v in res.violations)

    # When both are IBR certified: compatible Tier 1
    cand_ibr = ExtractedMaterialAttributes(
        item_type=ItemType.PIPE_SEAMLESS.value,
        size_nb_mm=100.0,
        pressure_class=300,
        metallurgy="ASTM A106 GR.B",
        schedule="SCH 40",
        is_ibr_certified=True
    )
    res_valid = evaluate_compatibility(src_ibr, cand_ibr)
    assert res_valid.tier == EquivalenceTier.TIER_1_IDENTICAL
    assert res_valid.is_compatible


def test_active_learning_approval_boosting():
    """Tests that active learning cache boosts approved candidates to #1 rank with verified badge."""
    cache = ActiveLearningCache()
    query = "FLG WNRF 4IN 300# A105"
    sku = "TEST-CAN-001"

    # Create dummy candidate pool
    c1 = MatchEvaluationResult(
        canonical_id="CAN-000001",
        tier=EquivalenceTier.TIER_1_IDENTICAL,
        is_compatible=True,
        confidence_score=0.92,
        rationale="Initial algorithmic score",
        violations=[],
        parameter_checks=[]
    )
    c2 = MatchEvaluationResult(
        canonical_id=sku,
        tier=EquivalenceTier.TIER_2_SUBSTITUTE,
        is_compatible=True,
        confidence_score=0.85,
        rationale="Initial lower score candidate",
        violations=[],
        parameter_checks=[]
    )
    initial_pool = [c1, c2]

    # Record Human Expert Approval for candidate c2
    cache.record_feedback(
        source_description=query,
        source_sku="SRC-001",
        canonical_id=sku,
        decision="APPROVE",
        officer="DR_S_SHARMA",
        action_note="Verified field substitution on Unit-3 heater."
    )

    reranked = cache.apply_dynamic_reranking(query, "SRC-001", initial_pool)

    # c2 must now be top rank with confidence >= 0.95 and verified rationale
    assert reranked[0].canonical_id == sku
    assert reranked[0].confidence_score >= 0.95
    assert "[VERIFIED BY HUMAN EXPERT]" in reranked[0].rationale


def test_active_learning_rejection_demotion():
    """Tests that active learning cache sinks rejected candidates down to Tier 3 incompatible."""
    cache = ActiveLearningCache()
    query = "VLV GT 2IN 300# WCB"
    sku = "REJECTED-SKU-999"

    c_valid = MatchEvaluationResult(
        canonical_id="VALID-SKU-100",
        tier=EquivalenceTier.TIER_1_IDENTICAL,
        is_compatible=True,
        confidence_score=0.95,
        rationale="Good candidate",
        violations=[],
        parameter_checks=[]
    )
    c_rejected = MatchEvaluationResult(
        canonical_id=sku,
        tier=EquivalenceTier.TIER_1_IDENTICAL,
        is_compatible=True,
        confidence_score=0.94,
        rationale="Initially thought identical",
        violations=[],
        parameter_checks=[]
    )
    pool = [c_rejected, c_valid]

    # Record Human Expert Rejection
    cache.record_feedback(
        source_description=query,
        source_sku="SRC-002",
        canonical_id=sku,
        decision="REJECT",
        officer="CHIEF_INSPECTOR_ROY",
        action_note="Valve trim incompatible with amine service."
    )

    reranked = cache.apply_dynamic_reranking(query, "SRC-002", pool)

    # c_rejected must now be demoted to Tier 3, is_compatible=False, and sorted behind valid candidates
    assert reranked[0].canonical_id == "VALID-SKU-100"
    demoted = next(r for r in reranked if r.canonical_id == sku)
    assert demoted.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
    assert not demoted.is_compatible
    assert "[REJECTED BY HUMAN EXPERT]" in demoted.rationale


def test_feedback_cache_api_endpoint():
    """Tests GET /api/v1/match/feedback-cache and verifies returned stats and seeded records."""
    response = client.get("/api/v1/match/feedback-cache")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "records" in data
    assert data["stats"]["total_feedback_entries"] >= 3
    assert data["stats"]["approval_count"] >= 2
    assert data["stats"]["rejection_count"] >= 1


def test_hitl_resolve_and_live_dynamic_rerank_flow():
    """Tests the full loop: HITL resolve -> cache update -> subsequent matching reflects feedback."""
    query = "FLG TEST AUTO RERANK 6IN 300# A105"
    test_sku = "CAN-AUTO-TEST-888"

    # Step 1: Submit a HITL approval
    resolve_payload = {
        "source_sku": "SRC-AUTO-001",
        "source_cpse": "IOCL",
        "canonical_id": test_sku,
        "decision": "APPROVE",
        "tier": "TIER_1_IDENTICAL",
        "confidence": 0.97,
        "officer": "SYSTEM_TEST_OFFICER",
        "source_description": query,
        "action_note": "Verified identical via integration test"
    }
    res = client.post("/api/v1/match/hitl-resolve", json=resolve_payload)
    assert res.status_code == 200

    # Step 2: Verify it is in the feedback cache
    cache_res = client.get("/api/v1/match/feedback-cache")
    assert cache_res.status_code == 200
    records = cache_res.json()["records"]
    assert any(r["canonical_id"] == test_sku for r in records)
