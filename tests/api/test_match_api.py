"""
Match API contract tests.

Covers the F-1 / F-2 remediation of POST /api/v1/match/search:

* anonymous                -> 401
* SITE_ENGINEER            -> 403
* TECHNICAL_AUTHORITY      -> 403
* CISF_SECURITY            -> 403
* VIGILANCE_AUDITOR        -> 403
* SUPER_ADMIN              -> 403
* MATERIALS_MANAGER        -> 200  (sole holder of MATCH_READ)
* CPSE isolation: results are scoped to the session-derived CPSE; a spoofed
  ``X-CPSE-ID`` header or a client body ``cpse`` field never broadens them.
* GET /api/v1/match/benchmark -> 404 (removed from the production router).

Authenticated cases use the real application authentication flow:
``POST /api/v1/auth/login`` establishes the server-side session cookie that the
following request presents. No authentication or authorization dependency is
mocked, overridden or weakened.
"""

import inspect

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api import dependencies as api_dependencies
from backend.app.core.config import settings
from backend.app.schemas.auth import DEFAULT_SEED_PASSWORD
from backend.app.schemas.material import MatchRequest, MatchSearchResponse
from backend.app.services.match_service import (
    parse_query,
    _resolve_item_type,
    _check_cross_standard_equivalence,
    _compute_mii_scoring,
    _resolve_tier,
    search_matches,
)
from backend.app.models.base import SessionLocal
from backend.app.models.tables import InventoryItem
from ml.ner.normalizer import DialectNormalizer
from rules.tolerance import evaluate_pair
from ml.ranking.ranker import CompatibilityRanker


# CPSE A = the caller's own tenant; CPSE B = a foreign tenant used to attempt
# cross-CPSE broadening.
CPSE_A = "OIL"
CPSE_B = "IOCL"
ISO_SKU_A = "TEST-ISO-OIL-0001"
ISO_SKU_B = "TEST-ISO-IOCL-0001"

MATCH_SEARCH_BODY = {
    "query_text": "FLG WNRF 4IN 300# A105",
    "item_type": "FLANGE",
    "size_nb_mm": 100.0,
    "pressure_class": 300,
}


# ── Real application fixtures ───────────────────────────────────────────────

@pytest.fixture(scope="module")
def _application_lifespan():
    """Run the real application lifespan once (DB init + seed users/inventory).

    This is the production startup path; no test-only authentication wiring.
    """
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


def _ensure_cpse_twin_items():
    """Insert identical matching parts under CPSE A and CPSE B (idempotent)."""
    db = SessionLocal()
    try:
        for sku in (ISO_SKU_A, ISO_SKU_B):
            db.query(InventoryItem).filter(InventoryItem.sku_code == sku).delete()
        db.commit()
        for sku, cpse, depot_id, depot_location in (
            (ISO_SKU_A, CPSE_A, "DEPOT-OIL-DLJ", "Duliajan"),
            (ISO_SKU_B, CPSE_B, "DEPOT-IOCL-PAN", "Panipat"),
        ):
            db.add(
                InventoryItem(
                    sku_code=sku,
                    cpse=cpse,
                    depot_id=depot_id,
                    depot_location=depot_location,
                    description="FLG WNRF 4IN 300# A105 FLANGE",
                    item_type="FLANGE",
                    size_nb_mm=100.0,
                    pressure_class=300,
                    metallurgy="ASTM A105",
                    facing_end="RF",
                    quantity=10,
                    unit_cost_inr=1500.0,
                    status="TO_BE_CONSUMED",
                )
            )
        db.commit()
    finally:
        db.close()


def _search_path():
    return "/api/v1/match/search"


