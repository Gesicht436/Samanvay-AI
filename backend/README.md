# Backend

The backend is a single FastAPI process. Contracts live in `app/contracts/` and are imported by the ingestion, matching, graph, and API modules.

Run locally from the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload
```

The API is available at `http://localhost:8000`, with OpenAPI documentation at `/docs`.