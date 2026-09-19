# Unit Test Suite (`tests/unit/`)

This directory contains fast, isolated unit tests validating individual deterministic functions, algorithms, and mathematical formulas.

---

## 1. File-by-File Breakdown

### `test_tolerance.py` — Engineering Safety Core Unit Tests (278 lines)
- **Purpose:** Exhaustively tests all 21 mechanical, metallurgical, and rotating equipment safety rules.
- **Covers:**
  - Exact match (`TIER_1_EXACT`).
  - Safe upgrades (`TIER_2_SUPERSET`): e.g. Class 600 replacing Class 300, ASTM A350 LF2 replacing A105.
  - Functional equivalents with warnings (`TIER_3_FUNCTIONAL_EQUIVALENT`): e.g. heavier pipe schedule.
  - Hard rejections (`TIER_4_INCOMPATIBLE`): e.g. non-NACE in sour service, RF bolted to cast iron FF, reduced bore on piggable lines, lower pressure class.

### `test_chemistry.py` — Metallurgical Chemistry Tests
- **Covers:**
  - Carbon Equivalent calculations ($CE_{IIW}$ and $P_{cm}$).
  - Weldability classification (Good, Fair, Poor).
  - Pitting Resistance Equivalent Number (PREN) for stainless and duplex steels.

### `test_logistics.py` — Logistics & Emissions Formulas
- **Covers:**
  - Haversine great-circle spherical distance.
  - Indian highway circuity factor ($1.25\times$).
  - Bureau of Energy Efficiency (BEE) freight carbon footprint formula ($62\text{ g } CO_2 / \text{tonne-km}$).

### `test_normalizer.py` — Unicode & Text Normalization Tests
- **Covers:**
  - Unicode NFKC decomposition.
  - Expansion of fractional symbols (½ $\rightarrow$ 1/2).
  - Dialect thesaurus substitutions.

### `test_ocr_and_mtc.py` — Vision & MTC Extraction Tests
- **Covers:**
  - PyMuPDF fast-path vector text extraction.
  - Image preprocessing (deskew, CLAHE, Otsu binarization).
  - EN 10204 Type 3.1 table parser for chemical heat analysis and tensile properties.

### `test_security.py` — Cryptographic Security Tests
- **Covers:**
  - SHA-256 hash chaining consistency.
  - Anti-tamper verification (proves that modifying any past row in the audit ledger invalidates downstream hashes).
  - HMAC-SHA256 digital gate pass seal computation.

---

## 2. Running Unit Tests

```bash
pytest tests/unit/ -v
```
