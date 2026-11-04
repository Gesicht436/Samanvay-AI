# Mechanical Safety Rules & Tolerance Classification Engine (`backend/app/matching/`)

## 1. Architectural Role & Overview

The `backend/app/matching/` package provides the deterministic mechanical and metallurgical rule evaluation layer within the backend.

It bridges low-level engineering physics checks with high-level API match responses, executing:
1. **ASME & ASTM Invariant Checks**: Evaluating nominal bore dimensions, ASME pressure class over-ratings, and directional corrosion alloy upgrades.
2. **Deterministic Safety Gating**: Calling into the 21 domain safety modules (`machine_learning/safety.py`) to catch zero-tolerance hazards before candidate suggestions reach users.
3. **Automated Workflow Routing**: Assigning standardized operational routing actions (`auto-link`, `hitl`, `manual-entry`) based on resulting tiers.

```mermaid
flowchart TD
    Req["ExtractedMaterialAttributes (Query Q)"] --> Matcher["tolerance.py: classify_candidate()"]
    Cand["CandidateMatch (Candidate C)"] --> Matcher

    subgraph ASMERules["1. Core ASME / ASTM Checks (asme_rules.py)"]
        Matcher --> SM["size_matches(): Strict Dims (NB mm)"]
        Matcher --> PS["pressure_substitutes(): Safe Over-Rating (>=)"]
        Matcher --> MS["metallurgy_substitutes(): ALLOY_UPGRADES DAG"]
    end

    subgraph SafetyGate["2. Zero-Tolerance Safety Gating"]
        Matcher --> SVG["machine_learning.safety: safety_violations()"]
        SVG --> Modules["21 Physical Hazard Modules (ASME, NACE, API, TEMA)"]
    end

    subgraph TieringAndRouting["3. Tier Assignment & Routing"]
        Matcher --> AT["machine_learning.tiers: assign_tier()"]
        AT -->|Tier-1 (>= 95%)| AutoLink["routing: 'auto-link' (Direct Procurement)"]
        AT -->|Tier-2 (80-94%)| HITL["routing: 'hitl' (Technical Authority Sign-off)"]
        AT -->|Tier-3 / Violations| Manual["routing: 'manual-entry' / Reject"]
    end
```

---

## 2. Module Inventory

| File | Primary Functions & Classes | Purpose |
| :--- | :--- | :--- |
| [`asme_rules.py`](file:///C:/Users/mayank/Development/Hackathons/Samanvay-AI/backend/app/matching/asme_rules.py) | `RuleDecision`, `size_matches()`, `pressure_substitutes()`, `metallurgy_substitutes()`, `ALLOY_UPGRADES` | Implements deterministic rule logic for dimensional equality, pressure class rating thresholds, and verified alloy upgrades. |
| [`tolerance.py`](file:///C:/Users/mayank/Development/Hackathons/Samanvay-AI/backend/app/matching/tolerance.py) | `classify_candidate()` | Combines dimensional checks, pressure rating rules, alloy upgrades, and all 21 safety violation checks into an authoritative `MatchResult`. |
| [`__init__.py`](file:///C:/Users/mayank/Development/Hackathons/Samanvay-AI/backend/app/matching/__init__.py) | Package initialization | Module namespace anchor. |

---

## 3. Engineering Rules & Invariant Logic

### 3.1. Dimensional Invariance (`size_matches`)
- Pipe diameters, flange nominal bores, and valve port sizes require exact parity ($NB_{\text{requested}} == NB_{\text{candidate}}$).
- Even minor dimensional variations cause immediate mechanical fit-up failures, flange bolt circle mismatches, or severe flow choke points.

### 3.2. Safe Pressure Over-Rating (`pressure_substitutes`)
- Pressure downgrades ($Class_{\text{candidate}} < Class_{\text{requested}}$) are strictly rejected to prevent catastrophic hydrostatic burst hazards under refinery operating pressures.
- Dimension-preserving pressure over-ratings ($Class_{\text{candidate}} \ge Class_{\text{requested}}$) are permitted when flange dimensions or wall schedules align safely.

### 3.3. Directed Alloy Upgrade DAG (`metallurgy_substitutes`)
Upgrades are unidirectional along verified corrosion and temperature resistance paths (`ALLOY_UPGRADES`):
- `304` $\longrightarrow$ `304L`, `316`, `316L`
- `304L` $\longrightarrow$ `316`, `316L`
- `316` $\longrightarrow$ `316L`
- `A105` (Carbon Steel) $\longrightarrow$ `F316`, `F316L` (Stainless Steel)

Any reverse substitution (e.g., substituting carbon steel for stainless steel, or higher-carbon standard grade for low-carbon `$L$` grade in nitric acid service) triggers an immediate safety violation.

---

## 4. Operational Routing Logic (`classify_candidate`)

Based on candidate similarity and the aggregated violation list, the system assigns one of three operational routing actions:

| Resulting Tier | Rule Violations | System Routing | Operational Action |
| :--- | :--- | :--- | :--- |
| **Tier-1** | None | `auto-link` | Automated direct reservation; immediate inter-CPSE transfer enabled. |
| **Tier-2** | Requires verification | `hitl` | Queued for Technical Authority / Chief Metallurgist digital sign-off. |
| **Tier-3 / Tier-4-Reject** | Fatal violation present | `manual-entry` | Hard rejection; blocked from transfer to eliminate plant safety hazards. |
