# Procurement & Working Capital Dashboard (`app/dashboard`)

## 1. Overview
The `app/dashboard` directory implements the primary operational dashboard of Samanvay-AI at the `/dashboard` route.

It gives plant managers, chief materials managers, and inventory controllers a high-level view of idle surplus inventory across sister CPSEs (IOCL, ONGC, BPCL), unlocked working capital, and active inter-refinery material transfer indents.

---

## 2. Key Components & Metrics

### 1. Key Performance Indicator (KPI) Metric Cards
- Surplus Items Identified: Count of idle line items detected across participating depots.
- Working Capital Unlocked: Total monetary valuation in INR of identified surplus materials that can be transferred instead of purchasing new inventory.
- Active Inter-CPSE Requisitions: Number of open transfer orders currently in transit or awaiting gate pass clearance.
- ASME Safety Invariant Accuracy: Real-time validation accuracy (100.00% across the 150 Golden Benchmark test cases).

### 2. Cross-CPSE Surplus Inventory Discovery Radar
A high-density tabular view listing available surplus stock:
- Material Details: Standardized description, canonical identifier, and UNSPSC commodity classification.
- Holding Enterprise: CPSE badge (`IOCL`, `ONGC`, `BPCL`) and specific holding depot (e.g. Panipat Refinery, Hazira Gas Plant, Kochi Refinery).
- Inventory Status: Available surplus quantity, unit rate in INR, and number of days the item has been sitting idle in storage.
- Safety Tier Indicator: Tier-1 Identical or Tier-2 Substitute compatibility indicator.

### 3. Search and Multi-Parameter Filtering
- Text Search: Live text filtering across descriptions, SKU codes, and depot names.
- CPSE Filter: Filter by `All CPSEs`, `IOCL`, `ONGC`, or `BPCL`.
- Category Filter: Filter by mechanical component types (Flanges, Valves, Pipes, Gaskets, Motors, Seals, Bearings).

### 4. Direct Operational Triggers
- 1-Click "Issue Indent": Launches a transfer requisition pre-filled with source and target depot information, material specifications, and unit rates.
- 1-Click "Export CSV": Generates an RFC 4180 compliant Excel CSV file containing filtered radar data for offline review and procurement committee meetings.

---

## 3. Implementation Details (`page.tsx`)
- Framework: React 19 Client Component (`'use client'`).
- Data Fetching: Calls `fetchSurplusRadar()` from `lib/api.ts` on initial mount, automatically falling back to mock fixtures if offline.
- CSV Export Integration: Uses `exportToCsv` from `lib/exportUtils.ts` with customized column headers and numeric formatting.
