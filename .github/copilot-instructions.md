# Samanvay-AI workspace instructions

- Use Python 3.11 or 3.12; never target Python 3.14 for ML dependencies.
- Keep the backend contract-first: Pydantic models in `backend/app/contracts/` are the API source of truth.
- Keep matching pure Python, Polars, and NumPy. Do not add CMake, pybind11, or native C++ extensions.
- Do not regenerate files under `data/ml_training/` or `data/mock_cpes_catalogs/` unless explicitly requested.
- Keep `frontend/src/lib/types.ts` synchronized with backend contracts.
- Prefer focused tests for ingestion, retrieval, tolerance classification, and API contracts.
