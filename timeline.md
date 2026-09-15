# ⏱️ Samanvay-AI (BharatCodex) — Master Project Timeline & Deadlines

> **Operating Principle:** No member should ever be blocked. Each milestone defines an explicit **Owner**, **Collaborators**, **Exact Inputs**, **Concrete Deliverable (Code/File)**, and the **Downstream Teammate** waiting for that deliverable.

---

## ️ Chronological Dependency Flow

```
[Phase 0: Scaffolding]
  Mayank (Contracts & Docker) ──► Ranvijay (Frontend Shell) & Shaurya (Data Check)
         │
         ▼
[Phase 1: Ingestion & Feature Engineering]
  Samriddih (Dual-Path OCR) ──► Ranvijay (Postgres Doc Storage)
  Hariom (Feature Normalizer & NER) ──► Shourya (BGE-M3 Fine-Tuning)
  Harsh (Neo4j Setup & Constraints)
         │
         ▼
[Phase 2: Matching, Safety Rules & API Gateway]
  Mayank & Shourya (ASME Tier Distribution Engine)
  Shourya & Mayank (Qdrant Vector Search Index)
  Harsh (Cypher Cross-CPSE Spare Locator)
  Mayank (FastAPI Gateway Endpoints) ──► Ranvijay (Frontend UI Views)
         │
         ▼
[Phase 3: End-to-End System Wiring & Benchmark]
  Mayank & Ranvijay (Wire UI to Live API)
  Shaurya (150-Case Golden Benchmark Suite)
  Hariom & Shourya (Extraction & Search Evaluation)
         │
         ▼
[Phase 4: Polish, Stress-Test & Pitch Rehearsal]
  Ranvijay (UI Polish & Animations)
  Mayank (Zero-Crash Verification & Demo Startup)
  Whole Team (Pitch Deck Rehearsal with SIH_Presentation.pptx)
```

---

##  Milestone Breakdown & Specific Deadlines

---

### Phase 0: Infrastructure, Contracts & Project Scaffolding
**Time Window:** **Hour 00:00 – Hour 02:00**  
**Goal:** Establish shared data schemas, repository skeleton, and containerized services so all teammates can work in parallel without merge conflicts.

