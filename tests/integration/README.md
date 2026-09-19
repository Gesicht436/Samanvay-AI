# Integration & Benchmark Tests (`tests/integration/`)

This directory contains integration test suites that validate end-to-end performance against public sector golden benchmarks.

---

## 1. File Breakdown

### `test_benchmarks.py` — Golden Benchmark Accuracy Suite
- **Purpose:** Executes the entire hybrid matching pipeline (NER $\rightarrow$ Vector Search $\rightarrow$ Cross-Encoder $\rightarrow$ Engineering Safety Core) across the 100+ verified test cases in `data/golden_benchmarks.json`.
- **Key Functions:**
  - `_load_benchmarks()`: Loads benchmark cases.
  - `test_golden_benchmark_case(case)`: Parameterized test verifying:
    1. Top-1 retrieved candidate matches expected SKU.
    2. Computed Dynamic Compatibility Tier matches expected tier.
    3. Any engineering violations match expected violation codes.

---

## 2. Running Integration Tests

```bash
pytest tests/integration/test_benchmarks.py -v
```
