# Knowledge Graph & Ontology (`backend/app/graph`)

## 1. Overview
The `graph` package implements the enterprise ontology for Samanvay-AI using **Neo4j** and Cypher queries.

The Knowledge Graph connects legacy enterprise SKUs across IOCL, ONGC, and BPCL to a standardized Canonical Master Catalog, and maps them to international commodity taxonomies (UNSPSC v26) and the Government e-Marketplace (GeM).

---

## 2. Graph Data Model & Ontology Schema

```
   (:UNSPSC_Class)                      (:GeM_Category)
           ^                                    ^
           | [:CLASSIFIED_UNDER]                | [:MAPPED_TO]
           |                                    |
   +----------------------------------------------------+
   |               (:CanonicalItem)                     |
   | canonical_id: "CAN-000001"                         |
   | item_type: "FLANGE_WELD_NECK"                      |
   | size_nb_mm: 100.0, pressure_class: 300             |
   | metallurgy: "ASTM A105", facing_end: "RF"          |
   +----------------------------------------------------+
           ^                                    ^
           | [:MAPS_TO {tier, confidence}]      | [:MAPS_TO]
           |                                    |
   (:CPSE_SKU {cpse: "IOCL"})           (:CPSE_SKU {cpse: "ONGC"})
   sku_code: "IOCL-MM-0004128"          sku_code: "ONGC-MAT-0000092"
           |                                    |
           | [:LOCATED_AT {qty: 45}]            | [:LOCATED_AT {qty: 12}]
           v                                    v
   (:Depot {name: "Panipat"})           (:Depot {name: "Hazira"})
```

### Node Labels
1. `(:CanonicalItem)`: The unified enterprise master item. Represents unique physical engineering specifications.
2. `(:CPSE_SKU)`: Proprietary inventory catalog numbers used in enterprise ERPs (IOCL, ONGC, BPCL).
3. `(:Depot)`: Physical storage locations (e.g. Panipat Refinery, Hazira Gas Plant, Kochi Refinery).
4. `(:UNSPSC_Class)`: United Nations Standard Products and Services Code (e.g. 40141600 for Valves and Flanges).
5. `(:GeM_Category)`: Indian Government e-Marketplace procurement category identifier.

### Relationship Types
- `(:CPSE_SKU)-[:MAPS_TO {tier, confidence, verified_by_hitl}]->(:CanonicalItem)`: Core reconciliation edge established deterministically or via HITL review.
- `(:CPSE_SKU)-[:LOCATED_AT {available_qty, unit_cost_inr, days_idle}]->(:Depot)`: Tracks physical inventory holding at depots.
- `(:CanonicalItem)-[:CLASSIFIED_UNDER]->(:UNSPSC_Class)`: Maps engineering specs to global supply codes.
- `(:CanonicalItem)-[:MAPPED_TO]->(:GeM_Category)`: Maps items to public procurement portal categories.

---

## 3. In-Memory Mock Fallback Mode

To ensure seamless local development without forcing every junior developer to install and run a Neo4j Docker container:
- `client.py` attempts connection to `bolt://localhost:7687`.
- If Neo4j is unreachable, the system automatically logs a diagnostic warning and activates an **In-Memory Graph Mock**.
- All queries in `queries.py` seamlessly switch to mock data structures, allowing unit tests and API endpoints to function with zero disruption.

---

## 4. Key Cypher Queries (`queries.py`)

### 1. Cross-CPSE Surplus Inventory Radar
Given a canonical item ID, finds all depots across all three CPSEs holding surplus stock:
```cypher
MATCH (c:CanonicalItem {canonical_id: $canonical_id})<-[m:MAPS_TO]-(sku:CPSE_SKU)-[loc:LOCATED_AT]->(d:Depot)
RETURN sku.sku_code AS sku_code,
       sku.cpse AS cpse,
       sku.description AS description,
       d.name AS depot_name,
       d.state AS depot_state,
       loc.available_qty AS available_qty,
       loc.unit_cost_inr AS unit_cost_inr,
       loc.days_idle AS days_idle,
       m.tier AS tier,
       m.confidence AS confidence
ORDER BY loc.days_idle DESC
```

### 2. Linking Reconciled SKU After Human Approval
When an engineer confirms a match in the HITL triage UI, this Cypher mutation links the SKU:
```cypher
MERGE (sku:CPSE_SKU {sku_code: $sku_code})
ON CREATE SET sku.cpse = $cpse
WITH sku
MATCH (canon:CanonicalItem {canonical_id: $canonical_id})
MERGE (sku)-[r:MAPS_TO]->(canon)
SET r.tier = $tier,
    r.confidence = $confidence,
    r.verified_by_hitl = $verified_by_hitl,
    r.officer = $officer,
    r.updated_at = datetime()
RETURN r
```

---

## 5. Seeding the Graph (`seed_graph.py`)
To populate Neo4j with 2,200 canonical materials and 10,800 simulated depot records:
```powershell
uv run python -m backend.app.graph.seed_graph
```
