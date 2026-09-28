# Samanvay-AI: Master System Specification & Technical Blueprint
## Sovereign Cross-CPSE Spare Parts Interoperability & Mutual Aid Mesh
### Ministry of Petroleum & Natural Gas (MoPNG) | Smart India Hackathon 2026 (SIH26099)

---

## Document & Project Metadata

| Metadata Field | Master Specification Value |
| :--- | :--- |
| **Project Code Name** | **Samanvay-AI** (समन्वय — Unified Sovereign Hydrocarbon MRO Grid) |
| **Problem Statement ID** | **SIH26099** (Smart India Hackathon 2026) |
| **Government Nodal Ministry** | **Ministry of Petroleum & Natural Gas (MoPNG)**, Government of India |
| **Target Enterprises (CPSEs)** | **IOCL**, **ONGC**, **BPCL**, **HPCL**, **GAIL**, **OIL**, **NRL** |
| **Development Team** | **BharatCodex** |
| **Team Leader** | **Mayank Anand** |
| **Core Engineering Team** | **Hariom Chandra Tripathi**, **Shourya Mishra**, **Harsh Rajput**, **Ranvijay Yadav**, **Samriddhi Mishra** |
| **Document Classification** | Sovereign Critical Infrastructure / Air-Gapped Industrial Specification |
| **Software Architecture Model** | Event-Driven, Micro-Modular, Transactional ACID & Graph Topology Mesh |
| **Production Target Version** | `v2.0.0-PROD` |
| **Target Infrastructure** | Air-Gapped Sovereign On-Premises / NICNET / BharatNet / Cloud-Native Docker Grid |
| **Document Purpose** | Comprehensive Technical Reference Manual, Architecture Specification & Ground-Truth System Blueprint |

---

## Table of Contents

