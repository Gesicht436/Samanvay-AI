"""
Samanvay-AI Core Configuration.

Pydantic BaseSettings for all DB connections, ML model paths,
engineering thresholds, and runtime SLA parameters.
All values are sourced from environment variables or .env files.

Production Security Policy (Neo4j)
------------------------------------
In production (``debug=False``) the Neo4j password must NOT be the
known default value ``"neo4j"``.  If the default is detected at startup
the application raises ``ValueError`` immediately.

This check intentionally does NOT log the password value.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, model_validator
from typing import Optional


# The Neo4j factory default password that must never reach production.
_NEO4J_DEFAULT_PASSWORD: str = "neo4j"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ──────────────────────────────────────────────
    app_name: str = "Samanvay-AI"
    app_version: str = "2.0.0-PROD"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # ── PostgreSQL 16 ────────────────────────────────────────────
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="samanvay", alias="POSTGRES_USER")
    postgres_password: str = Field(default="samanvay_secure", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="samanvay_db", alias="POSTGRES_DB")

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Qdrant Vector Database ───────────────────────────────────
    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_collection: str = "samanvay_inventory"
    qdrant_vector_size: int = 1024  # BAAI/bge-m3 dense dimension
    qdrant_hnsw_m: int = 16
    qdrant_hnsw_ef_construct: int = 100

    # ── Neo4j Graph Database ─────────────────────────────────────
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="samanvay_graph", alias="NEO4J_PASSWORD")

    # ── Neo4j Driver Reliability Settings ────────────────────────
    # These map to supported neo4j-python-driver keyword arguments.
    # connection_timeout: seconds to wait for a TCP connection.
    # max_connection_lifetime: seconds before a pooled connection is recycled.
    # max_connection_pool_size: upper bound on concurrent connections.
    # connection_acquisition_timeout: seconds to wait for a free slot from pool.
    neo4j_connection_timeout: int = Field(default=15, alias="NEO4J_CONNECTION_TIMEOUT")
    neo4j_max_connection_lifetime: int = Field(default=3600, alias="NEO4J_MAX_CONNECTION_LIFETIME")
    neo4j_max_connection_pool_size: int = Field(default=50, alias="NEO4J_MAX_CONNECTION_POOL_SIZE")
    neo4j_connection_acquisition_timeout: int = Field(
        default=60, alias="NEO4J_CONNECTION_ACQUISITION_TIMEOUT"
    )

    # ── ML Model Paths (Air-Gapped Local Inference) ──────────────
    deberta_model_path: str = "ml/ner/models/deberta-v3-small-ner"
    bge_m3_model_path: str = "ml/embeddings/models/bge-m3-onnx"
    xgboost_model_path: str = "ml/ranking/models/compatibility_ranker.json"

    # ── OCR Configuration ────────────────────────────────────────
    ocr_dpi: int = 300
    ocr_confidence_threshold: float = 0.85  # τ_OCR per spec §3.6.2
    ocr_max_concurrency: int = 4  # asyncio.Semaphore bound

    # ── ML Inference SLAs ────────────────────────────────────────
    vector_search_sla_ms: float = 15.0
    pymupdf_sla_ms: float = 50.0
    paddleocr_sla_ms: float = 250.0

    # ── Dynamic Batching ─────────────────────────────────────────
    max_batch_size: int = 8
    batch_timeout_ms: float = 25.0

    # ── ONNX Runtime ─────────────────────────────────────────────
    onnx_intra_op_threads: int = 4
    onnx_inter_op_threads: int = 2

    # ── Compatibility Thresholds (Per Spec §3.3.3) ───────────────
    tier_1_threshold: float = 0.95  # >= 95% → Tier 1 Identical
    tier_2_threshold: float = 0.80  # >= 80% → Tier 2 Substitute
    # < 80% → Tier 3 Incompatible

    # ── Carbon Equivalent Threshold (IIW §3.1) ──────────────────
    ce_weldability_limit: float = 0.43

    # ── GIS Logistics ────────────────────────────────────────────
    road_tortuosity_factor: float = 1.28
    avg_freight_speed_kmh: float = 40.0

    # ── Audit Ledger ─────────────────────────────────────────────
    genesis_root_hash: str = "0" * 64  # GENESIS_ROOT_64_HEX

    # ── Idempotency ──────────────────────────────────────────────
    idempotency_ttl_hours: int = 24

    # ── Dataset Paths ────────────────────────────────────────────
    inventory_catalog_path: str = "datasets/inventory_catalog.csv"
    golden_benchmarks_path: str = "datasets/golden_benchmarks.json"
    ocr_payloads_path: str = "datasets/ocr_payloads.json"

    # ── JWT Authentication & RBAC ────────────────────────────────
    jwt_secret_key: str = Field(
        default="samanvay_ai_sovereign_mopng_oil_jwt_secret_key_2026_super_secure_sha256",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 Hours

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # ── Production Security Validation ──────────────────────────
    @model_validator(mode="after")
    def _reject_default_neo4j_password_in_production(self) -> "Settings":
        """
        Raises ValueError when the Neo4j password is the factory default
        ('neo4j') and the application is NOT running in debug/dev mode.

        This prevents accidental deployment of a publicly-known credential.
        The password value is never included in the error message.
        """
        if not self.debug and self.neo4j_password == _NEO4J_DEFAULT_PASSWORD:
            raise ValueError(
                "Insecure Neo4j configuration: the Neo4j password is set to the "
                "factory default value which is not permitted in production "
                "(debug=False). Set a strong NEO4J_PASSWORD environment variable "
                "or enable debug=True for local development."
            )
        return self


settings = Settings()
