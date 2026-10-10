"""
AUTH Task 26 — route-level authorization regression tests for the material
management workflow (audit finding F-1).

These tests exercise the **real registered FastAPI routes** and the **real
authorization dependencies** (``require_permission`` / ``require_any_permission``
/ ``require_csrf`` in ``backend/app/api/dependencies.py``, backed by
``backend/app/core/authorization.evaluate`` and the frozen
``backend/app/core/permissions.ROLE_PERMISSIONS`` mapping).

What is faked (per task 26, because PostgreSQL is unavailable):
  * ``get_db_session``      -> an in-memory fake session (no database).
  * ``get_current_user``    -> a synthetic principal (injects *who* the caller is).
  * ``get_current_session`` -> a synthetic session carrying a known token hash so
                               the real ``require_csrf`` can be satisfied.

What is NOT faked (the actual subject under test):
  * FastAPI routing and path/prefix wiring.
  * ``require_permission`` / ``require_any_permission`` (the AUTH-007 RBAC gate).
  * ``require_csrf`` (Origin allowlist + session-bound synchronizer token).
  * The route bodies' resource-level checks (segregation of duties, tenant
    boundary, workflow-state transitions).

Only the data/service layer (``*_service`` functions called by the routes) is
mocked so an authorized request can complete without a database. Therefore these
are **route-level authorization tests**, not full database integration tests; they
prove the authorization boundary, not persistence.

No real network or HIBP requests are made and the application lifespan (DB init +
seed) is never started (``TestClient`` is used without a context manager).
"""

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api import dependencies as deps
from backend.app.api.routers import requisition as requisition_router
from backend.app.api.routers import inventory as inventory_router
from backend.app.core import permissions as perm
from backend.app.core import csrf as csrf_core
from backend.app.core.config import settings


API = "/api/v1"
REQ = f"{API}/requisition"
INV = f"{API}/inventory"
RID = "REQ-TEST-0001"
SKU = "SKU-TEST-001"

# Deterministic session material so the REAL require_csrf can be satisfied.
SESSION_TOKEN_HASH = ("ab" * 32)  # 64 lowercase hex chars -> valid HMAC key
CSRF_TOKEN = csrf_core.derive_csrf_token(SESSION_TOKEN_HASH)
ORIGIN = settings.allowed_origins_list[0]  # guaranteed to be on the allowlist


# ── Synthetic principals / records ───────────────────────────────────────────

class FakeUser:
    """Stand-in for the authenticated ``User`` ORM record (server-derived)."""

    def __init__(self, role, username="actor", cpse="ONGC", depot_id="DEPOT-ONGC-1"):
        self.id = 1
        self.username = username
        self.role = role
        self.cpse = cpse
        self.depot_id = depot_id
        self.is_active = True
        self.is_approved = True


class FakeAuthSession:
    """Stand-in ``AuthSession`` carrying the known token hash for CSRF."""

    def __init__(self):
        self.id = "sess-test-0001"
        self.user_id = 1
        self.session_token_hash = SESSION_TOKEN_HASH


class FakeRequisition:
    def __init__(self, status="PENDING_APPROVAL", source_cpse="ONGC",
                 target_cpse="ONGC", requested_by="REQUESTER-OTHER"):
        self.requisition_id = RID
        self.source_cpse = source_cpse
        self.target_cpse = target_cpse
        self.source_depot = "DEPOT-ONGC-1"
        self.requested_by = requested_by
        self.status = status
        self.approved_by = None
        self.approved_at = None
        self.rejection_reason = None
        self.dispatch_timestamp = None
        self.delivery_timestamp = None
        self.sku_code = SKU
        self.required_qty = 1


class _Query:
    def __init__(self, first):
        self._first = first

    def filter(self, *a, **k):
        return self

    def filter_by(self, *a, **k):
        return self

    def with_for_update(self, *a, **k):
        return self

    def order_by(self, *a, **k):
        return self

    def first(self):
        return self._first

    def all(self):
        return []

    def count(self):
        return 0


