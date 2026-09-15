"""
FastAPI Dependency Injection Providers for Sessions and Database Connections.
"""

from typing import Generator, Optional
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from neo4j import Session as Neo4jSession
from backend.app.ingestion.storage import get_db
from backend.app.ml.vector_search import get_qdrant_client
from backend.app.graph.client import get_neo4j_session

__all__ = [
    "get_db",
    "get_qdrant_client",
    "get_neo4j_session",
]
