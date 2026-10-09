# Machine Learning Techniques

This is the dedicated ML technique area for Samanvay-AI. All ML implementation and technique notes live here; the backend API imports this package without duplicating ML code.

## Two-stage flow

```text
raw procurement text
        |---------------- NER tagger ----------------> ExtractedMaterialAttributes
        |                                               |
        |---------------- BGE-M3 encoder --------------> Qdrant candidate pool
                                                        |
                                                        v
                                             backend/app/matching/
```

## Techniques

| Stage | Technique | Implementation | Output |
| --- | --- | --- | --- |
| Attribute extraction | DeBERTa-v3-small token classification with BIO labels | `machine_learning/train_ner.py` and `ner_tagger.py` | normalized material attributes |
| Semantic retrieval | BGE-M3 bi-encoder with MultipleNegativesRankingLoss | `machine_learning/train_biencoder.py` | 1024-dim embeddings |
| Candidate index | Qdrant HNSW cosine search | `machine_learning/vector_search.py` | candidates above 0.70 similarity |

## Commands

Run from the repository root after installing the ML extra:

```powershell
pip install -e ".[ml,dev]"
python -c "from machine_learning.train_ner import train_ner; train_ner()"
python -c "from machine_learning.train_biencoder import train; train()"
```

Model weights are intentionally ignored by Git and are saved under `machine_learning/model_weights/`.