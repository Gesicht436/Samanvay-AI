# Samanvay-AI Frontend Portal (`frontend/`)

### Sovereign Inter-CPSE Material Coordination & Mutual Aid Web Interface
**Ministry of Petroleum & Natural Gas (MoPNG) | Smart India Hackathon (SIH26099)**

Built with **Next.js 16 (App Router)**, **React 19**, and **Tailwind CSS v4**, this frontend portal provides a high-density, utility-focused operational web console for materials managers, maintenance engineers, and CISF security officers across Indian petroleum CPSEs.

---

## 1. Core Architectural Tenets

1. **Zero Mock Data (100% Dynamic Backend Integration):**
   - No hardcoded catalog items, dummy consignments, or fake audit events.
   - All state is fetched live from the FastAPI gateway (`http://localhost:8000`) backed by PostgreSQL 16, Qdrant, and the Sovereign Audit Ledger.
2. **Default Primary Theme: Light Mode:**
   - Standardized enterprise light mode by default with clean, high-contrast surfaces (`bg-slate-50`, `border-slate-200`, `text-slate-900`).
   - Seamless dark mode toggling available via the **Bottom-Left Switcher** in the sidebar.
3. **No Unnecessary Decorative Flair:**
   - High-density data tables, server-driven pagination, and responsive modals.
   - Elimination of non-functional animations, fake pulsating SVG graphics, and decorative badges.
4. **Attribute-Level Commercial Privacy:**
   - Unit purchase costs and proprietary ERP PO numbers are strictly masked across enterprise boundaries, allowing fair mutual-aid borrowing without revealing sensitive commercial terms.

---

## 2. Directory Structure

```
frontend/
├── package.json              # Next.js 16, React 19, Tailwind CSS v4, Lucide icons
├── tsconfig.json             # TypeScript configuration
├── next.config.ts            # Next.js runtime configuration
└── src/
    ├── app/                  # Next.js App Router routes
    │   ├── globals.css       # Tailwind CSS v4 themes and compact table utility classes
    │   ├── layout.tsx        # Master root layout with functional header and sidebar
    │   ├── page.tsx          # Command Center: live KPIs, requisitions, CPSE footprint, audit stream
    │   ├── inventory/        # Stock Ledger: 5,000 items, server pagination, filters, HITL review
    │   ├── discover/         # Surplus Discovery: ML + 21-rule tolerance radar, transfer creator
    │   ├── requests/         # Requisitions list & transfer order lifecycle
    │   │   └── [id]/         # Consignment detail: milestone stepper, CISF gate pass & QR code
    │   ├── audit/            # Sovereign Audit Trail: SHA-256 chain verification & CSV export
    │   └── upload/           # Document Intake: PyMuPDF / PaddleOCR extraction & recent intake list
    │       └── review/       # MTC Inspection: chemical analysis, IIW CE, ASTM conformance
    ├── components/           # Reusable UI components
    │   ├── Sidebar.tsx       # Navigation bar with active CPSE node selector & bottom-left theme toggle
    │   ├── ThemeProvider.tsx # Light/Dark theme context (defaults to light mode)
    │   ├── ThemeToggle.tsx   # Icon + label button for theme switching
    │   ├── QRCodeSVG.tsx     # Offline air-gapped SVG QR code generator for CISF gate passes
    │   └── ui/               # Card, KpiCard, StatusBadge, Modal primitives
    └── lib/                  # Utilities and API client
        ├── api.ts            # Typed REST API client communicating with FastAPI (/api/v1)
        ├── constants.ts      # CPSE depot metadata, status color mappings, tier labels
        ├── exportUtils.ts    # RFC 4180 compliant CSV export utility
        ├── formatters.ts     # Currency (INR Lakh/Crore) and unit formatting
        └── types.ts          # Core TypeScript interface definitions
```

---

## 3. Operational Route Specifications

| Route | View Name | Live API Integration | Functionality |
|---|---|---|---|
| `/` | **Command Center** | `GET /inventory/stats`<br>`GET /requisition/`<br>`GET /audit/?limit=5`<br>`GET /audit/verify` | Real-time aggregate KPIs (cataloged SKUs, surplus capital, HITL queue count), active requisitions table, cross-CPSE inventory footprint progress bars, and latest SHA-256 audit blocks. |
| `/inventory` | **Stock Ledger** | `GET /inventory?skip=..&limit=25`<br>`GET /inventory/hitl-queue`<br>`PUT /inventory/{sku}/status` | Server-paginated table across 5,000 catalog items. Filters by CPSE, category, status, and dialect text search. Includes technical specification modal (BIS IS standards, OIL MESC codes, GeM IDs, MII %) and status transition actions (`Broadcast`, `Retract`). |
| `/discover` | **Surplus Discovery** | `GET /graph/discover`<br>`POST /match/search`<br>`POST /requisition/` | Pre-Purchase Radar querying sister CPSE surplus with 21-rule engineering tolerance, continuous ML score, road transit distance, and inline requisition submission modal. |
| `/requests` | **Consignments Hub** | `GET /requisition/`<br>`PUT /requisition/{id}/approve`<br>`POST /requisition/{id}/gatepass`<br>`PUT /requisition/{id}/dispatch`<br>`PUT /requisition/{id}/deliver` | End-to-end mutual-aid transfer order management with live workflow actions (Approve $\rightarrow$ Issue Gate Pass $\rightarrow$ Dispatch $\rightarrow$ Confirm Receipt). |
| `/requests/[id]` | **Requisition Detail** | `GET /requisition/{id}` | Detailed requisition parameters, 5-stage lifecycle milestone stepper, CISF non-returnable gate pass, and offline air-gapped QR code. |
| `/audit` | **Audit Trail** | `GET /audit/`<br>`GET /audit/verify`<br>`GET /audit/export` | Sovereign SHA-256 Merkle chain verification, CSV export for audit authorities, category/CPSE filters, and block transaction payload inspector. |
| `/upload` | **Document Intake** | `POST /ingest/document`<br>`GET /ingest/documents` | Upload PDF or image Material Test Certificates (MTCs), delivery challans, and invoices for dual-path OCR parsing. Displays recent intake ledger. |
| `/upload/review` | **MTC Inspection** | `sessionStorage`<br>`POST /inventory/` | Visual chemical analysis breakdown ($\%C, \%Mn, \%Si, \%P, \%S$), IIW Carbon Equivalent ($CE_{\text{IIW}}$) calculation, weldability classification, and direct commit to ledger. |

---

## 4. Environment Configuration

Create or update `.env.local` inside `frontend/`:

```env
# Backend API Base URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 5. Development & Production Commands

All commands should be executed from within the `frontend/` directory:

```bash
# Install dependencies
npm install

# Start development server with Turbopack (runs on http://localhost:3000)
npm run dev

# Compile production build with strict TypeScript type-checking
npm run build

# Start production server
npm run start

# Run ESLint validation
npm run lint
```
