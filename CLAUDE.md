# CLAUDE.md - Samanvay-AI Architecture & Token-Optimized Developer Guide

> **Target Audience:** Anthropic Claude models (Claude 3.5 Sonnet, Claude 3.7 Sonnet, Claude 3 Opus) acting as senior staff engineer and pair programmer on Samanvay-AI.
> **Design Goal:** Provide maximum contextual grounding (problem statement, national domain context, architecture, invariants, file registry) while eliminating token waste so Claude can independently diagnose problems, propose optimal solutions, and build new features.

---

## 1. Claude Operating & Token-Minimization Directives

When interacting with this codebase, **Claude MUST adhere to these rules**:
1. **Omit Conversational Preamble:** Begin immediately with the diagnosis, code diff, or architectural plan. Never output filler ("Sure! I'd be happy to help", "Here is the refactored code:").
2. **Surgical Diffs Over File Dumps:** Never reprint untouched 400-line files. Use unified diff format (`diff -u`) or targeted replacement snippets referencing exact file paths and line anchors.
3. **Problem Identification Protocol:** When tasked with analyzing or optimizing code:
   - First, understand the module's exact role in the cross-CPSE workflow and respect its safety/security invariants.
   - Second, systematically identify defects, performance bottlenecks, race conditions, memory leaks, or architectural anti-patterns.
   - Third, formulate the optimal solution with trade-offs clearly articulated in 2-3 bullet points.
   - Fourth, provide precise, production-grade implementation code.
4. **Preserve Domain Integrity:** Preserve codified engineering standards (ASME, ASTM, API, NACE, TEMA), docstrings, and statutory compliance checks unless explicitly instructed otherwise.

---

## 2. Problem Statement & National Domain Context

### The Real-World Crisis
India's 7 major public sector oil, gas, and petrochemical enterprises (**OIL, IOCL, ONGC, BPCL, HPCL, GAIL, NRL**) operate under the Ministry of Petroleum & Natural Gas (**MoPNG | Smart India Hackathon SIH26099**).
- **Capital Blockage:** These 7 CPSEs collectively hold over **₹15,000–18,000 Crore** in maintenance, repair, and overhaul (MRO) spare parts sitting idle in central stores and refinery yards.
- **Downtime Costs:** Unplanned refinery shutdowns, offshore rig trips, or gas compressor failures cost Indian PSUs **₹5–20 Crore per day**.
- **Supply Chain Lead Times:** Emergency procurement from overseas OEMs (e.g. specialized API 6D valves, alloy heat exchanger tubes, cryogenic pumps) takes **6 to 18 months**, resulting in prolonged unit outages even while identical or superior spares sit unused at a neighbouring CPSE facility 150 km away.

