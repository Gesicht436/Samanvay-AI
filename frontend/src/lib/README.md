# Client Libraries & Utilities (`frontend/src/lib`)

## 1. Overview
The `lib` directory contains shared TypeScript utilities, data types, the centralized HTTP API client, and resilient mock fixtures.

---

## 2. Directory Structure

```
frontend/src/lib/
|-- api.ts                       # Centralized HTTP API client with backend integration
|-- exportUtils.ts               # RFC 4180 compliant Excel CSV export utility
|-- mockData.ts                  # Resilient fallback fixtures for offline operation
|-- types.ts                     # TypeScript type definitions and interfaces
`-- README.md                    # This file
```

---

## 3. Module Reference

### 1. Centralized API Client (`api.ts`)
`api.ts` provides strongly-typed asynchronous functions for all backend API endpoints:
- `matchSingleItem(query, topK)`: Calls `POST /api/v1/match/single`.
- `fetchHitlQueue(limit)`: Calls `GET /api/v1/match/hitl-queue`.
- `resolveHitlItem(payload)`: Calls `POST /api/v1/match/hitl-resolve`.
- `bulkResolveHitl(items, officer)`: Calls `POST /api/v1/match/hitl-bulk-resolve`.
- `createRequisition(payload)`: Calls `POST /api/v1/requisition/create`.
- `fetchRequisitions()`: Calls `GET /api/v1/requisition/list`.
- `fetchInventoryLocks()`: Calls `GET /api/v1/requisition/inventory-locks`.
- `updateRequisitionAction(reqId, action)`: Calls `POST /api/v1/requisition/{req_id}/action`.
- `fetchGatePass(reqId)`: Calls `GET /api/v1/requisition/{req_id}/gate-pass`.
- `calculateDistance(sourceDepot, targetDepot)`: Calls `POST /api/v1/requisition/calculate-distance`.
- `fetchSurplusRadar(canonicalId)`: Calls `GET /api/v1/graph/surplus-radar`.
- `fetchAuditLedger(limit)`: Calls `GET /api/v1/audit/ledger`.
- `verifyAuditRecord(auditId)`: Calls `GET /api/v1/audit/verify/{audit_id}`.
- `fetchFeedbackCache()`: Calls `GET /api/v1/match/feedback-cache`.

#### Network Resilience Pattern
Every API function wraps its `fetch()` call in a try/catch block. If the backend is offline, unreachable, or in development mode without databases, the function automatically returns realistic mock data from `mockData.ts`. This guarantees that UI screens and presentation demos remain 100% functional under any environment conditions.

---

### 2. RFC 4180 CSV Export Utility (`exportUtils.ts`)
`exportUtils.ts` implements a standardized spreadsheet export function:
```typescript
export function exportToCsv<T>(
  data: T[],
  filename: string,
  columnMapping: { [K in keyof T]?: string }
): void
```
- RFC 4180 Compliance: Handles fields containing commas, double quotes, or newlines by wrapping them in quotes and escaping internal quotes (`""`).
- Browser Download: Creates an in-memory `Blob` with `text/csv;charset=utf-8;` MIME type and triggers an automatic browser file download.
- Reusability: Integrated into the Dashboard, HITL Triage Queue, Transfers Hub, and Sovereign Audits ledger.

---

### 3. Shared TypeScript Contracts (`types.ts`)
Defines the exact TypeScript interfaces matching backend Pydantic v2 schemas:
- `MatchEvaluationResult`: Equivalence tiers, scores, parameter checks, and engineering rationale.
- `SurplusRadarItem`: Cross-CPSE inventory holdings with depot coordinates and idle durations.
- `HITLQueueItem`: Ambiguous match pairs pending human review.
- `TransferRequisition`: Requisition lifecycle details and logistics estimates.
- `AuditRecord`: Chronological compliance events with cryptographic SHA-256 digital seals.

---

### 4. Resilient Mock Fixtures (`mockData.ts`)
Contains realistic, domain-accurate fixtures across:
- Indian energy depots (Panipat, Hazira, Kochi, Mathura, Uran).
- Real material descriptions (e.g. `FLG WNRF 4IN 300# A105`, `VLV-GT-DN50-CL300-WCB-RF`).
- Realistic INR valuations and idle storage durations.
