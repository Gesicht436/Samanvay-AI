# Active Learning & Feedback Calibration (`ml/active_learning/`)

This directory implements the Human-in-the-Loop (HITL) active learning cache and golden benchmark bootstrapper for **Samanvay-AI**.

---

## 1. File-by-File Breakdown

### `cache.py` — In-Memory Decision Cache
- **Purpose:** Caches expert human engineering approvals and rejections to instantly resolve identical or highly similar subsequent requisition queries without repeated expensive model inferences.
- **Key Classes:**
  - `CacheEntry`: Data container storing:
    - `query_text`: The raw requisition query.
    - `query_vector`: 1024-dim dense embedding vector.
    - `candidate_id`: Stock SKU identifier.
    - `human_decision`: Boolean approval (`True` = accepted substitute, `False` = rejected).
    - `engineer_notes`: Auditable rationale recorded by the procurement officer.
    - `timestamp`: ISO-8601 recording time.
  - `ActiveLearningCache`:
    - `lookup(query_vector, candidate_id, threshold=0.98)`: Checks if a near-identical query has previously received human sign-off.
    - `record(query_text, query_vector, candidate_id, decision, notes)`: Stores human verification.
    - `export_dataset()`: Serializes active learning logs for fine-tuning offline cross-encoders.

### `bootstrapper.py` — Golden Benchmark Preloader
- **Purpose:** Bootstraps cold-start performance by seeding the active learning cache with known validated pairs from `datasets/golden_benchmarks.json`.
- **Key Functions:**
  - `seed_from_golden_benchmarks(cache, benchmarks_path)`: Reads verified public enterprise benchmark pairs (e.g. cross-plant interchanges between IOCL Paradip and ONGC Hazira) and pre-populates the cache.

---

## 2. Theory: Active Learning in Industrial Decision Support

### The Human-in-the-Loop (HITL) Fallback Mechanism:
1. When $\text{Confidence} \ge 0.85$ and deterministic rules pass: Automatic Match Approval.
2. When deterministic rules fail: Automatic Safety Rejection.
3. When $0.60 \le \text{Confidence} < 0.85$ (ambiguous edge cases, missing schedule, or partial trim specifications): The system flags the pair as `REQUIRES_HITL_REVIEW`.
4. Once an engineer reviews and approves/rejects the pair in the Samanvay-AI UI, `ActiveLearningCache` preserves the decision.

---

## 3. Code Example

```python
from ml.active_learning.cache import ActiveLearningCache
from ml.active_learning.bootstrapper import seed_from_golden_benchmarks

cache = ActiveLearningCache()
# Bootstrap from verified golden benchmarks
seed_from_golden_benchmarks(cache, "datasets/golden_benchmarks.json")

# Record a new human approval
cache.record(
    query_text="GATE VALVE 4 INCH 300LB WCB",
    query_vector=[0.05] * 1024,
    candidate_id="IOCL-PR-VLV-00921",
    decision=True,
    notes="Approved: A350 LF2 candidate satisfies low-temperature requirement."
)
```
