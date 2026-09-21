"""Pydantic v2 schemas for inventory management and lifecycle transitions."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class InventoryStatus(str, Enum):
    """Lifecycle status of an inventory item."""

    TO_BE_CONSUMED = "TO_BE_CONSUMED"
    IN_STORAGE = "IN_STORAGE"
    IDLE_SURPLUS = "IDLE_SURPLUS"
    RESERVED_TRANSFER = "RESERVED_TRANSFER"
    CONSUMED = "CONSUMED"


class InventoryItemResponse(BaseModel):
    """Public inventory item response (respects attribute-level privacy)."""

    id: int
    sku_code: str
    cpse: str
    depot_id: str
    depot_location: str
    description: str
    canonical_id: Optional[str] = None
    item_type: str
    size_nb_mm: Optional[float] = None
    pressure_class: Optional[int] = None
    pressure_rating_psi: Optional[float] = None
    schedule: Optional[str] = None
    metallurgy: Optional[str] = None
    facing_end: Optional[str] = None
    standard: Optional[str] = None
    indian_standard: Optional[str] = None
    oil_std_spec: Optional[str] = None
    oil_material_code: Optional[str] = None
    gem_category_id: Optional[str] = None
    gem_product_id: Optional[str] = None
    cppp_tender_ref: Optional[str] = None
    make_in_india_class: Optional[str] = "Class-I"
    local_content_percentage: Optional[float] = 75.0
    pressure_rating_bar: Optional[float] = None
    location_state: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)
    quantity: int
    status: InventoryStatus
    days_idle: int = 0
    is_broadcasted_surplus: bool = False
    created_at: datetime
    updated_at: datetime


class InventoryItemPrivateResponse(InventoryItemResponse):
    """
    Internal view with commercial pricing (own facility only).
    NEVER exposed in cross-CPSE responses per SIH Slide 4 privacy mandate.
    """

    po_no: Optional[str] = None
    heat_no: Optional[str] = None
    unit_cost_inr: float
    total_value_inr: float
    source_document_id: Optional[int] = None


class InventoryCreateRequest(BaseModel):
    """Payload for creating a new inventory item from ingestion."""

    sku_code: str
    cpse: str
    depot_id: str
    depot_location: str
    po_no: Optional[str] = None
    heat_no: Optional[str] = None
    description: str
    item_type: str
    size_nb_mm: Optional[float] = None
    pressure_class: Optional[int] = None
    pressure_rating_psi: Optional[float] = None
    schedule: Optional[str] = None
    metallurgy: Optional[str] = None
    facing_end: Optional[str] = None
    standard: Optional[str] = None
    indian_standard: Optional[str] = None
    oil_std_spec: Optional[str] = None
    oil_material_code: Optional[str] = None
    gem_category_id: Optional[str] = None
    gem_product_id: Optional[str] = None
    cppp_tender_ref: Optional[str] = None
    make_in_india_class: Optional[str] = "Class-I"
    local_content_percentage: Optional[float] = 75.0
    pressure_rating_bar: Optional[float] = None
    location_state: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)
    quantity: int = Field(..., ge=0)
    unit_cost_inr: float = Field(..., ge=0)
    status: InventoryStatus = InventoryStatus.TO_BE_CONSUMED
    source_document_id: Optional[int] = None


class InventoryStatusUpdateRequest(BaseModel):
    """Payload for lifecycle status transition."""

    status: InventoryStatus
    reason: Optional[str] = None
    officer: Optional[str] = None


class InventoryListResponse(BaseModel):
    """Paginated inventory list response."""

    items: list[InventoryItemResponse]
    total: int
    page: int = 1
    page_size: int = 50


class SurplusRadarItem(BaseModel):
    """
    Cross-CPSE surplus item for the Pre-Purchase Radar.
    Prices are STRIPPED per attribute-level privacy enforcement.
    """

    sku_code: str
    cpse: str
    depot_id: str
    depot_location: str
    description: str
    item_type: str
    size_nb_mm: Optional[float] = None
    pressure_class: Optional[int] = None
    pressure_rating_psi: Optional[float] = None
    schedule: Optional[str] = None
    metallurgy: Optional[str] = None
    facing_end: Optional[str] = None
    standard: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)
    quantity: int
    days_idle: int
    # NOTE: unit_cost_inr and total_value_inr are DELIBERATELY ABSENT
