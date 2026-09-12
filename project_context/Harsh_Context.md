# Algorithmic Rules & Knowledge Graph Workflow: Deterministic ASME Engine & Neo4j Ontology

**Role:** Algorithmic Rules & Knowledge Graph Lead (Harsh)

**Primary Directory:** `backend/app/matching/` and `backend/app/graph/`

**Target Environment:** Python 3.14, Neo4j Python Bolt Driver, Cypher, NumPy/Polars, Pydantic v2

---

### Objective & Architectural Role

Your mission is to build the deterministic validation guardrails and the semantic ontology layer for **Samanvay-AI (BharatCodex)**.

Machine learning alone cannot make procurement decisions in hydrocarbon refineries. A vector embedding model might assign a 92% similarity between a Class 150 flange and a Class 300 flange because the words look nearly identical, but installing that part on an active pipeline risks catastrophic failure.

You own the critical downstream logic:

1. **The Deterministic Rule Engine:** Enforce zero-tolerance ASME, ASTM, and API mechanical constraints on top of the vector candidate pool.

2. **The Knowledge Graph (Neo4j):** Model hierarchical enterprise taxonomies (UNSPSC v26, GeM) and manage cross-CPSE equivalence links (e.g., `IOCL_SKU` $\leftrightarrow$ `Canonical_Material` $\leftrightarrow$ `ONGC_SKU`).

```
               [From Hariom: NER Extracted Attributes & Vector Candidates][cite: 1]
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │    TASK 1: DETERMINISTIC ENGINE       │
                      │      (`app/matching/asme_rules.py`)   │
                      │                                       │
                      │  • Nominal Bore (NB) Invariant Check  │
                      │  • Pressure Class Tolerance Rating    │
                      │  • ASTM Metallurgy Upgrade Matrix     │
                      └───────────────────┬───────────────────┘
                                          │
                   Categorize into Safety & Equivalence Tiers
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
          [Tier-1: Identical]    [Tier-2: Substitute]    [Tier-3: Incompatible]
          (100% Drop-in Safe)    (Higher Spec Upgrade)    (Rejection Flagged)
                  │                       │
                  └───────────┬───────────┘
                              ▼
                      ┌───────────────────────────────────────┐
                      │     TASK 2: NEO4J ONTOLOGY GRAPH      │
                      │       (`app/graph/queries.py`)        │
                      │                                       │
                      │  • Link to Canonical Material Node    │
                      │  • Map to UNSPSC v26 & GeM Categories │[cite: 1]
                      │  • Query Nearest Idle Depot Spares    │[cite: 1]
                      └───────────────────────────────────────┘

```

---

### Task 1: Deterministic Tolerance & Verification Engine (`backend/app/matching/`)

You will translate engineering standards into fast, deterministic Python validation algorithms.

* **Module Files:**
* `backend/app/matching/tolerance.py`: Physical dimensional and pressure invariant verifiers.
* `backend/app/matching/asme_rules.py`: ASME B16.5, ASTM, and API logic matrices.

* **Algorithmic Rules to Implement:**
* **Rule 1: Dimension Invariant (Hard Reject)**
* If `candidate.size_nb_mm != source.size_nb_mm`, immediately flag as **Tier-3 (Incompatible)**. A $50\text{ mm}$ line cannot mate with a $65\text{ mm}$ flange under any circumstances.

* **Rule 2: Pressure Rating Compatibility**
* Down-rating is strictly forbidden: A Class 150 part can **never** substitute for a Class 300 part.
* Up-rating may qualify as a substitute (Tier-2) only if bolt hole configurations and facing types match (e.g., ASME B16.5 allowances).

* **Rule 3: Metallurgy Compatibility Matrix (ASTM Rules)**
* Build an adjacency matrix / directed compatibility graph for standard piping alloys:
* **Carbon Steel:** `ASTM A105` (Forged) $\leftrightarrow$ `ASTM A216 WCB` (Cast).
* **Upgrades Permitted (Tier-2):** `ASTM A312 TP316` (Stainless) can safely substitute for `ASTM A105` (Carbon Steel) in non-corrosive, non-high-temp boundary scenarios, but `A105` can **never** substitute for `TP316`.
* **Low Temperature:** `ASTM A350 LF2` required for sub-zero duties; standard `A105` is an invalid substitute.

* **Rule 4: Facing & End-Connection Matching**
* `RF` (Raised Face) $\neq$ `RTJ` (Ring Type Joint).
* `BW` (Butt Weld) $\neq$ `SW` (Socket Weld) $\neq$ `THRD` (Threaded).

* **Output Schema (Contracts):**
Assign each candidate match an `EquivalenceTier` enum:
* `TIER_1_IDENTICAL`: Exact engineering parity ($100\%$ dimension, rating, and metallurgy compatibility).
* `TIER_2_SUBSTITUTE`: Functional substitute meeting or exceeding original specifications (upgrade with identical mating interfaces).
* `TIER_3_INCOMPATIBLE`: Violates one or more hard physical constraints.

---

### Task 2: Neo4j Knowledge Graph & Ontology Service (`backend/app/graph/`)

