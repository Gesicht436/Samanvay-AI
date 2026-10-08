# AUTH-006 — Session & Authentication Implementation Design

**Project:** Samanvay-AI
**Branch:** `auth-development-shourya`
**Status:** Implementation-ready design; limited implementation/business-rule details remain open as identified in Section 18
**Depends on:** AUTH-003, AUTH-004, AUTH-005
**Scope:** Application-layer implementation blueprint only

**Classification key:** **FROZEN/TARGET** records decisions from AUTH-003/004/005; **CURRENT** records inspected repository behavior; **IMPLEMENTATION DETAIL** describes how code should realize the target; **OPEN DECISION** identifies an unresolved implementation/deployment/business-rule value; **BLOCKER** means implementation must not proceed until the specified input is supplied.

| Section                  | Classification                                                                         |
| ------------------------ | -------------------------------------------------------------------------------------- |
| 1. Current → Target      | CURRENT evidence mapped to FROZEN/TARGET; implementation inventory.                    |
| 2. Authentication Flow   | FROZEN/TARGET outcomes and implementation detail.                                      |
| 3. Session Cookie        | FROZEN/TARGET properties; implementation detail; production origin configuration open. |
| 4. CSRF                  | FROZEN/TARGET requirement and implementation detail.                                   |
| 5. Dependencies          | FROZEN/TARGET layering; implementation interface.                                      |
| 6. Authorization         | FROZEN/TARGET boundaries and implementation integration.                               |
| 7. Security Events       | FROZEN/TARGET store/events; implementation emission/transaction detail.                |
| 8. Rate Limiting         | FROZEN/TARGET protection; interface detail; production thresholds/provider open.       |
| 9. Frontend Migration    | CURRENT-to-TARGET mapping; implementation detail.                                      |
| 10. JWT Cutover          | FROZEN/TARGET cutover; release timing open.                                            |
| 11. Transactions         | FROZEN/TARGET atomicity; implementation detail.                                        |
| 12. Errors               | FROZEN/TARGET non-enumeration/denial; HTTP mapping detail.                             |
| 13. Tests                | TARGET verification plan.                                                              |
| 14. Implementation Order | Implementation detail.                                                                 |
| 15. Files                | CURRENT paths and planned implementation responsibilities.                             |
| 16. Acceptance           | FROZEN/TARGET acceptance requirements.                                                 |
| 17. Non-Goals            | FROZEN scope boundaries.                                                               |
| 18. Open Decisions       | Only genuinely unresolved implementation/business/deployment details.                  |

---

## 1. Current → Target Mapping

**Classification:** CURRENT → FROZEN/TARGET mapping; implementation inventory.

The target uses AUTH-003's four layers:

`Identity → Authentication → Authorization → Resource/Tenant Policy`

It also uses AUTH-004 security requirements and AUTH-005 server-side sessions.

The implemented architecture does **not** preserve the legacy JWT/localStorage authentication model. In the table below, "Current" records the legacy pre-AUTH-006 behavior it replaced (migration history); "Target" is the implemented, verified reality.

| Current                                                                                        | Target                                                                                                                                                                                           | Code action                                                                                                                                        |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `auth.login_user` returns a signed JWT in `Token.access_token`.                                | Login creates `AuthSession`, records security events, sets an HttpOnly session cookie, and returns user data only.                                                                               | Replace JWT response/session creation flow in `backend/app/api/routers/auth.py`.                                                                   |
| `get_current_user` decodes a bearer JWT and loads `User` by `sub`; it checks `is_active` only. | Required authentication resolves the cookie to an `AuthSession`, validates lifetime/revocation, loads the user, and checks both `is_active` and `is_approved`.                                   | Replace bearer parsing in `backend/app/api/dependencies.py`.                                                                                       |
| `get_optional_user` maps missing, invalid, or expired JWTs to `None`.                          | Optional authentication is permitted only on explicitly public routes. No cookie means anonymous. A malformed, unknown, expired, revoked, inactive, or unapproved presented session returns 401. | Replace silent JWT downgrade in dependencies and remove optional-auth treatment from protected routes.                                             |
| `create_access_token` / `decode_access_token` use PyJWT.                                       | Session secret is generated and SHA-256 hashed as specified in AUTH-005. Raw secret exists only as the browser cookie value.                                                                     | Remove JWT functions/imports only after all callers are migrated. Retain bcrypt and unrelated hashing functions.                                   |
| `AuthContext` stores token/user in localStorage.                                               | Browser authentication credential is a Secure/HttpOnly cookie. Frontend identity is memory-only and restored through `/auth/me`.                                                                 | Remove authentication credential persistence from localStorage.                                                                                    |
| `fetchAPI` reads localStorage and adds `Authorization: Bearer`.                                | Same-origin requests use `credentials: include`; unsafe authenticated requests carry an in-memory CSRF token.                                                                                    | Replace bearer/localStorage logic in `frontend/src/lib/api.ts`.                                                                                    |
| `/auth/me` validates bearer JWT.                                                               | `/auth/me` validates the server-side session and account state.                                                                                                                                  | Retain endpoint purpose; replace dependency.                                                                                                       |
| Logout only clears browser state.                                                              | `POST /auth/logout` revokes the server-side session and clears the cookie after successful persistence.                                                                                          | Add backend logout endpoint/service and make frontend logout asynchronous.                                                                         |
| Public signup creates an unapproved account and returns a JWT.                                 | **Public self-registration is disabled.** Account provisioning is a privileged administrative operation.                                                                                         | Remove/disable public signup as an authentication path. Implement controlled account provisioning only through the AUTH-003 administrative policy. |
| Login exposes different inactive/unapproved responses.                                         | Login returns the same generic authentication failure for unknown, invalid, inactive, or unapproved credentials.                                                                                 | Replace outward account-state details.                                                                                                             |
| Frontend role checks gate pages.                                                               | Frontend checks remain UX controls only. Backend authentication, authorization, CPSE, and resource policy are authoritative.                                                                     | Preserve UI guard purpose; update identity source.                                                                                                 |
| Public seed endpoints can create/re-enable seed accounts and expose credentials.               | Seed/admin provisioning is development/test-only or controlled deployment infrastructure. No public production seed credential exposure.                                                         | Remove public production seed behavior and credential disclosure.                                                                                  |

