# Knowledge Graph Core Workflow: Neo4j Enterprise Ontology & Spare Locator

**Role:** Knowledge Graph Lead (Neo4j) (Harsh)

**Collaborators:**
* **Mayank** (API Gateway integration & Tier Distribution System Lead)
* **Shaurya** (Provides taxonomy CSV tables & helps on Tier Distribution benchmarks)
* **Ranvijay** (Frontend consumer of graph spare locator endpoints)

**Primary Directory:** `backend/app/graph/`

**Target Environment:** Python 3.14, Neo4j Python Bolt Driver, Cypher, Docker

---

### Objective & Architectural Role

Your mission is to build and manage the entire **Neo4j Knowledge Graph** ontology layer for **Samanvay-AI (BharatCodex)**.

While ML extracts attributes and Mayank/Shaurya's Tier Distribution System validates ASME safety compliance, the Knowledge Graph is the engine that answers the core multi-crore question: **"Where across India's CPSE depots is an identical or substitute spare part sitting idle right now?"**

You own the **complete Neo4j lifecycle**:
1. **Neo4j Infrastructure & Connection Pooling:** Manage the Bolt driver, connection health, and session lifecycle.
2. **Schema & Taxonomy Seeding:** Load and link UNSPSC v26, GeM categories, and the 2,200 Canonical Master materials.
3. **Cross-CPSE Reconciliation Queries:** Build high-speed Cypher graph traversals that discover idle stock across sister enterprises (IOCL $\leftrightarrow$ ONGC $\leftrightarrow$ BPCL) and link reconciled SKUs with audit trails.

```
Incoming Reconciled SKU (from Mayank's Tier Distribution Engine)
                           │
                           ▼
               ┌───────────────────────┐
               │    NEO4J GRAPH CORE   │
               │(`backend/app/graph/`) │
               └───────────┬───────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
  [Taxonomy Linking]  [Depot Inventory]  [Equivalence Links]
  (:UNSPSC_Commodity) (:CPSE_Depot)      (:LegacySKU)-[:MAPS_TO]->
  (:GeM_Category)     (:LegacySKU)       (:CanonicalMaterial)
         │                 │                 │
         └─────────────────┼─────────────────┘
                           ▼
                 Cypher Query Service
              (`app/graph/queries.py`)
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
  [Cross-CPSE Idle Spares]    [Reconciliation Cluster]
   IOCL Panipat needs flange   Connected graph components
   -> ONGC Hazira has 45 units for Ranvijay's UI display
```

---

### Step-by-Step Implementation Guide

#### Step 1: Neo4j Connection & Pool Management (`backend/app/graph/client.py`)
* Connect to Neo4j instance (`bolt://localhost:7687` or via Docker Compose `neo4j:7687`).
* Configure connection pooling, authentication (`neo4j / password`), and automatic reconnection.
* Provide clean context-managed session generators for Mayank's FastAPI dependency injection.

#### Step 2: Graph Schema & Taxonomy Seeding (`backend/app/graph/seed_graph.py`)
* **Input CSVs:**
  * [`data/taxonomies/unspsc_v26.csv`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/taxonomies/unspsc_v26.csv) (Segments, Families, Classes, Commodities).
  * [`data/taxonomies/gem_categories.csv`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/taxonomies/gem_categories.csv) (Government e-Marketplace categories).
  * [`data/taxonomies/canonical_master.csv`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/taxonomies/canonical_master.csv) (2,200 standard materials).
  * Synthetic CPSE inventory in [`data/mock_cpes_catalogs/`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/mock_cpes_catalogs/) (IOCL, ONGC, BPCL depot stock).
