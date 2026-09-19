# Samanvay-AI Deterministic Engineering Safety Core (`rules/`)

The **Engineering Safety Core** is the deterministic validation engine of **Samanvay-AI**. While machine learning models (DeBERTa-v3 NER, BGE-M3 Dense Embeddings, and Cross-Encoder Rerankers) excel at semantic discovery across messy, non-standardized CPSE ERP catalogs, **AI cannot be trusted alone to sign off on high-pressure hydrocarbon piping or refinery safety systems**.

A single mismatched flange rating, an incompatible valve trim in sour gas service, or an improper metallurgical substitution can trigger catastrophic piping rupture, toxic H2S release, or refinery explosions.

The `rules/` module serves as the **Zero-Tolerance Safety Gatekeeper**:
- It evaluates every candidate material match discovered by vector search and reranking against **21 codified mechanical, metallurgical, and process engineering standards**.
- It outputs a deterministic **Compatibility Tier** (`Tier 1: Identical`, `Tier 2: Upgraded/Direct Substitute`, `Tier 3: Conditional/Requires Review`, `Tier 4: Incompatible/Hard Reject`).
- It produces human-readable, auditable engineering explanations detailing exact reasons for rejections, caveats, or acceptance.

---

## 1. Architectural Role in Samanvay-AI

```
                                [ Requisition Query ]
                                          │
                                          ▼
                       [ Hybrid Semantic & Vector Search ]
                             (Qdrant 1024-dim BGE-M3)
                                          │
                                          ▼
                             [ Cross-Encoder Reranker ]
                                (Top-K Candidates)
                                          │
                                          ▼
                   ┌──────────────────────────────────────────────┐
                   │       DETERMINISTIC SAFETY ENGINE (rules/)   │
                   │  rules.tolerance.evaluate_material_compat    │
                   └──────────────────────┬───────────────────────┘
                                          │
             ┌────────────────────────────┼────────────────────────────┐
             ▼                            ▼                            ▼
      [ ASME Rules ]               [ ASTM Rules ]              [ Valves / Rotating ]
   • ASME B16.5 (Class)         • ASTM A105 / A182 / A216     • API 6D (Bore)
   • ASME B16.9 (Fittings)      • ASTM A193/A194 (Fasteners)  • API 607 (Fire Safe)
   • ASME B16.20 (Gaskets)      • Metallurgy Directed Graph   • API 610 (Pumps)
   • ASME B16.48 (Blinds)       • Low Temp / Cryogenic Limits • API 682 (Seals)
             └────────────────────────────┬────────────────────────────┘
                                          │
                                          ▼
                       [ Categorized Compatibility Tier ]
                                 (Tier 1 to 4)
                                          │
                                          ▼
                       [ Sovereign SHA-256 Audit Ledger ]
```

---

## 2. Directory Structure & Sub-Rule Taxonomy

