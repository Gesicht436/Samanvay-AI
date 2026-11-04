"""
FastAPI Ingest Router — Multi-modal Document & Catalog Ingestion.

Powered by Hariom's OCR Pipeline (OCR.pipeline) and MTC Ingestion Intelligence
(backend.app.ingestion). Handles:
1. Multi-modal PDF & Scanned MTC Ingestion:
   - Native PyMuPDF vector stream extraction
   - Preprocessed PaddleOCR / EasyOCR raster scan path
   - EN 10204 3.1 MTC chemistry, IIW CE, and mechanical ASTM validation
   - Relational persistence into PostgreSQL IngestedDocument table
2. ERP Inventory Catalog Batch Streaming:
   - CSV / Excel batch import with schema validation
3. Ingested Document Ledger Queries.
"""

import io
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import pandas as pd

from backend.app.api.dependencies import get_db_session
from backend.app.models.tables import IngestedDocument, InventoryItem
from backend.app.ingestion.document import process_document, clean_text, parse_mtc_certificate

router = APIRouter(prefix="/ingest", tags=["Ingest"])

MAX_UPLOAD_BYTES = 15 * 1024 * 1024


class TextIngestRequest(BaseModel):
    raw_text: str = Field(min_length=1)


@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
):
    """
    Ingests procurement invoices, delivery challans, and EN 10204 3.1 MTC certificates.
    Performs dual-path PDF vector stream or raster OCR extraction, extracts chemical
    and mechanical properties, and verifies ASTM conformance.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    file_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large. Maximum upload size is 15 MB.",
        )

    # 1. Process Document through Hariom's OCR & Ingestion Pipeline
    try:
        doc_result = process_document(file_bytes, file.filename)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The selected document could not be processed: {exc}",
        ) from exc

    raw_text = doc_result.get("raw_text") or ""
    confidence = float(doc_result.get("confidence", 0.0))
    extraction_method = doc_result.get("extraction_method", "unknown")
    is_scanned = "paddle" in extraction_method.lower() or "easyocr" in extraction_method.lower()
    doc_type = "SCANNED_PDF" if is_scanned else "DIGITAL_VECTOR_PDF"
    is_unreadable = bool(not raw_text or len(raw_text.strip()) < 5 or confidence == 0.0)

    parsed_metadata = doc_result.get("parsed_metadata", {})
    chemistry = doc_result.get("chemistry", {})
    astm_conformance = doc_result.get("astm_conformance", False)
    warnings = doc_result.get("conformance_warnings", [])
    requires_hitl = doc_result.get("requires_hitl", False) or is_unreadable

    # 2. Persist into PostgreSQL IngestedDocument Ledger
    doc_record = IngestedDocument(
        filename=file.filename,
        doc_type=doc_type,
        is_scanned=is_scanned,
        confidence=confidence,
        raw_text=raw_text[:50000] if raw_text else "",
        parsed_metadata={
            **parsed_metadata,
            "chemistry": chemistry,
            "astm_conformance": astm_conformance,
            "warnings": warnings,
            "requires_hitl": requires_hitl,
            "is_unreadable": is_unreadable,
            "extraction_method": extraction_method,
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

    # Merge response with both frontend schemas
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
        "confidence": confidence,
        "extraction_method": extraction_method,
        "page_count": doc_result.get("page_count", 1),
        "pages": doc_result.get("pages", []),
        "requires_hitl": requires_hitl,
        "is_incomplete": bool(requires_hitl and not astm_conformance),
        "missing_attributes": warnings,
        "extracted_attributes": parsed_metadata.get("engineering_attributes", {}),
        "parsed_metadata": parsed_metadata,
        "raw_text": raw_text,
        "chemistry": chemistry,
        "carbon_equivalent_iiw": chemistry.get("carbon_equivalent_iiw") if isinstance(chemistry, dict) else None,
        "weldability": chemistry.get("weldability") if isinstance(chemistry, dict) else None,
        "pren": chemistry.get("pren") if isinstance(chemistry, dict) else None,
        "mechanical": parsed_metadata.get("mechanical_properties", []),
        "astm_conformance": astm_conformance,
        "warnings": warnings,
        "ocr_profile": doc_result.get("ocr_profile"),
        "bounding_boxes": [],
    }


@router.post("/text")
async def ingest_text(request: TextIngestRequest) -> dict:
    """
    Ingests raw MTC or certificate text directly for parsing and validation.
    """
    cleaned = clean_text(request.raw_text)
    metadata = parse_mtc_certificate(cleaned)
    return {
        "filename": None,
        "raw_text": cleaned,
        "parsed_metadata": metadata,
        "confidence": 1.0,
        "extraction_method": "manual_text",
        "page_count": 1,
    }


@router.post("/catalog")
async def upload_catalog(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
):
    """
    Batch imports ERP inventory catalog CSV or Excel spreadsheet into plant stock ledger.
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

    # Normalize column names
    col_map = {c: c.lower().strip() for c in df.columns}
    df.rename(columns=col_map, inplace=True)

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
                cpse=str(row.get("cpse", "IOCL")).strip(),
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
                available_qty=int(row.get("available_qty", row.get("quantity", 1))),
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
    db: Session = Depends(get_db_session),
):
    """
    Lists ingested documents from the sovereign intake ledger.
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
    db: Session = Depends(get_db_session),
):
    """
    Retrieves full parsed metadata and extraction results for an ingested document.
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
