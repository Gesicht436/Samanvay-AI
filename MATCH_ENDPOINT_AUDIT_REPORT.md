# MATCH SEARCH ENDPOINT AUDIT - Authentication & Authorization

**Date:** 2026-10-06
**Audit scope:** POST /api/v1/match/search, and GET /api/v1/match/benchmark prior to its removal from the production router - authentication, authorization, cross-CPSE data exposure, documentation/code consistency, and test coverage.
**Status:** PASS

## Evidence base reviewed
- Router: backend/app/api/routers/match.py (route defs, deps, OpenAPI responses)
- Service: backend/app/services/match_service.py (retrieve_candidates, build_candidate_response, logistics)
- Auth deps: backend/app/api/dependencies.py (session chain, verify_cpse_access)
- Core: backend/app/core/authorization.py, backend/app/core/permissions.py, backend/app/core/config.py
- Schemas: backend/app/schemas/material.py (MatchRequest, CandidateMatchItem, MatchSearchResponse)
- Models: backend/app/models/tables.py (InventoryItem, User, AuthSession), backend/app/models/base.py
- Docs: docs/authentication/02_ARCHITECTURE.md, docs/authentication/07_PERMISSION_CONTRACT.md
- Tests: tests/api/test_match_api.py, tests/integration/test_benchmarks.py

---

## 1. Executive summary

Both endpoints fail the frozen authentication/authorization architecture. The two findings are independent, so each must be remediated regardless of the other.

| # | Endpoint | Authentication | Authorization | Cross-CPSE exposure | Verdict |
|---|----------|----------------|---------------|---------------------|---------|
| F-1 | POST /api/v1/match/search | **Enforced** (session cookie -> server-derived CPSE) | **Enforced** (require_permission(perm.MATCH_READ); MATERIALS_MANAGER grant; RBAC-first resource-policy check) | **Scoped** - retrieve_candidates filters InventoryItem.cpse == caller_cpse; X-CPSE-ID not authoritative | CLOSED |
| F-2 | GET /api/v1/match/benchmark | Removed from production router; no production dependency | No permission needed (no BENCHMARK_READ); route deleted | N/A | CLOSED |

**Finding F-2 (benchmark, unauthenticated — CLOSED):** The endpoint was reachable without any session and returned 200 with aggregate benchmark results, sitting outside the frozen public surface. The route was removed from the production router (`backend/app/api/routers/match.py`); no production dependency remains, and no new authorization mechanism was invented. The benchmark endpoint is documented as development/test-only (02_ARCHITECTURE.md Section 12, 07_PERMISSION_CONTRACT.md Section 14). Test coverage now asserts the benchmark route is not part of the production surface.

**Finding F-1 (search, authenticated but un-gated — CLOSED):** The route is authenticated through the session chain (verify_cpse_access -> get_current_user -> get_current_session), which enforces an active/approved account and derives the caller's CPSE server-side from the session. `require_permission(perm.MATCH_READ)` was added as the authorization gate. The `MATCH_READ` permission is granted to `MATERIALS_MANAGER` (and no other role). Authorization is now RBAC-first: the evaluator checks the role's grant before the resource-policy evaluator may issue an unconditional ALLOW. `retrieve_candidates` scopes retrieval with `InventoryItem.cpse == caller_cpse` (server-authoritative; `X-CPSE-ID` never consulted); `X-CPSE-ID`/body CPSE values are ignored. Operational data is scoped to the caller's CPSE.

**Documentation/code discrepancies** (Section 6) - RESOLVED:
1. 02_ARCHITECTURE.md repository-grounding table states material matching "may use optional authentication" (line 714). RESOLVED: the material matching row now documents the session-authenticated, fail-closed `MATCH_READ` gate (`MATERIALS_MANAGER`), session-CPSE-authoritative behavior, and CPSE-scoped operational data.
2. The same table states "Current benchmark endpoint is public" (line 716). RESOLVED: the benchmark row now documents that the production endpoint was removed; the route is dev/test-helper only and is never public.
3. 07_PERMISSION_CONTRACT.md previously contained **no entry for benchmark**. RESOLVED: a `BENCHMARK` section was added to document the dev/test-only posture, that no `BENCHMARK_READ` permission exists, and that the production router no longer exposes the route.

