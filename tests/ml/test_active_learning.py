from backend.app.contracts.matching import CandidateMatch, Tier
from machine_learning.active_learning import ActiveLearningBootstrapper, ActiveLearningQueue


def _match(canonical_id: str, score: float) -> CandidateMatch:
    return CandidateMatch(
        canonical_id=canonical_id,
        similarity=score,
        tier=Tier.TIER_2,
        canonical_description=f"item {canonical_id}",
    )


def test_queue_evicts_least_recently_used_entry_and_refreshes_access():
    queue = ActiveLearningQueue(capacity=2)
    first = queue.enqueue("query a", _match("A", 0.7))
    second = queue.enqueue("query b", _match("B", 0.7))
    queue.get(first.id)
    third = queue.enqueue("query c", _match("C", 0.7))

    assert queue.get(first.id) is not None
    assert queue.get(second.id) is None
    assert queue.get(third.id) is not None


def test_bootstrapper_queues_most_uncertain_candidates_first_to_retain_them():
    queue = ActiveLearningQueue(capacity=2)
    records = [
        {"query": "certain", "candidate": _match("A", 0.95)},
        {"query": "uncertain-1", "candidate": _match("B", 0.51)},
        {"query": "uncertain-2", "candidate": _match("C", 0.49)},
    ]

    added = ActiveLearningBootstrapper(queue).bootstrap(records)

    assert added == 2
    assert {item.candidate.canonical_id for item in queue.list_items()} == {"B", "C"}


def test_bootstrapper_keeps_each_record_cosine_for_reranker_training():
    queue = ActiveLearningQueue()
    records = [
        {"query": "query A", "candidate": _match("A", 0.51), "cosine": 0.2},
        {"query": "query B", "candidate": _match("B", 0.52), "cosine": 0.8},
    ]

    ActiveLearningBootstrapper(queue).bootstrap(records)
    items = {item.query: item for item in queue.list_items()}

    assert items["query A"].cosine == 0.2
    assert items["query B"].cosine == 0.8


def test_resolved_feedback_is_available_as_training_pair():
    queue = ActiveLearningQueue()
    item = queue.enqueue("request", _match("CAN-1", 0.7))

    queue.resolve(item.id, accepted=True)

    assert queue.training_examples() == [
        {"query": "request", "candidate": "item CAN-1", "label": 1, "cosine": 0.7}
    ]