The legacy JWT dependency inventory (now removed) was useful for the completed migration; it is **not** an authorization list.

Required-authentication routes currently include `/auth/me`, `/auth/users`, approval/rejection operations, audit feedback, and privileged inventory operations.

Optional-authentication currently appears on inventory, matching, and requisition routes.

During the completed migration, every route was classified against the frozen AUTH-003 route/resource policy. No route may remain anonymous merely because its current implementation lacks an authentication dependency.

The final target is:

* Public: login, health/status, and development-only documentation/OpenAPI.
* Private: all business data and business operations.
* No anonymous business mutations.
* No invalid-credential-to-anonymous downgrade.
* No client-controlled identity or tenant authority.

---

## 2. Authentication Flow

**Classification:** FROZEN/TARGET account and session outcomes plus implementation detail.

### Login

1. Validate the login request against the approved `UserLogin` contract. Apply request-size and schema validation before database work.

2. Normalize the username consistently with the existing login contract.

3. Query `User.username`.

4. For a missing user, perform dummy bcrypt verification using a fixed non-user hash to reduce timing-based username enumeration.

5. For an existing user, verify the supplied password using the existing bcrypt helper.

6. Check `is_active`.

7. Check `is_approved`.

8. If credentials or account state are invalid, return the same generic 401 response. Do not disclose whether the username exists or whether the account is inactive/unapproved.

9. Only after successful credentials and account-state checks, generate a fresh 32-byte CSPRNG session secret.

10. Encode the cookie value as unpadded base64url.

11. Compute SHA-256 over the raw secret bytes and store only the lowercase 64-character hexadecimal digest.

12. Never persist or log the raw session secret.

13. Create `AuthSession` with:

* UUIDv4 ID
* `user_id`
* session-token hash
* UTC timestamps
* configured expiry
* optional approved metadata fields

14. Insert `SESSION_CREATED` and `LOGIN_SUCCESS` `SecurityEvent` records.

15. Session creation and both successful-login events occur in one PostgreSQL transaction.

16. If persistence fails, roll back and do not issue the session cookie.

17. After successful commit, issue the session cookie using Section 3.

18. Return the public `UserResponse`. Do not return:

* JWT
* access token
* refresh token
* raw session secret
* session ID
* authorization token
* CPSE authorization token.

19. The frontend then obtains a session-bound CSRF token through `GET /api/v1/auth/csrf`.

For unknown username, wrong password, inactive account, and unapproved account:

* status: 401
* outward message: generic authentication failure
* no account-state disclosure
* `LOGIN_FAILURE` recorded when possible
* `user_id` populated only when a matching user row exists
* `session_id = NULL`
* internal reason code may be stored in event metadata.

If required security-event persistence fails, the authentication operation remains denied.

### Logout

* Read the configured session cookie.
* Do not accept a user ID or session ID from the request body.
* Validate the request Origin.
* For a live session, require the session-bound CSRF token.
* Resolve the session using the cookie-derived hash.
* If the session does not exist, is malformed, expired, or already revoked, return idempotent 204 after Origin validation and clear the cookie.
* For a live session, set `revoked_at`.
* Insert `SESSION_REVOKED` and `LOGOUT`.
* Commit revocation and events atomically.
* Clear the cookie only after successful commit.
* Do not emit duplicate revocation/logout events for an already-revoked session.
* If persistence fails, return a retryable 503 rather than falsely reporting successful logout.

### Authenticated Request

1. Extract the configured session cookie.
2. Do not accept an `Authorization: Bearer` fallback.
3. Strictly decode canonical base64url.
4. Require exactly 32 decoded bytes.
5. SHA-256 hash the raw bytes.
6. Look up the session through the indexed hash.
7. Reject unknown, revoked, or expired sessions with 401.
8. Load the user through `AuthSession.user_id`.
9. Require `is_active = TRUE`.
10. Require `is_approved = TRUE`.
11. Update `last_seen_at`.
12. Commit that session update.
13. Construct a server-derived principal containing user identity, role, CPSE, depot, account state, and current session.
14. Pass that principal to centralized authorization/resource policy.

A disabled or unapproved account cannot continue using an existing session because account state is checked on every authenticated request.

### Account Provisioning

**Public self-registration is disabled.**

The target account lifecycle is:

`SUPER_ADMIN provisions account → account active/unapproved → SUPER_ADMIN separately approves → account becomes usable`

Account provisioning must:

* require the appropriate administrative authorization;
* assign role through server-controlled policy;
* assign CPSE/depot through server-controlled policy;
* never trust client-selected role, CPSE, or depot as authorization;
* create no usable session before approval;
* record the appropriate security event;
* keep creation and approval as separate operations.

