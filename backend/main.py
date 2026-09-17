"""
Samanvay-AI FastAPI Application Entrypoint.

Production-grade REST gateway with Pydantic v2, CORS middleware,
lifespan management, and clean router registration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.models.base import init_db
from backend.app.api.routers import ingest, match, inventory, requisition, graph, audit


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialize DB tables on startup."""
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Samanvay-AI: Sovereign AI-Powered Cross-CPSE Spare Parts Discovery "
        "& Compatibility Platform for MoPNG (SIH26099)"
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Router Registration ───────────────────────────────────────────────
app.include_router(ingest.router, prefix=settings.api_v1_prefix, tags=["Ingestion"])
app.include_router(match.router, prefix=settings.api_v1_prefix, tags=["Matching"])
app.include_router(inventory.router, prefix=settings.api_v1_prefix, tags=["Inventory"])
app.include_router(requisition.router, prefix=settings.api_v1_prefix, tags=["Requisition"])
app.include_router(graph.router, prefix=settings.api_v1_prefix, tags=["Graph"])
app.include_router(audit.router, prefix=settings.api_v1_prefix, tags=["Audit"])


@app.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }
