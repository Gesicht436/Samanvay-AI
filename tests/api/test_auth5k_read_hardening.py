"""
AUTH-5K focused tests — permission-only read hardening for three routes.

Scope (permission-only, E-1 tenant scoping explicitly untouched):

1. ``GET /api/v1/inventory/surplus`` requires ``INVENTORY_READ`` via the
   existing ``_inventory_session_cpse`` helper (session-CPSE preserved).
2. ``GET /api/v1/ingest/documents`` requires session + ``DOCUMENT_READ``.
3. ``GET /api/v1/ingest/documents/{doc_id}`` requires session +
   ``DOCUMENT_READ`` (existing 404 shape preserved, no tenant filter).

Authentication uses the real application flow (login session cookie). No
authentication or authorization dependency is mocked or overridden.
"""

import inspect

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api.routers import ingest as ingest_router
from backend.app.api.routers import inventory as inventory_router
from backend.app.core import permissions as perm
from backend.app.core.config import settings
from backend.app.models.base import SessionLocal
from backend.app.models.tables import IngestedDocument
from backend.app.schemas.auth import DEFAULT_SEED_PASSWORD

SURPLUS_PATH = "/api/v1/inventory/surplus"
DOCUMENTS_PATH = "/api/v1/ingest/documents"
MISSING_DOC_ID = 99999999


# ── Real application fixtures (mirrors test_match_api.py) ───────────────────

@pytest.fixture(scope="module")
def _application_lifespan():
    """Run the real application lifespan once (DB init + seed users)."""
    with TestClient(app):
        yield


@pytest.fixture()
def client(_application_lifespan):
    """Fresh client with an empty cookie jar, so every test starts anonymous."""
    return TestClient(app)


def _login(test_client, username):
    """Authenticate through the real login endpoint and session cookie flow."""
    response = test_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": DEFAULT_SEED_PASSWORD},
    )
    assert response.status_code == 200, response.text
    assert test_client.cookies.get(settings.session_cookie_name), (
        "login must establish the server-side session cookie"
    )
    return response.json()


def _ensure_document():
    """Return an existing ingested-document id, inserting one if the ledger is empty."""
    db = SessionLocal()
    try:
        existing = db.query(IngestedDocument).order_by(IngestedDocument.id.asc()).first()
        if existing is not None:
            return existing.id
        doc = IngestedDocument(
            filename="auth5k-regression-fixture.pdf",
            doc_type="MTC_CERTIFICATE",
            is_scanned=False,
            confidence=0.99,
            raw_text="AUTH-5K regression fixture",
            parsed_metadata={"fixture": True},
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc.id
    finally:
        db.close()


# ── Anonymous → 401 on all three routes ─────────────────────────────────────

def test_surplus_anonymous_returns_401(client):
    assert client.get(SURPLUS_PATH).status_code == 401


def test_documents_anonymous_returns_401(client):
    assert client.get(DOCUMENTS_PATH).status_code == 401


def test_document_by_id_anonymous_returns_401(client):
    # Authentication is evaluated before the 404 lookup.
    assert client.get(f"{DOCUMENTS_PATH}/{MISSING_DOC_ID}").status_code == 401


# ── Wrong role → 403 ────────────────────────────────────────────────────────

def test_surplus_site_engineer_forbidden(client):
    """SITE_ENGINEER holds no INVENTORY_READ grant."""
    _login(client, "engineer_oil")
    response = client.get(SURPLUS_PATH)
    assert response.status_code == 403
    assert response.json().get("detail") == {
        "error": "AUTHORIZATION_DENIED",
        "reason": "PERMISSION_NOT_GRANTED",
    }


def test_documents_materials_manager_forbidden(client):
    """MATERIALS_MANAGER holds no DOCUMENT_READ grant."""
    _login(client, "stores_oil")
    response = client.get(DOCUMENTS_PATH)
    assert response.status_code == 403
    assert response.json().get("detail") == {
        "error": "AUTHORIZATION_DENIED",
        "reason": "PERMISSION_NOT_GRANTED",
    }


def test_document_by_id_materials_manager_forbidden(client):
    _login(client, "stores_oil")
    doc_id = _ensure_document()
    response = client.get(f"{DOCUMENTS_PATH}/{doc_id}")
    assert response.status_code == 403
    assert response.json().get("detail") == {
        "error": "AUTHORIZATION_DENIED",
        "reason": "PERMISSION_NOT_GRANTED",
    }

# ── Legitimate grant-holders keep existing successful behavior ────────────────

def test_surplus_materials_manager_ok(client):
    """MATERIALS_MANAGER holds INVENTORY_READ; existing radar shape preserved."""
    _login(client, "stores_oil")
    response = client.get(SURPLUS_PATH)
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


def test_documents_auditor_ok(client):
    """VIGILANCE_AUDITOR holds DOCUMENT_READ; existing listing shape preserved."""
    _login(client, "auditor")
    response = client.get(DOCUMENTS_PATH)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "total" in body
    assert "documents" in body


def test_document_by_id_auditor_ok(client):
    _login(client, "auditor")
    doc_id = _ensure_document()
    response = client.get(f"{DOCUMENTS_PATH}/{doc_id}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == doc_id
    assert "metadata" in body


def test_document_by_id_missing_still_404(client):
    """The existing missing-document 404 shape is preserved."""
    _login(client, "auditor")
    response = client.get(f"{DOCUMENTS_PATH}/{MISSING_DOC_ID}")
    assert response.status_code == 404
    assert response.json().get("detail") == f"Document ID {MISSING_DOC_ID} not found."


# ── Tenant broadening is impossible ─────────────────────────────────────────

def test_surplus_x_cpse_header_cannot_broaden(client):
    """X-CPSE-ID is never consulted; the session CPSE stays authoritative."""
    _login(client, "stores_oil")
    plain = client.get(SURPLUS_PATH)
    spoofed = client.get(SURPLUS_PATH, headers={"X-CPSE-ID": "IOCL"})
    assert plain.status_code == 200
    assert spoofed.status_code == 200
    assert spoofed.json() == plain.json()


def test_surplus_query_cpse_cannot_broaden(client):
    """A client ?cpse= value cannot switch the session-CPSE tenant boundary."""
    _login(client, "stores_oil")
    plain = client.get(SURPLUS_PATH)
    scoped = client.get(f"{SURPLUS_PATH}?cpse=IOCL")
    assert plain.status_code == 200
    assert scoped.status_code == 200
    assert scoped.json() == plain.json()


# ── Scope guard: no new permission identifiers ──────────────────────────────

def test_no_new_permission_identifiers():
    """AUTH-5K is permission-only: the frozen vocabulary is unchanged."""
    assert "INVENTORY_SURPLUS_IDENTIFY" not in _route_dependency_names(
        inventory_router.get_surplus_items
    )
    assert _route_permission_names(ingest_router.list_documents) == {"DOCUMENT_READ"}
    assert _route_permission_names(ingest_router.get_document) == {"DOCUMENT_READ"}
    assert "DOCUMENT_READ" in perm.ALL_PERMISSIONS
    assert "INVENTORY_READ" in perm.ALL_PERMISSIONS


def _route_dependency_names(route_fn):
    source = inspect.getsource(route_fn)
    return source


def _route_permission_names(route_fn):
    source = inspect.getsource(route_fn)
    found = set()
    for name in ("DOCUMENT_READ", "INVENTORY_READ", "INVENTORY_SURPLUS_IDENTIFY"):
        if f"perm.{name}" in source:
            found.add(name)
    return found
