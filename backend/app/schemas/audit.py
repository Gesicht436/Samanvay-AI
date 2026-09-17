"""Pydantic v2 schemas for sovereign CVC/CAG audit ledger."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AuditActionCategory(str, Enum):
    INWARD_PROCUREMENT = "INWARD_PROCUREMENT"
    LIFECYCLE_TRANSITION = "LIFECYCLE_TRANSITION"
    REQUISITION_INITIATED = "REQUISITION_INITIATED"
    SUPPLY_CONFIRMED = "SUPPLY_CONFIRMED"
    GATE_PASS_ISSUED = "GATE_PASS_ISSUED"
    DELIVERY_VERIFIED = "DELIVERY_VERIFIED"
    HITL_DECISION = "HITL_DECISION"
    ACTIVE_LEARNING_FEEDBACK = "ACTIVE_LEARNING_FEEDBACK"


class AuditLogEntry(BaseModel):
    log_id: str
    timestamp: datetime
    action_category: AuditActionCategory
    action_name: str
    actor_name: str
    actor_role: str
    cpse: str
    depot: str
    reference_id: str
    details: str
    prev_hash: str
    sha256_hash: str
    is_verified: bool = True


class AuditLogCreateRequest(BaseModel):
    action_category: AuditActionCategory
    action_name: str
    actor_name: str
    actor_role: str
    cpse: str
    depot: str
    reference_id: str
    details: str


class AuditVerificationResponse(BaseModel):
    """Result of on-the-fly audit chain verification."""

    is_valid: bool
    total_entries: int
    entries_verified: int
    first_broken_index: Optional[int] = None
    message: str


class AuditLogListResponse(BaseModel):
    entries: list[AuditLogEntry]
    total: int
    page: int = 1
    page_size: int = 50


class ActiveLearningFeedback(BaseModel):
    """Schema for HITL active learning feedback decisions."""

    source_description: str
    source_sku: str
    canonical_id: str
    decision: str = Field(..., description="APPROVE, REJECT, or RECLASSIFY")
    officer: str
    action_note: Optional[str] = None
    tier_override: Optional[str] = None
    confidence_override: Optional[float] = Field(None, ge=0.0, le=1.0)