1. [Executive Summary & System Abstract](#1-executive-summary--system-abstract)
2. [Problem Statement Deep Dive (SIH26099)](#2-problem-statement-deep-dive-sih26099)
   - 2.1 The Hydrocarbon Enterprise Fragmentation Dilemma
   - 2.2 Financial Impact & Working Capital Lockup
   - 2.3 Critical Safety Hazards of Unregulated Substitution
   - 2.4 Sovereign Air-Gapped & Commercial Privacy Mandates
3. [The Five Non-Negotiable Architectural Invariants](#3-the-five-non-negotiable-architectural-invariants)
4. [Master High-Level Architecture](#4-master-high-level-architecture)
   - 4.1 System Topography & Inter-Service Communications
   - 4.2 Core Technological Stack Reference Matrix
   - 4.3 Workspace Repository Topology
5. [Subsystem 1: Smart Document Intake, Dual-Path OCR & Metallurgy Extraction](#5-subsystem-1-smart-document-intake-dual-path-ocr--metallurgy-extraction)
   - 5.1 Dual-Path Document Intake Architecture
   - 5.2 Fast Path: PyMuPDF Vector Text Stream Extraction (< 50ms)
   - 5.3 Raster Path: CLAHE, Otsu Binarization, Deskewing & PaddleOCR
   - 5.4 International Institute of Welding (IIW) Carbon Equivalent Formulation
   - 5.5 Pitting Resistance Equivalent Number (PREN) Calculation
   - 5.6 ASTM Chemical Composition & Mechanical Tensile Envelope Validation
   - 5.7 Graceful Degradation & Human-in-the-Loop (HITL) Exception Routing
6. [Subsystem 2: Dialect Normalization, Slot Tagging & Dense Embeddings](#6-subsystem-2-dialect-normalization-slot-tagging--dense-embeddings)
   - 6.1 CPSE Engineering Dialect Normalization Pipeline
   - 6.2 40+ Acronym Domain Dictionary & Term Expansion
   - 6.3 Regex Attribute Slot Extraction Architecture
   - 6.4 BAAI/bge-m3 1024-Dimensional Dense Vectorization
   - 6.5 Qdrant Vector Engine & HNSW Cosine Indexing
7. [Subsystem 3: Multi-Stage Hybrid Ranking & TreeSHAP Explainability](#7-subsystem-3-multi-stage-hybrid-ranking--treeshap-explainability)
   - 7.1 Multi-Stage Pipeline Architecture
   - 7.2 Physical Subvector Decomposition
   - 7.3 XGBoost Ranking Model Architecture & Hyperparameters
   - 7.4 TreeSHAP Attribution & Feature Importance Explainability
   - 7.5 Active Learning Feedback Loop & In-Memory Trie Cache
8. [Subsystem 4: The 21 Codified Deterministic Engineering Safety Modules](#8-subsystem-4-the-21-codified-deterministic-engineering-safety-modules)
   - 8.1 Module 1: ASME B16.5 / B16.34 Pressure Class Ladder & Operating PSI
   - 8.2 Module 2: ASTM Metallurgy Directed Acyclic Graph & Cryogenic Brittle Fracture Limits
   - 8.3 Module 3: ASME B36.10M / B36.19M Pipe Schedules & Wall Thickness Invariants
   - 8.4 Module 4: NACE MR0175 / ISO 15156 Wet H2S Sour Service Hardness Ceilings
   - 8.5 Module 5: ASME B16.5 Flange Facings, Serrations & Cast Iron Mating Rules
   - 8.6 Module 6: ASME B16.47 Large Flange Series Mismatch (Series A vs Series B)
   - 8.7 Module 7: ASME B16.20 Gaskets Integrity, Spiral Wound Inner Rings & PTFE Creep
   - 8.8 Module 8: ASTM A193 / A194 Fastener Pairing & Liquid Metal Embrittlement (LME)
   - 8.9 Module 9: API 6D Pipeline Piggable Full Bore Flow Restrictions
   - 8.10 Module 10: API 607 / API 6FA Flammable Hydrocarbon Fire-Safe Certification
   - 8.11 Module 11: API 600 / API 602 Valve Trim Material Degradation Ladder
   - 8.12 Module 12: API 520 / API 526 Pressure Safety Valve (PSV) Orifice Sizing & CDTP
   - 8.13 Module 13: ISO 4126-2 / ASME Sec VIII UG-127 Rupture Disk Non-Fragmentation Invariants
   - 8.14 Module 14: ASME B16.48 Positive Isolation Spectacle Blinds & Spacers
   - 8.15 Module 15: NACE SP0286 Flange Insulation Kits (FIK) & Cathodic Protection
   - 8.16 Module 16: ASTM A269 Instrumentation Small-Bore Tubing & Metric/Imperial Ferrule Traps
   - 8.17 Module 17: API 610 Centrifugal Pumps & Centerline Thermal Mounting
   - 8.18 Module 18: API 682 Mechanical Seals & Pressurized Barrier Piping Plans
   - 8.19 Module 19: API 618 / API 617 Reciprocating & Centrifugal Gas Compressors
   - 8.20 Module 20: IS/IEC 60079 & ISO 15 Hazardous Area Motors & C3 Bearing Clearances
   - 8.21 Module 21: Equipment Safety: TEMA Exchangers, API 2000 Tanks & ASTM C795 Insulation
9. [Subsystem 5: Dynamic Compatibility Tiers & Public Procurement Alignment](#9-subsystem-5-dynamic-compatibility-tiers--public-procurement-alignment)
   - 9.1 Mathematical Formulation of Dynamic Compatibility Tiers
   - 9.2 Indian Public Procurement Alignment: BIS/IS Equivalent Mapping
   - 9.3 Public Procurement (Preference to Make in India) Order (PPP-MII) Compliance
   - 9.4 GeM (Government e-Marketplace) & CPPP Tender Interoperability
10. [Subsystem 6: Knowledge Graph & National Logistics Topology Engine](#10-subsystem-6-knowledge-graph--national-logistics-topology-engine)
    - 10.1 Neo4j 5.20 Property Star Graph Schema
    - 10.2 The 19 National CPSE Hydrocarbon Depots & GPS Coordinates Matrix
    - 10.3 Haversine Great-Circle Geodesic Distance
    - 10.4 Indian National Highway Tortuosity Factor Formulation (1.28x)
    - 10.5 Freight Economics & Transit Time Calculations
    - 10.6 Bureau of Energy Efficiency (BEE) Carbon Savings Model
11. [Subsystem 7: Transactional Concurrency, Row Locks & Real-Time CDC](#11-subsystem-7-transactional-concurrency-row-locks--real-time-cdc)
    - 11.1 Atomic Pessimistic Locking Workflow (`SELECT ... FOR UPDATE`)
    - 11.2 Multi-Depot Stock Reservation & Expiry Lifecycle (7-Day Auto-Release)
    - 11.3 PostgreSQL Transactional CDC Outbox Architecture
    - 11.4 Asynchronous Neo4j Graph Synchronization via PostgreSQL LISTEN/NOTIFY
12. [Subsystem 8: Cryptographic Merkle Audit Ledger & Anti-Tamper Security](#12-subsystem-8-cryptographic-merkle-audit-ledger--anti-tamper-security)
    - 12.1 Merkle Block Structure & Parent Hash Invariants ($H_0 = \text{"000...000"}$)
    - 12.2 Cryptographic Event Block Model & Canonical JSON Serialization
    - 12.3 Cryptographic Chain Integrity Verification Algorithm
    - 12.4 Role-Based Access Control (RBAC) & Sovereign Multi-Tenancy Architecture
13. [Subsystem 9: Sovereign CISF Physical Verification & Pure SVG QR Gate Pass](#13-subsystem-9-sovereign-cisf-physical-verification--pure-svg-qr-gate-pass)
    - 13.1 Air-Gapped Pure SVG 25x25 QR Bit Matrix Engine
    - 13.2 CISF Physical Gate Pass Layout & Security Seal Verification
    - 13.3 End-to-End Handheld Scanner Verification Workflow
14. [Subsystem 10: PostgreSQL Database Schema & Complete Data Dictionary](#14-subsystem-10-postgresql-database-schema--complete-data-dictionary)
    - 14.1 Complete Database DDL SQL Specification
    - 14.2 Detailed Field Data Dictionary & Foreign Key Invariants
15. [Subsystem 11: Comprehensive API Specification & Pydantic Data Contracts](#15-subsystem-11-comprehensive-api-specification--pydantic-data-contracts)
    - 15.1 OpenAPI Endpoints Reference Directory
    - 15.2 Pydantic Validation Models & Schemas
    - 15.3 Request & Response Payloads Specification
16. [Subsystem 12: Frontend Architecture & User Interface Design](#16-subsystem-12-frontend-architecture--user-interface-design)
    - 16.1 Component Architecture & Routing Topography
    - 16.2 Executive Dashboard & Command Center UI
    - 16.3 Pre-Purchase Semantic Discovery Radar UI
    - 16.4 MTC Chemistry Inspection Studio UI
    - 16.5 Inter-CPSE Loan & Requisition Manager UI
    - 16.6 Sovereign Merkle Audit Ledger & CAG Export UI
17. [Subsystem 13: Dataset Architecture & Golden Benchmarks](#17-subsystem-13-dataset-architecture--golden-benchmarks)
    - 17.1 Golden Benchmark Dataset (`golden_benchmarks.json`)
    - 17.2 CPSE Synthetic Inventory Seed Generator
    - 17.3 Real-World MTC Document Test Corpus
18. [Subsystem 14: Comprehensive Test Suite & Quality Verification Matrix](#18-subsystem-14-comprehensive-test-suite--quality-verification-matrix)
    - 18.1 Tolerance Rules Verification Matrix
    - 18.2 OCR & Chemistry Engine Verification Suite
    - 18.3 Cryptographic Merkle Ledger Verification Tests
    - 18.4 Multi-Depot Concurrency & Allocation Integration Tests
19. [Subsystem 15: Containerization, Deployment & Air-Gapped Operation](#19-subsystem-15-containerization-deployment--air-gapped-operation)
    - 19.1 Multi-Container Docker Compose Architecture
    - 19.2 Zero-Cloud Air-Gapped Sovereign Deployment Guide
    - 19.3 Production Environment Variables & Security Configuration
20. [Subsystem 16: Future Roadmap & Long-Term Sovereign Grid Expansion](#20-subsystem-16-future-roadmap--long-term-sovereign-grid-expansion)
    - 20.1 Autonomous CPSE Tender Interception (CPPP & GeM Integration)
    - 20.2 Federated Edge Nodes on Offshore Platforms (WASM / SQLite)
    - 20.3 Advanced Drone & Aerial Logistics Integration for Emergency Corridors
21. [Document Certification & Team Sign-Off](#21-document-certification--team-sign-off)
22. [Subsystem 17: Comprehensive File-by-File Codebase Audit & Architectural Inventory](#22-comprehensive-file-by-file-codebase-audit--architectural-inventory)

---

## 1. Executive Summary & System Abstract

**Samanvay-AI** (समन्वय) is an enterprise-grade, sovereign interoperability platform and automated mutual-aid mesh engineered specifically for India's upstream, midstream, and downstream Central Public Sector Enterprises (CPSEs) operating under the aegis of the **Ministry of Petroleum & Natural Gas (MoPNG)**. The platform unites the disparate, siloed inventory ecosystems of **Indian Oil Corporation Limited (IOCL)**, **Oil and Natural Gas Corporation (ONGC)**, **Bharat Petroleum Corporation Limited (BPCL)**, **Hindustan Petroleum Corporation Limited (HPCL)**, **GAIL (India) Limited**, **Oil India Limited (OIL)**, and **Numaligarh Refinery Limited (NRL)** into a singular, high-performance, real-time mutual-aid network.

In high-hazard hydrocarbon processing plants, offshore production platforms, and cross-country gas transmission pipelines, unplanned asset downtime caused by critical spare part stockouts can lead to daily production losses exceeding ₹5 Crore to ₹15 Crore per facility. Simultaneously, across India's 19+ major petroleum refineries and petrochemical complexes, thousands of crores of rupees in capital remain locked in redundant, slow-moving, or dormant MRO (Maintenance, Repair, and Operations) inventory.

Samanvay-AI eliminates this fundamental systemic inefficiency through an innovative multi-tiered architecture:
1. **Intelligent Dual-Path Document Intake**: Rapidly ingests and digitizes legacy Material Test Certificates (MTCs), Purchase Orders, and Engineering Datasheets via PyMuPDF vector streams (< 50ms) and PaddleOCR binarization with automated chemical formula extraction (IIW Carbon Equivalent, PREN).
2. **CPSE Engineering Dialect Normalization**: Translates divergent enterprise-specific naming conventions across 40+ domain abbreviations into normalized engineering schemas mapped to 1024-dimensional dense semantic vector representations (`BAAI/bge-m3`).
3. **Multi-Stage Explainable Hybrid Ranking**: Combines fast cosine similarity pre-filtering in Qdrant vector spaces with fine-grained physical subvector matching and TreeSHAP-attributed XGBoost ranking models to evaluate candidate parts.
4. **21 Codified Deterministic Engineering Safety Modules**: Enforces hard, unbypassable safety constraints grounded in ASME, ASTM, API, NACE, ISO, and BIS/IS industrial standards. If any safety boundary is violated, the system triggers an immediate veto, capping compatibility at Tier 3 (Incompatible) regardless of high vector similarity.
5. **Knowledge Graph & National Logistics Routing**: Employs Neo4j 5.20 property star graphs and Haversine-geodesic algorithms calibrated with a 1.28x Indian National Highway tortuosity factor to compute real-time freight economics, road transit times, and Bureau of Energy Efficiency (BEE) carbon emissions abatement across 19 national CPSE depot nodes.
6. **ACID Transactional Concurrency & CDC Outbox**: Guarantees zero double-allocation of critical stock during concurrent multi-depot emergency requisitions using PostgreSQL pessimistic row-level locking (`SELECT ... FOR UPDATE`) and real-time Change Data Capture (`cdc_outbox`) for graph synchronization.
7. **Sovereign Merkle Audit Ledger & Air-Gapped SVG CISF Gate Passes**: Ensures complete tamper-evident auditability for Controller and Auditor General (CAG) compliance via SHA-256 parent-linked Merkle chains ($H_0 = \text{"000...000"}$) and generates standalone 25x25 bit-matrix SVG QR gate passes for Central Industrial Security Force (CISF) physical checkpoint verification without external cloud or CDN dependencies.

---

## 2. Problem Statement Deep Dive (SIH26099)

### 2.1 The Hydrocarbon Enterprise Fragmentation Dilemma
India's oil and gas infrastructure is operated by major CPSEs that historically deployed isolated Enterprise Resource Planning (ERP) installations (such as SAP ECC/S4HANA, Oracle E-Business Suite, and legacy Maximo systems). Over decades, these enterprises independently formulated their internal item codes, catalog taxonomies, and colloquial engineering descriptions.

For example, an identical 6-inch Class 300 Cast Carbon Steel Gate Valve with API 600 Trim 8 is cataloged under completely non-interoperable nomenclature across different CPSEs:
- **IOCL SAP Description**: `VLV GT 6IN 300# WCB FLG RF TRIM 8 FB`
- **ONGC Oracle Description**: `GATE VALVE 150MM CL300 ASTM A216 WCB RAISED FACE F/B T8`
- **BPCL Maximo Description**: `VALVE, GATE, FLANGED 6" 300LBS WCB/13CR BODY A216-WCB TRIM STLT`
- **GAIL SAP Description**: `6" 300LB WCB GT VLV FULL BORE RF 13% CR ASME B16.34`

When an emergency pipeline rupture or refinery shutdown occurs, maintenance engineers searching for urgent replacements across CPSE boundaries are prevented from discovering existing surplus stocks due to syntactic and dialectical misalignment. Consequently, plants resort to emergency procurement lead times of 16 to 48 weeks, prolonging catastrophic downtime.

### 2.2 Financial Impact & Working Capital Lockup
The financial consequences of inventory fragmentation are twofold:
1. **Downtime Capital Losses**: A single delayed replacement for a high-pressure pump seal or refinery boiler safety valve can halt hydrocracker or FCCU units, causing direct revenue losses ranging from ₹5 Crore to ₹15 Crore per day.
2. **Surplus Inventory Lockup**: CPSEs maintain multi-crore buffer stocks for catastrophic contingencies. Many of these critical spares sit dormant in regional depots for over 180 to 720 days, accumulating holding costs, degradation risks, and working capital deadlocks across the national balance sheet.

### 2.3 Critical Safety Hazards of Unregulated Substitution
In high-pressure, flammable, and toxic hydrocarbon environments (e.g., lethal wet H2S sour gas, cryogenic LNG, superheated steam), informal or naive AI-driven spare parts substitution is catastrophic.
- **Sour Gas Hydrogen Embrittlement**: Installing an uncertified carbon steel valve with Rockwell Hardness > 22 HRC in NACE MR0175 sour service causes catastrophic Sulfide Stress Cracking (SSC) and toxic gas releases.
- **Cryogenic Brittle Fracture**: Substituting standard ASTM A216 WCB carbon steel into a -100°C LNG service results in immediate catastrophic brittle fracture, as WCB becomes brittle below -29°C, whereas ASTM A352 LCB/LCC or ASTM A351 CF8M is legally required.
- **Pressure Class Rating Deficiencies**: Installing an ASME Class 150 component into a Class 300 operating manifold causes instantaneous rupture under hydrotest or operational pressure.

### 2.4 Sovereign Air-Gapped & Commercial Privacy Mandates
Public sector enterprises operate under strict regulatory, commercial, and national security directives:
- **Commercial Confidentiality**: Unit purchase prices (`unit_cost_inr`), total purchase order values (`total_value_inr`), and historical vendor contract IDs are commercially sensitive proprietary information. Exposing these across CPSE boundaries or to unauthorized third parties violates statutory trade secrecy and public procurement fairness.
- **Data Sovereignty & Air-Gap Requirements**: Hydrocarbon refineries and offshore production grids are designated as Critical Information Infrastructure (CII) by NCIIPC. The entire platform must operate entirely on-premises, within sovereign NICNET/BharatNet nodes or air-gapped secure networks, with zero reliance on external third-party proprietary AI APIs, cloud CDNs, or foreign hosted infrastructure.

---

## 3. The Six Non-Negotiable Architectural Invariants

Samanvay-AI is architected around **Six Core Non-Negotiable Invariants** that cannot be bypassed, disabled, or compromised under any operating condition:

```
+----------------------------------------------------------------------------------------------------+
|                               THE 6 NON-NEGOTIABLE ARCHITECTURAL INVARIANTS                         |
+====================================================================================================+
| 1. Dynamic Compatibility Tiers: S(Q, C) dynamic score. ZERO static global compatibility tiers.     |
| 2. Hard Deterministic Safety Gate: 21 Safety Rules have unilateral hard veto (Cap <= 0.74, Tier 3). |
| 3. Sovereign Attribute-Level Privacy: unit_cost_inr & PO data strictly stripped across CPSEs.      |
| 4. Air-Gapped Cryptographic Sovereignty: Zero external CDN/Cloud; SHA-256 Merkle chain & SVG QR.   |
| 5. Zero ERP Disruption: Transactional CDC Outbox (cdc_outbox table) without modifying SAP/Oracle.  |
| 6. Multi-Tenant Isolation & Segregation of Duties: Strict demand scoping & self-approval lock.     |
+----------------------------------------------------------------------------------------------------+
```

### Invariant 1: Dynamic Compatibility Tiers (Relational $S(Q, C)$)
Compatibility is strictly a **dynamic relational function** $S(Q, C)$ evaluated between a specific Query Requisition $Q$ and a Candidate Spare Part $C$ within an operational context. No item possesses a static global compatibility tier in isolation. A valve that is a Tier 1 direct replacement for a low-pressure utility water line will be an immediate Tier 3 fatal incompatibility for high-pressure sour gas service.

### Invariant 2: Hard Deterministic Safety Gate (Deterministic Rule Primacy)
While statistical vector embeddings and machine learning rankers propose candidate matches based on semantic similarity, they **NEVER** make final safety decisions. The **21 Codified Deterministic Engineering Safety Modules** hold unilateral, non-overridable veto power. If any deterministic safety invariant fails (e.g., pressure rating deficiency, NACE non-compliance, metallurgy downgrade), the candidate's final score is capped at $\le 0.74$, forcing an immediate Tier 3 (Incompatible) classification regardless of a 99% vector similarity score.

### Invariant 3: Sovereign Attribute-Level Privacy
Cross-enterprise data federation strictly filters commercial pricing, historical vendor procurement terms, and purchase order numbers at the serializer layer. Peer CPSEs can inspect technical engineering specifications, physical metallurgy, stock quantities, and depot geographical locations, but commercial financial terms remain completely masked.

### Invariant 4: Air-Gapped Cryptographic Sovereignty
The entire software stack operates with **zero external cloud or CDN dependencies**. All JavaScript libraries, CSS frameworks, vector models, and OCR engines are self-contained within local on-premises containers. The cryptographic audit ledger maintains an unbroken SHA-256 parent-linked Merkle chain initialized from the hardcoded genesis block $H_0 = \text{"0000000000000000000000000000000000000000000000000000000000000000"}$, and gate passes are rendered via pure inline SVG 25x25 bit-matrix QR generators.

### Invariant 5: Zero ERP Disruption
Samanvay-AI integrates seamlessly with legacy enterprise systems without necessitating intrusive schema modifications or real-time distributed transactions across SAP/Oracle databases. Synchronization is achieved via a non-blocking PostgreSQL transactional Change Data Capture (`cdc_outbox`) mechanism and automated asynchronous event streams.

### Invariant 6: Multi-Tenant Isolation & Segregation of Duties
Inter-CPSE material requisitions are strictly isolated at the query layer via `list_requisitions_for_user(db, user)`. Regular site engineers and plant managers can only access requisitions created by their own user account or incoming requests specifically targeting their depot/CPSE; cross-tenant transactions are completely shielded. Furthermore, requesters are strictly barred from approving their own requisitions (`HTTP 403 Forbidden`). Only the supplying CPSE's Materials Manager holds the statutory authority to release surplus inventory, and CISF Security Officers issue digital gate passes with SHA-256 cryptographic seals.

---

## 4. Master High-Level Architecture

### 4.1 System Topography & Inter-Service Communications

```mermaid
flowchart TD
    subgraph Enterprise_Clients["Enterprise Access Layer"]
        WebUI["Next.js 16 Sovereign UI (Tailwind CSS v4)"]
        CISF_Pass["CISF Gate Pass (Pure SVG 25x25 QR)"]
        ERP_Agent["Legacy ERP Connector (SAP / Oracle / Maximo)"]
    end

    subgraph API_Gateway["FastAPI Gateway & Core Router"]
        AuthModule["JWT RBAC & Sovereign Privacy Filter"]
        DocIngest["Document Ingestion & MTC OCR Pipeline"]
        SearchRouter["Semantic Discovery & Vector Search Router"]
        LoanRouter["ACID Loan & Concurrency Manager"]
        AuditRouter["Merkle Ledger Verification Router"]
    end

    subgraph Intelligent_Core["AI & Deterministic Engineering Engine"]
        DualOCR["Dual-Path OCR (PyMuPDF Vector / PaddleOCR CLAHE)"]
        ChemEngine["Metallurgy Engine (IIW CE & PREN Formulas)"]
        DialectNorm["CPSE Dialect Normalizer & Slot Extractor"]
        DenseEmbed["BAAI/bge-m3 1024-Dim Vector Encoder"]
        HybridRank["XGBoost Ranker + TreeSHAP Explainability"]
        SafetyRules["21 Deterministic Engineering Safety Modules"]
    end

    subgraph Data_Storage["Sovereign Data Storage Grid"]
        PostgresDB[("PostgreSQL 16 ACID Database (Row Locks & CDC Outbox)")]
        QdrantDB[("Qdrant Vector DB (HNSW Cosine Indexing)")]
        Neo4jDB[("Neo4j 5.20 Star Graph (Depot Logistics & Topology)")]
    end

    WebUI --> API_Gateway
    ERP_Agent --> API_Gateway
    API_Gateway --> AuthModule
    AuthModule --> DocIngest & SearchRouter & LoanRouter & AuditRouter

    DocIngest --> DualOCR --> ChemEngine
    SearchRouter --> DialectNorm --> DenseEmbed --> QdrantDB
    QdrantDB -.-> HybridRank
    HybridRank --> SafetyRules
    SafetyRules --> Neo4jDB

    LoanRouter --> PostgresDB
    PostgresDB -- "PostgreSQL NOTIFY" --> Neo4jDB
    AuditRouter --> PostgresDB
```

### 4.2 Core Technological Stack Reference Matrix

| Architectural Layer | Technology Selection | Version / Standard | Functional Scope & Rationale |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** | `0.115.0+` | High-throughput asynchronous Python framework with native Pydantic v2 validation. |
| **Relational Database** | **PostgreSQL** | `16.0 Alpine` | Master ACID transaction store; row-level locking (`SELECT FOR UPDATE`) and CDC Outbox. |
| **Vector Engine** | **Qdrant** | `v1.12.0` | On-premises vector similarity database executing HNSW indexing with payload filtering. |
| **Knowledge Graph** | **Neo4j** | `5.20.0 Community` | Multi-relational star graph mapping CPSE plants, depots, spatial coordinates, and transport edges. |
| **Embedding Model** | **BAAI/bge-m3** | `1024-dim Dense` | High-density multi-lingual semantic representation fine-tuned for engineering terminologies. |
| **Ranking Classifier** | **XGBoost** | `2.0.0+` | Gradient boosted decision trees trained on physical subvector feature representations. |
| **Explainable AI** | **TreeSHAP** | `0.44.0+` | Shapley additive feature attribution for transparent engineering score justification. |
| **OCR Engines** | **PyMuPDF / PaddleOCR** | `1.24.0 / 2.7.0` | Dual-path document processor with CLAHE contrast enhancement and Otsu binarization. |
| **Frontend Framework** | **Next.js (App Router)**| `16.0.0` | Server-side rendered React framework optimized for enterprise web performance. |
| **UI Component Layer** | **React & Tailwind CSS**| `19.0.0 / v4.0` | Modern, accessible component architecture with custom sovereign industrial themes. |
| **Cryptographic Hash** | **SHA-256 / Merkle** | `FIPS PUB 180-4` | Parent-linked immutable audit ledger ensuring zero tampering for statutory CAG audits. |
| **Container Engine** | **Docker & Compose** | `v2.24.0+` | Fully encapsulated, air-gapped sovereign deployment grid with local health checks. |

### 4.3 Workspace Repository Topology
The project codebase is organized into modular directories enforcing clean separation of concerns:
```
Samanvay-AI/
|-- backend/                     # FastAPI core backend service
|   |-- main.py                  # API gateway entrypoint & CORS middleware
|   |-- app/
|       |-- api/routers/         # Endpoints (items, loans, search, ocr, audit, depots, analytics)
|       |-- core/                # Database engine, config, security, exceptions
|       |-- models/              # SQLAlchemy ORM database models
|       |-- schemas/             # Pydantic v2 data validation schemas
|       |-- services/            # Business logic (loan service, audit service, sync service)
|-- rules/                       # The 21 Deterministic Engineering Safety Modules
|   |-- tolerance.py             # Master evaluation dispatcher & dynamic tier calculator
|   |-- asme/                    # ASME B16.5, B16.34, B36.10M, B16.47, B16.20, B16.48
|   |-- astm/                    # ASTM A105, A216, A350, A352, A312, A193/A194 fasteners
|   |-- piping/                  # Pipe schedules, flange facings, insulation kits
|   |-- valves/                  # API 6D, API 600, API 602, API 607, API 520, ISO 4126
|   |-- rotating/                # API 610 pumps, API 682 seals, API 618 compressors
|   |-- equipment/               # TEMA heat exchangers, API 2000 tanks, ASTM C795
|-- ml/                          # Machine Learning & AI Intelligence Subsystems
|   |-- vision/                  # Dual-Path OCR (PyMuPDF / PaddleOCR) & MTC chemistry parser
|   |-- ner/                     # CPSE dialect normalizer & regex slot tagger
|   |-- embeddings/              # BAAI/bge-m3 dense vector encoder & Qdrant client
|   |-- ranking/                 # XGBoost ranker & TreeSHAP explainability engine
|   |-- active_learning/         # In-memory feedback cache & trie lookup
|-- graph/                       # Neo4j Knowledge Graph & Logistics Engine
|   |-- schema.py                # Graph schema initialization & spatial constraints
|   |-- logistics.py             # Haversine distance, 1.28x tortuosity, freight & carbon model
|   |-- queries.py               # Cypher query templates
|   |-- syncer.py                # CDC Outbox synchronization worker
|-- frontend/                    # Next.js 16 Sovereign Web UI
|   |-- src/app/                 # App Router pages (dashboard, discover, inventory, audit, loans)
|   |-- src/components/          # UI components (QR Gate Pass, MTC Studio, Scorecard)
|-- datasets/                    # Golden benchmark datasets & synthetic inventory seeds
|-- docker/                      # Docker compose definitions & air-gapped configuration
|-- tests/                       # Pytest unit & integration test suites
```


## 5. Subsystem 1: Smart Document Intake, Dual-Path OCR & Metallurgy Extraction

### 5.1 Dual-Path Document Intake Architecture
The ingestion pipeline processes heterogeneous industrial documentation—such as Material Test Certificates (EN 10204 3.1 / 3.2), Vendor Purchase Orders, Mill Inspection Sheets, and Engineering Datasheets. The engine implements a dual-path routing mechanism optimized for both throughput speed and scanning resilience.

```mermaid
flowchart LR
    DocInput["PDF / Image Document Intake"] --> PathCheck{"Vector Text Stream Available?"}
    PathCheck -- "Yes (> 100 chars text)" --> FastPath["Fast Path: PyMuPDF Stream Extraction (< 50ms)"]
    PathCheck -- "No (Scanned / Rasterized)" --> RasterPath["Raster Path: Pre-processing & PaddleOCR"]

    subgraph Raster_Pipeline["Raster Enhancement Pipeline"]
        CLAHE["CLAHE Contrast Enhancement (clipLimit=2.0, tileGrid=8x8)"]
        Otsu["Otsu Adaptive Binarization"]
        Deskew["Affine Deskewing & Noise Reduction"]
        Paddle["PaddleOCR Inference (det + rec + cls)"]
        CLAHE --> Otsu --> Deskew --> Paddle
    end

    RasterPath --> Raster_Pipeline
    FastPath --> StructParser["Structured Regex Key-Value Parser"]
    Paddle --> StructParser

    StructParser --> ChemModule["Metallurgy Chemistry Extraction"]
    ChemModule --> CE_Calc["IIW Carbon Equivalent Calculation"]
    ChemModule --> PREN_Calc["PREN Corrosion Resistance Calculation"]
    ChemModule --> ASTM_Val["ASTM Chemistry & Tensile Envelope Verification"]
```

### 5.2 Fast Path: PyMuPDF Vector Text Stream Extraction (< 50ms)
For digitally born PDF documents (e.g. native SAP/Oracle purchase orders, modern CAD spec sheets), PyMuPDF parses embedded vector character streams and tabular bounding boxes in under 50 milliseconds. It skips heavy neural OCR inference, eliminating compute bottlenecks.

### 5.3 Raster Path: CLAHE, Otsu Binarization, Deskewing & PaddleOCR
For degraded, faxed, photocopied, or stamped physical mill test certificates, the raster path executes a specialized computer vision pipeline:
1. **Contrast Limited Adaptive Histogram Equalization (CLAHE)**: Operates on local $8 \times 8$ pixel tiles with a clipping limit of 2.0 to enhance faint dot-matrix printer characters without amplifying background noise.
2. **Otsu Binarization**: Dynamically calculates the optimal global threshold separating foreground ink text from yellowed or creased certificate parchment.
3. **Affine Deskewing**: Uses Hough line transforms to detect document rotation angles ($pm 45^circ$) and applies affine transformation matrices to re-align text horizontally.
4. **PaddleOCR Inference**: Executes lightweight convolutional text detection (DBNet) followed by CRNN-based sequence recognition and angle classification to yield bounding-box-aligned text tokens.

### 5.4 International Institute of Welding (IIW) Carbon Equivalent Formulation
The Carbon Equivalent ($CE$) quantifies the weldability of carbon and low-alloy steels and predicts susceptibility to Hydrogen-Induced Cold Cracking (HICC). When an MTC is uploaded, the chemistry engine automatically extracts elemental percentages and computes:

$$CE_{\text{IIW}} = \%C + \frac{\%Mn}{6} + \frac{\%Cr + \%Mo + \%V}{5} + \frac{\%Ni + \%Cu}{15}$$

#### Industrial Engineering Interpretation:
- **$CE_{\text{IIW}} \le 0.43\%$**: Excellent weldability. No mandatory preheat required under standard ambient conditions.
- **$0.43\% < CE_{\text{IIW}} \le 0.48\%$**: Moderate weldability. Mandatory preheating ($100^\circ\text{C} - 150^\circ\text{C}$) and low-hydrogen welding consumables required.
- **$CE_{\text{IIW}} > 0.48\%$**: Severe cracking susceptibility. Requires stringent preheating ($> 200^\circ\text{C}$), strict interpass temperature controls, and mandatory Post-Weld Heat Treatment (PWHT).

### 5.5 Pitting Resistance Equivalent Number (PREN) Calculation
For stainless steels and duplex alloys (e.g. ASTM A182 F316L, 2205 Duplex, 2507 Super Duplex), resistance to localized pitting and crevice corrosion in chloride-rich marine and offshore environments is computed via PREN:

$$\text{PREN} = \%Cr + 3.3 \times (\%Mo + 0.5 \times \%W) + 16 \times \%N$$

#### Critical Acceptance Thresholds:
- **Standard Austenitic (SS 304/304L)**: $\text{PREN} \approx 18 - 20$ (Unsuitable for seawater/marine splash zones).
- **Molybdenum Austenitic (SS 316/316L)**: $\text{PREN} \approx 23 - 25$ (Resistant to mild chlorides; susceptible to stagnant warm seawater).
- **2205 Duplex Stainless Steel**: $\text{PREN} \ge 34.0$ (Mandatory minimum for brackish water and coastal processing units).
- **2507 Super Duplex Stainless Steel**: $\text{PREN} \ge 42.0$ (Mandatory for subsea manifolds, hot sour brine, and offshore wellheads).

### 5.6 ASTM Chemical Composition & Mechanical Tensile Envelope Validation
The engine automatically cross-references parsed values against standardized ASTM material specification envelopes:

| ASTM Standard | Material Grade | Carbon (C max %) | Manganese (Mn %) | Chromium (Cr %) | Nickel (Ni %) | Molybdenum (Mo %) | Min Tensile (MPa) | Min Yield (MPa) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ASTM A105** | Carbon Steel Forging | $0.35$ | $0.60 - 1.05$ | $\le 0.30$ | $\le 0.40$ | $\le 0.12$ | $485$ | $250$ |
| **ASTM A216 WCB**| Cast Carbon Steel | $0.30$ | $\le 1.00$ | $\le 0.50$ | $\le 0.50$ | $\le 0.20$ | $485$ | $250$ |
| **ASTM A350 LF2** | Low Temp Carbon Steel | $0.30$ | $0.60 - 1.35$ | $\le 0.30$ | $\le 0.40$ | $\le 0.12$ | $485$ | $250$ |
| **ASTM A182 F316L**| Austenitic Stainless | $0.030$ | $\le 2.00$ | $16.0 - 18.0$ | $10.0 - 14.0$ | $2.00 - 3.00$ | $485$ | $170$ |
| **ASTM A182 F51** | 2205 Duplex Stainless | $0.030$ | $\le 2.00$ | $21.0 - 23.0$ | $4.50 - 6.50$ | $2.50 - 3.50$ | $620$ | $450$ |

### 5.7 Graceful Degradation & Human-in-the-Loop (HITL) Exception Routing
If OCR confidence falls below $85\%$, or if computed chemistry values fall outside ASTM envelopes (e.g. sulfur or phosphorus content exceeding $0.040\%$), the system flags the document as **`REQUIRES_METALLURGIST_REVIEW`**. The split-screen verification UI highlights disputed values with bounding boxes for single-click engineer confirmation.

---

## 6. Subsystem 2: Dialect Normalization, Slot Tagging & Dense Embeddings

### 6.1 CPSE Engineering Dialect Normalization Pipeline
Engineers across IOCL, ONGC, BPCL, HPCL, and GAIL use distinct abbreviation shorthands in catalog descriptions. The normalization pipeline transforms raw text strings into canonical standard formats before vectorization.

```mermaid
flowchart TD
    RawInput["Raw Catalog String: 'VLV GT 6IN 300# WCB FLG RF TRIM 8 FB'"] --> Tokenizer["Regex Tokenizer & Case Normalizer"]
    Tokenizer --> AcronymExp["40+ Domain Acronym Expansion & Mapping"]
    AcronymExp --> SlotTag["Regex Slot Tagging (Size, Class, Metallurgy, Trim, Facings)"]
    SlotTag --> CanonString["Canonical Spec: 'GATE VALVE 6 INCH CLASS 300 ASTM A216 WCB RF TRIM 8 FULL BORE'"]
    CanonString --> BGE_Encoder["BAAI/bge-m3 1024-Dim Vector Encoder"]
    BGE_Encoder --> Qdrant_Payload["Qdrant Point Struct (Payload + Vector)"]
```

### 6.2 40+ Acronym Domain Dictionary & Term Expansion
The normalization dictionary handles comprehensive domain expansions across all major CPSE catalog variants:

| Raw Token / Abbreviation | Canonical Standard Term | Engineering Classification |
| :--- | :--- | :--- |
| `VLV`, `VALV` | `VALVE` | Equipment Class |
| `GT`, `GTV` | `GATE VALVE` | Valve Type |
| `GL`, `GLB` | `GLOBE VALVE` | Valve Type |
| `CH`, `CHK`, `NRV` | `CHECK VALVE` (Non-Return Valve) | Valve Type |
| `BL`, `BAL` | `BALL VALVE` | Valve Type |
| `BF`, `BTY` | `BUTTERFLY VALVE` | Valve Type |
| `PLG` | `PLUG VALVE` | Valve Type |
| `PSV`, `PRV` | `PRESSURE SAFETY VALVE` | Safety Relief Device |
| `WCB` | `ASTM A216 GRADE WCB` | Cast Carbon Steel |
| `LCB`, `LCC` | `ASTM A352 GRADE LCB/LCC` | Low Temperature Cast Carbon Steel |
| `CF8M` | `ASTM A351 GRADE CF8M (SS 316)` | Cast Stainless Steel |
| `A105` | `ASTM A105` | Forged Carbon Steel |
| `LF2` | `ASTM A350 GRADE LF2` | Low Temperature Forged Carbon Steel |
| `F316L` | `ASTM A182 GRADE F316L` | Forged Austenitic Stainless Steel |
| `150#`, `150LB`, `CL150` | `CLASS 150` | ASME Pressure Class (PN 20) |
| `300#`, `300LB`, `CL300` | `CLASS 300` | ASME Pressure Class (PN 50) |
| `600#`, `600LB`, `CL600` | `CLASS 600` | ASME Pressure Class (PN 100) |
| `800#`, `800LB`, `CL800` | `CLASS 800` | API 602 Forged Pressure Class |
| `1500#`, `1500LB`, `CL1500` | `CLASS 1500` | ASME Pressure Class (PN 250) |
| `2500#`, `2500LB`, `CL2500` | `CLASS 2500` | ASME Pressure Class (PN 420) |
| `RF` | `RAISED FACE` | Flange Facing Type |
| `RTJ`, `RJ` | `RING TYPE JOINT` | Flange Facing Type |
| `FF` | `FLAT FACE` | Flange Facing Type |
| `BW`, `BWE` | `BUTT WELD END` | End Connection |
| `SW`, `SWE` | `SOCKET WELD END` | End Connection |
| `NPT`, `THD` | `NATIONAL PIPE THREAD (THREADED)` | End Connection |
| `FB` | `FULL BORE` | Flow Port Configuration |
| `RB` | `REDUCED BORE` | Flow Port Configuration |
| `SCH 40`, `SCH40`, `STD` | `SCHEDULE 40 (STANDARD WALL)` | ASME B36.10M Pipe Schedule |
| `SCH 80`, `SCH80`, `XS` | `SCHEDULE 80 (EXTRA STRONG)` | ASME B36.10M Pipe Schedule |
| `SCH 160`, `SCH160`, `XXS` | `SCHEDULE 160 (DOUBLE EXTRA STRONG)` | ASME B36.10M Pipe Schedule |
| `T8`, `TRIM 8`, `TRIM8` | `API 600 TRIM 8 (13Cr / Hardfaced Stellite)` | Valve Trim Code |
| `T5`, `TRIM 5`, `TRIM5` | `API 600 TRIM 5 (Full Stellite / Hardfaced)` | Valve Trim Code |
| `T12`, `TRIM 12` | `API 600 TRIM 12 (316SS / Hardfaced)` | Valve Trim Code |

### 6.3 Regex Attribute Slot Extraction Architecture
The slot tagger extracts exact engineering dimensions and parameters from unstructured descriptions:
- **Nominal Bore Size ($NB$)**: Regex patterns captures `(\d+(?:\.\d+)?)\s*(?:IN|INCH|"|MM|NB)`. Converts imperial inches to metric millimeters (e.g. $6" \rightarrow 150\text{mm}$).
- **Pressure Class**: Captures `(?:CL|CLASS|#|LB|LBS)\s*(\d{3,4})` or `(\d{3,4})\s*(?:#|LB|LBS)`.
- **Material Metallurgy**: Identifies standard ASTM designations (`WCB`, `LCB`, `CF8M`, `A105`, `LF2`, `F316L`).
- **Flange Facing**: Detects `RF`, `RTJ`, `FF`, `BW`, `SW`, `NPT`.

### 6.4 BAAI/bge-m3 1024-Dimensional Dense Vectorization
The platform utilizes the **`BAAI/bge-m3`** dense embedding model running locally via HuggingFace SentenceTransformers:
- **Embedding Dimensions**: 1024 float32 values per item.
- **Context Length**: 8192 tokens (easily ingesting full catalog specifications and MTC text).
- **Multi-Lingual / Technical Domain Tuning**: Specifically capable of mapping non-trivial industrial synonyms (e.g. *stellite-faced wedge* to *API Trim 5*).

### 6.5 Qdrant Vector Engine & HNSW Cosine Indexing
Vector points are indexed within an on-premises instance of **Qdrant v1.12.0**:
- **Index Distance Metric**: Cosine Similarity:
  $$\text{Cosine}(u, v) = \frac{u \cdot v}{\|u\| \|v\|}$$
- **HNSW Parameters**:
  - `m = 16`: Number of bidirectional links per node in the graph hierarchy.
  - `ef_construct = 128`: Number of nearest neighbors evaluated during index creation.
  - `ef_search = 64`: Search exploration breadth balancing latency (< 15ms) and recall (> 99.2%).
- **Payload Filtering**: High-speed pre-filtering on `item_type` and `is_active` flags before vector distance computation.

---

## 7. Subsystem 3: Multi-Stage Hybrid Ranking & TreeSHAP Explainability

### 7.1 Multi-Stage Pipeline Architecture
To achieve millisecond response times across hundreds of thousands of CPSE inventory items without compromising safety or precision, Samanvay-AI deploys a 3-stage ranking pipeline:

```mermaid
flowchart LR
    Query["User Requisition Spec"] --> S1["Stage 1: Qdrant Dense Cosine Pre-Filter (Top 100 Candidates)"]
    S1 --> S2["Stage 2: Physical Subvector & Attribute Decomposition"]
    S2 --> S3["Stage 3: XGBoost Multi-Feature Ranking Classifier"]
    S3 --> SHAP["TreeSHAP Attribution Engine (Feature Contributions)"]
    SHAP --> SafetyFilter["Subsystem 4: 21 Deterministic Engineering Safety Modules"]
```

### 7.2 Physical Subvector Decomposition
Rather than relying on a single black-box semantic score, the candidate pair $(Q, C)$ is decomposed into a structured physical feature vector $\mathbf{x} \in \mathbb{R}^8$:
1. $x_1$: **Cosine Semantic Similarity** (BAAI/bge-m3 dense vector similarity).
2. $x_2$: **Nominal Size Delta Ratio** $\frac{|NB_Q - NB_C|}{NB_Q}$.
3. $x_3$: **Pressure Rating Compatibility Score** (Evaluated from ASME B16.5 ladder: downgrades = 0, exact = 1.0, safe upgrades = 0.85).
4. $x_4$: **Metallurgical Hierarchy Compatibility** (Evaluated via ASTM Material DAG).
5. $x_5$: **Facing Match Binary** ($1.0$ if matching, $0.0$ if mismatch).
6. $x_6$: **Sour Service NACE Alignment** ($1.0$ if safe, $-1.0$ if non-compliant).
7. $x_7$: **Bore Flow Ratio** (Full Bore vs Reduced Bore factor).
8. $x_8$: **Geographical Distance Penalty** $\exp\left(-\frac{d_{\text{km}}}{1000}\right)$.

### 7.3 XGBoost Ranking Model Architecture & Hyperparameters
The ranking classifier is parameterized as follows:
- **Algorithm**: XGBoost (`xgb.XGBClassifier` / `rank:pairwise`)
- **Number of Estimators**: 250
- **Max Tree Depth**: 5
- **Learning Rate (eta)**: 0.05
- **Subsample Ratio**: 0.85
- **Objective Function**: Pairwise logistic ranking loss.

### 7.4 TreeSHAP Attribution & Feature Importance Explainability
For every ranked candidate, TreeSHAP decomposes the model's prediction score $f(\mathbf{x})$ into additive feature attributions:

$$f(\mathbf{x}) = \phi_0 + \sum_{i=1}^{M} \phi_i(Q, C)$$

Where:
- $\phi_0$ is the base expected value across the training distribution.
- $\phi_i(Q, C)$ represents the exact positive or negative score contribution of feature $i$ (e.g. $+0.22$ for Exact Metallurgy Match, $-0.45$ for Pressure Class Mismatch).
- These attributions are directly exported to the frontend UI as human-readable engineering scorecards.

### 7.5 Active Learning Feedback Loop & In-Memory Trie Cache
When certified plant metallurgists or Chief Reliability Engineers manually approve or reject a Tier 2 substitution recommendation:
1. The approval/rejection tuple $(Q, C, \text{decision}, \text{user\_id}, \text{timestamp})$ is recorded in the `active_learning_feedback` log.
2. The normalized specification key is cached in an **In-Memory Trie Structure** for instant $O(k)$ lookup on identical subsequent queries across all CPSEs.
3. Once 100 new verified interactions accumulate, an asynchronous background retraining job updates the XGBoost ranking weights.


## 8. Subsystem 4: The 21 Codified Deterministic Engineering Safety Modules

The core safety engine of Samanvay-AI comprises **21 codified, deterministic engineering safety modules**. Implemented in pure Python under `rules/`, these modules encode statutory industrial codes and safety invariants. In accordance with **Invariant 2**, these rules hold unilateral veto authority over statistical AI rankings.

```
+----------------------------------------------------------------------------------------------------+
|                               THE 21 DETERMINISTIC SAFETY MODULES OVERVIEW                         |
+====================================================================================================+
| M01. ASME B16.5 / B16.34: Pressure Class Ladder & Operating PSI                                     |
| M02. ASTM Metallurgy DAG: Upgrades Permitted, Downgrades Prohibited, Cryogenic Limits               |
| M03. ASME B36.10M / B36.19M: Pipe Schedules & Wall Thickness Invariants                            |
| M04. NACE MR0175 / ISO 15156: Wet H2S Sour Service Hardness Ceilings (<= 22 HRC / 250 HV)           |
| M05. ASME B16.5: Flange Facings, Phonographic Serrations & Cast Iron Mating Rules                  |
| M06. ASME B16.47: Large Diameter Flanges Series Mismatch (Series A MSS SP-44 vs Series B API 605)  |
| M07. ASME B16.20: Gaskets Integrity, Spiral Wound Inner Rings & PTFE Creep                         |
| M08. ASTM A193 / A194: High/Low Temperature Fastener Pairing & Liquid Metal Embrittlement (LME)    |
| M09. API 6D: Pipeline Piggable Full Bore Flow Restrictions & Cavity Relief                         |
| M10. API 607 / API 6FA: Flammable Hydrocarbon Fire-Safe Dual Certification Invariants              |
| M11. API 600 / API 602: Valve Trim Material Degradation Ladder                                     |
| M12. API 520 / API 526: Pressure Safety Valve (PSV) Orifice Letter Sizing & CDTP Set Pressure      |
| M13. ISO 4126-2 / ASME Sec VIII: Rupture Disk Non-Fragmentation & Vacuum Support Invariants        |
| M14. ASME B16.48: Positive Isolation Spectacle Blinds, Spades & Spacers Thickness                  |
| M15. NACE SP0286: Flange Insulation Kits (FIK) & Cathodic Protection Breakdown Prevention          |
| M16. ASTM A269: Instrumentation Small-Bore Tubing & Metric/Imperial Swagelok Ferrule Traps         |
| M17. API 610: Centrifugal Pumps Nozzle Loads & Centerline Thermal Mounting                         |
| M18. API 682: Mechanical Seals & Pressurized Dual Barrier Piping Plans                             |
| M19. API 618 / API 617: Reciprocating & Centrifugal Gas Compressors Molecular Weight Limits        |
| M20. IS/IEC 60079 & ISO 15: Hazardous Area Motors & C3 Bearing Internal Radial Clearances          |
| M21. Equipment Safety: TEMA Exchanger Shells, API 2000 Venting & ASTM C795 Stress Corrosion        |
+----------------------------------------------------------------------------------------------------+
```

---

### 8.1 Module 1: ASME B16.5 / B16.34 Pressure Class Ladder & Operating PSI
- **Industrial Standards**: ASME B16.5 (Pipe Flanges and Flanged Fittings), ASME B16.34 (Valves Flanged, Threaded, and Welding End).
- **Physical Invariant**: A replacement component's pressure class must be greater than or equal to the requisition requirement ($Class_{\text{cand}} \ge Class_{\text{req}}$).
- **Ascending Class Ladder**:
  $$\text{Class 150} < \text{Class 300} < \text{Class 600} < \text{Class 800} < \text{Class 900} < \text{Class 1500} < \text{Class 2500}$$
- **Operational PSI Check**: If explicit operating pressure is provided, candidate design pressure $P_{\text{design}}(T)$ at design temperature $T$ must satisfy $P_{\text{design}}(T) \ge P_{\text{operating}}$.
- **Failure Classification**:
  - Class Downgrade (e.g. Class 150 candidate for Class 300 requisition) $\rightarrow$ **FATAL ERROR (Score = 0.0, Tier 3)**.
  - Safe Over-Rating (e.g. Class 300 candidate for Class 150 requisition) $\rightarrow$ **PERMITTED (Score = 0.85, Tier 2)** provided face-to-face dimensions and bolt hole circles are verified.

```python
def evaluate_pressure_class(req_class: int, cand_class: int, operating_psi: float = None) -> RuleResult:
    CLASS_LADDER = [150, 300, 600, 800, 900, 1500, 2500]
    if req_class not in CLASS_LADDER or cand_class not in CLASS_LADDER:
        return RuleResult(passed=False, score=0.0, fatal=True, reason="Invalid ASME Pressure Class")
    if cand_class < req_class:
        return RuleResult(
            passed=False, score=0.0, fatal=True,
            reason=f"FATAL: Candidate pressure class ({cand_class}#) is lower than required ({req_class}#)"
        )
    if cand_class == req_class:
        return RuleResult(passed=True, score=1.0, fatal=False, reason="Exact pressure class match")
    return RuleResult(
        passed=True, score=0.85, fatal=False,
        reason=f"Safe over-rating: Candidate {cand_class}# exceeds required {req_class}#"
    )
```

---

### 8.2 Module 2: ASTM Metallurgy Directed Acyclic Graph & Cryogenic Brittle Fracture Limits
- **Industrial Standards**: ASTM A105, ASTM A216 WCB, ASTM A350 LF2, ASTM A352 LCB/LCC, ASTM A182 F316L, ASTM A351 CF8M.
- **Physical Invariant**: Material substitutions must follow strict metallurgical upgrade hierarchies. Standard Carbon Steel (A105/WCB) cannot be used in sub-zero applications due to loss of Charpy V-notch impact toughness (ductile-to-brittle transition temperature $T_{\text{DBTT}} \approx -29^\circ\text{C}$).
- **Material Upgrade Hierarchy (DAG)**:
  $$\text{CS (WCB/A105)} \longrightarrow \text{LTCS (LCB/LF2)} \longrightarrow \text{Austenitic SS (CF8M/F316L)} \longrightarrow \text{Duplex SS (F51/2205)}$$
- **Cryogenic Temperature Invariants**:
  - $T_{\text{min}} < -29^\circ\text{C}$: Mandatory LTCS (ASTM A350 LF2 / A352 LCB) or Stainless Steel (CF8M). WCB/A105 strictly prohibited.
  - $T_{\text{min}} < -46^\circ\text{C}$: Mandatory Austenitic Stainless Steel (ASTM A182 F316L / A351 CF8M). LTCS strictly prohibited.

---

### 8.3 Module 3: ASME B36.10M / B36.19M Pipe Schedules & Wall Thickness Invariants
- **Industrial Standards**: ASME B36.10M (Welded and Seamless Wrought Steel Pipe), ASME B36.19M (Stainless Steel Pipe).
- **Physical Invariant**: For buttweld components (pipes, elbows, reducers, tees, BW valves), candidate wall thickness $t_{\text{cand}}$ must match or exceed required schedule wall thickness ($t_{\text{cand}} \ge t_{\text{req}}$) with inside bore diameter matching within $\pm 1.5\text{mm}$ to prevent catastrophic welding flow turbulence and erosion.
- **Ascending Schedule Ladder**:
  $$\text{SCH 10} < \text{SCH 20} < \text{SCH 30} < \text{SCH STD/40} < \text{SCH 60} < \text{SCH XS/80} < \text{SCH 120} < \text{SCH 160} < \text{SCH XXS}$$

---

### 8.4 Module 4: NACE MR0175 / ISO 15156 Wet H2S Sour Service Hardness Ceilings
- **Industrial Standards**: NACE MR0175 / ISO 15156 (Petroleum and natural gas industries — Materials for use in H2S-containing environments in oil and gas production).
- **Physical Invariant**: In wet sour hydrocarbon service ($P_{\text{H2S}} \ge 0.05\text{ psia}$), parent metallic materials and weld heat-affected zones (HAZ) must have maximum hardness $\le 22\text{ HRC}$ ($250\text{ HV}$) to prevent Hydrogen-Induced Stress Cracking (HSC) and Sulfide Stress Corrosion (SSC).
- **Fatal Trap**: Using non-NACE compliant standard carbon steel in sour service triggers an **immediate fatal veto (Score = 0.0, Tier 3)**.

---

### 8.5 Module 5: ASME B16.5 Flange Facings, Serrations & Cast Iron Mating Rules
- **Industrial Standards**: ASME B16.5 Section 6.4, MSS SP-6.
- **Physical Invariants**:
  1. **Facing Compatibility**: Raised Face (RF), Ring Type Joint (RTJ), and Flat Face (FF) geometries are strictly non-interchangeable. Mating RF to RTJ results in zero gasket seating and catastrophic leak.
  2. **Cast Iron Mating Rule**: When bolting a ductile/carbon steel flange to a brittle Cast Iron (ASTM A126) or Bronze component, a **Flat Face (FF)** with full-face elastomeric gasket is mandatory. Mating an RF flange with high-tensile bolts breaks cast iron flange necks due to bending moments.
  3. **Surface Finish / Phonographic Serrations**: Standard RF flanges require spiral serrated finish ($125 - 250\,\mu\text{in Ra}$ or $3.2 - 6.3\,\mu\text{m Ra}$). Hydrogen/gas service requires smooth finish ($63 - 125\,\mu\text{in Ra}$).

---

### 8.6 Module 6: ASME B16.47 Large Flange Series Mismatch (Series A vs Series B)
- **Industrial Standards**: ASME B16.47 (Large Diameter Steel Flanges: NPS 26 Through NPS 60 Metric/Inch Standard).
- **Physical Invariant**: For pipe diameters $\ge 26\text{ inches}$, flanges are split into two completely non-interoperable dimensional series:
  - **Series A (MSS SP-44)**: Heavier flange, larger bolt diameters, fewer bolt holes, designed for piping and general pipeline service.
  - **Series B (API 605)**: Compact flange, smaller bolt diameters, more bolt holes, designed for compact vessel nozzle attachments.
- **Rule**: Mating a Series A flange to a Series B flange is physically impossible due to bolt circle mismatch. Any candidate with mismatched Series is a **FATAL ERROR (Score = 0.0)**.

---

### 8.7 Module 7: ASME B16.20 Gaskets Integrity, Spiral Wound Inner Rings & PTFE Creep
- **Industrial Standards**: ASME B16.20 (Metallic Gaskets for Pipe Flanges), API 6FB.
- **Physical Invariants**:
  1. **Inner Retaining Ring Invariant**: For ASME Class 900, Class 1500, and Class 2500 spiral wound gaskets, or any Class 150/300 gasket with PTFE filler, a solid metallic **Inner Ring** is mandatory to prevent inward radial buckling into the pipe bore under compressive bolt load.
  2. **Ring Joint Gasket Metallurgy**: RTJ oval/octagonal gaskets (Soft Iron, Low Carbon Steel, 316SS) must have a hardness lower than the mating flange groove (minimum delta $\Delta \ge 15\text{ HB}$) to ensure gasket plastic deformation without damaging costly flange sealing grooves.

---

### 8.8 Module 8: ASTM A193 / A194 Fastener Pairing & Liquid Metal Embrittlement (LME)
- **Industrial Standards**: ASTM A193 (Alloy-Steel and Stainless Steel Bolting), ASTM A194 (Carbon and Alloy Steel Nuts for Bolts for High Pressure or High Temperature Service).
- **Physical Invariants**:
  1. **Standard High-Temperature Pairing**: ASTM A193 Grade B7 stud bolts must be paired exclusively with ASTM A194 Grade 2H heavy hex nuts.
  2. **Low-Temperature Pairing**: ASTM A193 Grade L7 stud bolts must be paired with ASTM A194 Grade 7 or Grade 4 nuts.
  3. **Liquid Metal Embrittlement (LME) Warning**: Cadmium-plated or galvanized fasteners must **NEVER** be used above $200^\circ\text{C}$ or with austenitic stainless steel flanges. Molten zinc/cadmium diffuses into austenitic grain boundaries, causing catastrophic LME rupture.

---

### 8.9 Module 9: API 6D Pipeline Piggable Full Bore Flow Restrictions
- **Industrial Standards**: API 6D (Specification for Pipeline and Piping Valves).
- **Physical Invariant**: On cross-country transmission pipelines designated as **Piggable** for Intelligent Inline Inspection (ILI / MFL PIGs), valve bore must be strictly **Full Bore (FB)** with continuous cylindrical bore matching pipe ID within $-0\text{mm}/+1.5\text{mm}$. Reduced Bore (RB) valves cause physical PIG blockage, pipeline shutdown, and excavation.

---

### 8.10 Module 10: API 607 / API 6FA Flammable Hydrocarbon Fire-Safe Certification
- **Industrial Standards**: API 607 (Fire Test for Quarter-turn Valves and Valves Equipped with Nonmetallic Seats), API 6FA (Specification for Fire Test for Valves).
- **Physical Invariant**: In flammable hydrocarbon services (Gasoline, LPG, LNG, Crude Oil, Hydrogen), all soft-seated ball, butterfly, and plug valves must carry valid **API 607 / API 6FA Fire-Safe Dual Certification**. In a plant fire ($760^\circ\text{C} - 1000^\circ\text{C}$), soft PTFE/PEEK seats disintegrate, requiring the secondary metal-to-metal backup seat to seal tightly. Installing non-fire-safe soft-seated valves in flammable lines is a **FATAL ERROR**.

---

### 8.11 Module 11: API 600 / API 602 Valve Trim Material Degradation Ladder
- **Industrial Standards**: API 600 (Steel Gate Valves - Flanged and Butt-welding Ends, Bolted Bonnets), API 602 (Compact Steel Gate Valves).
- **Physical Invariant**: Valve trim materials (stem, disc/wedge seating surfaces, backseat bushing) must follow strict wear, galling, and temperature resistance hierarchies:
  $$\text{Trim 1 (13Cr)} \le \text{Trim 8 (13Cr + Stellite)} \le \text{Trim 5 (Full Hardfaced Stellite)} \le \text{Trim 12 (316SS + Stellite)}$$
- **High-Differential Steam/Slurry**: High differential throttling or superheated steam service requires full hardfacing (**Trim 5 / Trim 8**). Substituting Trim 1 (unfaced 13Cr) into high-pressure steam service leads to rapid wire-drawing erosion and seat leakage within weeks.

---

### 8.12 Module 12: API 520 / API 526 Pressure Safety Valve (PSV) Orifice Sizing & CDTP
- **Industrial Standards**: API 520 (Sizing, Selection, and Installation of Pressure-relieving Devices), API 526 (Flanged Steel Pressure-relief Valves).
- **Physical Invariants**:
  1. **Standard API Orifice Letter Invariant**: PSV effective discharge areas follow strict API 526 letter designations:
     $$\text{D} (0.110\text{ in}^2) < \text{E} (0.196) < \text{F} (0.307) < \text{G} (0.503) < \text{H} (0.785) < \text{J} (1.287) < \text{K} (1.838) < \text{L} (2.853) < \text{M} (3.60) < \text{N} (4.34) < \text{P} (6.38) < \text{Q} (11.05) < \text{R} (16.00) < \text{T} (26.00)$$
     Candidate orifice area $A_{\text{cand}}$ must be $\ge A_{\text{req}}$. Undersized orifice letters cause catastrophic vessel overpressure during relief events.
  2. **Cold Differential Test Pressure (CDTP)**: Must account for backpressure and temperature correction factors:
     $$\text{CDTP} = \frac{\text{Set Pressure} - P_{\text{back}}}{K_{T}}$$

---

### 8.13 Module 13: ISO 4126-2 / ASME Sec VIII UG-127 Rupture Disk Non-Fragmentation Invariants
- **Industrial Standards**: ISO 4126-2 (Safety devices for protection against excessive pressure - Part 2: Bursting disc safety devices), ASME Section VIII Division 1 UG-127.
- **Physical Invariants**:
  1. **Non-Fragmentation Requirement**: When a rupture disk is installed upstream of a Pressure Safety Valve (PSV) to isolate corrosive media, the disk must be **Reverse Buckling / Cross-Scored Non-Fragmenting**. Forward-acting fragmenting disks shed metal petals upon burst, jamming the downstream PSV nozzle.
  2. **Manufacturing Range & Burst Tolerance**: Marked burst pressure must fall within $\pm 5\%$ of specified design burst rating at coincident burst temperature.

---

### 8.14 Module 14: ASME B16.48 Positive Isolation Spectacle Blinds & Spacers
- **Industrial Standards**: ASME B16.48 (Line Blanks).
- **Physical Invariant**: Line blanks (spectacle blinds, figure-8 blinds, paddle blanks, paddle spacers) must have design thickness $t_{\text{blank}}$ calculated to withstand full line design pressure $P$ without exceeding allowable bending stress $S$:
  $$t_{\text{min}} = d_g \sqrt{\frac{3 P}{16 S}} + c$$
  Where $d_g$ is gasket contact diameter and $c$ is corrosion allowance ($3.0\text{mm}$). Installing makeshift plate cutouts or thinner class blanks is a **FATAL ERROR**.

---

### 8.15 Module 15: NACE SP0286 Flange Insulation Kits (FIK) & Cathodic Protection
- **Industrial Standards**: NACE SP0286 (Electrical Isolation of Cathodically Protected Pipelines).
- **Physical Invariants**:
  1. **Galvanic Isolation Integrity**: When joining dissimilar metals (e.g. Carbon Steel pipeline to Duplex Stainless valve or Offshore Wellhead), a full Flange Insulation Kit (dielectric gasket, G10 insulating sleeves, G10/steel dual washers) is mandatory to prevent electrochemical galvanic corrosion.
  2. **Dielectric Strength**: Insulating material must possess dielectric breakdown strength $\ge 500\text{ V/mil}$ (e.g. GRE / G10 Glass Reinforced Epoxy). Nitrile/Neoprene kits are prohibited above $100^\circ\text{C}$ or in aromatic hydrocarbons.

---

### 8.16 Module 16: ASTM A269 Instrumentation Small-Bore Tubing & Metric/Imperial Ferrule Traps
- **Industrial Standards**: ASTM A269 (Seamless and Welded Austenitic Stainless Steel Tubing for General Service).
- **Physical Invariants**:
  1. **Metric vs Fractional Imperial Outer Diameter**: Cross-mating fractional imperial tubing (e.g. $1/2" = 12.70\text{mm}$) with metric compression fittings (e.g. $12.00\text{mm}$) or vice versa causes improper ferrule swaging and catastrophic high-pressure blow-off ($> 100\text{ bar}$).
  2. **Tubing Hardness vs Ferrule Hardness**: Stainless steel tubing hardness must not exceed **$90\text{ HRB}$ ($200\text{ HV}$)** to permit Swagelok/Parker twin ferrules to bite into the tube wall without slipping.

---

### 8.17 Module 17: API 610 Centrifugal Pumps & Centerline Thermal Mounting
- **Industrial Standards**: API 610 / ISO 13709 (Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries, 12th Edition).
- **Physical Invariants**:
  1. **Thermal Centerline Support Invariant**: For pumping temperatures $T > 150^\circ\text{C}$ (e.g. hot crude bottoms, vacuum residue), pump casing must be **Centerline Mounted (API 610 Type OH2 / BB2)**. Foot-mounted pumps (Type OH1) expand upward when heated, causing severe shaft angular misalignment, bearing seizure, and mechanical seal destruction.
  2. **Nozzle Allowable Forces and Moments ($F_N, M_N$)**: Replacement pump nozzles must withstand standardized API 610 Table 5 nozzle loading envelopes without casing distortion.

---

### 8.18 Module 18: API 682 Mechanical Seals & Pressurized Barrier Piping Plans
- **Industrial Standards**: API 682 4th Edition / ISO 21049 (Pumps - Shaft Sealing Systems for Centrifugal and Rotary Pumps).
- **Physical Invariants**:
  1. **Toxic / Category 1 Hydrocarbon Containment**: Pumping hazardous, toxic, or light hydrocarbons ($RVP > 0.7\text{ bar}$) mandates **Dual Pressurized Barrier Seals (Arrangement 3)** with API Piping Plan 53A/53B/54 maintaining barrier fluid pressure at least $1.4\text{ bar}$ ($20\text{ psi}$) above seal chamber pressure.
  2. **Plan 11 / Plan 21 Flush Quench**: Single seals (Arrangement 1) are strictly prohibited on toxic sour services.

---

### 8.19 Module 19: API 618 / API 617 Reciprocating & Centrifugal Gas Compressors
- **Industrial Standards**: API 618 (Reciprocating Compressors for Petroleum, Chemical, and Gas Industry Services), API 617 (Axial and Centrifugal Compressors).
- **Physical Invariants**:
  1. **Gas Molecular Weight ($MW$) & Density Variation**: Centrifugal compressor impellers are engineered for specific gas molecular weight envelopes. A substitute rotor designed for lighter gas ($MW = 18\text{ g/mol}$) operating on heavy gas ($MW = 44\text{ g/mol}$) causes excessive gas bending loads and surge line instability.
  2. **Cylinder Cooling & Rod Load Reversal**: Reciprocating compressor piston rod replacement must satisfy rod reversal angle criteria ($> 15^\circ$ of crank rotation with negative load) to maintain hydrodynamic crosshead pin lubrication.

---

### 8.20 Module 20: IS/IEC 60079 & ISO 15 Hazardous Area Motors & C3 Bearing Clearances
- **Industrial Standards**: IS/IEC 60079 (Explosive Atmospheres - Equipment Protection by Flameproof Enclosures 'd' / Increased Safety 'e'), ISO 15.
- **Physical Invariants**:
  1. **Hazardous Zone Classification**: Motors in Zone 1 / Zone 0 hazardous refinery environments must be certified **Ex d (Flameproof) IIC T4** or higher. Installing an Ex nA or safe-area industrial motor in a Zone 1 hydrogen/hydrocarbon plant triggers an **immediate catastrophic fire hazard (Score = 0.0, FATAL)**.
  2. **Internal Radial Bearing Clearance (C3)**: High-speed electric motor bearings subjected to rotor thermal expansion require **ISO C3 clearance** ($15 - 30\,\mu\text{m}$). Standard (CN) clearance bearings suffer radial preloading and catastrophic thermal seizure at operating speeds.

---

### 8.21 Module 21: Equipment Safety: TEMA Exchangers, API 2000 Tanks & ASTM C795 Insulation
- **Industrial Standards**: TEMA Standards 10th Edition (Tubular Exchanger Manufacturers Association), API 2000 (Venting Atmospheric and Low-pressure Storage Tanks), ASTM C795.
- **Physical Invariants**:
  1. **TEMA Tube-to-Tubesheet Joint Differential Expansion**: In fixed tubesheet heat exchangers (TEMA Class R), substitute tube metallurgy must match shell thermal expansion coefficients $\alpha_T$ within $\pm 10\%$ to prevent tube buckling or pull-out from tubesheets.
  2. **API 2000 Emergency Inbreathing/Outbreathing**: Storage tank breather valves (PVRV) must match required volumetric venting capacity ($Nm^3/hr$) calculated from thermal outbreathing plus maximum liquid pump-in rate.
  3. **ASTM C795 Stress Corrosion Cracking (SCC) Inhibited Thermal Insulation**: Thermal insulation applied over austenitic stainless steel piping (SS 304/316) operating between $50^\circ\text{C}$ and $150^\circ\text{C}$ must be certified **ASTM C795 compliant** (leachable chlorides, fluorides, silicates, and sodium plotted within the Karnes curve) to prevent External Stress Corrosion Cracking (ESCC) under insulation (CUI).


## 9. Subsystem 5: Dynamic Compatibility Tiers & Public Procurement Alignment

### 9.1 Mathematical Formulation of Dynamic Compatibility Tiers
In strict compliance with **Invariant 1** and **Invariant 2**, compatibility between a Requisition Query $Q$ and a Candidate Spare Part $C$ is computed dynamically:

$$S(Q, C) = \begin{cases} 0.0 & \text{if } \exists i \in \{1 \dots 21\} \text{ such that } \text{Rule}_i(Q, C) = \text{FATAL} \\ f_{\text{XGBoost}}(\mathbf{x}) & \text{if all rules PASS} \end{cases}$$

The dynamic score is mapped to sovereign operational tiers:

| Dynamic Tier | Compatibility Score | Operational Meaning | System Action & Workflow |
| :--- | :--- | :--- | :--- |
| **Tier 1: Direct Interchangeable** | $S(Q, C) \ge 0.90$ | Exact drop-in replacement or safe over-rating. Zero engineering modifications required. | Immediate 1-Click Requisition Dispatch & CISF Gate Pass Generation. |
| **Tier 2: Functional Substitute** | $0.75 \le S(Q, C) < 0.90$ | Minor physical delta (e.g. Schedule 80 vs Schedule 40, Trim 5 vs Trim 8). Safe to operate. | Requires Human-in-the-Loop (HITL) Sign-off by Plant Reliability Engineer. |
| **Tier 3: Incompatible** | $S(Q, C) < 0.75$ | Critical safety rule violation, pressure downgrade, cryogenic embrittlement risk. | **Hard System Veto**. Requisition is strictly blocked; cannot be dispatched. |

```mermaid
flowchart TD
    Candidate["Candidate Part C & Requisition Q"] --> RulesCheck{"Execute 21 Deterministic Safety Modules"}
    RulesCheck -- "Any Fatal Rule Violations" --> CapScore["Cap Score: S(Q,C) <= 0.74 (FATAL)"]
    CapScore --> Tier3["Tier 3: Incompatible (VETOED)"]

    RulesCheck -- "All Safety Invariants PASS" --> MLScore["Compute XGBoost Score f(x)"]
    MLScore --> ScoreEval{"Evaluate Score S(Q,C)"}
    ScoreEval -- "S >= 0.90" --> Tier1["Tier 1: Direct Interchangeable (Instant Dispatch)"]
    ScoreEval -- "0.75 <= S < 0.90" --> Tier2["Tier 2: Functional Substitute (HITL Approval Required)"]
    ScoreEval -- "S < 0.75" --> Tier3
```

---

### 9.2 Indian Public Procurement Alignment: BIS/IS Equivalent Mapping
To facilitate sovereign procurement across Indian public sector enterprises, the platform maintains a dual-directional cross-reference between international standards (ASTM/ASME/API) and the Bureau of Indian Standards (BIS/IS):

| Component Category | International Standard | Indian Standard (BIS / IS) | Technical Specification Alignment |
| :--- | :--- | :--- | :--- |
| **Cast Carbon Steel Valves** | ASTM A216 Grade WCB | **IS 14846 / IS 2062 Grade B** | Spheroidal & structural cast steel grades with tensile $\ge 485\text{ MPa}$. |
| **Forged Carbon Steel Fittings**| ASTM A105 | **IS 1875 Class 2 / Class 4** | High-pressure forged carbon steel for piping flanges and fittings. |
| **Low-Temp Carbon Steel** | ASTM A350 LF2 / A352 LCB | **IS 2041 Grade R260** | Normalized fine-grain steel impact tested at $-46^\circ\text{C}$. |
| **Austenitic Stainless Steel** | ASTM A182 F316L / A312 TP316L| **IS 6911 Grade X02Cr17Ni12Mo2** | Low-carbon molybdenum austenitic stainless steel for chemical service. |
| **High-Pressure Bolting** | ASTM A193 Grade B7 | **IS 1367 Part 3 Grade 10.9** | High-tensile chromium-molybdenum alloy steel heat-treated fasteners. |
| **Flanged Pipe Fittings** | ASME B16.5 | **IS 6392 / IS 1538** | Steel pipe flanges and flanged fittings dimensional envelopes. |
| **Centrifugal Process Pumps** | API 610 12th Edition | **IS 5120 / IS 15660** | Technical specifications for centrifugal pumps in petroleum & gas. |
| **Flameproof Motors** | IEC 60079-1 | **IS/IEC 60079-1 (Ex d IIC)** | Flameproof enclosure requirements for hazardous hydrocarbon zones. |

---

### 9.3 Public Procurement (Preference to Make in India) Order (PPP-MII) Compliance
Samanvay-AI integrates the Government of India's **Public Procurement (Preference to Make in India) Order (PPP-MII 2017 / Revised 2020)** directly into the ranking engine:
- **Class-I Local Supplier**: Local content $\ge 50\%$. Ranked with highest priority in search results; eligible for statutory purchase preference.
- **Class-II Local Supplier**: Local content $\ge 20\%$ and $< 50\%$.
- **Non-Local Supplier**: Local content $< 20\%$.

When peer CPSEs search for replacements, items manufactured by certified Indian suppliers with verified local content percentages receive an explicit Make-in-India badge and local content multiplier in multi-depot optimization.

---

### 9.4 GeM (Government e-Marketplace) & CPPP Tender Interoperability
The platform provides pre-purchase discovery integration for enterprise procurement workflows. Prior to floating an external public tender on the **Central Public Procurement Portal (CPPP)** or **Government e-Marketplace (GeM)**, procurement officers execute an automated *Surplus Clearance Check*. If an identical or functional substitute spare part is sitting idle ($> 180\text{ days}$) at a sister CPSE depot within 500 km, the system issues a **Pre-Purchase Interception Advisory**, preventing redundant tender expenditures.

---

## 10. Subsystem 6: Knowledge Graph & National Logistics Topology Engine

### 10.1 Neo4j 5.20 Property Star Graph Schema
The geographical, operational, and organizational topology of India's hydrocarbon infrastructure is modeled in **Neo4j 5.20 Community Edition**:

```mermaid
graph TD
    Enterprise["(:Enterprise {code, name})"] -->|OWNS| Depot["(:Depot {code, name, lat, lon, plant_type})"]
    Depot -->|STOCKS| Item["(:Item {item_code, desc, category, quantity, days_idle})"]
    Depot -->|CONNECTED_TO {distance_km, transit_hours, route_type}| Depot
```

#### Node Labels & Properties:
- `(:Enterprise)`: `{enterprise_code: "IOCL", enterprise_name: "Indian Oil Corporation Limited"}`
- `(:Depot)`: `{depot_code: "IOCL_PANIPAT", name: "Panipat Refinery", latitude: 29.3909, longitude: 76.9635, plant_type: "REFINERY"}`
- `(:Item)`: `{item_id: "...", item_code: "VLV-GT-300-150", quantity: 4, days_idle: 210, is_active: true}`

#### Relationship Types:
- `(:Enterprise)-[:OWNS]->(:Depot)`
- `(:Depot)-[:STOCKS {quantity: 4, reserved: 0}]->(:Item)`
- `(:Depot)-[:CONNECTED_TO {distance_km: 1460.5, transit_hours: 40.5, road_quality: "NH_EXPRESSWAY"}]->(:Depot)`

---

### 10.2 The 19 National CPSE Hydrocarbon Depots & GPS Coordinates Matrix

| # | Enterprise | Depot / Plant Location Name | State | Latitude (°N) | Longitude (°E) | Plant Category | Railhead / Highway Connectivity |
| :- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **IOCL** | **Panipat Refinery & Petrochemical Complex** | Haryana | $29.3909$ | $76.9635$ | Mega Refinery / Petrochem | NH-44 / Panipat Junction |
| **2** | **IOCL** | **Mathura Refinery** | Uttar Pradesh | $27.4924$ | $77.6737$ | Refinery / Downstream | NH-19 / Mathura Junction |
| **3** | **IOCL** | **Gujarat Refinery (Koyali, Vadodara)** | Gujarat | $22.3588$ | $73.1311$ | Mega Refinery / Petrochem | NH-48 / Vadodara Junction |
| **4** | **IOCL** | **Paradip Refinery** | Odisha | $20.2644$ | $86.6084$ | Coastal Deepwater Refinery | NH-53 / Paradip Port Rail |
| **5** | **IOCL** | **Haldia Refinery** | West Bengal | $22.0620$ | $88.0610$ | Coastal Refinery / Lube | NH-116 / Haldia Port Rail |
| **6** | **ONGC** | **Hazira Gas Processing Plant** | Gujarat | $21.1120$ | $72.6510$ | Sour Gas Sweetening Plant | NH-53 / Surat Broad Gauge |
| **7** | **ONGC** | **Uran Gas Processing & LPG Terminal** | Maharashtra | $18.8870$ | $72.9400$ | Offshore Terminal & Gas | JNPT Rail Corridor |
| **8** | **ONGC** | **Ankleshwar Asset Regional Depot** | Gujarat | $21.6260$ | $73.0030$ | Onshore Exploration Asset | NH-48 / Western Dedicated Freight |
| **9** | **ONGC** | **Nazira Regional Headquarters & Base** | Assam | $26.9180$ | $94.7330$ | North-East Exploration Base | Simaluguri Junction |
| **10**| **BPCL** | **Mumbai Refinery (Mahul)** | Maharashtra | $19.0100$ | $72.8900$ | Coastal Mega Refinery | Mumbai Port Trust Rail |
| **11**| **BPCL** | **Kochi Refinery (Ambalamugal)** | Kerala | $9.9810$ | $76.3570$ | Coastal Petrochem Refinery | NH-85 / Cochin Port Rail |
| **12**| **BPCL** | **Bina Refinery (Bharat Oman Refineries)** | Madhya Pradesh| $24.2380$ | $78.1880$ | Inland Mega Refinery | Bina Junction / Central Freight |
| **13**| **HPCL** | **Mumbai Refinery (Chembur)** | Maharashtra | $19.0050$ | $72.8850$ | Coastal Refinery / Lubes | Mumbai Port Trust Rail |
| **14**| **HPCL** | **Visakhapatnam Refinery (Vizag)** | Andhra Pradesh| $17.6868$ | $83.2185$ | Coastal Mega Refinery | NH-16 / Vizag Port Rail |
| **15**| **HPCL** | **Guru Gobind Singh Refinery (Bathinda - HMEL)**| Punjab | $30.1280$ | $74.9220$ | Strategic Inland Refinery | Bathinda Multi-Junction Rail |
| **16**| **GAIL** | **Pata Petrochemical Complex** | Uttar Pradesh | $26.6080$ | $79.5280$ | Gas Cracker & Polymer | NH-19 / Auraiya Rail Siding |
| **17**| **GAIL** | **Vijaipur Gas Compressor Complex** | Madhya Pradesh| $24.2620$ | $77.3040$ | HVJ Pipeline Core Hub | Guna Junction / Rail Corridor |
| **18**| **OIL** | **Duliajan Operational Headquarters** | Assam | $27.3580$ | $95.3190$ | Exploration & Gas Grid Base | Dibrugarh Railway Division |
| **19**| **NRL** | **Numaligarh Refinery Complex** | Assam | $26.5980$ | $93.7580$ | Strategic North-East Refinery | NH-129 / Numaligarh Rail Siding |

---

### 10.3 Haversine Great-Circle Geodesic Distance
The direct spherical angular distance $\Delta\sigma$ between Depot $A (\phi_1, \lambda_1)$ and Depot $B (\phi_2, \lambda_2)$ is computed via the Haversine equation:

$$\Delta\phi = \phi_2 - \phi_1, \quad \Delta\lambda = \lambda_2 - \lambda_1$$

$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1) \cos(\phi_2) \sin^2\left(\frac{\Delta\lambda}{2}\right)$$

$$d_{\text{haversine}} = 2 R \cdot \arctan2\left(\sqrt{a}, \sqrt{1-a}\right)$$

Where $R = 6371.0\text{ km}$ is the volumetric mean radius of the Earth.

---

### 10.4 Indian National Highway Tortuosity Factor Formulation (1.28x)
Real-world highway routing across the Indian subcontinent deviates from straight-line geodesic vectors due to geography, mountain passes, and highway network topology. Samanvay-AI applies the empirically calibrated **Indian National Highway Tortuosity Factor ($	au_{\text{NH}} = 1.28$)**:

$$d_{\text{road}} = 1.28 \times d_{\text{haversine}}$$

---

### 10.5 Freight Economics & Transit Time Calculations
- **Heavy Industrial Commercial Transit Speed**: $v_{\text{avg}} = 36.0\text{ km/h}$ (reflecting Indian heavy commercial vehicle regulations, toll gates, and state border checkpoints).
- **Estimated Road Transit Time**:
  $$t_{\text{transit}} = \frac{d_{\text{road}}}{36.0\text{ km/h}} + t_{\text{handling}}$$
  Where $t_{\text{handling}} = 4.0\text{ hours}$ for crane loading, strapping, and CISF gate clearance.
- **Dedicated Heavy Freight Transport Cost**:
  $$\text{Cost}_{\text{freight}} = \max\left(₹15,000,\; d_{\text{road}} \times ₹45.00/\text{km}\right)$$

---

### 10.6 Bureau of Energy Efficiency (BEE) Carbon Savings Model
When an emergency spare part is obtained via the domestic CPSE mutual-aid mesh instead of air-freighting new manufacturing imports from Europe or North America, the platform computes total greenhouse gas emissions abated in accordance with **Bureau of Energy Efficiency (BEE)** and **IPCC** carbon guidelines:

$$\text{Emissions}_{\text{Domestic Road}} = d_{\text{road}} \times 0.125\text{ kg CO}_2/\text{km}$$

$$\text{Emissions}_{\text{Air Import Baseline}} = 1.150\text{ kg CO}_2/\text{ton-km} \times 8500\text{ km} \times W_{\text{metric tons}}$$

$$\Delta\text{CO}_2\text{ Saved} = \text{Emissions}_{\text{Air Import Baseline}} - \text{Emissions}_{\text{Domestic Road}}$$

---

## 11. Subsystem 7: Transactional Concurrency, Row Locks & Real-Time CDC

### 11.1 Atomic Pessimistic Locking Workflow (`SELECT ... FOR UPDATE`)
In emergency plant shutdown scenarios, multiple CPSE refineries may simultaneously attempt to requisition the same critical spare part sitting in a remote surplus depot. To eliminate catastrophic double-allocation or race conditions, Samanvay-AI enforces **ACID Transaction Isolation** via PostgreSQL row-level pessimistic locking:

```sql
-- Transaction Begins
BEGIN;

-- Step 1: Pessimistic Row Lock with Exclusive Row Lock
SELECT id, quantity, reserved_quantity, item_code
FROM items
WHERE id = 'c7a8b9e0-1234-5678-9abc-def012345678'
FOR UPDATE;

-- Step 2: In-Transaction Inventory Integrity Verification
-- Application verifies: (quantity - reserved_quantity) >= requested_quantity

-- Step 3: Atomic Stock Reservation
UPDATE items
SET reserved_quantity = reserved_quantity + 2,
    updated_at = NOW()
WHERE id = 'c7a8b9e0-1234-5678-9abc-def012345678';

-- Step 4: Loan Record Creation
INSERT INTO loans (
    id, item_id, borrower_enterprise_code, lender_enterprise_code,
    borrower_depot_id, lender_depot_id, quantity, status,
    urgency_level, auto_release_at, created_at
) VALUES (
    gen_random_uuid(), 'c7a8b9e0-1234-5678-9abc-def012345678', 'BPCL', 'IOCL',
    'depot_bpcl_mumbai', 'depot_iocl_panipat', 2, 'APPROVED',
    'EMERGENCY', NOW() + INTERVAL '7 days', NOW()
);

-- Step 5: CDC Outbox Event Creation
INSERT INTO cdc_outbox (
    id, aggregate_type, aggregate_id, event_type, payload, created_at
) VALUES (
    gen_random_uuid(), 'ITEM', 'c7a8b9e0-1234-5678-9abc-def012345678',
    'ITEM_STOCK_RESERVED', '{"reserved": 2, "borrower": "BPCL"}', NOW()
);

-- Transaction Commits & Releases Row Lock
COMMIT;
```

---

### 11.2 Multi-Depot Stock Reservation & Expiry Lifecycle (7-Day Auto-Release)
When a requisition requests more units than any single depot possesses (e.g. Requisition requires 10 valves, Depot A has 6, Depot B has 4), the **Multi-Depot Split Allocation Engine** executes coordinated row-level locks across all participating depots within a single database transaction.

Every approved requisition carries a strict **7-Day Auto-Release Timer** (`auto_release_at`). If the borrowing CPSE fails to dispatch physical transport or issue CISF gate clearance within 168 hours, an automated Celery/PostgreSQL background worker cancels the reservation, restores available quantities, and logs a timeout event in the Merkle audit trail.

---

### 11.3 PostgreSQL Transactional CDC Outbox Architecture
To keep the Neo4j Knowledge Graph and Qdrant Vector DB synchronized without dual-write inconsistencies, all state-changing operations write events to the **`cdc_outbox`** table within the *same database transaction* as the entity update.

```mermaid
flowchart LR
    AppTx["API Transaction (Loan / Item Update)"] --> DB_Write["Write to 'items' / 'loans' Table"]
    AppTx --> Outbox_Write["Write to 'cdc_outbox' Table"]
    DB_Write & Outbox_Write --> Commit["ACID DB Commit"]
    Commit --> PG_Notify["PostgreSQL Trigger: pg_notify('samanvay_cdc_channel', outbox_id)"]
    PG_Notify --> Worker["Async Background Syncer (LISTEN samanvay_cdc_channel)"]
    Worker --> Neo4jSync["Sync Neo4j Graph Topology & Quantities"]
    Worker --> QdrantSync["Sync Qdrant Vector Payloads"]
```

---

### 11.4 Asynchronous Neo4j Graph Synchronization via PostgreSQL LISTEN/NOTIFY
A lightweight Python daemon runs `LISTEN samanvay_cdc_channel;` on the PostgreSQL connection pool. Upon notification, it drains unprocessed outbox rows and executes idempotent Cypher updates:

```cypher
MATCH (d:Depot {depot_code: $depot_code})-[r:STOCKS]->(i:Item {item_code: $item_code})
SET r.quantity = $new_quantity,
    r.reserved = $new_reserved,
    r.last_updated = timestamp()
RETURN r;
```

---

## 12. Subsystem 8: Cryptographic Merkle Audit Ledger & Anti-Tamper Security

### 12.1 Merkle Block Structure & Parent Hash Invariants ($H_0 = 	ext{"000...000"}$)
To guarantee total anti-tamper security for statutory reviews by the **Comptroller and Auditor General (CAG)** and internal vigilance officers, every state transition (loan creation, gate pass generation, physical receipt, return) is permanently written to an append-only cryptographic chain.

```mermaid
flowchart LR
    Genesis["Genesis Block 0<br/>Parent Hash: 00000000...0000"] --> Block1["Audit Block 1<br/>Parent: H0<br/>Hash: H1"]
    Block1 --> Block2["Audit Block 2<br/>Parent: H1<br/>Hash: H2"]
    Block2 --> Block3["Audit Block N<br/>Parent: H(N-1)<br/>Hash: HN"]
```

- **Genesis Parent Hash ($H_0$)**: Exactly 64 zero characters:
  `"0000000000000000000000000000000000000000000000000000000000000000"`
- **Block Hash Formulation**:
  $$H_k = \text{SHA-256}\left(\text{CanonicalJSON}\left(id, \text{parent\_hash}_{k-1}, \text{event\_type}, \text{actor\_id}, \text{enterprise\_code}, \text{payload}, \text{timestamp}\right)\right)$$

---

### 12.2 Cryptographic Event Block Model & Canonical JSON Serialization
To prevent cryptographic hash divergences across different server architectures or Python/JavaScript serialization engines, all JSON payloads are normalized using **Canonical JSON (RFC 8785)**:
- Keys are sorted lexicographically in ASCII order.
- Whitespace is strictly eliminated (`separators=(',', ':')`).
- Floating point values are rendered with deterministic precision.

```python
import hashlib
import json

def generate_audit_hash(parent_hash: str, event_type: str, actor_id: str,
                        enterprise_code: str, payload: dict, timestamp: str) -> str:
    canonical_dict = {
        "actor_id": actor_id,
        "enterprise_code": enterprise_code,
        "event_type": event_type,
        "parent_hash": parent_hash,
        "payload": payload,
        "timestamp": timestamp
    }
    canonical_bytes = json.dumps(canonical_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(canonical_bytes).hexdigest()
```

---

### 12.3 Cryptographic Chain Integrity Verification Algorithm
The system provides a 1-click CAG Audit Verification endpoint that scans the entire chain from genesis to head in $O(N)$ time:

```python
def verify_merkle_chain_integrity(audit_blocks: list) -> tuple[bool, str]:
    if not audit_blocks:
        return True, "Empty ledger"
    
    expected_parent = "0" * 64
    for idx, block in enumerate(audit_blocks):
        if block.parent_hash != expected_parent:
            return False, f"Broken chain link at index {idx}: Block parent_hash mismatch"
        
        computed_hash = generate_audit_hash(
            parent_hash=block.parent_hash,
            event_type=block.event_type,
            actor_id=block.actor_id,
            enterprise_code=block.enterprise_code,
            payload=block.payload,
            timestamp=block.timestamp.isoformat()
        )
        if computed_hash != block.current_hash:
            return False, f"Tampered record detected at block index {idx} (ID: {block.id})"
        
        expected_parent = block.current_hash
        
    return True, f"Cryptographic integrity verified across {len(audit_blocks)} blocks"
```

---

### 12.4 Role-Based Access Control (RBAC) & Sovereign Multi-Tenancy Architecture
Samanvay-AI enforces strict multi-tenant boundary isolation and cryptographic Segregation of Duties (SoD) using signed JWT tokens containing claims:
- `sub`: Username (e.g. `iocl_eng`, `ongc_mm`).
- `cpse`: Tenant enterprise code (`OIL`, `IOCL`, `ONGC`, `BPCL`, `HPCL`, `GAIL`, `NRL`, `MOPNG`, `ADMIN`).
- `depot_id`: Assigned refinery depot identifier (e.g. `IOCL-PANIPAT`, `ONGC-URAN`).
- `role`: Production RBAC role:
  - **`SITE_ENGINEER`**: Search catalog, run multi-property discovery, inspect technical scorecards, initiate borrow requisitions.
  - **`MATERIALS_MANAGER`**: Authorize/reject surplus material release for their depot, manage depot inventory status, triage HITL queues.
  - **`CISF_SECURITY`**: Sentry gate verification, inspect SHA-256 digital seals, sign and issue physical digital gate passes with inline SVG QR codes.
  - **`TECHNICAL_AUTHORITY`**: Evaluate Tier 2 engineering substitutions, verify MTC chemistry ($CE_{\text{IIW}}$, PREN), and review welding preheat waivers.
  - **`VIGILANCE_AUDITOR`**: Read-only sovereign audit verification, trace cryptographic Merkle hash chains root-to-tip, export RFC 4180 CSV reports for CVC/CAG statutory reviews.
  - **`SUPER_ADMIN`**: Global inter-CPSE administration, user lifecycle governance, and interactive multi-tenant context switching.

#### 12.4.1 Multi-Tenant Consignment Isolation (`list_requisitions_for_user`)
Consignment visibility is strictly scoped at the database layer via `list_requisitions_for_user(db, user)`:
- **`SUPER_ADMIN` / `VIGILANCE_AUDITOR`**: Full federation visibility across all inter-CPSE requisitions.
- **`MATERIALS_MANAGER`**: Can inspect incoming demands where `source_depot == user.depot_id` or `source_cpse == user.cpse` (to approve surplus releases), plus their own created requisitions.
- **`SITE_ENGINEER` / Standard Officers**: Strictly restricted to requisitions they individually submitted (`requested_by == user.username`) or incoming transfers to their immediate depot. Requisitions between unrelated CPSEs are completely shielded.

#### 12.4.2 Segregation of Duties (SoD) & Self-Approval Prevention
To prevent unauthorized transfer of public assets and ensure compliance with Central Vigilance Commission (CVC) statutory guidelines:
- A user who creates a requisition is **strictly prohibited from approving it** (`HTTP 403 Forbidden: Segregation of Duties violation: Requesters cannot approve their own requisitions`).
- Only a `MATERIALS_MANAGER` belonging to the **supplying CPSE** can authorize surplus release.
- Only a `CISF_SECURITY` officer can issue the digital gate pass with its cryptographic SHA-256 seal.

#### 12.4.3 The 25+ Pre-Configured Demo Persona Matrix
The database auto-seeder initializes pre-configured persona accounts across all 7 CPSEs, Central MoPNG Vigilance, and Super Admin (all with default credentials: `Samanvay@2026`):

| Username | CPSE / Org | Depot | Role | Key Capabilities |
|---|---|---|---|---|
| `oil_eng` | OIL | Duliajan | `SITE_ENGINEER` | Creates exploration & pipeline requisitions |
| `oil_mm` | OIL | Duliajan | `MATERIALS_MANAGER` | Authorizes Duliajan central store surplus releases |
| `oil_sec` | OIL | Duliajan | `CISF_SECURITY` | Issues physical digital gate passes at Duliajan |
| `iocl_eng` | IOCL | Panipat | `SITE_ENGINEER` | Requisitions refinery spares, tests isolation |
| `iocl_mm` | IOCL | Panipat | `MATERIALS_MANAGER` | Approves Panipat refinery surplus releases |
| `iocl_sec` | IOCL | Panipat | `CISF_SECURITY` | Gate pass verification for outward logistics |
| `ongc_eng` | ONGC | Uran | `SITE_ENGINEER` | Offshore/onshore asset maintenance demands |
| `ongc_mm` | ONGC | Uran | `MATERIALS_MANAGER` | Authorizes Uran gas complex surplus releases |
| `ongc_sec` | ONGC | Uran | `CISF_SECURITY` | Sentry verification at Uran checkpoint |
| `bpcl_eng` | BPCL | Mahul | `SITE_ENGINEER` | Refinery maintenance borrow requests |
| `bpcl_mm` | BPCL | Mahul | `MATERIALS_MANAGER` | Authorizes Mumbai refinery surplus dispatch |
| `bpcl_sec` | BPCL | Mahul | `CISF_SECURITY` | Issues gate passes at Mahul gate |
| `hpcl_eng` | HPCL | Visakh | `SITE_ENGINEER` | Coastal refinery maintenance requisitions |
| `hpcl_mm` | HPCL | Visakh | `MATERIALS_MANAGER` | Authorizes Visakh refinery surplus dispatch |
| `hpcl_sec` | HPCL | Visakh | `CISF_SECURITY` | Security verification at Visakh refinery |
| `gail_eng` | GAIL | Pata | `SITE_ENGINEER` | Gas transmission & petrochemical demands |
| `gail_mm` | GAIL | Pata | `MATERIALS_MANAGER` | Authorizes Pata petrochemical surplus release |
| `gail_sec` | GAIL | Pata | `CISF_SECURITY` | Gate sentry at Pata complex |
| `nrl_eng` | NRL | Numaligarh | `SITE_ENGINEER` | North-East hydrocracker spare requisitions |
| `nrl_mm` | NRL | Numaligarh | `MATERIALS_MANAGER` | Authorizes Numaligarh refinery surplus release |
| `nrl_sec` | NRL | Numaligarh | `CISF_SECURITY` | Gate pass issuance at Numaligarh |
| `mopng_tech` | MoPNG | Central | `TECHNICAL_AUTHORITY` | Reviews technical waivers & MTC overrides |
| `mopng_auditor` | MoPNG | Central | `VIGILANCE_AUDITOR` | Full sovereign audit verification & CAG CSV export |
| `super_admin` | ADMIN | HQ | `SUPER_ADMIN` | Global tenant switching & system administration |


## 13. Subsystem 9: Sovereign CISF Physical Verification & Pure SVG QR Gate Pass

### 13.1 Air-Gapped Pure SVG 25x25 QR Bit Matrix Engine
In compliance with **Invariant 4**, the generation of security gate passes and digital verification barcodes must execute without any external third-party cloud APIs (such as Google Charts API or external CDN JavaScript bundles). 

Samanvay-AI implements a pure, client-side mathematical QR bit-matrix generator that computes standard ISO/IEC 18004 QR matrices and renders them as deterministic, inline scalable vector graphics (SVG) with zero network calls:

```typescript
// Pure In-Memory SVG 25x25 QR Matrix Generator (No External Libraries)
export function renderPureSVGQR(dataString: string, sizePx: number = 200): string {
  const matrix = computeISO18004Matrix(dataString); // 25x25 boolean grid
  const cellSize = sizePx / matrix.length;
  
  let rects = '';
  for (let r = 0; r < matrix.length; r++) {
    for (let c = 0; c < matrix[r].length; c++) {
      if (matrix[r][c]) {
        rects += `<rect x="${c * cellSize}" y="${r * cellSize}" width="${cellSize}" height="${cellSize}" fill="#0f172a" />`;
      }
    }
  }
  
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${sizePx} ${sizePx}" width="${sizePx}" height="${sizePx}">
    <rect width="100%" height="100%" fill="#ffffff" />
    ${rects}
  </svg>`;
}
```

---

### 13.2 CISF Physical Gate Pass Layout & Security Seal Verification
When a spare part loan is approved by the lending enterprise, the platform compiles an official **Ministry of Petroleum & Natural Gas Sovereign Inter-CPSE Material Transfer Gate Pass**:

```
+----------------------------------------------------------------------------------------------------+
|                MINISTRY OF PETROLEUM & NATURAL GAS (MoPNG) - GOVERNMENT OF INDIA                   |
|                        SOVEREIGN INTER-CPSE MATERIAL TRANSFER PASS                                 |
+====================================================================================================+
| GATE PASS NO: GP-2026-IOCL-BPCL-004291               DATE OF ISSUE: 2026-09-27 18:30 IST           |
| DISPATCH DEPOT: IOCL Panipat Refinery (Haryana)      RECEIVING DEPOT: BPCL Mumbai Refinery (Maha)  |
+----------------------------------------------------------------------------------------------------+
| ITEM DESCRIPTION: 6IN CLASS 300 WCB GATE VALVE API 600 TRIM 8 RF FLANGED (IS 14846 / ASME B16.34)  |
| ITEM CODE: IOCL-MAT-VLV-49102                        QUANTITY DISPATCHED: 2 NOS (HEAVY CRATE)      |
| REQUISITION URGENCY: EMERGENCY PLANT SHUTDOWN        AUTHORIZED LOAN ID: LN-8849-IOCL-BPCL         |
| VEHICLE REGISTRATION: HR-06-EA-9912 (GPS TRACKED)    TRANSPORTER: CONCOR INTER-MODAL HEAVY         |
+----------------------------------------------------------------------------------------------------+
|                                      CRYPTOGRAPHIC VERIFICATION                                    |
| [  PURE SVG 25x25 QR CODE  ]       MERKLE BLOCK HASH: 8f9c1a704e6b2d10...09f2                      |
| [  CONTAINING SIGNED JSON  ]       DIGITAL SECURITY SEAL: SHA256-AUTH-VERIFIED                     |
|                                    CAG AUDIT COMPLIANCE: MoPNG-CPSE-GRID-OK                        |
+----------------------------------------------------------------------------------------------------+
| CISF SECURITY CHECKPOINT CLEARANCE:                                                                |
| [ ] OUTWARD GATE CLEARANCE (IOCL PANIPAT): CISF INSPECTOR SIGN & STAMP: ________________________   |
| [ ] INWARD GATE CLEARANCE (BPCL MUMBAI):  CISF INSPECTOR SIGN & STAMP: ________________________   |
+----------------------------------------------------------------------------------------------------+
```

---

### 13.3 End-to-End Handheld Scanner Verification Workflow
1. **Scanning**: At the refinery exit perimeter, the CISF security officer scans the printed or mobile SVG QR pass using an air-gapped Android rugged handheld terminal.
2. **Payload Parsing**: The terminal extracts the compact JSON payload:
   `{"gp_no":"GP-2026-IOCL-BPCL-004291","loan_id":"LN-8849","item_code":"VLV-49102","qty":2,"hash":"8f9c1a..."}`.
3. **Local Intranet Verification**: The terminal queries the local depot node via mTLS. The node re-computes the Merkle hash against the PostgreSQL database.
4. **Instant Visual Authorization**: A green **`CISF CLEARANCE GRANTED`** screen appears with item photo, vehicle number, and dispatch manifest.

---

## 14. Subsystem 10: PostgreSQL Database Schema & Complete Data Dictionary

### 14.1 Complete Database DDL SQL Specification

```sql
-- ============================================================================
-- SAMANVAY-AI PRODUCTION DATABASE DDL SCHEMA (POSTGRESQL 16)
-- ============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enums
CREATE TYPE enterprise_enum AS ENUM ('IOCL', 'ONGC', 'BPCL', 'HPCL', 'GAIL', 'OIL', 'NRL');
CREATE TYPE plant_type_enum AS ENUM ('REFINERY', 'PETROCHEMICAL', 'GAS_PROCESSING', 'EXPLORATION_ASSET', 'OFFSHORE_BASE', 'COMPRESSOR_STATION');
CREATE TYPE user_role_enum AS ENUM ('PLANT_ENGINEER', 'RELIABILITY_LEAD', 'DEPOT_SUPERVISOR', 'CAG_AUDITOR', 'SYSTEM_ADMIN');
CREATE TYPE loan_status_enum AS ENUM ('PENDING', 'APPROVED', 'DISPATCHED', 'IN_TRANSIT', 'RECEIVED', 'RETURNED', 'REJECTED', 'EXPIRED');
CREATE TYPE urgency_level_enum AS ENUM ('ROUTINE', 'PLANNED_MAINTENANCE', 'URGENT', 'EMERGENCY_SHUTDOWN');

-- 1. Enterprises Table
CREATE TABLE enterprises (
    code enterprise_enum PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ministry VARCHAR(255) DEFAULT 'Ministry of Petroleum & Natural Gas',
    headquarters_city VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Depots Table
CREATE TABLE depots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enterprise_code enterprise_enum NOT NULL REFERENCES enterprises(code) ON DELETE CASCADE,
    depot_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    state VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    plant_type plant_type_enum NOT NULL,
    railhead_connected BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enterprise_code enterprise_enum NOT NULL REFERENCES enterprises(code),
    depot_id UUID REFERENCES depots(id),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role_enum NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Inventory Items Table
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    depot_id UUID NOT NULL REFERENCES depots(id) ON DELETE CASCADE,
    enterprise_code enterprise_enum NOT NULL REFERENCES enterprises(code),
    item_code VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    item_type VARCHAR(100) NOT NULL,
    size_nb_mm DOUBLE PRECISION,
    pressure_class INT,
    schedule VARCHAR(50),
    metallurgy VARCHAR(100),
    flange_facing VARCHAR(50),
    trim_designation VARCHAR(50),
    indian_standard VARCHAR(100),
    make_in_india_class VARCHAR(50) DEFAULT 'Class-I',
    local_content_percentage DOUBLE PRECISION DEFAULT 80.0,
    quantity INT NOT NULL CHECK (quantity >= 0),
    reserved_quantity INT NOT NULL DEFAULT 0 CHECK (reserved_quantity >= 0 AND reserved_quantity <= quantity),
    unit_of_measure VARCHAR(20) DEFAULT 'NOS',
    days_idle INT DEFAULT 0,
    unit_cost_inr NUMERIC(15, 2), -- Sovereign Protected
    total_value_inr NUMERIC(15, 2), -- Sovereign Protected
    po_number VARCHAR(100), -- Sovereign Protected
    mtc_document_url TEXT,
    mtc_carbon_equivalent DOUBLE PRECISION,
    mtc_pren DOUBLE PRECISION,
    mtc_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Inter-CPSE Loans Table
CREATE TABLE loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_reference_no VARCHAR(100) UNIQUE NOT NULL,
    item_id UUID NOT NULL REFERENCES items(id),
    borrower_enterprise_code enterprise_enum NOT NULL REFERENCES enterprises(code),
    lender_enterprise_code enterprise_enum NOT NULL REFERENCES enterprises(code),
    borrower_depot_id UUID NOT NULL REFERENCES depots(id),
    lender_depot_id UUID NOT NULL REFERENCES depots(id),
    quantity INT NOT NULL CHECK (quantity > 0),
    status loan_status_enum NOT NULL DEFAULT 'PENDING',
    urgency_level urgency_level_enum NOT NULL,
    reason TEXT NOT NULL,
    dispatched_at TIMESTAMP WITH TIME ZONE,
    received_at TIMESTAMP WITH TIME ZONE,
    returned_at TIMESTAMP WITH TIME ZONE,
    auto_release_at TIMESTAMP WITH TIME ZONE NOT NULL,
    gate_pass_number VARCHAR(100) UNIQUE,
    vehicle_number VARCHAR(50),
    transporter_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Cryptographic Merkle Audit Events Table
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sequence_no BIGSERIAL UNIQUE NOT NULL,
    parent_hash CHAR(64) NOT NULL,
    current_hash CHAR(64) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    actor_id VARCHAR(100) NOT NULL,
    enterprise_code enterprise_enum NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Transactional CDC Outbox Table
CREATE TABLE cdc_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type VARCHAR(50) NOT NULL,
    aggregate_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indices for High Performance
CREATE INDEX idx_items_depot ON items(depot_id);
CREATE INDEX idx_items_enterprise ON items(enterprise_code);
CREATE INDEX idx_items_type_class ON items(item_type, pressure_class);
CREATE INDEX idx_loans_borrower ON loans(borrower_enterprise_code, status);
CREATE INDEX idx_loans_lender ON loans(lender_enterprise_code, status);
CREATE INDEX idx_audit_parent_hash ON audit_events(parent_hash);
CREATE INDEX idx_cdc_unprocessed ON cdc_outbox(processed) WHERE processed = false;
```

---

### 14.2 Detailed Field Data Dictionary & Foreign Key Invariants
- **`items.reserved_quantity`**: Strictly bounded by database constraints ($0 \le \text{reserved} \le \text{quantity}$). Checked atomically via row-level locks.
- **`items.unit_cost_inr` & `items.po_number`**: Stripped dynamically by FastAPI serializers during cross-enterprise data requests (**Invariant 3**).
- **`audit_events.parent_hash`**: Strict cryptographic linkage to prior block; sequence number indexed for linear $O(N)$ audit verification.
- **`loans.auto_release_at`**: Automated timestamp set to $\text{NOW}() + 7\text{ days}$ during reservation.

---

## 15. Subsystem 11: Comprehensive API Specification & Pydantic Data Contracts

### 15.1 OpenAPI Endpoints Reference Directory

| HTTP Verb | Path | Protected Role | Functional Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/token` | Public | User authentication & JWT token generation. |
| `POST` | `/api/v1/search/discover` | Authenticated | Semantic discovery radar executing multi-stage ranking & safety rules. |
| `POST` | `/api/v1/ocr/upload` | Engineer / Lead | Fast-path & PaddleOCR MTC document parser with chemistry calculations. |
| `GET` | `/api/v1/items` | Authenticated | Filterable inventory catalog with sovereign privacy protection. |
| `POST` | `/api/v1/loans/request` | Engineer | Atomic multi-depot reservation and loan application. |
| `POST` | `/api/v1/loans/{id}/approve` | Reliability Lead | Lead authorization for Tier 2 substitutions and dispatch. |
| `GET` | `/api/v1/loans/{id}/gate-pass`| Supervisor / CISF | Generates pure inline SVG 25x25 QR CISF Gate Pass. |
| `GET` | `/api/v1/audit/verify-chain` | CAG Auditor | Full-chain cryptographic Merkle integrity verification. |
| `GET` | `/api/v1/depots/topology` | Authenticated | Returns 19 CPSE depots with live stock counts and GIS coordinates. |

---

### 15.2 Pydantic Validation Models & Schemas

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Discovery Search Request
class DiscoverySearchRequest(BaseModel):
    query_text: str = Field(..., example="6IN Class 300 WCB Gate Valve API 600 Trim 8 RF")
    target_depot_id: Optional[UUID] = None
    max_distance_km: Optional[float] = Field(default=2500.0, ge=0.0)
    required_quantity: int = Field(default=1, ge=1)
    operating_temperature_c: Optional[float] = None
    is_sour_service_nace: Optional[bool] = False

# Ranked Candidate Response
class CandidateMatchResponse(BaseModel):
    item_id: UUID
    enterprise_code: str
    depot_name: str
    item_code: str
    description: str
    quantity_available: int
    days_idle: int
    compatibility_score: float
    tier: str
    is_safe_to_dispatch: bool
    distance_km: float
    estimated_transit_hours: float
    carbon_abated_kg: float
    shap_explanations: List[str]
    rule_verdicts: List[dict]

# MTC Extraction Result
class MTCChemistryResponse(BaseModel):
    document_hash: str
    extracted_text: str
    detected_grade: str
    carbon_percentage: float
    manganese_percentage: float
    chromium_percentage: float
    nickel_percentage: float
    molybdenum_percentage: float
    carbon_equivalent_iiw: float
    pren_score: Optional[float]
    astm_envelope_passed: bool
    weldability_verdict: str
```

---

## 16. Subsystem 12: Frontend Architecture & User Interface Design

### 16.1 Minimalist Design System & Visual Foundations
Built on **Next.js 16 (App Router)** with Turbopack, **React 19**, and **Tailwind CSS v4**, the frontend interface follows a modern, high-precision industrial minimalist aesthetic inspired by **Linear**, **Vercel**, and **Palantir Foundry**:
- **Monochromatic Zinc/Slate Palette**: 95% neutral off-black/white foundation (`#09090b` dark canvas, `#121215` elevated panels, `#fafafa` light canvas) paired with crisp 1px hairline borders (`border-zinc-200` light, `border-zinc-800` dark) and micro-borders instead of heavy drop shadows to eliminate cognitive fatigue for refinery superintendents during 8–10 hour shifts.
- **Dual Typographic Discipline**:
  - Primary Interface Copy: **Geist Sans** (high x-height geometric sans-serif for UI labels and navigation).
  - Technical Data & Numerals: **JetBrains Mono** (`tabular-nums lining-nums`) for exact vertical alignment of ASTM ladle chemistry, SKU identifiers, monetary metrics (₹ Cr), and SHA-256 cryptographic hashes.
- **Purposeful Semantic Status Accents**: Saturated colors are strictly reserved for functional status communication:
  - `Emerald` (`#10b981`): Verified, Tier 1 Direct Substitute, SHA-256 Valid, Gate Pass Authorized.
  - `Amber` (`#f59e0b`): Caution, Tier 2 Conditional Match, HITL Metallurgical Review Required.
  - `Rose` (`#f43f5e`): Veto, Tier 3 Incompatible, ASME Flange Mismatch, Cryptographic Tamper Alert.

### 16.2 Navigation & App Shell Architecture
- **Single-Origin Reverse Proxy (`next.config.ts`)**:
  - The Next.js 16 standalone container internally rewrites `/api/v1/:path*` to `http://samanvay-ai-backend:8000/api/v1/:path*`.
  - Eliminates Cross-Origin Resource Sharing (CORS) preflights, cookie partitioning issues, and mixed-content SSL errors when running over public Cloudflare Tunnels.
- **Locked Organization Header Badge (`AppShell.tsx`)**:
  - Standard officers (`SITE_ENGINEER`, `MATERIALS_MANAGER`, `CISF_SECURITY`) have an un-editable locked organization badge reflecting their sovereign CPSE and refinery depot assignment (e.g. `[IOCL] Panipat Refinery Stores`).
  - Only `SUPER_ADMIN` accounts possess the interactive dual-dropdown switcher to emulate and inspect operations across any CPSE and depot.
- **Collapsible Desktop Sidebar & Mobile-Responsive Slide-Out Sheet**:
  - Desktop (`md:flex`): Smoothly expands to 240px (`w-60`) or collapses to a 56px (`w-14`) minimal icon dock. Global `[` keyboard shortcut and toggle button.
  - Mobile (`< 768px`): Hidden by default. Slide-over drawer with backdrop overlay triggered via a hamburger menu with ergonomic touch targets ($> 44\times 44\text{px}$) per Apple/Google HIG guidelines, auto-closing upon route navigation.
- **Compact 48px Utility Bar (`AppShell.tsx`)**:
  - Unobtrusive 48px height (`h-12`) preserving vertical workspace height.
  - Hierarchical breadcrumbs (`MoPNG Mesh > [Active View]`).
  - Persistent CPSE Tenant Badge with live backend connection pulse.
  - Global Command Palette trigger button (`⌘K` / `Ctrl+K`).
- **Comprehensive Global Command Palette (`CommandPalette.tsx`)**:
  - Instant keyboard access via `Cmd+K` or `Ctrl+K`.
  - Live fuzzy search across parts, SKUs, and MTCs via backend PostgreSQL and vector search.
  - Instant CPSE Context Switcher for administrators (`OIL`, `IOCL`, `ONGC`, `BPCL`, `HPCL`, `GAIL`, `NRL`).
  - Quick action shortcuts: Export CAG Audit CSV, Verify Merkle Ledger, Scan CISF Gate Pass.

### 16.3 High-Density Information Architecture & Inspection Pattern
- **Balanced Compact 38px Table Standard**:
  - Compact table rows (`.compact-table`, 38px row height) providing 16–22 data rows above the fold.
  - Right-aligned tabular monospaced numbers for physical dimensions, quantities, and pricing.
- **Multi-Property Specification Search Panel (`/discover`)**:
  - Expandable drawer accepting detailed engineering filters: Nominal Bore (`size_nb_mm`), ASME Pressure Class, Pipe Schedule, ASTM Metallurgy Grade, IIW Weldability Class (`HIGH_WELDABILITY`, `STANDARD`, `NON_WELDABLE`), NACE MR0175 sour service compliance, flange facing ends, and API 600 valve trims.
  - Dynamically calculates Compatibility Tiers (Tier 1 Drop-in, Tier 2 Functional Substitute, Tier 3 Incompatible) without pre-baked static tier assumptions (Invariant #1 & #2).
- **Sliding Side Inspector Drawer (`SideDrawer.tsx` in `src/components/ui`)**:
  - Palantir/Linear style 480px slide-over inspection sheet sliding from the right edge when any inventory or surplus item row is clicked.
  - Retains operator's table scroll position and active filter state while surfacing:
    1. 21 deterministic mechanical safety gate checklist (Pass/Fail green/red status indicators).
    2. ASTM ladle chemistry comparison table (C, Mn, P, S, Si, CE).
    3. Road logistics route & 1.28x road tortuosity transit calculation.
    4. Direct Inter-CPSE loan requisition transfer form.
- **Subtle Hairline Skeletons (`Skeleton`)**:
  - Zero-layout-shift hairline shimmer placeholders that match table row geometry during live data fetching.
- **Strict Zero-Mock Data Guarantee**:
  - Zero mock data arrays, zero fake fallbacks, and zero hardcoded property fabrications.
  - All views bind strictly to live backend API routes (`/api/v1/...`). Missing or unreadable data safely defaults to empty arrays (`[]`), `null`, or manual editable fields.

### 16.4 Route Topography
- `/login`: 1-Click Sovereign Evaluation Hub featuring 25+ pre-configured demo personas categorized across 10 filter tabs (`ALL`, `OIL`, `IOCL`, `ONGC`, `BPCL`, `HPCL`, `GAIL`, `NRL`, `MOPNG`, `ADMIN`).
- `/dashboard`: Role-adaptive Command Center with live KPI cards, active requisitions, interactive GIS refinery depot map, and Merkle ledger status.
- `/discover`: Multi-Property Specification Search with category segmented pills, compact table, dynamic tri-tier calculation, and slide-over 21-gate inspector drawer.
- `/inventory`: Plant stock ledger and HITL triage desk with 1-click surplus broadcasting.
- `/upload`: PyMuPDF and PaddleOCR MTC document dropzone with recent document tracking.
- `/upload/review`: Interactive manual property review screen with unreadable scan fallback protection and client-side $CE_{\text{IIW}}$ recalculation.
- `/requests`: Consignment and loan requisition manager with persona-scoped tabs (`"My Outgoing Requisitions"`, `"Incoming Depot Requests"`, `"All Requisitions"`) and Segregation of Duties approval controls.
- `/requests/[id]`: Printable CISF Gate Pass with standalone SVG QR bit-matrix and cryptographic SHA-256 seal.
- `/audit`: Sovereign cryptographic audit trail with SHA-256 linked blocks and 1-click CAG RFC-4180 export.
- `/admin/users`: Sovereign identity management and node authorization desk.


## 17. Subsystem 13: Dataset Architecture & Golden Benchmarks

### 17.1 Golden Benchmark Dataset (`golden_benchmarks.json`)
To evaluate machine learning models and deterministic safety logic under rigorous testing conditions, Samanvay-AI establishes a standardized **150-scenario Golden Benchmark Dataset** curated by certified refinery piping and materials engineers:

```mermaid
pie title Golden Benchmark Dataset Distribution (150 Ground Truth Pairs)
    "Tier 1: Identical / Safe Over-rating (50 Pairs)" : 50
    "Tier 2: Functional Substitutes (50 Pairs)" : 50
    "Tier 3: Fatal Safety Traps (50 Pairs)" : 50
```

#### Benchmark Categories:
1. **Tier 1 Direct Interchangeable (50 Pairs)**:
   - Identical dimensional, metallurgical, and pressure class matches across different CPSE catalog abbreviations.
   - Dual-certified ASTM/IS equivalents (e.g. ASTM A216 WCB $\leftrightarrow$ IS 14846).
   - ASME Class 600 candidate replacing Class 300 requisition in non-restricted utility service.
2. **Tier 2 Functional Substitutes (50 Pairs)**:
   - Schedule 80 pipe replacing Schedule 40 (heavier wall thickness acceptable with flow verification).
   - API 600 Trim 5 (Full Stellite) replacing Trim 8 (13Cr/Stellite) in standard valve service.
   - Low Temperature Carbon Steel (ASTM A350 LF2) replacing standard ASTM A105 carbon steel in ambient utility line.
3. **Tier 3 Fatal Incompatibilities (50 Pairs)**:
   - Pressure class downgrade (Class 150 candidate for Class 600 requisition).
   - Cryogenic fracture trap (ASTM A105 carbon steel candidate for $-50^\circ\text{C}$ LNG service).
   - Sour gas cracking trap (Non-NACE carbon steel > 22 HRC candidate for wet H2S line).
   - Flange series mismatch (ASME B16.47 Series A vs Series B 36" flange).
   - Swagelok metric $12\text{mm}$ ferrule mated to $1/2"$ ($12.7\text{mm}$) imperial tubing.
   - Standard CN clearance bearing installed in 3000 RPM high-temperature boiler feed motor.

---

### 17.2 CPSE Synthetic Inventory Seed Generator
The platform includes an automated synthetic inventory seed script (`scripts/seed_inventory.py`) that populates the PostgreSQL database with over **5,000 hyper-realistic CPSE inventory records** distributed across all 19 national depots. It accurately simulates:
- Realistic CPSE-specific abbreviation dialects and catalog patterns.
- Idle durations ranging from 30 days to 750+ days.
- Sovereign pricing attributes (`unit_cost_inr` between ₹2,500 and ₹45,00,000).
- Indian Standard (BIS/IS) alignments and Make-in-India local content percentages (55% to 95%).

---

### 17.3 Real-World MTC Document Test Corpus
A curated corpus of digitized Material Test Certificates (MTC EN 10204 Type 3.1) representing:
- Carbon steel forgings (ASTM A105).
- Low temperature alloy castings (ASTM A352 LCB).
- High alloy stainless forgings (ASTM A182 F316L).
- Duplex stainless steel bar stock (ASTM A182 F51 / 2205 Duplex).

---

## 18. Subsystem 14: Comprehensive Test Suite & Quality Verification Matrix

### 18.1 Tolerance Rules Verification Matrix
The Python test suite under `tests/unit/test_tolerance.py` validates every safety boundary across all 21 safety modules:

| Test Module | Test Method | Test Scenario & Boundary Condition | Expected Result |
| :--- | :--- | :--- | :--- |
| `test_tolerance.py` | `test_pressure_class_upgrade` | Requisition: 150#, Candidate: 300# | **PASS (Score = 0.85, Tier 2)** |
| `test_tolerance.py` | `test_pressure_class_downgrade` | Requisition: 600#, Candidate: 300# | **FATAL (Score = 0.0, Tier 3)** |
| `test_tolerance.py` | `test_cryogenic_wcb_failure` | Requisition: $-45^\circ\text{C}$, Candidate: ASTM A216 WCB | **FATAL (Score = 0.0, Tier 3)** |
| `test_tolerance.py` | `test_sour_gas_nace_violation` | Requisition: NACE Sour, Candidate: Standard CS 25 HRC | **FATAL (Score = 0.0, Tier 3)** |
| `test_tolerance.py` | `test_flange_series_mismatch` | Requisition: B16.47 Series A, Candidate: Series B | **FATAL (Score = 0.0, Tier 3)** |
| `test_tolerance.py` | `test_piggable_bore_restriction`| Requisition: API 6D Full Bore, Candidate: Reduced Bore | **FATAL (Score = 0.0, Tier 3)** |
| `test_tolerance.py` | `test_hazardous_motor_zone` | Requisition: Zone 1 IIC, Candidate: Safe Area Industrial | **FATAL (Score = 0.0, Tier 3)** |
| `test_tolerance.py` | `test_bearing_c3_clearance` | Requisition: C3 High Speed, Candidate: CN Standard | **FATAL (Score = 0.0, Tier 3)** |

---

### 18.2 OCR & Chemistry Engine Verification Suite
Implemented under `tests/unit/test_chemistry.py`:
- Validates IIW Carbon Equivalent formula against known ladle analyses ($CE_{\text{IIW}} = \%C + \frac{\%Mn}{6} + \frac{\%Cr+\%Mo+\%V}{5} + \frac{\%Ni+\%Cu}{15}$).
- Verifies PREN calculations for SS 316L ($ge 23$) and 2205 Duplex ($ge 34$).
- Tests automatic rejection of certificates exceeding ASTM maximum phosphorus ($> 0.040\%$) and sulfur ($> 0.040\%$).

---

### 18.3 Cryptographic Merkle Ledger Verification Tests
Implemented under `tests/unit/test_security.py`:
- Tests Genesis block hash generation ($H_0 = \text{"000...000"}$).
- Simulates intentional payload tampering (modifying quantity in Block 3) and verifies that `verify_merkle_chain_integrity` immediately halts and pinpoints the corrupted block ID.
- Verifies password hashing via Bcrypt with salt rounds $ge 12$.

---

### 18.4 Multi-Depot Concurrency & Allocation Integration Tests
Implemented under `tests/integration/test_concurrency.py`:
- Simulates 20 concurrent threads attempting to reserve 10 items from a depot holding only 5 units.
- Verifies that exactly 5 units are reserved across successful transactions and remaining threads receive clean `409 Conflict` errors without database corruption or deadlock.

---

## 19. Subsystem 15: Containerization, Deployment & Air-Gapped Operation

### 19.1 Multi-Container Docker Compose Architecture
Samanvay-AI is fully containerized using **Docker Compose**, orchestrating five core microservices:

```yaml
version: '3.8'

services:
  samanvay-postgres:
    image: postgres:16-alpine
    container_name: samanvay-postgres
    restart: always
    environment:
      POSTGRES_DB: samanvay_db
      POSTGRES_USER: samanvay_admin
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U samanvay_admin -d samanvay_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  samanvay-qdrant:
    image: qdrant/qdrant:v1.12.0
    container_name: samanvay-qdrant
    restart: always
    environment:
      QDRANT__TELEMETRY_DISABLED: "true"
    ports:
      - "6333:6333"
    volumes:
      - qdrantdata:/qdrant/storage

  samanvay-neo4j:
    image: neo4j:5.20-community
    container_name: samanvay-neo4j
    restart: always
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc"]'
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4jdata:/data

  samanvay-backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    container_name: samanvay-backend
    restart: always
    depends_on:
      samanvay-postgres:
        condition: service_healthy
      samanvay-qdrant:
        condition: service_started
      samanvay-neo4j:
        condition: service_started
    environment:
      DATABASE_URL: postgresql://samanvay_admin:${POSTGRES_PASSWORD}@samanvay-postgres:5432/samanvay_db
      QDRANT_HOST: samanvay-qdrant
      QDRANT_PORT: 6333
      NEO4J_URI: bolt://samanvay-neo4j:7687
      NEO4J_PASSWORD: ${NEO4J_PASSWORD}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    ports:
      - "8000:8000"

  samanvay-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: samanvay-frontend
    restart: always
    depends_on:
      - samanvay-backend
    environment:
      NEXT_PUBLIC_API_URL: http://samanvay-backend:8000
    ports:
      - "3000:3000"

volumes:
  pgdata:
  qdrantdata:
  neo4jdata:
```

---

### 19.2 Zero-Cloud Air-Gapped Sovereign Deployment Guide
1. **Model Pre-Packaging**: The `BAAI/bge-m3` model weights (approx 2.2 GB) and PaddleOCR models are bundled into local Docker layers at build time.
2. **Offline Installation**: On air-gapped refinery servers, Docker images are loaded via `docker load -i samanvay_v2_bundle.tar.gz`.
3. **Internal Intranet Binding**: Services bind strictly to internal NICNET / CPSE private IPv4 subnets (`10.x.x.x` or `172.16.x.x`) with external internet gateways disabled.

---

### 19.3 Production Environment Variables & Security Configuration

| Environment Variable | Description | Security Requirement |
| :--- | :--- | :--- |
| `POSTGRES_PASSWORD` | Master PostgreSQL database password. | Minimum 32 characters, high entropy. |
| `NEO4J_PASSWORD` | Master Neo4j graph database password. | Minimum 32 characters. |
| `JWT_SECRET_KEY` | Symmetric encryption key for JWT token signing. | Cryptographically random 256-bit key. |
| `QDRANT__TELEMETRY_DISABLED` | Disables outbound telemetry calls. | Mandatory `true` in air-gapped nodes. |
| `MERKLE_GENESIS_HASH` | Immutable root parent hash. | Exactly 64 hexadecimal zeros. |

---

## 20. Subsystem 16: Future Roadmap & Long-Term Sovereign Grid Expansion

### 20.1 Autonomous CPSE Tender Interception (CPPP & GeM Integration)
Development of automated webhook connectors into the **Central Public Procurement Portal (CPPP)** and **Government e-Marketplace (GeM)**. Whenever a CPSE uploads a Notice Inviting Tender (NIT) for spare parts procurement, Samanvay-AI will automatically parse the bill of quantities (BOQ) and notify the procurement officer if idle surplus is available across sister CPSEs before external purchase orders are issued.

### 20.2 Federated Edge Nodes on Offshore Platforms (WASM / SQLite)
Deployment of ultra-lightweight WebAssembly (WASM) and SQLite edge nodes aboard **ONGC offshore drilling rigs and platforms** (e.g. Mumbai High, Neelam, Heera). During satellite communication outages, offshore maintenance engineers can execute local deterministic tolerance evaluations and log emergency requisitions that automatically synchronize upon link restoration.

### 20.3 Advanced Drone & Aerial Logistics Integration for Emergency Corridors
Establishment of coordinated emergency aerial dispatch corridors with the Ministry of Civil Aviation and MoPNG for rapid transport of lightweight, mission-critical instrumentation (e.g. Rupture Disks, High-Pressure Sensors, Mechanical Seal Cartridges) via heavy-lift autonomous logistics UAVs.

---

## 21. Document Certification & Team Sign-Off

This document constitutes the official, ground-truth Master System Specification and Technical Architecture Blueprint for **Samanvay-AI (SIH26099)**. It has been authored, verified, and certified by the BharatCodex engineering team for submission to the **Ministry of Petroleum & Natural Gas (MoPNG)**, Government of India.

```
+----------------------------------------------------------------------------------------------------+
|                                    BHARATCODEX ENGINEERING TEAM SIGN-OFF                            |
+====================================================================================================+
| Team Leader:                                                                                       |
|   - Mayank Anand                  (Full-Stack Architecture, ML & Deterministic Safety Engine)       |
|                                                                                                    |
| Core Engineering Team:                                                                             |
|   - Hariom Chandra Tripathi       (Backend Architecture, ACID Concurrency & CDC Outbox)             |
|   - Shourya Mishra                (Neo4j Graph Logistics, Spatial Geodesics & BEE Models)           |
|   - Harsh Rajput                  (Computer Vision, Dual-Path OCR & MTC Chemistry Engine)           |
|   - Ranvijay Yadav                (Cryptographic Merkle Audit Ledger & Air-Gapped Gate Pass)        |
|   - Samriddhi Mishra              (Next.js 16 Sovereign UI/UX Design & Quality Engineering)        |
+----------------------------------------------------------------------------------------------------+
| Submission Date: September 2026                                                                    |
| Project Status: Production Ready (v2.0.0-PROD)                                                     |
| Classification: Sovereign Hydrocarbon Critical Infrastructure Specification Sheet                  |
+----------------------------------------------------------------------------------------------------+
```


## 22. Comprehensive File-by-File Codebase Audit & Architectural Inventory

To guarantee total transparency, reproducibility, and technical rigor, this section documents **every single source, test, configuration, schema, and rule file** across the entire Samanvay-AI repository (200+ distinct files). Each entry details the exact normalized file path, total line count, key exported classes/functions, and its precise functional role within the sovereign mutual-aid mesh.

---

### 22.1 Directory: `backend` (39 Files)

| File Path | Lines | Key Symbols / Classes / Functions | Architectural Role & Implementation Details |
| :--- | :--- | :--- | :--- |
| `backend/app/api/dependencies.py` | `148` | Configuration / Data / Schema | FastAPI dependency injection provider. Enforces JWT authentication, enterprise tenant isolation, and database session lifecycle. |
| `backend/app/api/README.md` | `42` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/api/routers/audit.py` | `97` | Configuration / Data / Schema | Merkle audit router. Exposes cryptographic verification endpoints for full chain scanning and CAG export compliance. |
| `backend/app/api/routers/auth.py` | `299` | Configuration / Data / Schema | Authentication router. Issues signed JWT bearer tokens with CPSE enterprise claims and user permission scopes. |
| `backend/app/api/routers/graph.py` | `283` | Configuration / Data / Schema | Knowledge graph router. Executes spatial queries, depot logistics lookups, and route optimization across CPSE nodes. |
| `backend/app/api/routers/ingest.py` | `253` | Configuration / Data / Schema | Document intake router. Dispatches incoming PDF/image MTCs to fast-path PyMuPDF or PaddleOCR computer vision pipelines. |
| `backend/app/api/routers/inventory.py` | `64` | Configuration / Data / Schema | Inventory items router. Implements catalog search and stock queries with dynamic serializer masking of sovereign commercial attributes (Invariant 3). |
| `backend/app/api/routers/match.py` | `256` | Configuration / Data / Schema | Semantic discovery and matching router. Executes 3-stage ranking (Qdrant HNSW + XGBoost + TreeSHAP) and 21 deterministic safety modules. |
| `backend/app/api/routers/README.md` | `70` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/api/routers/requisition.py` | `164` | Configuration / Data / Schema | Inter-CPSE loan and requisition manager. Handles multi-depot atomic reservations, lead approvals, and gate pass issuance. |
| `backend/app/api/routers/__init__.py` | `1` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/api/__init__.py` | `1` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/core/config.py` | `115` | Configuration / Data / Schema | Pydantic BaseSettings configuration. Loads and validates environment variables (DB URLs, JWT secrets, Qdrant/Neo4j credentials). |
| `backend/app/core/exceptions.py` | `99` | Configuration / Data / Schema | Custom exception hierarchy. Defines domain errors: ItemNotFoundError, InsufficientStockError, SafetyRuleViolationError, ChainTamperedError. |
| `backend/app/core/README.md` | `58` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/core/security.py` | `172` | Configuration / Data / Schema | Cryptographic utilities. Handles PassLib Bcrypt password hashing, JWT creation/decoding, and SHA-256 Merkle block generation. |
| `backend/app/core/__init__.py` | `22` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/models/base.py` | `39` | Configuration / Data / Schema | Declarative base model. Provides common timestamp columns (created_at, updated_at) and UUID primary key generator. |
| `backend/app/models/README.md` | `83` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/models/tables.py` | `271` | Configuration / Data / Schema | SQLAlchemy ORM definitions for `enterprises`, `depots`, `users`, `items`, `requisitions`, `audit_events`, and `cdc_outbox` tables. |
| `backend/app/models/__init__.py` | `34` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/README.md` | `35` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/schemas/audit.py` | `76` | Configuration / Data / Schema | Pydantic schemas for Merkle audit chain verification responses, block models, and CAG export structures. |
| `backend/app/schemas/auth.py` | `150` | Configuration / Data / Schema | Pydantic schemas for login requests, JWT token payloads, user registration, and enterprise profiles. |
| `backend/app/schemas/inventory.py` | `145` | Configuration / Data / Schema | Pydantic schemas for item catalog responses, inventory filtering, and stock update requests. |
| `backend/app/schemas/material.py` | `360` | Configuration / Data / Schema | Comprehensive material specification schemas for valves, piping, fittings, flanges, pumps, and motors. |
| `backend/app/schemas/README.md` | `58` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/schemas/requisition.py` | `100` | Configuration / Data / Schema | Pydantic schemas for requisition creation, multi-depot reservation allocations, and loan status updates. |
| `backend/app/schemas/__init__.py` | `70` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/services/audit_service.py` | `216` | Configuration / Data / Schema | Audit service layer. Manages append-only Merkle ledger event creation and O(N) chain integrity verification. |
| `backend/app/services/cdc_manager.py` | `277` | Configuration / Data / Schema | Change Data Capture (CDC) manager. Handles transactional outbox event publishing and PostgreSQL NOTIFY triggers. |
| `backend/app/services/inventory_service.py` | `229` | Configuration / Data / Schema | Inventory business logic. Executes stock queries, idle duration checks (> 180 days), and sovereign price masking. |
| `backend/app/services/README.md` | `74` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/services/requisition_service.py` | `301` | Configuration / Data / Schema | Requisition business logic. Implements atomic row locks (SELECT ... FOR UPDATE), 7-day auto-release timers, and approval workflows. |
| `backend/app/services/seeder.py` | `208` | Configuration / Data / Schema | Database seeding service. Populates demo CPSE inventories, users, and depot topologies. |
| `backend/app/services/__init__.py` | `1` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/app/__init__.py` | `1` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |
| `backend/main.py` | `88` | Configuration / Data / Schema | FastAPI gateway entrypoint. Configures CORS middleware, lifespan events, routes all sub-routers, and handles global HTTP exceptions. |
| `backend/README.md` | `93` | Configuration / Data / Schema | Backend service, schema definition, or API utility. |

### 22.2 Directory: `rules` (43 Files)

| File Path | Lines | Key Symbols / Classes / Functions | Architectural Role & Implementation Details |
| :--- | :--- | :--- | :--- |
| `rules/asme/facings.py` | `122` | Configuration / Data / Schema | Module 5: ASME B16.5 flange facings. Checks RF/RTJ/FF mating and enforces flat-face requirement on brittle cast iron flanges. |
| `rules/asme/fittings.py` | `138` | Configuration / Data / Schema | Core architectural component. |
| `rules/asme/flange_insulation.py` | `68` | Configuration / Data / Schema | Module 15: NACE SP0286 flange insulation kits. Prevents galvanic corrosion between dissimilar metals in cathodically protected lines. |
| `rules/asme/gaskets.py` | `133` | Configuration / Data / Schema | Module 7: ASME B16.20 gasket safety. Enforces metallic inner rings on high-pressure spiral wound gaskets and checks RTJ hardness deltas. |
| `rules/asme/large_flanges.py` | `66` | Configuration / Data / Schema | Module 6: ASME B16.47 large diameter flanges. Strictly blocks mismatch between Series A (MSS SP-44) and Series B (API 605). |
| `rules/asme/line_blinds.py` | `47` | Configuration / Data / Schema | Module 14: ASME B16.48 spectacle blinds & spacers. Verifies minimum blank thickness against ASME Section VIII bending equations. |
| `rules/asme/pressure_class.py` | `161` | Configuration / Data / Schema | Module 1: ASME B16.5 / B16.34 pressure class ladder. Prevents pressure rating downgrades; permits verified safe over-ratings. |
| `rules/asme/README.md` | `98` | Configuration / Data / Schema | Core architectural component. |
| `rules/asme/__init__.py` | `2` | Configuration / Data / Schema | Core architectural component. |
| `rules/astm/fasteners.py` | `133` | Configuration / Data / Schema | Module 8: ASTM A193/A194 fastener pairing. Validates B7/2H and L7/7 pairs; blocks cadmium/zinc coatings on high-temp stainless flanges. |
| `rules/astm/metallurgy_dag.py` | `305` | Configuration / Data / Schema | Module 2: ASTM metallurgy Directed Acyclic Graph. Prevents material downgrades and cryogenic brittle fracture (< -29°C). |
| `rules/astm/README.md` | `84` | Configuration / Data / Schema | Core architectural component. |
| `rules/astm/__init__.py` | `2` | Configuration / Data / Schema | Core architectural component. |
| `rules/equipment/heat_exchangers.py` | `103` | Configuration / Data / Schema | Module 21a: TEMA heat exchanger tube bundle compatibility and thermal expansion coefficient alignment. |
| `rules/equipment/README.md` | `64` | Configuration / Data / Schema | Core architectural component. |
| `rules/equipment/strainers_traps.py` | `83` | Configuration / Data / Schema | Core architectural component. |
| `rules/equipment/tank_safety.py` | `80` | Configuration / Data / Schema | Module 21b: API 2000 atmospheric storage tank breather venting and emergency inbreathing/outbreathing sizing. |
| `rules/equipment/thermal_insulation.py` | `65` | Configuration / Data / Schema | Module 21c: ASTM C795 stress corrosion inhibited thermal insulation for austenitic stainless piping (preventing CUI). |
| `rules/equipment/__init__.py` | `16` | Configuration / Data / Schema | Core architectural component. |
| `rules/piping/expansion_joints.py` | `58` | Configuration / Data / Schema | Core architectural component. |
| `rules/piping/line_pipe.py` | `95` | Configuration / Data / Schema | Core architectural component. |
| `rules/piping/nace.py` | `68` | Configuration / Data / Schema | Module 4: NACE MR0175 / ISO 15156 wet sour gas safety. Enforces 22 HRC (250 HV) maximum hardness ceiling. |
| `rules/piping/README.md` | `83` | Configuration / Data / Schema | Core architectural component. |
| `rules/piping/schedules.py` | `142` | Configuration / Data / Schema | Module 3: ASME B36.10M/B36.19M pipe schedules. Ensures buttweld wall thickness matching and prevents erosion turbulence. |
| `rules/piping/tubing.py` | `69` | Configuration / Data / Schema | Module 16: ASTM A269 small-bore tubing. Blocks hazardous cross-mating between imperial (1/2") and metric (12mm) ferrule fittings. |
| `rules/piping/__init__.py` | `2` | Configuration / Data / Schema | Core architectural component. |
| `rules/README.md` | `216` | Configuration / Data / Schema | Core architectural component. |
| `rules/rotating/bearings.py` | `70` | Configuration / Data / Schema | Core architectural component. |
| `rules/rotating/compressors.py` | `76` | Configuration / Data / Schema | Module 19: API 618/617 gas compressors. Validates gas molecular weight envelopes and reciprocating rod load reversals. |
| `rules/rotating/motors.py` | `149` | Configuration / Data / Schema | Module 20: IS/IEC 60079 hazardous area motors. Enforces Ex d flameproof rating in Zone 1 areas and C3 bearing internal clearances. |
| `rules/rotating/pumps.py` | `138` | Configuration / Data / Schema | Module 17: API 610 centrifugal process pumps. Mandates centerline mounting for pumping temperatures > 150°C. |
| `rules/rotating/README.md` | `80` | Configuration / Data / Schema | Core architectural component. |
| `rules/rotating/seals.py` | `106` | Configuration / Data / Schema | Module 18: API 682 mechanical seals. Enforces dual pressurized barrier seal plans (Plan 53A/B) on toxic hydrocarbon pumps. |
| `rules/rotating/__init__.py` | `2` | Configuration / Data / Schema | Core architectural component. |
| `rules/tolerance.py` | `489` | Configuration / Data / Schema | Master tolerance orchestrator. Dispatches candidate pairs across all 21 deterministic safety modules and computes dynamic compatibility score S(Q,C). |
| `rules/valves/bore.py` | `49` | Configuration / Data / Schema | Module 9: API 6D piggable pipeline flow. Restricts pipeline valves to Full Bore (FB) to prevent PIG tool jams. |
| `rules/valves/fire_safe.py` | `144` | Configuration / Data / Schema | Module 10: API 607 / API 6FA fire safety. Mandates certified fire-safe soft seated valves in flammable hydrocarbon circuits. |
| `rules/valves/psv.py` | `73` | Configuration / Data / Schema | Module 12: API 520/526 PSV orifice sizing. Ensures relief orifice letter (D-T) meets or exceeds required relief capacity. |
| `rules/valves/README.md` | `75` | Configuration / Data / Schema | Core architectural component. |
| `rules/valves/rupture_disks.py` | `59` | Configuration / Data / Schema | Module 13: ISO 4126-2 rupture disks. Enforces reverse buckling non-fragmenting disks upstream of PSV nozzles. |
| `rules/valves/trim.py` | `67` | Configuration / Data / Schema | Module 11: API 600/602 valve trim ladder. Prevents trim downgrades (e.g. Trim 1 vs Trim 8) in erosive and steam service. |
| `rules/valves/__init__.py` | `2` | Configuration / Data / Schema | Core architectural component. |
| `rules/__init__.py` | `8` | Configuration / Data / Schema | Core architectural component. |

### 22.3 Directory: `ml` (24 Files)

| File Path | Lines | Key Symbols / Classes / Functions | Architectural Role & Implementation Details |
| :--- | :--- | :--- | :--- |
| `ml/active_learning/bootstrapper.py` | `29` | Configuration / Data / Schema | Core architectural component. |
| `ml/active_learning/cache.py` | `45` | Configuration / Data / Schema | Active learning Trie cache. Provides O(k) lookup for previously verified expert engineer substitution decisions. |
| `ml/active_learning/README.md` | `60` | Configuration / Data / Schema | Core architectural component. |
| `ml/active_learning/__init__.py` | `5` | Configuration / Data / Schema | Core architectural component. |
| `ml/embeddings/qdrant_client.py` | `102` | Configuration / Data / Schema | Qdrant vector database client. Manages collection schema, HNSW parameters, and payload-filtered cosine similarity search. |
| `ml/embeddings/README.md` | `60` | Configuration / Data / Schema | Core architectural component. |
| `ml/embeddings/vector_encoder.py` | `37` | Configuration / Data / Schema | BAAI/bge-m3 dense vectorizer. Generates 1024-dimensional semantic embeddings for catalog items and search queries. |
| `ml/embeddings/__init__.py` | `5` | Configuration / Data / Schema | Core architectural component. |
| `ml/ner/normalizer.py` | `284` | Configuration / Data / Schema | Dialect normalizer. Maps 40+ CPSE catalog abbreviations to standard canonical engineering nomenclature. |
| `ml/ner/README.md` | `80` | Configuration / Data / Schema | Core architectural component. |
| `ml/ner/slot_tagger.py` | `80` | Configuration / Data / Schema | Regex slot extractor. Extracts NB size, pressure class, metallurgy, and flange facings from raw descriptions. |
| `ml/ner/__init__.py` | `5` | Configuration / Data / Schema | Core architectural component. |
| `ml/ranking/explainer.py` | `32` | Configuration / Data / Schema | TreeSHAP explainability module. Generates feature attribution values explaining positive/negative compatibility score weights. |
| `ml/ranking/feature_extract.py` | `100` | Configuration / Data / Schema | Core architectural component. |
| `ml/ranking/ranker.py` | `29` | Configuration / Data / Schema | XGBoost ranking engine. Trains and executes pairwise ranking models over 8-dimensional physical subvector representations. |
| `ml/ranking/README.md` | `76` | Configuration / Data / Schema | Core architectural component. |
| `ml/ranking/__init__.py` | `6` | Configuration / Data / Schema | Core architectural component. |
| `ml/README.md` | `132` | Configuration / Data / Schema | Core architectural component. |
| `ml/vision/chemistry.py` | `212` | Configuration / Data / Schema | Metallurgy chemistry engine. Computes IIW Carbon Equivalent and PREN corrosion index; checks ASTM ladle composition limits. |
| `ml/vision/mtc_parser.py` | `377` | Configuration / Data / Schema | MTC document parser. Extracts heat numbers, yield/tensile strength, elongation, and chemical elements via structured regex. |
| `ml/vision/ocr_engine.py` | `325` | Configuration / Data / Schema | Computer vision OCR engine. Dispatches PyMuPDF vector streams and PaddleOCR with CLAHE and Otsu binarization. |
| `ml/vision/README.md` | `82` | Configuration / Data / Schema | Core architectural component. |
| `ml/vision/__init__.py` | `6` | Configuration / Data / Schema | Core architectural component. |
| `ml/__init__.py` | `2` | Configuration / Data / Schema | Core architectural component. |

### 22.4 Directory: `graph` (7 Files)

| File Path | Lines | Key Symbols / Classes / Functions | Architectural Role & Implementation Details |
| :--- | :--- | :--- | :--- |
| `graph/logistics.py` | `113` | Configuration / Data / Schema | National logistics engine. Computes Haversine great-circle distances, 1.28x highway tortuosity, transit hours, and BEE CO2 savings. |
| `graph/queries.py` | `107` | Configuration / Data / Schema | Pre-compiled Cypher queries for multi-hop inventory traversal and spatial nearest-depot routing. |
| `graph/README.md` | `134` | Configuration / Data / Schema | Core architectural component. |
| `graph/schema.py` | `53` | Configuration / Data / Schema | Neo4j knowledge graph schema initializer. Sets up spatial constraints, indices, and node labels. |
| `graph/seed_graph.py` | `164` | Configuration / Data / Schema | Core architectural component. |
| `graph/syncer.py` | `338` | Configuration / Data / Schema | CDC Outbox synchronization worker. Consumes PostgreSQL LISTEN events and updates Neo4j graph nodes and edges. |
| `graph/__init__.py` | `16` | Configuration / Data / Schema | Core architectural component. |

### 22.5 Directory: `frontend` (38 Files)

| File Path | Lines | Key Symbols / Classes / Functions | Architectural Role & Implementation Details |
| :--- | :--- | :--- | :--- |
| `frontend/next-env.d.ts` | `8` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/next.config.ts` | `9` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/package-lock.json` | `6965` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/package.json` | `31` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/postcss.config.mjs` | `6` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/public/.gitkeep` | `2` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/README.md` | `107` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/app/admin/users/page.tsx` | `125` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/app/audit/page.tsx` | `444` | Configuration / Data / Schema | Sovereign Merkle audit ledger UI. Provides 1-click CAG chain integrity verification and cryptographic certificate export. |
| `frontend/src/app/dashboard/page.tsx` | `619` | Configuration / Data / Schema | Executive command dashboard. Visualizes national surplus capital, CPSE inventory distribution, and GIS depot map. |
| `frontend/src/app/discover/page.tsx` | `522` | Configuration / Data / Schema | Pre-purchase semantic discovery radar. Real-time candidate matching with 21-rule scorecards and transit routes. |
| `frontend/src/app/globals.css` | `92` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/app/inventory/page.tsx` | `675` | Configuration / Data / Schema | Plant inventory management page. Highlights dormant stock (> 180 days) with 1-click mutual-aid broadcasting. |
| `frontend/src/app/layout.tsx` | `44` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/app/login/page.tsx` | `233` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/app/page.tsx` | `341` | Configuration / Data / Schema | Root landing page. Renders national sovereign mutual aid mesh portal with quick search and login entrypoints. |
| `frontend/src/app/requests/page.tsx` | `383` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/app/requests/[id]/page.tsx` | `384` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/app/signup/page.tsx` | `367` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/app/upload/page.tsx` | `253` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/app/upload/review/page.tsx` | `294` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/components/AppShell.tsx` | `118` | `AppShell` | Compact 48px utility header with breadcrumbs, CPSE tenant switcher dropdown, and global Cmd+K command palette trigger. |
| `frontend/src/components/CommandPalette.tsx` | `238` | `CommandPalette` | Global Cmd+K / Ctrl+K action hub for instant parts fuzzy search, CPSE tenant switching, and CAG audit CSV export. |
| `frontend/src/components/ProtectedRoute.tsx` | `139` | `ProtectedRoute` | Route guard restricting access to authenticated users matching specific CPSE operational roles. |
| `frontend/src/components/PublicNavbar.tsx` | `82` | `PublicNavbar` | Minimalist 48px public navigation bar for landing and authentication pages. |
| `frontend/src/components/QRCodeSVG.tsx` | `142` | `QRCodeSVG` | Pure SVG 25x25 bit-matrix QR code renderer for air-gapped CISF Gate Pass clearance. |
| `frontend/src/components/Sidebar.tsx` | `216` | `Sidebar` | Linear-style collapsible navigation rail (240px to 56px) with keyboard shortcut ([), active indicator, and theme switcher. |
| `frontend/src/components/ThemeProvider.tsx` | `57` | `ThemeProvider` | Dark/light theme and active CPSE context provider using React context and localStorage. |
| `frontend/src/components/ThemeToggle.tsx` | `33` | `ThemeToggle` | Minimalist Sun/Moon theme toggle button supporting full and icon-only collapsed rail layouts. |
| `frontend/src/components/ui/index.tsx` | `287` | `Card`, `KpiCard`, `SideDrawer`, `Skeleton`, `StatusBadge`, `Modal` | Minimalist UI component library with 480px sliding side inspector drawer, hairline shimmer skeletons, and status dot badges. |
| `frontend/src/components/UserHeaderBadge.tsx` | `48` | `UserHeaderBadge` | Minimalist user session pill displaying authenticated username, CPSE badge, and quick sign-out. |
| `frontend/src/context/AuthContext.tsx` | `157` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/lib/api.ts` | `165` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/lib/constants.ts` | `36` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/lib/exportUtils.ts` | `41` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/lib/formatters.ts` | `28` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/src/lib/types.ts` | `82` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |
| `frontend/tsconfig.json` | `43` | Configuration / Data / Schema | Next.js 16 UI component, context provider, or layout module. |

### 22.6 Directory: `datasets` (6 Files)

| File Path | Lines | Key Symbols / Classes / Functions | Architectural Role & Implementation Details |
| :--- | :--- | :--- | :--- |
| `datasets/generators/generate_datasets.py` | `1042` | Configuration / Data / Schema | Core architectural component. |
| `datasets/generators/README.md` | `34` | Configuration / Data / Schema | Core architectural component. |
| `datasets/golden_benchmarks.json` | `3976` | Configuration / Data / Schema | Master golden benchmark dataset. Contains 150 verified ground-truth test pairs across Tier 1, Tier 2, and Tier 3 scenarios. |
| `datasets/inventory_catalog.csv` | `5002` | Configuration / Data / Schema | Core architectural component. |
| `datasets/ocr_payloads.json` | `19552` | Configuration / Data / Schema | Core architectural component. |
| `datasets/README.md` | `90` | Configuration / Data / Schema | Core architectural component. |

### 22.7 Directory: `docker` (10 Files)

| File Path | Lines | Key Symbols / Classes / Functions | Architectural Role & Implementation Details |
| :--- | :--- | :--- | :--- |
| `docker/.dockerignore` | `31` | Configuration / Data / Schema | Core architectural component. |
| `docker/.env.docker` | `31` | Configuration / Data / Schema | Core architectural component. |
| `docker/docker-compose.yml` | `295` | Configuration / Data / Schema | Master Docker Compose orchestration for PostgreSQL 16, Qdrant, Neo4j, FastAPI backend, and Next.js frontend. |
| `docker/Dockerfile.backend` | `106` | Configuration / Data / Schema | Core architectural component. |
| `docker/Dockerfile.frontend` | `77` | Configuration / Data / Schema | Core architectural component. |
| `docker/Dockerfile.ml` | `62` | Configuration / Data / Schema | Core architectural component. |
| `docker/init-db/01-init-samanvay.sql` | `14` | Configuration / Data / Schema | Core architectural component. |
| `docker/init-db/README.md` | `32` | Configuration / Data / Schema | Core architectural component. |
| `docker/README.md` | `112` | Configuration / Data / Schema | Core architectural component. |
| `docker/__init__.py` | `3` | Configuration / Data / Schema | Core architectural component. |

### 22.8 Directory: `scripts` (6 Files)

| File Path | Lines | Key Symbols / Classes / Functions | Architectural Role & Implementation Details |
| :--- | :--- | :--- | :--- |
| `scripts/cdc_worker.py` | `29` | Configuration / Data / Schema | Core architectural component. |
| `scripts/generate_datasets.py` | `1042` | Configuration / Data / Schema | Core architectural component. |
| `scripts/README.md` | `52` | Configuration / Data / Schema | Core architectural component. |
| `scripts/seed_database.py` | `260` | Configuration / Data / Schema | Database seeder. Generates 5000+ realistic CPSE inventory records with Make-in-India metadata across 19 national depots. |
| `scripts/test_live_cdc.py` | `135` | Configuration / Data / Schema | Core architectural component. |
| `scripts/verify_live_api.py` | `119` | Configuration / Data / Schema | Core architectural component. |

### 22.9 Directory: `tests` (27 Files)

| File Path | Lines | Key Symbols / Classes / Functions | Architectural Role & Implementation Details |
| :--- | :--- | :--- | :--- |
| `tests/api/README.md` | `41` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/api/test_audit_api.py` | `75` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/api/test_auth_api.py` | `166` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/api/test_graph_api.py` | `61` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/api/test_inventory_api.py` | `44` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/api/test_match_api.py` | `61` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/api/test_requisition_api.py` | `37` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/api/test_signup_api.py` | `114` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/api/__init__.py` | `1` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/conftest.py` | `18` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/integration/README.md` | `25` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/integration/test_benchmarks.py` | `44` | Configuration / Data / Schema | Automated evaluation suite running all 150 Golden Benchmark test scenarios through the end-to-end ranking and safety pipeline. |
| `tests/integration/__init__.py` | `1` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/ml/README.md` | `22` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/ml/test_ner.py` | `18` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/ml/__init__.py` | `1` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/README.md` | `60` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/unit/README.md` | `67` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/unit/test_chemistry.py` | `25` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/unit/test_indian_procurement_alignment.py` | `112` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/unit/test_logistics.py` | `37` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/unit/test_normalizer.py` | `25` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/unit/test_ocr_and_mtc.py` | `195` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/unit/test_security.py` | `108` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/unit/test_tolerance.py` | `279` | Configuration / Data / Schema | Comprehensive unit test suite verifying all 21 deterministic safety rules against boundary edge cases. |
| `tests/unit/__init__.py` | `1` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |
| `tests/__init__.py` | `1` | Configuration / Data / Schema | Automated pytest test suite validating specific system behaviors, security invariants, or API contracts. |

### 22.10 Directory: `Root Level Files` (10 Files)

| File Path | Lines | Key Symbols / Classes / Functions | Architectural Role & Implementation Details |
| :--- | :--- | :--- | :--- |
| `.env.example` | `22` | Configuration / Data / Schema | Core architectural component. |
| `.gitignore` | `43` | Configuration / Data / Schema | Core architectural component. |
| `.python-version` | `2` | Configuration / Data / Schema | Core architectural component. |
| `architecture.md` | `594` | Configuration / Data / Schema | Core architectural component. |
| `context.md` | `1642` | Configuration / Data / Schema | Core architectural component. |
| `pyproject.toml` | `53` | Configuration / Data / Schema | Core architectural component. |
| `README.md` | `271` | Configuration / Data / Schema | Core architectural component. |
| `SIH_Presentation.pptx` | `2496` | Configuration / Data / Schema | Core architectural component. |
| `SIH_Presentation_backup.pptx` | `3227` | Configuration / Data / Schema | Core architectural component. |
| `uv.lock` | `3419` | Configuration / Data / Schema | Core architectural component. |
