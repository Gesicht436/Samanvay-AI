from types import SimpleNamespace

import pytest

from backend.app.contracts.matching import CandidateMatch
from machine_learning.reranker import CompatibilityRanker
from machine_learning.tiers import Tier
from machine_learning.vector_search import VectorSearcher


class FakeClient:
    def __init__(self):
        self.request = None
        self.requests = []

    def query_points(self, **kwargs):
        self.request = kwargs
        self.requests.append(kwargs)
        score = {"dim": 0.91, "met": 0.82, "pt": 0.73, "std": 0.64}[kwargs["using"]]
        points = [
            SimpleNamespace(id="a", score=score, payload={"canonical_id": "a", "item_type": "VALVE", "size_nb_mm": 100, "pressure_class": 600}),
            SimpleNamespace(id="b", score=score - 0.1, payload={"canonical_id": "b", "item_type": "BOLT", "size_nb_mm": 100, "pressure_class": 300}),
        ]
        return SimpleNamespace(points=points)


class FakeEncoder:
    def encode(self, text, normalize_embeddings=True):
        return [0.1, 0.2]


class RecordingRanker:
    model = None

    def __init__(self):
        self.domain_scores = []

    def score(self, query, candidate, cosine, domain_scores):
        self.domain_scores.append(domain_scores)
        return cosine


def test_search_fetches_five_times_k_then_reranks_and_returns_contract_fields():
    client = FakeClient()
    searcher = VectorSearcher(client=client, encoder=FakeEncoder())
    ranker = CompatibilityRanker(model_path="missing-reranker-model.xgb")

    matches = searcher.get_candidate_skus("VALVE DN100 CLASS 300", top_k=1, reranker=ranker)

    assert client.request["limit"] == 5
    assert {request["using"] for request in client.requests} == {"dim", "met", "pt", "std"}
    assert len(matches) == 1
    assert isinstance(matches[0], CandidateMatch)
    assert matches[0].tier != Tier.TIER_4_REJECT
    assert isinstance(matches[0].violations, list)
    assert isinstance(matches[0].reasons, list)


def test_search_passes_all_four_domain_cosines_into_reranker():
    ranker = RecordingRanker()
    searcher = VectorSearcher(client=FakeClient(), encoder=FakeEncoder())

    searcher.get_candidate_skus("VALVE DN100 CLASS 300", top_k=1, reranker=ranker)

    assert ranker.domain_scores
    assert ranker.domain_scores[0] == {"dim": 0.91, "met": 0.82, "pt": 0.73, "std": 0.64}


def test_explicit_item_type_uses_a_qdrant_payload_filter():
    client = FakeClient()
    searcher = VectorSearcher(client=client, encoder=FakeEncoder())

    searcher.get_candidate_skus("VALVE DN100", item_type="VALVE")

    assert client.request["query_filter"] is not None


def test_named_vector_search_rejects_clients_without_query_points():
    searcher = VectorSearcher(client=object(), encoder=FakeEncoder())

    with pytest.raises(RuntimeError, match="query_points"):
        searcher.get_candidate_skus("VALVE DN100")