No public `/auth/signup` path may create accounts in the target production API.

### Account Approval

Approval is a separate administrative operation.

The operation must:

* authenticate the acting administrator;
* authorize the operation through centralized policy;
* validate target account state;
* set `is_approved = TRUE`;
* record `ACCOUNT_APPROVED`;
* preserve the separation between account creation and account approval.

Approval does not automatically create a browser session.

### Account Rejection

Rejection is an administrative operation subject to centralized authorization and target-state validation.

The implementation must record `ACCOUNT_REJECTED` with the acting administrator/session as the event identity.

If the target account row is deleted, the event's `user_id`/`session_id` refer to the actor, not the deleted target. Target identity may be stored in sanitized metadata as defined by the SecurityEvent schema.

### Disabled Account

For account disablement:

* set `is_active = FALSE`;
* revoke the user's active sessions;
* record `ACCOUNT_DISABLED`;
* record relevant `SESSION_REVOKED` events;
* perform account-state and session changes atomically.

No new administrative disable endpoint should be invented solely by AUTH-006 if the existing authorized account-management scope does not contain it.

---

## 3. Session Cookie Specification

| Attribute                   | Target contract                                                                         |
| --------------------------- | --------------------------------------------------------------------------------------- |
| Production name             | `__Host-samanvay_session`                                                               |
| Local HTTP development name | `samanvay_session`                                                                      |
| `HttpOnly`                  | Always `true`.                                                                          |
| `Secure`                    | Required outside local HTTP development. Production must reject insecure configuration. |
| `SameSite`                  | `Lax`.                                                                                  |
| `Path`                      | `/`.                                                                                    |
| `Domain`                    | Omitted. Host-only cookie.                                                              |
| `Max-Age` / `Expires`       | Derived from the same `AuthSession.expires_at`.                                         |
| JavaScript access           | Forbidden.                                                                              |
| Credential delivery         | Browser-managed cookie through same-origin API requests.                                |

The production cookie uses the `__Host-` prefix and therefore must not specify a Domain attribute and must use Secure + Path `/`.

The local development cookie may use `samanvay_session` because localhost HTTP cannot satisfy the Secure requirement.

Production browser origins must be supplied through deployment configuration.

Do not derive an allowed origin from an untrusted Host or forwarded-host header.

The existing Next.js rewrite must be verified to preserve:

* incoming Cookie headers;
* outgoing Set-Cookie headers.

---

## 4. CSRF Strategy

Use a session-bound synchronizer token combined with strict Origin validation.

HttpOnly protects the session secret from JavaScript but does not eliminate CSRF.

### Safe Methods

`GET`, `HEAD`, and `OPTIONS` must not mutate application state.

Existing GET endpoints with side effects, including seed behavior, must not remain public.

### Unsafe Methods

Browser state-changing requests using cookie authentication require:

* valid session;
* valid session-bound CSRF token;
* exact allowed Origin.

This applies to:

* account administration;
* logout;
* inventory mutations;
* requisition mutations;
* audit feedback;
* ingestion;
* other protected state-changing business operations.

### CSRF Token

Derive the token deterministically from the session secret/hash according to AUTH-005-compatible implementation:

`HMAC-SHA256(key=session-secret-derived material, message="samanvay-csrf-v1")`

The implementation must not persist the CSRF token in the database.

Add:

`GET /api/v1/auth/csrf`

It:

* requires a valid session;
* returns the derived token;
* sets `Cache-Control: no-store`;
* does not expose the session cookie.

The frontend stores the CSRF token in memory only.

### Origin Validation

Compare the request Origin against an explicit configured allowlist.

Do not trust arbitrary:

* `Host`
* `X-Forwarded-Host`
* other client-supplied proxy headers.

Missing/invalid Origin or CSRF token returns 403 before mutation.

Emit `AUTHORIZATION_FAILURE` when an authenticated principal is available.

### Read-Only POSTs

A POST endpoint may omit the CSRF token only if it is explicitly verified to be strictly side-effect-free and classified accordingly.

This does not make an otherwise public business mutation acceptable.

---

## 5. Authentication Dependencies

Target FastAPI flow:

```text
get_db_session
        ↓
get_current_session
        ↓
get_current_user
        ↓
require_permission(...)
        ↓
resource / tenant policy
        ↓
service
        ↓
repository / DB
```

### `get_current_session`

Responsibilities:

* read session cookie;
* validate format;
* hash secret;
* indexed session lookup;
* verify expiry;
* verify revocation;
* return session principal context.

It must not:

* decode JWTs;
* accept bearer authentication;
* trust client identity fields.

### `get_current_user`

Responsibilities:

* load User from the validated session;
* verify active state;
* verify approved state;
* update `last_seen_at`;
* return server-derived identity.

### Optional Authentication

Optional authentication is retained only where a route is explicitly public and identity is genuinely optional.

For a public route:

* no cookie → anonymous;
* valid cookie → authenticated personalization if explicitly supported;
* malformed/unknown/expired/revoked cookie → 401;
* inactive/unapproved account → 401.

Invalid credentials must never silently become anonymous.

All business operations are private unless explicitly classified as one of the frozen public categories.

### Authorization Dependency

`require_permission(...)` delegates to the centralized AUTH-003 authorization policy.

It must not become another scattered collection of role comparisons.

The authorization layer receives:

* authenticated user;
* role;
* CPSE;
* depot;
* operation;
* resource context;
* workflow state where relevant.

It evaluates:

`permission → CPSE → resource/ownership → workflow authority`

