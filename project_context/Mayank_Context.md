# System Architecture, API Gateway & Tier Distribution Workflow

**Role:** Team Lead, System Architect & Tier Distribution Lead (Mayank Anand)

**Collaborators:**
* **Shaurya** (Collaborates with you on Qdrant Vector DB & assists on the Tier Distribution System)
* **Ranvijay** (Builds Next.js 16 frontend & document storage schema; you handle all connections)
* **Harsh** (Owns Neo4j; you consume his Cypher spare locator queries in the API Gateway)
* **Hariom** (Provides DeBERTa NER extracted attributes for your Tier Distribution engine)
* **Samriddih** (Provides OCR extracted document text for your `/ingest/document` route)

**Primary Directories:** `backend/app/api/`, `backend/app/contracts/`, `backend/app/matching/`

**Target Environment:** Python 3.14, FastAPI, Pydantic v2, SQLAlchemy, Docker Compose, PostgreSQL, Qdrant

---

### Objective & Architectural Role

As the Team Lead and System Architect, your mission is to unify all subsystems of **Samanvay-AI (BharatCodex)** into a high-performance, contract-first monorepo, and to lead the development of the **Tier Distribution System**:

1. **Contract-First Monorepo Architecture:** Establish strict Pydantic v2 schemas in `backend/app/contracts/` as the single source of truth across all modules.
2. **FastAPI Gateway & Universal Wiring:** Build all REST API routes (`/ingest`, `/match`, `/graph`) and manage all infrastructure connections (PostgreSQL engine sessions, Qdrant vector client with Shourya, and frontend-to-backend connectivity).
3. **Tier Distribution System Lead (with Shourya):** Build the deterministic validation engine (`backend/app/matching/tolerance.py` and `asme_rules.py`) that applies ASME B16.5 and ASTM engineering rules to classify matches into **Tier-1 (Identical)**, **Tier-2 (Substitute)**, and **Tier-3 (Incompatible)**.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        NEXT.JS 16 WEB PORTAL                           │
│               (Ranvijay: Deduplication Studio, HITL, Dashboard)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                              REST / JSON
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  MAYANK'S FASTAPI GATEWAY ENGINE                       │
│                       (`backend/app/api/v1/`)                          │
│                                                                        │
│  ┌───────────────────────┐ ┌───────────────────┐ ┌──────────────────┐  │
│  │   INGEST ROUTER       │ │   MATCH ROUTER    │ │   GRAPH ROUTER   │  │
│  │ (Samriddih OCR text & │ │ (Hariom NER &     │ │ (Harsh's Neo4j   │  │
│  │  Ranvijay Doc Storage)│ │  Shourya Vector)  │ │  Cypher Spares)  │  │
│  └───────────────────────┘ └─────────┬─────────┘ └──────────────────┘  │
│                                      │                                 │
│                                      ▼                                 │
│                   TIER DISTRIBUTION SYSTEM (Mayank & Shourya)          │
│                    • ASME B16.5 Dimensional & Pressure Checks          │
│                    • ASTM Metallurgy Compatibility Matrices            │
│                    • Categorize into Tier-1, Tier-2, Tier-3            │
└──────────────┬───────────────────────┬──────────────────────┬──────────┘
               │                       │                      │
               ▼                       ▼                      ▼
      ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
      │   POSTGRESQL    │    │      NEO4J       │    │     QDRANT      │
      │  (Audit/Auth/   │    │ (Taxonomy/Equiv. │    │ (Dense Vector   │
      │   Doc Staging)  │    │      Graph)      │    │  SKU Index)     │
      └─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

### Step-by-Step Implementation Guide

#### Step 1: Pydantic Data Contracts (`backend/app/contracts/`)
Create immutable schemas serving as the contract between all teammates:
* `material.py`: `ExtractedMaterialAttributes` (Item type, size NB mm, pressure class, metallurgy, facing, standard) and `CanonicalMaterial`.
* `matching.py`: `EquivalenceTier` enum (`TIER_1_IDENTICAL`, `TIER_2_SUBSTITUTE`, `TIER_3_INCOMPATIBLE`), `MatchCandidate`, `MatchResult`.
* `taxonomy.py`: `UNSPSCCommodity`, `GeMCategory`.