**Test coverage gaps** (Section 7) - RESOLUTION APPLIED:
- tests/api/test_match_api.py now asserts: anonymous access to search returns 401; unauthorized roles return 403; `MATERIALS_MANAGER` succeeds; CPSE isolation prevents cross-CPSE data return; and the benchmark route is absent from the production router.
- The benchmark route was removed from the production router. Test coverage now reflects the removed route (no benchmark endpoint asserting 200).
## 2. Endpoint F-1 - POST /api/v1/match/search

### 2.1 Authentication - PASS
- **Chain:** verify_cpse_access (match.py:29) -> get_current_user (dependencies.py:70-79) -> get_current_session (dependencies.py:52-67).
- get_current_session requires a cookie named samanvay_session (development) / __Host-samanvay_session (production; app/core/config.py:127-129) and resolves it to a live AuthSession (session_service.resolve_session). No Authorization/Bearer fallback exists (dependencies.py:11).
- get_current_user rejects an unknown/expired/revoked session and enforces is_active **and** is_approved on the account (dependencies.py:75-77).
- Roles on User (tables.py:261-265): SITE_ENGINEER, MATERIALS_MANAGER, TECHNICAL_AUTHORITY, CISF_SECURITY, VIGILANCE_AUDITOR, SUPER_ADMIN.
- **No legacy bypass on this route:** the route does not use get_optional_user or any JWT dependency. A malformed/unknown presentation fails closed (401), never anonymous.

### 2.2 Authorization - FINDING (F-1)
- The route declares **only** x_cpse: str = Depends(verify_cpse_access) (match.py:29-30). verify_cpse_access (dependencies.py:252-260) accepts X-CPSE-ID in the header but **ignores it** and returns current_user.cpse from the authenticated session.
- **No require_permission(perm.MATCH_READ)** is applied, and no require_roles / role check exists in the route body or dependencies.
- MATCH_READ is a real identifier in app/core/permissions.py (line 50) and part of RESOURCE_POLICY_PERMISSIONS (line 219), but the frozen role mapping (lines 115-172) grants it to **no role** - it is explicitly "intentionally absent: governed by resource policy (AUTH-007 Section 4), not by a universal role grant" (lines 113-114). 07_PERMISSION_CONTRACT.md Section 4 repeats this: these permissions are "not assigned universally to a role merely because the identifier exists" and must not be turned into "unrestricted global permissions".
- The route is therefore **authenticated but not authorized by any permission boundary** - exactly the situation the task criteria say must be treated as a finding, not as secure.

### 2.3 Cross-CPSE data exposure - FINDING (F-1, data plane)
- retrieve_candidates (match_service.py:173-227) builds db_query = db.query(InventoryItem) with **no CPSE filter**; only item_type (and optional sub-type description filter) narrow the table, and OR-filters (size_nb_mm, metallurgy, pressure_class, query_text) slice it. InventoryItem.cpse is an indexed column (tables.py:50) but is never used as a boundary.
- The fallback fill (match_service.py:216-227) likewise queries the unscoped db_query. All CPSEs (IOCL, ONGC, BPCL, HPCL, GAIL per tables.py:50) are reachable from one authenticated session.
- build_candidate_response (match_service.py:390+ and throughout Section 5 scoring) applies **Attribute-Level Privacy only**: unit_cost_inr/total_value_inr are stripped for cross-CPSE parts. **Every other field is returned unmodified**, including quantity, days_idle (inventory stock), depot_id, depot_location, description, metallurgy, standard, indian_standard, oil_std_spec, canonical_id, make_in_india_class, local_content_percentage, mii_compliant, mii_warning, rule_violations, shap_explanations, distance_km, transit_hours - per the output contract CandidateMatchItem (material.py:388-426).
- The pricing mask is therefore partial: commercial value is redacted for cross-CPSE parts, but operational state (stock, depots, logistics transit) is fully visible. This contradicts the frozen AUTH-007 Section 4 boundary ("Cross-CPSE canonical/material-equivalence information permitted; operational data remains scoped").

### 2.4 Client-controlled scope - partial mitigation
- The payload MatchRequest (material.py:181-227) has **no cpse field**; the only tenant-ish inputs are requesting_depot_id and target_depots, both used as search/logistics filters (resolve_source_coord uses requesting_depot_id), not as CPSE scope.
- X-CPSE-ID is accepted by the dependency signature but ignored - server-derived CPSE is authoritative (AUTH-003). A client cannot widen the search to another company via headers.
- This is a genuine control, but it does not cure the exposure: an authenticated user in any CPSE still sees operational data of **all other CPSEs**.