---

## 6. Authorization Boundary

Authentication establishes identity.

Authorization establishes whether that identity may perform the requested operation.

Resource/tenant policy establishes whether the requested resource is within the authorized scope.

### Frozen Authorization Rules

The following policies are authoritative.

#### Requisition

| Operation                    | Authorized role                          |
| ---------------------------- | ---------------------------------------- |
| Create                       | SITE_ENGINEER                            |
| Approve Standard/Low Value   | MATERIALS_MANAGER                        |
| Approve Technical/High Value | TECHNICAL_AUTHORITY                      |
| Reject                       | MATERIALS_MANAGER or TECHNICAL_AUTHORITY |
| Issue Gate Pass              | CISF_SECURITY                            |
| Dispatch                     | MATERIALS_MANAGER                        |
| Deliver/Receive              | SITE_ENGINEER                            |
| Audit/Oversight              | VIGILANCE_AUDITOR, read-only             |
| System administration        | SUPER_ADMIN                              |

Classification between Standard/Low Value and Technical/High Value is server-controlled using deterministic business rules. The requester cannot select a category merely to influence the approver.

#### Requisition Visibility

* SITE_ENGINEER: own requisitions only.
* MATERIALS_MANAGER: requisitions within own CPSE.
* TECHNICAL_AUTHORITY: relevant Technical/High Value requisitions.
* CISF_SECURITY: requisitions while gate-pass action is required.
* VIGILANCE_AUDITOR: only when required for an explicitly authorized audit.
* SUPER_ADMIN: no automatic operational requisition visibility.

Cross-CPSE operational requisition access is prohibited.

#### Inventory

* MATERIALS_MANAGER: create/add/update, status changes, stock verification/reconciliation, surplus/obsolete identification, dispatch.
* SITE_ENGINEER: receive/confirm delivered material.
* VIGILANCE_AUDITOR: read-only inventory/audit oversight.
* TECHNICAL_AUTHORITY: no general inventory authority; only workflow-required access.
* CISF_SECURITY: no general inventory authority; only workflow-required access.
* SUPER_ADMIN: system administration only; no implicit inventory workflow permission.

Authenticated users may view inventory within their own CPSE according to role/resource policy.

Disposal/write-off authorization remains outside Samanvay-AI.

#### Audit

VIGILANCE_AUDITOR may:

* view audit records;
* create audit findings/observations;
* add audit feedback/comments;
* view/export audit history.

VIGILANCE_AUDITOR may not:

* modify requisitions;
* modify inventory;
* dispatch/deliver materials;
* issue gate passes;
* perform operational workflow actions.

Finding verification/final closure is performed by a separate management authority rather than the auditor or SUPER_ADMIN.

Management response:

* MATERIALS_MANAGER for operational/material-related findings;
* TECHNICAL_AUTHORITY for technical findings.

The exact existing-role implementation mapping for final finding closure is a remaining business-detail question if required by the current codebase.

#### Cross-CPSE Audit

Cross-CPSE audit access is permitted only through explicit case-specific authorization.

When authorized, the auditor may access the complete evidentiary set necessary for that audit, including when required:

* audit finding;
* supporting documents;
* related requisitions;
* related inventory.

The access remains:

* read-only;
* audit-purpose-only;
* explicitly authorized;
* CPSE-scoped to the approved audit context;
* auditable.

#### Material Matching

Cross-CPSE canonical/material-equivalence information is permitted.

This does **not** authorize access to another CPSE's:

* stock;
* inventory;
* depot;
* requisition;
* operational logistics;
* other operational data.

#### Graph

Cross-CPSE canonical/material relationships are permitted.

Operational graph data remains CPSE-isolated, including:

* inventory/stock;
* depots;
* logistics routes;
* requisitions.

#### Documents

Normal users access documents within their own CPSE.

VIGILANCE_AUDITOR may access documents needed for legitimate audit responsibilities.

Cross-CPSE document access requires explicit audit authorization.

#### Ingestion

Catalog/document ingestion requires:

* authenticated session;
* appropriate permission;
* CPSE/resource policy;
* validation;
* audit/security telemetry.

The authorized operational roles are:

* MATERIALS_MANAGER;
* SUPER_ADMIN, subject to the distinction that SUPER_ADMIN's system-administration authority does not automatically grant business-data visibility.

#### SUPER_ADMIN

SUPER_ADMIN is a system-administration role.

It does not automatically inherit:

* inventory workflow authority;
* requisition workflow authority;
* audit authority;
* cross-CPSE operational visibility;
* tenant bypass;
* ownership bypass;
* security-control bypass.

### Client-Controlled Identity

The following must never establish authorization:

* request-body user ID;
* request-body role;
* request-body CPSE;
* request-body depot;
* `X-CPSE-ID`;
* requester field;
* approved-by field;
* issuing-officer field;
* arbitrary path/query user identifiers.

The authenticated session establishes actor identity.

The authenticated user's CPSE establishes the normal tenant boundary.

`X-CPSE-ID` is never an authorization mechanism.

### Resource Authorization Sequence

For resource-addressed operations:

```text
resource existence handling
        ↓
authentication
        ↓
permission
        ↓
CPSE/tenant policy
        ↓
ownership / operational authority
        ↓
workflow-state authorization
        ↓
operation
```

The implementation must avoid turning unauthorized resource IDs into a reliable existence oracle.

---

## 7. Security Events

`SecurityEvent` is the authoritative authentication/security telemetry store.

