# Dense Vector Embeddings & Qdrant Client (`ml/embeddings/`)

This directory handles dense semantic text representation and vector database indexing using **BAAI/BGE-M3** and **Qdrant**.

---

## 1. File-by-File Breakdown

### `vector_encoder.py` — BAAI/BGE-M3 Dense Text Encoder
- **Purpose:** Converts free-form ERP item descriptions, requisition queries, and technical specifications into dense 1024-dimensional normalized vector representations.
- **Key Classes:**
  - `VectorEncoder`:
    - `encode(text: str) -> np.ndarray`: Produces a single normalized 1024-dim vector.
    - `encode_batch(texts: List[str], batch_size=32) -> np.ndarray`: Efficient batched inference.
    - Utilizes `sentence-transformers` with fallback to ONNX Runtime for CPU acceleration in air-gapped environments.
    - Performs $L_2$ vector normalization: $\|\mathbf{v}\|_2 = 1.0$, allowing cosine similarity to be computed via dot product: $\cos(\mathbf{u}, \mathbf{v}) = \mathbf{u} \cdot \mathbf{v}$.

### `qdrant_client.py` — Qdrant Vector Database Client
- **Purpose:** High-level interface to Qdrant vector search engine.
- **Key Classes:**
  - `SamanvayQdrantClient`:
    - `init_collection(collection_name="samanvay_inventory")`: Configures collection with 1024 dimensions and Cosine distance metric. Sets up HNSW index parameters ($M=16$, $efConstruction=100$).
    - `upsert_inventory_batch(items: List[Dict[str, Any]])`: Uploads vectors alongside rich metadata payloads (CPSE, SKU, item type, nominal size, pressure class, depot location).
    - `search(query_vector, top_k=20, filters=None)`: Performs approximate nearest neighbor (ANN) search with optional strict payload filtering (e.g., filter only available stock within `IOCL` or `ONGC`).

---

## 2. Theory & Mathematics for Juniors

### 1. Hierarchical Navigable Small World (HNSW) Graphs:
- Traditional brute-force vector search requires $O(N)$ dot products across millions of items, introducing hundreds of milliseconds of latency.
- HNSW builds a multi-layer graph with logarithmic $O(\log N)$ search complexity. Upper layers have long-range skip edges for rapid traversal; bottom layer contains fine-grained local neighborhoods.

### 2. Why BAAI/BGE-M3:
- Supports 100+ languages including Indian technical mixed code (Hindi/English transliterations).
- Handles arbitrary sequence lengths up to 8192 tokens.
- Demonstrates state-of-the-art retrieval accuracy on domain-specific engineering acronyms.

---

## 3. Code Example

```python
from ml.embeddings.vector_encoder import VectorEncoder
from ml.embeddings.qdrant_client import SamanvayQdrantClient

# Initialize encoder and Qdrant client
encoder = VectorEncoder()
client = SamanvayQdrantClient(host="localhost", port=6333)

# Generate dense embedding
query = "SEAMLESS LINE PIPE 12 INCH SCH 40 API 5L GR B PSL2"
vector = encoder.encode(query)

# Search vector database
results = client.search(query_vector=vector.tolist(), top_k=5)
for hit in results:
    print(f"SKU: {hit.payload['sku_code']} | Score: {hit.score:.4f} | Description: {hit.payload['description']}")
```
