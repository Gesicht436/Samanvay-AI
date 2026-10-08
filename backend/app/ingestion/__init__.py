from ocr_engine_unified import normalize_text 
"""Public document-ingestion contract used by the API and UI."""

import re
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .certificate import _number, mechanical_table_values, parse_mtc
from .pdf_parser import extract_pdf_text


ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}


def clean_text(raw_text: str) -> str:
	"""Normalize text without discarding record boundaries used by the parser."""
	cleaned = raw_text.replace("\u00d7", "x").replace("\u2033", '"').replace("\u2019", "'")
	# A certificate generally has one labelled value per line. Collapsing every
	# whitespace character made a field such as Grade consume the full document.
	lines = [re.sub(r"[ \t\f\v]+", " ", line).strip() for line in cleaned.splitlines()]
	return "\n".join(line for line in lines if line).strip()


def parse_mtc_certificate(raw_text: str) -> dict[str, Any]:
	"""Return the stable metadata shape consumed by the ingest dashboard."""
	record = parse_mtc(normalize_text(raw_text))
	mechanical = mechanical_table_values(raw_text)
	return {
		"certificate_type": record.doc_type,
		"certificate_number": record.cert_no,
		"purchase_order": record.po_no,
		"material_grade": record.material_grade,
		"governing_standard": record.standard,
		"heat_numbers": [record.heat_no] if record.heat_no else [],
		"quantity": record.qty,
		"yield_strength_mpa": _number(raw_text, "yield strength (mpa)", "yield (mpa)", "yield strength", "yield") or mechanical.get("yield_strength_mpa"),
		"tensile_strength_mpa": _number(raw_text, "tensile strength (mpa)", "tensile (mpa)", "tensile strength", "tensile") or mechanical.get("tensile_strength_mpa"),
		"elongation_pct": _number(raw_text, "elongation (%)", "elongation") or mechanical.get("elongation_pct"),
		"product_description": record.description,
	}


def _confidence(extraction_method: str) -> float:
	return {"native_pdf": 1.0, "manual_text": 1.0, "ocr_image": 0.82, "hybrid_ocr": 0.75}.get(extraction_method, 0.7)


def process_document(file_bytes: bytes, filename: str) -> dict[str, Any]:
	"""Process a supported document using the existing PDF/OCR extraction primitives."""
	suffix = Path(filename).suffix.lower()
	if suffix not in ALLOWED_EXTENSIONS:
		raise ValueError("Unsupported file type. Use PDF, PNG, JPG, JPEG, TIFF, BMP, or WEBP.")
	temporary_path: str | None = None
	try:
		with NamedTemporaryFile(suffix=suffix, delete=False) as target:
			target.write(file_bytes)
			temporary_path = target.name
		if suffix == ".pdf":
			import fitz

			with fitz.open(temporary_path) as document:
				page_count = len(document)
				native_pages = sum(bool(page.get_text("words")) for page in document)
				if native_pages == page_count:
					raw_text = "\n\n".join(page.get_text("text").strip() for page in document).strip()
				else:
					raw_text = ""
			if native_pages != page_count:
				raw_text = extract_pdf_text(temporary_path)
			extraction_method = "native_pdf" if native_pages == page_count else "hybrid_ocr"
		else:
			from OCR import extract_document

			extraction = extract_document(temporary_path)
			raw_text = extraction.raw_text
			extraction_method = "ocr_image"
			page_count = 1
		cleaned = clean_text(raw_text)
		return {
			"filename": filename,
			"raw_text": cleaned,
			"parsed_metadata": parse_mtc_certificate(cleaned),
			"confidence": _confidence(extraction_method),
			"extraction_method": extraction_method,
			"page_count": page_count,
		}
	finally:
		if temporary_path:
			Path(temporary_path).unlink(missing_ok=True)


def run_ocr(image_bytes: bytes, min_confidence: float = 0.60) -> tuple[str, float]:
	"""Run the existing OCR engine for a single image payload."""
	from OCR import extract_document

	with NamedTemporaryFile(suffix=".png", delete=False) as target:
		target.write(image_bytes)
		path = Path(target.name)
	try:
		extraction = extract_document(path)
		confidence = _confidence("ocr_image")
		return (extraction.raw_text, confidence) if confidence >= min_confidence else ("", confidence)
	finally:
		path.unlink(missing_ok=True)
