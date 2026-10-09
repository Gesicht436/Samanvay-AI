"""Public document-ingestion contract used by the API and UI."""

import re
from typing import Any

from .certificate import _number, mechanical_table_values, parse_mtc

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}


def clean_text(raw_text: str) -> str:
	"""Normalize text without discarding record boundaries used by the parser."""
	cleaned = raw_text.replace("\u00d7", "x").replace("\u2033", '"').replace("\u2019", "'")
	# A certificate generally has one labelled value per line. Collapsing every
	# whitespace character made a field such as Grade consume the full document.
	lines = [re.sub(r"[ \t\f\v]+", " ", line).strip() for line in cleaned.splitlines()]
	return "\n".join(line for line in lines if line).strip()


def _labelled_values(raw_text: str, pattern: str, primary: str | None) -> list[str]:
	values = [
		match.group(1).strip(" \t:;,.")
		for match in re.finditer(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
	]
	if primary:
		values.insert(0, primary)
		unique: dict[str, str] = {}
		for value in values:
			if value:
				unique.setdefault(value.casefold(), value)
		return list(unique.values())
	unique = {}
	for value in values:
		if value:
			unique.setdefault(value.casefold(), value)
	return list(unique.values())


def parse_mtc_certificate(raw_text: str) -> dict[str, Any]:
	"""Return the stable metadata shape consumed by the ingest dashboard."""
	record = parse_mtc(raw_text)
	mechanical = mechanical_table_values(raw_text)
	from machine_learning.ner_tagger import extract_attributes

	attributes = extract_attributes(raw_text).model_dump(exclude={"raw_description"})
	manufacturer_list = _labelled_values(
		raw_text,
		r"\b(?:MANUFACTURER|MFR\.?|MAKE)\s*[:#-]?\s*(.+?)(?=\s+(?:PRODUCT\s+FORM|COATING|INSPECTION\s+CLASS|TPI|INSPECTION\s+AGENCY|DOCUMENT\s+NO|PROJECT|END\s+CONNECTION|TEMPERATURE|P\.?O\.?|CERTIFICATE|BID)|\r?$)",
		attributes.get("manufacturer"),
	)
	tpi_list = _labelled_values(
		raw_text,
		r"\b(?:TPI|INSPECTION\s+AGENCY)\s*[:#-]?\s*(.+?)(?=\s+(?:INSPECTION\s+CLASS|DOCUMENT\s+NO|PROJECT|MANUFACTURER|MFR\.?|MAKE|END\s+CONNECTION|TEMPERATURE|P\.?O\.?|CERTIFICATE|BID)|\r?$)",
		attributes.get("inspection_agency"),
	)
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
		"chemical_composition": [item.model_dump() for item in record.chemical_composition],
	    "mechanical_properties": [item.model_dump() for item in record.mechanical_properties],
	    "engineering_attributes": attributes,
		"manufacturer_list": manufacturer_list,
		"tpi_list": tpi_list,
	}


def _confidence(extraction_method: str) -> float:
	return {"native_pdf": 1.0, "manual_text": 1.0, "ocr_image": 0.82, "hybrid_ocr": 0.75}.get(extraction_method, 0.7)


def process_document(file_bytes: bytes, filename: str) -> dict[str, Any]:
	"""Process an in-memory document while keeping the established API method names."""
	from .document import ingest_document

	result = ingest_document(file_bytes, filename)
	payload = result.model_dump(mode="json")
	if payload["extraction_method"] == "pymupdf":
		payload["extraction_method"] = "native_pdf"
	elif payload["extraction_method"] in {"paddleocr", "easyocr"}:
		payload["extraction_method"] = "ocr_image"
	return payload


def run_ocr(image_bytes: bytes, min_confidence: float = 0.60) -> tuple[str, float]:
	"""Run the existing OCR engine for a single image payload."""
	from OCR import extract_document

	extraction = extract_document(image_bytes, "upload.png")
	confidence = _confidence("ocr_image")
	return (extraction.raw_text, confidence) if confidence >= min_confidence else ("", confidence)
