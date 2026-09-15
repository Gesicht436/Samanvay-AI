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
