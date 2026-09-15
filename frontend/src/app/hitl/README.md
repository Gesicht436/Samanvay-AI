# Human-in-the-Loop (HITL) Triage Queue (`app/hitl`)

## 1. Overview
The `app/hitl` directory implements the Human-in-the-Loop (HITL) verification panel at the `/hitl` route.

While Tier-1 identical components can be approved automatically, **Tier-2 Substitutions** (e.g. installing a Class 600 valve on a Class 300 line, or replacing Carbon Steel A105 with Stainless Steel F316) involve engineering upgrades. Although safe according to ASME rules, such substitutions must be reviewed by an authorized procurement officer or plant engineer before inventory is dispatched.

---

## 2. Key Components & Capabilities

### 1. High-Density Triage Review Cards
Each ambiguous match or upgrade candidate is presented in a self-contained review card:
- Source Item Header: Originating enterprise badge (`IOCL`, `ONGC`, `BPCL`), source depot location, SKU code, and raw ERP description.
- Suggested Candidate Header: Target enterprise, depot, canonical item code, and standardized description.
- Economic Metrics: Unit cost in INR, available surplus quantity, and days idle in storage.
- Safety Rationale: Algorithmic justification explaining why the substitution is a valid engineering upgrade.

### 2. Side-by-Side Parameter Inspection Matrix
A structured table comparing each critical specification:
- Item Type: Source vs Candidate with `EXACT` badge.
- Nominal Bore: Source size vs Candidate size with `EXACT` badge.
- Pressure Class: Comparison showing `UPGRADE` badge (e.g. Class 300 required vs Class 600 available).
- Metallurgy: Alloy comparison showing `UPGRADE` badge (e.g. Carbon Steel A105 vs Stainless F316).
- Facing / End: End connection status badge.

### 3. Triage Actions & Workflow Triggers
- Single-Item "Approve Match": Confirms the substitution, records the decision in the sovereign audit log, links the SKU in Neo4j, and boosts the match in the active learning cache.
- Single-Item "Reject Match": Rejects the substitution, logs the rejection note, and marks the pair as incompatible in the active learning cache.
- "1-Click Bulk Approve All Safe Matches": Authorizes all safe Tier-1 and verified Tier-2 matches in the queue simultaneously.
- 1-Click "Export CSV": Downloads the pending triage items into an RFC 4180 spreadsheet for offline engineering committee meetings.

---

## 3. Active Learning Feedback Loop
When an action button is clicked:
1. An asynchronous POST request is dispatched to `/api/v1/match/hitl-resolve` or `/api/v1/match/hitl-bulk-resolve`.
2. The item is removed from the active triage queue UI immediately (optimistic UI update).
3. The backend `ActiveLearningCache` registers the decision. Any subsequent search for that exact item will immediately reflect the engineer's judgment in `< 1ms` without requiring server restart or model retraining.
