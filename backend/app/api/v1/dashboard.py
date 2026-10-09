from importlib.util import find_spec
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.app.api.deps import get_vector_searcher
from backend.app.config import get_settings
from backend.app.contracts.dashboard import DashboardSummary
from machine_learning.active_learning import get_active_learning_queue
from machine_learning.subvectors import encode_subvectors
from OCR.pipeline import OCR_PREPROCESSING, OCR_ROUTING, RASTER_DPI

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary() -> dict[str, Any]:
    settings = get_settings()
    queue = get_active_learning_queue()
    model_ready = Path(settings.model_weights_path).is_dir()
    vector_search = {"ready": False, "message": "Matching model or vector database is unavailable"}
    if not model_ready:
        vector_search["message"] = "Embedding model is not installed"
    else:
        try:
            searcher = get_vector_searcher()
            if searcher.client.collection_exists(settings.qdrant_collection):
                from machine_learning.subvectors import DOMAINS

                vectors = encode_subvectors(
                    {"canonical_description": "readiness probe material"},
                    searcher.encoder,
                )
                searcher.client.query_points(
                    collection_name=settings.qdrant_collection,
                    query=vectors[DOMAINS[0]],
                    using=DOMAINS[0],
                    limit=1,
                )
                vector_search = {"ready": True, "message": "Vector search is operational"}
            else:
                vector_search["message"] = "Vector index has not been built yet"
        except HTTPException as exc:
            model_ready = False
            vector_search["message"] = str(exc.detail)
        except (OSError, RuntimeError, ValueError):
            vector_search["message"] = "Vector index is not queryable"

    return {
        "vector_search": vector_search,
        "embedding_model_ready": model_ready,
        "reranker_model_ready": Path("machine_learning/model_weights/reranker.xgb").is_file(),
        "pending_reviews": len(queue.list_items()),
        "resolved_reviews": len(queue.training_examples()),
        "review_capacity": queue.capacity,
        "capabilities": {
            "industry_metadata": True,
            "mtc_chemistry": True,
            "named_vector_domains": ["dim", "met", "pt", "std"],
            "active_learning": True,
        },
        "ocr": {
            "routing": OCR_ROUTING,
            "raster_dpi": RASTER_DPI,
            "preprocessing": list(OCR_PREPROCESSING),
            "primary_engine": "PaddleOCR",
            "primary_engine_ready": find_spec("paddleocr") is not None,
            "fallback_engine": "EasyOCR",
            "fallback_engine_ready": find_spec("easyocr") is not None,
            "mtc_intelligence": True,
            "chemistry_extraction": True,
            "manufacturer_tpi_extraction": True,
        },
    }
