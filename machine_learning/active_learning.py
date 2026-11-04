"""Bounded human-review queue with uncertainty sampling and LRU retention."""

import hashlib
import json
import os
from collections import OrderedDict, deque
from datetime import UTC, datetime
from threading import RLock
from typing import Any, Optional, Dict

from pydantic import BaseModel, Field

from backend.app.contracts.matching import CandidateMatch


class ReviewItem(BaseModel):
    id: str
    query: str
    candidate: CandidateMatch
    uncertainty: float = Field(ge=0.0, le=1.0)
    cosine: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ActiveLearningQueue:
    def __init__(self, capacity: int = 500) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self._items: OrderedDict[str, ReviewItem] = OrderedDict()
        self._resolved: deque[dict[str, Any]] = deque(maxlen=capacity * 10)
        self._lock = RLock()

    def enqueue(
        self,
        query: str,
        candidate: CandidateMatch,
        uncertainty: float | None = None,
        cosine: float | None = None,
    ) -> ReviewItem:
        score_uncertainty = (
            uncertainty
            if uncertainty is not None
            else 1.0 - min(1.0, abs(float(candidate.similarity) - 0.5) * 2)
        )
        identity = hashlib.sha256(
            json.dumps([query, candidate.canonical_id], separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        item = ReviewItem(
            id=identity,
            query=query,
            candidate=candidate,
            uncertainty=score_uncertainty,
            cosine=float(candidate.similarity if cosine is None else cosine),
        )
        with self._lock:
            self._items[identity] = item
            self._items.move_to_end(identity)
            while len(self._items) > self.capacity:
                self._items.popitem(last=False)
        return item

    def get(self, item_id: str) -> ReviewItem | None:
        with self._lock:
            item = self._items.get(item_id)
            if item is not None:
                self._items.move_to_end(item_id)
            return item

    def list_items(self) -> list[ReviewItem]:
        with self._lock:
            return list(reversed(self._items.values()))

    def observe(self, query: str, candidate: CandidateMatch, cosine: float | None = None) -> ReviewItem | None:
        if candidate.tier.value == "Tier-1":
            return None
        return self.enqueue(query, candidate, cosine=cosine)

    def resolve(
        self,
        item_id: str,
        accepted: bool,
        corrected_candidate: str | None = None,
    ) -> dict[str, Any] | None:
        with self._lock:
            item = self._items.pop(item_id, None)
            if item is None:
                return None
            example = {
                "query": item.query,
                "candidate": corrected_candidate or item.candidate.canonical_description or item.candidate.canonical_id,
                "label": int(accepted),
                "cosine": item.cosine,
            }
            self._resolved.append(example)
            return example

    def training_examples(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(example) for example in self._resolved]


class ActiveLearningBootstrapper:
    def __init__(self, queue: ActiveLearningQueue) -> None:
        self.queue = queue

    def bootstrap(self, records: list[dict[str, Any]]) -> int:
        examples: list[tuple[float, str, CandidateMatch, float]] = []
        for record in records:
            candidate_value = record["candidate"]
            candidate = (
                candidate_value
                if isinstance(candidate_value, CandidateMatch)
                else CandidateMatch.model_validate(candidate_value)
            )
            if candidate.tier.value == "Tier-1":
                continue
            uncertainty = 1.0 - min(1.0, abs(float(candidate.similarity) - 0.5) * 2)
            examples.append(
                (
                    uncertainty,
                    str(record["query"]),
                    candidate,
                    float(
                        candidate.similarity
                        if record.get("cosine") is None
                        else record["cosine"]
                    ),
                )
            )

        initial_size = len(self.queue.list_items())
        for uncertainty, query, candidate, cosine in sorted(examples, key=lambda entry: entry[0]):
            self.queue.enqueue(
                query,
                candidate,
                uncertainty,
                cosine=cosine,
            )
        return len(self.queue.list_items()) - initial_size


_active_learning_queue = ActiveLearningQueue()


def get_active_learning_queue() -> ActiveLearningQueue:
    return _active_learning_queue


# ── ActiveLearningCache & Golden Benchmark Seeder ─────────────────────────────

class CacheEntry:
    def __init__(self, query_text: str, source_sku: str, decision: str, tier_override: str, officer: str):
        self.query_text = query_text
        self.source_sku = source_sku
        self.decision = decision
        self.tier_override = tier_override
        self.officer = officer
        self.stamp = ""


class ActiveLearningCache:
    def __init__(self, max_size=10000):
        self.max_size = max_size
        self.cache: Dict[tuple, CacheEntry] = OrderedDict()
        self.sku_stamps = {}

    def lookup(self, query_text: str, source_sku: str) -> Optional[CacheEntry]:
        key = (query_text, source_sku)
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def record_decision(self, query_text: str, source_sku: str, decision: str, tier_override: str, officer: str):
        key = (query_text, source_sku)
        entry = CacheEntry(query_text, source_sku, decision, tier_override, officer)
        self.cache[key] = entry
        self.cache.move_to_end(key)

        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

        if decision == "APPROVE":
            self.boost_approved(source_sku)
        elif decision == "REJECT":
            self.demote_rejected(source_sku)

    def boost_approved(self, sku_code: str):
        if len(self.sku_stamps) >= self.max_size and sku_code not in self.sku_stamps:
            self.sku_stamps.pop(next(iter(self.sku_stamps)))
        self.sku_stamps[sku_code] = "[VERIFIED BY HUMAN EXPERT]"

    def demote_rejected(self, sku_code: str):
        if len(self.sku_stamps) >= self.max_size and sku_code not in self.sku_stamps:
            self.sku_stamps.pop(next(iter(self.sku_stamps)))
        self.sku_stamps[sku_code] = "[REJECTED BY HUMAN EXPERT]"


def seed_from_golden_benchmarks(cache: ActiveLearningCache, benchmarks_path: str):
    if not os.path.exists(benchmarks_path):
        return

    with open(benchmarks_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return

    officer = "CHIEF_MATERIALS_ENGINEER_BOOTSTRAP"

    for item in data:
        query = item.get("query_text")
        sku = item.get("source_sku")
        tier = item.get("tier", 3)

        if not query or not sku:
            continue

        decision = "APPROVE" if tier in [1, 2] else "REJECT"
        tier_override = f"Tier {tier}"

        cache.record_decision(query, sku, decision, tier_override, officer)
