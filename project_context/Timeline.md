# ⏱️ Samanvay-AI (BharatCodex) — Master Project Timeline & Deadlines

> **Quick Link:** See root [`timeline.md`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/timeline.md) for the full master version.

---

## 🗺️ Chronological Dependency Flow

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

## 📅 Milestone Breakdown & Specific Deadlines

### Phase 0: Infrastructure & Scaffolding (Hours 00:00 – 02:00)
* **T+01:00 (Mayank):** Data Contracts in [`backend/app/contracts/material.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/contracts/material.py) and [`matching.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/contracts/matching.py).
* **T+01:30 (Mayank):** Docker Compose stack (`docker-compose.yml`) + base FastAPI app (`backend/app/main.py`).
* **T+02:00 (Ranvijay):** Next.js 16 app shell with `shadcn/ui`, persistent enterprise sidebar, and TypeScript types in `frontend/src/lib/types.ts`.

### Phase 1: Ingestion & Feature Engineering (Hours 02:00 – 06:00)
* **T+03:30 (Samriddih):** Dual-path parser (`pdf_parser.py`: PyMuPDF fast path) and PaddleOCR wrapper (`ocr_engine.py`) with auto-angle rotation.
* **T+04:15 (Ranvijay & Samriddih):** PostgreSQL document storage (`backend/app/ingestion/storage.py`) for ingested PDFs and MTC metadata.
* **T+04:45 (Hariom):** Feature engineering & unit normalization pipeline (`backend/app/ml/ner_tagger.py`) converting inches/DN to metric mm and cleaning pressure ratings.
* **T+05:30 (Shourya):** Fine-tune BGE-M3 bi-encoder (`backend/app/ml/train_biencoder.py`) on 8,000 contrastive pairs.
* **T+06:00 (Harsh):** Neo4j container setup, unique constraints, and automated seeding script (`seed_graph.py`).

### Phase 2: Matching, Safety Rules & API Gateway (Hours 06:00 – 12:00)
* **T+07:30 (Shourya & Mayank):** Seed Qdrant vector collection (`canonical_materials`) and implement `<15ms` search in `backend/app/ml/vector_search.py`.
* **T+08:30 (Mayank & Shourya):** Build **Tier Distribution System** in `backend/app/matching/tolerance.py` & `asme_rules.py` (ASME B16.5 & ASTM alloy checks).
* **T+09:15 (Harsh):** Cypher cross-CPSE spare locator query (`queries.py`: `find_inter_cpse_spares()`) and reconciliation link writer.
* **T+10:00 (Shaurya):** Batch catalog streaming parser (`backend/app/ingestion/data_pipeline/loader.py`) with column header auto-normalizer.
* **T+11:00 (Ranvijay):** Complete frontend pages using mock data: Deduplication Studio (`/deduplication`), HITL Review Queue (`/hitl`), and Analytics Dashboard (`/dashboard`).
* **T+12:00 (Mayank):** FastAPI REST routes live at `/api/v1/ingest`, `/api/v1/match`, `/api/v1/graph`.

### Phase 3: End-to-End System Wiring & Benchmark (Hours 12:00 – 18:00)
* **T+14:00 (Mayank & Ranvijay):** Wire `frontend/src/lib/api.ts` to live FastAPI endpoints. Test live batch upload and 1-click approvals.
* **T+15:30 (Shaurya):** Curate 150-case Golden Benchmark Suite (`data/evaluation/benchmark_test_cases.json`) and run automated accuracy tests.
* **T+16:30 (Hariom):** Finalize DeBERTa-v3 token classifier on 5k NER samples (`backend/app/ml/train_ner.py`).
* **T+17:30 (Harsh & Mayank):** Validate cross-CPSE spare locator queries with live depot data (e.g. ONGC Hazira surplus for IOCL Panipat).

### Phase 4: Polish, Stress-Testing & Live Pitch Readiness (Hours 18:00 – 24:00)
* **T+19:30 (Ranvijay):** UI visual polish: green/amber confidence badges, smooth progress bars, dark/light mode toggle.
* **T+21:00 (Mayank & Team):** Latency audit ($<200\text{ ms}$) and zero-crash verification with offline fallback.
* **T+22:30 (Mayank):** Align live demo features with [`SIH_Presentation.pptx`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/SIH_Presentation.pptx) and [`stage_diagram.png`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/stage_diagram.png).
* **T+24:00 (Whole Team):** Dry run pitch rehearsal: 30 seconds per slide, 2-minute live demo, and evaluator Q&A.
