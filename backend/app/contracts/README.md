# Data Contracts & Schemas (`backend/app/contracts`)

## 1. Overview
The `contracts` directory contains all data schemas defined using **Pydantic v2**. 

In industrial procurement software, data contracts serve three essential purposes:
1. Runtime Validation: Reject invalid or corrupt inputs before they reach business logic.
2. Serialization & Deserialization: Convert between Python objects, JSON HTTP payloads, and database records.
3. System Safety: Ensure that critical engineering attributes (such as pressure rating, wall thickness, or metallurgical grade) are strictly typed and never accidentally set to invalid default values.

---

## 2. Directory Structure

```
backend/app/contracts/
|-- base.py                      # Common base models, pagination schemas, and mixins
|-- matching.py                  # Evaluation results, equivalence tiers, and violation details
|-- material.py                  # Extracted attributes, canonical catalog schemas, and enums
|-- requisition.py               # Transfer requisitions, gate passes, and inventory lock contracts
|-- taxonomy.py                  # UNSPSC v26 and Government e-Marketplace (GeM) mappings
`-- README.md                    # This file
```

---

## 3. Schema Reference

### A. Material Schemas (`material.py`)

#### `ItemType` (Enum)
Standardized catalog of mechanical, electrical, and structural component classes:
- `FLANGE_WELD_NECK`, `FLANGE_BLIND`, `FLANGE_SLIP_ON`
- `GATE_VALVE`, `BALL_VALVE`, `GLOBE_VALVE`, `CHECK_VALVE`, `BUTTERFLY_VALVE`, `PLUG_VALVE`
- `PIPE_SEAMLESS`, `ELBOW_BUTTWELD`, `SPIRAL_WOUND_GASKET`, `STUD_BOLT`
- `PUMP_CENTRIFUGAL`, `MECHANICAL_SEAL`, `BEARING_ROLLER`, `MOTOR_FLAMEPROOF`
- `CABLE_ARMOURED`, `ACTUATOR_PNEUMATIC`, `FERRULE_FITTING`

#### `FacingEnd` (Enum)
End connections and mating flange facing styles:
- `RF` (Raised Face): Standard serrated gasket mating surface.
- `RTJ` (Ring Type Joint): Metallic octagonal/oval ring groove for high-pressure service (> 600#).
- `FF` (Flat Face): Full-face flat surface used primarily with brittle cast iron components.
- `BW` (Butt Weld): Beveled ends for full-penetration pipeline welding.
- `SW` (Socket Weld): Socket recess for filleted piping joints.
- `THRD` (Threaded): NPT or BSP threaded connections.

#### `ExtractedMaterialAttributes` (BaseModel)
The central standardized engineering representation extracted from raw text:
- `item_type`: Normalized component classification string.
- `size_nb_mm`: Nominal bore in millimeters (e.g. `100.0` for 4-inch).
- `size_inch`: Imperial string representation (e.g. `4"`).
- `dn_code`: Metric diameter nominal string (e.g. `DN100`).
- `pressure_class`: Integer ASME pressure rating (`150`, `300`, `600`, `900`, `1500`, `2500`).
- `metallurgy`: Standardized ASTM alloy specification (e.g. `ASTM A105`, `ASTM A182 F316`).
- `facing_end`: Flange facing or valve end connection.
- `standard`: Governing standard (e.g. `ASME B16.5`, `API 600`, `ASME B16.20`).
- `schedule`: Pipe wall thickness (e.g. `SCH 40`, `SCH 80`, `STD`, `XS`, `XXS`).
- `is_sour_service`: Boolean flag indicating NACE MR0175 / ISO 15156 H2S compliance requirement.
- `is_ibr_certified`: Boolean flag indicating statutory Indian Boiler Regulations (IBR 1950) certification.
- `flange_series`: Large diameter designation (`SERIES_A` vs `SERIES_B` under ASME B16.47).
- `gasket_type` / `gasket_filler`: Spiral wound gasket profile and filler material (Graphite vs PTFE).
- `bolt_grade` / `nut_grade`: Fastener material specifications (ASTM A193 B7 vs ASTM A320 L7).
- `power_kw` / `speed_rpm` / `poles` / `hazardous_cert`: Rotating electrical motor attributes.
- `extraction_confidence`: Numerical score between 0.0 and 1.0 reflecting attribute completeness.

---

### B. Matching Schemas (`matching.py`)

#### `EquivalenceTier` (Enum)
- `TIER_1_IDENTICAL`: 100% specification parity across size, pressure, alloy, and connection. Drop-in replacement.
- `TIER_2_SUBSTITUTE`: Safe engineering upgrade meeting or exceeding specs. Requires human review.
- `TIER_3_INCOMPATIBLE`: Hard safety rejection due to an engineering violation.

#### `ToleranceViolation` (BaseModel)
Describes a specific safety rule failure:
- `rule_name`: Evaluated rule (e.g. `ASME Pressure Rating Invariant`, `ASTM Metallurgy Safety Rule`).
- `field`: The violated attribute name.
- `expected`: Source requirement value.
- `actual`: Candidate value found.
- `message`: Clear explanation of why the combination is unsafe.

#### `MatchEvaluationResult` (BaseModel)
The complete outcome returned by the tolerance engine:
- `tier`: Assigned EquivalenceTier.
- `is_compatible`: Boolean flag indicating whether the item can safely be deployed.
- `confidence_score`: Float between 0.0 and 1.0.
- `violations`: List of ToleranceViolation objects (empty for compatible matches).
- `parameter_checks`: Detailed list of `ParameterMatchDetail` objects showing status per attribute (`EXACT`, `UPGRADE`, `MISMATCH`).
- `rationale`: Human-readable engineering justification.
- `requires_hitl`: True if human approval is recommended.
- `candidate_canonical_id` / `canonical_id`: Unique identifier of the evaluated candidate SKU.

---

### C. Requisition Schemas (`requisition.py`)
- `TransferRequisitionRequest`: Input payload for creating a cross-CPSE transfer.
- `TransferRequisitionResponse`: Requisition details including calculated GIS road distance and freight.
- `InventoryLock`: Tracks depot inventory reservation locks to prevent double allocation.
- `GatePassDetails`: Printable CISF Digital Gate Pass details with verification hash and SVG QR code.
