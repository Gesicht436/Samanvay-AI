"""SQLAlchemy ORM models for all 8 PostgreSQL tables per specsheet §4.1."""

from datetime import datetime, timezone, timedelta

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Computed,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class IngestedDocument(Base):
    """Ingested document metadata — MTCs, delivery challans, PO invoices."""

    __tablename__ = "ingested_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    doc_type = Column(String(64), nullable=False)  # MTC_CERTIFICATE, DELIVERY_CHALLAN, PO_INVOICE
    is_scanned = Column(Boolean, default=False)
    confidence = Column(Numeric(5, 4), nullable=False)
    raw_text = Column(Text, nullable=True)
    parsed_metadata = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    inventory_items = relationship("InventoryItem", back_populates="source_document")


class InventoryItem(Base):
    """Plant inventory ledger — the central stock table for all CPSEs."""

    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_code = Column(String(64), unique=True, nullable=False, index=True)
    cpse = Column(String(32), nullable=False, index=True)  # IOCL, ONGC, BPCL, HPCL, GAIL
    depot_id = Column(String(64), nullable=False, index=True)
    depot_location = Column(String(255), nullable=False)
    po_no = Column(String(128), nullable=True)
    heat_no = Column(String(128), nullable=True)
    description = Column(Text, nullable=False)
    canonical_id = Column(String(64), nullable=True)
    item_type = Column(String(64), nullable=False, index=True)
    size_nb_mm = Column(Numeric(8, 2), nullable=True)
    pressure_class = Column(Integer, nullable=True)
    pressure_rating_psi = Column(Numeric(10, 2), nullable=True)
    schedule = Column(String(32), nullable=True)
    metallurgy = Column(String(64), nullable=True)
    facing_end = Column(String(32), nullable=True)
    standard = Column(String(64), nullable=True)
    properties = Column(JSONB, default={})  # Equipment-specific: trim, port_bore, seal_plan
    quantity = Column(Integer, nullable=False)
    unit_cost_inr = Column(Numeric(14, 2), nullable=False)
    total_value_inr = Column(
        Numeric(14, 2),
        Computed("quantity * unit_cost_inr"),
        nullable=True,
    )
    status = Column(String(32), nullable=False, default="TO_BE_CONSUMED", index=True)
    days_idle = Column(Integer, default=0)
    source_document_id = Column(Integer, ForeignKey("ingested_documents.id"), nullable=True)
    is_broadcasted_surplus = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (CheckConstraint("quantity >= 0", name="ck_quantity_non_negative"),)

    # Relationships
    source_document = relationship("IngestedDocument", back_populates="inventory_items")
    locks = relationship("InventoryLock", back_populates="inventory_item")


class Requisition(Base):
    """Inter-CPSE requisition and transfer orders."""

    __tablename__ = "requisitions"

    requisition_id = Column(String(64), primary_key=True)
    source_cpse = Column(String(32), nullable=False)
    source_depot = Column(String(255), nullable=False)
    source_unit = Column(String(128), nullable=False)
    target_cpse = Column(String(32), nullable=False)
    target_depot = Column(String(255), nullable=False)
    sku_code = Column(String(64), ForeignKey("inventory_items.sku_code"), nullable=False)
    item_description = Column(Text, nullable=False)
    required_qty = Column(Integer, nullable=False)
    unit_cost_inr = Column(Numeric(14, 2), nullable=False)
    total_value_inr = Column(Numeric(14, 2), nullable=False)
    justification = Column(Text, nullable=False)
    urgency_level = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="PENDING_APPROVAL")
    requested_by = Column(String(128), nullable=False)
    approved_by = Column(String(128), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    dispatch_timestamp = Column(DateTime(timezone=True), nullable=True)
    delivery_timestamp = Column(DateTime(timezone=True), nullable=True)
    audit_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (CheckConstraint("required_qty > 0", name="ck_required_qty_positive"),)

    # Relationships
    locks = relationship("InventoryLock", back_populates="requisition")
    gate_passes = relationship("DigitalGatePass", back_populates="requisition")


class InventoryLock(Base):
    """Atomic multi-depot inventory reservation locks (SELECT ... FOR UPDATE)."""

    __tablename__ = "inventory_locks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_code = Column(String(64), ForeignKey("inventory_items.sku_code"), nullable=False)
    requisition_id = Column(String(64), ForeignKey("requisitions.requisition_id"), nullable=False)
    locked_qty = Column(Integer, nullable=False)
    locked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)

    __table_args__ = (CheckConstraint("locked_qty > 0", name="ck_locked_qty_positive"),)

    # Relationships
    inventory_item = relationship("InventoryItem", back_populates="locks")
    requisition = relationship("Requisition", back_populates="locks")