#### Step 2: Tier Distribution System (`backend/app/matching/`) (with Shourya)
Translate ASME B16.5 and ASTM alloy standards into vectorized Python checks:
* **Rule 1 (Size Invariant):** If `candidate.size_nb_mm != source.size_nb_mm` $\rightarrow$ Hard Reject (`TIER_3_INCOMPATIBLE`).
* **Rule 2 (Pressure Class):** Down-rating is strictly forbidden (e.g. Class 150 cannot replace Class 300 $\rightarrow$ `TIER_3`). Up-rating is permitted if facing and bolt circles match (e.g. Class 600 replacing Class 300 $\rightarrow$ `TIER_2_SUBSTITUTE`).
* **Rule 3 (Metallurgy Compatibility):** Carbon Steel A105 $\rightarrow$ Stainless SS316 is a safe upgrade (`TIER_2`), but SS316 $\rightarrow$ A105 is a dangerous downgrade (`TIER_3`). Low-temp A350 LF2 requires impact-tested steel; standard A105 is rejected.
* **Rule 4 (Facing & End Connection):** Raised Face (RF) $\neq$ Ring Type Joint (RTJ).

```python
# backend/app/matching/tolerance.py
def evaluate_compatibility(source: ExtractedMaterialAttributes, candidate: ExtractedMaterialAttributes) -> MatchEvaluationResult:
    # 1. Hard physical size check
    if source.size_nb_mm != candidate.size_nb_mm:
        return MatchEvaluationResult(tier=EquivalenceTier.TIER_3_INCOMPATIBLE, rationale="Nominal bore size mismatch.")

    # 2. Pressure class check
    if candidate.pressure_class < source.pressure_class:
        return MatchEvaluationResult(tier=EquivalenceTier.TIER_3_INCOMPATIBLE, rationale="Pressure down-rating is unsafe.")

    # 3. Metallurgy check
    if not is_metallurgy_compatible(source.metallurgy, candidate.metallurgy):
        return MatchEvaluationResult(tier=EquivalenceTier.TIER_3_INCOMPATIBLE, rationale="Metallurgy incompatible.")

    # 4. Parity check
    if candidate == source:
        return MatchEvaluationResult(tier=EquivalenceTier.TIER_1_IDENTICAL, rationale="100% specification parity.")
    return MatchEvaluationResult(tier=EquivalenceTier.TIER_2_SUBSTITUTE, rationale="Functional upgrade meeting or exceeding specifications.")
```

#### Step 3: FastAPI Gateway Routes (`backend/app/api/v1/`)
* **`POST /api/v1/ingest/upload`**: Ingests catalog spreadsheets (using Shaurya's `loader.py`) or PDFs (using Samriddih's `process_document()`).
* **`GET /api/v1/match/hitl-queue`**: Returns pending matches with confidence between $70\%$ and $90\%$ or Tier-2 substitutes for human review.
* **`POST /api/v1/match/hitl-resolve`**: Receives procurement officer's approval/rejection and invokes Harsh's `link_reconciled_sku()` to update Neo4j.
* **`GET /api/v1/graph/spares/{sku_code}`**: Invokes Harsh's `find_inter_cpse_spares()` to locate nearest idle spares for Ranvijay's dashboard.

#### Step 4: System Integration & Wiring
* Provide database sessions (`deps.py`) using SQLAlchemy connection pooling for PostgreSQL.
* Pair with Shourya to connect the Qdrant vector client.
* Configure CORS middleware in `main.py` to allow Ranvijay's Next.js app (`localhost:3000`).

---

### File Deliverables & Directory Layout

```
backend/app/
├── contracts/                # Pydantic v2 schemas
│   ├── material.py
│   ├── matching.py
│   └── taxonomy.py
├── matching/                 # Tier Distribution System (with Shourya)
│   ├── asme_rules.py         # ASME & ASTM tolerance matrices
│   └── tolerance.py          # Deterministic invariant check & tier assignment
├── api/
│   ├── deps.py               # DB session & service dependency injection
│   └── v1/
│       ├── ingest.py         # Document & catalog intake endpoints
│       ├── match.py          # Matching, deduplication & HITL triage
│       └── graph.py          # Knowledge graph visualizer data endpoints
├── main.py                   # FastAPI app entry point & CORS
└── config.py                 # Pydantic Settings & environment variables
```

---

### Team Collaboration & Handoffs
1. **With Shourya:** You collaborate on Qdrant vector setup and pair to build and verify the Tier Distribution System rules.
2. **With Ranvijay:** Ranvijay builds the UI; you provide the backend endpoints, data contracts, and handle all connections.
3. **With Harsh:** You integrate Harsh's Neo4j queries into the API gateway for spare part discovery and link persistence.
4. **With Hariom & Samriddih:** You expose their OCR and NER capabilities to the API and feed their outputs into the Tier Distribution engine.
