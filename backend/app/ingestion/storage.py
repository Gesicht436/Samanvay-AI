"""
PostgreSQL / SQLAlchemy Storage Layer for Ingested Documents and Reconciliation Audits.
Provides robust fallback to SQLite when PostgreSQL container is offline.
"""

import logging
from typing import Generator, Optional, Dict, Any, List
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    Boolean,
    Float,
    desc
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from backend.app.contracts.base import Base
from backend.app.config import settings

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# SQLAlchemy Models
# -----------------------------------------------------------------------------

class IngestedDocument(Base):
    """Stores raw OCR/digital text and extracted key-values from uploaded certificates and challans."""
    __tablename__ = "ingested_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    doc_type = Column(String(100), default="MTC_CERTIFICATE", nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReconciliationAudit(Base):
    """Audit trail for material code standardization and human-in-the-loop decisions."""
    __tablename__ = "reconciliation_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_sku = Column(String(100), nullable=False)
    source_cpse = Column(String(50), nullable=False)
    source_description = Column(Text, nullable=True)
    matched_canonical_id = Column(String(50), nullable=False)
    tier = Column(String(50), nullable=False)  # TIER_1_IDENTICAL, TIER_2_SUBSTITUTE
    confidence = Column(Float, nullable=False)
    verified_by_hitl = Column(Boolean, default=False, nullable=False)
    hitl_officer = Column(String(100), default="SYSTEM_AUTO", nullable=False)
    action_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InventoryItem(Base):
    """Central repository of physical components, tracking lifecycle tags and idle surplus state."""
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_code = Column(String(100), nullable=False, index=True)
    cpse = Column(String(50), nullable=False, index=True)  # IOCL, ONGC, BPCL
    depot_id = Column(String(50), nullable=False, index=True)
    depot_location = Column(String(255), nullable=False)
    po_no = Column(String(100), nullable=True)
    heat_no = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    canonical_id = Column(String(50), nullable=True, index=True)
    item_type = Column(String(100), nullable=True)
    size_nb_mm = Column(Float, nullable=True)
    pressure_class = Column(Integer, nullable=True)
    metallurgy = Column(String(100), nullable=True)
    facing_end = Column(String(50), nullable=True)
    standard = Column(String(100), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_cost_inr = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="TO_BE_CONSUMED", nullable=False, index=True)
    days_idle = Column(Integer, default=0, nullable=False)
    source_document_id = Column(Integer, nullable=True)
    action_note = Column(Text, nullable=True)
    last_updated_by = Column(String(100), default="SITE_ENGINEER", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# -----------------------------------------------------------------------------
# Database Engine Initialization with Fallback
# -----------------------------------------------------------------------------

def get_engine():
    """Attempts connection to PostgreSQL; falls back to SQLite if PostgreSQL is unreachable."""
    try:
        pg_engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 2}
        )
        with pg_engine.connect():
            pass
        logger.info("[+] Successfully connected to PostgreSQL.")
        return pg_engine
    except Exception as e:
        logger.warning(f"[-] PostgreSQL connection unavailable ({e}). Falling back to local SQLite.")
        sqlite_engine = create_engine(
            settings.SQLITE_FALLBACK_URL,
            connect_args={"check_same_thread": False}
        )
        return sqlite_engine


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Creates all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------------------------------
# Storage Helper Functions
# -----------------------------------------------------------------------------

