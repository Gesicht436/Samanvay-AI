# Pydantic Schemas & DTO Contracts (`backend/app/schemas/`)

This directory houses the **Pydantic v2** data transfer objects (DTOs), request payload validators, response serializers, and enum taxonomies governing **Samanvay-AI**.

All schemas enforce strict type validation, attribute-level privacy masking, and graceful degradation handling across the platform.

---

## 1. Schema-by-Schema Breakdown

### A. [`auth.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/schemas/auth.py) — Authentication & RBAC Contracts
Defines identity models, login/signup contracts, and the 25 pre-configured demo persona accounts federating the 7 CPSEs:

- **Enums & Models:**
  - `UserRole(str, Enum)`: Sovereign functional roles:
    - `SITE_ENGINEER`: Plant maintenance engineer (submits emergency requisitions).
    - `MATERIALS_MANAGER`: Warehouse superintendent (approves surplus release from their depot).
    - `TECHNICAL_AUTHORITY`: Chief metallurgist / QA lead (resolves HITL borderline triage).
    - `CISF_SECURITY`: Central Industrial Security Force officer (issues gate passes, inspects seals).
    - `VIGILANCE_AUDITOR`: CVC officer / CAG auditor (inspects SHA-256 ledger integrity).
    - `SUPER_ADMIN`: Ministry system administrator (governs users, system configuration).
  - `UserLogin`: Credentials model (`username`, `password`).
  - `UserSignup`: Registration model (`username`, `password`, `full_name`, `email`, `role`, `cpse`, `depot_id`).
  - `UserResponse`: Clean profile representation with `is_active` and `is_approved` flags (`from_attributes = True`).
  - `Token`: JWT payload wrapper (`access_token`, `token_type = "bearer"`, `user: UserResponse`).
  - `TokenPayload`: Decoded JWT token claims (`sub`, `role`, `cpse`, `depot_id`, `exp`).
  - `SeedUserInfo`: Structured container for pre-seeded test accounts.

- **Pre-Configured Demo Accounts (25 Personas):**
  - **OIL (Duliajan, Assam):** `engineer_oil`, `stores_oil`, `cisf_oil`, `tech_authority`, `cisf_officer`
  - **IOCL (Panipat, Haryana):** `engineer_iocl`, `stores_iocl`, `cisf_iocl`
  - **ONGC (Uran, Maharashtra):** `engineer_ongc`, `stores_ongc`, `cisf_ongc`
  - **GAIL (Pata, Uttar Pradesh):** `engineer_gail`, `stores_gail`, `cisf_gail`
  - **BPCL (Mumbai Mahul):** `engineer_bpcl`, `stores_bpcl`, `cisf_bpcl`
  - **HPCL (Visakh Refinery, AP):** `engineer_hpcl`, `stores_hpcl`, `cisf_hpcl`
  - **NRL (Numaligarh, Assam):** `engineer_nrl`, `stores_nrl`, `cisf_nrl`
  - **MoPNG Central:** `auditor` (CVO/CAG Auditor), `admin` (Ministry Super Admin)
  - **Default Master Password:** `Samanvay@2026`

---

### B. [`material.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/schemas/material.py) — Dynamic Compatibility & Engineering Evaluation
Codifies dynamic compatibility scoring, multi-property discovery parameters, and deterministic safety violations:

- **Enums & Core Classes:**
  - `DynamicCompatibilityTier(str, Enum)`:
    - `TIER_1_IDENTICAL`: $\ge 95\%$ match, identical nominal bore, pressure rating, and metallurgy.
    - `TIER_2_SUBSTITUTE`: $80\% - 94\%$, certified engineering upgrade (e.g. A350 LF2 replacing A105, or Class 600 replacing Class 300). Requires HITL confirmation.
    - `TIER_3_INCOMPATIBLE`: $< 80\%$ continuous score OR **any zero-tolerance safety gate violation**.
    - *Invariant #1:* Tiers are **never stored statically** on inventory items — they are dynamically computed for each unique Query-Candidate pair $S(Q, C)$.
  - `ExtractedMaterialAttributes`:
    - Handles physical specifications: `item_type`, `size_nb_mm`, `pressure_class`, `pressure_rating_bar`, `pressure_rating_psi`, `schedule`, `metallurgy`, `facing_end`, `standard`, `indian_standard` (IS 14846, IS 1239, IS 2062), `oil_std_spec`, `oil_material_code` (MESC), `gem_category_id`, `cppp_tender_ref`, `make_in_india_class`, `local_content_percentage`.
    - **Graceful Degradation Flags:** On stained or degraded scans, fields default to `None` with `is_incomplete = True`, `missing_attributes = [...]`, and `requires_hitl = True` rather than raising uncaught runtime exceptions.
  - **Multi-Property Engineering Parameters:**
    - `weldability_class`: Evaluated via the IIW Carbon Equivalent equation:
      $$CE = C + \frac{Mn}{6} + \frac{Cr + Mo + V}{5} + \frac{Ni + Cu}{15}$$
      High weldability requires $CE \le 0.40$; standard carbon steel ceiling is $CE \le 0.43$.
    - `sour_service`: Enforces NACE MR0175 / ISO 15156 maximum hardness $\le 22\text{ HRC}$ and certified SSC/HIC resistance.
    - `facing_end`: Flange end geometries (RF, RTJ, FF).
    - `trim_no`: API valve trim ladders (Trim 1, 5, 8, 12).
    - `severe_cyclic`: ASME B31.3 Chapter IX cyclic duty constraints.
  - `RuleViolation`:
    - Detailed container for engineering violations: `module_name`, `standard_code`, `failure_mode_prevented`, and `explanation`.
  - `CompatibilityResult` (aliased to `ToleranceResult`):
    - Full evaluation payload containing `is_compatible`, `score`, `compatibility_tier`, `explanation`, `rule_violations`, and `property_scorecard`.

