# Machine Learning Training Datasets

The `data/ml_training` directory contains serialized, high-quality labeled training corpora used for fine-tuning Samanvay-AI's neural models.

---

## Dataset Inventory

### 1. `biencoder_pairs.jsonl` (Contrastive Bi-Encoder Dataset)
- **Record Count**: 8,000 paired material samples.
- **Objective**: MultipleNegativesRankingLoss (MNRL) contrastive fine-tuning of multilingual dense encoders (`BGE-M3`).
- **Format**: JSON Lines (`jsonl`).
- **Schema**:
  ```json
  {
    "canonical_id": "CANON-FLG-WN-0012",
    "anchor": "FLG WNRF 4IN 300# A105 SCH 40",
    "positive": "4 INCH CLASS 300 WELD NECK RAISED FACE FLANGE ASTM A105"
  }
  ```
- **Leak-Safe Splitting**: Structured by unique `canonical_id` partitions in `machine_learning/train_biencoder.py` to ensure zero identity leakage between training and validation folds.

### 2. `ner_train.jsonl` (DeBERTa Token Classification Dataset)
- **Record Count**: 5,000 annotated tender and catalog descriptions.
- **Objective**: Character-level offset sequence labeling for 18 named entity classes.
- **Format**: JSON Lines (`jsonl`).
- **Schema**:
  ```json
  {
    "text": "GATE VALVE 2IN 150# A216 WCB RF FLANGED IS 1239",
    "entities": [
      {"start": 0, "end": 10, "label": "ITEM_TYPE"},
      {"start": 11, "end": 14, "label": "SIZE"},
      {"start": 15, "end": 19, "label": "PRESSURE_RATING"},
      {"start": 20, "end": 28, "label": "METALLURGY"},
      {"start": 29, "end": 31, "label": "FACING_END"},
      {"start": 40, "end": 47, "label": "INDIAN_STANDARD"}
    ]
  }
  ```
- **Annotation Consistency**: Conforms to standard `B-` (Beginning) and `I-` (Inside) BIO chunking via `machine_learning/train_ner.py`.
