"""
Samanvay Canonical Material Schema (SCMS-27).

Defines the enterprise canonical schema, column aliases, normalization rules,
and Pydantic v2 data contracts for cross-CPSE material master catalogs,
inter-depot requisitions, and inventory data pipelines.
"""

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Canonical 27 Columns Specification (SCMS-27)
# ---------------------------------------------------------------------------
CANONICAL_COLUMNS: list[str] = [
    # Tier 1: Identity & Multi-Tenant Partitioning (5)
    "sku_code",
    "canonical_id",
    "cpse",
    "depot_id",
    "depot_location",
    # Tier 2: Physical & Engineering Specifications (8)
    "item_type",
    "description",
    "size_nb_mm",
    "pressure_class",
    "pressure_rating_bar",
    "metallurgy",
    "facing_end",
    "schedule",
    # Tier 3: Standards, Compliance & National Mandates (5)
    "standard",
    "indian_standard",
    "oil_std_spec",
    "make_in_india_class",
    "local_content_percentage",
    # Tier 4: Public Procurement & Catalog Mapping (4)
    "oil_material_code",
    "gem_category_id",
    "cppp_tender_ref",
    "po_no",
    # Tier 5: Inventory, Valuation & Lifecycle (5)
    "quantity",
    "unit_cost_inr",
    "status",
    "days_idle",
    "is_broadcasted_surplus",
]

# Primary identifier and tenant columns required for valid inventory items
MANDATORY_COLUMNS: list[str] = [
    "sku_code",
    "cpse",
    "depot_location",
    "description",
    "quantity",
    "unit_cost_inr",
]

# ---------------------------------------------------------------------------
# Comprehensive Dialect & Legacy Column Aliases
# ---------------------------------------------------------------------------
COLUMN_ALIASES: dict[str, str] = {
    # CPSE / Enterprise identifiers
    "cpse_name": "cpse",
    "organization": "cpse",
    "company": "cpse",
    "enterprise": "cpse",
    "psu": "cpse",
    # Material descriptions
    "raw_description": "description",
    "item_description": "description",
    "material_description": "description",
    "canonical_description": "description",
    "material_desc": "description",
    "item_name": "description",
    # SKU / Part codes
    "local_code": "sku_code",
    "material_code": "sku_code",
    "item_code": "sku_code",
    "part_number": "sku_code",
    "part_no": "sku_code",
    # Nominal Bore / Sizing
    "nominal_bore_mm": "size_nb_mm",
    "size_mm": "size_nb_mm",
    "nb_mm": "size_nb_mm",
    "size_nb": "size_nb_mm",
    "extracted_size_nb_mm": "size_nb_mm",
    # Item type & classifications
    "extracted_item_type": "item_type",
    "material_type": "item_type",
    "equipment_type": "item_type",
    # Pressure ratings
    "extracted_pressure_class": "pressure_class",
    "rating_class": "pressure_class",
    "class": "pressure_class",
    "rating_bar": "pressure_rating_bar",
    "pn_bar": "pressure_rating_bar",
    # Metallurgy & materials
    "extracted_metallurgy": "metallurgy",
    "material_grade": "metallurgy",
    "material": "metallurgy",
    "grade": "metallurgy",
    # Facing / End connections
    "extracted_facing": "facing_end",
    "facing": "facing_end",
    "end_connection": "facing_end",
    # Engineering standards
    "extracted_standard": "standard",
    "std": "standard",
    "design_standard": "standard",
    # Aging & idle metrics
    "idle_days": "days_idle",
    "aging_days": "days_idle",
    # Public procurement identifiers
    "mesc_code": "oil_material_code",
    "sap_material_code": "oil_material_code",
    "gem_category": "gem_category_id",
    "gem_cat": "gem_category_id",
    "cppp_tender_id": "cppp_tender_ref",
    "tender_ref": "cppp_tender_ref",
    "tender_id": "cppp_tender_ref",
    # Surplus flags
    "is_surplus": "is_broadcasted_surplus",
    "surplus": "is_broadcasted_surplus",
    "surplus_flag": "is_broadcasted_surplus",
}


