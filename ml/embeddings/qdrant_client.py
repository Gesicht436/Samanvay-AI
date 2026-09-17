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

class SamanvayQdrantClient:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            self.models = models
            self.active = True
        except ImportError:
            self.client = None
            self.active = False
            
    def connect(self):
        if not self.active:
            return
            
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

    def upsert_items(self, items: List[Dict[str, Any]]):
        if not self.active:
            return
            
        points = []
        for item in items:
            points.append(
                self.models.PointStruct(
                    id=item["sku_code"],
                    vector=item["vector"],
                    payload={"item_type": item.get("item_type", "UNKNOWN"), **item.get("payload", {})}
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
