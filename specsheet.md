# Samanvay-AI: System Engineering Specification & Rebuild Blueprint
**Document Version:** 2.0.0-PROD  
**Target Milestone:** Production Rebuild (Clean Architecture)  
**Problem Statement ID:** SIH26099 | Smart India Hackathon (MoPNG)  
**Team ID:** 26P30 | **Team Name:** BharatCodex  
**Author / Lead:** Mayank Anand (Team Lead & Systems Architect)  
**Compliance Standard:** 100% Aligned with `SIH_Presentation.pptx` (Zero Contradictions)

---

## 1. Executive Vision & Rebuild Rationale

### 1.1 The Core Problem
The Indian Ministry of Petroleum and Natural Gas (MoPNG) oversees premier Central Public Sector Enterprises (CPSEs)—**IOCL, ONGC, BPCL, HPCL, and GAIL**—operating dozens of oil refineries, petrochemical complexes, offshore platforms, and pipeline terminals across India.

Currently, each enterprise maintains isolated Enterprise Resource Planning (ERP) instances (predominantly SAP MM and Oracle E-Business Suite) with proprietary material master coding taxonomies:
- **IOCL:** Truncated imperial descriptions with hash ratings (e.g. `FLG WNRF 4IN 300# A105`).
- **ONGC:** Verbose, comma-delimited formal specifications (e.g. `FLANGE, WELDING NECK, 4 INCH, CLASS 300, ASTM A105, ASME B16.5, RF FACING`).
- **BPCL:** Metric-preferred hyphenated alphanumeric strings (e.g. `FLG-WN-DN100-PN50-A105-RF`).

Because these codes do not cross-reference, enterprises procure redundant emergency spares via costly public tenders (taking 4–6 weeks lead time) while identical or safe substitute spares sit dormant as idle surplus in sister CPSE warehouses within reasonable trucking distance. Across MoPNG enterprises, **over ₹100+ Crores of working capital is trapped in dormant, duplicate spare parts**.

### 1.2 Why Rebuild from Scratch? (Post-Mortem of v1 Prototype)
The initial prototype established proof-of-concept for the hackathon but accumulated critical architectural anti-patterns, technical debt, and deviations from the production vision:
1. **Hardcoded Heuristic Fallbacks:** The API client and router endpoints contained embedded fallback mock data with hardcoded string checks (e.g., `if (upper.includes("MOTOR")) return {...}`). In production, missing data must be handled cleanly via robust database queries or explicit empty-state contracts, never fake heuristics.
2. **Route Fragmentation & Redirect Shims:** Several routes (`/dashboard`, `/deduplication`, `/transfers`, `/audits`, `/hitl`) were turned into redirect wrappers to alternate pages, creating confusing route loops and violating the presentation's commitment to a dedicated HITL queue and separate operational hubs.
3. **Attribute-Level Privacy Violation:** The v1 prototype exposed item unit costs and total valuations across CPSEs in cross-search results. This directly violated **Slide 4 of `SIH_Presentation.pptx`**, which explicitly mandates:
   > *"Attribute-Level Privacy: Cross-company search reveals only physical specs and depot inventory counts; commercial prices remain strictly hidden."*
4. **Dead & Orphaned Code:** Multiple exploratory scripts, half-implemented biencoder training loops, unreferenced CSS files, and unused Pydantic models cluttered the codebase.
5. **Coupled Database Drivers:** Database connectivity, mock dictionaries, and file reads were tangled inside route handlers instead of being separated into distinct Repository and Service layers.

### 1.3 Architectural Guarantees (Non-Negotiable Invariants)
In strict compliance with `SIH_Presentation.pptx`:
1. **Zero Disruption to Existing ERPs:** Samanvay-AI connects strictly as an external, read-only intelligence layer over batch catalog exports (CSV/Excel) and document streams. Existing SAP/Oracle transactional databases remain 100% untouched.
2. **100% Private & Sovereign Air-Gapped Deployment:** Operates entirely within secure government cloud infrastructure (NIC / RailTel Cloud) with zero third-party SaaS dependencies, zero external LLM API calls (no OpenAI/Anthropic/Gemini cloud endpoints), and complete local inference.
3. **Per-Query Runtime Dynamic Compatibility Tiers (Zero Static Pre-Assignment):** Compatibility tiers (Tier 1, Tier 2, Tier 3) are strictly computed **at runtime on a per-part basis** relative to the exact item being searched by the site engineer ($Q \leftrightarrow C_i$). Warehouse surplus items possess no static tier in the database. An ML scoring model (trained using the 21 codified rulesets and physical feature extractors) computes a continuous compatibility score ($S \in [0\%, 100\%]$):
   - $\ge 95\%$ match with identical dimensions and chemical/physical properties $\implies$ **Tier 1 (Direct Interchangeable)**.
   - $\ge 80\%$ to $< 95\%$ match with safe upgrades or minor adaptable variances $\implies$ **Tier 2 (Functional Substitute - Requires HITL Sign-off)**.
   - $< 80\%$ match OR any violation of zero-tolerance engineering invariants $\implies$ **Tier 3 (Incompatible / Hazardous Replacement)**.
   A Deterministic Engineering Safety Core enforces that AI vector similarity is mathematically incapable of overriding a zero-tolerance physical safety rule.
4. **Sovereign Audit Trail & CVC/CAG Compliance:** Every material classification, status transition, engineer approval, and gate pass dispatch is cryptographically signed with SHA-256 digital seals and logged in an append-only audit ledger.
5. **Scale & Latency SLA:** Searches across 100,000 catalog line items in `< 15 ms`; processes document OCR in `< 50 ms` per vector page and `< 250 ms` for high-resolution scans.
6. **Enabler Role (Zero Statutory Certificate Validation Overhead):** Samanvay-AI acts strictly as an **operational unification and discovery enabler** across CPSE databases. It standardizes catalogs, performs property-level engineering compatibility (dimensions, pressure ratings, metallurgy, connection types), and facilitates inter-CPSE logistics. The platform **does NOT** perform statutory certificate audits or validations (such as verifying IBR Form III-C/IV or PESO licenses); statutory certification compliance remains with plant inspection authorities and existing enterprise ERP workflows.

---

## 2. End-to-End System Architecture

```
+----------------------------------------------------------------------------------------------------+
|                                      CLIENT PRESENTATION LAYER                                     |
|                      Next.js 16 (App Router) | React 19 | Tailwind CSS | shadcn/ui                 |
|                                                                                                    |
|  [/upload]              [/inventory]                 [/discover]               [/requests]              [/audit]              |
|  Bill & MTC Intake      Plant Stock Ledger,          Pre-Purchase Radar        Inter-CPSE Indents,      Sovereign Vigilance   |
|  & Site OCR Preview     Surplus Lifecycle &          Cross-CPSE Discovery      Consignment Milestones   SHA-256 Hash Chain    |
|                         Embedded HITL Triage Queue   (Attributes Protected)    & CISF Outward Gate Pass CVC / CAG Audit Trail |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  | HTTPS / REST (Typed OpenAPI Contracts)
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                     FASTAPI GATEWAY & API ROUTERS                                  |
|                             FastAPI | Pydantic v2 | Python 3.12/3.14                               |
|                                                                                                    |
|  [/api/v1/ingest]    [/api/v1/inventory]  [/api/v1/match]    [/api/v1/graph]    [/api/v1/requisition]  [/api/v1/audit]|
|  Multi-modal PDF/MTC Central Stock Ledger NER + Qdrant Top-K Neo4j Surplus      Inventory Locks, GIS,  Chained Ledger |
|  Batch Catalog Stream & Lifecycle Updates  & Tolerance Rules  Radar & Taxonomy   CISF SVG Gate Pass     & Verification |
+----------------------------------------------------------------------------------------------------+
                                                  |
                   +------------------------------+------------------------------+
                   |                                                             |
                   v                                                             v
+------------------------------------+                         +-------------------------------------+
|      STAGE 01 & 02: AI & ML        |                         |   STAGE 03: DETERMINISTIC SAFETY    |
|                                    |                         |                                     |
| 1. Document Intelligence:          |                         | 1. Master Tolerance Engine:         |
|    - PyMuPDF (vector PDF < 50ms)   |                         |    - Tier-1: Drop-In Match (>= 95%) |
|    - PaddleOCR PP-OCRv4 (< 250ms)  |                         |    - Tier-2: Safe Upgrade (80%-94%) |
|    - Certificate chemistry & CE    |                         |    - Tier-3: Incompatible (< 80%)   |
| 2. Dialect NER Slot Tagger:        |                         | 2. Engineering Standards Invariants:|
|    - NFKC + CPSE Dialect Thesaurus |                         |    - ASME B16.5 Pressure Classes    |
|    - DeBERTa-v3 Slot Extractor     |                         |    - ASTM Metallurgy Directed Graph |
| 3. Dense Vector Retrieval:         |                         |    - ASME B36.10M Pipe Schedules    |
|    - BAAI/bge-m3 (1024-dim)        |                         |    - NACE MR0175 Wet H2S Sour Duty  |
|    - Qdrant HNSW Cosine Index      |                         |    - ASME B16.47 Large Flange Series|
|    - Payload Pre-filtering (< 15ms)|                         |    - IS/IEC 60079 Flameproof Motors |
|                                    |                         |    - API 682 Seal Plans & ISO 15 Brg|
|                                    |                         |    - API 520 / 526 Relief Valves    |
+------------------------------------+                         +-------------------------------------+
                   |                                                             |
                   +------------------------------+------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                    STAGE 04: KNOWLEDGE GRAPH & DATA                                |
|                                                                                                    |
| 1. Neo4j Graph Ontology:                                                                           |
|    - (:CPSE)-[:OPERATES]->(:Depot)-[:HOLDS]->(:InventoryItem)-[:STANDARDIZED_AS]->(:CanonicalMaterial)  |
|    - (:CanonicalMaterial)-[:CLASSIFIED_UNDER]->(:GeMCategory) & (:UNSPSCCommodity)                 |
| 2. PostgreSQL 16 (Relational Ledger):                                                              |
|    - Ingested documents, inventory items, active requisitions, audit logs, atomic inventory locks |
| 3. Active Learning Cache:                                                                          |
|    - Dual-index in-memory LRU + DB persistence for real-time dynamic reranking (< 1ms)             |
| 4. GIS Logistics & Statutory CISF Gate Pass Engine:                                                |
|    - 19 CPSE depot GPS coordinates, Haversine + 1.28x road tortuosity, CONCOR freight rates       |
|    - Self-contained SVG QR codes with SHA-256 digital seals                                        |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Detailed Subsystem Specifications

### 3.1 Stage 01: Smart Document Intake & Certificate Intelligence

#### A. Objectives & Operational SLA
- Ingest vendor procurement invoices, material test certificates (MTCs under **EN 10204 3.1 / 3.2**), delivery challans, and equipment inspection sheets.
- Throughput SLA: Sub-50ms for native digital vector PDFs via stream extraction; sub-250ms for high-resolution scanned sheets via hardware-accelerated OCR.

#### B. Ingestion Pipeline
1. **Document Classifier:** Inspects file headers to distinguish digital vector PDFs from raster scans.
2. **Dual-Path Extraction:**
   - *Fast Path (Digital Vector PDFs):* PyMuPDF (`fitz`) extracts embedded text streams, character positions, and vector table grids in $< 50\text{ ms}$ without rasterization.
   - *Scan Path (Raster Images & Scanned Challans):*
     - Standardized strictly on **PaddleOCR (PP-OCRv4)** across all deployment environments (Windows and Linux) for consistent character recognition, zero platform-specific divergence, and native rotated bounding-box detection.
     - Image preprocessing: 300 DPI normalization, adaptive contrast enhancement, and deskew estimation using Hough line transforms.
3. **MTC Certificate Extraction Engine (`certificate.py`):**
   - **Header Parsing:** Heat/Melt number, MTC certificate number, Purchase Order (PO) reference, manufacturer name, third-party inspection (TPI) agency (e.g. Lloyds, DNV, Bureau Veritas).
   - **Chemical Composition Matrix:** Extracts elemental weight percentages: Carbon ($C$), Manganese ($Mn$), Silicon ($Si$), Phosphorus ($P$), Sulfur ($S$), Chromium ($Cr$), Molybdenum ($Mo$), Nickel ($Ni$), Vanadium ($V$), Copper ($Cu$).
   - **Carbon Equivalent ($CE$) Calculation:**
     Automatically computes the International Institute of Welding (IIW) Carbon Equivalent formula:
     $$CE = C + \frac{Mn}{6} + \frac{Cr + Mo + V}{5} + \frac{Ni + Cu}{15}$$
     - If $CE \le 0.43\%$: Marked as `STANDARD_WELDABLE` (safe for standard refinery field welding).
     - If $CE > 0.43\%$: Marked as `PREHEAT_REQUIRED_HIGH_CE` (triggers statutory pre-heat/post-weld heat treatment warning).
   - **Mechanical Property Thresholds:**
     Validates yield strength ($R_e$), tensile strength ($R_m$), elongation ($A\%$), and Charpy V-notch impact toughness against ASTM specifications. If measured values fail ASTM minimums, generates an immediate material non-conformance rejection warning.

---

### 3.2 Stage 02: Dialect Normalization, AI Slot Tagging & Vector Retrieval

#### A. Refinery Dialect Normalizer & Thesaurus (`ner_tagger.py`)
Applies Unicode NFKC normalization and an exhaustive CPSE dialect thesaurus mapping enterprise shorthand into standardized engineering terminology before tokenization:

| Raw Dialect / Shorthand | Standardized Terminology | Extracted Metadata |
|---|---|---|
| `NRV`, `NON RETURN VLV`, `CHK VLV` | `CHECK VALVE` | `item_type = CHECK_VALVE` |
| `BFV`, `BFLY VLV` | `BUTTERFLY VALVE` | `item_type = BUTTERFLY_VALVE`, `standard = API 609` |
| `SPRF`, `SP BLIND`, `SPEC BLIND` | `SPECTACLE BLIND RF` | `item_type = FLANGE_BLIND`, `facing_end = RF` |
| `LTCS`, `LF-2`, `A-350 LF2` | `ASTM A350 LF2` | `metallurgy = ASTM A350 LF2`, `temp_service = CRYOGENIC` |
| `DSS`, `UNS S31803`, `F51` | `DUPLEX STAINLESS STEEL` | `metallurgy = ASTM A182 F51` |
| `SDSS`, `UNS S32750`, `F53` | `SUPER DUPLEX STAINLESS` | `metallurgy = ASTM A815 S32750` |
| `INCO 625`, `ALLOY 625` | `INCONEL 625` | `metallurgy = INCONEL 625` |
| `HAST-C`, `C-276` | `HASTELLOY C-276` | `metallurgy = HASTELLOY C-276` |
| `PN 20` / `PN 50` / `PN 100` | `CLASS 150` / `CLASS 300` / `CLASS 600` | `pressure_class = 150 / 300 / 600` |
| `4IN`, `4"`, `4 INCH`, `DN100` | `100.0 mm` | `size_nb_mm = 100.0` |

