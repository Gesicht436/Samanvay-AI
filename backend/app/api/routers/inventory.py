from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.app.api.dependencies import (
    _record_authorization_failure,
    get_db_session,
    InventoryFilterParams,
    PaginationParams,
    require_csrf,
    require_permission,
    validate_idempotency_key,
    verify_cpse_access,
)
from backend.app.core import permissions as perm
from backend.app.models.tables import AuthSession, User
from backend.app.services.inventory_service import (
    list_inventory,
    get_item,
    create_item,
    transition_status,
    get_surplus_radar,
    get_hitl_queue,
    get_inventory_stats,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


def _inventory_session_cpse(
    current_user: User = Depends(require_permission(perm.INVENTORY_READ)),
    db: Session = Depends(get_db_session),
) -> str:
    """Return the authenticated session's CPSE for inventory read access.

    Authentication and authorization are delegated to the centralized AUTH-007
    dependency (``INVENTORY_READ``). The tenant context is taken ONLY from the
    authenticated session user; a client-supplied ``?cpse`` query parameter, a
    request-body CPSE, or an ``X-CPSE-ID`` header is never consulted as a tenant
    selector. If the account carries no CPSE, the request fails closed instead of
    defaulting to a fallback tenant.
    """
    cpse = current_user.cpse
    if not cpse:
        _record_authorization_failure(
            db,
            current_user,
            permission=perm.INVENTORY_READ,
            reason_code="MISSING_RESOURCE_ATTRIBUTES",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "AUTHORIZATION_DENIED",
                "reason": "MISSING_RESOURCE_ATTRIBUTES",
            },
        )
    return cpse


@router.get("")
@router.get("/")
def get_inventory_list(
    filters: InventoryFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
    session_cpse: str = Depends(_inventory_session_cpse),
    db: Session = Depends(get_db_session)
):
    filter_dict = {k: v for k, v in filters.__dict__.items() if v is not None}
    pag_dict = {"skip": pagination.skip, "limit": pagination.limit}
    return list_inventory(db, filter_dict, pag_dict, session_cpse)

@router.get("/stats")
def get_stats(session_cpse: str = Depends(_inventory_session_cpse), db: Session = Depends(get_db_session)):
    return get_inventory_stats(db, session_cpse)

@router.get("/surplus")
def get_surplus_items(cpse: str = Depends(verify_cpse_access), db: Session = Depends(get_db_session)):
    return get_surplus_radar(db, cpse)

@router.get("/hitl-queue")
def get_hitl_items(
    session_cpse: str = Depends(_inventory_session_cpse),
    db: Session = Depends(get_db_session),
):
    return get_hitl_queue(db, session_cpse)

@router.get("/{sku_code}")
def get_inventory_item(sku_code: str, session_cpse: str = Depends(_inventory_session_cpse), db: Session = Depends(get_db_session)):
    return get_item(db, sku_code, session_cpse)


def _inventory_mutation_identity(permission: str):
    """Return the authenticated actor for an inventory mutation route.

    Authentication and authorization are delegated to the centralized AUTH-007
    dependency for ``permission`` (``INVENTORY_CREATE`` /
    ``INVENTORY_STATUS_CHANGE``). Both the tenant context and the actor identity
    used by the mutation come ONLY from the authenticated session: a client-
    supplied ``cpse``, ``officer``/``actor`` body field or ``X-CPSE-ID`` header is
    never consulted. If the account carries no CPSE the request fails closed
    rather than defaulting to a fallback tenant.
    """

    def dependency(
        current_user: User = Depends(require_permission(permission)),
        db: Session = Depends(get_db_session),
    ) -> User:
        if not current_user.cpse:
            _record_authorization_failure(
                db,
                current_user,
                permission=permission,
                reason_code="MISSING_RESOURCE_ATTRIBUTES",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "AUTHORIZATION_DENIED",
                    "reason": "MISSING_RESOURCE_ATTRIBUTES",
                },
            )
        return current_user

    return dependency


@router.post("")
@router.post("/")
def create_inventory_item(
    payload: Dict[str, Any],
    current_user: User = Depends(_inventory_mutation_identity(perm.INVENTORY_CREATE)),
    _csrf: AuthSession = Depends(require_csrf),
    db: Session = Depends(get_db_session),
):
    return create_item(db, payload, current_user.cpse, current_user.username)

@router.put("/{sku_code}/status")
def update_item_status(
    sku_code: str, 
    payload: Dict[str, Any], 
    current_user: User = Depends(_inventory_mutation_identity(perm.INVENTORY_STATUS_CHANGE)),
    _csrf: AuthSession = Depends(require_csrf),
    idempotency_key: str = Depends(validate_idempotency_key),
    db: Session = Depends(get_db_session)
):
    if isinstance(idempotency_key, dict) and idempotency_key.get("status") == "CACHED":
        return idempotency_key["data"]
        
    new_status = payload.get("status")
    reason = payload.get("reason", "")
    officer = current_user.username
    return transition_status(db, sku_code, new_status, reason, officer, current_user.cpse)
