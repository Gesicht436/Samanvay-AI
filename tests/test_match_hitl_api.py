from fastapi.testclient import TestClient

from backend.app.contracts.matching import CandidateMatch, Tier
from backend.app.main import app
from machine_learning.active_learning import ActiveLearningQueue


def test_hitl_queue_bootstrap_list_and_resolve(monkeypatch):
    from backend.app.api.v1 import match

    queue = ActiveLearningQueue(capacity=4)
    monkeypatch.setattr(match, "get_active_learning_queue", lambda: queue)
    client = TestClient(app)
    candidate = CandidateMatch(
        canonical_id="CAN-1",
        similarity=0.7,
        tier=Tier.TIER_2,
        canonical_description="GATE VALVE DN100",
    )

    bootstrap = client.post(
        "/v1/match/hitl-bootstrap",
        json={"items": [{"query": "GATE VALVE DN100", "candidate": candidate.model_dump(mode="json")}]},
    )

    assert bootstrap.status_code == 200
    assert bootstrap.json()["items_added"] == 1
    queued = client.get("/v1/match/hitl-queue")
    assert queued.status_code == 200
    item = queued.json()["items"][0]
    resolved = client.post(
        "/v1/match/hitl-resolve",
        json={"item_id": item["id"], "accepted": False, "corrected_candidate": "GATE VALVE DN100 CLASS 300"},
    )

    assert resolved.status_code == 200
    assert resolved.json()["training_example"] == {
        "query": "GATE VALVE DN100",
        "candidate": "GATE VALVE DN100 CLASS 300",
        "label": 0,
        "cosine": 0.7,
    }
    assert client.get("/v1/match/hitl-queue").json()["items"] == []


def test_hitl_resolve_reports_unknown_review_item():
    client = TestClient(app)

    response = client.post(
        "/v1/match/hitl-resolve",
        json={"item_id": "unknown", "accepted": True},
    )

    assert response.status_code == 404


def test_match_api_returns_ranked_candidates_and_domain_scores(monkeypatch):
    from backend.app.api import deps

    candidate = CandidateMatch(
        canonical_id="CAN-1",
        similarity=0.91,
        tier=Tier.TIER_1,
        item_type="VALVE",
        size_nb_mm=100,
        pressure_class=600,
        domain_scores={"dim": 0.95, "met": 0.9, "pt": 0.92, "std": 0.87},
    )

    class FakeSearcher:
        def __init__(self):
            self.request = None

        def get_candidate_skus(self, description, top_k, reranker):
            self.request = (description, top_k, reranker)
            return [candidate]

    searcher = FakeSearcher()
    app.dependency_overrides[deps.get_vector_searcher] = lambda: searcher
    try:
        response = TestClient(app).post(
            "/v1/match",
            json={"raw_description": "VALVE DN100 CLASS 300", "top_k": 3},
        )
    finally:
        app.dependency_overrides.pop(deps.get_vector_searcher, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["matches"][0]["canonical_id"] == "CAN-1"
    assert payload["matches"][0]["domain_scores"] == candidate.domain_scores
    assert searcher.request[1] == 3
    assert searcher.request[2] is not None


def test_match_api_returns_service_unavailable_instead_of_mock_result(monkeypatch):
    from backend.app.api import deps

    def unavailable():
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Embedding model is not installed")

    app.dependency_overrides[deps.get_vector_searcher] = unavailable
    try:
        response = TestClient(app).post("/v1/match", json={"raw_description": "VALVE DN100"})
    finally:
        app.dependency_overrides.pop(deps.get_vector_searcher, None)

    assert response.status_code == 503
    assert response.json()["detail"] == "Embedding model is not installed"


def test_dashboard_summary_exposes_live_review_and_feature_status(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from backend.app.api.v1 import dashboard

    monkeypatch.setattr(
        dashboard,
        "get_settings",
        lambda: SimpleNamespace(
            model_weights_path=str(tmp_path / "missing-model"),
            qdrant_host="localhost",
            qdrant_port=6333,
            qdrant_collection="canonical_materials",
        ),
    )
    monkeypatch.setattr(dashboard, "get_active_learning_queue", lambda: ActiveLearningQueue(capacity=7))

    response = TestClient(app).get("/v1/dashboard/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["vector_search"]["ready"] is False
    assert payload["pending_reviews"] == 0
    assert payload["review_capacity"] == 7
    assert payload["capabilities"]["named_vector_domains"] == ["dim", "met", "pt", "std"]
    assert payload["ocr"]["routing"] == "per_page_hybrid"
    assert payload["ocr"]["raster_dpi"] == 300
    assert payload["ocr"]["preprocessing"] == ["denoise", "deskew", "contrast"]
    assert payload["ocr"]["primary_engine"] == "PaddleOCR"
    assert payload["ocr"]["fallback_engine"] == "EasyOCR"
    assert payload["ocr"]["manufacturer_tpi_extraction"] is True
