# Automated Test Suite (`tests`)

## 1. Overview
The `tests` directory contains the automated test suite for Samanvay-AI, implemented using **Pytest** and **HTTPX/TestClient**.

The test suite covers:
- Deterministic ASME, ASTM, and IBR engineering compatibility invariants.
- Machine learning attribute extraction and refinery dialect normalization.
- Active learning feedback persistence and dynamic online candidate reranking.
- Inter-CPSE logistics routing, inventory reservation locks, and CISF gate pass issuance.
- Document ingestion, OCR pipelines, and tabular MTC chemical analysis.
- End-to-end FastAPI endpoint contracts and database persistence.

---

## 2. Test Modules Breakdown (82 Test Cases)

| Test File | Tests | Focus Area |
|---|---|---|
| `test_active_learning.py` | 7 | Active learning feedback cache, rank #1 approval boosting, rejection demotion, dialect thesaurus, and IBR tolerance checks. |
| `test_api.py` | 11 | FastAPI route integration (`/match/single`, `/hitl-resolve`, `/requisition/create`, `/depots`). |
| `test_asme_rules.py` | 11 | ASME B16.5 pressure class ladders, ASTM metallurgy directed graph, and mating face compatibility. |
| `test_audit.py` | 5 | Sovereign audit ledger persistence, parameter filtering, and SHA-256 digital seal verification. |
| `test_graph_queries.py` | 3 | Neo4j Cypher query execution, surplus radar searches, and SKU reconciliation links. |
| `test_ingestion.py` | 4 | OCR text parsing, PDF table extraction, and EN 10204 3.1 MTC chemistry parsing. |
| `test_logistics.py` | 8 | Haversine road distance calculations, inventory locks, and digital CISF material gate pass generation. |
| `test_ml_extraction.py` | 6 | Slot-filling NER tagger extraction across IOCL, ONGC, and BPCL naming conventions. |
| `test_piping_spec_rules.py` | 17 | ASME B36.10M schedules, NACE MR0175 sour service, B16.47 Series A vs B, and IBR 1950 rules. |
| `test_rotating_rules.py` | 7 | IS/IEC 60079 flameproof motors, API 682 seal flush plans, and ISO 15 bearing clearances. |
| `test_storage.py` | 3 | SQLAlchemy session management, database migrations, and audit table transactions. |

---

## 3. Running the Tests

### A. Run All Tests
From the project root:
```powershell
uv run pytest
```
*Expected result: 82 passed in ~55 seconds.*

### B. Run a Specific Test Module
```powershell
uv run pytest tests/test_active_learning.py -v
```

### C. Run Tests by Keyword Filter
```powershell
uv run pytest -k "asme" -v
```

### D. Run with Detailed Print Statements
```powershell
uv run pytest -s
```

---

## 4. Test Design Principles for Contributors

1. Deterministic Isolation: Tests must not depend on live internet connections or running third-party database servers.
   - Neo4j graph calls gracefully fall back to an in-memory dictionary graph during tests.
   - Qdrant vector calls fall back to in-memory feature embedding search.
   - Database operations use an in-memory or temporary SQLite database.
2. Exact Assertions: In safety-critical validation tests, always assert exact tier outputs (`EquivalenceTier.TIER_3_INCOMPATIBLE`), specific violation rule names, and exact compatibility flags (`is_compatible is False`).
3. Regression Prevention: Any new rule or dialect term added to `ner_tagger.py` or `asme_rules.py` must be accompanied by corresponding test cases in `test_asme_rules.py` or `test_active_learning.py`.