Do not duplicate authentication events into `SovereignAuditLedger`.

Required event types:

| Event                   | Trigger                                                |
| ----------------------- | ------------------------------------------------------ |
| `LOGIN_SUCCESS`         | Successful credential authentication                   |
| `LOGIN_FAILURE`         | Failed authentication                                  |
| `SESSION_CREATED`       | Session creation                                       |
| `SESSION_REVOKED`       | Session revocation                                     |
| `LOGOUT`                | Successful authenticated logout                        |
| `PASSWORD_CHANGED`      | Password change when implemented                       |
| `ACCOUNT_APPROVED`      | Administrative approval                                |
| `ACCOUNT_REJECTED`      | Administrative rejection                               |
| `ACCOUNT_DISABLED`      | Administrative disablement                             |
| `ACCOUNT_LINKED`        | Account linking when implemented                       |
| `AUTHORIZATION_FAILURE` | Authorization/security-policy denial                   |
| `RATE_LIMIT_TRIGGERED`  | Abuse-control block                                    |

Do not invent additional authentication event types merely to represent implementation convenience.

Never store:

* password;
* password hash;
* raw session secret;
* session-token hash where prohibited by event schema;
* CSRF token;
* JWT;
* access token;
* refresh token;
* secret-bearing request body.

Security-event writes associated with security-sensitive state changes occur in the same transaction as the state change.

---

## 8. Rate Limiting / Abuse Controls

A product-neutral rate-limit interface is required.

```text
RateLimitGuard.consume(
    scope,
    opaque_subject,
    client_ip,
    now
)
    → allowed | retry_after_seconds
```

Required abuse-control surfaces:

* login;
* account recovery when implemented.

**Public signup is disabled**, so no production signup abuse surface exists in the target API.

A rate-limit denial:

* returns 429;
* provides bounded `Retry-After`;
* records `RATE_LIMIT_TRIGGERED`;
* does not disclose account existence.

Rate-limit backend failure must fail closed for authentication abuse surfaces.

Production thresholds and shared implementation remain deployment/security-policy configuration rather than architecture decisions.

---

## 9. Frontend Migration

### AuthContext

Remove:

* authentication token localStorage;
* authentication user localStorage;
* bearer-token state;
* token restoration.

Maintain:

* in-memory user;
* in-memory CSRF token;
* loading/auth-restoration state.

### Startup

Call `/auth/me` with credentials.

On success:

* populate user;
* obtain CSRF token.

On 401:

* clear in-memory authentication.

On transient server/network failure:

* keep authentication state unresolved rather than falsely declaring logout.

### Login

Send username/password using credentials-enabled request.

The server sets the cookie.

Frontend receives no authentication credential.

After successful login:

* obtain `/auth/me`;
* obtain CSRF token;
* establish in-memory authenticated state.

### Signup

The production frontend must not expose public self-registration because the target architecture disables public signup.

Any legacy signup page must therefore be removed from the production navigation/API flow or converted to the approved administrative provisioning flow.

It must never create an authenticated dashboard state.

### Logout

`AuthContext.logout` becomes asynchronous.

It:

1. sends `POST /auth/logout`;
2. supplies CSRF token;
3. waits for server response;
4. clears local in-memory identity only after successful revocation;
5. handles retryable server failures without falsely reporting logout.

### API Client

`api.ts` must:

* use `credentials: 'include'`;
* remove Authorization bearer injection;
* remove auth localStorage access;
* attach CSRF header to applicable unsafe authenticated requests;
* handle 401 as session expiry;
* preserve authenticated state on 403.

### ProtectedRoute

ProtectedRoute remains a UI control.

It does not enforce security.

The backend remains authoritative.

### Seed UI

Production UI must not display:

* seed personas;
* shared seed passwords;
* public seed-account provisioning.

Development/test seed behavior must be explicitly gated.

---

## 10. JWT Cutover (Completed by AUTH-006)

**STATUS: EXECUTED.** The sequence below records the completed finite session cutover; no JWT authentication path remains in the repository.

Use AUTH-005's finite session cutover.

Existing JWTs were not migrated into sessions.

Implementation sequence:

1. Apply the required versioned database migration.

2. Implement session authentication and tests.

3. Replace required and optional JWT dependencies.

4. Search the entire repository for:

   * `HTTPBearer`
   * `Authorization: Bearer`
   * `decode_access_token`
   * `create_access_token`
   * `get_optional_user`
   * JWT-specific response models.

5. Migrate frontend API/context/UI to cookie authentication.

6. Coordinate application cutover.

7. Stop old JWT-serving instances.

8. Deploy the session-only backend/frontend.

9. Old JWTs fail after cutover.

10. Users authenticate again and receive new sessions.

11. Remove PyJWT/JWT configuration/helpers only after global caller search confirms they are unused. (Completed: JWT helpers were removed with the cutover, and the unused PyJWT dependency was dropped in Task 16A.)

There must be no indefinite hybrid JWT/session authentication mode.

---

## 11. Transaction Boundaries

### Login

One transaction:

```text
credential/account validation
        ↓
AuthSession insert
        +
SESSION_CREATED
        +
LOGIN_SUCCESS
        ↓
COMMIT
        ↓
Set-Cookie
```

### Logout

One transaction:

```text
revoked_at update
        +
SESSION_REVOKED
        +
LOGOUT
        ↓
COMMIT
        ↓
Clear cookie
```

### Account Approval

One transaction:

```text
is_approved = true
        +
ACCOUNT_APPROVED
        ↓
COMMIT
```