def test_normalizer_and_matching_pipeline():
    normalizer = DialectNormalizer()
    norm = normalizer.normalize("FLG WNRF 4IN 300# A105 SCH 40")

    assert norm.get("item_type") == "FLANGE"
    assert norm.get("size_nb_mm") == 100.0
    assert norm.get("pressure_class") == 300
    assert "A105" in norm.get("metallurgy", "")

    query_part = {
        "item_type": "FLANGE",
        "size_nb_mm": 100.0,
        "pressure_class": 300,
        "metallurgy": "ASTM A105",
        "properties": {"facing": "RF"},
    }

    # Identical candidate
    cand_identical = {
        "item_type": "FLANGE",
        "size_nb_mm": 100.0,
        "pressure_class": 300,
        "metallurgy": "ASTM A105",
        "properties": {"facing": "RF"},
    }
    result_identical = evaluate_pair(query_part, cand_identical)
    assert result_identical.is_compatible is True
    assert "TIER_1" in result_identical.compatibility_tier.name

    # Incompatible size
    cand_wrong_size = {
        "item_type": "FLANGE",
        "size_nb_mm": 150.0,
        "pressure_class": 300,
        "metallurgy": "ASTM A105",
        "properties": {"facing": "RF"},
    }
    result_wrong_size = evaluate_pair(query_part, cand_wrong_size)
    assert result_wrong_size.is_compatible is False
    assert len(result_wrong_size.rule_violations) > 0
    assert "DIM" in str(result_wrong_size.rule_violations[0].module_name)


def test_compatibility_ranker_scoring():
    ranker = CompatibilityRanker()
    q = {"item_type": "VALVE", "size_nb_mm": 50.0, "pressure_class": 150, "metallurgy": "A216 WCB"}
    c1 = {"item_type": "VALVE", "size_nb_mm": 50.0, "pressure_class": 150, "metallurgy": "A216 WCB"}
    c2 = {"item_type": "VALVE", "size_nb_mm": 50.0, "pressure_class": 300, "metallurgy": "A216 WCB"}

    score1 = ranker.predict(q, c1)
    score2 = ranker.predict(q, c2)

    assert score1 >= 0.80
    assert isinstance(score2, float)


def test_match_service_parse_query_with_model():
    req = MatchRequest(
        query_text="GATE VALVE 4IN 150# A216 WCB",
        item_type="VALVE",
        size_nb_mm=100.0,
        pressure_class=150,
        metallurgy="ASTM A216 WCB",
        sour_service=True,
    )
    query_part, normalized = parse_query(req)
    assert query_part["item_type"] == "VALVE"
    assert query_part["size_nb_mm"] == 100.0
    assert query_part["pressure_class"] == 150
    assert query_part["properties"].get("sour_service") is True
    assert query_part["properties"].get("hardness_max_hrc") == 22.0


def test_match_service_helpers():
    base_type, sub_type = _resolve_item_type("GATE_VALVE")
    assert base_type == "VALVE"
    assert sub_type == "GATE"

    base_type, sub_type = _resolve_item_type("WN_FLANGE")
    assert base_type == "FLANGE"
    assert sub_type == "WN"

    assert _resolve_tier(0.96, True) == "Tier 1"
    assert _resolve_tier(0.85, True) == "Tier 2"
    assert _resolve_tier(0.70, True) == "Tier 3"
    assert _resolve_tier(0.99, False) == "Tier 3"


# ── F-1: MATCH_READ RBAC gate ───────────────────────────────────────────────

def test_match_search_anonymous_returns_401(client):
    """Anonymous callers are rejected before any route logic; the X-CPSE-ID
    header must not act as a credential."""
    response = client.post(
        _search_path(),
        json=MATCH_SEARCH_BODY,
        headers={"X-CPSE-ID": "IOCL"},
    )
    assert response.status_code == 401


@pytest.mark.parametrize(
    "username,expected_status",
    [
        pytest.param("engineer_oil", 403, id="site-engineer"),
        pytest.param("tech_authority", 403, id="technical-authority"),
        pytest.param("cisf_oil", 403, id="cisf-security"),
        pytest.param("auditor", 403, id="vigilance-auditor"),
        pytest.param("admin", 403, id="super-admin"),
        pytest.param("stores_oil", 200, id="materials-manager"),
    ],
)
def test_match_search_authorization_matrix(client, username, expected_status):
    """Every role without MATCH_READ is denied; MATERIALS_MANAGER is allowed.

    SUPER_ADMIN has no implicit bypass, so it is denied as well.
    """
    _login(client, username)
    response = client.post(
        _search_path(),
        json=MATCH_SEARCH_BODY,
        headers={"X-CPSE-ID": CPSE_A},
    )
    assert response.status_code == expected_status

    if expected_status == 200:
        _ensure_cpse_twin_items()
        validated = MatchSearchResponse(**response.json())
        assert validated.query == MATCH_SEARCH_BODY["query_text"]
        assert validated.candidates
        assert len(validated.candidates) == validated.total_candidates_evaluated
        # Session-derived CPSE scoping (stores_oil belongs to CPSE A).
        assert all(cand.cpse == CPSE_A for cand in validated.candidates)
    else:
        assert response.json().get("detail") == {
            "error": "AUTHORIZATION_DENIED",
            "reason": "PERMISSION_NOT_GRANTED",
        }


