# Knowledge Graph & Logistics Topology (`graph/`)

This directory implements the **Property Star Knowledge Graph** and **Inter-Plant Logistics Topology Engine** using **Neo4j 5.20**.

While vector databases identify unstructured semantic similarities, the knowledge graph provides **topological awareness**:
- Models physical asset ownership across 5 major public sector undertakings (IOCL, ONGC, GAIL, BPCL, HPCL).
- Models spatial warehouse and depot coordinates across India (Hazira, Paradip, Jamnagar, Vadodara, Mathura, Mumbai, etc.).
- Computes multi-modal transit logistics, road distances, transit hours, freight costs, and green transport carbon footprints ($CO_2$ emissions).
- Tracks material substitution paths and cluster-level surplus availability.

---

## 1. File-by-File Breakdown

### `schema.py` — Graph Ontologies & Enums
- **Purpose:** Defines standard node labels, relationship types, and edge property contracts.
- **Key Enums:**
  - `NodeTypes`:
    - `CPSE`: Enterprise nodes (e.g. `name: "IOCL"`, `code: "IOCL"`).
    - `Plant`: Refinery/Petrochemical complexes (e.g. `name: "Paradip Refinery"`).
    - `Depot`: Warehouse locations storing physical materials.
    - `Item`: Specific inventory stock units (SKUs).
    - `PhysicalSpec`: Abstract engineering specification grouping interchangeable physical items.
    - `MaterialGrade`: Metallurgical alloy definitions (e.g. `ASTM A105`, `ASTM A182 F316L`).
    - `PressureRating`: ASME rating classes (`150#`, `300#`, `600#`).
    - `Dimension`: Nominal sizes (`2 INCH`, `4 INCH`, `DN100`).
  - `RelTypes`:
    - `(:CPSE)-[:OWNS]->(:Plant)`
    - `(:Plant)-[:HAS_DEPOT]->(:Depot)`
    - `(:Depot)-[:STOCKS]->(:Item)`
    - `(:Item)-[:CONFORMS_TO]->(:PhysicalSpec)`
    - `(:PhysicalSpec)-[:HAS_MATERIAL]->(:MaterialGrade)`
    - `(:Depot)-[:TRANSIT_ROUTE_TO {distance_km, hours}]->(:Depot)`
  - `CompatEdges`:
    - `(:PhysicalSpec)-[:CAN_SUBSTITUTE_FOR {tier, confidence, verified_by_rules}]->(:PhysicalSpec)`

### `logistics.py` — Haversine & Carbon Freight Calculations
- **Purpose:** Computes inter-depot freight logistics, transit times, and carbon emissions.
- **Key Functions:**
  - `haversine_distance(lat1, lon1, lat2, lon2) -> float`:
    - Calculates the great-circle surface distance between two GPS coordinates using the Haversine formula:
      $$d = 2R \arcsin \left( \sqrt{ \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right) } \right)$$
      where $R = 6,371\text{ km}$.
  - `road_distance(lat1, lon1, lat2, lon2) -> float`:
    - Applies the Indian National Highway circuity factor ($1.25 \times$ Haversine distance) to account for road terrain and routing detours.
  - `estimate_transit_hours(distance_km: float) -> float`:
    - Computes transit duration assuming an average heavy commercial vehicle speed of $40\text{ km/h}$ plus statutory inter-state border checkpoint and toll delays ($2.0\text{ hrs}$ buffer).
  - `calculate_freight_co2(distance_km: float, weight_mt: float) -> float`:
    - Implements the **Bureau of Energy Efficiency (BEE)** freight emission standard:
      $$\text{Emissions (kg } CO_2) = \frac{\text{Distance (km)} \times \text{Weight (Metric Tonnes)} \times 62\text{ g } CO_2}{1000}$$
  - `estimate_freight_cost(distance_km: float, weight_mt: float) -> float`:
    - Models Indian freight economics based on per-tonne-km tariff schedules with minimum mobilization base fees.