### Account Rejection

One transaction:

```text
target rejection/deletion
        +
ACCOUNT_REJECTED
        ↓
COMMIT
```

The event identifies the acting administrator rather than a deleted target.

### Account Disablement

One transaction:

```text
is_active = false
        +
session revocation
        +
ACCOUNT_DISABLED
        +
SESSION_REVOKED
        ↓
COMMIT
```

### Account Provisioning

Administrative account creation must create the account in its initial unapproved state.

It does not create a session.

Creation and approval remain separate operations.

### Signup

Public signup is disabled in the target architecture.

No signup transaction is required in the target production authentication flow.

### Migration

Database schema evolution must use the separately selected versioned migration mechanism.

`create_all()` is not schema migration.

---

## 12. Error Semantics

| Condition                                     | Target response/behavior                          |
| --------------------------------------------- | ------------------------------------------------- |
| Missing cookie on required route              | 401                                               |
| Malformed cookie                              | 401; clear cookie                                 |
| Unknown session                               | 401; clear cookie                                 |
| Expired session                               | 401; clear cookie                                 |
| Revoked session                               | 401; clear cookie                                 |
| Inactive account                              | 401; generic                                      |
| Unapproved account                            | 401; generic                                      |
| Unknown username                              | Same generic login 401                            |
| Wrong password                                | Same generic login 401                            |
| Login persistence failure                     | 503; no session cookie                            |
| Logout persistence failure                    | 503; do not claim successful server logout        |
| Invalid/missing CSRF                          | 403                                               |
| Invalid Origin                                | 403                                               |
| Insufficient permission                       | 403                                               |
| Rate limit                                    | 429                                               |
| Unknown protected resource                    | Must not disclose unauthorized resource existence |
| Validation error                              | 422 where appropriate                             |
| Public route with malformed presented session | 401, not anonymous downgrade                      |

401 clears frontend authentication state.

403 does not imply that the session has expired.

API responses must never expose:

* session secret;
* password;
* password hash;
* token;
* CSRF token;
* internal credential material.

---

## 13. Testing Blueprint

Use isolated FastAPI test fixtures and test database state.

### Session

Test:

* valid session;
* absent cookie;
* malformed cookie;
* wrong-length cookie;
* unknown session hash;
* expired session;
* revoked session;
* inactive account;
* unapproved account;
* `last_seen_at` update;
* logout revocation;
* idempotent repeated logout;
* transaction rollback.

### Login

Test:

* successful authentication;
* one session creation;
* required success events;
* unknown username;
* incorrect password;
* inactive account;
* unapproved account;
* generic external response;
* dummy password verification;
* raw secret never persisted;
* no access token in response;
* correct cookie flags;
* persistence failure;
* rate-limit enforcement before expensive password verification.

### Account Administration

Test:

* only authorized administrator can provision accounts;
* new accounts are unapproved;
* provisioning does not create sessions;
* client-selected role cannot establish privilege;
* client-selected CPSE cannot establish tenant membership;
* approval is separate from creation;
* approval creates appropriate event;
* rejection validates target state;
* administrative actions record the acting principal.

### CSRF

Test:

* valid Origin + valid token;
* missing token;
* invalid token;
* malformed token;
* invalid Origin;
* safe methods;
* state-changing methods;
* no mutation after CSRF rejection;
* token `no-store`;
* token not persisted in browser storage;
* token not logged.

### Authorization

Test every frozen policy category:

* requisition creation;
* Standard/Low approval;
* Technical/High approval;
* rejection;
* gate pass;
* dispatch;
* delivery/receipt;
* requisition visibility;
* inventory operations;
* inventory visibility;
* audit operations;
* management response;
* cross-CPSE audit authorization;
* material matching cross-CPSE canonical access;
* graph canonical cross-CPSE access;
* operational graph isolation;
* document CPSE isolation;
* ingestion permissions;
* SUPER_ADMIN non-bypass behavior.

### CPSE Isolation

Test that:

* authenticated user cannot access another CPSE's operational inventory;
* authenticated user cannot access another CPSE's requisition;
* authenticated user cannot access another CPSE's depot/stock/logistics data;
* `X-CPSE-ID` cannot broaden authorization;
* request-body CPSE cannot broaden authorization;
* SUPER_ADMIN does not bypass tenant isolation;
* explicitly authorized cross-CPSE audit context works only for the approved audit.

### Frontend

Test:

* session restoration;
* no auth token in localStorage/sessionStorage;
* no bearer header;
* CSRF token memory-only;
* 401 clears identity;
* 403 preserves identity;
* logout waits for server response;
* production UI does not expose seed credentials;
* public signup is unavailable;
* authentication state is not inferred from client-controlled role data.

### JWT Regression

After cutover, test that bearer JWTs are rejected across all previously JWT-protected routes.

---

## 14. Implementation Order

1. **Preflight contracts**

   * confirm centralized permission-provider interface;
   * confirm exact permission vocabulary;
   * confirm session configuration values;
   * confirm deployment origin configuration;
   * confirm migration mechanism.

2. **Database/model layer**

   * implement `AuthSession`;
   * implement `SecurityEvent`;
   * apply exact AUTH-005 types/FKs/indexes.

3. **Session service**

   * random secret generation;
   * hashing;
   * lookup;
   * creation;
   * revocation;
   * expiry;
   * account-state handling;
   * `last_seen_at`.

4. **CSRF**

   * session-bound token derivation;
   * Origin validation;
   * constant-time token comparison;
   * `/auth/csrf`.

