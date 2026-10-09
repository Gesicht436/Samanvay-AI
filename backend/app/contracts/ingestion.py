from typing import Any

from pydantic import BaseModel, Field


class ChemicalComposition(BaseModel):
    element: str
    value: float | None = None
    unit: str | None = None


class MechanicalProperty(BaseModel):
    property: str
    value: float | None = None
    unit: str | None = None


class MTCRecord(BaseModel):
    doc_type: str = "MTC"
    cert_no: str | None = None
    po_no: str | None = None
    description: str | None = None
    standard: str | None = None
    material_grade: str | None = None
    heat_no: str | None = None
    qty: str | None = None
    chemical_composition: list[ChemicalComposition] = Field(default_factory=list)
    mechanical_properties: list[MechanicalProperty] = Field(default_factory=list)


class OCRPage(BaseModel):
    page: int
    text: str
    blocks: list[dict[str, Any]] = Field(default_factory=list)
    regions: list[dict[str, Any]] = Field(default_factory=list)
    extraction_method: str | None = None
    ocr_engine: str | None = None
    raster_dpi: int | None = None


class IngestResponse(BaseModel):
    filename: str | None
    source_type: str
    extraction_method: str
    raw_text: str
    text: str
    pages: list[OCRPage] = Field(default_factory=list)
    mtc: MTCRecord


class OCRProfile(BaseModel):
    routing: str
    raster_dpi: int
    preprocessing: list[str]
    primary_engine: str
    fallback_engine: str
    mtc_intelligence: bool
    chemistry_extraction: bool


class DocumentIngestResponse(BaseModel):
    filename: str | None
    raw_text: str
    parsed_metadata: dict[str, Any]
    confidence: float
    extraction_method: str
    page_count: int
    pages: list[OCRPage] = Field(default_factory=list)
    ocr_profile: OCRProfile
    mtc: MTCRecord | None = None
    chemistry: dict[str, float | str | None] | None = None
    astm_conformance: dict[str, Any] | None = None
    requires_hitl: bool = False