---

### C. [`inventory.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/schemas/inventory.py) — Catalog Views & Attribute-Level Privacy
Enforces public vs. private data representations to protect sensitive commercial acquisition prices across CPSEs:

- **Enums & Classes:**
  - `InventoryStatus(str, Enum)`:
    - `TO_BE_CONSUMED`: Active operational stock reserved for ongoing maintenance.
    - `IN_STORAGE`: Healthy spares held in standard storage.
    - `IDLE_SURPLUS`: Identified surplus available for cross-CPSE mutual aid transfer.
    - `RESERVED_TRANSFER`: Locked under an active inter-CPSE requisition.
    - `CONSUMED`: Physically issued and debited from inventory.
  - `InventoryItemResponse`:
    - **Public CPSE View:** Shared across enterprises. Strictly omits `unit_cost_inr`, `total_value_inr`, and `po_no` when viewed by a sister enterprise, preventing commercial exposure.
  - `InventoryItemPrivateResponse`:
    - **Owning CPSE Internal View:** Extends `InventoryItemResponse` with confidential financial accounting values (`unit_cost_inr`, `total_value_inr`, `po_no`, `heat_no`, `source_document_id`).
  - `InventoryCreateRequest`:
    - Strict schema validating new catalog records from ERP bulk sync or manual creation.

---

### D. [`requisition.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/schemas/requisition.py) — Requisitions & CISF Gate Passes
Contracts governing inter-enterprise transfers, priority tiers, and digital security gate passes:

- **Enums & Classes:**
  - `UrgencyLevel(str, Enum)`:
    - `EMERGENCY_SHUTDOWN`: Critical plant stoppage (immediate expedited dispatch).
    - `PLANNED_MAINTENANCE`: Scheduled turnaround or overhaul.
    - `ROUTINE`: Regular operational restocking.
  - `RequisitionStatus(str, Enum)`:
    - `PENDING_APPROVAL`: Created by engineer; awaiting supplying CPSE approval.
    - `APPROVED_FOR_DISPATCH`: Authorized by supplying Materials Manager.
    - `IN_TRANSIT`: Dispatched from warehouse; physical freight on road.
    - `DELIVERED`: Received and confirmed at destination plant.
    - `REJECTED`: Cancelled by requester or declined by supplier.
  - `RequisitionCreateRequest`: Validates `sku_code`, `required_qty > 0`, `source_unit`, `justification`, and `urgency_level`.
  - `RequisitionResponse`: Serialized requisition order with timestamps, audit hash, and linked CISF gate pass.
  - `RequisitionApprovalRequest` & `RequisitionRejectionRequest`: Payload models for SoD actions.
  - `GatePassCreateRequest`: Input payload for CISF security personnel (`transporter_name`, `vehicle_no`, `driver_name`, `driver_id_no`, `gst_eway_bill_no`, `issuing_officer`).
  - `GatePassResponse`: Complete gate pass document embedding `sha256_hash`, `transit_distance_km`, `co2_saved_kg`, `estimated_transit_hours`, and `qr_code_svg`.

---

### E. [`audit.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/schemas/audit.py) — Sovereign Audit Ledger Contracts
Defines serialization models and verification report schemas for statutory compliance:

- **Enums & Classes:**
  - `AuditActionCategory(str, Enum)`:
    - `INWARD_PROCUREMENT`: New material receipt and MTC verification.
    - `LIFECYCLE_TRANSITION`: State change (e.g. declared surplus).
    - `REQUISITION_INITIATED`: New transfer request created.
    - `SUPPLY_CONFIRMED`: Authorized by supplying CPSE.
    - `GATE_PASS_ISSUED`: Digital gate pass generated by CISF.
    - `DELIVERY_VERIFIED`: In-gate arrival confirmed and lock released.
    - `HITL_DECISION`: Human authority manual override.
    - `ACTIVE_LEARNING_FEEDBACK`: Engineer classification feedback.
  - `AuditLogEntry`: Pydantic representation of an individual immutable audit block including `prev_hash` and `sha256_hash`.
  - `AuditVerificationResponse`:
    - Structured verification report returned by `/api/v1/audit/verify` (`is_valid: bool`, `total_entries: int`, `entries_verified: int`, `first_broken_index: Optional[int]`, `message: str`).
  - `ActiveLearningFeedback`: Payload for submitting engineer triage decisions on borderline items.

---

## 2. Usage Examples

### Validating Requisition Payload with Pydantic v2:
```python
from backend.app.schemas.requisition import RequisitionCreateRequest, UrgencyLevel

payload = {
    "sku_code": "OIL-VLV-100",
    "required_qty": 2,
    "source_unit": "Crude Distillation Unit (CDU-1)",
    "justification": "Emergency replacement for leaking gate valve on sour crude line",
    "urgency_level": "EMERGENCY_SHUTDOWN",
    "requested_by": "engineer_oil",
}

# Strict validation
req = RequisitionCreateRequest(**payload)
assert req.urgency_level == UrgencyLevel.EMERGENCY_SHUTDOWN
assert req.required_qty == 2
```

### Validating Extracted Attributes with Graceful Degradation:
```python
from backend.app.schemas.material import ExtractedMaterialAttributes

# Ingesting degraded scan with missing pressure class
attrs = ExtractedMaterialAttributes(
    item_type="GATE_VALVE",
    size_nb_mm=100.0,
    pressure_class=None,
    metallurgy="ASTM A216 WCB",
    is_incomplete=True,
    missing_attributes=["pressure_class"],
    confidence_score=0.62,
    requires_hitl=True,
)

assert attrs.requires_hitl is True
assert "pressure_class" in attrs.missing_attributes
```
