# ML Runbook

1. Confirm `data/ml_training/ner_train.jsonl`, `biencoder_pairs.jsonl`, and `data/taxonomies/canonical_master.csv` are present.
2. Install `.[ml,dev]` with Python 3.11 or 3.12.
3. Train NER. The loader uses character offsets and emits BIO labels for `ITEM_TYPE`, `SIZE`, `PRESSURE_RATING`, `METALLURGY`, `FACING_END`, and `STANDARD`.
4. Train BGE-M3 using in-batch negatives; held-out records are grouped by `canonical_id` to prevent identity leakage.
5. Start Qdrant with `docker compose -f deployment/docker-compose.yml up -d qdrant`.
6. Load the canonical CSV with `machine_learning.vector_search.index_canonical_master(...)`; it indexes into a staging collection and atomically swaps the configured Qdrant alias after the staging index is ready.
7. Call `machine_learning.ner_tagger.extract_attributes(...)` and `VectorSearcher.get_candidate_skus(...)` from the API pipeline.

The regex normalization layer is always applied, even when a fine-tuned NER model is available. This keeps units, pressure classes, abbreviations, and material grades deterministic at the contract boundary.