5. **Rate-limit interface**

   * product-neutral interface;
   * test implementation;
   * production provider injection.

6. **Authentication dependencies**

   * required session;
   * optional public-session handling;
   * current-user resolution;
   * account-state enforcement.

7. **Central authorization integration**

   * permission adapter;
   * CPSE policy;
   * resource policy;
   * workflow-state checks.

8. **Authentication/admin endpoints**

   * login;
   * `/me`;
   * logout;
   * CSRF;
   * administrative account provisioning/approval/rejection;
   * controlled seed behavior.

9. **Route migration**

   * migrate all JWT dependencies;
   * eliminate anonymous business mutations;
   * apply frozen resource/CPSE policies;
   * apply CSRF to unsafe cookie-authenticated operations.

10. **Frontend**

    * AuthContext;
    * API client;
    * protected routing;
    * logout;
    * authentication UI;
    * removal of localStorage credentials.

11. **JWT cutover (completed)**

    * coordinated deployment;
    * reject old JWTs;
    * remove obsolete JWT code.

12. **Security verification**

    * execute Section 13;
    * perform repository-wide search;
    * verify no unrelated business behavior changed.

---

## 15. Files-to-Change Plan

### Expected to change

| Path                                          | Responsibility                                                                                 |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `backend/app/models/tables.py`                | Add `AuthSession` and `SecurityEvent`.                                                         |
| `backend/app/api/routers/auth.py`             | Login, `/me`, logout, CSRF, account administration, controlled seed behavior.                  |
| `backend/app/api/dependencies.py`             | Session resolution, current user, authorization integration, CPSE/resource policy integration. |
| `backend/app/core/security.py`                | Retain bcrypt and required hashing; JWT helpers already removed (cutover complete).            |
| `backend/app/core/config.py`                  | Session/cookie/origin/rate-limit configuration and validation.                                 |
| `backend/main.py`                             | Security middleware/integration, CORS restrictions, controlled startup behavior.               |
| `backend/app/services/seeder.py`              | Development/test-only seed behavior.                                                           |
| `backend/app/api/routers/audit.py`            | Session authentication, audit authorization, CSRF for mutations.                               |
| `backend/app/api/routers/inventory.py`        | Session authentication, inventory authorization, CPSE/resource policy, CSRF.                   |
| `backend/app/api/routers/match.py`            | Session handling and approved cross-CPSE canonical matching policy.                            |
| `backend/app/api/routers/requisition.py`      | Session authentication, requisition workflow/visibility policy, CSRF.                          |
| `backend/app/api/routers/ingest.py`           | Authenticated ingestion policy and CSRF.                                                       |
| `backend/app/api/routers/graph.py`            | Session/CPSE policy where required by graph resource classification.                           |
| `backend/app/schemas/auth.py`                 | Session-safe response models.                                                                  |
| `frontend/src/context/AuthContext.tsx`        | Memory-only identity and CSRF state.                                                           |
| `frontend/src/lib/api.ts`                     | Cookie credentials and CSRF.                                                                   |
| `frontend/src/lib/types.ts`                   | Session-safe auth types.                                                                       |
| `frontend/src/components/ProtectedRoute.tsx`  | Server-derived identity handling.                                                              |
| `frontend/src/components/Sidebar.tsx`         | Server logout.                                                                                 |
| `frontend/src/components/UserHeaderBadge.tsx` | Server logout.                                                                                 |

### Expected to be created

| Path                                           | Responsibility                                    |
| ---------------------------------------------- | ------------------------------------------------- |
| `backend/app/services/auth_session_service.py` | Session lifecycle.                                |
| `backend/app/core/csrf.py`                     | CSRF token derivation/validation.                 |
| `backend/app/services/auth_rate_limit.py`      | Rate-limit interface.                             |
| `tests/api/test_session_auth_api.py`           | Session/auth/security-event tests.                |
| `tests/api/test_csrf_api.py`                   | CSRF/Origin tests.                                |
| `tests/api/test_authorization_api.py`          | Central authorization/CPSE/resource policy tests. |
| `tests/api/test_rate_limit_auth.py`            | Rate-limit tests.                                 |

### Expected to be removed/deprecated

After repository-wide cutover (completed — see Section 10):

* JWT response models;
* bearer-token injection;
* authentication localStorage keys;
* JWT helpers;
* obsolete JWT settings;
* public production seed credential exposure;
* public self-registration endpoint;
* seed UI that exposes shared credentials.

No migration framework is selected by AUTH-006.

---

## 16. Acceptance Criteria

AUTH-006 implementation is complete only when:

