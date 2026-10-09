# Architecture

Samanvay-AI is a single FastAPI process with modular domain routers. The pipeline is ingestion, attribute extraction, dense retrieval, deterministic validation, graph lookup, and audit logging. Next.js consumes typed API contracts and falls back to local mock data for frontend-only work.

The matching engine deliberately uses pure Python, Polars, and NumPy. The pitch-deck term C++ Gate is an engineering label, not a native compilation target.
