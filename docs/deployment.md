# Deployment

Local dependencies are defined in `deployment/docker-compose.yml`. Production deployment should provide secrets through the environment, use managed Qdrant/Neo4j/PostgreSQL services, and persist model weights outside the application image.

For a local CPU-only setup without Docker:

1. Install the optional matching dependencies with `pip install -e ".[ml]"`.
2. Download `BAAI/bge-m3` into the configured `MODEL_WEIGHTS_PATH` (default: `machine_learning/model_weights/bge_m3_cpes`).
3. Set `QDRANT_LOCAL_PATH` if the default `data/qdrant_local` location is not suitable.
4. Run `python -m scripts.index_canonical_master` once to build the four-domain catalog index.
5. Start the API and frontend normally. Matching uses a reachable Qdrant server when available; otherwise it opens the persistent embedded database. The embedded database can only be opened by one process at a time, so stop the API before re-indexing.

The dashboard reports matching as ready only after loading the configured encoder and successfully querying the configured collection.