* **Graph Constraints to Create:**
  ```cypher
  CREATE CONSTRAINT IF NOT EXISTS FOR (c:CanonicalMaterial) REQUIRE c.canonical_id IS UNIQUE;
  CREATE CONSTRAINT IF NOT EXISTS FOR (u:UNSPSC_Commodity) REQUIRE u.code IS UNIQUE;
  CREATE CONSTRAINT IF NOT EXISTS FOR (g:GeM_Category) REQUIRE g.category_id IS UNIQUE;
  CREATE CONSTRAINT IF NOT EXISTS FOR (d:CPSE_Depot) REQUIRE d.depot_id IS UNIQUE;
  ```
* **Relationships to Build:**
  ```cypher
  (:CanonicalMaterial)-[:CLASSIFIED_UNDER]->(:UNSPSC_Commodity)
  (:CanonicalMaterial)-[:LISTED_ON_GEM]->(:GeM_Category)
  (:LegacySKU)-[:STORED_AT {quantity, idle_days, unit_cost}]->(:CPSE_Depot)
  ```

#### Step 3: High-Performance Cypher Queries (`backend/app/graph/queries.py`)

1. **Cross-CPSE Spare Locator:**
   ```cypher
   // Given a source SKU, find matching idle stock at sister CPSE depots
   MATCH (s:LegacySKU {local_code: $sku_code, cpse: $source_cpse})
         -[:MAPS_TO]->(c:CanonicalMaterial)
         <-[:MAPS_TO]-(other:LegacySKU)
         -[stock:STORED_AT]->(d:CPSE_Depot)
   WHERE other.cpse <> $source_cpse AND stock.quantity > 0
   RETURN other.local_code AS equivalent_sku, 
          other.cpse AS owner_cpse, 
          d.location_name AS depot, 
          d.depot_id AS depot_id,
          stock.quantity AS available_qty, 
          stock.idle_days AS days_idle,
          stock.unit_cost AS unit_cost
   ORDER BY stock.idle_days DESC;
   ```

2. **Reconciliation Mapping & HITL Link Writer:**
   ```cypher
   // Persist human-approved or auto-matched links
   MERGE (s:LegacySKU {local_code: $sku_code, cpse: $cpse})
   MERGE (c:CanonicalMaterial {canonical_id: $canonical_id})
   MERGE (s)-[r:MAPS_TO]->(c)
   SET r.tier = $tier,
       r.confidence = $confidence,
       r.verified_by_hitl = $verified_by_hitl,
       r.updated_at = datetime();
   ```

3. **Inter-Enterprise Deduplication Cluster Traversal:**
   * Cypher query returning connected components for Ranvijay's UI visualizer.

---

### File Deliverables & Directory Layout

Work strictly inside `backend/app/graph/`:

```
backend/app/graph/
├── __init__.py
├── client.py             # Neo4j Bolt driver initialization & connection pooling
├── seed_graph.py         # Automated database seeding script from taxonomies & catalogs
└── queries.py            # Optimized Cypher traversal functions
```

**Interface Signatures:**
```python
# graph/client.py
def get_neo4j_session():
    """Yields an active Neo4j session for FastAPI route dependencies."""
    ...

# graph/queries.py
def link_reconciled_sku(sku_code: str, cpse: str, canonical_id: str, tier: str, confidence: float, verified: bool = False) -> None:
    """Creates or updates MAPS_TO relationship between LegacySKU and CanonicalMaterial."""
    ...

def find_inter_cpse_spares(sku_code: str, source_cpse: str) -> list[dict]:
    """Finds available idle inventory across sister CPSE depots for the requested item."""
    ...
```

---

### Team Collaboration & Handoffs
1. **From Mayank's Tier Distribution System:** You receive approved matches with their assigned tiers (`TIER_1_IDENTICAL` or `TIER_2_SUBSTITUTE`) to persist into the graph.
2. **To Mayank's API Gateway:** Your `find_inter_cpse_spares()` powers the `GET /api/v1/graph/spares/{sku_code}` endpoint.
3. **To Ranvijay's UI:** Your cross-depot results populate the **Cross-CPSE Spare Locator Table** on the Next.js Procurement Analytics Dashboard.