class FakeDB:
    """Minimal in-memory session: records staged/committed objects, no SQL."""

    def __init__(self, first_result=None):
        self._first_result = first_result
        self.added = []
        self.commits = 0

    def query(self, *a, **k):
        return _Query(self._first_result)

    def add(self, obj):
        self.added.append(obj)

    def add_all(self, objs):
        self.added.extend(objs)

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass

    def refresh(self, obj):
        pass

    def flush(self):
        pass

    def close(self):
        pass


class _Obj:
    """Attribute bag for faked service return values."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


# ── Faked service layer (data layer only; authorization stays real) ──────────

def _fake_create_requisition(db, payload, idempotency_key):
    return _Obj(requisition_id=RID, sku_code=SKU, required_qty=1,
                status="PENDING_APPROVAL", audit_hash="0" * 64)


def _fake_approve_requisition(db, req_id, username):
    return _Obj(requisition_id=req_id, status="APPROVED", approved_by=username)


def _fake_reject_requisition(db, req_id, reason):
    return _Obj(requisition_id=req_id, status="REJECTED", rejection_reason=reason)


def _fake_generate_gate_pass(db, req_id, payload):
    return _Obj(gate_pass_no="GP-TEST-0001", requisition_id=req_id,
                sha256_hash="0" * 64, qr_code_svg="<svg/>",
                transit_distance_km=12.5, estimated_transit_hours=3,
                co2_saved_kg=4.2)


def _fake_dispatch_requisition(db, req_id):
    return _Obj(requisition_id=req_id, status="DISPATCHED",
                dispatch_timestamp=datetime.now(timezone.utc))


def _fake_deliver_requisition(db, req_id):
    return _Obj(requisition_id=req_id, status="DELIVERED",
                delivery_timestamp=datetime.now(timezone.utc))


def _fake_list_requisitions_for_user(db, user):
    return []


def _fake_get_requisition_for_user(db, req_id, user):
    return {"requisition_id": req_id}


def _fake_create_item(db, payload, requesting_cpse, actor):
    return {"sku_code": SKU, "cpse": requesting_cpse, "status": "ACTIVE"}


def _fake_transition_status(db, sku_code, new_status, reason, officer, requesting_cpse):
    return {"sku_code": sku_code, "status": new_status}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    # NOTE: no ``with`` -> the application lifespan (DB init + seed) never runs.
    return TestClient(app)


@pytest.fixture
def configure(monkeypatch):
    """Mock the data/service layer and inject a synthetic principal.

    ``setup(...)`` chooses the caller's role/CPSE and the resource record that
    the route body reads from the fake DB. The real authorization
    dependencies remain in force.
    """
    # Replace only the service functions the routes call.
    monkeypatch.setattr(requisition_router, "create_requisition", _fake_create_requisition)
    monkeypatch.setattr(requisition_router, "approve_requisition", _fake_approve_requisition)
    monkeypatch.setattr(requisition_router, "reject_requisition", _fake_reject_requisition)
    monkeypatch.setattr(requisition_router, "generate_gate_pass", _fake_generate_gate_pass)
    monkeypatch.setattr(requisition_router, "dispatch_requisition", _fake_dispatch_requisition)
    monkeypatch.setattr(requisition_router, "deliver_requisition", _fake_deliver_requisition)
    monkeypatch.setattr(requisition_router, "list_requisitions_for_user", _fake_list_requisitions_for_user)
    monkeypatch.setattr(requisition_router, "get_requisition_for_user", _fake_get_requisition_for_user)
    monkeypatch.setattr(inventory_router, "create_item", _fake_create_item)
    monkeypatch.setattr(inventory_router, "transition_status", _fake_transition_status)

    state = {"authenticated": True, "user": FakeUser(perm.SITE_ENGINEER)}

    def _db_override_factory(db):
        def _dep():
            yield db
        return _dep

    def _user_override():
        if not state["authenticated"]:
            raise HTTPException(status_code=401, detail="Authentication required.")
        return state["user"]

    def _session_override():
        if not state["authenticated"]:
            raise HTTPException(status_code=401, detail="Authentication required.")
        return FakeAuthSession()

    def setup(*, role=perm.SITE_ENGINEER, authenticated=True, cpse="ONGC",
              username="actor", record_status="PENDING_APPROVAL",
              req_source_cpse="ONGC", req_target_cpse="ONGC",
              requested_by="REQUESTER-OTHER"):
        state["authenticated"] = authenticated
        state["user"] = FakeUser(role=role, username=username, cpse=cpse)
        record = FakeRequisition(status=record_status, source_cpse=req_source_cpse,
                                 target_cpse=req_target_cpse, requested_by=requested_by)
        db = FakeDB(first_result=record)
        app.dependency_overrides[deps.get_db_session] = _db_override_factory(db)
        app.dependency_overrides[deps.get_current_user] = _user_override
        app.dependency_overrides[deps.get_current_session] = _session_override

    yield setup

    app.dependency_overrides.pop(deps.get_db_session, None)
    app.dependency_overrides.pop(deps.get_current_user, None)
    app.dependency_overrides.pop(deps.get_current_session, None)


def _call(client, method, path, body):
    headers = {"origin": ORIGIN, "x-csrf-token": CSRF_TOKEN}
    kwargs = {"headers": headers}
    if method in ("post", "put", "patch") and body is not None:
        kwargs["json"] = body
    return getattr(client, method)(path, **kwargs)


# ── Route / permission matrix (derived from the real routers) ────────────────

# (method, path, body) for every workflow write; the permission each enforces
# is asserted implicitly via the 401/403/200 assertions below.
WORKFLOW_WRITES = [
    ("post", f"{REQ}", {}),
    ("put", f"{REQ}/{RID}/approve", {}),
    ("put", f"{REQ}/{RID}/reject", {"reason": "declined"}),
    ("post", f"{REQ}/{RID}/gatepass", {}),
    ("put", f"{REQ}/{RID}/dispatch", None),
    ("put", f"{REQ}/{RID}/deliver", None),
    ("post", f"{INV}", {}),
    ("put", f"{INV}/{SKU}/status", {"status": "IDLE_SURPLUS"}),
]

# Roles that hold NONE of the workflow permissions (auditor + admin).
NO_WORKFLOW_ROLES = [perm.VIGILANCE_AUDITOR, perm.SUPER_ADMIN]

# (method, path, body, authorized role, required requisition status for the body)
WORKFLOW_AUTHZ = [
    ("post", f"{REQ}", {}, perm.SITE_ENGINEER, "PENDING_APPROVAL"),
    ("get", f"{REQ}", None, perm.SITE_ENGINEER, "PENDING_APPROVAL"),
    ("put", f"{REQ}/{RID}/approve", {}, perm.MATERIALS_MANAGER, "PENDING_APPROVAL"),
    ("put", f"{REQ}/{RID}/approve", {}, perm.TECHNICAL_AUTHORITY, "PENDING_APPROVAL"),
    ("put", f"{REQ}/{RID}/reject", {"reason": "declined"}, perm.MATERIALS_MANAGER, "PENDING_APPROVAL"),
    ("post", f"{REQ}/{RID}/gatepass", {}, perm.CISF_SECURITY, "APPROVED"),
    ("put", f"{REQ}/{RID}/dispatch", None, perm.MATERIALS_MANAGER, "GATE_PASS_ISSUED"),
    ("put", f"{REQ}/{RID}/deliver", None, perm.SITE_ENGINEER, "DISPATCHED"),
    ("post", f"{INV}", {}, perm.MATERIALS_MANAGER, "PENDING_APPROVAL"),
    ("put", f"{INV}/{SKU}/status", {"status": "IDLE_SURPLUS"}, perm.MATERIALS_MANAGER, "PENDING_APPROVAL"),
]


# ── 1. Anonymous requests are rejected (401) ─────────────────────────────────

@pytest.mark.parametrize("method,path,body", WORKFLOW_WRITES)
def test_anonymous_rejected(client, configure, method, path, body):
    configure(authenticated=False)
    resp = _call(client, method, path, body)
    assert resp.status_code == 401, f"{method.upper()} {path} anonymous -> {resp.status_code}"


# ── 2. Authenticated users without the permission are rejected (403) ─────────

@pytest.mark.parametrize("method,path,body", WORKFLOW_WRITES)
@pytest.mark.parametrize("role", NO_WORKFLOW_ROLES)
def test_unauthorized_role_rejected(client, configure, role, method, path, body):
    configure(role=role)
    resp = _call(client, method, path, body)
    assert resp.status_code == 403, f"{method.upper()} {path} as {role} -> {resp.status_code}"
    detail = resp.json().get("detail", {})
    # The denial must originate from the AUTH-007 RBAC gate.
    assert detail.get("error") == "AUTHORIZATION_DENIED"
    assert detail.get("reason") == "PERMISSION_NOT_GRANTED"


# ── 3. Auditors cannot perform write operations (read-only) ──────────────────

@pytest.mark.parametrize("method,path,body", WORKFLOW_WRITES)
def test_auditor_is_read_only(client, configure, method, path, body):
    configure(role=perm.VIGILANCE_AUDITOR)
    resp = _call(client, method, path, body)
    assert resp.status_code == 403


# ── 4. SUPER_ADMIN cannot bypass workflow-specific authorization ─────────────

@pytest.mark.parametrize("method,path,body", WORKFLOW_WRITES)
def test_super_admin_cannot_bypass_workflow(client, configure, method, path, body):
    configure(role=perm.SUPER_ADMIN)
    resp = _call(client, method, path, body)
    assert resp.status_code == 403, f"SUPER_ADMIN bypassed {method.upper()} {path}"


# ── 5. Authorized roles pass the authorization boundary ──────────────────────

@pytest.mark.parametrize("method,path,body,role,record_status", WORKFLOW_AUTHZ)
def test_authorized_role_passes_boundary(client, configure, method, path, body, role, record_status):
    configure(role=role, record_status=record_status)
    resp = _call(client, method, path, body)
    assert 200 <= resp.status_code < 300, (
        f"{method.upper()} {path} as {role} -> {resp.status_code}: {resp.text[:200]}"
    )


# ── 6. Resource-level authorization enforced by the real route bodies ────────

def test_segregation_of_duties_blocks_self_approval(client, configure):
    # A materials manager may not approve a requisition they themselves raised.
    configure(role=perm.MATERIALS_MANAGER, username="actor", requested_by="actor")
    resp = _call(client, "put", f"{REQ}/{RID}/approve", {})
    assert resp.status_code == 403
    assert "Segregation of duties" in resp.text


def test_cross_tenant_dispatch_rejected(client, configure):
    # A manager from a different CPSE cannot dispatch another CPSE's material,
    # even though they hold REQUISITION_DISPATCH.
    configure(role=perm.MATERIALS_MANAGER, cpse="IOCL",
              record_status="GATE_PASS_ISSUED", req_source_cpse="ONGC")
    resp = _call(client, "put", f"{REQ}/{RID}/dispatch", None)
    assert resp.status_code == 403
    assert "TENANT" in resp.text or "forbidden" in resp.text.lower()


def test_invalid_workflow_transition_rejected(client, configure):
    # Dispatch requires GATE_PASS_ISSUED; a still-pending requisition is 409.
    configure(role=perm.MATERIALS_MANAGER, cpse="ONGC",
              record_status="PENDING_APPROVAL", req_source_cpse="ONGC")
    resp = _call(client, "put", f"{REQ}/{RID}/dispatch", None)
    assert resp.status_code == 409
    assert "GATE_PASS_ISSUED" in resp.text


# ── 7. Guard: the authorization dependencies themselves are not overridden ────

def test_authorization_dependencies_are_real(client, configure):
    configure(role=perm.SITE_ENGINEER)
    # We override only the leaf identity/DB deps, never the authz gate.
    assert deps.require_permission not in app.dependency_overrides
    assert deps.require_any_permission not in app.dependency_overrides
    assert deps.require_csrf not in app.dependency_overrides
    assert deps.get_current_user in app.dependency_overrides  # identity is stubbed


