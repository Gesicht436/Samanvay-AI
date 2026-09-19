# Machine Learning & NLP Test Suite (`tests/ml/`)

This directory validates natural language processing, dialect normalization, and named entity recognition models.

---

## 1. File Breakdown

### `test_ner.py` — Dialect Normalizer & Slot Tagger Tests
- **Purpose:** Verifies that non-standard industrial jargon and abbreviated descriptions are accurately normalized and parsed into structured physical attributes.
- **Key Tests:**
  - `test_dialect_normalization()`: Verifies expansion of abbreviations across IOCL, ONGC, and metric styles (e.g. `"VLV"` $\rightarrow$ `"VALVE"`, `"300#"` $\rightarrow$ `"CLASS 300"`, `"CS"` $\rightarrow$ `"CARBON STEEL"`).
  - `test_slot_extraction()`: Evaluates `SlotTagger` extraction on complex descriptions, verifying precision on `item_type`, `size`, `pressure_class`, `material_grade`, `schedule`, and `trim`.

---

## 2. Running ML Tests

```bash
pytest tests/ml/ -v
```