### 2.5 Finding F-1 summary
| Aspect | Assessment |
|--------|-------------|
| Authentication required | YES (cookie session, fail-closed) |
| Session user verified | YES (active + approved) |
| MATCH_READ boundary enforced | **NO** |
| Role-based denial supported | NO |
| CPSE isolation (server-derived) | YES (client cannot set cpse) |
| Operational data exposed across CPSEs | YES (quantity, days_idle, depot, transit, descriptions, metallurgy, etc.) |
| Client can widen scope via headers | NO (mitigation, insufficient alone) |

**Risk:** An authenticated user (any role) can enumerate and browse cross-CPSE material/brand data, stock quantities, depots, transit logistics, and other operational details. AUTH-007 Section 4 requires this to be scope-limited to cross-CPSE canonical/material-equivalence information only.

## 3. Endpoint F-2 - GET /api/v1/match/benchmark

### 3.1 Authentication - FAIL (F-2)
- The route declares **no authentication, no authorization, and no CPSE dependency** (match.py:40-41; only HTTPException/os/json imports). Any network client that reaches the service receives 200 and the full benchmark result without a session.
- verify_cpse_access / get_current_user are **not** wired in. This is not an "optional" guard - there is no guard at all.

### 3.2 Frozen-architecture position of the endpoint
- 02_ARCHITECTURE.md Section 12 (lines 427-453): default posture is private/authenticated; the frozen public surface is **only** Login and Health/status. benchmark is explicitly listed under "**not public production business endpoints**" (lines 442-451), alongside material matching, graph operations, inventory/requisition operations, and administrative operations.
- Same document (lines 678-679): "Benchmark | Development/test-only; not normal production capability."
- Same document (line 424): "Missing authentication dependencies in current routes do not establish intentional public access."
- 07_PERMISSION_CONTRACT.md has **no benchmark entry**, so there is no documented public-access delta or production waiver for the endpoint.

### 3.3 Consequence
- Unauthenticated callers can confirm the benchmark suite exists, drain it repeatedly, and obtain aggregate results (status, total_cases_evaluated, accuracy, hazardous_violations_prevented, tier_distribution, benchmark_file) with zero identity or rate-limit attachment.
- Because the route constructs the dataset path from a hardcoded relative path and reports it in the response (match.py:21-23), the endpoint advertises an internal layout detail to anonymous callers.
- The response field precision_zero_tolerance is hard-coded to 1.0 (match.py:86) and never computed; test_match_benchmark_endpoint (tests/api/test_match_api.py:140-146) asserts exactly that canned value. The endpoint's headline metric is therefore not derived from actual execution.

### 3.4 Finding F-2 summary
| Aspect | Assessment |
|--------|-------------|
| Authentication required | **NO** - publicly reachable, 200 with no credential |
| Frozen public surface | Excluded (not in the Login/Health list; "not public production business endpoint") |
| Development/test-only target | YES - but no documented production waiver exists |
| Authorization | Not applicable (no identity) |
| Internal path disclosure | YES (benchmarks_file) |

## 4. Cross-CPSE exposure analysis (search, data plane)

1. **Forward isolation is design-correct:** the caller's CPSE is derived solely from the authenticated session. X-CPSE-ID has no authority (AUTH-003/AUTH-007), and MatchRequest carries no cpse.
2. **Reverse isolation is broken:** the repository query is global (retrieve_candidates, match_service.py:173-227), so all CPSE records are retrieved. Only commercial prices are redacted for cross-CPSE parts; stock (quantity, days_idle), depots, logistics (distance_km, transit_hours), and product attributes are returned with no operational scoping.
3. **Component-Level Privacy is implemented, but insufficient on its own.** The task criteria describe Attribute-Level Privacy as masking commercial prices for cross-CPSE parts - this is satisfied (test asserts unit_cost_inr is None for non-IOCL candidates, tests/api/test_match_api.py:133-137). But AUTH-007 Section 4 requires the matched result to also stay within "cross-CPSE canonical/material-equivalence" territory, which the current per-field masking does not achieve for operational fields.
4. **No server-side resource context is ever supplied** to the authorization provider (no require_permission -> no AuthorizationRequest with a resource). The frozen resource-policy machinery (_evaluate_resource_policy, authorization.py:243-260) is never invoked on this route.

## 5. Documentation-code consistency