class DigitalGatePass(Base):
    """CISF digital material gate pass with SHA-256 seal and SVG QR code."""

    __tablename__ = "digital_gate_passes"

    gate_pass_no = Column(String(64), primary_key=True)
    requisition_id = Column(String(64), ForeignKey("requisitions.requisition_id"), nullable=False)
    issuing_cpse = Column(String(32), nullable=False)
    issuing_depot = Column(String(255), nullable=False)
    receiving_cpse = Column(String(32), nullable=False)
    receiving_depot = Column(String(255), nullable=False)
    transporter_name = Column(String(128), nullable=False)
    vehicle_no = Column(String(32), nullable=False)
    driver_name = Column(String(128), nullable=False)
    driver_id_no = Column(String(64), nullable=False)
    gst_eway_bill_no = Column(String(64), nullable=False)
    cisf_verification_seal = Column(String(128), nullable=False)
    issue_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    sha256_hash = Column(String(64), nullable=False)
    transit_distance_km = Column(Numeric(10, 2), nullable=False)
    co2_saved_kg = Column(Numeric(10, 2), nullable=False)
    estimated_transit_hours = Column(Integer, nullable=False)
    qr_code_svg = Column(Text, nullable=False)

    # Relationships
    requisition = relationship("Requisition", back_populates="gate_passes")


class SovereignAuditLedger(Base):
    """CVC/CAG sovereign audit ledger with cryptographic SHA-256 hash chain."""

    __tablename__ = "sovereign_audit_ledger"

    log_id = Column(String(64), primary_key=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    action_category = Column(String(64), nullable=False)
    action_name = Column(String(128), nullable=False)
    actor_name = Column(String(128), nullable=False)
    actor_role = Column(String(128), nullable=False)
    cpse = Column(String(32), nullable=False)
    depot = Column(String(255), nullable=False)
    reference_id = Column(String(128), nullable=False)
    details = Column(Text, nullable=False)
    prev_hash = Column(String(64), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    is_verified = Column(Boolean, default=True)


class ActiveLearningFeedback(Base):
    """Active learning feedback cache table for online dynamic reranking."""

    __tablename__ = "active_learning_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_description = Column(Text, nullable=False)
    source_sku = Column(String(64), nullable=False, index=True)
    canonical_id = Column(String(64), nullable=False, index=True)
    decision = Column(String(16), nullable=False)  # APPROVE, REJECT, RECLASSIFY
    officer = Column(String(128), nullable=False)
    action_note = Column(Text, nullable=True)
    tier_override = Column(String(32), nullable=True)
    confidence_override = Column(Numeric(5, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class IdempotencyKey(Base):
    """API idempotency key cache for high-value asset transfer protection."""

    __tablename__ = "idempotency_keys"

    key = Column(String(128), primary_key=True)
    endpoint = Column(String(255), nullable=False)
    request_hash = Column(String(64), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_body = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)


class CdcOutbox(Base):
    """Transactional Change Data Capture Outbox table for real-time Neo4j synchronization."""

    __tablename__ = "cdc_outbox"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(64), nullable=False, index=True)
    operation = Column(String(16), nullable=False)  # INSERT, UPDATE, DELETE
    record_id = Column(String(128), nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)  # PENDING, PROCESSED, FAILED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

