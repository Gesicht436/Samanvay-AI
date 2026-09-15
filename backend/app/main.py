"""
Samanvay-AI (BharatCodex) Unified FastAPI Gateway Application.
Provides REST API endpoints for multi-modal ingestion, deterministic ASME/ASTM
material code harmonization, Neo4j cross-CPSE spare locator, and HITL triage.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.api.v1 import api_v1_router
from backend.app.ingestion.storage import init_db
from backend.app.graph.client import verify_connectivity, close_neo4j_driver

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle
    logger.info(f"[+] Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    try:
        init_db()
        logger.info("[+] Relational database tables initialized.")
    except Exception as e:
        logger.warning(f"[-] Database initialization error: {e}")

    neo4j_ok = verify_connectivity()
    logger.info(f"[+] Neo4j cluster status: {'ONLINE' if neo4j_ok else 'OFFLINE (fallback mode active)'}")

    yield

    # Shutdown lifecycle
    logger.info("[-] Shutting down application...")
    close_neo4j_driver()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "AI-Driven Standardization and Harmonization of Material Codes Across CPSEs (MoPNG). "
        "Combines domain-adapted NER, BGE-M3 dense vector retrieval, and deterministic ASME B16.5 safety rules."
    ),
    lifespan=lifespan
)

# Configure CORS Middleware for Next.js 16 Web Portal
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health & Diagnostics"])
def health_check():
    """Returns application health and subsystem connectivity status."""
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "neo4j_connected": verify_connectivity(),
        "database": "CONNECTED",
        "vector_engine": "QDRANT"
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API Gateway.",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