def save_extracted_document(
    db: Session,
    filename: str,
    raw_text: str,
    metadata: Optional[Dict[str, Any]] = None,
    doc_type: str = "MTC_CERTIFICATE"
) -> IngestedDocument:
    """Persists extracted OCR/PDF document text and structured key-values."""
    doc = IngestedDocument(
        filename=filename,
        doc_type=doc_type,
        raw_text=raw_text,
        parsed_metadata=metadata or {}
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def save_reconciliation_decision(
    db: Session,
    source_sku: str,
    source_cpse: str,
    matched_canonical_id: str,
    tier: str,
    confidence: float,
    verified_by_hitl: bool = False,
    hitl_officer: str = "SYSTEM_AUTO",
    source_description: Optional[str] = None,
    action_note: Optional[str] = None
) -> ReconciliationAudit:
    """Logs a material code reconciliation decision for auditing."""
    audit = ReconciliationAudit(
        source_sku=source_sku,
        source_cpse=source_cpse,
        source_description=source_description,
        matched_canonical_id=matched_canonical_id,
        tier=tier,
        confidence=confidence,
        verified_by_hitl=verified_by_hitl,
        hitl_officer=hitl_officer,
        action_note=action_note
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


def get_all_documents(db: Session, limit: int = 50) -> List[IngestedDocument]:
    """Retrieves recent ingested documents for audit inspection."""
    return db.query(IngestedDocument).order_by(desc(IngestedDocument.created_at)).limit(limit).all()


def get_recent_audits(db: Session, limit: int = 50) -> List[ReconciliationAudit]:
    """Retrieves recent reconciliation audits."""
    return db.query(ReconciliationAudit).order_by(desc(ReconciliationAudit.created_at)).limit(limit).all()


# -----------------------------------------------------------------------------
# Central Inventory Item Operations
# -----------------------------------------------------------------------------

def create_inventory_item(
    db: Session,
    sku_code: str,
    cpse: str,
    depot_id: str,
    depot_location: str,
    description: str,
    quantity: int = 1,
    unit_cost_inr: float = 0.0,
    status: str = "TO_BE_CONSUMED",
    po_no: Optional[str] = None,
    heat_no: Optional[str] = None,
    canonical_id: Optional[str] = None,
    item_type: Optional[str] = None,
    size_nb_mm: Optional[float] = None,
    pressure_class: Optional[int] = None,
    metallurgy: Optional[str] = None,
    facing_end: Optional[str] = None,
    standard: Optional[str] = None,
    source_document_id: Optional[int] = None,
    action_note: Optional[str] = None,
    engineer_id: str = "SITE_ENGINEER"
) -> InventoryItem:
    """Inserts a new inventory item verified from an uploaded procurement bill."""
    item = InventoryItem(
        sku_code=sku_code,
        cpse=cpse,
        depot_id=depot_id,
        depot_location=depot_location,
        description=description,
        quantity=quantity,
        unit_cost_inr=unit_cost_inr,
        status=status,
        po_no=po_no,
        heat_no=heat_no,
        canonical_id=canonical_id,
        item_type=item_type,
        size_nb_mm=size_nb_mm,
        pressure_class=pressure_class,
        metallurgy=metallurgy,
        facing_end=facing_end,
        standard=standard,
        source_document_id=source_document_id,
        action_note=action_note,
        last_updated_by=engineer_id,
        days_idle=0
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_inventory_items(
    db: Session,
    cpse: Optional[str] = None,
    status: Optional[str] = None,
    depot_id: Optional[str] = None,
    limit: int = 100
) -> List[InventoryItem]:
    """Retrieves central inventory items filtered by CPSE, status, or depot."""
    query = db.query(InventoryItem)
    if cpse:
        query = query.filter(InventoryItem.cpse == cpse)
    if status:
        query = query.filter(InventoryItem.status == status)
    if depot_id:
        query = query.filter(InventoryItem.depot_id == depot_id)
    return query.order_by(desc(InventoryItem.updated_at)).limit(limit).all()


def get_inventory_item_by_id(db: Session, item_id: int) -> Optional[InventoryItem]:
    """Finds an inventory item by primary key."""
    return db.query(InventoryItem).filter(InventoryItem.id == item_id).first()


def update_inventory_status(
    db: Session,
    item_id: int,
    new_status: str,
    action_note: Optional[str] = None,
    engineer_id: str = "SITE_ENGINEER"
) -> Optional[InventoryItem]:
    """Transitions the lifecycle status of an inventory item (e.g. TO_BE_CONSUMED -> IDLE_SURPLUS)."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        return None
    item.status = new_status
    if action_note:
        item.action_note = action_note
    item.last_updated_by = engineer_id
    if new_status == "IDLE_SURPLUS" and item.days_idle == 0:
        item.days_idle = 90  # Default idle threshold for newly flagged surplus
    db.commit()
    db.refresh(item)
    return item

