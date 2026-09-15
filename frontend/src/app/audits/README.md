# Sovereign Audit Trail Ledger (`app/audits`)

## 1. Overview
The `app/audits` directory implements the central compliance and audit trail ledger at the `/audits` route.

In Indian Public Sector Undertakings (PSUs), procurement actions are strictly regulated by guidelines from the **Central Vigilance Commission (CVC)** and the **Comptroller and Auditor General of India (CAG)**. Any system that modifies item classifications, recommends substitutes, or authorizes inter-enterprise asset transfers must maintain an immutable, tamper-evident audit record.

---

## 2. Key Components & Capabilities

### 1. Chronological Compliance Event Stream
A high-density tabular view presenting every material reconciliation event across the federation:
- Timestamp: ISO UTC timestamp formatted in local Indian Standard Time (IST).
- Event ID & Action Type: Unique audit record number and standardized action tag (`HITL_APPROVAL`, `STANDARDIZATION_MATCH`, `REQUISITION_INITIATED`, `GATE_PASS_ISSUED`).
- Enterprise & SKU: Originating CPSE (`IOCL`, `ONGC`, `BPCL`) and source catalog SKU.
- Matched Master Item: Target canonical identifier (`CAN-000001` to `CAN-002200`).
- Equivalence Tier & Score: Assigned tier (`Tier-1`, `Tier-2`) and algorithmic confidence percentage.
- Reviewing Officer: User identifier or officer designation who authorized the action.
- Action Notes: Rationale justifying the decision.

### 2. Cryptographic SHA-256 Integrity Verification
To ensure that audit records cannot be tampered with or retroactively altered:
- Each event row stores a SHA-256 digital digest computed over the record parameters (SKU, CPSE, Canonical ID, Timestamp, Officer, Decision).
- Click the "Verify Seal" button in any row:
  - The client triggers an asynchronous check against `/api/v1/audit/verify/{audit_id}`.
  - The backend recomputes the SHA-256 hash over the raw database record.
  - A green badge displays `VERIFIED: Cryptographic Seal Intact`, confirming that the record has not been altered since creation.

### 3. Multi-Parameter Filtering & RFC 4180 CSV Export
- Search Bar: Search across descriptions, SKUs, and officer names.
- Enterprise Filter: Isolate events for `All CPSEs`, `IOCL`, `ONGC`, or `BPCL`.
- Action Category Filter: Filter specifically for `Approvals`, `Rejections`, or `Transfers`.
- 1-Click "Export CSV": Exports the complete audit ledger into an RFC 4180 compliant spreadsheet formatted for presentation to vigilance inspectors and external auditors.
