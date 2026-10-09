from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.app.contracts.ingestion import DocumentIngestResponse
from backend.app.ingestion import clean_text, parse_mtc_certificate, process_document

router = APIRouter()


MAX_UPLOAD_BYTES = 15 * 1024 * 1024


class TextIngestRequest(BaseModel):
    raw_text: str = Field(min_length=1)


@router.post("/document", response_model=DocumentIngestResponse)
async def ingest_document(file: UploadFile = File(...)) -> dict:
    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large. Maximum upload size is 15 MB.")
    try:
        return process_document(contents, file.filename or "upload.pdf")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=f"Document needs OCR but OCR support is unavailable: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The selected document could not be read. Upload a valid PDF or image.") from exc


@router.post("/text")
async def ingest_text(request: TextIngestRequest) -> dict:
    cleaned = clean_text(request.raw_text)
    return {
        "filename": None,
        "raw_text": cleaned,
        "parsed_metadata": parse_mtc_certificate(cleaned),
        "confidence": 1.0,
        "extraction_method": "manual_text",
        "page_count": 1,
    }