#### B. DeBERTa-v3 Slot Extraction
- Uses fine-tuned `microsoft/deberta-v3-small` for token classification (Named Entity Recognition).
- Labels: `B-ITEM_TYPE`, `I-ITEM_TYPE`, `B-SIZE`, `B-CLASS`, `B-MAT`, `I-MAT`, `B-FACING`, `B-SCHED`, `B-STD`.
- Outputs a strongly-typed Pydantic model: [`ExtractedMaterialAttributes`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/contracts/material.py).

#### C. Semantic Dense Vector Search (`vector_search.py`)
- **Embedding Model:** `BAAI/bge-m3` running locally via HuggingFace / ONNX Runtime. Generates dense 1024-dimensional semantic vectors.
- **Vector Database:** Qdrant instance with HNSW graph indexing (`m=16`, `ef_construct=100`, Cosine distance).
- **Payload Pre-Filtering:** To ensure candidates conform to the same broad category, vector queries enforce a hard payload filter on `item_type` (e.g. searching a gate valve will never evaluate flanges in vector space).
- **SLA:** Top-5 candidate retrieval executed in $< 15$ ms across 100,000 indexed records.

---

### 3.3 Stage 03: Runtime Per-Part Dynamic Compatibility Engine & Deterministic Safety Core

#### 3.3.1 Relational Per-Part Dynamic Compatibility & Granular Multi-Property Tiering
- **Zero Static Pre-Assignment Rule:**
  - Physical spare parts sitting on warehouse shelves in any CPSE depot **do not possess an intrinsic or static compatibility tier**. Storing a static `tier` column on inventory items is strictly prohibited as an architectural anti-pattern.
  - A compatibility tier is **strictly a dynamic, relational computation** calculated at runtime between the specific item searched by the site engineer (Query Part $Q$) and a retrieved candidate surplus item (Candidate Part $C$).