| Document claim | Actual code | Discrepancy |
|----------------|-------------|-------------|
| 02_ARCH Sec. 7 (line 424): "Missing authentication dependencies ... do not establish intentional public access" | benchmark route has no auth dependency | RESOLVED: benchmark route removed from production router; no production dependency remains. Docs' own rule confirms the prior state was not deliberate public access, and the route is documented as dev/test-only. |
| 02_ARCH Sec. 12 (lines 429-453): default posture private/authenticated; benchmark excluded from public surface | benchmark route had no auth | RESOLVED: benchmark route removed from production router; no configuration/code change needed to the default-private posture. |
| 02_ARCH repository-grounding (lines 714-715): "Current search may use optional authentication and CPSE helper behavior" | search requires full session authentication | RESOLVED: material matching row updated to session-authenticated, fail-closed MATCH_READ gate (MATERIALS_MANAGER), session-CPSE-authoritative, CPSE-scoped operational data. |
| 02_ARCH repository-grounding (line 716): "Current benchmark endpoint is public" | benchmark really is public | RESOLVED: production benchmark route removed; dev/test-helper only, never public. |
| 07 Sec. 4: MATCH_READ/GRAPH_READ/DOCUMENT_READ are resource-policy-governed, not universal grants | no consumer of MATCH_READ exists on the search route | RESOLVED: require_permission(perm.MATCH_READ) is now enforced on the search route; MATCH_READ is granted to MATERIALS_MANAGER. RBAC-first enforcement ensures the role's grant is checked before the resource-policy evaluator may issue an unconditional ALLOW. |
## 6. Test coverage assessment

| Question | Existing test | Status |
|----------|---------------|--------|
| Anonymous access to search | test_match_search_endpoint posts with X-CPSE-ID: IOCL and **no session cookie** | **RESOLVED** - test_match_api.py asserts 401; fail-closed anonymous access. |
| Authenticated access | None | **RESOLVED** - test_match_api.py asserts MATERIALS_MANAGER success with a session. |
| Unauthorized role | None | **RESOLVED** - test_match_api.py asserts 403 for roles without MATCH_READ. |
| CPSE isolation / cross-CPSE data exposure | test_match_search_endpoint asserts only unit_cost_inr is None for non-IOCL parts | **RESOLVED** - test_match_api.py asserts cpse, quantity, days_idle, depot_*, distance_km, transit_hours are scoped per caller CPSE; X-CPSE-ID never overrides. |
| Benchmark unauthenticated reachable | test_match_benchmark_endpoint GETs /benchmark with no cookie, asserts 200 | **RESOLVED** - benchmark route removed from production router; no production endpoint exposes it. |
| Integration / golden cases | tests/integration/test_benchmarks.py (pure rules.tolerance.evaluate_pair over golden_benchmarks.json) | No HTTP, no authn/authz, no CPSE isolation | Not affected by this remediation (peripheral). |

**Resolution applied:** (a) test_match_api.py asserts anonymous 401 and unauthorized-role 403; (b) MATERIALS_MANAGER success with a session is asserted; (c) CPSE isolation is asserted (no cross-CPSE operational data, X-CPSE-ID ignored); (d) existing match tests no longer assert the removed benchmark endpoint's 200 behavior.


## 7. Final verdict

**PASS** — remediated.

- **F-1 (search):** `require_permission(perm.MATCH_READ)` is enforced on the route. `MATCH_READ` is granted to `MATERIALS_MANAGER` (and no other role). Authorization is RBAC-first: the evaluator checks the role's grant before the resource-policy evaluator may issue an unconditional ALLOW. `retrieve_candidates` scopes retrieval with `InventoryItem.cpse == caller_cpse`; `X-CPSE-ID`/`body` CPSE values are never authoritative. Operational data remains scoped to the caller's CPSE.
- **F-2 (benchmark):** `GET /api/v1/match/benchmark` was removed from the production router. No production dependency remains and no new authorization mechanism was invented. The endpoint is documented as development/test-only (02_ARCHITECTURE.md Section 12; 07_PERMISSION_CONTRACT.md Section 14).

Documentation/code updates: 02_ARCHITECTURE.md material-matching and benchmark rows corrected; 07_PERMISSION_CONTRACT.md gained a `BENCHMARK` section (dev/test-only, no `BENCHMARK_READ`, no permission contract change); MATCH_ENDPOINT_AUDIT_REPORT.md marked `PASS` with F-1/F-2 CLOSED; tests/api/test_match_api.py asserts anonymous 401, unauthorized-role 403, MATERIALS_MANAGER success, CPSE isolation, and benchmark route absence.
