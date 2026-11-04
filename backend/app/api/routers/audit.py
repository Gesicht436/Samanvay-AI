from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
from backend.app.api.dependencies import (
    get_db_session,
    PaginationParams,
    require_csrf,
    require_permission,
    verify_cpse_access,
)
from backend.app.core import permissions as perm
from backend.app.models.tables import AuthSession, User
from backend.app.schemas.audit import ActiveLearningFeedback, AuditActionCategory
from backend.app.services.audit_service import (
    verify_chain,
    export_csv,
    create_audit_entry,
    list_audit_entries,
    get_audit_entry_by_id,
)

router = APIRouter(prefix="/audit", tags=["Audit"])


def _verification_payload(db: Session) -> Dict[str, Any]:
    result = verify_chain(db)
    return {
        "is_valid": result.is_valid,
        "total_verified": result.total_verified,
        "invalid_entries": result.invalid_entries,
    }


@router.get("/")
def list_entries(
    pagination: PaginationParams = Depends(),
    category: Optional[str] = Query(default="ALL"),
    cpse: str = Depends(verify_cpse_access),
    current_user: User = Depends(require_permission(perm.AUDIT_READ)),
    db: Session = Depends(get_db_session),
):
    """List sovereign ledger records inside the authenticated CPSE only.

    The authenticated session CPSE is the effective filter; a client-supplied
    ``cpse`` query value never establishes or broadens authority (AUTH-007
    Sections 15 and 18).
    """
    return list_audit_entries(
        db,
        skip=pagination.skip,
        limit=pagination.limit,
        category=category,
        cpse=cpse,
    )


@router.get("/verify")
def verify_audit_chain_endpoint(
    current_user: User = Depends(require_permission(perm.AUDIT_READ)),
    db: Session = Depends(get_db_session),
):
    """Global chain-integrity verification (read-only, no state written).

    The ledger is one global hash chain, so verification is intentionally not
    partitioned by CPSE. Protected by ``AUDIT_READ`` only.
    """
    return _verification_payload(db)


@router.post("/verify")
def verify_audit_chain_post_endpoint(
    current_user: User = Depends(require_permission(perm.AUDIT_READ)),
    _csrf: AuthSession = Depends(require_csrf),
    db: Session = Depends(get_db_session),
):
    """Read-only chain verification over an unsafe method; CSRF-verified."""
    return _verification_payload(db)


@router.get("/export")
def export_audit_csv_endpoint(
    category: Optional[str] = Query(default=None),
    cpse: str = Depends(verify_cpse_access),
    current_user: User = Depends(require_permission(perm.AUDIT_EXPORT)),
    db: Session = Depends(get_db_session),
):
    """Export sovereign ledger records inside the authenticated CPSE only.

    Export authority is the distinct ``AUDIT_EXPORT`` permission; the session
    CPSE is the only accepted tenant filter.
    """
    filters: Dict[str, Any] = {"cpse": cpse}
    if category and category != "ALL":
        filters["category"] = category

    csv_data = export_csv(db, filters)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=samanvay_sovereign_audit_ledger.csv"},
    )


@router.get("/{log_id}")
def get_entry(
    log_id: str,
    cpse: str = Depends(verify_cpse_access),
    current_user: User = Depends(require_permission(perm.AUDIT_READ)),
    db: Session = Depends(get_db_session),
):
    """Return one ledger record, scoped to the authenticated CPSE.

    A record that exists but belongs to another CPSE is indistinguishable from
    a record that does not exist: both answer 404 and no 403 is returned.
    """
    entry = get_audit_entry_by_id(db, log_id, cpse)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Audit entry {log_id} not found")
    return {
        "log_id": entry.log_id,
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        "action_category": entry.action_category,
        "action_name": entry.action_name,
        "actor_name": entry.actor_name,
        "actor_role": entry.actor_role,
        "cpse": entry.cpse,
        "depot": entry.depot,
        "reference_id": entry.reference_id,
        "details": entry.details,
        "prev_hash": entry.prev_hash,
        "sha256_hash": entry.sha256_hash,
        "is_verified": entry.is_verified,
    }


@router.post("/feedback")
def submit_feedback(
    payload: ActiveLearningFeedback,
    current_user: User = Depends(require_permission(perm.AUDIT_FEEDBACK_CREATE)),
    _csrf: AuthSession = Depends(require_csrf),
    db: Session = Depends(get_db_session),
):
    """Append an HITL/active-learning decision to the sovereign ledger.

    Actor, role, CPSE and depot are session-derived. The client-supplied
    ``officer`` value is overwritten with the authenticated username so no
    request field can forge attribution. This is a business/statutory ledger
    write only: it creates no ``SecurityEvent`` (AUTH-006 Section 7).
    """
    details = payload.model_dump()
    details["officer"] = current_user.username

    entry = create_audit_entry(db, {
        "action_category": AuditActionCategory.ACTIVE_LEARNING_FEEDBACK.value,
        "action": "HITL_FEEDBACK",
        "actor": current_user.username,
        "actor_role": current_user.role,
        "cpse": current_user.cpse,
        "depot": current_user.depot_id,
        "reference_id": payload.source_sku,
        "payload": details,
    })
    return {"status": "SUCCESS", "log_id": entry.log_id, "sha256_hash": entry.sha256_hash}