```
rules/
├── __init__.py               # Exposes evaluate_material_compatibility and core types
├── tolerance.py              # Central orchestrator integrating all 21 modular sub-rules
├── asme/                     # American Society of Mechanical Engineers standards
│   ├── facings.py            # Flange facing compatibility (RF, FF, RTJ)
│   ├── fittings.py           # Forged & buttweld fittings ratings (ASME B16.11 / B16.9)
│   ├── flange_insulation.py  # Dielectric insulation kits for cathodic protection
│   ├── gaskets.py            # Gasket types, seating stress, ASME B16.20/B16.21 limits
│   ├── large_flanges.py      # ASME B16.47 Series A vs Series B compatibility
│   ├── line_blinds.py        # ASME B16.48 spectacle blinds & spacers
│   └── pressure_class.py     # ASME B16.5 rating classes (150# to 2500#) & PN ratings
├── astm/                     # American Society for Testing and Materials standards
│   ├── fasteners.py          # Stud bolts & nuts (ASTM A193/A194/A320)
│   └── metallurgy_dag.py     # Directed Acyclic Graph of metallurgical substitutions
├── equipment/                # Process Equipment Standards
│   ├── heat_exchangers.py    # TEMA standards, tube gauges (BWG), impingement plates
│   ├── strainers_traps.py    # Y/T/Basket strainers, steam traps differential pressure
│   ├── tank_safety.py        # API 650/620 tank vents, flame arresters, coating specs
│   └── thermal_insulation.py # Hot/cold insulation, CUI (Corrosion Under Insulation)
├── piping/                   # Piping & Pipeline Standards
│   ├── expansion_joints.py   # Bellows, metallic/elastomeric expansion joints
│   ├── line_pipe.py          # API 5L line pipe (PSL 1 vs PSL 2, Charpy V-notch)
│   ├── nace.py               # NACE MR0175 / ISO 15156 sour service compliance
│   ├── schedules.py          # ASME B36.10M / B36.19M pipe schedules & wall thicknesses
│   └── tubing.py             # Instrumentation tubing hardness (<80 HRB) & ferrules
├── rotating/                 # Rotating Machinery Standards
│   ├── bearings.py           # ISO 281 bearing L10h rating life, clearance classes
│   ├── compressors.py        # API 617 / API 618 / API 619 process gas compressors
│   ├── motors.py             # IEC 60034 / NEMA MG-1 motors, Ex d flameproof enclosures
│   ├── pumps.py              # API 610 centrifugal pumps, NPSHa vs NPSHr margin
│   └── seals.py              # API 682 mechanical seal arrangements & flush plans
└── valves/                   # Valve Specifications
    ├── bore.py               # API 6D Full Bore (FB) vs Reduced Bore (RB), piggability
    ├── fire_safe.py          # API 607 / API 6FA / ISO 10497 fire safe certifications
    ├── psv.py                # API 520/526 pressure safety relief valve sizing & orifices
    ├── rupture_disks.py      # ASME Sec VIII / ISO 4126 burst pressure tolerances
    └── trim.py               # API 600/602 trim numbers (Trim 1 to Trim 17)
```

---

## 3. Core Engine: `tolerance.py`

### Key Function: `evaluate_material_compatibility(query, candidate)`
This function is the heart of the safety evaluation. It receives two objects or dictionaries (the requisition requirement `query` and the inventory item `candidate`) containing extracted physical attributes:

#### Inputs:
- `query`: `Dict[str, Any]` or `PhysicalAttributes` schema instance containing:
  - `item_type`, `size`, `pressure_class`, `material_grade`, `schedule`, `facing`, `trim`, `design_temp_c`, `design_pressure_bar`, `nace_compliant`, etc.
- `candidate`: `Dict[str, Any]` or `PhysicalAttributes` representing the warehouse stock item.

#### Outputs:
Returns a `CompatibilityEvaluation` object containing:
- `tier`: `DynamicCompatibilityTier` (`TIER_1_EXACT`, `TIER_2_SUPERSET`, `TIER_3_FUNCTIONAL_EQUIVALENT`, `TIER_4_INCOMPATIBLE`).
- `is_compatible`: Boolean (`True` if Tier 1, 2, or 3; `False` if Tier 4).
- `overall_score`: Float between `0.0` and `1.0`.
- `violations`: `List[str]` of hard safety failures (e.g. `"PRESSURE_RATING_TOO_LOW"`, `"NACE_SOUR_VIOLATION"`).
- `warnings`: `List[str]` of operational caveats (e.g. `"UPGRADED_METALLURGY_COST_PREMIUM"`, `"DIMENSIONAL_SCHEDULE_HEAVIER"`).
- `sub_rule_results`: Dictionary of individual checks across all 21 standards.

### Evaluation Workflow in `tolerance.py`:
1. **Item Type Consistency:** Prevents comparing incompatible categories (e.g. gate valve vs centrifugal pump).
2. **Nominal Size Matching:** Enforces dimensional outer diameter (OD) and bore compatibility.
3. **Pressure Class Verification (`asme/pressure_class.py`):** Candidate must meet or exceed query pressure class at design temperature.
4. **Metallurgical DAG Traversal (`astm/metallurgy_dag.py`):** Checks alloy compatibility (e.g. 316L SS can safely replace 304 SS, but Carbon Steel cannot replace Stainless Steel in acid service).
5. **NACE MR0175 Sour Service Gatekeeper (`piping/nace.py`):** If sour service is required, non-NACE materials are rejected unconditionally.
6. **Sub-rule Delegation:** Dynamically routes attributes to equipment-specific modules (valves, pumps, compressors, gaskets, etc.).
7. **Tier Aggregation:** If any sub-rule returns a hard rejection (`TIER_4_INCOMPATIBLE`), the overall evaluation immediately falls to Tier 4.