1. Browser authentication uses server-side `AuthSession`.
2. No JWT authentication fallback remains.
3. Raw session secrets are never stored or logged.
4. Only the AUTH-005 session-secret hash is persisted.
5. Cookie attributes match Section 3.
6. Browser JavaScript cannot read the session cookie.
7. Public self-registration is disabled.
8. Administrative provisioning creates unapproved accounts without sessions.
9. Approval is separate from account creation.
10. Inactive/unapproved accounts cannot authenticate or use existing sessions.
11. Logout revokes the server-side session.
12. Logout is idempotent.
13. Authentication credentials are absent from localStorage/sessionStorage.
14. No bearer authentication remains.
15. CSRF/Origin controls protect applicable unsafe browser requests.
16. Security events use `SecurityEvent` as the authoritative authentication/security telemetry store.
17. Authentication state changes and required security events are transactional.
18. Login/authentication abuse surfaces use the rate-limit interface.
19. All business APIs are private by default.
20. No anonymous business mutation remains.
21. CPSE is derived from authenticated identity.
22. `X-CPSE-ID` cannot establish tenant authorization.
23. Cross-CPSE operational access is denied.
24. Explicit cross-CPSE canonical/material-equivalence access works only where authorized.
25. Explicit cross-CPSE audit access works only through approved audit authorization.
26. SUPER_ADMIN does not bypass tenant/resource/security controls.
27. Requisition workflow permissions match AUTH-003.
28. Inventory permissions match AUTH-003.
29. Audit permissions match AUTH-003.
30. Resource IDs cannot bypass ownership/operational-authority checks.
31. Frontend authorization remains UX-only.
32. JWTs are rejected after coordinated cutover.
33. Required security regression tests pass.
34. No unrelated business behavior is changed beyond explicitly approved authentication, authorization, tenant-policy, and CSRF integration.
35. Versioned database migration is applied before session-dependent application rollout.
36. `create_all()` is not used as schema evolution.

---

## 17. Explicit Non-Goals

AUTH-006 does **not** implement or redesign:

* Google OAuth/OIDC implementation or `OAuthIdentity` persistence. OIDC/Google is not part of the current authentication target; any future reintroduction requires an explicit approved task. The credential-authority direction is External Organizational Authority / Federation (`10_DECISIONS.md` D-CRED-1); its exact protocol/provider remains an open architecture decision. The local password store remains the **prototype credential authority** (development/demo authentication) for the submitted prototype — not organizational password ownership and not the production CPSE identity architecture; production delegation of credential verification to the organization-approved credential authority is deployment-specific and unresolved (Task 17).
* Password reset/recovery.
* Email verification.
* Step-up authentication/MFA.
* Session-management UI/device management.
* Selection of an external rate-limit product.
* Selection of migration tooling.
* Production domain changes.
* Unrelated business workflow redesign.
* Disposal/write-off authority.
* Granting SUPER_ADMIN universal business-data authority.
* Automatic cross-CPSE operational access.
* Changing the frozen CPSE boundary.
* Reopening the frozen requisition, inventory, audit, document, matching, or graph authorization policies.

AUTH-006 implements the frozen authorization architecture; it does not redesign it.

---

## 18. Open Decisions and Blocking Inputs

Only the following items remain genuinely open.

### 1. Exact Permission Vocabulary / Provider Interface — IMPLEMENTATION BLOCKER

AUTH-003 freezes centralized authorization and the role grants, but the exact code-level permission keys/provider interface may still need to be defined.

Before implementing `require_permission`, establish:

* permission identifiers;
* policy-provider interface;
* role-to-permission mapping;
* resource-context interface.

Do not reintroduce scattered role comparisons.

The role grants themselves are **not open architecture decisions**.

### 2. Exact Deterministic Requisition Classification Rules — BUSINESS-RULE INPUT

AUTH-003 already freezes:

* Standard/Low Value → MATERIALS_MANAGER;
* Technical/High Value → TECHNICAL_AUTHORITY.

What remains is the exact deterministic rule set used by Samanvay-AI to classify a requisition.

The requester must not control the classification.

### 3. Finding-Closure Role Mapping — BUSINESS IMPLEMENTATION DETAIL

AUTH-003 freezes that final finding verification/closure is performed by a separate management authority, not VIGILANCE_AUDITOR or SUPER_ADMIN.

If the current repository requires a concrete existing-role mapping, that mapping must be defined before implementation.

Do not grant closure authority to the auditor or SUPER_ADMIN merely because no mapping currently exists.

### 4. Cross-CPSE Audit Authorization Mechanics — IMPLEMENTATION DETAIL

The policy is frozen:

* case-specific;
* explicit;
* audit-purpose-only;
* read-only;
* complete necessary evidentiary access;
* auditable.

The implementation still needs to define the concrete representation and lifecycle of that authorization, including:

* granting authority;
* scope;
* expiry/revocation;
* audit context;
* enforcement mechanism;
* security-event context.

This is an implementation-detail question, not a reopening of the cross-CPSE policy.

### 5. Session Product/Deployment Values — OPEN CONFIGURATION

AUTH-005 leaves specific deployment values such as:

* absolute session expiry;
* idle/session policy;
* concurrent-session behavior;
* session metadata;
* SecurityEvent retention.

These must be configured before production deployment.

They do not change the server-side-session architecture.

### 6. Rate-Limit Provider and Thresholds — OPEN DEPLOYMENT VALUE

The application interface and fail-closed behavior are defined.

Production still needs:

* shared implementation;
* thresholds;
* windows;
* deployment configuration.

No particular external product is mandated by AUTH-006.

### 7. Production Browser Origin — OPEN DEPLOYMENT VALUE

Configure the exact HTTPS browser origin(s) used by the deployed application.

The session cookie remains host-only with Domain omitted.

### 8. Migration Tooling — OPEN IMPLEMENTATION VALUE

AUTH-005 requires a versioned migration mechanism.

The repository-specific migration tool must be selected before implementing the schema migration.

`create_all()` must not be substituted for versioned migration.

---

**AUTH-006 DESIGN — IMPLEMENTATION-READY SUBJECT TO THE LIMITED INPUTS IN SECTION 18**

The authentication architecture and major authorization/security policies are frozen. Section 18 contains only implementation, business-rule, or deployment values that were not defined by AUTH-003/004/005. It does not reopen the frozen architecture.