### Why CPSEs Could Not Share Spares Previously (The 4 Barriers)
1. **Catalog Babel (Semantic Disconnect):** Each CPSE maintains independent, legacy ERP instances (SAP S/4HANA, Oracle ERP, IBM Maximo). Descriptions are inconsistent, heavily abbreviated, and dialect-laden (e.g. `VLV GT 4" 300# A105 RF TRIM 8` vs `VALVE, GATE, 100MM, CL300, CS, FLGD`). There is no unified national material taxonomy.
2. **Zero Risk Tolerance & Life-Safety Hazards:** Hydrocarbon processing involves extreme pressures (up to 2,500# / 420 bar), cryogenic LNG ($-162^\circ\text{C}$), high-temperature creep ($>500^\circ\text{C}$), and toxic sour gas ($H_2S$). A single mismatched flange, an un-annealed U-tube, an incompatible valve trim, or a non-NACE alloy causes catastrophic pipeline rupture, fatal gas leaks, or refinery explosions. **Probabilistic AI alone cannot be trusted with life-safety decisions.**
3. **Multi-Tenant Trust, Governance & Procurement Law:** Public sector enterprises are governed by strict oversight (Central Vigilance Commission [CVC], Comptroller and Auditor General [CAG], DPIIT Public Procurement Orders, GeM mandates). CPSEs cannot simply "lend" components without cryptographic custody transfer, tamper-evident audit trails, strict segregation of duties (preventing self-dealing/unauthorized surplus release), and physical gate security verification (CISF).
4. **Logistics & Decarbonization:** Moving heavy industrial equipment across India requires real-time routing over complex highway networks with road tortuosity ($1.28\times$), transit hour estimates, and Bureau of Energy Efficiency (BEE) freight carbon footprint accounting.

### How Samanvay-AI Solves the Problem
Samanvay-AI is a sovereign, multi-tenant mutual aid mesh that enables cross-CPSE spare parts interoperability through:
1. **Intelligent MTC & Catalog Intake:** Dual-path OCR extracting chemical and mechanical test data from EN 10204 3.1/3.2 certificates in $<50$ms.
2. **CPSE Dialect Normalization & Dense Vector Retrieval:** Normalizing 40+ enterprise dialects into canonical engineering schemas and indexing via 1024-dim dense embeddings in Qdrant.
3. **Deterministic Engineering Safety Core:** 21 codified mechanical and metallurgical engineering standards that hold unilateral veto power over AI recommendations.
4. **Dynamic Tri-Tier Compatibility Scoring:** Real-time compatibility evaluation $S(Q, C)$ relative to a specific target demand query, completely eliminating static, pre-baked tier classifications.
5. **Multi-Tenant Consignment Isolation & Cryptographic SoD:** Role-based access control where requesters only see their own demands and incoming depot requests, requesters are blocked from self-approving release, and supplying CPSE Materials Managers authorize surplus dispatch.
6. **Air-Gapped Offline Digital Gate Pass:** CISF security officers verify dispatches using SHA-256 HMAC digital seals and inline SVG QR codes without requiring external internet connectivity.
7. **Sovereign Audit Ledger:** Chained cryptographic blocks ($H_i = \text{SHA256}(H_{i-1} \parallel \text{fields})$) ensuring statutory compliance for CVC/CAG inquiries.
8. **Logistics & Decarbonization Star Graph:** Neo4j 5.20 knowledge graph modeling 19 CPSE refinery depots across India, calculating Haversine distance, highway tortuosity, and $CO_2$ emission savings.

---

## 3. Core System Architecture & Data Flow

```
                      [ Site Engineer / User Demand ]
                                     │
                                     ▼
                      [ Next.js 16 Portal (Port 3000) ]
                                     │
                 (Reverse Proxy: /api/v1/* -> port 8000)
                                     │
                                     ▼
                    [ FastAPI Gateway (Port 8000) ]
                                     │
    ┌────────────────────────────────┼────────────────────────────────┐
    │                                │                                │
    ▼                                ▼                                ▼
[ Ingest / MTC Parser ]     [ Multi-Property Match ]     [ Consignment Requisition ]
(PyMuPDF / PaddleOCR)       (Dialect -> Dense Vector)    (Multi-Tenant Isolation)
    │                                │                                │
    ▼                                ▼                                ▼
(Ladle Chemistry:           [ Candidate Retrieval ]      [ Pessimistic Locking ]
 CE_IIW, PREN, Yield)        (Qdrant 1024-dim HNSW)      (SELECT ... FOR UPDATE)
                                     │                                │
                                     ▼                                ▼
                          [ Deterministic Safety Core ]   [ SoD Release Approval ]
                          (21 Codified Standards)        (Supplying CPSE Manager)
                                     │                                │
                     ┌───────────────┴───────────────┐                ▼
                     │                               │        [ CISF Digital Gate Pass ]
             [ VIOLATION? ]                   [ PASSED? ]     (SHA-256 HMAC & SVG QR)
                     │                               │                │
                     ▼                               ▼                ▼
            TIER 3 INCOMPATIBLE              TIER 1 / TIER 2  [ Sovereign Audit Ledger ]
            (Score = 0.0 Veto)               (Score >= 0.80)  (Chained Cryptographic Blocks)
                                                                      │
                                                                      ▼
                                                              [ CDC Outbox -> Neo4j ]
                                                              (19-Depot Logistics Graph)
```

---

## 4. Non-Negotiable Architecture Invariants

When inspecting, refactoring, or extending the codebase, **Claude must NEVER violate these 5 invariants**:

| Invariant | Principle | Enforcement Mechanism |
|---|---|---|
| **#1: Hard Safety Gate** | Safety standards possess unilateral veto authority. AI vector similarity is strictly prohibited from overriding safety rules. | If any deterministic safety check fails, `compatibility_tier` is forced to `TIER_3_INCOMPATIBLE` and `composite_score` is set to `0.0`. |
| **#2: Zero Static Tiers** | Catalog items have NO inherent, static compatibility tier. Tiers are purely dynamic relative to a query: $S(Q, C)$. | Catalog browsing is completely tier-neutral. Tiers exist only as the output of `evaluate_material_compatibility(query, candidate)`. |
| **#3: Consignment Isolation** | Tenants must not view or tamper with other organizations' requisitions. | `list_requisitions_for_user(db, user)` filters records: regular users only see requests they created or incoming requests for their depot/CPSE. |
| **#4: Segregation of Duties** | Requisitioning engineers cannot authorize surplus stock release from their own or foreign depots. | Self-approval returns `HTTP 403 Forbidden`. Only the supplying CPSE's `MATERIALS_MANAGER` can approve. `CISF_SECURITY` issues the digital gate pass. |
| **#5: Chained Sovereign Ledger** | Audit records must be mathematically tamper-evident from Genesis root to latest entry. | Every ledger entry computes `entry_hash = SHA256(previous_hash + payload)`. Genesis root is `"0" * 64`. Any modification breaks the chain. |

---

## 5. Codebase Directory & File Registry

Use this index directly to locate components without wasting tokens on file-system exploration:

### Backend Services & Routers (`backend/`)
- `backend/main.py`: FastAPI entrypoint, CORS configuration, lifespan seeder, CDC background daemon, router mounting.
- `backend/app/core/config.py`: Pydantic `BaseSettings` for database URLs, Qdrant/Neo4j endpoints, and engineering thresholds.
- `backend/app/core/security.py`: Chained SHA-256 ledger algorithms, HMAC-SHA256 gate pass seals, JWT encoding/decoding, bcrypt.
- `backend/app/core/exceptions.py`: Domain HTTP exceptions (`ResourceNotFoundError`, `ValidationError`, `IdempotencyConflictError`, etc.).
- `backend/app/api/dependencies.py`: FastAPI dependency injection (`get_db_session`, `get_current_user`, `require_roles`, `validate_idempotency_key`, `verify_cpse_access`).
- `backend/app/api/routers/`:
  - `auth.py`: JWT login, user registration, profile retrieval, super admin governance.
  - `requisition.py`: Multi-tenant consignment lifecycle, segregation of duties, gate pass generation, status transitions.
  - `match.py`: Multi-property specification matching (`size_nb_mm`, `pressure_class`, `schedule`, `metallurgy`, `weldability_class`, `sour_service`, `facing_end`, `trim_no`).
  - `inventory.py`: Catalog exploration, surplus radar, HITL triage queue, commercial price privacy stripping.
  - `graph.py`: Surplus discovery, GIS transit calculations, 19-depot topology queries.
  - `audit.py`: Sovereign audit ledger verification root-to-tip, RFC 4180 CSV statutory compliance export.
  - `ingest.py`: Dual-path PDF MTC intake, chemistry extraction, OCR fallback.
- `backend/app/models/`:
  - `base.py`: SQLAlchemy `Base`, connection pooling engine (`pool_pre_ping=True`).
  - `user.py`: `User` table (username, cpse, depot_id, role, hashed_password).
  - `inventory.py`: `InventoryItem` (27 columns: BIS IS, GeM, MESC, MII %, dimensions, metallurgy, status).
  - `requisition.py`: `Requisition`, `InventoryLock`, `DigitalGatePass`.
  - `audit.py`: `SovereignAuditLedger`, `ActiveLearningFeedback`.
  - `cdc.py`: `CdcOutbox` table.
- `backend/app/schemas/`:
  - `auth.py`: `UserRole`, `TokenResponse`, login/signup DTOs.
  - `material.py`: `DynamicCompatibilityTier`, `ExtractedMaterialAttributes`, `PropertyScorecard`, `RuleViolation`.
  - `inventory.py`: `InventoryItemPublic`, `InventoryItemPrivate` (privacy filtering).
  - `requisition.py`: `RequisitionCreate`, `RequisitionResponse`, `GatePassResponse`.
  - `audit.py`: `AuditEntryResponse`, `AuditChainVerificationResponse`.
- `backend/app/services/`:
  - `requisition_service.py`: State machine transitions, pessimistic locking (`SELECT ... FOR UPDATE`).
  - `inventory_service.py`: Catalog queries, privacy masking, surplus status updates.
  - `audit_service.py`: Cryptographic block appending, chain verification.
  - `cdc_manager.py`: PostgreSQL trigger listener (`samanvay_cdc_channel`) streaming to Neo4j.
  - `seeder.py`: Startup idempotent seeder (5,000 items, 25+ demo personas, genesis blocks).

### Deterministic Safety Core (`rules/`)
- `rules/tolerance.py`: Master orchestrator `evaluate_material_compatibility(query, candidate)`.
- `rules/asme/`:
  - `pressure_class.py`: ASME B16.5 / B16.34 classes (150# - 2500#), PSI ratings, bolt circle dimension mismatches.
  - `facings.py`: ASME B16.5 RF vs FF vs RTJ, cast iron ear cracking (B31.3 Section 312.2), slip-on vs weld neck.
  - `large_flanges.py`: ASME B16.47 Series A (MSS SP-44) vs Series B (API 605) bolt circle incompatibility.
  - `fittings.py`: ASME B16.11 forged socket/threaded & B16.9 buttweld fittings.
  - `gaskets.py`: ASME B16.20 spiral wound inner rings, RTJ ring hardness (< flange ring groove).
  - `line_blinds.py`: ASME B16.48 spectacle blinds, paddle blanks, paddle spacers.
  - `flange_insulation.py`: NACE SP0286 dielectric insulation kits (Type E vs Type F).
- `rules/astm/`:
  - `metallurgy_dag.py`: ASTM DAG (Levels 0–13), low-temp brittle transition ($-46^\circ\text{C}$ Charpy), creep steels (P11, P22, P91), sensitization.
  - `fasteners.py`: ASTM A193 B7/B16/L7 studs + A194 2H/7 nuts pairing, Liquid Metal Embrittlement (LME $>200^\circ\text{C}$).
- `rules/piping/`:
  - `schedules.py`: ASME B36.10M/B36.19M pipe schedules ladder, ISO 21809 3LPE coatings.
  - `nace.py`: NACE MR0175 / ISO 15156 sour hydrocarbon hardness ceiling ($\le 22$ HRC / 248 HV).
  - `line_pipe.py`: API 5L PSL 1 vs PSL 2 fracture toughness, ASME B31.3 Category M lethal fluid service.
  - `tubing.py`: ASTM A269 metric vs imperial OD, maximum hardness $\le 90$ HRB.
  - `expansion_joints.py`: EJMA metallic bellows (tied vs unrestrained), ISO 10380 braided hoses.
- `rules/equipment/`:
  - `heat_exchangers.py`: TEMA R > C > B classes, seamless vs welded tubes, BWG wall thickness basis, U-bend annealing.
  - `tank_safety.py`: API 2000 PVRV vacuum implosion, ISO 16852 detonation flame arrestors, tank coating systems.
  - `strainers_traps.py`: Pump suction mesh/NPSH, filter microns, NPT vs BSPT threads, steam trap backpressure.
  - `thermal_insulation.py`: ASTM C795 CUI leachable chlorides ($<50$ ppm), ASTM C552 cellular glass for cryogenic duty.
- `rules/rotating/`:
  - `pumps.py`: API 610 pumps (OH1 vs OH2 centerline mounting for $>150^\circ\text{C}$), wear ring hardness differential $\Delta \ge 50$ HB.
  - `seals.py`: API 682 seal flush plans (Plan 53B vs Plan 52 in toxic service), elastomer O-ring thermal limits.
  - `motors.py`: IEC 60034 / IS 325 motors, Ex d flameproof vs Ex e enclosures, 2-pole vs 4-pole synchronous speed.
  - `bearings.py`: ISO 15 rolling bearings, radial internal clearance ladder (C2 < CN < C3 < C4).
  - `compressors.py`: API 618 reciprocating cylinder valve orientation, API 617 impellers, API 692 dry gas seals.
- `rules/valves/`:
  - `bore.py`: API 6D Full Bore (FB) vs Reduced Bore (RB) piggability invariant.
  - `fire_safe.py`: API 607 / API 6FA fire-safe certification, API 609 butterfly categories (A vs B), API 594 check valves.
  - `trim.py`: API 600 gate valve trim ladder (Trim 1 through 16: 410 SS -> Stellite -> Monel).
  - `psv.py`: API 520 / API 526 PSV orifice area letters (D through T), CDTP set pressure tolerance.
  - `rupture_disks.py`: ASME Sec VIII UG-127 non-fragmenting disk mandate upstream of PSVs, reverse buckling cyclic fatigue.

### Machine Learning & Graph Mesh (`ml/`, `graph/`)
- `ml/ner/normalizer.py`: 40+ CPSE acronym thesaurus (`DIALECT_THESAURUS`), Indian standard extractors (IS, GeM, CPPP, MII).
- `ml/embeddings/client.py`: `BAAI/bge-m3` 1024-dim dense representation, Qdrant client collection initialization.
- `ml/ranking/ranker.py` & `feature_extract.py`: 4 domain subvectors (Dimensional, Metallurgical, Pressure/Temp, Standards) + XGBoost ranker + TreeSHAP.
- `ml/vision/mtc_parser.py`: Dual-path PyMuPDF (<50ms vector stream) vs PaddleOCR/EasyOCR, chemical ladle analysis ($CE_{\text{IIW}}$, PREN).
- `ml/active_learning/cache.py`: `ActiveLearningCache` HITL prediction caching and expert verification stamps.
- `graph/schema.py` & `syncer.py`: Neo4j 5.20 node definitions, 19 CPSE depot coordinates, road circuity ($1.28\times$), CDC outbox batch streaming.

### Frontend Command Center (`frontend/`)
- `frontend/next.config.ts`: Next.js `rewrites()` `/api/v1/:path*` -> internal backend container port 8000.
- `frontend/app/`: Next.js 16 App Router pages (`layout.tsx`, `page.tsx`, `discover/page.tsx`, `requests/page.tsx`, `catalog/page.tsx`, `audit/page.tsx`, `network/page.tsx`, `eval-hub/page.tsx`).
- `frontend/components/`: Reusable UI (`AppShell.tsx`, `Navigation.tsx`, `GatePassModal.tsx`, `PropertyScorecardModal.tsx`, `EvaluationHubModal.tsx`).

---

## 6. How Claude Should Analyze, Identify Problems & Propose Solutions

When the user asks Claude to build new features, review, or refactor code in any part of the project, Claude should follow this structured thinking process:

### Step 1: Deep Code Inspection
- Locate the relevant file(s) in Section 5.
- Read and inspect the implementation in context of the surrounding subsystem (e.g. how a router calls services, how services interact with models and transactions, how rules interact with scoring).
- Verify compliance with the 5 Architecture Invariants (Section 4).

### Step 2: Problem & Inefficiency Diagnosis
Systematically analyze the code for:
- **Performance & Latency:** Unnecessary query amplification (N+1 queries), missing database indices, un-memoized repeated calculations, synchronous operations blocking async event loops, or heavy model initializations in hot paths.
- **Concurrency & Race Conditions:** Vulnerabilities in inventory locking, state transitions without atomic updates, or unhandled concurrent approvals.
- **Resource & Memory Footprint:** RSS memory bloat, unbounded in-memory caches, unclosed connections or file descriptors, or excessive payload serialization.
- **Safety & Domain Gaps:** Missing physical invariants, incorrect tolerance boundaries, unhandled edge cases in standards codification, or inadequate error reporting.
- **Security & Multi-Tenant Leaks:** Cross-tenant visibility leaks, missing role guards, or un-audited state changes.
- **Code Cleanliness & Maintainability:** Code duplication, tight coupling, missing type annotations, or untestable structures.

### Step 3: Structured Problem & Solution Presentation
When reporting findings to the user, format responses compactly:
1. **Identified Issue:** 1-sentence description of the bug, bottleneck, or design gap.
2. **Impact & Root Cause:** 2-3 bullet points explaining why it happens and what it costs in production (latency, memory, race condition, compliance).
3. **Proposed Optimal Solution:** Architectural approach and technical trade-offs.
4. **Targeted Implementation:** Surgical code diffs (`diff -u` style or clean replacement blocks) ready to apply.

---

## 7. Developer Commands & Workflows

```powershell
# --- Python Virtual Environment & Testing ---
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000   # Launch Backend Gateway
uv run pytest tests/unit/test_tolerance.py -v                       # Test 21 mechanical safety rules
uv run pytest tests/api/ -v                                         # Test FastAPI REST endpoints
uv run pytest tests/integration/ -v                                 # Test 150 Golden Benchmarks
uv run pytest tests/unit/test_chemistry.py -v                       # Test IIW CE & PREN formulas

# --- Frontend Portal Development ---
cd frontend
npm run dev                                                         # Launch Next.js dev server on :3000
npm run build                                                       # Test production standalone build

# --- Full Stack Docker Compose ---
docker compose -f docker/docker-compose.yml down -v                 # Clean volume reset
docker compose -f docker/docker-compose.yml --env-file docker/.env.docker up -d --build # Production rebuild
```

---

## 8. Demo Personas & Auth Credentials

All accounts share the default password: **`Samanvay@2026`**

| Persona Username | CPSE / Organization | Role | Purpose / Authority |
|---|---|---|---|
| `oil_eng` | Oil India Limited (Duliajan) | `SITE_ENGINEER` | Creates requisitions, searches surplus catalog |
| `oil_mm` | Oil India Limited (Duliajan) | `MATERIALS_MANAGER` | Approves surplus releases, manages depot stock |
| `oil_sec` | Oil India Limited (Duliajan) | `CISF_SECURITY` | Validates QR code, signs & issues gate pass |
| `iocl_eng` | Indian Oil Corporation (Panipat) | `SITE_ENGINEER` | Requisitions refinery spares, tests cross-tenant isolation |
| `iocl_mm` | Indian Oil Corporation (Panipat) | `MATERIALS_MANAGER` | Supplying authority for Panipat depot inventory |
| `ongc_eng` | ONGC (Uran/Mumbai) | `SITE_ENGINEER` | Offshore/onshore asset maintenance demands |
| `ongc_mm` | ONGC (Uran/Mumbai) | `MATERIALS_MANAGER` | Offshore surplus release authorization |
| `bpcl_mm` | Bharat Petroleum (Mahul) | `MATERIALS_MANAGER` | Downstream refinery spare supply management |
| `hpcl_mm` | HPCL (Visakh) | `MATERIALS_MANAGER` | Coastal refinery inventory management |
| `gail_mm` | GAIL India (Pata) | `MATERIALS_MANAGER` | Gas transmission pipeline spare release |
| `nrl_mm` | Numaligarh Refinery (Numaligarh) | `MATERIALS_MANAGER` | North-East refinery logistics coordination |
| `mopng_auditor` | MoPNG Central Authority | `VIGILANCE_AUDITOR` | Read-only sovereign audit verification, CVC exports |
| `super_admin` | Inter-CPSE Headquarters | `SUPER_ADMIN` | Global tenant switcher, system configuration |

---

## 9. Codified Engineering Math & Physics Reference

- **IIW Carbon Equivalent ($CE_{\text{IIW}}$):**
  $$CE_{\text{IIW}} = C + \frac{Mn}{6} + \frac{Cr + Mo + V}{5} + \frac{Ni + Cu}{15}$$
  - $CE \le 0.43$: Safe weldability without mandatory pre-heat.
  - $CE > 0.43$: High cracking risk, mandatory pre-heat/PWHT or Tier 3 veto.
- **Pitting Resistance Equivalent Number (PREN):**
  $$\text{PREN} = \text{Cr} + 3.3(\text{Mo} + 0.5\text{W}) + 16\text{N}$$
  - Duplex 2205: $\text{PREN} \approx 35$; Super Duplex 2507: $\text{PREN} \ge 42$.
- **Barlow's Equation for Internal Pipe Pressure ($P$):**
  $$P = \frac{2 \cdot S \cdot t}{D}$$
  - $S$ = Allowable stress, $t$ = Wall thickness, $D$ = Outside diameter.
- **NACE MR0175 Hardness Ceiling:**
  - Standard carbon steel exposed to wet sour gas ($H_2S$) MUST NOT exceed **22 HRC** (248 HV).
- **Haversine Distance ($D_{\text{km}}$) with Indian Road Circuity:**
  $$\text{Road Distance} = 1.28 \times D_{\text{haversine}}$$
- **BEE Freight $\text{CO}_2$ Savings:**
  $$\text{Saved } \text{CO}_2 (\text{kg}) = (\text{Air/Sea km} - \text{Domestic km}) \times \text{Weight (tonnes)} \times 0.0612$$
