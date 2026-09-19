# Pydantic Schemas & DTO Contracts (`backend/app/schemas/`)

This directory contains the **Pydantic v2** models defining input validation schemas, output serialization models, and enum taxonomies.

---

## 1. File-by-File Breakdown

### `material.py` — Physical Specifications & Compatibility Tiers
- **Purpose:** Core schemas for engineering attributes and matching results.
- **Key Enums & Classes:**
  - `DynamicCompatibilityTier(str, Enum)`:
    - `TIER_1_EXACT`: Exact dimensional, metallurgical, and rating identity.
    - `TIER_2_SUPERSET`: Certified engineering upgrade (e.g. Class 600 replacing Class 300; A350 LF2 replacing A105).
    - `TIER_3_FUNCTIONAL_EQUIVALENT`: Acceptable substitute with operational caveat (e.g. heavier pipe schedule reducing flow area).
    - `TIER_4_INCOMPATIBLE`: Hard engineering rejection (e.g. non-NACE pipe in sour service; RF flange bolted to brittle cast iron FF).
  - `PhysicalAttributes`: Validated extraction container (item type, size, class, material grade, schedule, facing, trim, NACE compliance).
  - `MaterialMatchResult`: Comprehensive match payload containing candidate SKU, tier, match score, radar subvector similarities, violations, and logistics.

### `inventory.py` — Inventory Input & Response Contracts
- **Purpose:** Public vs private inventory representations.
- **Key Classes:**
  - `InventoryStatus(str, Enum)`: `AVAILABLE`, `RESERVED`, `DISPATCHED`, `SCRAPPED`.
  - `InventoryItemResponse`: Public data transfer object shared across CPSEs (strips sensitive acquisition costs).
  - `InventoryItemPrivateResponse`: Extended object visible only to owning CPSE administrators (includes financial ledger cost).

### `requisition.py` — Requisition Request & Response Models
- **Purpose:** Validation contracts for order lifecycle operations.
- **Key Classes:**
  - `UrgencyLevel(str, Enum)`: `ROUTINE`, `URGENT`, `EMERGENCY_SHUTDOWN`.
  - `RequisitionStatus(str, Enum)`: `PENDING`, `MATCHED`, `APPROVED`, `DISPATCHED`, `COMPLETED`, `CANCELLED`.
  - `RequisitionCreateRequest`: Validates mandatory fields and quantities.
  - `RequisitionResponse`: Detailed requisition record with transit progress and gate pass seal.

### `audit.py` — Audit Logging Contracts
- **Purpose:** Audit ledger serialization models.
- **Key Classes:**
  - `AuditActionCategory(str, Enum)`: `MATCH_SEARCH`, `INVENTORY_LOCK`, `REQUISITION_DISPATCH`, etc.
  - `AuditLogEntry`: Serialized audit block with cryptographic hashes.
  - `AuditChainVerificationResponse`: Cryptographic audit verification report (`is_tamper_free`, `verified_blocks`, `tampered_blocks`).

---

## 2. Code Example

```python
from backend.app.schemas.material import PhysicalAttributes, DynamicCompatibilityTier

attrs = PhysicalAttributes(
    item_type="GATE_VALVE",
    size="4 INCH",
    pressure_class=300,
    material_grade="ASTM A216 WCB",
    nace_compliant=True
)
print("Validated:", attrs.model_dump())
```
