from pydantic import BaseModel


class DashboardOCRStatus(BaseModel):
    routing: str
    raster_dpi: int
    preprocessing: list[str]
    primary_engine: str
    primary_engine_ready: bool
    fallback_engine: str
    fallback_engine_ready: bool
    mtc_intelligence: bool
    chemistry_extraction: bool
    manufacturer_tpi_extraction: bool


class DashboardCapabilities(BaseModel):
    industry_metadata: bool
    mtc_chemistry: bool
    named_vector_domains: list[str]
    active_learning: bool


class DashboardSummary(BaseModel):
    vector_search: dict[str, bool | str]
    embedding_model_ready: bool
    reranker_model_ready: bool
    pending_reviews: int
    resolved_reviews: int
    review_capacity: int
    capabilities: DashboardCapabilities
    ocr: DashboardOCRStatus
