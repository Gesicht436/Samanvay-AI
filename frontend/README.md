# Samanvay-AI Frontend Portal (`frontend`)

## 1. Overview
The `frontend` directory contains the modernized sovereign web portal for Samanvay-AI, built with **Next.js 15**, **React 19**, **TypeScript**, and **Tailwind CSS**.

### Design Philosophy
- **Sleek & Minimalistic Aesthetic**: Clean, modern design inspired by modern developer platforms (GitHub, Linear, Vercel) with generous whitespace, subtle borders, and clear visual hierarchy.
- **Light & Dark Theme Toggle**: Full CSS variable-driven light mode (primary) with dark mode accessibility toggle, respecting system preferences and persisting choices in `localStorage`.
- **Strict Separation of Concerns**: Distinct, modular pages for each operational stage. No monolithic files.
- **Zero Emojis**: Strictly enforced professional enterprise styling suitable for Ministry of Petroleum & Natural Gas (MoPNG) officers and site engineers.

---

## 2. Directory Structure

```
frontend/src/
|-- app/
|   |-- layout.tsx              # Root layout with Sidebar and ThemeProvider
|   |-- page.tsx                # Root redirect to /upload
|   |-- globals.css             # CSS custom properties for light/dark themes
|   |-- upload/
|   |   |-- page.tsx            # Procurement bill & MTC intake with WinRT OCR
|   |   `-- review/
|   |       `-- page.tsx        # Dedicated Site Engineer Inward Review page
|   |-- inventory/
|   |   `-- page.tsx            # Plant inventory tracking & surplus lifecycle radar
|   |-- discover/
|   |   `-- page.tsx            # Cross-CPSE spare search & indent composition
|   |-- requests/
|   |   |-- page.tsx            # Requisitions inbox (Inbound/Outbound/Confirm/Decline)
|   |   `-- [id]/
|   |       `-- page.tsx        # Single request detail with live tracking timeline
|   `-- audit/
|       `-- page.tsx            # Sovereign compliance audit ledger (SHA-256 sealed)
|-- components/
|   |-- Sidebar.tsx             # Left sidebar navigation with plant facility switcher
|   |-- ThemeProvider.tsx       # Theme context & CPSE facility state
|   |-- ThemeToggle.tsx         # Sun/Moon mode switcher button
|   `-- ui/
|       |-- Card.tsx            # Minimalist Card wrapper & CardHeader
|       |-- Modal.tsx           # Accessible modal dialog
|       |-- StatusBadge.tsx     # Standardized status badge with dot indicators
|       |-- KpiCard.tsx         # Metric summary counter cards
|       |-- Timeline.tsx        # Vertical live movement timeline
|       `-- EmptyState.tsx      # Clean empty state illustrations
`-- lib/
    |-- api.ts                  # Centralized REST client with offline fallback fixtures
    |-- types.ts                # TypeScript domain models and interfaces
    |-- constants.ts            # CPSE depot registry, lifecycle maps, urgency levels
    |-- formatters.ts           # INR currency, date, and time utilities
    `-- theme.ts                # Theme preference storage and DOM class manipulator
```

---

## 3. Pages & End-to-End Operational Workflow

```
[1. Upload Bill/MTC] ──> [2. Engineer Inward Review] ──> [3. Plant Inventory]
                                                               │
                                                               ▼ (If idle >90d)
                                                        [Broadcast Surplus]
                                                               │
[5. Live Tracking Timeline] ◄── [4. Facility Confirms] ◄── [Discover & Request]
```

### 1. Document Upload & OCR Intake (`/upload`)
- Multi-format file intake supporting scanned invoices, digital bills, and EN 10204 3.1 Mill Test Certificates in PDF, PNG, JPG, or TIFF.
- Live WinRT OCR processing extracting Heat numbers, PO numbers, ASTM metallurgy, ASME standards, and line items in sub-250ms.
- Test presets featuring real refinery certificates for immediate one-click testing.
- Direct navigation to Site Engineer Review.

### 2. Site Engineer Inward Review (`/upload/review`)
- Detailed inspection workbench where site engineers verify extracted attributes before committing assets to the central database.
- Editable technical specifications: SKU code, size (NB mm), pressure class, metallurgy, facing, and governing standard.
- **Initial Lifecycle Tag Selection**:
  - `TO_BE_CONSUMED`: Reserved for upcoming turnaround maintenance. Private to plant; hidden from sister CPSE surplus discovery.
  - `IN_STORAGE`: Standard warehouse reserve buffer stock.
- Single-click commit to central PostgreSQL database and Neo4j knowledge graph.

### 3. Plant Inventory & Surplus Radar (`/inventory`)
- Central repository of all inward physical assets with real-time lifecycle tracking.
- KPI metric counters: Total Tracked, To Be Consumed, In Storage, Idle Surplus, Consumed.
- Dynamic filtering by holding CPSE, lifecycle status, or text search.
- **Lifecycle Transition Actions**:
  - `Mark Idle Surplus`: Prompts for justification note and immediately broadcasts the asset to all sister CPSEs in Neo4j.
  - `Mark Consumed`: Records installation in processing unit and archives the record.

### 4. Cross-CPSE Spare Material Discovery (`/discover`)
- Unified search engine across all certified spare items held by ONGC, IOCL, BPCL, HPCL, and GAIL.
- Filter by holding CPSE, equipment category, or metallurgy.
- **Send Procurement Request Modal**: Pre-fills target facility information, validates requested quantity against available stock, captures urgency level (`EMERGENCY_SHUTDOWN`, `PLANNED_MAINTENANCE`, `ROUTINE`), and transmits the indent.

### 5. Procurement Requests & Tracking Inbox (`/requests`)
- Unified requests dashboard with tabbed segmentation:
  - **All Requests**: Global view of all transfer activity.
  - **Received Requests (Inbound)**: Filtered to requests targeting the active facility. Enables 1-click **Confirm Supply** or **Decline Request**.
  - **Sent Requests (Outbound)**: Outward indents issued to other refineries.
- Quick status filters and search bar.

### 6. Request Detail & Live Tracking Timeline (`/requests/[id]`)
- Comprehensive bilateral view accessible to both sender and receiver facilities.
- Corridor tracking cards displaying requesting unit, supplying depot, allocated valuation, and transporter fleet details.
- **Interactive Live Movement Timeline**:
  - Step 1: Procurement Request Issued (with engineer notes)
  - Step 2: Supply Capability Confirmed / Declined (with facility sign-off)
  - Step 3: CISF Material Gate Pass Issued (with SHA-256 seal)
  - Step 4: Outward Perimeter Gate Dispatch (vehicle and driver details)
  - Step 5: Consignment Delivery & Handover at Site Depot
- Printable official CISF Electronic Material Gate Pass with cryptographic QR code and verification URL.

### 7. Sovereign Audit Ledger (`/audit`)
- CVC and CAG compliant immutable audit trail.
- Every bill commit, lifecycle transition, and transfer indent is cryptographically sealed with a SHA-256 hash.
- Export to RFC 4180 Excel CSV with UTF-8 BOM encoding.

---

## 4. Development & Build Verification

```powershell
# Run development server
cd frontend
npm run dev

# Verify static build and TypeScript compilation
npm run build
```
