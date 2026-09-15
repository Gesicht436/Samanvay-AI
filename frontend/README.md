# Samanvay-AI Frontend Portal (`frontend`)

## 1. Overview
The `frontend` directory contains the web portal for Samanvay-AI, built with **Next.js 16**, **React 19**, **TypeScript**, and **Tailwind CSS**.

### Design Philosophy
The user interface is inspired by **Amazon Business** and the **AWS Management Console**:
- Clean Light Mode: High-contrast white cards (`#ffffff`) with subtle gray borders (`#d5d9d9`) on light slate backgrounds (`#f8fafc`).
- Information Density: Tables and attribute grids prioritize high information density, clear status badges, and rapid scanning over marketing fluff or empty space.
- Zero Jargon / Zero Emojis: Designed strictly for plant engineers, procurement officers, and inventory controllers without distracting buzzwords or emojis.
- Instant Utility: Every view provides actionable buttons (1-click Indent, Batch Approval, Gate Pass Print, RFC 4180 Excel CSV Export).

---

## 2. Directory Structure

```
frontend/
|-- src/
|   |-- app/                     # Next.js App Router pages
|   |   |-- audits/              # Sovereign compliance audit ledger page
|   |   |-- dashboard/           # Procurement KPIs and surplus inventory discovery radar
|   |   |-- deduplication/       # Material standardization workbench & MTC image viewer
|   |   |-- hitl/                # Human-in-the-Loop batch triage review queue
|   |   |-- transfers/           # Inter-CPSE material requisitions and CISF gate pass
|   |   |-- layout.tsx           # Root layout incorporating TopNav and styling
|   |   |-- page.tsx             # Root redirect to /dashboard
|   |   `-- globals.css          # Tailwind CSS directives and global typography
|   |-- components/              # Shared UI components
|   |   `-- TopNav.tsx           # Amazon-style global navigation header and depot switcher
|   `-- lib/                     # Client utilities
|       `-- exportUtils.ts       # RFC 4180 compliant Excel CSV export utility
|-- package.json                 # Node dependencies and scripts
|-- tsconfig.json                # Strict TypeScript compiler options
|-- tailwind.config.ts           # Tailwind CSS theme configuration
`-- README.md                    # This file
```

---

## 3. Application Routes & Features

### 1. Global Navigation Bar (`components/TopNav.tsx`)
- Deep Navy header (`#131921`) with Samanvay-AI identity.
- "Deliver to Depot" active operating depot selector (Panipat, Hazira, Kochi, Mathura, Uran).
- Global cross-CPSE procurement search bar with category dropdown and golden search button (`#febd69`).
- Sub-navigation ribbon (`#232f3e`) linking Dashboard, Deduplication, HITL Triage, Transfers, and Sovereign Audits.

### 2. Procurement & Surplus Radar Dashboard (`app/dashboard/page.tsx`)
- KPI Summary Cards: Surplus Items Identified, Working Capital Unlocked (INR), Active Inter-CPSE Requisitions, ASME Safety Invariant Accuracy (100%).
- Surplus Inventory Discovery Radar: Tabular view of idle stock across CPSE depots with search and CPSE filters (`All`, `IOCL`, `ONGC`, `BPCL`).
- Direct Action: 1-click "Issue Indent" button pre-populates a transfer requisition directly from the radar row.
- Export: 1-click "Export CSV" downloads a standardized RFC 4180 spreadsheet.

### 3. Material Deduplication & MTC Studio (`app/deduplication/page.tsx`)
- Real-Time Standardization Workbench: Paste any raw ERP description (e.g. `NRV 2IN 150# CS`) to view extracted attributes in milliseconds.
- Spec Attribute Grid: Side-by-side breakdown of Item Type, Nominal Bore mm, Pressure Class, Metallurgy, Facing, and Standard.
- ASME Tolerance Result: Clear Tier-1 (Identical), Tier-2 (Substitute), or Tier-3 (Incompatible) indicator with engineering justification.
- Scanned Document & MTC Viewer: Preset buttons to test against real procurement documents (`Image (1).jpeg` through `Image (7).jpeg`) showing OCR extracted items, heat numbers, and chemical analysis.

### 4. Human-in-the-Loop Batch Triage (`app/hitl/page.tsx`)
- Triage Review Cards: High-density cards displaying ambiguous matches (70%-90% confidence or Tier-2 upgrades) for engineer review.
- Spec Comparison Table: Side-by-side comparison of requested source parameters vs candidate inventory with `EXACT` and `UPGRADE` badges.
- Single & Batch Actions: Single-click "Approve" and "Reject" buttons, plus a "1-Click Bulk Approve All Safe Matches" button.
- Live Active Learning: Decisions instantly update the backend active learning cache without page reload.

### 5. Inter-CPSE Transfers & CISF Gate Pass (`app/transfers/page.tsx`)
- Transfer Requisitions Ledger: Status-tabbed view (`ALL`, `PENDING_APPROVAL`, `APPROVED`, `DISPATCHED`, `DELIVERED`).
- Multi-Depot Inventory Locks: Displays active surplus inventory reservation locks preventing double-allocation across depots.
- GIS Route Details: Displays calculated highway distance in kilometers, estimated transit duration, and road freight costs.
- Official Printable CISF Digital Gate Pass: Modal rendering of the statutory Central Industrial Security Force (CISF) Material Gate Pass with verification seal, authorized signatory fields, and scannable SVG QR code.

### 6. Sovereign Audit Trail Ledger (`app/audits/page.tsx`)
- Compliance Event Ledger: Chronological event stream compliant with CVC and CAG public procurement transparency guidelines.
- Cryptographic Verification: Displays the SHA-256 digital signature computed over event parameters with a "Verify Seal" integrity validator.
- Filtering & Export: Filter by CPSE or event category, with 1-click CSV export.

---

## 4. Local Development Setup

### 1. Install Node Dependencies
From the `frontend/` directory:
```powershell
npm install
```

### 2. Run Development Server
```powershell
npm run dev
```
Open `http://localhost:3000` in your web browser.

### 3. Production Build & Type Checking
To compile the application and verify all static routes:
```powershell
npm run build
```
Expected output:
- Compiles in ~2 seconds.
- Validates all TypeScript types and ESLint rules.
- Generates 9 static pages (`/`, `/_not-found`, `/dashboard`, `/deduplication`, `/hitl`, `/transfers`, `/audits`).
