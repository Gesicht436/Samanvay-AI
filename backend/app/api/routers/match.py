"""
Match Router: thin HTTP layer delegating to match_service.py.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.app.api.dependencies import (
    get_db_session,
    require_csrf,
    require_permission,
    verify_cpse_access,
)
from backend.app.core import permissions as perm
from backend.app.models.tables import AuthSession, User
from backend.app.schemas.material import MatchRequest, MatchSearchResponse
from backend.app.services.match_service import (
    search_matches as _search_matches,
    # Re-exported for backend/main.py lifespan, which seeds the active-learning
    # cache from this module. Keep importable here.
    active_cache,
)

router = APIRouter(prefix="/match", tags=["Match"])


@router.post("/search", response_model=MatchSearchResponse)
def search_matches(
    payload: MatchRequest,
    _current_user: User = Depends(require_permission(perm.MATCH_READ)),
    _csrf: AuthSession = Depends(require_csrf),
    x_cpse: str = Depends(verify_cpse_access),
    db: Session = Depends(get_db_session),
):
    """
    Zero-Mock Matching & Compatibility Pipeline.
    Normalizes query → retrieves candidates → evaluates 21 safety rules →
    scores via ML → computes logistics → enforces cross-CPSE privacy.
    Operational data is scoped server-authoritatively to the authenticated
    session's CPSE; X-CPSE-ID is never consulted. Fail-closed: a role without
    MATCH_READ is denied before the service is entered.

    Task 19: authenticated protected POST — strict Origin + session-bound
    CSRF token required before the pipeline runs (no read-only exemption).
    """
    return _search_matches(payload, x_cpse, db)
