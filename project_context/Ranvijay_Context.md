# Central Web Portal & Document Database Storage Workflow

**Role:** Frontend Developer & Document Database Lead (Ranvijay)

**Collaborators:**
* **Samriddih** (Document Intelligence Lead — provides OCR extracted text & MTC layouts)
* **Mayank** (Team Lead & System Architect — handles all database connections, API routes, and frontend-to-backend wiring)
* **Harsh** (Provides Neo4j cross-CPSE spare locator data)

**Primary Directories:** `frontend/` and `backend/app/ingestion/`

**Target Environment:** Node.js 26, Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, PostgreSQL, SQLAlchemy

---

### Objective & Architectural Role

Your mission encompasses two vital aspects of **Samanvay-AI (BharatCodex)**:
1. **The User-Facing Enterprise Web Application:** The presentation and interaction layer that hackathon judges, Ministry (MoPNG) officials, and plant engineers will evaluate.
2. **Document Ingestion Database Storage:** Collaborating with Samriddih to persist raw OCR-extracted text, certificates, and parsed document metadata into PostgreSQL staging tables.

Mayank manages all the database engine configurations, connection pooling, and API gateway routing, while you focus on the UI implementation and document storage schema.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        NEXT.JS 16 WEB PORTAL                           │
│                                                                        │
│  ┌───────────────────────┐ ┌───────────────────┐ ┌──────────────────┐  │
│  │   DEDUPLICATION &     │ │   HITL TRIAGE     │ │   PROCUREMENT    │  │
│  │   INGESTION STUDIO    │ │   QUEUE PANEL     │ │   ANALYTICS      │  │
│  │ (CSV/Excel/MTC Drag)  │ │ (Accept / Reject) │ │ (Capital Freed)  │  │
│  └──────────┬────────────┘ └─────────┬─────────┘ └─────────┬────────┘  │
│             │                        │                     │           │
│             └────────────────────────┼─────────────────────┘           │
│                                      ▼                                 │
│                           API CLIENT / DATA HOOKS                      │
│                           (TanStack React Query)                       │
│                                      │                                 │
└──────────────────────────────────────┼─────────────────────────────────┘
                                       │
                               REST / JSON Calls
                                       ▼
                       Mayank's Unified FastAPI Gateway
                                       │
                      ┌────────────────┴────────────────┐
                      ▼                                 ▼
             [Mayank & Harsh]                  [Ranvijay & Samriddih]
            (Neo4j / ASME Rules)              (PostgreSQL Document DB)
```

---

### Task 1: Document Text Database Persistence (with Samriddih & Mayank)

When Samriddih's PaddleOCR / PyMuPDF engine extracts text from scanned MTCs, delivery challans, or plant invoices, that data must be safely stored in PostgreSQL for auditability and downstream processing.

* **File:** `backend/app/ingestion/storage.py` (or `backend/app/contracts/document_db.py`)
* **SQLAlchemy Schema to Implement:**
  ```python
  from sqlalchemy import Column, String, Text, DateTime, JSON, Integer
  from sqlalchemy.sql import func
  from backend.app.contracts.base import Base # Mayank provides Base

  class IngestedDocument(Base):
      __tablename__ = "ingested_documents"

      id = Column(Integer, primary_key=True, autoincrement=True)
      filename = Column(String(255), nullable=False)
      doc_type = Column(String(100), default="MTC_CERTIFICATE")
      raw_text = Column(Text, nullable=False)
      parsed_metadata = Column(JSON, nullable=True) # Heat No, Grade, Size, Specs
      created_at = Column(DateTime(timezone=True), server_default=func.now())
  ```
* **Storage Function:**
  ```python
  def save_extracted_document(db_session, filename: str, raw_text: str, metadata: dict) -> IngestedDocument:
      doc = IngestedDocument(filename=filename, raw_text=raw_text, parsed_metadata=metadata)
      db_session.add(doc)
      db_session.commit()
      db_session.refresh(doc)
      return doc
  ```
* *Note: Mayank handles the database engine and provides the `db_session` dependency in FastAPI.*

---

### Task 2: Core Frontend Workflows (Next.js 16)

**1. Catalog Deduplication Studio (`src/app/deduplication/page.tsx`)**
* **Drag-and-Drop Ingestion:** Accepts messy inventory CSV/XLSX dumps or MTC certificate PDFs.
* **Batch Processing Progress Bar:** Real-time feedback while the backend processes items through OCR, NER, and ASME rules.
* **Summary KPI Cards:** Total Items Uploaded, Tier-1 Exact Matches, Tier-2 Safe Substitutes, and Borderline Items in HITL Queue.

**2. Human-in-the-Loop (HITL) Triage Panel (`src/app/hitl/page.tsx`)**
* **The Demo Showstopper:** When AI confidence is between 70% and 90%, procurement managers review matches side-by-side:
  * **Left Side (Source CPSE Part):** e.g., `IOCL: FLG WNRF 4IN 300# A105` (Panipat Depot, Unit Cost ₹12,400).
  * **Right Side (Suggested Match):** e.g., `ONGC: FLANGE WELD NECK 4" CL300 ASTM A105` (Hazira Depot, 45 units available).
  * **Parameter Badges:** High-contrast green pill badges: `[NB: 100mm ✓]` `[Class: 300 ✓]` `[Steel: ASTM A105 ✓]`.
  * **Action Buttons:** `[Approve & Link]` (calls `/match/hitl-resolve`), `[Reclassify]`, `[Reject]`.

**3. Procurement Analytics Dashboard (`src/app/dashboard/page.tsx`)**
* **Working Capital Unlocked:** Calculated savings from identifying idle surplus instead of placing fresh tenders (₹1,500+ Cr).
* **Cross-CPSE Spare Locator Table:** Shows exact quantities and days idle at sister depots.
* **Taxonomy Distribution Chart:** Breakdown of items categorized under UNSPSC segments.

---

### File Deliverables & Directory Layout

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx                # App shell, persistent sidebar & navigation
│   │   ├── page.tsx                  # Redirects to /dashboard
│   │   ├── dashboard/page.tsx        # Procurement analytics overview
│   │   ├── deduplication/page.tsx    # Batch file upload and deduplication studio
│   │   └── hitl/page.tsx             # Human-in-the-loop review queue
│   ├── components/
│   │   ├── ui/                       # shadcn/ui components (Button, Card, Table, Badge)
│   │   └── ItemComparisonCard.tsx    # Side-by-side reconciliation comparison widget
│   └── lib/
│       ├── api.ts                    # API client calling Mayank's FastAPI routes
│       ├── types.ts                  # TypeScript interfaces matching backend Pydantic models
│       └── mockData.ts               # Fallback mock data for offline UI development

backend/app/ingestion/
└── storage.py                        # Document database persistence in PostgreSQL
```

---

### Team Collaboration & Handoffs
1. **With Samriddih:** Samriddih produces the clean OCR text and certificate dicts; your `storage.py` saves them to PostgreSQL.
2. **With Mayank:** Mayank sets up the PostgreSQL database connection and wires up the backend REST endpoints; your `api.ts` connects the frontend to Mayank's API.
3. **With Harsh:** Harsh's Neo4j queries provide the cross-CPSE spare locator data that populates your Analytics Dashboard.