# ── F-2: server-authoritative CPSE scoping ──────────────────────────────────

def _iter_api_routes(routes):
    """Yield every route, descending into FastAPI's nested included routers."""
    for route in routes:
        yield route
        for attr in ("routes", "original_router"):
            sub = getattr(route, attr, None)
            if sub is None:
                continue
            if hasattr(sub, "__iter__") and not isinstance(sub, (str, bytes)):
                yield from _iter_api_routes(sub)
            elif hasattr(sub, "routes"):
                yield from _iter_api_routes(sub.routes)


def test_match_search_route_wiring_uses_session_cpse():
    """Static wiring check: the route derives CPSE from the session user only
    (verify_cpse_access) and is gated by require_permission(MATCH_READ).

    ``verify_cpse_access`` accepts nothing but the authenticated user, so
    X-CPSE-ID cannot reach the service through this route."""
    from backend.app.api.routers import match as match_router

    route = next(
        r
        for r in _iter_api_routes(app.routes)
        if getattr(r, "endpoint", None) is match_router.search_matches
    )
    assert "POST" in (route.methods or set())

    calls = []
    stack = [route.dependant]
    while stack:
        dep = stack.pop()
        if dep.call is not None:
            calls.append(dep.call)
        stack.extend(dep.dependencies)

    assert api_dependencies.verify_cpse_access in calls, (
        "route must obtain CPSE via verify_cpse_access (session-derived)"
    )
    assert list(inspect.signature(api_dependencies.verify_cpse_access).parameters) == [
        "current_user"
    ], "verify_cpse_access must not accept any client-controlled input"
    assert any(
        getattr(call, "__qualname__", "").endswith("require_permission.<locals>.checker")
        for call in calls
    ), "MATCH_READ permission gate missing from route"


def test_match_search_cpse_isolation_header_cannot_broaden(client):
    """Authenticate as the MATERIALS_MANAGER of CPSE A and request matching.

    Operational candidates must come only from CPSE A, even when X-CPSE-ID and
    a client body ``cpse`` field both claim CPSE B."""
    _ensure_cpse_twin_items()
    _login(client, "stores_oil")  # session CPSE = CPSE A

    spoofed_body = dict(MATCH_SEARCH_BODY)
    spoofed_body["cpse"] = CPSE_B  # client-supplied body CPSE attempt
    spoofed = client.post(
        _search_path(),
        json=spoofed_body,
        headers={"X-CPSE-ID": CPSE_B},
    )
    assert spoofed.status_code == 200
    spoofed_data = MatchSearchResponse(**spoofed.json())
    assert spoofed_data.candidates, "expected candidates from CPSE A"
    assert all(cand.cpse == CPSE_A for cand in spoofed_data.candidates)
    spoofed_skus = {cand.sku_code for cand in spoofed_data.candidates}
    assert ISO_SKU_B not in spoofed_skus

    # The CPSE B twin exists and matches the same query, so its absence proves
    # the server-side filter rather than missing data.
    db = SessionLocal()
    try:
        twin_b = (
            db.query(InventoryItem)
            .filter(InventoryItem.sku_code == ISO_SKU_B)
            .first()
        )
        assert twin_b is not None
        assert twin_b.cpse == CPSE_B
    finally:
        db.close()

    # The header cannot broaden results: an otherwise identical request with
    # the caller's own CPSE yields exactly the same candidate set.
    honest = client.post(
        _search_path(),
        json=MATCH_SEARCH_BODY,
        headers={"X-CPSE-ID": CPSE_A},
    )
    assert honest.status_code == 200
    honest_data = MatchSearchResponse(**honest.json())
    assert all(cand.cpse == CPSE_A for cand in honest_data.candidates)
    assert {cand.sku_code for cand in honest_data.candidates} == spoofed_skus


def test_match_benchmark_route_absent(client):
    """The benchmark endpoint is not part of the production router."""
    response = client.get("/api/v1/match/benchmark")
    assert response.status_code == 404
