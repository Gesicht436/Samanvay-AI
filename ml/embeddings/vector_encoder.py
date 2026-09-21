import random
from typing import List

class VectorEncoder:
    def __init__(self, model_name="BAAI/bge-m3"):
        self.model_name = model_name
        self.dim = 1024
        self.use_transformer = False
        try:
            import os
            from sentence_transformers import SentenceTransformer
            try:
                self.model = SentenceTransformer(model_name, local_files_only=True)
                self.use_transformer = True
            except Exception:
                if os.getenv("DOWNLOAD_EMBEDDING_MODEL", "false").lower() in ("true", "1"):
                    self.model = SentenceTransformer(model_name)
                    self.use_transformer = True
                else:
                    self.model = None
        except (ImportError, Exception):
            self.model = None

    def encode(self, text: str) -> List[float]:
        if self.use_transformer:
            return self.model.encode(text).tolist()
        
        # Fallback pseudo-random reproducible embedding
        random.seed(hash(text))
        return [random.uniform(-1, 1) for _ in range(self.dim)]

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        if self.use_transformer:
            return self.model.encode(texts).tolist()
        
        return [self.encode(t) for t in texts]