def normalize_catalog_row(raw_row: dict[str, Any]) -> dict[str, Any]:
    """
    Normalizes arbitrary CPSE / vendor catalog rows into the Canonical Material Schema (SCMS-27).
    Maps legacy headers and dialect-specific column variations to standard canonical names,
    while retaining unmapped fields inside properties.
    """
    normalized: dict[str, Any] = {}
    properties: dict[str, Any] = {}

    for key, val in raw_row.items():
        if val is None or (isinstance(val, float) and str(val) == "nan"):
            continue

        clean_key = str(key).strip().lower()
        mapped_key = COLUMN_ALIASES.get(clean_key, clean_key)

        if mapped_key in CANONICAL_COLUMNS:
            normalized[mapped_key] = val
        elif mapped_key in (
            "heat_no",
            "gem_product_id",
            "pressure_rating_psi",
            "location_state",
            "hsn_code",
            "unspsc_code",
        ):
            # Known supplementary catalog fields
            normalized[mapped_key] = val
        else:
            properties[clean_key] = val

    # Preserve any incoming properties dict
    if "properties" in raw_row and isinstance(raw_row["properties"], dict):
        properties.update(raw_row["properties"])

    if properties:
        normalized["properties"] = properties

    # CPSE normalization: uppercase string
    if "cpse" in normalized and normalized["cpse"]:
        normalized["cpse"] = str(normalized["cpse"]).strip().upper()

    # Derived depot_id if missing
    if "depot_id" not in normalized or not normalized["depot_id"]:
        cpse_str = normalized.get("cpse", "CPSE")
        loc_str = normalized.get("depot_location", "CENTRAL")
        loc_prefix = str(loc_str).split(",")[0].strip().replace(" ", "_").upper()
        normalized["depot_id"] = f"{cpse_str}_{loc_prefix}"

    # Default lifecycle status based on idle days if missing
    if "status" not in normalized or not normalized["status"]:
        days = int(normalized.get("days_idle", 0) or 0)
        if days >= 365:
            normalized["status"] = "SURPLUS_DECLARED"
            normalized["is_broadcasted_surplus"] = True
        elif days >= 180:
            normalized["status"] = "POTENTIAL_SURPLUS"
            normalized["is_broadcasted_surplus"] = True
        else:
            normalized["status"] = "TO_BE_CONSUMED"
            if "is_broadcasted_surplus" not in normalized:
                normalized["is_broadcasted_surplus"] = False

    return normalized


# ---------------------------------------------------------------------------
# Pydantic v2 Canonical Material Contract
# ---------------------------------------------------------------------------
class CanonicalMaterialItem(BaseModel):
    """
    Strongly-typed Pydantic v2 contract for Canonical Material Schema (SCMS-27).
    Enforces validation, typing, and safety defaults across API schemas,
    ingestion pipelines, and background sync workers.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Tier 1: Identity & Multi-Tenant Partitioning
    sku_code: str = Field(..., description="Unique CPSE SKU / Local Material Code")
    canonical_id: Optional[str] = Field(None, description="Normalized canonical identifier (e.g. CAN-000590)")
    cpse: str = Field(..., description="CPSE identifier (e.g. IOCL, ONGC, BPCL, HPCL, GAIL, OIL, NRL)")
    depot_id: str = Field(..., description="Internal depot / warehouse code")
    depot_location: str = Field(..., description="Physical location name and address")

    # Tier 2: Physical & Engineering Specifications
    item_type: str = Field(default="EQUIPMENT", description="Canonical item classification (e.g. FLANGE, VALVE_BALL)")
    description: str = Field(..., description="Complete engineering item description")
    size_nb_mm: Optional[float] = Field(None, description="Nominal bore in millimeters")
    pressure_class: Optional[int] = Field(None, description="ASME pressure class rating (e.g. 150, 300, 600)")
    pressure_rating_bar: Optional[float] = Field(None, description="PN rating in Bar")
    metallurgy: Optional[str] = Field(None, description="ASTM / AISI metallurgical grade")
    facing_end: Optional[str] = Field(None, description="Flange facing or pipe end connection (e.g. RF, RTJ, BW)")
    schedule: Optional[str] = Field(None, description="Pipe / fitting schedule (e.g. SCH 40, SCH 80)")

    # Tier 3: Standards, Compliance & National Mandates
    standard: Optional[str] = Field(None, description="International engineering standard (e.g. ASME B16.5)")
    indian_standard: Optional[str] = Field(None, description="Bureau of Indian Standards specification (e.g. IS 1367)")
    oil_std_spec: Optional[str] = Field(None, description="OISD or EIL specification")
    make_in_india_class: Optional[str] = Field(default="Class-I", description="Make-in-India preference class")
    local_content_percentage: Optional[float] = Field(default=75.0, description="Indigenous local content percentage")

    # Tier 4: Public Procurement & Catalog Mapping
    oil_material_code: Optional[str] = Field(None, description="8-digit MESC or SAP material code")
    gem_category_id: Optional[str] = Field(None, description="GeM portal product category identifier")
    cppp_tender_ref: Optional[str] = Field(None, description="CPPP tender reference number")
    po_no: Optional[str] = Field(None, description="Purchase order reference")

    # Tier 5: Inventory, Valuation & Lifecycle
    quantity: int = Field(..., ge=0, description="Current stock level in units")
    unit_cost_inr: float = Field(..., ge=0.0, description="Unit acquisition cost in INR")
    status: str = Field(default="TO_BE_CONSUMED", description="Material lifecycle status")
    days_idle: int = Field(default=0, ge=0, description="Continuous idle days in warehouse")
    is_broadcasted_surplus: bool = Field(default=False, description="Flag indicating surplus broadcast on exchange")

    # Tier 6: Supplementary / Extensible Attributes
    heat_no: Optional[str] = Field(None, description="Material Test Certificate heat number")
    gem_product_id: Optional[str] = Field(None, description="GeM unique catalog product identifier")
    pressure_rating_psi: Optional[float] = Field(None, description="Pressure rating in PSI")
    location_state: Optional[str] = Field(None, description="Depot state / province")
    properties: dict[str, Any] = Field(default_factory=dict, description="Extensible equipment-specific key-value metadata")

    @field_validator("cpse")
    @classmethod
    def validate_cpse(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean:
            raise ValueError("CPSE identifier cannot be empty")
        return clean

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v

    @field_validator("unit_cost_inr")
    @classmethod
    def validate_unit_cost(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError("Unit cost cannot be negative")
        return v
