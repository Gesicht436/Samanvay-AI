from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException

from backend.app.config import get_settings


@lru_cache(maxsize=1)
def get_vector_searcher():
    from machine_learning.vector_search import VectorSearcher

    try:
        import httpx
        from qdrant_client import QdrantClient
        from qdrant_client.http.exceptions import ResponseHandlingException
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Install the optional vector-search dependencies to enable matching",
        ) from exc

    settings = get_settings()
    model_path = Path(settings.model_weights_path)
    if not model_path.is_dir():
        raise HTTPException(status_code=503, detail="Embedding model is not installed")

    try:
        encoder = SentenceTransformer(str(model_path), device="cpu")
    except OSError as exc:
        raise HTTPException(status_code=503, detail="Embedding model could not be loaded") from exc

    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port, timeout=1)
    try:
        client.get_collections()
    except (httpx.HTTPError, OSError, ResponseHandlingException):
        client.close()
        local_path = Path(settings.qdrant_local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        client = QdrantClient(path=str(local_path))

    return VectorSearcher(client=client, encoder=encoder)


def audit_context() -> Generator[dict[str, str], None, None]:
    yield {"actor": "anonymous", "action": "request"}
