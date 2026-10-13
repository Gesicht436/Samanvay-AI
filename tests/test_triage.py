"""Unit tests for document triage and classification logic."""

import fitz
import pytest
from ml.vision.exceptions import (
    CorruptFileError,
    EncryptedFileError,
    PageLimitExceededError,
    UnsupportedFormatError,
)
from ml.vision.triage import inspect_document, verify_file_integrity


def test_empty_file_raises_corrupt_error():
    with pytest.raises(CorruptFileError, match="Input file is empty"):
        verify_file_integrity(b"")


def test_unsupported_magic_bytes_raises():
    with pytest.raises(UnsupportedFormatError, match="Unsupported file format"):
        verify_file_integrity(b"INVALID_HEADER_DATA")


def test_valid_pdf_classification():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "EN 10204 3.1 Inspection Certificate Material Test Report Grade ASTM A105 Heat H-99128")
    pdf_bytes = doc.tobytes()
    doc.close()

    result = inspect_document(pdf_bytes)
    assert result["format"] == "pdf"
    assert result["page_count"] == 1
    assert result["pages"][0]["type"] == "digital_vector"


def test_scanned_pdf_page_classification():
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()

    result = inspect_document(pdf_bytes)
    assert result["pages"][0]["type"] == "scanned_raster"