- **The Granular Multi-Property System ($K \approx 6 \text{ to } 10$ Parameters):**
  A physical part in process engineering is not a simple string. It comprises a set of $K$ physical parameters:
  1. **Universal Core Properties (Present across all fluid/mechanical parts):**
     - **Dimensions / Size:** Nominal diameter (NPS/DN), Outer Diameter (OD), Bolt Circle (PCD), Face-to-Face length.
       - *ABSOLUTE HARD CONSTRAINT:* If primary physical dimensions vary, **Dimension Tier = Tier 3 (HARD REJECT)** $\implies$ **Final Composite Tier FORCED TO TIER 3 (0% Compatibility)**. No exceptions.
     - **Pressure Rating / Class:** Design working pressure in PSI / bar, or ASME Class (150# to 2500#).
       - Down-rating is strictly rejected (**Tier 3**). Equal or dimension-preserving safe over-rating achieves $\ge 95\%$ (**Tier 1**).
     - **Body Metallurgy / Alloy:** Material chemical grade and yield strength.
       - Downgrade is rejected (**Tier 3**). Equal or safe alloy upgrade per ASTM DAG achieves $\ge 95\%$ (**Tier 1** for direct interchangeable) or $80\%\text{--}94\%$ (**Tier 2** for functional substitute requiring HITL sign-off).
     - **End Connection Geometry:** Flanged RF/RTJ, Beveled End (BE), Threaded (NPT), Socket Weld (SW).
       - Incompatible connection types are rejected (**Tier 3**).

  2. **Equipment-Specific Physical Properties (Evaluated per Component Family):**
     - **Valves (8–10 Properties):**
       - `Trim Metallurgy:` API 600 Trim number (Trim 1, 5, 8, 12, 16 - stem, seat, wedge). Mismatch in erosive/corrosive lines is flagged or rejected.
       - `Port Bore Type:` Full Bore (FB - piggable) vs. Reduced Bore (RB). If piggability is required, RB is blocked (**Tier 3**).
       - `Fire-Safe Certification:` API 607 / API 6FA certified vs. standard non-fire-safe soft seals.
       - `Actuator Mounting:` ISO 5211 top flange for bare shaft, handwheel, or motor actuator matching.
     - **Pipes & Tubing (6–8 Properties):**
       - `Schedule / Wall Thickness:` ASME B36.10M / B36.19M (SCH 40, SCH 80, STD, XS). Down-scheduling is blocked (**Tier 3**).
       - `Manufacturing Method:` Seamless (SMLS) vs. Welded (ERW, LSAW). Welded cannot replace seamless in lethal/hydrogen lines (**Tier 3**).
       - `Quality Level:` API 5L PSL 1 vs. PSL 2 (mandatory Charpy notch toughness for gas transmission).
       - `Coating / Lining:` Bare, 3LPE, FBE, Galvanized (GI).
     - **Flanges (7–9 Properties):**
       - `Facing Finish & Serration:` ASME B16.5 RF vs. RTJ, spiral serrations ($Ra = 3.2 - 6.3\,\mu\text{m}$) vs. smooth ($Ra = 1.6 - 3.2\,\mu\text{m}$).
       - `Bore Matching:` Weld Neck bore must match pipe schedule ID to prevent turbulence erosion.
       - `Flange Series:` ASME B16.47 Series A (MSS SP-44) vs. Series B (API 605) bolt circle incompatibility.
       - `Sour Duty:` NACE MR0175 / ISO 15156 hardness verification ($\le 22\text{ HRC}$).
     - **Pumps & Rotating Machinery (7–9 Properties):**
       - `API 610 Configuration:` OH1 (foot-mounted) vs. OH2 (centerline-mounted for $>150^\circ\text{C}$).
       - `Material Class:` S-1, S-6 (12% Cr), A-8 (SS316), D-1 (Duplex).
       - `Impeller Diameter & Running Speed:` 2-pole (3000 RPM) vs. 4-pole (1500 RPM) hydraulic shock prevention.
       - `Mechanical Seal Flush Plan:` API 682 Plan 11 (single) vs. Plan 53A (dual pressurized barrier).
       - `Hazardous Area Enclosure:` `Ex d IIC T4 Gb` flameproof motor enclosure.

  > [!NOTE]
  > **Enabler Boundary (Certificate Validation Out-of-Scope):** Samanvay-AI does not search for or validate external government certificates (such as IBR Form III-C or PESO licenses). The platform unifies CPSE databases to match physical specifications (dimensions, pressure, metallurgy, and connection type). Regulatory statutory clearance remains the domain of plant inspectors and enterprise ERPs.

- **Hierarchical Multi-Property Aggregation Logic (Property Tiers $\to$ Final Composite Tier):**
  ```python
  def aggregate_compatibility(Q, C) -> Tuple[DynamicCompatibilityTier, float, PropertyScorecard]:
      # Step 1: Evaluate all active physical properties (Universal + Equipment-Specific)
      evaluated_properties: Dict[str, PropertyEvaluation] = {}
      for prop_name, prop_val in Q.properties.items():
          evaluated_properties[prop_name] = evaluate_property(prop_name, prop_val, C.properties.get(prop_name))
      
      # Step 2: Enforce Dimensional Zero-Tolerance Hard Constraint
      if evaluated_properties["dimensions"].tier == DynamicCompatibilityTier.TIER_3:
          return DynamicCompatibilityTier.TIER_3, 0.0, "DIMENSIONAL MISMATCH: Part physically does not fit line"
          
      # Step 3: Enforce Pressure Down-Rating Hard Constraint
      if evaluated_properties["pressure"].tier == DynamicCompatibilityTier.TIER_3:
          return DynamicCompatibilityTier.TIER_3, 0.0, "PRESSURE DOWN-RATING: Rupture risk under operating pressure"
          
      # Step 4: Enforce Equipment-Specific Fatal Safety Constraints (e.g. piggability, sour service, severe cyclic)
      if any(p.tier == DynamicCompatibilityTier.TIER_3 for p in evaluated_properties.values()):
          return DynamicCompatibilityTier.TIER_3, 0.0, "SAFETY INVARIANT BREACH: One or more properties are strictly incompatible"
          
      # Step 5: Compute ML composite score across valid physical properties
      composite_score = ml_model.predict(evaluated_properties)
      
      # Step 6: Map to final composite tier
      if composite_score >= 0.95 and all(p.tier == DynamicCompatibilityTier.TIER_1 for p in evaluated_properties.values()):
          return DynamicCompatibilityTier.TIER_1, composite_score, "Direct Interchangeable Drop-In Replacement"
      elif composite_score >= 0.80:
          return DynamicCompatibilityTier.TIER_2, composite_score, "Functional Substitute / Safe Upgrade (Requires HITL Review)"
      else:
          return DynamicCompatibilityTier.TIER_3, composite_score, "Incompatible Replacement (Score Below Threshold)"
  ```

- **Concrete Examples for the Site Engineer:**
  - **Example 1 (Searched: 10" GI Pipe 300 PSI | Candidate A: 10" GI Pipe 350 PSI):**
    - `Dimensions (10" OD)`: 🟢 **TIER 1 (100% Match)**
    - `Pressure (350 PSI vs 300 PSI)`: 🟢 **TIER 1 (Safe Over-Rating - 97% Match)**
    - `Material (Galvanized Iron)`: 🟢 **TIER 1 (100% Match)**
    - **Final Outcome:** 🟢 **TIER 1 (98% Compatibility)** $\to$ Safe, superior, immediate drop-in replacement.
  - **Example 2 (Searched: 10" GI Pipe 300 PSI | Candidate B: 10" GI Pipe 250 PSI):**
    - `Dimensions (10" OD)`: 🟢 **TIER 1 (100% Match)**
    - `Pressure (250 PSI vs 300 PSI)`: 🔴 **TIER 3 (0% - REJECTED: Down-rating rupture hazard)**
    - `Material (Galvanized Iron)`: 🟢 **TIER 1 (100% Match)**
    - **Final Outcome:** 🔴 **TIER 3 (HARD REJECTED: Incompatible due to Pressure Down-Rating)**.
  - **Example 3 (Searched: 10" GI Pipe 300 PSI | Candidate C: 8" GI Pipe 350 PSI):**
    - `Dimensions (8" OD vs 10" OD)`: 🔴 **TIER 3 (0% - HARD REJECT: Dimensional Mismatch)**
    - `Pressure (350 PSI vs 300 PSI)`: 🟢 TIER 1 (Safe Over-Rating)
    - `Material (Galvanized Iron)`: 🟢 TIER 1 (100% Match)
    - **Final Outcome:** 🔴 **TIER 3 (HARD REJECTED: Dimension Mismatch - Does Not Fit Line)**.

#### 3.3.2 ML Compatibility Scoring Engine (Trained on Codified Rulesets)
To determine whether a candidate achieves $\ge 95\%$, $\ge 80\%$, or $< 80\%$ compatibility, an ML Compatibility Model (Cross-Encoder Ranker + Gradient Boosted Decision Ensemble) is trained on historical CPSE maintenance interchangeability logs and the 21 codified engineering rulesets:
1. **Multi-Attribute Feature Extraction ($Q \leftrightarrow C$):**
   - **Dimensional Vector:** $\Delta \text{NPS}$ (nominal pipe size), $\Delta \text{OD}$, $\Delta \text{Bore}$, $\Delta \text{PCD}$ (pitch circle diameter), $\Delta \text{Bolt Holes}$, $\Delta \text{Serration Roughness } (Ra)$.
   - **Metallurgy & Chemical Vector:** Elemental weight percentage cosine distance ($\Delta C, \Delta Mn, \Delta Cr, \Delta Mo, \Delta Ni, \Delta V$), Carbon Equivalent delta ($\Delta CE$), Pitting Resistance Equivalent Number ($\Delta \text{PREN}$), Charpy impact test rating, ASTM DAG step distance.
   - **Pressure-Temperature Envelope Vector:** Design pressure containment ratio $P_C(T) / P_Q(T)$, operating temperature capability delta $\Delta T$.
   - **Standards & Certifications Vector:** ASME/API/EN cross-equivalence, fire-safe rating match, NACE sour service compliance, material test certificate grade (EN 10204 3.1).
2. **Continuous Compatibility Score ($S(Q, C)$):**
   The ML model outputs a continuous similarity and suitability score:
   $$S(Q, C) = f_{\text{ML}}\big(\mathbf{x}_{\text{dim}}, \mathbf{x}_{\text{metal}}, \mathbf{x}_{\text{PT}}, \mathbf{x}_{\text{std}}\big) \in [0.0, 1.0] \quad (0\% - 100\%)$$

#### 3.3.3 Dynamic Runtime Tier Classification & Deterministic Safety Gate
The runtime score is mapped to operational compatibility tiers, guarded by an immutable **Deterministic Engineering Safety Gate**:

```
                  [Query Part Q]  <----->  [Candidate Surplus Part C]
                                      |
                                      v
                      [Feature Extraction Pipeline]
                     (Dims, Metallurgy, P-T, Standards)
                                      |
                                      v
                         [ML Compatibility Model]
                  Calculates Continuous Score S(Q, C)
                                      |
                                      v
               +---------------------------------------------+
               |   DETERMINISTIC ZERO-TOLERANCE SAFETY GATE  |
               |     (Evaluates 21 Domain Safety Modules)     |
               +---------------------------------------------+
                                      |
                  Did candidate violate ANY zero-tolerance rule?
                  (e.g., Dimensional Mismatch, Down-rated pressure,
                   Lower schedule, Cryogenic embrittlement,
                   Piggability block, Category M threaded, Non-Ex)
                                 /         \
                              YES           NO
                             /               \
                            v                 v
                 [FORCE TIER 3]        Check Score Threshold:
             is_compatible = False     - If S(Q, C) >= 95%:
             Hard safety violation;      --> TIER 1 (Identical)
             Overrides ML score;       - If 80% <= S(Q, C) < 95%:
             Displays Failure Reason.    --> TIER 2 (Substitute / Upgrade)
                                       - If S(Q, C) < 80%:
                                         --> TIER 3 (Incompatible)
```

1. **Tier 1 (Direct Interchangeable / Identical Replacement):**
   - **Criterion:** Composite Score $S(Q, C) \ge 95\%$ (e.g. $95\% - 100\%$) AND all property tiers $\ge$ Tier 1 AND zero safety rule violations.
   - **Physical Characteristics:** All critical dimensions identical (NPS, outer diameter, bolt circle, bore, facing), metallurgy identical or chemically/physically equivalent, pressure rating equal or safe over-rating, standards equivalent.
   - **Site Engineer Action:** 100% plug-and-play drop-in replacement. Can be requisitioned and installed immediately with zero engineering modification or piping redesign.
2. **Tier 2 (Functional Substitute / Safe Upgrade):**
   - **Criterion:** Composite Score $80\% \le S(Q, C) < 95\%$ (or safe upgrades per the 21 rulesets, e.g. SS316 substituting SS304, or heavier Schedule 80 substituting Schedule 40).
   - **Physical Characteristics:** Dimensionally compatible or adaptable, material/pressure is a safe upgrade meeting or exceeding design specifications, but introduces minor functional variance (e.g., higher pressure rating requiring longer studs, thicker schedule with minor flow delta, superior alloy requiring specific welding filler).
   - **Site Engineer Action:** UI highlights the engineering upgrade delta and requires Human-in-the-Loop (HITL) site engineer review and sign-off before dispatch (`requires_hitl = True`).
3. **Tier 3 (Incompatible / Hazardous Replacement):**
   - **Criterion:** Composite Score $S(Q, C) < 80\%$ OR **violation of ANY codified zero-tolerance invariant** (dimensional variation, pressure down-rating, metallurgy downgrade, etc.).
   - **Physical Characteristics:** Physically not compatible (dimensional mismatch) or physically dangerous as a replacement (hydrostatic rupture risk, toxic gas leakage, thermal expansion seizure, brittle shattering).
   - **Site Engineer Action:** Prohibited from automated requisition. The UI displays prominent red warnings detailing the exact standard violation, failure mode prevented, and safety risk.

---

The deterministic tolerance engine ([`backend/app/matching/tolerance.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/matching/tolerance.py)) receives extracted physical attributes from the query and candidate items. It applies an immutable set of codified engineering safety rules across 21 comprehensive physical engineering domain modules. Probabilistic AI vector similarity is mathematically prohibited from overriding any deterministic rule.

---

#### Module 1: ASME B16.5 / B16.34 Pressure Class Hierarchy & P-T Ratings
- **Class Hierarchy:** `Class 150 < Class 300 < Class 600 < Class 900 < Class 1500 < Class 2500` (and metric equivalents `PN 20 < PN 50 < PN 100 < PN 150 < PN 250 < PN 420`).
- **Down-Rating Prohibition (Fatal Rupture Trap):**
  If candidate pressure class < source required pressure class (e.g. installing Class 150 where Class 300 is required):
  - Result: **Tier-3 Incompatible** (`is_compatible = False`).
  - Violation message: *"FATAL PRESSURE DOWN-RATING: Rupture risk under operating design pressure per ASME B16.5 Table 2."*
- **Up-Rating Permitted & Physical Mating Invariants:**
  - **In-Line Components & Continuous Piping (Dimension-Preserving):** For components where upgrading pressure preserves all outer and mating dimensions (e.g. 10" pipe rated 350 PSI substituting for 300 PSI, or Class 6000# socket weld fitting for 3000# with identical pipe socket OD), the upgrade is classified as **Tier-1 Identical / Safe Over-Rating** ($\ge 95\%$, plug-and-play).
  - **Flanged Components (ASME B16.5 Bolt Circle Invariant):** Upgrading the pressure class of a flanged valve or nozzle (e.g., Class 600# for a Class 300# line) alters the Bolt Circle Diameter (BCD), flange outer diameter, and bolt hole quantity. A Class 600 flange **cannot physically bolt** to a Class 300 flange $\implies$ **Tier-3 Mating Dimension Mismatch**. If evaluating unattached raw forgings, or if spool transition adapters are engineered, this is categorized as **Tier-2 Substitute** (`requires_hitl = True`, verification badge: `[PRESSURE UPGRADE: Class 300 -> Class 600 (Flange Mating Verification Mandatory)]`).
- **ASME B16.34 Standard Class vs. Special Class:**
  Special Class valves (with non-destructive examination NDE per ASME B16.34 Annex B) can replace Standard Class valves, but Standard Class cannot substitute for Special Class under severe pressure/temperature transients.

---

#### Module 2: ASTM Metallurgy Directed Acyclic Graph & High-Temperature Creep
Safe upgrades flow in a strict directed acyclic graph (DAG) representing corrosion resistance, yield strength, and temperature capabilities:

```
Carbon Steel (A105 / A216 WCB / A106-B)
       |
       +---> Low-Temp Carbon Steel (A350 LF2 / A352 LCB / A333-6) [-46°C Charpy Impact Tested]
       |            |
       |            +---> Austenitic Stainless Steel (A182 F304 / A351 CF8 / A312 TP304)
       |                         |
       |                         +---> Molybdenum Stainless Steel (A182 F316 / A351 CF8M / A312 TP316)
       |                                      |
       |                                      +---> Duplex Stainless Steel 2205 (A182 F51 / A815 S31803)
       |                                                   |
       |                                                   +---> Super Duplex Stainless 2507 (A182 F53 / A815 S32750)
       |                                                                |
       |                                                                +---> Nickel Alloys (Inconel 625 / Hastelloy C-276)
```

**Chrome-Molybdenum High-Temperature Creep Steels (FCCU / Hydrocracker / Coker Units):**
```
Carbon Steel (A105) ---> 1.25Cr-0.5Mo (A182 F11 / A217 WC6) ---> 2.25Cr-1Mo (A182 F22 / A217 WC9) ---> 5Cr-0.5Mo (F5 / C5) ---> 9Cr-1Mo-V (A182 F91 / A217 C12A)
```

- **Downgrade Prohibition:** Downward movement in the hierarchy (e.g., replacing SS316 with Carbon Steel A105) is blocked as a fatal corrosion failure trap (**Tier-3 Incompatible**).
- **Cryogenic Safety Trap:** Replacing low-temp certified `ASTM A350 LF2` with standard `ASTM A105` is blocked as a **Tier-3 Cryogenic Brittle Fracture Trap** because standard A105 lacks impact toughness testing at $-46^\circ\text{C}$ and shatters under thermal shock.
- **Creep Range Invariant:** In delayed coker or hydrocracker furnace lines operating above $450^\circ\text{C}$, substituting Cr-Mo alloy steel (F11/F22) with standard carbon steel (A105) is blocked as a **Tier-3 Creep Rupture Trap** (graphitization and accelerated creep void growth).
- **Intergranular Corrosion Trap (Sensitization):** In nitric/polythionic acid duty, standard carbon grades (SS304/SS316 with $C \le 0.08\%$) cannot substitute for low-carbon stabilized grades (`304L`, `316L`, `SS321`, `SS347`) $\to$ **Tier-3 Intergranular Stress Corrosion Cracking Trap**.

---

#### Module 3: ASME B36.10M / B36.19M Pipe Schedules & Wall Thickness Invariants
- **Schedule Ladder:** `SCH 5 < SCH 10 < SCH 20 < SCH 30 < STD / SCH 40 < SCH 60 < XS / SCH 80 < SCH 100 < SCH 120 < SCH 140 < SCH 160 < XXS`.
- **Down-Schedule Prohibition (Burst Hazard):** Candidate pipe with thinner nominal wall thickness ($t_{nom}$) than required by the process piping schedule is rejected as **Tier-3 Incompatible**.
- **Schedule Upgrade Permitted:** Upgrading to a heavier schedule (e.g., Sch 40 $\to$ Sch 80) is permitted as a **Tier-2 Substitute** (`requires_hitl = True`, checking flow reduction vs. pressure safety).
- **Stainless Pipe Schedule Mismatch:** Carbon steel pipe schedules (ASME B36.10M) and stainless steel schedules (ASME B36.19M, designated with suffix 'S', e.g., Sch 10S, Sch 40S, Sch 80S) differ in wall thicknesses above NPS 12. Cross-matching without thickness verification is blocked.

---

#### Module 4: NACE MR0175 / ISO 15156 Sour Service & ASME B16.47 Large Flanges
- **Sour Service Invariant (NACE MR0175 / ISO 15156):**
  If process medium contains wet hydrogen sulfide ($H_2S$) exceeding NACE partial pressure limits:
  - Material must be NACE compliant (hardness strictly $\le 22\text{ HRC}$ for carbon steels, heat-treated, certified resistance to Sulfide Stress Cracking - SSC and Hydrogen-Induced Cracking - HIC).
  - Supplying commercial non-NACE material is blocked as **Tier-3 Incompatible** (catastrophic sulfide stress cracking blowout).
- **ASME B16.47 Large Diameter Flanges (NPS 26 to NPS 60):**
  - **Series A (MSS SP-44):** Thicker, heavier flanges with larger bolt diameters and fewer bolt holes, designed for general pipeline and plant piping.
  - **Series B (API 605):** Thinner, lighter flanges with smaller bolt diameters and more bolt holes, originally designed for compact equipment nozzles.
  - **Series Incompatibility Invariant:** Series A and Series B flanges **cannot bolt together** due to completely different bolt circle diameters (BCD) and hole patterns. Any Series A vs. Series B substitution is strictly blocked as **Tier-3 Incompatible**.

---

#### Module 5: Valve Standards, Trim Ladders & Fire-Safe Certification
- **API 600 Steel Gate Valve Trim Ladder:**
  Trim numbers define the metallurgy of the valve stem, disc seating surface, and body seat rings:
  - `Trim 1:` 410 Stainless Steel (13% Cr) - Standard utility service.
  - `Trim 5:` Full Stellite (Hardfaced Co-Cr-A) - Severe high-pressure/temp erosive service.
  - `Trim 8:` 410 + Stellite Hardface (Universal refinery standard trim).
  - `Trim 12:` 316 + Stellite Hardface - Corrosive sour service.
  - `Trim 16:` Monel - Hydrofluoric acid (HF) alkylation service.
  - **Trim Downgrade Trap:** Demoting a Trim 5 or Trim 8 valve to Trim 1 in abrasive/erosive catalytic cracking slurry is blocked as a **Tier-3 Rapid Seat Washout Trap**.
- **API 6D Pipeline Valves - Piggability Invariant:**
  - **Full Bore (FB) vs. Reduced Bore (RB):** In pipeline transmission manifolds, substituting a Reduced Bore valve into an operational pipeline requiring PIG scraping is blocked as a **Tier-3 Pipeline PIG Blockage Trap**.
- **API 607 / API 6FA / ISO 10497 Fire-Safe Certification:**
  - In hydrocarbon service handling flammables, valves must carry fire-safe testing certification (retaining seal integrity after 30 minutes at $750^\circ\text{C}-1000^\circ\text{C}$).
  - Proposing a non-fire-tested soft-seated valve with standard virgin PTFE seats is blocked as a **Tier-3 Hydrocarbon Fire Disaster Trap**.
- **API 609 Butterfly Valves (Category A vs. Category B):**
  - Category A: Concentric resilient-seated (rubber lined) valves limited to low-pressure utility water/air ($\le 150\#, \le 120^\circ\text{C}$).
  - Category B: Double-offset / Triple-offset high-performance metal-to-metal valves for refinery process lines.
  - Category A substituted into Category B duty is strictly blocked as a **Tier-3 Elastomer Blowout Trap**.
- **API 594 Check Valves (Dual Plate vs. Swing):**
  - Retainerless design verification: In toxic / volatile organic compound (VOC) service, through-hole pin retainers risk fugitive pin leaks; retainerless design is mandatory.
- **API 520 / API 526 Pressure Safety Relief Valves (PSV):**
  - Orifice Area Invariant: Standardized letter designations (`D, E, F, G, H, J, K, L, M, N, P, Q, R, T`). Substituting a smaller orifice area (e.g. Orifice D for Orifice F) or lower Cold Differential Test Pressure (CDTP) is blocked as a **Tier-3 Overpressure Vessel Detonation Trap**.

---

#### Module 6: Forged & Buttweld Piping Fittings (ASME B16.9 / B16.11 / MSS SP-97 / MSS SP-75)
- **ASME B16.11 Forged Steel High-Pressure Fittings:**
  - Threaded Ratings: `2000# < 3000# < 6000#`.
  - Socket-Weld Ratings: `3000# < 6000# < 9000#`.
  - Substituting Class 2000# or 3000# for a 6000# specification is blocked as **Tier-3 Incompatible**.
- **ASME B16.9 Buttweld Fittings (Elbows, Tees, Reducers):**
  - **Long Radius (LR, $R = 1.5D$) vs. Short Radius (SR, $R = 1.0D$):** Short radius elbows create high pressure drops and block pigging tools. Proposing SR for LR in piggable lines is blocked as a **Tier-3 Restriction Trap**.
- **MSS SP-97 Integrally Reinforced Branch Outlets (Olets):**
  - Weldolet, Sockolet, Threadolet, Elbolet, Latrolet: Must match header pipe run size and branch schedule wall thickness to maintain structural branch reinforcement per ASME B31.3 Section 304.3.
- **MSS SP-75 / API 5L High-Test Pipeline Fittings:**
  - High-yield pipeline fittings (`WPHY 42, 52, 60, 65, 70`): Cannot be downgraded to standard low-yield A234 WPB in cross-country transmission gas grids.

---

#### Module 7: Flange Facings, Serrations & Joint Mechanical Invariants
- **Facing Geometry Compatibility (ASME B16.5):**
  - `RF` (Raised Face) $\leftrightarrow$ `RF`: Compatible.
  - `RTJ` (Ring Type Joint) $\leftrightarrow$ `RTJ`: Compatible.
  - `RF` $\leftrightarrow$ `RTJ`: **Strictly Incompatible (Tier-3)**. An RF flange cannot compress or seal inside an RTJ ring groove.
  - `TG` (Tongue & Groove) and `FM` (Face to Male/Female): Must pair strictly with their corresponding female/groove mating flange.
- **Cast Iron Equipment Flange Invariant (Flat Face vs. Raised Face):**
  - Cast iron pumps and valves (ASTM A126 Class B) carry Flat Face (FF) flanges.
  - Bolting a Raised Face (RF) steel flange to a Flat Face (FF) cast iron flange concentrates bolt loads on the raised face, creating excessive bending moments that crack the brittle cast iron flange ear.
  - Any RF-to-FF connection on brittle cast iron bodies is blocked as a **Tier-3 Flange Fracture Trap** (ASME B31.3 Section 312.2).
- **Flange Serration Surface Finish (MSS SP-6 / ASME B16.5):**
  - Standard Spiral / Concentric Serrated: $Ra = 3.2 - 6.3\ \mu\text{m}$ ($125 - 250\ \mu\text{in}$ AARH) required for flexible graphite and spiral wound gaskets.
  - Smooth Finish: $Ra = 1.6 - 3.2\ \mu\text{m}$ required for solid PTFE sheet gaskets. Mismatch leads to gasket creep or blowout.
- **Flange Attachment Type (Weld Neck vs. Slip-On):**
  - Weld Neck (WN) carries full-penetration butt-weld with smooth stress transition.
  - Slip-On (SO) has fillet welds with sharp stress concentration corners.
  - In ASME B31.3 **Severe Cyclic Conditions** or cryogenic service, Slip-On flanges are statutorily prohibited. Substituting Slip-On for Weld Neck is blocked as a **Tier-3 Fatigue Fracture Trap**.

---

#### Module 8: Gaskets & Bolting Fasteners Integrity (ASME B16.20 / B16.21 / ASTM A193 / A194 / A320)
- **ASME B16.20 Spiral Wound Gaskets (SWG):**
  - **Inner Ring Mandate:** In ASME B16.5 Class 900+ flanges, in all PTFE-filled spiral wound gaskets, and in vacuum services, an internal solid metallic Inner Ring is mandatory to prevent inward radial buckling of windings into the pipe bore. Omission is blocked as a **Tier-3 Gasket Collapse Trap**.
  - **Filler Compatibility:** Flexible Graphite (rated to $650^\circ\text{C}$) cannot be substituted with PTFE (max operating limit $200^\circ\text{C}-260^\circ\text{C}$) in high-temp lines $\to$ **Tier-3 Gasket Melting / Creep Trap**.
- **ASME B16.20 Metallic Ring Joint Gaskets (RTJ):**
  - Octagonal (R) rings seal both flat and angled groove faces; Oval (R) rings seal older round-bottom grooves.
  - `RX` rings: Pressure-energized; interchangeable with standard R grooves.
  - `BX` rings: Specialized for API 6A ultra-high pressures (up to 15,000 PSI) with pressure venting passage; **cannot fit into standard ASME B16.5 R grooves**.
  - **Material Hardness Rule:** Gasket ring material must be softer than flange groove metal (e.g. Soft Iron $\le 90\text{ HRB}$, SS316 $\le 160\text{ HRB}$). Harder gasket metal indenting and damaging flange face grooves is blocked as a **Tier-3 Groove Galling Trap**.
- **ASTM A193 / A194 Stud Bolt and Nut Metallurgy:**
  - High-Temperature Alloy Bolting:
    - Stud: `ASTM A193 Gr. B7` (Cr-Mo quenched and tempered, up to $425^\circ\text{C}$).
    - Matching Nut: Must be `ASTM A194 Gr. 2H` (heavy hex).
    - High-Creep Duty: `ASTM A193 Gr. B16` ($450^\circ\text{C}-540^\circ\text{C}$) requires `ASTM A194 Gr. 7` (Mo alloy) or `Gr. 4` nuts.
    - Low-Temperature Duty: `ASTM A320 Gr. L7` ($-101^\circ\text{C}$) requires `ASTM A194 Gr. 7` nuts.
    - Sour Service (NACE MR0175): Standard B7 studs exceed 22 HRC and are prohibited in sour duty. Mandates `ASTM A193 Gr. B7M` studs ($\le 22\text{ HRC}$) paired with `ASTM A194 Gr. 2HM` nuts ($\le 22\text{ HRC}$), or `ASTM A320 Gr. L7M` / `Gr. 7M` for cryogenic sour duty.
    - **Nut Mismatch Trap:** Pairing low-carbon commercial mild steel nuts (e.g., Gr. 2 or commercial Class 4.6) with B7 alloy studs is blocked as a **Tier-3 Thread Shear / Bolt Blowout Trap**.
- **Fastener Coating Compatibility & Liquid Metal Embrittlement (LME):**
  - In services operating above $200^\circ\text{C}-250^\circ\text{C}$, Cadmium-plated and Zinc-plated / Galvanized high-strength alloy bolts are prohibited due to **Liquid Metal Embrittlement (LME)** cracking, where molten zinc/cadmium penetrates steel grain boundaries. High-temp bolting mandates uncoated bare, phosphated, or PTFE/Xylan-coated finishes.

---

#### Module 9: Process Piping Fluid Service Categories & Line Pipe (ASME B31.3 / API 5L)
- **ASME B31.3 Category M Fluid Service (Lethal / Toxic Duty):**
  - Applies to fluids where a single leak can cause serious irreversible harm or fatality (e.g., phosgene, hydrogen cyanide, wet chlorine, concentrated HF acid).
  - In Category M service: Threaded joints, socket-welded joints above NPS 2, and non-metallic seals are statutorily prohibited; 100% radiographic examination (RT) is mandatory.
  - Proposing non-Category M standard commercial components into Category M lines is blocked as a **Tier-3 Lethal Toxic Escape Trap**.
- **API 5L Line Pipe Product Specification Level (PSL 1 vs. PSL 2):**
  - PSL 1: Standard line pipe without mandatory fracture toughness testing.
  - PSL 2: Mandatory Charpy V-notch toughness testing, yield-to-tensile ratio ceiling ($\le 0.93$), strict maximum Carbon Equivalent ($CE_{IIW} \le 0.43$, $CE_{Pcm} \le 0.25$), and mandatory traceability.
  - In cross-country high-pressure gas pipelines governed by PNGRB / ASME B31.8, substituting PSL 1 pipe for PSL 2 is blocked as a **Tier-3 Brittle Pipeline Rupture Trap**.

---

#### Module 10: Instrumentation Small-Bore Tubing & Compression Fittings (ASTM A269)
- **Dimensional System Invariance (Fractional Imperial vs. Metric OD):**
  - Fractional imperial tubing: Measured by outside diameter in fractions of an inch ($1/4" = 6.35\text{ mm}$, $3/8" = 9.53\text{ mm}$, $1/2" = 12.7\text{ mm}$).
  - Metric tubing: Measured in true millimeters ($6\text{ mm}$, $8\text{ mm}$, $10\text{ mm}$, $12\text{ mm}$).
  - **Cross-Mating Hazard:** Mating a $12\text{ mm}$ compression tube fitting (Swagelok / Parker A-LOK) onto $1/2" (12.7\text{ mm})$ tubing results in under-swaging, or fitting $1/2"$ onto $12\text{ mm}$ leaves insufficient grip. Under high impulse pressures (up to 6,000 PSI), the tube violently blows out of the fitting $\to$ **Tier-3 Tube Blow-Off Disaster Trap**.
- **Metallurgical Hardness Differential Rule:**
  - Tube fitting ferrules must swage and coin into the instrument tube surface. The tubing must be fully annealed with maximum hardness $\le 90\text{ HRB}$ for austenitic stainless steel (ASTM A269 TP316L). Installing standard fittings on cold-drawn un-annealed high-hardness tubing ($> 90\text{ HRB}$) prevents ferrule coining and causes joint separation under vibration.

---

#### Module 11: Rotating & Electrical Equipment (IS/IEC 60079 / API 682 / ISO 15)
- **IS/IEC 60079 Flameproof Electric Motors:**
  - Hazardous Area Enclosure: `Ex d IIC T4 Gb` (flameproof, hydrogen/acetylene group IIC, max surface temp $135^\circ\text{C}$).
  - Non-Ex standard motor proposed for refinery hazardous Zone 1/2 $\to$ **Tier-3 Fatal Explosion Trap**.
  - Power Under-Rating: Proposing motor kW below pump rated power $\to$ **Tier-3 Overload Tripping Trap**.
  - Synchronous Speed / Pole Mismatch: Substituting a 2-pole (3000 RPM) motor for a 4-pole (1500 RPM) pump drive quadruples head and causes **Tier-3 Hydraulic Shock / Pump Casing Rupture**.
- **API 682 Mechanical Seals & Flush Piping Plans:**
  - Single unpressurized flush (`Plan 11`, `Plan 21`, `Plan 32`) vs. Dual pressurized barrier systems (`Plan 53A`, `Plan 53B`, `Plan 54`).
  - In toxic, carcinogenic (benzene), or light volatile hydrocarbon service ($< 0.4$ specific gravity), downgrading a dual pressurized barrier seal (Plan 53A) to an unpressurized single seal is blocked as a **Tier-3 Toxic Atmosphere Seal Blowout Trap**.
- **ISO 15 Rolling Element Bearings:**
  - Radial Internal Clearance: `C2 (tight) < CN (normal) < C3 (increased) < C4 (extra increased)`.
  - In high-temperature hydrocarbon pumps, operational heat transfer expands the shaft and inner ring. Replacing a `C3` clearance bearing with normal `CN` clearance eliminates radial running room, leading to thermal expansion lockup and **Tier-3 Bearing Seizure / Shaft Snap**.

---

#### Module 12: Heat Exchanger Bundles & Tubing (TEMA & ASME Section VIII Div 1/2)
- **TEMA Construction Classes:**
  - `TEMA R` (Severe petroleum refinery and processing duties) > `TEMA C` (General commercial process duties) > `TEMA B` (Chemical process service).
  - Class Downgrade Prohibition: Proposing a `TEMA C` or `TEMA B` exchanger bundle/shell for a refinery crude distillation or hydrotreater unit where `TEMA R` is specified is blocked as a **Tier-3 Heat Exchanger Premature Failure Trap** (insufficient tube sheet thickness, baffle clearance erosion, and corrosion allowances).
- **Seamless vs. Welded Heat Exchanger Tubing:**
  - High-pressure hydrogen, reboiler, and lethal process services specify seamless tubes (`ASTM A213` Ferritic/Austenitic Alloy Steel or `ASTM B111` Copper-Nickel).
  - Welded tubes (`ASTM A249` Welded Austenitic Stainless Steel) cannot be substituted for seamless tubes in critical heat exchangers $\to$ **Tier-3 Weld Seam Fatigue/Corrosion Rupture Trap**.
- **Wall Thickness Gauge (BWG) Rule:**
  - Birmingham Wire Gauge (BWG) tube specification defines Minimum Wall (MW) or Average Wall (AW).
  - Substituting Average Wall (AW) tubing when Minimum Wall (MW) is specified creates local under-gauge thin spots along the tube length, causing rapid external pressure collapse under shell-side pressure $\to$ **Tier-3 Tube Buckling / Shell-Side Blowout Trap**.
- **U-Bend Heat Treatment Invariant (TEMA R RCB-2.31):**
  - Austenitic stainless steel cold-formed U-tubes (`ASTM A688 TP304L/316L`) must be solution annealed in the bend area. Un-annealed cold-worked U-bends retain residual forming stress, precipitating **Tier-3 Chloride Stress Corrosion Cracking (Cl-SCC) in U-Bends**.

---

#### Module 13: Centrifugal Pumps & Critical Spare Internals (API 610 / ISO 13709)
- **Pump Mount Configuration Invariance (OH1 vs. OH2):**
  - `OH1`: Foot-mounted overhung single-stage pump (suitable only for ambient/low temperature).
  - `OH2`: Centerline-mounted overhung single-stage pump.
  - Thermal Expansion Invariant: For pumped hydrocarbons operating at temperatures $> 150^\circ\text{C}$, substituting an OH1 foot-mounted pump for an OH2 centerline-mounted pump is blocked as a **Tier-3 Thermal Shaft Misalignment / Mechanical Seal Destruction Trap** (casing thermal expansion lifts the shaft centerline, binding the coupling and rupturing seal faces).
- **API 610 Pump Material Classes:**
  - Metallurgy Hierarchy: `S-1 (Cast Iron)` < `S-3 (Carbon Steel)` < `S-5 (Carbon Steel / 12% Cr)` < `S-6 (Carbon Steel / 12% Cr sour)` < `C-6 (12% Cr full)` < `A-8 (SS316)` < `D-1 (Duplex 2205)` < `D-2 (Super Duplex 2507)`.
  - Downgrade Prohibition: In sour hydrocarbon or produced water service, substituting Class `S-6` or `A-8` with `S-1` (cast iron) or `S-3` (carbon steel) is blocked as a **Tier-3 Pump Casing Pinhole Erosion / Toxic Fluid Ejection Trap**.
- **Wear Ring Hardness Differential Rule:**
  - Per API 610 clause 6.7.2, mating rotating impeller wear rings and stationary casing wear rings must maintain a minimum hardness differential of **50 HB** (unless both rings are hardened austenitic stainless steels or non-metallic composite inserts).
  - Supplying equal-hardness spare wear rings of identical grade without coating is blocked as a **Tier-3 Galling Seizure / Rotor Lockup Trap**.

---

#### Module 14: Reciprocating & Centrifugal Compressors (API 618 / API 617 / API 692)
- **API 618 Reciprocating Compressor Cylinder Valves (Hoerbiger Type):**
  - Directional Valve Invariance: Suction valves open inward into cylinder; discharge valves open outward into discharge plenum.
  - Inverted Valve Installation Trap: Installing a discharge valve into a suction port prevents gas intake and triggers extreme re-compression heating, resulting in **Tier-3 Cylinder Head Detonation / Valve Cage Failure**.
- **API 617 Impeller & Shaft Metallurgy (NACE Sour Gas):**
  - In wet $\text{H}_2\text{S}$ gas compression, high-strength martensitic or precipitation-hardened steels (e.g. standard 17-4PH) without specialized heat treatment (`H1150M` double aging per NACE MR0175) suffer rapid sulfide stress cracking $\to$ **Tier-3 High-Speed Impeller Burst / Casing Destruction Trap**.
- **API 692 Dry Gas Seals (DGS) & Buffer Systems:**
  - In toxic, flammable, or high-pressure gas service, compressor shafts utilize Tandem Dry Gas Seals with an intermediate inert nitrogen buffer gas barrier.
  - Downgrading a tandem dry gas seal to a single seal or eliminating the nitrogen separation seal is blocked as a **Tier-3 Explosive Gas Escape / Compressor Bay Fire Trap**.

---

#### Module 15: Rupture Disks & Overpressure Protection (ASME Sec VIII / ISO 4126-2 / API 520)
- **Rupture Disk Type Invariance (Forward-Acting vs. Reverse Buckling):**
  - `Forward-Acting (Tension-Loaded):` Subject to fatigue; operating ratio limited to $70\text{--}80\%$ of stamped burst pressure.
  - `Reverse Buckling (Compression-Loaded):` Resists cyclic fatigue; operating ratio allowable up to $90\text{--}95\%$ of stamped burst pressure.
  - Reverse buckling disks cannot be replaced with tension-loaded forward-acting disks in pulsating process lines $\to$ **Tier-3 Premature Fatigue Rupture / Atmospheric Discharge Trap**.
- **Non-Fragmenting Disk Mandate Upstream of PSVs:**
  - Per ASME Section VIII Div 1 UG-127 and API 520, when a rupture disk is installed upstream of a Pressure Safety Valve (PSV) for isolation/corrosion protection, it must be certified **Non-Fragmenting** (e.g., cross-scored reverse buckling).
  - Installing a standard fragmenting rupture disk upstream of a PSV is blocked as a **Tier-3 PSV Nozzle Clogging / Catastrophic Vessel Overpressure Trap** (metal petals shear off upon burst and lodge in the PSV inlet nozzle, preventing valve lift).
- **Combination Capacity Factor ($K_v$):**
  - When pairing a rupture disk with a PSV, the certified derating factor ($K_v = 0.90$) must be applied. Uncertified disk-PSV combinations lacking national board certification are rejected.

---

#### Module 16: Positive Isolation Line Blinds & Spacers (ASME B16.48 / ASME B31.3)
- **Certified Blinds vs. Uncertified Field Fabrication:**
  - Positive isolation during maintenance shut-ins requires certified `ASME B16.48` Spectacle Blinds, Paddle Blinds (Spades), and Paddle Spacers manufactured to match line pressure classes (Class 150 to 2500).
  - Substituting shop-cut uncalculated flat carbon steel plate in place of an ASME B16.48 certified paddle blind is blocked as a **Tier-3 Positive Isolation Blowout Trap** (unreinforced flat plate yields plastically under line design pressure, releasing toxic hydrocarbons onto turnaround crews).
- **Spade vs. Spacer Identification Geometry:**
  - ASME B16.48 mandates distinctive external handle geometry:
    - `Paddle Spade (Blind):` Solid disk with solid rectangular handle.
    - `Paddle Spacer (Open):` Open bore with hole drilled through the handle.
  - Installing unmarked or reversed handles is flagged as a safety violation (**Tier-2 HITL Mandatory**) to prevent accidental pressurized line opening.

---

#### Module 17: Atmospheric & Low-Pressure Tank Storage Safety (API 2000 / API 650 / ISO 16852)
- **API 2000 Pressure-Vacuum Relief Valves (PVRV / Breather Valves):**
  - Out-breathing protects tank against overpressure during liquid filling and thermal solar heating; In-breathing protects tank against vacuum collapse during liquid pump-out and sudden rainstorm thermal quenching.
  - Sizing Under-Rating Prohibition: Proposing a PVRV with flow venting capacity ($Nm^3/hr$) below API 2000 calculated pump-out rate is blocked as a **Tier-3 Atmospheric Tank Vacuum Implosion Trap** (thin atmospheric tank shell collapses like an aluminum can).
- **ISO 16852 / EN 12874 Flame Arrestors & Detonation Arrestors:**
  - `End-of-Line Deflagration Arrestor:` Protects tank vents open directly to atmosphere against atmospheric flash ignition.
  - `In-Line Detonation Arrestor:` Specifically engineered with shock attenuation to quench supersonic flame fronts ($> 2,000\text{ m/s}$) in closed piping runs with high length-to-diameter ($L/D$) ratios.
  - Substituting an End-of-Line deflagration arrestor inside an in-line flare/vapor recovery header is blocked as a **Tier-3 Supersonic Flame Shock Penetration / Tank Farm Fire Trap**.

---

#### Module 18: Metallic Expansion Joints & Flexible Hoses (EJMA / ISO 10380 / BS 6501)
- **EJMA Expansion Joint Restraint Invariance (Tied vs. Unrestrained):**
  - `Tied Expansion Joints (Tie Rods / Limit Stops):` Contain full internal pressure thrust force ($F_{thrust} = P \times A_{bellows}$) while absorbing lateral deflection.
  - `Unrestrained Bellows:` Requires massive rigid main anchors to resist pressure thrust.
  - Restraint Removal Trap: Substituting an unrestrained bellows where tied expansion joints are specified is blocked as a **Tier-3 Pipe Anchor Shearing / Bellows Tensile Rupture Trap** (thousands of pounds of unrestrained hydrostatic thrust rip pipe guides and pull bellows apart).
- **ISO 10380 Corrugated Metal Hose Braid Integrity:**
  - Single-braided vs. Double-braided corrugated stainless steel hoses (`ASTM A240 316L/321`).
  - High-pressure pulsation applications requiring double-braided construction cannot be substituted with single-braided hoses $\to$ **Tier-3 Hose Braid Tensile Rupture Trap**.

---

#### Module 19: In-Line Strainers & Steam Trapping Systems (ASME B16.34 / ISO 6552)
- **Strainer Mesh Aperture Sizing Invariance:**
  - `Pump Suction Y-Strainers / Basket Strainers:` Fine mesh ($< 40\text{ mesh}$ / $< 400\,\mu\text{m}$) causes high differential pressure, starving pump suction below Net Positive Suction Head Required ($NPSH_r$) $\to$ **Tier-3 Pump Cavitation & Impeller Pitting Trap**.
  - `Compressor Suction & Mechanical Seal Flush Strainers:` Coarse mesh ($> 20\text{ mesh}$) allows pipe scale and abrasive particles into close-tolerance seal faces $\to$ **Tier-3 Mechanical Seal Scoring & Fluid Leakage Trap**.
- **Steam Trap Operating Mechanism & Backpressure Invariance:**
  - `Thermodynamic Disc Traps:` Fail if backpressure exceeds $80\%$ of inlet steam pressure; cannot be installed in high-backpressure closed condensate return systems.
  - `Inverted Bucket & Float & Thermostatic (F&T) Traps:` Continuous modulating condensate drainage.
  - Incompatible trap selection leading to condensate backup in main steam lines is blocked as a **Tier-3 Steam Line Water Hammer Pipe Rupture Trap**.

---

#### Module 20: Flange Insulation Kits & Cathodic Protection (NACE SP0286 / NACE SP0169)
- **Flange Insulation Kit (FIK) Gasket Configuration:**
  - `Type F (Raised Face Only):` Gasket fits inside bolt circle.
  - `Type E (Full Face):` Gasket outside diameter matches flange OD with bolt holes pre-punched.
  - `Type D (Ring Type Joint - RTJ):` Gasket fits octagonal RTJ groove.
  - Galvanic Bridging Trap: In buried or offshore seawater piping connecting dissimilar metals (e.g. Carbon Steel to Stainless Steel), installing a Type F kit instead of a Type E full-face kit allows conductive dirt, mud, or moisture to bridge the exposed outer flange gap, defeating cathodic isolation and precipitating **Tier-3 Accelerated Galvanic Perforation Trap**.
- **Dielectric Retainer Material Thermal Rating:**
  - Standard Phenolic retainers degrade above $100^\circ\text{C}$; high-temperature service requires `NEMA G10` (glass epoxy, up to $150^\circ\text{C}$) or `NEMA G11` (up to $180^\circ\text{C}$) with Spring-Energized PTFE or Inconel seals. Over-temperature degradation $\to$ **Tier-3 Dielectric Breakdown / Seal Fire Trap**.

---

#### Module 21: Thermal Insulation, CUI & Passive Fireproofing (ASTM C795 / ASTM C552 / API 936)
- **ASTM C795 Leachable Chloride Invariance (CUI Prevention):**
  - In petrochemical and offshore environments operating between $50^\circ\text{C}$ and $150^\circ\text{C}$, thermal insulation applied over austenitic stainless steel (`SS304/316`) or duplex alloys must strictly comply with `ASTM C795` (leachable chloride and fluoride ions chemically balanced by sodium silicate inhibitors per Dana test).
  - Substituting commercial-grade non-inhibited calcium silicate or mineral wool insulation is blocked as a **Tier-3 Chloride External Stress Corrosion Cracking (Cl-ESCC) / Pipe Perforation Trap**.
- **ASTM C552 Cellular Glass for Cryogenic LNG / LPG Service:**
  - Cryogenic liquid piping ($-162^\circ\text{C}$ LNG / $-42^\circ\text{C}$ Propane) requires 100% closed-cell, completely non-absorbent cellular glass insulation.
  - Substituting permeable fibrous insulation on cryogenic lines allows atmospheric water vapor ingress, causing ice formation, volume expansion, and **Tier-3 Cryogenic Insulation Shattering / Heavy Boil-Off Loss**.

---

### Exhaustive Standards & Failure Invariants Matrix

| Standard | Scope & Equipment | Key Parameter Invariant | Failure Mode Prevented | Assigned Tier |
|---|---|---|---|---|
| **ASME B16.5** | Flanges (NPS 1/2 to 24) | Pressure Rating $\ge$ Required | Hydrostatic rupture / flange bolt yield | Tier-3 if down-rated |
| **ASME B16.47** | Large Flanges (NPS 26 to 60) | Series A vs. Series B parity | Bolt circle & hole pattern mismatch | Tier-3 if mismatched |
| **ASME B16.34** | Flanged & Welding Valves | P-T envelope / Wall thickness | Valve body shell rupture under pressure | Tier-3 if under-rated |
| **ASME B36.10M** | Carbon Steel Pipe Schedules | Schedule wall thickness $t_{nom}$ | Thin-wall pipe burst under hoop stress | Tier-3 if down-scheduled |
| **ASME B36.19M** | Stainless Steel Pipe Schedules | Schedule 'S' wall thickness | Vacuum collapse / pressure containment loss | Tier-3 if down-scheduled |
| **ASME B16.9** | Buttweld Fittings | Bend Radius $1.5D$ (LR) vs $1.0D$ (SR) | Pipeline scraper (PIG) stuck in line | Tier-3 if piggable |
| **ASME B16.11** | Forged SW & Screwed Fittings | Class 2000# vs 3000# vs 6000# | Socket-weld joint rupture under pressure | Tier-3 if down-rated |
| **ASME B16.20** | Spiral Wound Gaskets | Solid Inner Ring mandate | Inward radial winding buckling into bore | Tier-3 if omitted |
| **ASME B16.20** | RTJ Ring Joint Gaskets | Octagonal vs Oval; RX vs BX | Flange groove damage / seal leakage | Tier-3 if mismatched |
| **ASME B16.21** | Non-Metallic Flat Gaskets | Max operating temperature ($T_{max}$) | Elastomer/CNAF degradation and blowout | Tier-3 if over-temp |
| **ASME B31.3** | Process Piping (Refinery) | Category M Toxic Fluid Service | Lethal toxic atmospheric gas escape | Tier-3 if non-Cat M |
| **ASME B31.3** | Severe Cyclic Service | Weld Neck vs. Slip-On Flange | Fillet weld fatigue cracking | Tier-3 if Slip-On |
| **API 600** | Steel Gate Valves | Trim number metallurgy (1, 5, 8, 12) | Rapid seat washout in erosive slurry | Tier-3 if downgraded |
| **API 6D** | Pipeline Valves | Full Bore (FB) vs. Reduced Bore (RB) | PIG inspection tool trapped in pipeline | Tier-3 if FB required |
| **API 602** | Compact Steel Forged Valves | Pressure Class 800# / 1500# | High-pressure socket weld valve failure | Tier-3 if under-rated |
| **API 607** | Valve Fire Testing | Fire-Safe certified construction | Seat melting & hydrocarbon fire feeding | Tier-3 if non-fire-safe |
| **API 609** | Butterfly Valves | Category A vs. Category B (Offset) | Resilient liner blowout in process line | Tier-3 if Cat A in Cat B |
| **API 526** | Pressure Relief Valves | Relief Orifice Letter & CDTP | Vessel overpressure detonation | Tier-3 if undersized |
| **API 5L** | Line Pipe | PSL 1 vs. PSL 2 Quality Level | Brittle fracture in high-pressure gas grid | Tier-3 if PSL 1 in PSL 2 |
| **API 682** | Mechanical Seal Piping Plans | Plan 53A dual vs Plan 11 single | Carcinogenic benzene / VOC leakage | Tier-3 if downgraded |
| **ASTM A105** | Carbon Steel Forgings | Ambient service ($-29^\circ\text{C}$ to $425^\circ\text{C}$) | Brittle fracture if used at cryogenic temp | Tier-3 if in LF2 service |
| **ASTM A350** | Low-Temp Carbon Steel (LF2) | Charpy V-notch tested at $-46^\circ\text{C}$ | Low-temp ductile-to-brittle failure | Tier-2 upgrade over A105 |
| **ASTM A182** | Alloy & Stainless Forgings | F11, F22, F5, F91 Cr-Mo Steels | High-temp creep rupture in coker/FCCU | Tier-3 if carbon steel |
| **ASTM A182** | Stainless Forgings (F316/F316L) | Molybdenum $\ge 2.0\%$ for pitting | Acid corrosion & pipeline perforation | Tier-3 if carbon steel |
| **ASTM A193/A194** | High-Temp Studs & Nuts | Gr. B7 stud with Gr. 2H nut matching | Thread shear / bolt elongation blowout | Tier-3 if mismatched |
| **ASTM A320/A194** | Low-Temp Studs & Nuts | Gr. L7 stud with Gr. 7 nut ($-101^\circ\text{C}$) | Cryogenic brittle bolt fracture | Tier-3 if B7 in L7 duty |
| **ASTM A269** | Instrument Tubing | Fractional Imperial vs. Metric OD | Tubing compression ferrule blowout | Tier-3 if mismatched OD |
| **NACE MR0175** | Sour Hydrocarbon Service | Hardness $\le 22\text{ HRC}$, HIC/SSC test | Sulfide stress corrosion cracking rupture | Tier-3 if non-NACE |
| **IS/IEC 60079** | Hazardous Area Motors | Enclosure `Ex d IIC T4 Gb` | Electric spark igniting explosive vapor | Tier-3 if Non-Ex |
| **ISO 15** | Rolling Bearings | Radial Clearance C3 vs. CN | Shaft thermal expansion seizure | Tier-3 if CN in C3 duty |
| **TEMA Standards** | Heat Exchanger Shell & Bundles | TEMA Class R vs. C/B parity | Thin tube sheet erosion & premature failure | Tier-3 if downgraded |
| **ASTM A213/A249** | Heat Exchanger Tubes | Seamless (A213) vs. Welded (A249) | Longitudinal weld corrosion rupture | Tier-3 if welded for seamless |
| **API 610** | Centrifugal Process Pumps | Mounting OH1 (foot) vs. OH2 (center) | Thermal casing expansion shaft binding | Tier-3 if OH1 for OH2 ($>150^\circ\text{C}$) |
| **API 610** | Pump Spare Wear Rings | Minimum 50 HB hardness differential | Rotating/stationary ring galling seizure | Tier-3 if identical hardness |
| **API 618** | Reciprocating Compressors | Hoerbiger Suction vs. Discharge valves | Inverted valve cylinder head detonation | Tier-3 if mismatched |
| **API 692** | Dry Gas Seals (Compressors) | Tandem seal with N2 buffer vs single | Lethal toxic hydrocarbon gas escape | Tier-3 if single in toxic duty |
| **ISO 4126-2 / UG-127** | Rupture Disks (Bursting Disks) | Non-Fragmenting type upstream of PSV | Metal petals blocking safety valve nozzle | Tier-3 if fragmenting disk |
| **ASME B16.48** | Line Blinds & Spacers | Certified thickness vs. shop-cut plate | Positive isolation plate yield blowout | Tier-3 if shop-cut plate |
| **API 2000** | Storage Tank Venting & PVRVs | In-breathing flow capacity $\ge$ pump-out | Atmospheric tank vacuum shell collapse | Tier-3 if undersized |
| **ISO 16852** | Flame & Detonation Arrestors | In-line Detonation vs End-of-line Deflagration | Supersonic flame shock passing arrestor | Tier-3 if deflagration in-line |
| **EJMA Standards** | Metallic Expansion Joints | Tied (tie rods) vs. Unrestrained bellows | Pipe guide anchor shear / bellows blowout | Tier-3 if unrestrained |
| **NACE SP0286** | Flange Insulation Kits (FIK) | Type E (full face) vs Type F (raised) | Conductive dirt bridging & galvanic corrosion | Tier-3 if Type F on bimetallic |
| **ASTM C795** | Thermal Insulation over SS | Leachable Chlorides $<50\text{ ppm}$ + Inhibitor | Chloride external stress corrosion cracking | Tier-3 if non-ASTM C795 |
| **ASTM C552** | Cryogenic Cellular Glass | 100% closed-cell vapor impermeability | Water vapor ice-jacking & boil-off runaway | Tier-3 if permeable |

---

### 3.4 Stage 04: Neo4j Canonical Property Knowledge Graph & Pre-Purchase Radar

#### A. Neo4j Canonical Property Knowledge Graph Architecture (`seed_graph.py` & `queries.py`)

Rather than maintaining a passive taxonomy tree or attempting an unsustainable $O(N^2)$ part-to-part dense mesh, Neo4j implements a **Multi-Attribute Canonical Property Graph with Directed Compatibility Edges**. Parts connect to shared physical property nodes ($K \approx 6 \text{ to } 10$ properties depending on equipment family), and the property nodes hold the codified engineering safety relationships.

##### 1. Graph Schema Meta-Model ($K$-Attribute Star Graph)
```cypher
// 1. Enterprise & Holding Depot Nodes
(:CPSE {code: "IOCL", name: "Indian Oil Corporation Ltd"})
  -[:OPERATES]-> (:Depot {id: "DEPOT-IOCL-PNP", name: "Panipat Refinery", state: "Haryana", lat: 29.3909, lon: 76.9635})
  -[:HOLDS {available_qty: 12, days_idle: 180, po_no: "PO-IOCL-2025-88"}]-> (:InventoryItem {sku_code: "IOCL-VALVE-0041", status: "IDLE_SURPLUS"})

// 2. Physical Property Star Connections (Connected per Equipment Family, K = 6 to 10)
// Example: API 600 Gate Valve (K = 9 properties)
(:InventoryItem {sku_code: "IOCL-VALVE-0041"})
  -[:HAS_SIZE]-> (:Size {item_type: "GATE_VALVE", nps: "6 inch", dn_mm: 150})
  -[:HAS_PRESSURE_CLASS]-> (:PressureClass {class_rating: 300, pn_equivalent: 50})
  -[:HAS_BODY_METALLURGY]-> (:MaterialGrade {name: "ASTM A216 WCB", family: "CARBON_STEEL"})
  -[:HAS_TRIM]-> (:ValveTrim {trim_no: 8, stem: "13Cr", seat_surface: "Stellite Hardfaced", wedge_surface: "13Cr"})
  -[:HAS_PORT_BORE]-> (:PortBore {type: "FULL_BORE", is_piggable: true})
  -[:HAS_FACING]-> (:FlangeFacing {type: "RF", serration_ra_min: 3.2, serration_ra_max: 6.3})
  -[:HAS_END_CONNECTION]-> (:EndConnection {type: "FLANGED"})
  -[:HAS_FIRE_SAFE_RATING]-> (:FireSafeRating {standard: "API 607", certified: true})
  -[:HAS_OPERATOR]-> (:ValveOperator {type: "HANDWHEEL", is_actuator_ready: true})

// Example: API 5L / ASTM Line Pipe (K = 7 properties)
(:InventoryItem {sku_code: "BPCL-PIPE-0912"})
  -[:HAS_SIZE]-> (:Size {item_type: "PIPE", nps: "10 inch", od_mm: 273.0})
  -[:HAS_SCHEDULE]-> (:PipeSchedule {schedule_name: "SCH 40", wall_thickness_mm: 9.27})
  -[:HAS_PRESSURE_RATING]-> (:PressureRating {psi: 350, max_operating_bar: 24.1})
  -[:HAS_BODY_METALLURGY]-> (:MaterialGrade {name: "Galvanized Iron", family: "IRON"})
  -[:HAS_MANUFACTURING_METHOD]-> (:PipeMfgMethod {type: "SEAMLESS"})
  -[:HAS_END_PREP]-> (:EndPrep {type: "BE", description: "Beveled End"})
  -[:HAS_COATING]-> (:PipeCoating {type: "GALVANIZED"})

// 3. Taxonomy Connections (Standard GeM & UNSPSC Taxonomies)
(:InventoryItem)-[:STANDARDIZED_AS {verified_by: "HUMAN_EXPERT"}]-> (:CanonicalMaterial {canonical_id: "CAN-000041"})
  -[:CLASSIFIED_UNDER]-> (:GeMCategory {code: "GEM-CAT-VALVE-GATE"})
  -[:MAPPED_TO]-> (:UNSPSCCommodity {code: "40141611", title: "Gate valves"})
```

##### 2. Inter-Property Directed Engineering Compatibility Edges (The In-Graph Rules Engine)
Every property node type holds pre-codified engineering safety relationships:
- **Dimensions & Size (`:Size`):**
  - Only connects via `[:EXACT_MATCH]` to identical dimensional nodes.
  - **Zero Cross-Size Edges:** A 10" node has **no relationship** to an 8" or 12" node. The graph topology physically enforces the **Dimensional Zero-Tolerance Invariant** because mismatched dimensions are disconnected in graph space.
- **Pressure Class & Rating (`:PressureClass` / `:PressureRating`):**
  - Exact match: `(:PressureClass {class_rating: 300})-[:EXACT_MATCH {score: 1.0}]->(:PressureClass {class_rating: 300})`
  - Safe Over-Rating (Directed Upgrade): `(:PressureClass {class_rating: 600})-[:SAFE_UPGRADE_FOR {score: 0.95}]->(:PressureClass {class_rating: 300})`
  - Down-Rating Prohibition: `Class 150` has **NO outgoing edge** to `Class 300`. Traversal from 300# can never reach 150#.
- **Body Metallurgy (`:MaterialGrade`):**
  - Codifies the ASTM Metallurgy DAG directly as directed graph edges:
    `(:MaterialGrade {name: "SS316"})-[:ALLOY_UPGRADE_FOR {score: 0.92}]->(:MaterialGrade {name: "SS304"})`
    `(:MaterialGrade {name: "SS304"})-[:ALLOY_UPGRADE_FOR {score: 0.85}]->(:MaterialGrade {name: "ASTM A105"})`
    `(:MaterialGrade {name: "Duplex 2205"})-[:ALLOY_UPGRADE_FOR {score: 0.95}]->(:MaterialGrade {name: "SS316"})`
- **Valve Trims (`:ValveTrim` per API 600):**
  - `(:ValveTrim {trim_no: 8})-[:TRIM_UPGRADE_FOR {score: 0.95}]->(:ValveTrim {trim_no: 1})` (Stellite hardfacing on seats upgrades standard 13Cr).
  - `(:ValveTrim {trim_no: 5})-[:TRIM_UPGRADE_FOR {score: 0.98}]->(:ValveTrim {trim_no: 8})` (Full Stellite trim upgrades Trim 8).
- **Port Bore (`:PortBore`):**
  - `(:PortBore {type: "FULL_BORE"})-[:PORT_UPGRADE_FOR]->(:PortBore {type: "REDUCED_BORE"})` (Full bore can replace reduced bore, but reduced bore cannot replace full bore on piggable pipelines).
- **Flange Facings & End Connections (`:FlangeFacing`, `:EndConnection`):**
  - `(:FlangeFacing {type: "RF"})-[:EXACT_MATCH]->(:FlangeFacing {type: "RF"})`
  - Incompatible connections (e.g. RF to RTJ) have no edge.

##### 3. High-Speed Sub-Millisecond Multi-Property Traversal Query
When a site engineer searches for a spare valve (e.g. `Gate Valve, 6", Class 150, WCB, Trim 1, Full Bore, RF`):
```cypher
// 1. Match searched target property nodes
MATCH (target_size:Size {item_type: "GATE_VALVE", nps: "6 inch"})
MATCH (target_class:PressureClass {class_rating: 150})
MATCH (target_body:MaterialGrade {name: "ASTM A216 WCB"})
MATCH (target_trim:ValveTrim {trim_no: 1})
MATCH (target_port:PortBore {type: "FULL_BORE"})
MATCH (target_facing:FlangeFacing {type: "RF"})

// 2. Traversal 1: Enforce exact dimension (Hard constraint: O(1) pointer jump)
MATCH (candidate:InventoryItem {status: "IDLE_SURPLUS"})-[:HAS_SIZE]->(target_size)

// 3. Traversal 2: Follow pressure compatibility edges (exact or safe upgrade)
MATCH (candidate)-[:HAS_PRESSURE_CLASS]->(p:PressureClass)
WHERE p = target_class OR (p)-[:SAFE_UPGRADE_FOR]->(target_class)

// 4. Traversal 3: Follow metallurgy compatibility edges (exact or safe alloy upgrade)
MATCH (candidate)-[:HAS_BODY_METALLURGY]->(m:MaterialGrade)
WHERE m = target_body OR (m)-[:ALLOY_UPGRADE_FOR]->(target_body)

// 5. Traversal 4: Follow trim compatibility (exact or superior hardfaced trim)
MATCH (candidate)-[:HAS_TRIM]->(t:ValveTrim)
WHERE t = target_trim OR (t)-[:TRIM_UPGRADE_FOR]->(target_trim)

// 6. Traversal 5: Follow port bore compatibility (Full bore requirement)
MATCH (candidate)-[:HAS_PORT_BORE]->(pb:PortBore)
WHERE pb = target_port OR (pb)-[:PORT_UPGRADE_FOR]->(target_port)

// 7. Traversal 6: Follow facing compatibility
MATCH (candidate)-[:HAS_FACING]->(f:FlangeFacing)
WHERE f = target_facing

// 8. Connect to holding depot for logistics evaluation
MATCH (depot:Depot)-[:HOLDS]->(candidate)
MATCH (cpse:CPSE)-[:OPERATES]->(depot)

// 9. Path-Derived Runtime Dynamic Tier Assignment
RETURN candidate.sku_code AS sku,
       cpse.code AS cpse,
       depot.id AS depot_id,
       depot.name AS depot_name,
       depot.lat AS lat,
       depot.lon AS lon,
       candidate.available_qty AS qty,
       candidate.days_idle AS days_idle,
       p.class_rating AS candidate_class,
       t.trim_no AS candidate_trim_no,
       CASE 
         WHEN p = target_class AND m = target_body AND t = target_trim AND pb = target_port AND f = target_facing THEN "TIER_1_IDENTICAL"
         ELSE "TIER_2_SUBSTITUTE"
       END AS dynamic_tier,
       CASE
         WHEN p = target_class AND m = target_body AND t = target_trim AND pb = target_port AND f = target_facing THEN 0.98
         ELSE 0.88
       END AS path_compatibility_score
ORDER BY dynamic_tier ASC, candidate.days_idle DESC;
```

##### 4. Mathematical Complexity: Why Property Stars Scale as $O(K \times N)$
1. **The Dense Part-to-Part Pitfall ($O(N^2)$):**
   If 100,000 inventory items connect directly to each other:
   $$\text{Total Edges} = \frac{N(N - 1)}{2} = \frac{100,000 \times 99,999}{2} \approx \mathbf{5,000,000,000\text{ edges (5 Billion)}}$$
   Storing 5 billion edges would crash graph RAM and make real-time updates impossible.
2. **The Canonical Property Star Solution ($O(K \times N)$):**
   By routing each part to its $K$ property nodes (where $K \approx 6 \text{ to } 10$ depending on whether it is a pipe, flange, valve, or pump):
   $$\text{Total Edges} = K \times N \approx 8 \times 100,000 = \mathbf{800,000\text{ edges}}$$
   800,000 edges require less than **100 MB of RAM** in Neo4j, enabling full graph traversals in **$< 2\text{ ms}$**.
3. **Deterministic Hard Safety Gating in Graph Space:**
   Dimensional mismatches and pressure down-ratings are mathematically unreachable because **no edges exist** in the graph. The traversal engine simply returns 0 matches for invalid candidates without burning CPU cycles on ML models.
4. **Transparent Path Provenance:**
   The graph query path itself explains *why* the part is Tier 1 or Tier 2: `(Candidate) -> (Class 600#) -[:SAFE_UPGRADE_FOR]-> (Class 300#)`.

#### B. Attribute-Level Privacy Enforcement (Strict SIH Compliance)
- **Private Intranet View (Own Facility):** Plant engineers and stores managers see internal commercial pricing, purchase order values, and vendor details for their own inventory.
- **Federated Cross-CPSE Search (Sister Facilities):** When an engineer at IOCL Panipat queries the surplus radar, the API strictly strips out:
  - $\times$ Unit purchase price in INR
  - $\times$ Total valuation in INR
  - $\times$ Vendor / supplier identification
  - $\times$ Commercial contract terms
- **What is Shared Across CPSEs:**
  - $\checkmark$ Standardized physical specifications (Item Type, Size, Pressure Class, Metallurgy, Schedule, Standards)
  - $\checkmark$ Available surplus quantity
  - $\checkmark$ Holding depot location & CPSE enterprise name
  - $\checkmark$ Number of days sitting dormant (idle duration)
  - $\checkmark$ Physical inspection compliance (MTC 3.1, NACE MR0175, Fire-Safe API 607)

#### C. Central Plant Inventory Lifecycle
Every inventory asset moves through a well-defined lifecycle:
```
Inward Bill & MTC OCR
         |
         v
[Site Engineer Review (/upload/review)]
         |
         +--------------------------------+
         |                                |
         v                                v
(TO_BE_CONSUMED)                   (IN_STORAGE)
Allocated for turnaround;          Buffer warehouse stock;
Private to facility.               Internal plant reserve.
         |                                |
         | (Unconsumed after 90 days)     | (Marked as dormant)
         +--------------------------------+
                         |
                         v
                  (IDLE_SURPLUS)
         *Mirrored to Neo4j Graph*
   *Broadcasted on Live Pre-Purchase Radar*
                         |
           +-------------+-------------+
           |                           |
           v                           v
   (RESERVED_TRANSFER)             (CONSUMED)
Locked for Inter-CPSE Requisition  Installed in refinery unit;
Atomic reservation active.         Permanently archived.
```

#### D. GIS Multi-Depot Logistics Engine (`logistics.py`)
1. **Geographic Registry:** Coordinates for 19 key petroleum assets across 5 CPSEs:
   - IOCL: Panipat (HR), Mathura (UP), Koyali (GJ), Paradip (OD), Barauni (BR), Guwahati (AS), Digboi (AS).
   - ONGC: Hazira (GJ), Ankleshwar (GJ), Uran (MH), Mumbai High Base (MH), Rajahmundry (AP).
   - BPCL: Mumbai Mahul (MH), Kochi (KL), Bina (MP).
   - HPCL: Mumbai (MH), Visakh (AP).
   - GAIL: Pata (UP), Vijaipur (MP).
2. **Distance & Route Calculations:**
   - Great-circle geodesic distance ($d$) computed via the Haversine formula.
   - Commercial road transit distance: $D_{\text{road}} = d \times 1.28$ (accounting for Indian national highway network tortuosity).
   - Transit lead time: Based on average commercial freight speeds (35–45 km/h) plus statutory state border & terminal inspection windows.
   - Rail / Road freight cost: Based on Container Corporation of India (CONCOR) freight tariff schedules.
   - Environmental metric: Computes avoided $CO_2$ emissions versus foreign overseas air/sea imports.

#### E. Statutory CISF Digital Material Gate Pass
- Outward movement from any refinery or gas plant requires statutory clearance by the **Central Industrial Security Force (CISF)**.
- When a supplying facility confirms supply, the system issues an official **CISF Electronic Material Gate Pass** featuring:
   - Statutory serial number: `OGP-2026-[DEPOT]-081-[SERIAL]`.
   - Non-Returnable Outward Inter-CPSE pass designation.
   - Assigned vehicle number, driver name, and commercial driver's license number.
   - GST E-Way bill number.
   - Cryptographic SHA-256 seal computed over vehicle, consignment, and officer attributes.
   - Self-contained SVG QR code with embedded cryptographic verification URL.
   - Print-optimized stylesheet (`@media print`) enabling 1-click high-resolution printing for CISF perimeter security gates.

---

### 3.5 Stage 05: Sovereign Audit Ledger & Active Learning Dynamic Reranker

#### A. CVC / CAG Compliance Audit Ledger (`audit.py`)
- In compliance with Department of Public Enterprises (DPE) and Central Vigilance Commission (CVC) guidelines:
  - Every action (`INWARD_PROCUREMENT`, `LIFECYCLE_TRANSITION`, `REQUISITION_INITIATED`, `SUPPLY_CONFIRMED`, `GATE_PASS_ISSUED`, `DELIVERY_VERIFIED`) writes an immutable row into the database.
  - Each entry generates a cryptographically chained SHA-256 digital signature:
    $$\text{Hash}_i = \text{SHA256}\big(\text{prev\_hash}_{i-1} \parallel \text{LogID} \parallel \text{Timestamp} \parallel \text{Actor} \parallel \text{Action} \parallel \text{RefID} \parallel \text{Details}\big)$$
    For the genesis entry, $\text{prev\_hash}_0$ defaults to a fixed root constant (`GENESIS_ROOT_64_HEX`). This creates a mathematically tamper-evident hash chain: retroactively deleting, altering, or re-ordering any historical row breaks all subsequent hash seals.
  - Any user can click "Verify Seal" to trigger an on-the-fly recursive recomputation across the chain, validating that the audit trail has not been tampered with.

#### B. Active Learning Feedback Cache & Online Dynamic Reranker (`active_learning.py`)
- Rebuilding must eliminate the need for periodic batch retraining for human feedback.
- When an authorized engineer or vigilance committee approves or rejects an ambiguous match in the HITL triage queue:
  1. The decision is recorded in the `ActiveLearningCache` (dual-indexed by query text and source SKU).
  2. The record is persisted to the `active_learning_feedback` database table.
  3. Subsequent vector search queries for that item check the cache in $< 1$ ms:
     - **Approved Matches:** Score boosted to $\ge 0.95$, rank elevated to #1, stamped with `[VERIFIED BY HUMAN EXPERT]`.
     - **Rejected Matches:** Immediately demoted to **Tier-3 Incompatible**, compatibility set to `False`, stamped with `[REJECTED BY HUMAN EXPERT]`.

---

## 4. Target Data Contracts & Schemas

### 4.1 Database Entity-Relationship Diagram (PostgreSQL)

```sql
-- 1. Ingested Document Metadata Table
CREATE TABLE ingested_documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    doc_type VARCHAR(64) NOT NULL, -- MTC_CERTIFICATE, DELIVERY_CHALLAN, PO_INVOICE
    is_scanned BOOLEAN DEFAULT FALSE,
    confidence NUMERIC(5, 4) NOT NULL,
    raw_text TEXT,
    parsed_metadata JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Plant Inventory Ledger Table
CREATE TABLE inventory_items (
    id SERIAL PRIMARY KEY,
    sku_code VARCHAR(64) UNIQUE NOT NULL,
    cpse VARCHAR(32) NOT NULL, -- IOCL, ONGC, BPCL, HPCL, GAIL
    depot_id VARCHAR(64) NOT NULL,
    depot_location VARCHAR(255) NOT NULL,
    po_no VARCHAR(128),
    heat_no VARCHAR(128),
    description TEXT NOT NULL,
    canonical_id VARCHAR(64),
    item_type VARCHAR(64) NOT NULL,
    size_nb_mm NUMERIC(8, 2),
    pressure_class INTEGER,               -- ASME Class (e.g. 150, 300, 600)
    pressure_rating_psi NUMERIC(10, 2),   -- Operating PSI rating for pipes/tubing
    schedule VARCHAR(32),                 -- Pipe schedule (e.g. SCH 40, SCH 80, SCH 160)
    metallurgy VARCHAR(64),
    facing_end VARCHAR(32),
    standard VARCHAR(64),
    properties JSONB DEFAULT '{}',        -- Equipment-specific specs (trim_no, port_bore, seal_plan, ex_class)
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    unit_cost_inr NUMERIC(14, 2) NOT NULL,
    total_value_inr NUMERIC(14, 2) GENERATED ALWAYS AS (quantity * unit_cost_inr) STORED,
    status VARCHAR(32) NOT NULL DEFAULT 'TO_BE_CONSUMED', -- TO_BE_CONSUMED, IN_STORAGE, IDLE_SURPLUS, RESERVED_TRANSFER, CONSUMED
    days_idle INTEGER DEFAULT 0,
    source_document_id INTEGER REFERENCES ingested_documents(id),
    is_broadcasted_surplus BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Inter-CPSE Requisition & Transfer Orders
CREATE TABLE requisitions (
    requisition_id VARCHAR(64) PRIMARY KEY,
    source_cpse VARCHAR(32) NOT NULL,     -- Requesting enterprise
    source_depot VARCHAR(255) NOT NULL,   -- Requesting plant / depot
    source_unit VARCHAR(128) NOT NULL,
    target_cpse VARCHAR(32) NOT NULL,     -- Supplying enterprise
    target_depot VARCHAR(255) NOT NULL,   -- Supplying surplus depot
    sku_code VARCHAR(64) NOT NULL REFERENCES inventory_items(sku_code),
    item_description TEXT NOT NULL,
    required_qty INTEGER NOT NULL CHECK (required_qty > 0),
    unit_cost_inr NUMERIC(14, 2) NOT NULL,
    total_value_inr NUMERIC(14, 2) NOT NULL,
    justification TEXT NOT NULL,
    urgency_level VARCHAR(32) NOT NULL,   -- EMERGENCY_SHUTDOWN, PLANNED_MAINTENANCE, ROUTINE
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING_APPROVAL', -- PENDING_APPROVAL, APPROVED_FOR_DISPATCH, IN_TRANSIT, DELIVERED, REJECTED
    requested_by VARCHAR(128) NOT NULL,
    approved_by VARCHAR(128),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    dispatch_timestamp TIMESTAMP WITH TIME ZONE,
    delivery_timestamp TIMESTAMP WITH TIME ZONE,
    audit_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Atomic Multi-Depot Inventory Reservation Locks
CREATE TABLE inventory_locks (
    id SERIAL PRIMARY KEY,
    sku_code VARCHAR(64) NOT NULL REFERENCES inventory_items(sku_code),
    requisition_id VARCHAR(64) NOT NULL REFERENCES requisitions(requisition_id),
    locked_qty INTEGER NOT NULL CHECK (locked_qty > 0),
    locked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- 5. Digital Material Gate Passes
CREATE TABLE digital_gate_passes (
    gate_pass_no VARCHAR(64) PRIMARY KEY,
    requisition_id VARCHAR(64) NOT NULL REFERENCES requisitions(requisition_id),
    issuing_cpse VARCHAR(32) NOT NULL,
    issuing_depot VARCHAR(255) NOT NULL,
    receiving_cpse VARCHAR(32) NOT NULL,
    receiving_depot VARCHAR(255) NOT NULL,
    transporter_name VARCHAR(128) NOT NULL,
    vehicle_no VARCHAR(32) NOT NULL,
    driver_name VARCHAR(128) NOT NULL,
    driver_id_no VARCHAR(64) NOT NULL,
    gst_eway_bill_no VARCHAR(64) NOT NULL,
    cisf_verification_seal VARCHAR(128) NOT NULL,
    issue_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sha256_hash VARCHAR(64) NOT NULL,
    transit_distance_km NUMERIC(10, 2) NOT NULL,
    co2_saved_kg NUMERIC(10, 2) NOT NULL,
    estimated_transit_hours INTEGER NOT NULL,
    qr_code_svg TEXT NOT NULL
);

-- 6. Sovereign CVC/CAG Audit Ledger (Cryptographic Blockchain)
CREATE TABLE sovereign_audit_ledger (
    log_id VARCHAR(64) PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    action_category VARCHAR(64) NOT NULL,
    action_name VARCHAR(128) NOT NULL,
    actor_name VARCHAR(128) NOT NULL,
    actor_role VARCHAR(128) NOT NULL,
    cpse VARCHAR(32) NOT NULL,
    depot VARCHAR(255) NOT NULL,
    reference_id VARCHAR(128) NOT NULL,
    details TEXT NOT NULL,
    prev_hash VARCHAR(64) NOT NULL,       -- Chained parent hash (GENESIS_ROOT for initial row)
    sha256_hash VARCHAR(64) NOT NULL,     -- Tamper-evident seal: SHA256(prev_hash || log_id || details)
    is_verified BOOLEAN DEFAULT TRUE
);

-- 7. Active Learning Feedback Cache Table
CREATE TABLE active_learning_feedback (
    id SERIAL PRIMARY KEY,
    source_description TEXT NOT NULL,
    source_sku VARCHAR(64) NOT NULL,
    canonical_id VARCHAR(64) NOT NULL,
    decision VARCHAR(16) NOT NULL, -- APPROVE, REJECT, RECLASSIFY
    officer VARCHAR(128) NOT NULL,
    action_note TEXT,
    tier_override VARCHAR(32),
    confidence_override NUMERIC(5, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 Core Pydantic OpenAPI Contracts (Dynamic Per-Part Matching)

```python
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DynamicCompatibilityTier(str, Enum):
    TIER_1_IDENTICAL = "TIER_1_IDENTICAL"       # >= 95% Compatibility, identical dims & metallurgy, plug-and-play
    TIER_2_SUBSTITUTE = "TIER_2_SUBSTITUTE"     # 80% - 94% Compatibility, safe upgrade, requires HITL review
    TIER_3_INCOMPATIBLE = "TIER_3_INCOMPATIBLE" # < 80% Compatibility OR zero-tolerance invariant violated

class PhysicalAttributes(BaseModel):
    item_type: str = Field(..., description="e.g. FLANGE, GATE_VALVE, PIPE, PUMP, TUBE")
    size_nb_mm: Optional[float] = Field(None, description="Nominal bore in mm (e.g. 100.0 for 4\")")
    pressure_class: Optional[int] = Field(None, description="ASME pressure class (e.g. 150, 300, 600)")
    schedule: Optional[str] = Field(None, description="Pipe schedule (e.g. SCH 40, SCH 80, SCH 160)")
    metallurgy: Optional[str] = Field(None, description="Material grade (e.g. ASTM A105, A182 F316L)")
    facing_end: Optional[str] = Field(None, description="e.g. RF, RTJ, FF, BW, SW")
    standard: Optional[str] = Field(None, description="e.g. ASME B16.5, API 600, ASTM A269")

class MatchRequest(BaseModel):
    query_text: Optional[str] = Field(None, description="Free-form engineer search prompt")
    source_sku: Optional[str] = Field(None, description="Known SKU being replaced")
    source_attributes: Optional[PhysicalAttributes] = Field(None, description="Explicit searched attributes")
    requesting_depot_id: Optional[str] = Field(None, description="Current depot ID of requesting engineer for GIS transit distance calculation")
    target_depots: Optional[List[str]] = Field(None, description="Filter candidate search radius")
    top_k: int = Field(default=10, ge=1, le=50)

class PropertyEvaluationStatus(str, Enum):
    IDENTICAL = "IDENTICAL"                 # 100% exact parity (Tier 1)
    SAFE_UPGRADE = "SAFE_UPGRADE"           # Exceeds spec safely (Tier 1 or Tier 2, e.g. 350 PSI >= 300 PSI)
    ADAPTABLE = "ADAPTABLE"                 # Minor variance requiring HITL (Tier 2)
    HARD_REJECT = "HARD_REJECT"             # Dimensional mismatch or fatal safety violation (Tier 3)

class PropertyEvaluation(BaseModel):
    property_name: str                      # "DIMENSIONS", "PRESSURE_RATING", "METALLURGY", "CONNECTION", "SCHEDULE", "TRIM"
    tier: DynamicCompatibilityTier          # Individual Tier for this specific property
    score: float = Field(..., ge=0.0, le=1.0) # Individual score [0.0 - 1.0]
    searched_value: Optional[str] = None    # Value requested by engineer (e.g. "10 inch", "300 PSI")
    candidate_value: Optional[str] = None   # Value on candidate part (e.g. "10 inch", "350 PSI")
    status: PropertyEvaluationStatus
    comment: str                            # e.g. "100% exact OD match", "Safe over-rating (350 PSI >= 300 PSI)"

class PropertyScorecard(BaseModel):
    dimensions: PropertyEvaluation          # Hard zero-tolerance: Tier 3 if mismatched!
    pressure: PropertyEvaluation            # Hard zero-tolerance: Tier 3 if candidate < searched!
    metallurgy: PropertyEvaluation          # Tier 3 if downgraded; Tier 1/2 if equal or safe upgrade
    connection: PropertyEvaluation          # Tier 3 if mechanically incompatible
    equipment_specific: Dict[str, PropertyEvaluation] = Field(default_factory=dict, description="Component-specific properties, e.g. trim, schedule, port bore, seal plan")

class RuleViolation(BaseModel):
    module_name: str
    standard_code: str
    failure_mode_prevented: str
    explanation: str

class CandidateMatchResult(BaseModel):
    sku_code: str
    cpse: str
    depot_id: str
    depot_location: str
    standard_description: str
    available_qty: int
    days_idle: int
    attributes: PhysicalAttributes
    
    # Granular Physical Property-by-Property Breakdown:
    property_scorecard: PropertyScorecard
    
    # Dynamic Runtime Evaluated Metrics relative to query Q:
    compatibility_score: float = Field(..., ge=0.0, le=1.0, description="Runtime ML composite score [0.0 - 1.0]")
    compatibility_tier: DynamicCompatibilityTier = Field(..., description="Runtime computed composite compatibility tier")
    is_compatible: bool = Field(..., description="True if Tier 1 or Tier 2; False if Tier 3")
    requires_hitl: bool = Field(..., description="True for Tier 2 substitutes requiring site engineer sign-off")
    engineering_upgrades: List[str] = Field(default_factory=list, description="e.g. ['PRESSURE UPGRADE: 300# -> 600#']")
    rule_violations: List[RuleViolation] = Field(default_factory=list, description="Fatal zero-tolerance physical violations")
    
    # Inter-CPSE Logistics Summary:
    cisf_eligible: bool = True
    transit_distance_km: float
    transit_lead_hours: int

class MatchResponse(BaseModel):
    query_id: str
    searched_attributes: PhysicalAttributes
    total_candidates_evaluated: int
    execution_time_ms: float
    candidates: List[CandidateMatchResult]
```

---

## 5. Clean Frontend Architecture & Route Map

The rebuilt frontend uses **Next.js 16 (App Router)**, **React 19**, **Tailwind CSS**, and **shadcn/ui**. All redirect shims and artificial fallback mocks from v1 are eliminated. The frontend implements a unified, high-density 5-hub navigation structure:

```
frontend/src/
|-- app/
|   |-- layout.tsx               # Root Layout with ThemeProvider & Sovereign Header
|   |-- page.tsx                 # Default Entrypoint (Redirects to /upload)
|   |-- globals.css              # Global tokens, minimal scrollbars, @media print rules
|   |
|   |-- upload/
|   |   |-- page.tsx             # Stage 01: Scanned MTC & Procurement Bill Drag-and-Drop Intake
|   |   `-- review/
|   |       `-- page.tsx         # Site Engineer Inward Verification & Lifecycle Tag Selection
|   |
|   |-- inventory/
|   |   `-- page.tsx             # Stage 04: Plant Stock Ledger, Lifecycle Transitions & Embedded HITL Triage
|   |                            # Tabs: [All Inventory Stock] | [Broadcasted Surplus] | [HITL Triage Queue] | [Archived]
|   |
|   |-- discover/
|   |   `-- page.tsx             # Stage 04: Cross-CPSE Surplus Discovery Radar (Attribute-Level Price Protected)
|   |
|   |-- requests/
|   |   |-- page.tsx             # Inter-CPSE Requisition Hub & Supply Confirmation Inbox
|   |   `-- [id]/
|   |       `-- page.tsx         # Live Consignment Tracking, Movement Timeline & Printable CISF Gate Pass
|   |
|   `-- audit/
|       `-- page.tsx             # Stage 05: Sovereign Audit Ledger, SHA-256 Verification & RFC 4180 CSV
|
|-- components/
|   |-- Sidebar.tsx              # Clean Left-Hand Enterprise Navigation with Active CPSE Switcher
|   |-- ThemeProvider.tsx        # Light/Dark Theme & CPSE Facility Context Provider
|   |-- ThemeToggle.tsx          # Minimalist Sun/Moon Theme Toggle
|   `-- ui/                      # shadcn/ui Design Primitives
|       |-- Card.tsx             # Base surface container
|       |-- Modal.tsx            # Accessible dialog modal
|       |-- StatusBadge.tsx      # Tier-1, Tier-2, Tier-3 & Lifecycle status badges
|       |-- KpiCard.tsx          # Numerical metric display cards
|       |-- Timeline.tsx         # Chronological consignment tracking tree
|       `-- EmptyState.tsx       # Standardized zero-result display
|
`-- lib/
    |-- api.ts                   # Centralized HTTP API Client (Typed, Pure REST, Zero Fake Heuristics)
    |-- types.ts                 # Full TypeScript Interfaces matching Pydantic schemas
    |-- constants.ts             # 19 CPSE Depot Metadata, Corridors, Status Maps
    |-- formatters.ts            # INR Currency, Relative Time, ISO Date formatters
    `-- exportUtils.ts           # RFC 4180 Compliant CSV Export with UTF-8 BOM
```

### 5.1 Route Functionality Matrix

| Route | Primary Responsibility | Key Interactive Actions |
|---|---|---|
| `/upload` | Intake bills, delivery slips, and EN 10204 3.1 MTC certificates | Dropzone, sample test presets, live sub-250ms PaddleOCR preview table, chemistry breakdown. |
| `/upload/review` | Site Engineer inward verification | Edit extracted specs, verify ASTM chemistry against standards, set initial status (`TO_BE_CONSUMED` vs `IN_STORAGE`), commit to DB. |
| `/inventory` | Plant warehouse stock, surplus radar & **Embedded HITL Triage** | Tab 1: Local Stock Ledger.<br>Tab 2: Active Broadcasted Surplus.<br>**Tab 3: HITL Verification Queue** (side-by-side spec comparison for borderline 80%–94% matches & Tier-2 upgrades, single-click approve/reject).<br>Tab 4: Consumed/Archived. |
| `/discover` | Cross-CPSE spare discovery (Pre-Purchase Radar) | Search 100k items across sister depots, filter by CPSE, view physical specs and idle days (**prices strictly hidden per SIH Slide 4**), 1-click compose requisition. |
| `/requests` | Transfer orders & supply inbox | View inbound requests from other plants, confirm capability to supply, decline with reason, track active road freight. |
| `/requests/[id]` | Consignment tracking & CISF gate pass | Live milestone movement timeline, dispatch clearance button, print-ready official CISF Outward Gate Pass with SVG QR code. |
| `/audit` | Sovereign vigilance ledger | Inspect chronological event stream, verify SHA-256 digital seals on the fly, export RFC 4180 compliant CSV for CVC/CAG inspectors. |

---

## 6. Implementation Roadmap & Modular Execution Plan (Docker-First)

### Phase 1: Docker Infrastructure & Core Database Contracts (Clean Foundation)
- [ ] Spin up live Docker Compose services: **PostgreSQL 16**, **Qdrant (v1.12+)**, and **Neo4j (v5.20+)**.
- [ ] Remove all legacy SQLite fallback code, in-memory dictionary graph hacks, and mock router returns.
- [ ] Initialize clean SQLAlchemy declarative models and Alembic migrations.
- [ ] Implement typed Pydantic v2 schemas across `material.py`, `matching.py`, `inventory.py`, `requisition.py`, and `audit.py`.

### Phase 2: Deterministic Engineering Safety Core
- [ ] Port and modularize ASME B16.5 pressure class ladders (`asme_rules.py`).
- [ ] Port ASTM metallurgy directed acyclic graph and cryogenic LF2 safety traps.
- [ ] Port ASME B36.10M schedules, NACE MR0175 sour service, and B16.47 flange series (`piping_spec_rules.py`).
- [ ] Port IS/IEC 60079 flameproof motor, API 682 mechanical seal, and ISO 15 bearing clearance rules (`rotating_rules.py`).
- [ ] Implement master tolerance evaluation pipeline (`tolerance.py`).
- [ ] Execute automated benchmark suite (150 Golden Benchmark test cases, comprising 82 core integration scenarios and 68 physical engineering domain tests) guaranteeing 100% precision.

### Phase 3: PaddleOCR & PyMuPDF Ingestion Subsystem
- [ ] Standardize strictly on **PaddleOCR (PP-OCRv4)** and **PyMuPDF** across all platforms.
- [ ] Implement document header parsing and image pre-processing (deskew, contrast).
- [ ] Implement EN 10204 3.1 MTC chemistry extraction, IIW Carbon Equivalent ($CE$) computation, and ASTM mechanical threshold validation.
- [ ] Implement streaming batch catalog loader for large ERP CSV/Excel exports.

### Phase 4: NLP Slot Tagger, Qdrant Vector Search & Active Learning
- [ ] Implement Unicode NFKC normalizer and CPSE dialect thesaurus (`ner_tagger.py`).
- [ ] Index canonical catalogs into live Qdrant with HNSW cosine indexing and `item_type` pre-filtering.
- [ ] Implement `ActiveLearningCache` backed by PostgreSQL persistence for online dynamic reranking (< 1ms).

### Phase 5: Neo4j Canonical Property Graph & GIS Gate Pass Engine
- [ ] Populate live Neo4j with shared physical property nodes (`:Dimension`, `:PressureRating`, `:MaterialGrade`, `:EndConnection`).
- [ ] Codify inter-property directed engineering safety relationships (`:SAFE_UPGRADE_FOR`, `:ALLOY_UPGRADE_FOR`, `:COMPATIBLE_WITH`).
- [ ] Seed CPSE enterprise & depot nodes, canonical material mappings, GeM categories, and UNSPSC codes.
- [ ] Implement multi-property sub-millisecond Cypher traversal queries with path-derived dynamic runtime tier calculation in `queries.py`.
- [ ] Implement GIS multi-depot Haversine engine with $1.28\times$ road tortuosity factor (`logistics.py`).
- [ ] Implement atomic inventory reservation lock service in PostgreSQL.
- [ ] Implement self-contained SVG QR code generator for official CISF gate passes.

### Phase 6: Pure REST API Gateway (Zero Mock Fallbacks)
- [ ] Implement clean FastAPI routers (`ingest.py`, `match.py`, `inventory.py`, `requisition.py`, `graph.py`, `audit.py`).
- [ ] Enforce **Attribute-Level Privacy**: Strip unit costs and valuations from cross-CPSE responses in `/api/v1/graph/discover`.
- [ ] Provide pure HTTP 404 / 422 error states instead of artificial heuristics when records do not exist.

### Phase 7: Next.js 16 Clean Web Portal Rebuild
- [ ] Rebuild frontend pages without redirect shims: `/upload`, `/upload/review`, `/inventory` (with embedded HITL triage tab), `/discover`, `/requests`, `/requests/[id]`, and `/audit`.
- [ ] Connect `api.ts` directly to live backend endpoints, removing all artificial fallback mocks.
- [ ] Verify print stylesheet (`@media print`) for official CISF gate pass.
- [ ] Execute full end-to-end integration tests across all 150 benchmark test cases.

---

## 7. Locked Engineering Decisions (Confirmed User Specifications)

| # | Domain Decision | Confirmed Specification | Rationale & SIH Alignment |
|---|---|---|---|
| **D1** | **OCR & Document Intelligence** | **PaddleOCR + PyMuPDF Strictly** across all environments (Windows and Linux). | Eliminates platform-specific branching; guarantees 100% consistent character extraction on rotated scanned slips. |
| **D2** | **Commercial Privacy** | **Strict Attribute-Level Privacy** (Unit prices & valuations strictly hidden across CPSEs; only physical specs, stock, and depot shown). | 100% compliant with **Slide 4 of `SIH_Presentation.pptx`**, preventing anti-competitive price leaks between PSUs. |
| **D3** | **HITL Triage Location** | **Embedded Triage Tab inside `/inventory`** (`[All Stock] \| [Live Surplus] \| [HITL Verification (80%-94%)] \| [Archived]`). | Streamlines site engineer workflow by co-locating stock management with triage verification without route clutter. |
| **D4** | **Database & Services Stack** | **Docker-First Only** (Live PostgreSQL 16, Qdrant, Neo4j; zero SQLite / in-memory mock fallbacks). | Completely eliminates dual-fallback code, fake mock dictionaries, and unverified mock states, ensuring true enterprise fidelity. |
| **D5** | **Graph Database Architecture** | **Canonical Property Graph with Directed Compatibility Edges** (Parts connect to Dimension, Pressure, Material, and Connection nodes; property nodes hold directed upgrade edges). | Prevents $O(N^2)$ edge explosion; enforces dimensional zero-tolerance directly in graph topology; delivers sub-millisecond path traversals for Tier 1 and Tier 2 discovery. |

