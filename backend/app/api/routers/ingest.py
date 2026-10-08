"""
FastAPI Ingest Router — Multi-modal Document & Catalog Ingestion.

Handles:
1. Multi-modal PDF & Scanned MTC Ingestion:
   - Fast PyMuPDF digital vector stream extraction (< 50ms)
   - Preprocessed PaddleOCR raster scan path
   - EN 10204 3.1 MTC chemistry, IIW CE, and mechanical ASTM validation
   - Automatic graceful degradation and routing to HITL queue
2. ERP Inventory Catalog Batch Streaming:
   - CSV / Excel batch import with schema validation
3. Ingested Document Ledger Queries.
"""

import io
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import pandas as pd

from backend.app.api.dependencies import (
    get_db_session,
    require_csrf,
    require_permission,
    verify_cpse_access,
)
from backend.app.core import permissions as perm
from backend.app.models.tables import AuthSession, IngestedDocument, InventoryItem, User
from backend.app.schemas.material import ExtractedMaterialAttributes
from ml.vision.ocr_engine import OCREngine
from ml.vision.mtc_parser import MTCParser


router = APIRouter(prefix="/ingest", tags=["Ingest"])

# Singleton engine instances
ocr_engine = OCREngine()
mtc_parser = MTCParser()


@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission(perm.INGEST_DOCUMENT)),
    _csrf: AuthSession = Depends(require_csrf),
    db: Session = Depends(get_db_session),
):
    """
    Ingests procurement invoices, delivery challans, and EN 10204 3.1 MTC certificates.
    Performs dual-path PDF vector stream or raster OCR extraction, extracts chemical
    and mechanical properties, and verifies ASTM conformance.

    Requires ``INGEST_DOCUMENT`` and a CSRF-verified session (AUTH-007/AUTH-006).
    ``IngestedDocument`` has no CPSE/depot ownership column, so this write is
    authenticated and permissioned but not tenant-scoped; document ownership
    remains an unresolved decision and is deliberately not invented here.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    # 1. Dual-Path Text Extraction
    ocr_result = ocr_engine.extract_document(file_bytes, file.filename)
    raw_text = (ocr_result.get("raw_text") or "").strip()
    confidence = float(ocr_result.get("confidence_score", 0.0))
    doc_type = ocr_result.get("doc_type", "UNKNOWN")
    is_scanned = bool(ocr_result.get("is_scanned", False))
    is_unreadable = bool(not raw_text or len(raw_text) < 5 or confidence == 0.0)

    # 2. MTC Certificate Extraction & ASTM Validation
    parsed_mtc = mtc_parser.parse_full_mtc(raw_text, confidence_score=confidence)
    material_attrs = mtc_parser.to_material_attributes(parsed_mtc)

    # If document is unreadable, force requires_hitl and mark incomplete
    if is_unreadable:
        material_attrs.requires_hitl = True
        material_attrs.is_incomplete = True

    # 3. Persist into Relational Ledger
    doc_record = IngestedDocument(
        filename=file.filename,
        doc_type=doc_type,
        is_scanned=is_scanned,
        confidence=confidence,
        raw_text=raw_text[:50000] if raw_text else "",
        parsed_metadata={
            "header": parsed_mtc.get("header", {}),
            "chemistry": parsed_mtc.get("chemical_composition", {}),
            "carbon_equivalent_iiw": parsed_mtc.get("carbon_equivalent_iiw"),
            "weldability": parsed_mtc.get("weldability"),
            "pren": parsed_mtc.get("pren"),
            "mechanical": parsed_mtc.get("mechanical_properties", {}),
            "conforms_to_astm": parsed_mtc.get("conforms_to_astm", False),
            "warnings": parsed_mtc.get("non_conformance_warnings", []),
            "missing_attributes": material_attrs.missing_attributes,
            "requires_hitl": material_attrs.requires_hitl,
            "is_unreadable": is_unreadable,
        },
    )

    try:
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)
        doc_id = doc_record.id
    except Exception:
        db.rollback()
        doc_id = None

    return {
        "document_id": doc_id,
        "filename": file.filename,
        "doc_type": doc_type,
        "is_scanned": is_scanned,
        "is_unreadable": is_unreadable,
        "status_message": (
            "⚠️ Image is not readable. No extractable text found. Please enter properties manually."
            if is_unreadable
            else "Document text successfully parsed."
        ),
        "confidence_score": confidence,
        "requires_hitl": material_attrs.requires_hitl,
        "is_incomplete": material_attrs.is_incomplete,
        "missing_attributes": material_attrs.missing_attributes,
        "extracted_attributes": material_attrs.model_dump(),
        "chemistry": parsed_mtc.get("chemical_composition", {}),
        "carbon_equivalent_iiw": parsed_mtc.get("carbon_equivalent_iiw"),
        "weldability": parsed_mtc.get("weldability"),
        "pren": parsed_mtc.get("pren"),
        "mechanical": parsed_mtc.get("mechanical_properties", {}),
        "astm_conformance": parsed_mtc.get("conforms_to_astm", False),
        "warnings": parsed_mtc.get("non_conformance_warnings", []),
        "bounding_boxes": ocr_result.get("bounding_boxes", [])[:50],
    }


@router.post("/catalog")
async def upload_catalog(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission(perm.INGEST_CATALOG)),
    _csrf: AuthSession = Depends(require_csrf),
    session_cpse: str = Depends(verify_cpse_access),
    db: Session = Depends(get_db_session),
):
    """
    Batch imports ERP inventory catalog CSV or Excel spreadsheet into plant stock ledger.

    Requires ``INGEST_CATALOG`` and a CSRF-verified session. The authenticated
    session CPSE is the only accepted tenant: a file that declares a different
    CPSE is rejected outright rather than imported into another tenant, and an
    absent CPSE column/blank cell falls back to the session CPSE.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_bytes = await file.read()
    fn_lower = file.filename.lower()

    try:
        if fn_lower.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif fn_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            raise HTTPException(status_code=400, detail="Unsupported catalog format. Must be CSV or Excel.")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse tabular file: {str(e)}")

    required_cols = {"sku_code", "cpse", "depot_id", "description", "item_type"}
    actual_cols = {c.lower().strip() for c in df.columns}

    # Normalize column names
    col_map = {c: c.lower().strip() for c in df.columns}
    df.rename(columns=col_map, inplace=True)

    # Tenant boundary: the authenticated session CPSE is authoritative. A file
    # that declares any other CPSE is rejected in full so no row can be inserted
    # into a foreign tenant (AUTH-007 Sections 15 and 18).
    effective_cpse = session_cpse.strip().upper()
    if "cpse" in df.columns:
        declared = {
            str(value).strip().upper()
            for value in df["cpse"].tolist()
            if pd.notna(value) and str(value).strip()
        }
        foreign = sorted(value for value in declared if value != effective_cpse)
        if foreign:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Catalog declares CPSE values outside the authenticated session "
                    f"tenant ({foreign}). Ingestion is restricted to {session_cpse}."
                ),
            )

    imported_count = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            sku = str(row.get("sku_code", "")).strip()
            if not sku or sku == "nan":
                continue

            existing = db.query(InventoryItem).filter(InventoryItem.sku_code == sku).first()
            if existing:
                continue

            item = InventoryItem(
                sku_code=sku,
                cpse=effective_cpse,
                depot_id=str(row.get("depot_id", "DEFAULT_DEPOT")).strip(),
                depot_location=str(row.get("depot_location", "Main Plant")).strip(),
                description=str(row.get("description", "")).strip(),
                item_type=str(row.get("item_type", "GENERAL")).strip().upper(),
                size_nb_mm=float(row.get("size_nb_mm")) if pd.notna(row.get("size_nb_mm")) else None,
                pressure_class=int(row.get("pressure_class")) if pd.notna(row.get("pressure_class")) else None,
                schedule=str(row.get("schedule")) if pd.notna(row.get("schedule")) else None,
                metallurgy=str(row.get("metallurgy")) if pd.notna(row.get("metallurgy")) else None,
                facing_end=str(row.get("facing_end")) if pd.notna(row.get("facing_end")) else None,
                standard=str(row.get("standard")) if pd.notna(row.get("standard")) else None,
                # The model column is ``quantity``; ``available_qty`` is the
                # ERP export header and is mapped onto it here.
                quantity=int(row.get("available_qty", row.get("quantity", 1))),
                days_idle=int(row.get("days_idle", 0)),
                unit_cost_inr=float(row.get("unit_cost_inr", 0.0)) if pd.notna(row.get("unit_cost_inr")) else 0.0,
                status="SURPLUS" if int(row.get("days_idle", 0)) >= 90 else "ACTIVE",
            )
            db.add(item)
            imported_count += 1
        except Exception as ex:
            errors.append(f"Row {idx}: {str(ex)}")

    try:
        db.commit()
    except Exception:
        db.rollback()

    return {
        "filename": file.filename,
        "rows_processed": len(df),
        "imported_count": imported_count,
        "errors_count": len(errors),
        "status": "COMPLETED",
    }