---

## 4. Tech Stack & Dependencies

| Tool / Library | Version / Spec | Purpose |
|---|---|---|
| **Python** | `3.11+` | Core programming language |
| **Pydantic v2** | `^2.6.0` | Strict data validation, schema enforcement, type coercion |
| **NetworkX** | `^3.2` | Directed Acyclic Graph (DAG) construction and topological traversal for metallurgy |
| **PyTest** | `^8.0` | Unit test execution with 100+ parametric test cases |

---

## 5. Theoretical Concepts & Engineering Standards for Juniors

To master and contribute to this module, junior engineers and developers should study:

### 1. Mechanical Piping & Flange Design:
- **ASME B16.5 & B16.47:** Understand flange ratings (150# to 2500#). Learn why pressure ratings decrease as temperature increases due to material creep and yield strength reduction.
- **ASME B36.10M & B36.19M:** Understand nominal pipe size (NPS) vs outer diameter (OD) and how pipe schedule determines wall thickness.
- **Gasket Dynamics (ASME B16.20):** Seating factor ($m$) and minimum design seating stress ($y$). Why spiral wound gaskets require inner rings on Class 900+ flanges.

### 2. Metallurgy & Materials Science:
- **ASTM Standards:** A105 (forgings), A106 (seamless CS pipe), A216 WCB/WCC (castings), A350 LF2 (low temp), A182 (alloy/SS forgings), A312 (austenitic pipe).
- **Directed Acyclic Graphs (DAGs):** How mathematical lattices model partial ordering in material substitutability (e.g., Duplex 2205 $\succ$ 316L $\succ$ 304).
- **NACE MR0175 / ISO 15156:** Sulfide Stress Cracking (SSC), Hydrogen-Induced Cracking (HIC), and strict hardness limits (maximum 22 HRC).

### 3. Rotating & Pressure Equipment:
- **API 610 (Centrifugal Pumps):** NPSHa (Available) vs NPSHr (Required) cavitation margins; Best Efficiency Point (BEP).
- **API 682 (Mechanical Seals):** Seal arrangements (Single, Dual Unpressurized, Dual Pressurized) and API flush plans.
- **API 6D & API 600:** Pipeline valves, full bore piggability, and standard trim metallurgy numbers.

---

## 6. Practical Code Usage

```python
from rules.tolerance import evaluate_material_compatibility

# Requirement from IOCL Refinery
query_spec = {
    "item_type": "GATE_VALVE",
    "size": "4 INCH",
    "pressure_class": 300,
    "material_grade": "ASTM A216 WCB",
    "facing": "RF",
    "trim": "TRIM 8",
    "nace_compliant": True
}

# Candidate stock found at ONGC Hazira Plant
candidate_spec = {
    "item_type": "GATE_VALVE",
    "size": "4 INCH",
    "pressure_class": 600,            # Higher pressure rating (Safe upgrade)
    "material_grade": "ASTM A350 LF2", # Low-temp carbon steel (Superior impact toughness)
    "facing": "RF",
    "trim": "TRIM 8",
    "nace_compliant": True
}

# Run deterministic evaluation
result = evaluate_material_compatibility(query_spec, candidate_spec)

print(f"Compatibility Tier: {result.tier}")
print(f"Is Safe to Substitute: {result.is_compatible}")
print(f"Overall Score: {result.overall_score}")
print(f"Engineering Caveats: {result.warnings}")
```

---

## 7. How to Test

Run the comprehensive unit test suite covering all 21 standards:

```bash
# Run all tolerance and engineering rules tests
pytest tests/unit/test_tolerance.py -v

# Run with coverage report
pytest tests/unit/test_tolerance.py --cov=rules --cov-report=term-missing
```

---

## 8. Contribution Guide: Adding a New Engineering Rule

1. **Create the Sub-rule Module:** Add your rule in the relevant sub-package (e.g. `rules/valves/control_valves.py`).
2. **Define Pure Functions:** The rule must be a deterministic pure function returning a boolean, a score, and a list of violations/warnings.
3. **Register in `rules/tolerance.py`:** Import your check function into `evaluate_material_compatibility` and map it to the relevant `item_type`.
4. **Write Unit Tests:** Add parameterized test cases in `tests/unit/test_tolerance.py` testing exact match, valid superset, valid conditional, and dangerous incompatibility cases.
