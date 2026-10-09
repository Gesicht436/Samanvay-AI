from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_local_path: str = "data/qdrant_local"
    qdrant_collection: str = "canonical_materials"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "change-me"
    postgres_dsn: str = "postgresql+psycopg://samanvay:samanvay@localhost:5432/samanvay"
    model_weights_path: str = "machine_learning/model_weights/bge_m3_cpes"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
