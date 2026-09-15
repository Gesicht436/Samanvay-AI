# Backend Application Package (`backend/app`)

## 1. Overview
The `backend/app` directory is the core Python package containing the business logic, API routers, domain contracts, machine learning models, and data persistence layers of Samanvay-AI.

---

## 2. Package Architecture and Request Lifecycle

When a request arrives at the FastAPI server, it traverses the application layers in a structured sequence:

```
                  Client HTTP Request (e.g. POST /api/v1/match/single)
                                      |
                                      v
                       [main.py: Lifespan & Routing]
                                      |
                                      v
                        [api/v1/match.py: Route Handler]
                                      |
       +------------------------------+-------------------------------+
       |                                                              |
       v                                                              v
[ml/ner_tagger.py]                                        [ml/vector_search.py]
Extracts size, pressure,                                  Retrieves top-K candidates
metallurgy, schedule, IBR                                 from Qdrant catalog
       |                                                              |
       +------------------------------+-------------------------------+
                                      |
                                      v
                    [matching/tolerance.py: Rule Engine]
              Applies deterministic ASME B16.5, ASTM, NACE,
              and IBR rules to categorize into Tier-1, 2, or 3
                                      |
                                      v
                 [matching/active_learning.py: Dynamic Reranker]
              Applies historical engineer verification boosts/demotions
                                      |
                                      v
                  [ingestion/storage.py & graph/queries.py]
              Saves audit records to PostgreSQL / links Neo4j graph
                                      |
                                      v
                    JSON Response returned to client
```

---

## 3. Subpackage Breakdown

### 1. `api/`
Handles HTTP communication, parameter validation, and dependency injection:
- `deps.py`: Manages database session lifecycles (`get_db`) and service handles.
- `v1/`: Version 1 API routers (`match.py`, `requisition.py`, `ingest.py`, `graph.py`, `audit.py`).

### 2. `contracts/`
Defines the Pydantic v2 schemas used across the system:
- `material.py`: `ExtractedMaterialAttributes`, `ItemType`, `FacingEnd`, `CanonicalMaterial`.
- `matching.py`: `MatchEvaluationResult`, `EquivalenceTier`, `ToleranceViolation`.
- `requisition.py`: `TransferRequisitionRequest`, `GatePassDetails`, `InventoryLock`.
- `taxonomy.py`: `TaxonomyMapping`, UNSPSC v26 and GeM schema contracts.

### 3. `matching/`
Houses the deterministic engineering tolerance engine:
- `tolerance.py`: Primary evaluation pipeline for candidate pools.
- `asme_rules.py`: Pressure class hierarchy (Class 150 to 2500) and ASTM metallurgy DAG.
- `piping_spec_rules.py`: Pipe schedules (B36.10M), NACE MR0175 sour service, B16.47 flange series, and IBR 1950 boiler rules.
- `rotating_rules.py`: Rules for Ex-d electric motors (IS/IEC 60079), mechanical seals (API 682), and bearings (ISO 15).
- `active_learning.py`: Online feedback cache and dynamic reranker.
- `logistics.py`: GIS multi-depot distance matrix, freight costs, and CISF gate pass generator.

### 4. `ml/`
Provides natural language processing and candidate retrieval:
- `ner_tagger.py`: Slot-filling parser for extracting specifications from CPSE descriptions.
- `vector_search.py`: Qdrant vector index search with fast in-memory fallback.
- `train_ner.py` / `train_biencoder.py`: Scripts for fine-tuning NLP models on CPSE catalogs.
- `model_weights/`: Directory storing transformer model checkpoints.

### 5. `ingestion/`
Responsible for document parsing and persistence:
- `ocr_engine.py`: High-performance OCR engine with native Windows Media OCR (`winocr`), PaddleOCR, and PDFPlumber.
- `certificate.py`: Parser for Mill Test Certificates (MTCs), extracting heat numbers and chemical analysis.
- `pdf_parser.py`: PDF document processing and table extraction.
- `storage.py`: SQLAlchemy database models, session management, and audit persistence.
- `data_pipeline/`: Utilities for streaming ERP catalogs and synthetic test data generation.

### 6. `graph/`
Manages the Neo4j knowledge graph ontology:
- `client.py`: Neo4j driver connection with automatic in-memory fallback.
- `queries.py`: Cypher queries for inventory discovery, taxonomic navigation, and SKU linkage.
- `seed_graph.py`: Script to populate the graph with 2,200 canonical items and 10,800 depot records.

### 7. Configuration (`config.py`)
Centralized settings management using `pydantic-settings`:
- Environment variables loaded automatically from `.env` or system environment.
- Configurable database connection strings, API prefixes, and server ports.
