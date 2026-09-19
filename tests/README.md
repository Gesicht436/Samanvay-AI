# Test Suite & Quality Assurance (`tests/`)

This directory houses the comprehensive automated test suite for **Samanvay-AI**, ensuring safety, cryptographic integrity, API correctness, and machine learning accuracy.

---

## 1. Test Suite Architecture

```
tests/
├── conftest.py               # Shared PyTest fixtures (mock DB sessions, sample materials)
├── api/                      # REST API endpoint tests (FastAPI TestClient)
│   ├── test_audit_api.py     # SHA-256 chain verification & RFC 4180 CSV export
│   ├── test_graph_api.py     # Logistics distance & privacy attribute stripping
│   ├── test_inventory_api.py # Inventory CRUD & cross-CPSE privacy filtering
│   ├── test_match_api.py     # End-to-end semantic match & safety engine scoring
│   └── test_requisition_api.py # Idempotency keys & pessimistic locking concurrency
├── integration/              # Full-system integration tests
│   └── test_benchmarks.py    # Automated execution across 100+ golden benchmarks
├── ml/                       # Machine learning & NLP tests
│   └── test_ner.py           # Dialect normalizer & DeBERTa slot tagger extraction
└── unit/                     # Focused unit tests
    ├── test_chemistry.py     # Carbon Equivalent, weldability & PREN formulas
    ├── test_logistics.py     # Haversine, road circuity & BEE CO2 calculation
    ├── test_normalizer.py    # NFKC unicode cleaning & abbreviation expansion
    ├── test_ocr_and_mtc.py   # Dual-path PDF parsing & MTC table extraction
    ├── test_security.py      # Chained SHA-256 hashing & HMAC gate pass sealing
    └── test_tolerance.py     # Unit tests for all 21 engineering safety rules
```

---

## 2. Running Tests

### Run All Tests:
```bash
pytest tests/ -v
```

### Run by Domain:
```bash
# Run unit tests
pytest tests/unit/ -v

# Run API endpoint tests
pytest tests/api/ -v

# Run ML & NER tests
pytest tests/ml/ -v

# Run Golden Benchmark accuracy tests
pytest tests/integration/ -v
```

### Run with Test Coverage:
```bash
pytest tests/ --cov=backend/app --cov=rules --cov=ml --cov=graph --cov-report=term-missing
```
