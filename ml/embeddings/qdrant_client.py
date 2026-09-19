import os
from typing import List, Dict, Any

try:
    from backend.app.core.config import settings
except ImportError:
    class Settings:
        QDRANT_HOST = "localhost"
        QDRANT_PORT = 6333
        QDRANT_COLLECTION = "inventory"
    settings = Settings()

import uuid

class SamanvayQdrantClient:
    def __init__(self):
        self.collection_name = getattr(settings, "qdrant_collection", None) or getattr(settings, "QDRANT_COLLECTION", "samanvay_inventory")
        host = getattr(settings, "qdrant_host", None) or getattr(settings, "QDRANT_HOST", "localhost")
        port = getattr(settings, "qdrant_port", None) or getattr(settings, "QDRANT_PORT", 6333)
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            self.client = QdrantClient(host=host, port=port)
            self.models = models
            self.active = True
            self.connect()
        except Exception:
            self.client = None
            self.active = False
            
    def connect(self):
        if not self.active:
            return
            
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if self.collection_name not in collections:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=self.models.VectorParams(
                        size=1024,
                        distance=self.models.Distance.COSINE
                    ),
                    hnsw_config=self.models.HnswConfigDiff(
                        m=16,
                        ef_construct=100
                    )
                )
        except Exception:
            self.active = False

    def upsert_items(self, items: List[Dict[str, Any]]):
        if not self.active or not items:
            return
            
        points = []
        for item in items:
            sku = item.get("sku_code", "")
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, sku))
            payload = {"sku_code": sku, "item_type": item.get("item_type", "UNKNOWN"), **item.get("payload", {})}
            points.append(
                self.models.PointStruct(
                    id=point_id,
                    vector=item["vector"],
                    payload=payload
                )
            )
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query_vector: List[float], item_type_filter: str = None, top_k: int = 10) -> List[Any]:
        if not self.active:
            return []
            
        q_filter = None
        if item_type_filter:
            q_filter = self.models.Filter(
                must=[
                    self.models.FieldCondition(
                        key="item_type",
                        match=self.models.MatchValue(value=item_type_filter)
                    )
                ]
            )
            
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=q_filter,
            limit=top_k
        )
        return results

    def delete_item(self, sku_code: str):
        if not self.active:
            return
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=self.models.PointIdsList(
                points=[sku_code],
            ),
        )
