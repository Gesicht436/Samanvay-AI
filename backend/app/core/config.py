"""
Samanvay-AI Core Configuration.

Pydantic BaseSettings for all DB connections, ML model paths,
engineering thresholds, and runtime SLA parameters.
All values are sourced from environment variables or .env files.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, model_validator
from typing import Optional


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

    # ── Server-side Session Authentication (AUTH-005 / AUTH-006) ──
    # NOTE: absolute session expiry, idle/session policy, concurrency and
    # retention are deployment/product inputs and are NOT fixed by the frozen
    # architecture. The value below is a configurable default.
    app_env: str = Field(default="development", alias="APP_ENV")
    session_absolute_expire_minutes: int = Field(
        default=720, alias="SESSION_ABSOLUTE_EXPIRE_MINUTES"
    )
    # None => derived: Secure in production, insecure local HTTP development only.
    session_cookie_secure: Optional[bool] = Field(
        default=None, alias="SESSION_COOKIE_SECURE"
    )
    # Comma-separated explicit Origin allowlist for CSRF Origin validation.
    # Production browser origin is an open deployment value.
    auth_allowed_origins: str = Field(default="", alias="AUTH_ALLOWED_ORIGINS")
    # Login rate-limit thresholds (AUTH-006 Section 8). Defaults preserve the
    # existing behavior: 10 attempts per 60-second fixed window per username.
    # Values below 1 are rejected as nonsensical.
    auth_login_rate_limit_attempts: int = Field(
        default=10, ge=1, le=1000, alias="AUTH_LOGIN_RATE_LIMIT_ATTEMPTS"
    )
    auth_login_rate_limit_window_seconds: int = Field(
        default=60, ge=1, le=3600, alias="AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS"
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def is_production(self) -> bool:
        """True when APP_ENV indicates a production deployment."""
        return self.app_env.strip().lower() in ("production", "prod")

    @property
    def session_cookie_name(self) -> str:
        """AUTH-006 Section 3: production uses the __Host- prefixed cookie."""
        return "__Host-samanvay_session" if self.is_production else "samanvay_session"

    @property
    def cookie_secure(self) -> bool:
        """Production is always Secure; local HTTP development may be insecure."""
        if self.is_production:
            return True
        return bool(self.session_cookie_secure)

    @property
    def allowed_origins_list(self) -> list:
        """Explicit configured Origin allowlist (never derived from Host headers)."""
        configured = [
            o.strip() for o in self.auth_allowed_origins.split(",") if o.strip()
        ]
        if configured:
            return configured
        return ["http://localhost:3000", "http://localhost:3001"]

    @model_validator(mode="after")
    def _reject_insecure_production_cookie(self):
        """Production must reject an insecure cookie configuration."""
        if self.is_production and self.session_cookie_secure is False:
            raise ValueError(
                "SESSION_COOKIE_SECURE cannot be disabled in a production deployment"
            )
        return self


settings = Settings()
