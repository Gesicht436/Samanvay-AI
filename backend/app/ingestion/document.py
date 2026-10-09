"""Compose OCR, MTC parsing, chemistry checks, and the document API contract."""

import logging
import re
from pathlib import Path
from typing import Any

from backend.app.contracts.ingestion import (
    DocumentIngestResponse,
    MTCRecord,
    OCRPage,
    OCRProfile,
)
from OCR.pipeline import (
    OCR_PREPROCESSING,
    OCR_ROUTING,
    RASTER_DPI,
    DocumentExtraction,
    extract_document,
)

from .certificate import parse_mtc
from .chemistry import (
    astm_chemistry_conformance,
    carbon_equivalent_iiw,
    classify_weldability,
    composition_by_symbol,
    pren,
)

logger = logging.getLogger(__name__)
_ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}


def _empty_metadata() -> dict[str, Any]:
    return {
        "certificate_type": "MTC",
        "certificate_number": None,
        "purchase_order": None,
        "material_grade": None,
        "governing_standard": None,
        "heat_numbers": [],
        "quantity": None,
        "yield_strength_mpa": None,
        "tensile_strength_mpa": None,
        "elongation_pct": None,
        "product_description": None,
        "chemical_composition": [],
        "mechanical_properties": [],
        "engineering_attributes": {},
        "manufacturer_list": [],
        "tpi_list": [],
    }


def _is_mtc(record: MTCRecord) -> bool:
    return any(
        (
            record.cert_no,
            record.material_grade,
            record.heat_no,
            record.chemical_composition,
            record.mechanical_properties,
        )
    )


def _page_contract(page: dict[str, Any]) -> OCRPage:
    return OCRPage(
        page=page["page"],
        text=page["text"],
        blocks=page["blocks"],
        regions=page["regions"],
        extraction_method=page["extraction_method"],
        ocr_engine=page["ocr_engine"],
        raster_dpi=page["raster_dpi"],
    )


def _parsed_metadata(
    text: str,
    normalized_text: str,
    record: MTCRecord,
) -> dict[str, Any]:
    from machine_learning.ner_tagger import extract_attributes

    from . import parse_mtc_certificate

    metadata = parse_mtc_certificate(text)
    canonical_tokens = re.findall(
        r"\b(?:SIZE_NB_MM|SIZE_IN|CLASS)=\d+(?:\.\d+)?",
        normalized_text,
    )
    attribute_text = " ".join((text, *canonical_tokens))
    attributes = extract_attributes(attribute_text).model_dump(exclude={"raw_description"})
    metadata["engineering_attributes"] = attributes
    metadata["manufacturer_list"] = (
        [attributes["manufacturer"]] if attributes.get("manufacturer") else []
    )
    metadata["tpi_list"] = (
        [attributes["inspection_agency"]] if attributes.get("inspection_agency") else []
    )
    metadata["certificate_type"] = record.doc_type
    return metadata


def _empty_mtc_result(
    filename: str,
    raw_text: str,
    extraction: DocumentExtraction,
    pages: list[OCRPage],
    warning: str,
) -> DocumentIngestResponse:
    logger.warning("MTC parsing requires human review for %s: %s", filename, warning)
    return DocumentIngestResponse(
        filename=filename,
        raw_text=raw_text,
        parsed_metadata=_empty_metadata(),
        confidence=extraction.confidence,
        extraction_method=extraction.extraction_method,
        page_count=len(pages),
        pages=pages,
        ocr_profile=OCRProfile(
            routing=OCR_ROUTING,
            raster_dpi=RASTER_DPI,
            preprocessing=list(OCR_PREPROCESSING),
            primary_engine="paddleocr",
            fallback_engine="easyocr",
            mtc_intelligence=True,
            chemistry_extraction=True,
        ),
        astm_conformance={"conforming": False, "warnings": [warning]},
        chemistry={
            "carbon_equivalent_iiw": None,
            "weldability": None,
            "pren": None,
        },
        requires_hitl=True,
    )


def ingest_document(file_bytes: bytes, filename: str) -> DocumentIngestResponse:
    """Extract a document, parse its MTC content, and return chemistry and review results."""
    if Path(filename).suffix.lower() not in _ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type. Use PDF, PNG, JPG, JPEG, TIFF, BMP, or WEBP.")
    try:
        extraction = extract_document(file_bytes, filename)
    except Exception as exc:
        logger.exception("OCR failed for document %s", filename)
        raise RuntimeError(f"Document OCR failed: {exc}") from exc

    pages = [_page_contract(page) for page in extraction.pages]
    from . import clean_text

    raw_text = clean_text(extraction.raw_text)
    normalized_text = clean_text(extraction.normalized_text)
    try:
        record = parse_mtc(raw_text)
        if not _is_mtc(record):
            return _empty_mtc_result(
                filename,
                raw_text,
                extraction,
                pages,
                "No MTC fields or test results were recognized.",
            )
        metadata = _parsed_metadata(raw_text, normalized_text, record)
    except Exception as exc:
        logger.warning("MTC parser failed for %s: %s", filename, exc, exc_info=True)
        return _empty_mtc_result(
            filename,
            raw_text,
            extraction,
            pages,
            f"MTC parsing failed: {exc}",
        )

    composition = composition_by_symbol(record.chemical_composition)
    carbon_equivalent = carbon_equivalent_iiw(composition)
    conforming, warnings = astm_chemistry_conformance(
        composition,
        record.material_grade,
    )
    chemistry = {
        "carbon_equivalent_iiw": carbon_equivalent,
        "weldability": classify_weldability(carbon_equivalent),
        "pren": pren(composition),
    }
    return DocumentIngestResponse(
        filename=filename,
        raw_text=raw_text,
        parsed_metadata=metadata,
        confidence=extraction.confidence,
        extraction_method=extraction.extraction_method,
        page_count=len(pages),
        pages=pages,
        ocr_profile=OCRProfile(
            routing=OCR_ROUTING,
            raster_dpi=RASTER_DPI,
            preprocessing=list(OCR_PREPROCESSING),
            primary_engine="paddleocr",
            fallback_engine="easyocr",
            mtc_intelligence=True,
            chemistry_extraction=True,
        ),
        mtc=record,
        chemistry=chemistry,
        astm_conformance={"conforming": conforming, "warnings": warnings},
        requires_hitl=not conforming,
    )
