# Machine Learning

All ML implementation lives in `machine_learning/`. NER training consumes the existing `data/ml_training/ner_train.jsonl`. Bi-encoder training consumes `biencoder_pairs.jsonl`, uses BAAI/bge-m3 and MultipleNegativesRankingLoss, then saves to `machine_learning/model_weights/bge_m3_cpes/`.

Qdrant stores 1024-dimensional cosine vectors in four named domains (`dim`, `met`, `pt`, `std`) for dimensional, metallurgy, pressure/temperature, and standards/procurement evidence. Canonical re-indexing populates a staging collection before swapping the configured collection alias. Heavy ML dependencies are optional so contract and rule tests can run without model downloads.

The compatibility reranker uses thirteen deterministic features, including separate dimension, metallurgy, pressure/temperature, and standards cosine scores. It falls back to a 50/50 blend of fused cosine similarity and structural compatibility when `machine_learning/model_weights/reranker.xgb` is absent. Build its training pairs with `python scripts/build_reranker_pairs.py`, then train it with `python -m machine_learning.reranker.train`. `python -m machine_learning.train_all --stage ner,biencoder,reranker` trains selected stages in NER, bi-encoder, reranker order.

NER and regex extraction cover 25 label groups, including BIS/IS, OISD, EIL, GeM, CPPP, and MESC identifiers. The in-memory active-learning queue uses uncertainty sampling and LRU eviction; feedback can be bootstrapped through `/v1/match/hitl-bootstrap` and is returned as query/candidate/cosine/label training examples. Deployments requiring feedback to survive process restarts should persist these examples in their application database.