@router.get("/documents")
def list_documents(
    skip: int = 0,
    limit: int = 20,
    _current_user: User = Depends(require_permission(perm.DOCUMENT_READ)),
    db: Session = Depends(get_db_session),
):
    """
    Lists ingested documents from the sovereign intake ledger.

    AUTH-5K: authentication + DOCUMENT_READ permission only. Tenant scoping
    is explicitly deferred (E-1): IngestedDocument has no CPSE/depot
    ownership field, so no tenant filter is introduced here.
    """
    try:
        docs = db.query(IngestedDocument).order_by(IngestedDocument.id.desc()).offset(skip).limit(limit).all()
        return {
            "total": len(docs),
            "documents": [
                {
                    "id": d.id,
                    "filename": d.filename,
                    "doc_type": d.doc_type,
                    "is_scanned": d.is_scanned,
                    "confidence": float(d.confidence),
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                    "metadata": d.parsed_metadata,
                }
                for d in docs
            ]
        }
    except Exception:
        return {"total": 0, "documents": []}


@router.get("/documents/{doc_id}")
def get_document(
    doc_id: int,
    _current_user: User = Depends(require_permission(perm.DOCUMENT_READ)),
    db: Session = Depends(get_db_session),
):
    """
    Retrieves full parsed metadata and extraction results for an ingested document.

    AUTH-5K: authentication + DOCUMENT_READ permission only. Tenant scoping
    is explicitly deferred (E-1): IngestedDocument has no CPSE/depot
    ownership field, so no tenant filter is introduced here.
    """
    doc = db.query(IngestedDocument).filter(IngestedDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document ID {doc_id} not found.")

    return {
        "id": doc.id,
        "filename": doc.filename,
        "doc_type": doc.doc_type,
        "is_scanned": doc.is_scanned,
        "confidence": float(doc.confidence),
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "raw_text_preview": doc.raw_text[:1000] if doc.raw_text else "",
        "metadata": doc.parsed_metadata,
    }
