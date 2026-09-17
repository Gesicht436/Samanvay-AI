from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.app.api.dependencies import get_db_session

router = APIRouter(prefix="/ingest", tags=["Ingest"])

@router.post("/document")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    # Placeholder for OCR extraction returning ExtractedMaterialAttributes
    return {"filename": file.filename, "extracted_attributes": {}}

@router.post("/catalog")
async def upload_catalog(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    # Placeholder for Batch import CSV/Excel ERP catalog
    return {"filename": file.filename, "status": "Batch import started"}

@router.get("/documents")
def list_documents(skip: int = 0, limit: int = 10, db: Session = Depends(get_db_session)):
    return {"skip": skip, "limit": limit, "documents": []}

@router.get("/documents/{doc_id}")
def get_document(doc_id: str, db: Session = Depends(get_db_session)):
    return {"id": doc_id, "metadata": {}}
