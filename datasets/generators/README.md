# Dataset Generators

This directory contains the synthetic dataset generation harness responsible for creating reproducible benchmark corpora, enterprise inventory inventories, and degraded OCR test streams.

---

## Script Breakdown

### 1. `generate_datasets.py`
- **Output Targets**:
  1. `datasets/inventory_catalog.csv`: 5,000+ items across 7 CPSEs with simulated ERP noise, 12% property sparsity, and physical depot locations.
  2. `datasets/golden_benchmarks.json`: 150 paired engineering test cases (50 Tier 1 Identical, 50 Tier 2 Safe Upgrades, 50 Tier 3 Incompatible traps) targeting all 21 codified deterministic engineering rules.
  3. `datasets/ocr_payloads.json`: 500 simulated PaddleOCR and EasyOCR document extractions containing 10% low-confidence scans and 5% OCR character hallucination test cases (e.g., numeral '0' read as letter 'O', yield strength digit substitutions).
- **Execution Command**:
  ```powershell
  uv run python datasets/generators/generate_datasets.py
  ```
