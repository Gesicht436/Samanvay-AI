"""Pydantic v2 schemas for inter-CPSE requisitions and CISF gate passes."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UrgencyLevel(str, Enum):
    EMERGENCY_SHUTDOWN = "EMERGENCY_SHUTDOWN"
    PLANNED_MAINTENANCE = "PLANNED_MAINTENANCE"
    ROUTINE = "ROUTINE"


class RequisitionStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED_FOR_DISPATCH = "APPROVED_FOR_DISPATCH"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"


class RequisitionCreateRequest(BaseModel):
    """Payload for POST /api/v1/requisition. Requires 'Idempotency-Key' header."""

    sku_code: str
    required_qty: int = Field(..., gt=0)
    source_unit: str
    justification: str
    urgency_level: UrgencyLevel
    requested_by: str


class RequisitionResponse(BaseModel):
    requisition_id: str
    source_cpse: str
    source_depot: str
    source_unit: str
    target_cpse: str
    target_depot: str
    sku_code: str
    item_description: str
    required_qty: int
    unit_cost_inr: float
    total_value_inr: float
    justification: str
    urgency_level: UrgencyLevel
    status: RequisitionStatus
    requested_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    dispatch_timestamp: Optional[datetime] = None
    delivery_timestamp: Optional[datetime] = None
    audit_hash: str
    created_at: datetime


class RequisitionApprovalRequest(BaseModel):
    approved_by: str
    approval_note: Optional[str] = None


class RequisitionRejectionRequest(BaseModel):
    rejected_by: str
    rejection_reason: str


class GatePassCreateRequest(BaseModel):
    """Payload for CISF gate pass generation."""

    transporter_name: str
    vehicle_no: str
    driver_name: str
    driver_id_no: str
    gst_eway_bill_no: str
    issuing_officer: str


class GatePassResponse(BaseModel):
    gate_pass_no: str
    requisition_id: str
    issuing_cpse: str
    issuing_depot: str
    receiving_cpse: str
    receiving_depot: str
    transporter_name: str
    vehicle_no: str
    driver_name: str
    driver_id_no: str
    gst_eway_bill_no: str
    cisf_verification_seal: str
    issue_timestamp: datetime
    sha256_hash: str
    transit_distance_km: float
    co2_saved_kg: float
    estimated_transit_hours: int
    qr_code_svg: str