### `queries.py` — Cypher Query Repository
- **Purpose:** Encapsulates optimized, parameterized Neo4j Cypher queries.
- **Key Classes:**
  - `GraphQuerier`:
    - `find_surplus_clusters(item_type: str, min_qty: int)`: Identifies depots with surplus stockpiles exceeding local consumption thresholds.
    - `find_interchangeable_candidates(spec_id: str)`: Traverses transitive `CAN_SUBSTITUTE_FOR` edges up to depth 2.
    - `get_shortest_transit_path(from_depot: str, to_depot: str)`: Cypher Dijkstra shortest-path traversal on `TRANSIT_ROUTE_TO` relationships.

### `syncer.py` — PostgreSQL to Neo4j Change Data Capture (CDC) Syncer
- **Purpose:** Keeps the knowledge graph synchronized in real time with transactional changes occurring in PostgreSQL.
- **Key Classes:**
  - `Neo4jSyncer`:
    - `sync_item(item_data)`: Creates or updates `(:Item)` node, attaches it to the owning `(:Depot)` and `(:CPSE)`, and creates relationships to its `(:PhysicalSpec)`.
    - `update_stock(sku_code: str, new_qty: int)`: Atomically updates the stock quantity property on the item node.
    - `batch_sync(items_list)`: Executes high-throughput batched UNWIND Cypher statements for bulk initial ingestion.

### `seed_graph.py` — Graph Topology Initializer
- **Purpose:** Seeds the database with sovereign enterprise nodes, refineries, depots, GPS coordinates, and baseline road transit routes across India.
- **Key Classes:**
  - `GraphSeeder`:
    - Sets unique index constraints: `CREATE CONSTRAINT FOR (c:CPSE) REQUIRE c.code IS UNIQUE`, etc.
    - Pre-populates 15+ major Indian hydrocarbon industrial clusters (Paradip, Hazira, Jamnagar, Mumbai, Visakhapatnam, Mathura, Haldia, Kochi, etc.).

---

## 2. Tech Stack & Dependencies

| Tool / Library | Version | Purpose |
|---|---|---|
| **Neo4j** | `5.20-community` | Graph database engine |
| **neo4j-driver** | `^5.18.0` | Official asynchronous and synchronous Python Bolt protocol driver |
| **Python math** | `3.11+` | High-precision trigonometric computation for spherical distance calculations |

---

## 3. Graph Data Model & Cypher Example

```
(:CPSE {code: "IOCL"})
       │
       ▼ [:OWNS]
(:Plant {name: "Paradip Refinery"})
       │
       ▼ [:HAS_DEPOT]
(:Depot {id: "IOCL-PR", lat: 20.26, lon: 86.67})
       │
       ▼ [:STOCKS]
(:Item {sku: "IOCL-PR-VLV-01", qty: 14})
       │
       ▼ [:CONFORMS_TO]
(:PhysicalSpec {type: "GATE_VALVE", size: "4 INCH", class: 300, mat: "A216-WCB"})
       │
       ▲ [:CAN_SUBSTITUTE_FOR {tier: 2, verified_by_rules: true}]
(:PhysicalSpec {type: "GATE_VALVE", size: "4 INCH", class: 600, mat: "A350-LF2"})
```

### Finding Surplus Within 500km Transit Radius:
```cypher
MATCH (origin:Depot {id: $requisition_depot})
MATCH (target:Depot)-[:STOCKS]->(item:Item)-[:CONFORMS_TO]->(spec:PhysicalSpec)
WHERE spec.type = $item_type AND item.qty >= $min_qty AND target.id <> origin.id
WITH origin, target, item, spec,
     point.distance(point({latitude: origin.lat, longitude: origin.lon}),
                    point({latitude: target.lat, longitude: target.lon})) / 1000.0 AS direct_km
WHERE direct_km <= 500.0
RETURN target.name, item.sku, item.qty, direct_km
ORDER BY direct_km ASC;
```

---

## 4. How to Test

```bash
# Run unit tests for Haversine logistics & road distance calculations
pytest tests/unit/test_logistics.py -v

# Run API integration tests for graph discovery endpoints
pytest tests/api/test_graph_api.py -v
```
