"""
Application Settings & Environment Configuration for Samanvay-AI.
Uses Pydantic Settings with automatic .env loading and sensible defaults.
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Application
    PROJECT_NAME: str = "Samanvay-AI (BharatCodex)"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # PostgreSQL Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "samanvay_db"
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/samanvay_db"
    SQLITE_FALLBACK_URL: str = f"sqlite:///{BASE_DIR}/samanvay_local.db"

    # Qdrant Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_COLLECTION: str = "canonical_materials"
    QDRANT_VECTOR_SIZE: int = 1024

    # Neo4j Knowledge Graph
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Data Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    MOCK_CATALOGS_DIR: Path = BASE_DIR / "data" / "mock_cpes_catalogs"
    TAXONOMIES_DIR: Path = BASE_DIR / "data" / "taxonomies"

    # ML Model Checkpoint Paths
    MODEL_DIR: Path = BASE_DIR / "backend" / "app" / "ml" / "model_weights"
    BGE_M3_MODEL_PATH: Path = BASE_DIR / "backend" / "app" / "ml" / "model_weights" / "bge_m3_cpes"
    NER_MODEL_PATH: Path = BASE_DIR / "backend" / "app" / "ml" / "model_weights" / "ner_deberta"
    BASE_BGE_M3: str = "BAAI/bge-m3"
    BASE_DEBERTA: str = "microsoft/deberta-v3-small"

    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]


settings = Settings()