You will model and query the canonical semantic graph representing relationships across CPSE catalogs, standards, and depot physical locations.

* **Module Files:**
* `backend/app/graph/client.py`: Neo4j Bolt driver initialization and connection pooling.

* `backend/app/graph/queries.py`: Optimized Cypher traversal functions.

* **Graph Schema Design:**
* **Nodes:**
* `(:LegacySKU {id, cpse, raw_description, local_code})`

* `(:CanonicalMaterial {canonical_id, name, size_nb_mm, pressure_class, metallurgy})`

* `(:UNSPSC_Commodity {code, title, class_code, family_code})`

* `(:GeM_Category {category_id, name})`

* `(:CPSE_Depot {depot_id, cpse, location_name, latitude, longitude})`

* **Edges / Relationships:**
* `(:LegacySKU)-[:MAPS_TO {confidence, verified_by_hitl}]->(:CanonicalMaterial)`
* `(:CanonicalMaterial)-[:CLASSIFIED_UNDER]->(:UNSPSC_Commodity)`

* `(:CanonicalMaterial)-[:LISTED_ON_GEM]->(:GeM_Category)`
* `(:LegacySKU)-[:STORED_AT {quantity, idle_days, unit_cost}]->(:CPSE_Depot)`
* `(:CanonicalMaterial)-[:SUBSTITUTE_FOR {safety_margin, rule_ref}]->(:CanonicalMaterial)`

* **Cypher Queries to Implement:**

1. **Cross-CPSE Reconciliation:**

```cypher
// Given an IOCL SKU, find equivalent spare inventory at nearby ONGC or BPCL depots
MATCH (s:LegacySKU {local_code: $sku_code, cpse: $source_cpse})
      -[:MAPS_TO]->(c:CanonicalMaterial)
      <-[:MAPS_TO]-(other:LegacySKU)
      -[stock:STORED_AT]->(d:CPSE_Depot)
WHERE other.cpse <> $source_cpse AND stock.quantity > 0
RETURN other.local_code AS equivalent_sku, other.cpse AS owner_cpse, 
       d.location_name AS depot, stock.quantity AS available_qty, 
       stock.idle_days AS days_idle

```

1. **Inter-Enterprise Deduplication Cluster:**

* Traversal query returning connected components linking legacy SKUs to canonical items to power Ranvijay’s React Flow graph visualization on the frontend.

---

### Task 3: Directory Deliverables & Interface Signatures

You work strictly within `backend/app/matching/` and `backend/app/graph/`:

```
backend/app/
├── matching/
│   ├── __init__.py
│   ├── asme_rules.py         # Metallurgy & pressure rating validation tables[cite: 1]
│   └── tolerance.py          # Strict equality checks and tier classification
└── graph/
    ├── __init__.py
    ├── client.py             # Neo4j connection pool manager[cite: 1]
    ├── queries.py            # Cypher query functions[cite: 1]
    └── seed_graph.py         # Seeds UNSPSC v26 and GeM taxonomies from Shaurya's tables[cite: 1]

```

**Interface Signatures:**

```python
# matching/tolerance.py
def evaluate_compatibility(
    source_attr: ExtractedMaterialAttributes, 
    candidate_attr: ExtractedMaterialAttributes
) -> MatchEvaluationResult:
    """
    Applies ASME/ASTM rules. Returns EquivalenceTier (Tier-1, Tier-2, Tier-3) 
    and detailed engineering rationale.
    """
    ...

# graph/queries.py
def link_reconciled_sku(
    tx, 
    sku_id: str, 
    canonical_id: str, 
    tier: str, 
    confidence: float
) -> None:
    """Creates or updates MAPS_TO relationship between a LegacySKU and CanonicalMaterial."""
    ...

def find_inter_cpse_spares(canonical_id: str, exclude_cpse: str) -> list[DepotSpareInventory]:
    """Finds idle inventory for a canonical item across other sister CPSE depots."""
    ...

```

---

### Anticipated Clarifying Questions & Your Direct Answers

* **Q: "Why aren't we writing this in C++ like the original plan?"**
**A:** Profiling shows our dataset size for the live demo is under 50,000 SKUs. Doing this in pure Python using clean dictionary lookups and vectorization is fast (sub-millisecond execution per pair), eliminates compilation issues on teammates' laptops, and saves hours of integration headaches.
* **Q: "Where do I get the ASME standard specifications and metallurgy rules?"**
**A:** You do not need to model all 500 pages of ASME B16.5. Focus on the core hydrocarbon essentials:

1. Standard pressure classes: $150, 300, 600, 900, 1500, 2500$.

2. Standard Nominal Bore sizes: $15, 20, 25, 40, 50, 80, 100, 150, 200, 250, 300\text{ mm}$.
3. Common metallurgies: Carbon Steel (`A105`), Stainless (`SS304`, `SS316`), Low-temp CS (`A350 LF2`).

* **Q: "Where do I get the Neo4j initial data?"**
**A:** Shaurya is preparing the UNSPSC v26 and GeM hierarchy CSVs in `data/taxonomies/`. You will write a script (`seed_graph.py`) that loads those CSVs using Neo4j's `LOAD CSV` Cypher clause during setup.
