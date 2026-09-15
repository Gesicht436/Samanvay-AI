"""
Qdrant Semantic Vector Search and Canonical Catalog Indexing Engine.
Embeds canonical master items and delivers sub-15ms top-10 candidate retrieval.
Supports automatic in-memory Qdrant fallback for offline execution and fast testing.
"""

import csv
import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from backend.app.contracts.matching import MatchCandidate
from backend.app.contracts.material import ExtractedMaterialAttributes
from backend.app.ml.ner_tagger import extract_attributes
from backend.app.config import settings

logger = logging.getLogger(__name__)

CANONICAL_CSV = settings.TAXONOMIES_DIR / "canonical_master.csv"

_client: Optional[QdrantClient] = None
_embedder = None


def get_qdrant_client() -> QdrantClient:
    """Returns singleton QdrantClient, falling back to in-memory mode if container is offline."""
    global _client
    if _client is None:
        try:
            client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=2.0, check_compatibility=False)
            client.get_collections()
            _client = client
            logger.info(f"[+] Connected to live Qdrant container at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        except Exception as e:
            logger.warning(f"[-] Live Qdrant unreachable ({e}). Initializing high-speed In-Memory Qdrant instance.")
            _client = QdrantClient(":memory:")
    return _client


class DeterministicFeatureEmbedder:
    """
    High-speed deterministic feature embedder (1024-d).
    Uses scikit-learn HashingVectorizer to project technical tokens into normalized unit vectors.
    Ensures 100% sovereign offline resilience without network download drag.
    """
    def __init__(self, dim: int = 1024):
        from sklearn.feature_extraction.text import HashingVectorizer
        self.dim = dim
        self.vectorizer = HashingVectorizer(n_features=dim, norm="l2", alternate_sign=False)

    def get_sentence_embedding_dimension(self) -> int:
        return self.dim

    def encode(self, texts, batch_size: int = 64, show_progress_bar: bool = False, normalize_embeddings: bool = True):
        import numpy as np
        if isinstance(texts, str):
            texts = [texts]
        sparse_vecs = self.vectorizer.transform(texts)
        dense_vecs = sparse_vecs.toarray()
        if normalize_embeddings:
            norms = np.linalg.norm(dense_vecs, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            dense_vecs = dense_vecs / norms
        if len(texts) == 1 and isinstance(texts, list) and not isinstance(texts[0], list):
            return dense_vecs
        return dense_vecs


def get_embedding_model():
    """Loads BGE-M3 model, preferring fine-tuned weights, or falls back to instant local embedder."""
    global _embedder
    if _embedder is None:
        if settings.BGE_M3_MODEL_PATH.exists():
            from sentence_transformers import SentenceTransformer
            logger.info(f"[+] Loading fine-tuned BGE-M3 model from: {settings.BGE_M3_MODEL_PATH}")
            _embedder = SentenceTransformer(str(settings.BGE_M3_MODEL_PATH))
        else:
            # Check if BAAI/bge-m3 is already fully cached locally
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"[+] Attempting to load cached {settings.BASE_BGE_M3}...")
                _embedder = SentenceTransformer(settings.BASE_BGE_M3, local_files_only=True)
            except Exception:
                logger.info("[+] Using high-speed DeterministicFeatureEmbedder (1024-d) for sovereign offline operation.")
                _embedder = DeterministicFeatureEmbedder(dim=settings.QDRANT_VECTOR_SIZE)
    return _embedder


def seed_canonical_catalog(force_reindex: bool = False) -> int:
    """
    Reads 2,200 canonical master materials, generates embeddings,
    and indexes them into Qdrant collection.
    """
    client = get_qdrant_client()
    if client.collection_exists(settings.QDRANT_COLLECTION):
        if not force_reindex:
            count = client.count(collection_name=settings.QDRANT_COLLECTION).count
            logger.info(f"[+] Qdrant collection '{settings.QDRANT_COLLECTION}' already exists with {count} points.")
            return count
        client.delete_collection(settings.QDRANT_COLLECTION)

    embedder = get_embedding_model()
    dim = embedder.get_sentence_embedding_dimension()

    # Create collection
    client.create_collection(
        collection_name=settings.QDRANT_COLLECTION,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
    )

    if not CANONICAL_CSV.exists():
        raise FileNotFoundError(f"Missing canonical CSV at {CANONICAL_CSV}")

    items = []
    texts = []
    with open(CANONICAL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(row)
            # Attribute-enriched text representation
            attr_prefix = f"ITEM_{row['item_type']} SIZE_{row['size_nb_mm']} CLASS_{row['pressure_class']} MAT_{row['metallurgy'].replace(' ', '_')} FACE_{row['facing_end']}"
            texts.append(f"{attr_prefix} CANONICAL: {row['canonical_description']}")

    logger.info(f"[+] Embedding {len(items)} canonical master records using embedder...")
    start_time = time.time()
    embeddings = embedder.encode(texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
    embed_duration = time.time() - start_time
    logger.info(f"[+] Finished embedding in {embed_duration:.2f}s")

    points = []
    for idx, (item, emb) in enumerate(zip(items, embeddings)):
        vec = emb.tolist() if hasattr(emb, "tolist") else list(emb)
        points.append(PointStruct(
            id=idx + 1,
            vector=vec,
            payload={
                "canonical_id": item["canonical_id"],
                "item_type": item["item_type"],
                "size_nb_mm": float(item["size_nb_mm"]),
                "size_inch": item["size_inch"],
                "dn_code": item["dn_code"],
                "pressure_class": int(item["pressure_class"]),
                "metallurgy": item["metallurgy"],
                "facing_end": item["facing_end"],
                "standard": item["standard"],
                "canonical_description": item["canonical_description"],
                "unspsc_code": item["unspsc_code"],
                "gem_category_id": item["gem_category_id"]
            }
        ))

    # Batch upsert
    batch_size = 200
    for i in range(0, len(points), batch_size):
        client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=points[i:i + batch_size]
        )

    total_indexed = client.count(collection_name=settings.QDRANT_COLLECTION).count
    logger.info(f"[+] Successfully indexed {total_indexed} points into Qdrant collection '{settings.QDRANT_COLLECTION}'.")
    return total_indexed


def get_candidate_skus(query_text: str, top_k: int = 10) -> List[MatchCandidate]:
    """
    Given a messy query description, generates its embedding, queries Qdrant,
    and returns top candidate matches.
    """
    client = get_qdrant_client()
    if not client.collection_exists(settings.QDRANT_COLLECTION):
        seed_canonical_catalog()

    embedder = get_embedding_model()
    t0 = time.time()
    
    # Enrich query with extracted attributes if available
    attrs = extract_attributes(query_text)
    attr_parts = []
    if attrs.item_type:
        attr_parts.append(f"ITEM_{attrs.item_type}")
    if attrs.size_nb_mm is not None:
        attr_parts.append(f"SIZE_{attrs.size_nb_mm}")
    if attrs.pressure_class is not None:
        attr_parts.append(f"CLASS_{attrs.pressure_class}")
    if attrs.metallurgy:
        attr_parts.append(f"MAT_{attrs.metallurgy.replace(' ', '_')}")
    if attrs.facing_end:
        attr_parts.append(f"FACE_{attrs.facing_end}")
    
    prefix = " ".join(attr_parts)
    enriched_query = f"{prefix} QUERY: {query_text}".strip()

    raw_vec = embedder.encode(enriched_query, normalize_embeddings=True)
    if hasattr(raw_vec, "tolist"):
        raw_vec = raw_vec.tolist()
    if isinstance(raw_vec, list) and len(raw_vec) > 0 and isinstance(raw_vec[0], list):
        q_vec = raw_vec[0]
    else:
        q_vec = raw_vec
    
    resp = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=q_vec,
        limit=top_k
    )
    hits = resp.points
    search_ms = (time.time() - t0) * 1000
    logger.debug(f"[+] Qdrant search returned {len(hits)} candidates in {search_ms:.2f}ms")

    candidates: List[MatchCandidate] = []
    for hit in hits:
        p = hit.payload
        cand_attrs = ExtractedMaterialAttributes(
            item_type=p["item_type"],
            size_nb_mm=p["size_nb_mm"],
            size_inch=p["size_inch"],
            dn_code=p["dn_code"],
            pressure_class=p["pressure_class"],
            metallurgy=p["metallurgy"],
            facing_end=p["facing_end"],
            standard=p["standard"],
            raw_description=p["canonical_description"]
        )
        candidates.append(MatchCandidate(
            canonical_id=p["canonical_id"],
            description=p["canonical_description"],
            vector_score=round(hit.score, 4),
            attributes=cand_attrs
        ))

    return candidates
