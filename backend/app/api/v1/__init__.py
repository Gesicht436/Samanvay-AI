from fastapi import APIRouter
from backend.app.api.v1.ingest import router as ingest_router
from backend.app.api.v1.match import router as match_router
from backend.app.api.v1.graph import router as graph_router
from backend.app.api.v1.requisition import router as requisition_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.inventory import router as inventory_router

api_v1_router = APIRouter()
api_v1_router.include_router(ingest_router)
api_v1_router.include_router(match_router)
api_v1_router.include_router(graph_router)
api_v1_router.include_router(requisition_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(inventory_router)

__all__ = ["api_v1_router"]

