"""
Pydantic v2 Contracts for Central Inventory Management & Lifecycle Transitions.
Defines statuses for procurement intake, planned maintenance allocation,
idle surplus broadcasting, and inter-CPSE discovery.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class InventoryItemStatus(str, Enum):
    TO_BE_CONSUMED = "TO_BE_CONSUMED"       # Allocated for upcoming turnaround / unit maintenance
    IN_STORAGE = "IN_STORAGE"               # Standard warehouse stock buffer
    IDLE_SURPLUS = "IDLE_SURPLUS"           # Dormant / unconsumed stock (Broadcasted to sister CPSEs)
    RESERVED_TRANSFER = "RESERVED_TRANSFER" # Locked by active inter-CPSE transfer indent
    CONSUMED = "CONSUMED"                   # Commissioned into refinery pipeline / plant


class InventoryItemCreate(BaseModel):
    """Payload submitted by site engineer after reviewing OCR-extracted procurement bill."""
    sku_code: str = Field(..., description="Enterprise SKU or Material Code (e.g. ONGC-ANK-2026-0041)")
    cpse: str = Field(..., description="Enterprise identifier: IOCL, ONGC, or BPCL")
    depot_id: str = Field(..., description="Storage facility ID (e.g. DEPOT-ONGC-ANK)")
    depot_location: str = Field(..., description="Human-readable plant location name")
    po_no: Optional[str] = Field(None, description="Procurement purchase order number")
    heat_no: Optional[str] = Field(None, description="MTC cast/heat melt number")
    description: str = Field(..., description="Component engineering description")
    canonical_id: Optional[str] = Field(None, description="Standardized canonical ID (e.g. CAN-000209)")
    item_type: Optional[str] = Field(None, description="Normalized item type")
    size_nb_mm: Optional[float] = Field(None, description="Nominal bore diameter in millimeters")
    pressure_class: Optional[int] = Field(None, description="ASME pressure rating class")
    metallurgy: Optional[str] = Field(None, description="ASTM standard material grade")
    facing_end: Optional[str] = Field(None, description="Facing end interface (RF, RTJ, BW, etc.)")
    standard: Optional[str] = Field(None, description="Governing standard (ASME B16.5, API 600, etc.)")
    quantity: int = Field(default=1, ge=1, description="Quantity received in bill")
    unit_cost_inr: float = Field(default=0.0, ge=0.0, description="Unit cost in INR")
    status: InventoryItemStatus = Field(default=InventoryItemStatus.TO_BE_CONSUMED)
    source_document_id: Optional[int] = Field(None, description="Foreign key to ingested_documents record")
    action_note: Optional[str] = Field(None, description="Engineer comment or intended maintenance unit")
    engineer_id: str = Field(default="SITE_ENGINEER_ONGC", description="ID of verifying site engineer")


class InventoryStatusUpdate(BaseModel):
    """Payload to transition item status (e.g. TO_BE_CONSUMED -> IDLE_SURPLUS)."""
    status: InventoryItemStatus = Field(..., description="Target lifecycle state")
    action_note: Optional[str] = Field(None, description="Reason for status transition")
    engineer_id: str = Field(default="SITE_ENGINEER", description="ID of acting site engineer")


class InventoryItemResponse(BaseModel):
    """Full inventory item model returned by API."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_code: str
    cpse: str
    depot_id: str
    depot_location: str
    po_no: Optional[str] = None
    heat_no: Optional[str] = None
    description: str
    canonical_id: Optional[str] = None
    item_type: Optional[str] = None
    size_nb_mm: Optional[float] = None
    pressure_class: Optional[int] = None
    metallurgy: Optional[str] = None
    facing_end: Optional[str] = None
    standard: Optional[str] = None
    quantity: int
    unit_cost_inr: float
    total_value_inr: float
    status: InventoryItemStatus
    days_idle: int
    source_document_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_broadcasted_surplus: bool = Field(default=False, description="True if visible to sister CPSEs as idle stock")