| Time | Task & Owner | Collaborator(s) | Description | Concrete Deliverable | Downstream Dependency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T+01:00** | **Data Contracts**<br>`Mayank` | *Solo* | Define immutable Pydantic v2 schemas for extracted materials, equivalence tiers, and taxonomy categories. | [`backend/app/contracts/material.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/contracts/material.py)<br>[`backend/app/contracts/matching.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/contracts/matching.py) | **Hariom, Harsh, Ranvijay** need these schemas to type their inputs/outputs. |
| **T+01:30** | **Container Stack**<br>`Mayank` | *Harsh, Shourya* | Configure Docker Compose for PostgreSQL, Neo4j, and Qdrant. Provide base FastAPI app with CORS. | `docker-compose.yml`<br>[`backend/app/main.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/main.py) | **Harsh** (Neo4j), **Shourya** (Qdrant), **Ranvijay** (Postgres). |
| **T+02:00** | **UI Shell & Types**<br>`Ranvijay` | `Mayank` | Scaffold Next.js 16 app with `shadcn/ui`, persistent enterprise sidebar, and TypeScript types matching Mayank's Pydantic models. | `frontend/src/lib/types.ts`<br>`frontend/src/app/layout.tsx` | Unblocks independent UI development using mock data. |

---

### Phase 1: Intake, OCR Ingestion & Feature Engineering
**Time Window:** **Hour 02:00 – Hour 06:00**  
**Goal:** Ingest messy documents, normalize technical units, seed the graph taxonomy, and train base models.

| Time | Task & Owner | Collaborator(s) | Description | Concrete Deliverable | Downstream Dependency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T+03:30** | **Dual-Path OCR Engine**<br>`Samriddih` | *Solo* | Build PyMuPDF fast path ($<50\text{ ms}$) for digital PDFs and PaddleOCR PP-OCRv4 with auto-rotation for scanned certificates. | [`backend/app/ingestion/pdf_parser.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/ingestion/pdf_parser.py)<br>[`backend/app/ingestion/ocr_engine.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/ingestion/ocr_engine.py) | **Ranvijay** (receives text to save); **Hariom** (receives text to parse). |
| **T+04:15** | **PostgreSQL Document Storage**<br>`Ranvijay` | `Samriddih`, `Mayank` | Implement SQLAlchemy schema `IngestedDocument` and save function. Mayank wires the DB session dependency. | `backend/app/ingestion/storage.py` | Stores uploaded certificates and raw text for audit logging. |
| **T+04:45** | **Feature Engineering & Normalization**<br>`Hariom` | *Solo* | Build regex unit standardizers: convert inches/DN to metric mm float (`100.0`), strip `#`/`CLASS` to integer (`300`), map alloy abbreviations. | [`backend/app/ml/ner_tagger.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/ml/ner_tagger.py) (`extract_attributes()`) | **Mayank & Shourya** (Tier Distribution System receives normalized specs). |
| **T+05:30** | **Bi-Encoder Contrastive Training**<br>`Shourya` | `Hariom` | Fine-tune `BAAI/bge-m3` on [`data/ml_training/biencoder_pairs.jsonl`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/ml_training/biencoder_pairs.jsonl) using `MultipleNegativesRankingLoss`. | `backend/app/ml/train_biencoder.py`<br>`backend/app/ml/model_weights/bge_m3_cpes/` | Generates 1024-d embeddings for Qdrant index search. |
| **T+06:00** | **Neo4j Constraints & Seeding**<br>`Harsh` | `Shaurya` | Seed Neo4j with [`unspsc_v26.csv`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/taxonomies/unspsc_v26.csv), [`gem_categories.csv`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/taxonomies/gem_categories.csv), and [`canonical_master.csv`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/taxonomies/canonical_master.csv). Set unique constraints. | [`backend/app/graph/seed_graph.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/graph/seed_graph.py)<br>[`backend/app/graph/client.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/graph/client.py) | **Harsh** can now run Cypher queries against populated graph nodes. |

---

### Phase 2: Search, Safety Rules, Graph Traversal & API Gateway
**Time Window:** **Hour 06:00 – Hour 12:00**  
**Goal:** Implement the deterministic ASME safety checks, vector retrieval, cross-depot Cypher queries, and expose full REST routes.

| Time | Task & Owner | Collaborator(s) | Description | Concrete Deliverable | Downstream Dependency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T+07:30** | **Qdrant Vector Index**<br>`Shourya & Mayank` | *Pair* | Connect to Qdrant, embed 2,200 canonical master items using BGE-M3, and expose sub-15ms candidate retrieval. | [`backend/app/ml/vector_search.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/ml/vector_search.py) (`get_candidate_skus()`) | Feeds top-10 candidate pool into Tier Distribution System. |
| **T+08:30** | **Tier Distribution System**<br>`Mayank` | `Shourya` | Implement deterministic ASME B16.5 & ASTM alloy tolerance engine. Strict size checking, pressure down-rating block, tier assignment. | [`backend/app/matching/tolerance.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/matching/tolerance.py)<br>[`backend/app/matching/asme_rules.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/matching/asme_rules.py) | Categorizes matches into Tier-1 (Exact), Tier-2 (Upgrade), Tier-3 (Reject). |
| **T+09:15** | **Cross-CPSE Spare Locator Queries**<br>`Harsh` | *Solo* | Write optimized Cypher queries finding matching idle stock across sister depots (IOCL $\leftrightarrow$ ONGC $\leftrightarrow$ BPCL) and link reconciled SKUs. | [`backend/app/graph/queries.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/graph/queries.py) (`find_inter_cpse_spares()`, `link_reconciled_sku()`) | **Mayank's** API router consumes these queries. |
| **T+10:00** | **Batch Catalog Ingestion Loader**<br>`Shaurya` | `Mayank` | Implement format-agnostic streaming reader (`polars`/`pandas`) for CSV/Excel with column header auto-normalizer. | `backend/app/ingestion/data_pipeline/loader.py` | **Mayank's** `POST /api/v1/ingest/upload` endpoint streams large catalog files. |
| **T+11:00** | **Frontend Core Pages (Mock Data)**<br>`Ranvijay` | *Solo* | Complete Deduplication Studio (`/deduplication`), HITL Triage Queue (`/hitl`), and Analytics Dashboard (`/dashboard`) using `mockData.ts`. | `frontend/src/app/deduplication/page.tsx`<br>`frontend/src/app/hitl/page.tsx`<br>`frontend/src/app/dashboard/page.tsx` | UI is visually complete and ready to connect to live backend. |
| **T+12:00** | **FastAPI Gateway Endpoints**<br>`Mayank` | `Harsh, Ranvijay` | Build and test all REST routes: `/ingest/upload`, `/match/hitl-queue`, `/match/hitl-resolve`, `/graph/spares/{sku_code}`. | [`backend/app/api/v1/ingest.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/v1/ingest.py)<br>[`backend/app/api/v1/match.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/v1/match.py)<br>[`backend/app/api/v1/graph.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/v1/graph.py) | Live Swagger API docs at `http://localhost:8000/docs`. |

---

### Phase 3: End-to-End System Integration & Benchmarking
**Time Window:** **Hour 12:00 – Hour 18:00**  
**Goal:** Wire frontend to live backend APIs, replace mock data, run golden benchmarks, and verify cross-depot spare transfers.

| Time | Task & Owner | Collaborator(s) | Description | Concrete Deliverable | Downstream Dependency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T+14:00** | **Live Frontend-to-Backend Wiring**<br>`Mayank & Ranvijay` | *Pair* | Connect `frontend/src/lib/api.ts` to live FastAPI endpoints. Test live batch upload and 1-click HITL approvals with real database persistence. | `frontend/src/lib/api.ts`<br>Verified live communication | Real data flows from Next.js $\rightarrow$ FastAPI $\rightarrow$ Postgres/Neo4j. |
| **T+15:30** | **Golden Benchmark Suite**<br>`Shaurya` | `Mayank` | Curate 150–200 edge cases (50 Tier-1 duplicates, 50 Tier-2 valid upgrades, 50 Tier-3 hard safety traps). Run automated validation script. | `data/evaluation/benchmark_test_cases.json`<br>`data/evaluation/run_benchmark.py` | Proves system accuracy (100% precision on safety invariants) to judges. |
| **T+16:30** | **Token Extraction Fine-Tuning**<br>`Hariom` | `Shourya` | Finalize DeBERTa-v3 token classifier on 5,000 NER samples and benchmark F1 score across the 6 entity types. | `backend/app/ml/train_ner.py`<br>`backend/app/ml/model_weights/ner_deberta/` | Production weights for token extraction. |
| **T+17:30** | **Cross-Depot Verification**<br>`Harsh` | `Mayank, Ranvijay` | Test live spare location: upload an IOCL requirement and verify that ONGC Hazira surplus spares appear on Ranvijay's dashboard table. | End-to-end traversal test script in `backend/app/graph/test_queries.py` | Validates the primary business KPI for presentation. |

---

### Phase 4: Polish, Stress-Testing & Live Pitch Readiness
**Time Window:** **Hour 18:00 – Hour 24:00**  
**Goal:** Polish UI visuals, ensure lightning latency ($<200\text{ ms}$), eliminate all crash risks, and rehearse the presentation.

| Time | Task & Owner | Collaborator(s) | Description | Concrete Deliverable | Downstream Dependency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T+19:30** | **UI Visual Polish & Badges**<br>`Ranvijay` | *Solo* | Add color-coded confidence badges (Green for Tier-1, Amber for Tier-2, Red for Tier-3), smooth progress bar animations, and dark/light mode toggle. | Polished Next.js frontend pages | Visually stunning UI for live evaluator inspection. |
| **T+21:00** | **Zero-Crash & Latency Audit**<br>`Mayank` | `Shourya, Harsh` | Test full pipeline latency ($<200\text{ ms}$). Ensure offline fallback to `mockData.ts` works if any container disconnects. | One-click launch script (`docker compose up` / `run_demo.bat`) | Eliminates live-demo panic. |
| **T+22:30** | **Slide Deck Alignment**<br>`Mayank` | `Team` | Verify that every statistic in [`SIH_Presentation.pptx`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/SIH_Presentation.pptx) and [`stage_diagram.png`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/stage_diagram.png) exactly matches live demo capabilities. | Aligned presentation deck & demo script | Complete alignment between slides and software. |
| **T+24:00** | **Full Team Pitch Rehearsal**<br>`Whole Team` | *All* | Dry run the 5-minute presentation: 30 seconds per slide, live 2-minute product demo on Next.js, and Q&A handling. | **Demo-Ready Team & Product**  | **Victory at Smart India Hackathon!** |

---

##  Deliverable Checklist Per Person

### Mayank Anand (Team Lead & Tier Distribution Lead)
- [ ] [`backend/app/contracts/material.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/contracts/material.py) & [`matching.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/contracts/matching.py) (Pydantic v2 schemas)
- [ ] `docker-compose.yml` (Postgres, Qdrant, Neo4j, backend)
- [ ] [`backend/app/matching/tolerance.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/matching/tolerance.py) (ASME/ASTM tolerance engine with Shaurya)
- [ ] [`backend/app/api/v1/`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/v1/) (`ingest.py`, `match.py`, `graph.py` REST routes)
- [ ] Universal wiring: Postgres DB sessions, Qdrant vector client, Next.js CORS

### Samriddih (Document Intelligence Lead)
- [ ] [`backend/app/ingestion/ocr_engine.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/ingestion/ocr_engine.py) (PaddleOCR PP-OCRv4 wrapper with angle correction)
- [ ] [`backend/app/ingestion/pdf_parser.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/ingestion/pdf_parser.py) (Dual-path PyMuPDF/OCR router)
- [ ] [`backend/app/ingestion/certificate.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/ingestion/certificate.py) (EN 10204 3.1 MTC layout parser)
- [ ] Integration with Ranvijay's `storage.py` to persist extracted documents into PostgreSQL

### Ranvijay (Frontend & Document Database Lead)
- [ ] `backend/app/ingestion/storage.py` (SQLAlchemy `IngestedDocument` table model)
- [ ] `frontend/src/app/deduplication/page.tsx` (Batch catalog drag-and-drop studio)
- [ ] `frontend/src/app/hitl/page.tsx` (Side-by-side HITL verification card with 1-click approvals)
- [ ] `frontend/src/app/dashboard/page.tsx` (Procurement analytics & cross-CPSE spare locator)
- [ ] `frontend/src/lib/api.ts` (API client with seamless offline fallback to `mockData.ts`)

### Hariom (Machine Learning Lead)
- [ ] [`backend/app/ml/ner_tagger.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/ml/ner_tagger.py) (`extract_attributes()` unit normalizer & regex fallback)
- [ ] `backend/app/ml/train_ner.py` (DeBERTa-v3 token classifier training script)
- [ ] `backend/app/ml/model_weights/ner_deberta/` (Saved model checkpoint)
- [ ] Validated Pydantic output (`ExtractedMaterialAttributes`) passed to Mayank's Tier engine

### Shaurya (Semantic Matching, Data & Float Lead)
- [ ] `backend/app/ml/train_biencoder.py` (BGE-M3 contrastive fine-tuning on 8k pairs)
- [ ] `backend/app/ml/vector_search.py` (Qdrant client & sub-15ms search with Mayank)
- [ ] [`backend/app/matching/asme_rules.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/matching/asme_rules.py) (ASME/ASTM tolerance rules assistance with Mayank)
- [ ] `backend/app/ingestion/data_pipeline/loader.py` (Batch CSV/Excel streaming parser)
- [ ] `data/evaluation/benchmark_test_cases.json` (150-case golden evaluation benchmark)

### Harsh (Knowledge Graph Lead)
- [ ] [`backend/app/graph/client.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/graph/client.py) (Neo4j Bolt driver initialization & connection pooling)
- [ ] [`backend/app/graph/seed_graph.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/graph/seed_graph.py) (Automated taxonomy & catalog graph loader)
- [ ] [`backend/app/graph/queries.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/graph/queries.py) (`find_inter_cpse_spares()` cross-depot Cypher query)
- [ ] Reconciled SKU relationship writer (`link_reconciled_sku()` with audit timestamp)
