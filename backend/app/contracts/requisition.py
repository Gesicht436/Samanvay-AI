"""
Pydantic v2 Contracts for Cross-CPSE Material Requisitions & CISF Digital Gate Passes.
Complies with Central Vigilance Commission (CVC) procurement transparency,
GST E-Way Bill transit tracking, and CISF perimeter material movement control.
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RequisitionStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED_FOR_DISPATCH = "APPROVED_FOR_DISPATCH"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"


class UrgencyLevel(str, Enum):
    EMERGENCY_SHUTDOWN = "EMERGENCY_SHUTDOWN"    # Critical refinery unit trip / shutdown risk
    PLANNED_MAINTENANCE = "PLANNED_MAINTENANCE"  # Turnaround window scheduled within 14 days
    ROUTINE = "ROUTINE"                          # Surplus replenishment


class RequisitionItem(BaseModel):
    sku_code: str
    description: str
    quantity: int
    unit_cost_inr: float
    total_value_inr: float
    canonical_id: Optional[str] = None


class DigitalMaterialGatePass(BaseModel):
    """
    Official CISF (Central Industrial Security Force) Electronic Material Gate Pass.
    Issued upon approval of cross-CPSE transfer indent.
    """
    model_config = ConfigDict(from_attributes=True)

    gate_pass_no: str = Field(..., description="Official Non-Returnable Outward Gate Pass No, e.g. OGP-2026-081-9921")
    pass_type: str = Field(default="NON_RETURNABLE_OUTWARD_INTER_CPSE")
    requisition_id: str
    issuing_cpse: str
    issuing_depot: str
    receiving_cpse: str
    receiving_depot: str
    transporter_name: str = Field(default="CONCOR / Bharat Logistics Rail-Road Fleet")
    vehicle_no: str
    driver_name: str
    driver_id_no: str = Field(..., description="Aadhaar / Commercial Driving License No")
    gst_eway_bill_no: str
    cisf_verification_seal: str = Field(..., description="Digital verification token from refinery security gate")
    issue_timestamp: str
    sha256_hash: str = Field(..., description="Cryptographic tamper-proof seal of gate pass payload")
    transit_distance_km: float
    co2_saved_kg: float
    estimated_transit_hours: int
    qr_code_svg: Optional[str] = Field(None, description="Inline scalable SVG QR code for gate security scanning")
    qr_code_data_url: Optional[str] = Field(None, description="Base64 Data URI for QR code embedding")
    verification_url: Optional[str] = Field(None, description="Public/CISF URL for cryptographic authenticity verification")


class TimelineEvent(BaseModel):
    timestamp: str
    event: str          # "CREATED", "CONFIRMED", "APPROVED", "DISPATCHED", "IN_TRANSIT", "DELIVERED", "REJECTED"
    title: str          # User-facing title, e.g. "Procurement Request Issued"
    actor: str          # e.g. "Mayank Anand, Executive Engineer (Materials)"
    actor_cpse: str     # e.g. "IOCL"
    notes: Optional[str] = None
    details: Optional[dict] = None


class InterCPSERequisition(BaseModel):
    """
    Lifecycle tracking model for inter-enterprise transfer of surplus spares.
    """
    model_config = ConfigDict(from_attributes=True)

    requisition_id: str = Field(..., description="Unique indent identifier, e.g. IND-2026-0042")
    source_cpse: str = Field(..., description="Requesting CPSE, e.g. IOCL")
    source_depot: str = Field(..., description="Requesting depot, e.g. Panipat Refinery, Haryana")
    source_unit: str = Field(default="Refinery CDU-2 / Hydrocracker Unit")
    target_cpse: str = Field(..., description="Sister CPSE holding surplus stock, e.g. ONGC")
    target_depot: str = Field(..., description="Surplus depot, e.g. Hazira Gas Processing Plant, Gujarat")
    sku_code: str
    item_description: str
    required_qty: int
    unit_cost_inr: float
    total_value_inr: float
    justification: str
    urgency_level: UrgencyLevel
    created_at: str
    status: RequisitionStatus
    requested_by: str = Field(default="Mayank Anand, Executive Engineer (Materials)")
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    dispatch_timestamp: Optional[str] = None
    delivery_timestamp: Optional[str] = None
    gate_pass: Optional[DigitalMaterialGatePass] = None
    audit_hash: str = Field(..., description="Immutable SHA-256 audit fingerprint")
    timeline: List[TimelineEvent] = Field(default_factory=list)
    tracking_carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[str] = None
    facility_confirmation_note: Optional[str] = None


class RequisitionCreateRequest(BaseModel):
    source_cpse: str
    source_depot: str
    source_unit: str = "Refinery Process Unit"
    target_cpse: str
    target_depot: str
    sku_code: str
    item_description: str
    required_qty: int = 1
    unit_cost_inr: float
    justification: str
    urgency_level: UrgencyLevel = UrgencyLevel.EMERGENCY_SHUTDOWN


class RequisitionApproveRequest(BaseModel):
    approver_name: str = "P. K. Sharma, Chief General Manager (Procurement)"
    vehicle_no: str = "HR-06-EA-8841"
    driver_name: str = "Rajesh Kumar Yadav"
    driver_id_no: str = "DL-042019948123"


class RequisitionConfirmRequest(BaseModel):
    confirming_officer: str = "P. K. Sharma, Chief General Manager (Procurement)"
    confirmation_notes: str = "Part physical condition verified in surplus bay; facility confirmed capability to supply requested quantity."
    vehicle_no: Optional[str] = "GJ-05-AB-7712"
    driver_name: Optional[str] = "Mukesh Singh Parmar"
    driver_id_no: Optional[str] = "DL-GJ0520210084"


class RequisitionRejectRequest(BaseModel):
    rejection_reason: str = "Item reserved for imminent internal unit turnaround maintenance."
    rejected_by: str = "A. K. Ganguly, GM (Materials)"


class RequisitionTrackUpdateRequest(BaseModel):
    event: str = "IN_TRANSIT_UPDATE"
    title: str = "Transit Checkpoint Verified"
    actor: str = "CISF Toll Checkpost Officer"
    actor_cpse: str = "MoPNG"
    notes: Optional[str] = "Vehicle cleared interstate transit corridor checkpoint."
    tracking_carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[str] = None


class RouteEstimateRequest(BaseModel):
    origin_depot: str = Field(..., description="Origin depot name or ID, e.g. 'Hazira Gas Processing Plant, Gujarat'")
    destination_depot: str = Field(..., description="Destination depot name or ID, e.g. 'Panipat Refinery, Haryana'")
    cargo_weight_tons: float = Field(default=1.0, description="Estimated total weight in metric tons")


class RouteEstimateResponse(BaseModel):
    origin_depot: str
    destination_depot: str
    origin_cpse: str
    destination_cpse: str
    geodesic_distance_km: float
    road_distance_km: float
    driving_hours: float
    total_transit_hours: int
    estimated_transit_days: float
    freight_cost_inr: float
    co2_emissions_kg: float
    co2_avoided_vs_import_kg: float
    primary_corridor: str
    recommended_logistics_mode: str


class InventoryLockItem(BaseModel):
    sku_code: str
    cpse: str
    depot: str
    item_description: str
    total_stock: int
    available_stock: int
    reserved_stock: int
    active_requisition_ids: List[str]
    lock_status: str  # "AVAILABLE", "PARTIALLY_RESERVED", "LOCKED"


class GatePassVerificationResponse(BaseModel):
    gate_pass_no: str
    requisition_id: str
    status: str
    is_valid: bool
    cisf_seal_valid: bool
    issuing_depot: str
    receiving_depot: str
    vehicle_no: str
    driver_name: str
    sha256_hash: str
    issue_timestamp: str
    verification_message: str

