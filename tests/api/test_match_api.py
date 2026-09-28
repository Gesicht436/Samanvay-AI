import pytest
from fastapi.testclient import TestClient

from backend.main import app
from ml.ner.normalizer import DialectNormalizer
from rules.tolerance import evaluate_pair
from ml.ranking.ranker import CompatibilityRanker
from backend.app.schemas.material import MatchRequest, MatchSearchResponse
from backend.app.services.match_service import (
    parse_query,
    _resolve_item_type,
    _check_cross_standard_equivalence,
    _compute_mii_scoring,
    _resolve_tier,
    search_matches,
)
from backend.app.models.base import SessionLocal
from backend.app.models.tables import InventoryItem


client = TestClient(app)


def test_normalizer_and_matching_pipeline():
    normalizer = DialectNormalizer()
    norm = normalizer.normalize("FLG WNRF 4IN 300# A105 SCH 40")

    assert norm.get("item_type") == "FLANGE"
    assert norm.get("size_nb_mm") == 100.0
    assert norm.get("pressure_class") == 300
    assert "A105" in norm.get("metallurgy", "")

    query_part = {
        "item_type": "FLANGE",
        "size_nb_mm": 100.0,
        "pressure_class": 300,
        "metallurgy": "ASTM A105",
        "properties": {"facing": "RF"},
    }

    # Identical candidate
    cand_identical = {
        "item_type": "FLANGE",
        "size_nb_mm": 100.0,
        "pressure_class": 300,
        "metallurgy": "ASTM A105",
        "properties": {"facing": "RF"},
    }
    result_identical = evaluate_pair(query_part, cand_identical)
    assert result_identical.is_compatible is True
    assert "TIER_1" in result_identical.compatibility_tier.name

    # Incompatible size
    cand_wrong_size = {
        "item_type": "FLANGE",
        "size_nb_mm": 150.0,
        "pressure_class": 300,
        "metallurgy": "ASTM A105",
        "properties": {"facing": "RF"},
    }
    result_wrong_size = evaluate_pair(query_part, cand_wrong_size)
    assert result_wrong_size.is_compatible is False
    assert len(result_wrong_size.rule_violations) > 0
    assert "DIM" in str(result_wrong_size.rule_violations[0].module_name)


def test_compatibility_ranker_scoring():
    ranker = CompatibilityRanker()
    q = {"item_type": "VALVE", "size_nb_mm": 50.0, "pressure_class": 150, "metallurgy": "A216 WCB"}
    c1 = {"item_type": "VALVE", "size_nb_mm": 50.0, "pressure_class": 150, "metallurgy": "A216 WCB"}
    c2 = {"item_type": "VALVE", "size_nb_mm": 50.0, "pressure_class": 300, "metallurgy": "A216 WCB"}

    score1 = ranker.predict(q, c1)
    score2 = ranker.predict(q, c2)

    assert score1 >= 0.80
    assert isinstance(score2, float)


def test_match_service_parse_query_with_model():
    req = MatchRequest(
        query_text="GATE VALVE 4IN 150# A216 WCB",
        item_type="VALVE",
        size_nb_mm=100.0,
        pressure_class=150,
        metallurgy="ASTM A216 WCB",
        sour_service=True,
    )
    query_part, normalized = parse_query(req)
    assert query_part["item_type"] == "VALVE"
    assert query_part["size_nb_mm"] == 100.0
    assert query_part["pressure_class"] == 150
    assert query_part["properties"].get("sour_service") is True
    assert query_part["properties"].get("hardness_max_hrc") == 22.0


def test_match_service_helpers():
    base_type, sub_type = _resolve_item_type("GATE_VALVE")
    assert base_type == "VALVE"
    assert sub_type == "GATE"

    base_type, sub_type = _resolve_item_type("WN_FLANGE")
    assert base_type == "FLANGE"
    assert sub_type == "WN"

    assert _resolve_tier(0.96, True) == "Tier 1"
    assert _resolve_tier(0.85, True) == "Tier 2"
    assert _resolve_tier(0.70, True) == "Tier 3"
    assert _resolve_tier(0.99, False) == "Tier 3"


def test_match_search_endpoint():
    response = client.post(
        "/api/v1/match/search",
        json={
            "query_text": "FLG WNRF 4IN 300# A105",
            "item_type": "FLANGE",
            "size_nb_mm": 100.0,
            "pressure_class": 300,
        },
        headers={"X-CPSE-ID": "IOCL"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "candidates" in data
    assert isinstance(data["candidates"], list)

    # Validate against MatchSearchResponse schema
    validated = MatchSearchResponse(**data)
    assert validated.query == "FLG WNRF 4IN 300# A105"

    # Verify Attribute-Level Privacy: cross-CPSE candidates must NOT have unit_cost_inr
    for cand in validated.candidates:
        if cand.cpse != "IOCL":
            assert cand.unit_cost_inr is None
            assert cand.total_value_inr is None


def test_match_benchmark_endpoint():
    response = client.get("/api/v1/match/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["total_cases_evaluated"] == 150
    assert data["precision_zero_tolerance"] == 1.0
