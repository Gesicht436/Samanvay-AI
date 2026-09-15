"""
Unit Tests for Database Storage and Relational Persistence.
"""

import pytest
from sqlalchemy.orm import Session
from backend.app.ingestion.storage import (
    init_db,
    SessionLocal,
    save_extracted_document,
    save_reconciliation_decision,
    get_all_documents,
    get_recent_audits,
    IngestedDocument,
    ReconciliationAudit,
)
from backend.app.graph.client import verify_connectivity


@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()


def test_save_and_retrieve_ingested_document(db_session: Session):
    filename = "test_flange_cert.pdf"
    raw_text = "BHARAT HEAVY PROCESS SPARES WELD NECK FLANGE 4IN 300# A105"
    metadata = {
        "heat_no": "HT-9999",
        "material_grade": "ASTM A105",
        "yield_mpa": 310
    }

    doc = save_extracted_document(
        db=db_session,
        filename=filename,
        raw_text=raw_text,
        metadata=metadata,
        doc_type="MTC_CERTIFICATE"
    )

    assert doc.id is not None
    assert doc.filename == filename
    assert doc.parsed_metadata["heat_no"] == "HT-9999"

    all_docs = get_all_documents(db_session, limit=10)
    assert any(d.id == doc.id for d in all_docs)


def test_save_and_retrieve_reconciliation_audit(db_session: Session):
    audit = save_reconciliation_decision(
        db=db_session,
        source_sku="IOCL-MM-0001",
        source_cpse="IOCL",
        source_description="FLG WNRF 4IN 300# A105",
        matched_canonical_id="CAN-000009",
        tier="TIER_1_IDENTICAL",
        confidence=1.0,
        verified_by_hitl=True,
        hitl_officer="MAYANK_ANAND",
        action_note="Approved identical drop-in flange"
    )

    assert audit.id is not None
    assert audit.source_sku == "IOCL-MM-0001"
    assert audit.verified_by_hitl is True
    assert audit.hitl_officer == "MAYANK_ANAND"

    recent = get_recent_audits(db_session, limit=10)
    assert any(a.id == audit.id for a in recent)


def test_neo4j_connectivity_graceful():
    # Tests that checking connectivity does not raise an unhandled crash if Neo4j is offline
    is_connected = verify_connectivity()
    assert isinstance(is_connected, bool)
