# AUTH-003 — Authentication & Authorization Architecture

**Project:** Samanvay-AI
**Branch:** `auth-development-shourya`
**Status:** Frozen target architecture; implementation and detailed policy mechanics remain to be specified
**Scope:** Authentication, authorization, tenant/resource policy, and their security boundaries

This document records the authoritative AUTH-003 target architecture. It is not a statement that the target controls are already implemented. Current repository behavior is summarized separately in Section 21. AUTH-004 defines threat requirements; AUTH-005 defines the target database/session data model. Neither this document nor later implementation work may silently change the frozen decisions recorded here.

---

## 1. Security Layers

The target architecture has four distinct security layers:

```text
Identity → Authentication → Authorization → Resource/Tenant Policy
```

* **Identity:** the local account and its server-held attributes.
* **Authentication:** establishes which user is making the request.
* **Authorization:** decides whether that authenticated identity may perform an operation.
* **Resource/Tenant Policy:** decides whether the identity may perform that operation on the particular CPSE, depot, or resource.

Authentication does not imply authorization. Authorization does not by itself establish that the requested resource belongs to the caller's permitted tenant or operational scope. These checks must not be collapsed into a single role comparison.

---

## 2. Browser Authentication

### FROZEN target

* Browser authentication uses a server-side, revocable session as defined by AUTH-005.
* The browser carries the session credential in a `Secure`, `HttpOnly`, `SameSite` cookie.
* No authentication token or session credential is stored in `localStorage` or exposed to frontend JavaScript.
* The server resolves identity from the session and the current database account; the cookie is not a role, CPSE, or permission token.

### Current repository behavior

The current browser stores a JWT in `localStorage` under `samanvay_auth_token`; the frontend API client sends `Authorization: Bearer ...`. There is no authentication cookie or server-side session model. See `frontend/src/context/AuthContext.tsx`, `frontend/src/lib/api.ts`, and `backend/app/core/security.py`.

---

## 3. Session Model

The session schema, types, hash representation, foreign keys, retention, and migration contract are defined by AUTH-005. AUTH-003 does not redefine them.

An authenticated session may be established only when:

1. The local user exists.
2. Credentials or an explicitly supported authentication method succeed.
3. `is_active = true`.
4. `is_approved = true`.
5. A new server-side session is created and committed successfully.

Session state is server-side and revocable. Logout, expiration, account disablement, and other policy invalidations make the session unusable. Existing JWTs are not migrated into session rows; AUTH-005 defines the finite cutover.

---

## 4. Account State

### FROZEN target

* Public self-registration is disabled. A public client cannot create a local account or submit authoritative role, CPSE, or depot assignments.
* Account provisioning is performed only through an authenticated, backend-authorized administrative provisioning operation.
* `SUPER_ADMIN` is the authorized administrative role for account provisioning and approval.
* Provisioning assigns the persisted role, CPSE, and depot through the authorized server-side operation. Client-supplied role/CPSE/depot values cannot independently establish authorization.
* A newly provisioned account starts with `is_active = true` and `is_approved = false`.
* No usable session/cookie is created for an unapproved account.
* Approval is a separate authenticated administrative operation authorized to `SUPER_ADMIN`.
* Approval changes `is_approved`; it does not silently change the account's role, CPSE, or depot.
* No public request can create `SUPER_ADMIN` or any other privileged role.
* An inactive user cannot log in or continue using an existing session.
* Account state must be evaluated consistently during authentication/session resolution. A credential that is invalid, expired, revoked, or associated with an inactive/unapproved account must not be silently downgraded into anonymous behavior on a protected route.
* The current repository has no protected account-creation/editing route; this is an implementation gap, not an unresolved target-policy decision.
* Database nullability/backfill and account-state persistence are defined by AUTH-005.

These are **TARGET** controls. Current behavior is documented in Section 21.

---

## 5. Roles

The declared application roles remain:

* `SITE_ENGINEER`
* `MATERIALS_MANAGER`
* `TECHNICAL_AUTHORITY`
* `CISF_SECURITY`
* `VIGILANCE_AUDITOR`
* `SUPER_ADMIN`

`AUDITOR` is not a separate target role. The existing `AUDITOR` versus `VIGILANCE_AUDITOR` inconsistency is a migration/data-cleanup issue, not a new role.

Roles are inputs to centralized authorization policy. A client-submitted role is never trusted.

### FROZEN role principle

No role inherits another role's business workflow permissions merely because of administrative status, seniority, or current repository behavior.

In particular:

* `SUPER_ADMIN` is a **system-administration role**, not a universal business-data role.
* `SUPER_ADMIN` does not automatically receive inventory, requisition, operational-document, dispatch, delivery, gate-pass, or cross-CPSE operational authority.
* `VIGILANCE_AUDITOR` receives audit-domain authority but not authority to modify underlying operational records.
* `TECHNICAL_AUTHORITY` and `CISF_SECURITY` have no general inventory-read grant; they receive inventory access only where explicitly required by an authorized workflow.
* No target role called `AUDITOR` is introduced.

---

## 6. Centralized Authorization

### FROZEN target

Authorization decisions use reusable centralized permissions/policies. They must not depend on scattered route-level code such as:

```python
if user.role == "...":
    ...
```

The target request path is:

```text
Router
    → Authentication dependency
    → Authorization dependency / centralized policy
    → Resource and tenant policy
    → Service
    → Repository / database
```

The policy interface accepts a server-derived principal, an operation/permission identifier from the finalized authorization policy, and resource context where applicable. It returns an allow/deny decision.

No implementation may fall back to route-specific role comparisons merely because a concrete permission key has not yet been selected.

### Central permission contract

The reusable policy interface is conceptually:

```text
authorize(authenticated_principal, operation_descriptor, resource_context)
    → AuthorizationDecision(allow | deny, reason_category)
```

`authenticated_principal` is created only from the validated server-side session and current User row.

`operation_descriptor` identifies the route/service action using an identifier registered in one central policy catalog.

`resource_context` contains server-loaded resource identity, CPSE/depot, owner/requester, current workflow state, and requested transition as applicable.

The policy decision composes:

* role-to-permission mapping,
* tenant scope,
* resource ownership,
* operational authority,
* workflow state,
* explicit cross-CPSE exceptions where applicable.

A route may request a decision but may not implement its own authorization policy.

Denials are enforced before the business operation and generate `AUTHORIZATION_FAILURE` through the AUTH-005 `SecurityEvent` store.

Authentication/account-state validation is a prerequisite, not a permission grant. The principal must be authenticated, active, approved, and backed by a valid session before protected authorization is evaluated.

A generic operation permission never automatically grants access to every resource or workflow transition.

### FROZEN role/capability policy

The following are owner-approved target capabilities. Capability labels describe policy domains and are not themselves concrete permission-key strings.

| Role                  | System/user administration | Inventory                                                                                                               | Audit domain                                                                                       | Requisition                                                                                                   | Oversight                            |
| --------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| `SITE_ENGINEER`       | None                       | Receive/confirm delivered material only                                                                                 | No audit-domain mutation grant                                                                     | Create; Deliver/Receive                                                                                       | No general oversight grant           |
| `MATERIALS_MANAGER`   | None                       | Create/add/update; status changes; stock verification/reconciliation; identify surplus/obsolete; dispatch to field/site | No audit-domain mutation grant                                                                     | Approve Standard/Low Value; Reject; Dispatch                                                                  | No general oversight grant           |
| `TECHNICAL_AUTHORITY` | None                       | No general inventory permission; workflow-specific access only where explicitly authorized                              | No audit-domain mutation grant                                                                     | Approve Technical/High Value; Reject                                                                          | No general oversight grant           |
| `CISF_SECURITY`       | None                       | No general inventory permission; workflow-specific access only where explicitly authorized                              | No audit-domain mutation grant                                                                     | Issue Gate Pass                                                                                               | No general oversight grant           |
| `VIGILANCE_AUDITOR`   | None                       | Read-only inventory/audit oversight                                                                                     | View audit records; create findings/observations; add feedback/comments; view/export audit history | Read-only access to relevant requisitions when required for an authorized audit; no state-changing transition | Read-only audit oversight            |
| `SUPER_ADMIN`         | System administration      | No implicit business inventory permission                                                                               | No implicit operational/audit-domain mutation authority                                            | No implicit workflow-transition permission                                                                    | No implicit business-data visibility |

### FROZEN SUPER_ADMIN rule

`SUPER_ADMIN` authority does not bypass:

* authentication,
* centralized authorization,
* CPSE/tenant policy,
* resource/ownership policy,
* workflow state validation,
* SecurityEvent/audit logging,
* step-up authentication where required,
* or other security controls.

Administrative privilege is not equivalent to universal business-data privilege.

### FROZEN audit separation rule

`VIGILANCE_AUDITOR` may create and read audit-domain findings, observations, feedback, and comments as defined above.

Those grants do **not** permit the auditor to modify:

* requisitions,
* inventory,
* dispatch/delivery,
* gate passes,
* material records,
* or other operational business records.

Audit-domain write access is not operational workflow authority.

### Current repository behavior

No centralized permission-policy provider was found. Current checks include `require_roles` for an inventory status route and direct role comparisons in authentication/requisition handlers. Those checks are current behavior only and do not define the target authorization architecture.

---

## 7. Backend Authorization Is Authoritative

* Every protected operation must be enforceable server-side.
* Frontend guards such as `ProtectedRoute`, hidden buttons, and role-dependent workspaces are UI behavior only.
* A direct API request must receive the same backend authentication, permission, tenant, and resource checks as a request initiated by the UI.
* The frontend may improve navigation and user feedback but cannot grant access.
* Missing authentication dependencies in current routes do not establish intentional public access.

---

## 8. CPSE Tenant Boundary

CPSE is a real tenant boundary.

### FROZEN target

For authenticated requests:

* Derive CPSE from the authenticated server-side user/session.
* `X-CPSE-ID` never establishes authentication, tenant membership, or authorization.
* Client-supplied CPSE/depot values cannot override the authenticated user's identity.
* Every user is restricted to their own CPSE for operational access.
* There is no automatic cross-CPSE operational access, including for `SUPER_ADMIN`.
* Cross-CPSE access exists only for the explicitly frozen exceptions below.

### FROZEN cross-CPSE exceptions

**Material matching**

Cross-CPSE canonical/material-equivalence information is permitted.

This does not authorize exposure of another CPSE's:

* stock,
* inventory quantities,
* depot information,
* requisitions,
* logistics/operational data,
* or other protected operational information.

**Graph**

Cross-CPSE canonical/material relationships are permitted.

Operational graph data remains CPSE-isolated, including:

* inventory/stock,
* depots,
* logistics routes,
* requisitions,
* and other operational relationships.

**Documents**

Normal users access documents within their own CPSE.

`VIGILANCE_AUDITOR` may access documents belonging to another CPSE only when required for a legitimate, explicitly authorized audit and only to the extent necessary for that audit.

**Audit**

Cross-CPSE audit access is permitted only on a case-by-case basis through explicit authorization for a specific audit.

When authorized, the auditor may access the complete evidentiary set necessary for that audit, including as necessary:

* audit findings,
* supporting documents,
* related requisitions,
* related inventory,
* and other relevant evidence.

This access is read-only and audit-purpose-only. It does not create operational authority.

The exact mechanism for creating, representing, checking, expiring, and auditing a case-specific audit authorization remains an implementation detail to be specified.

---

## 9. Resource Authorization

A resource ID is a selector, not an authorization credential. Knowing or guessing an ID is insufficient to read or mutate the resource.

For resource-addressed operations, the target sequence is:

1. Establish resource existence as appropriate, without disclosing it to an unauthorized caller.
2. Authenticate the caller.
3. Verify the required permission.
4. Verify the CPSE/tenant boundary.
5. Verify ownership or operational authority where applicable.
6. Validate workflow state where applicable.
7. Perform the operation.

Resource policy runs after identity is established and before protected service access or mutation.

The applicable ownership and operational-authority rules are part of the permission/resource policy, not implied by possession of the path parameter.

---

## 10. Client-Controlled Identity Fields

The following values, and similar actor/identity fields, must never establish identity or authorization when supplied by a client:

* `user_id`
* `role`
* CPSE
* depot
* `approved_by`
* requester
* `issuing_officer`
* workflow actor
* status

Authenticated identity comes from the server-side session.

Where an operation records an actor, use the authenticated principal.

Request-body, query, header, and path values may identify a target or provide non-authoritative input only; they do not replace the principal or policy checks.

---

## 11. Requisition Workflow

The requisition workflow is an explicit state machine:

```text
CREATE
    → PENDING
    → APPROVED / REJECTED
    → GATE PASS
    → DISPATCHED
    → DELIVERED
```

Each state transition has its own authorization.

The server validates:

* current state,
* requested transition,
* authenticated actor,
* applicable permission,
* CPSE/resource policy,
* and operational authority

before changing state.

A client cannot establish or bypass workflow authority by supplying a status, approver, requester, user ID, or requisition ID.

### FROZEN requisition authorization policy

| Operation/transition         | Target role                                  | Required boundary                                                                 |
| ---------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------- |
| Create → PENDING             | `SITE_ENGINEER`                              | Authenticated requester and authorized CPSE/resource context                      |
| Approve Standard/Low Value   | `MATERIALS_MANAGER`                          | Supplying-CPSE/resource policy and deterministic classification                   |
| Approve Technical/High Value | `TECHNICAL_AUTHORITY`                        | Supplying-CPSE/resource policy and deterministic classification                   |
| Reject                       | `MATERIALS_MANAGER` or `TECHNICAL_AUTHORITY` | Current state, requester/source/tenant policy                                     |
| Issue Gate Pass              | `CISF_SECURITY`                              | Approved/current requisition and supplying-CPSE authority                         |
| Dispatch                     | `MATERIALS_MANAGER`                          | Source/depot operational authority and valid current state                        |
| Deliver/Receive              | `SITE_ENGINEER`                              | Receiving CPSE/depot operational authority and valid current state                |
| Audit/Oversight              | `VIGILANCE_AUDITOR`                          | Read-only, relevant records only, and explicit audit authorization where required |
| System administration        | `SUPER_ADMIN`                                | Administrative operations only; no workflow inheritance                           |

### FROZEN approval-class rule

The system must use a predefined deterministic business rule to classify a requisition as:

* Standard/Low Value, or
* Technical/High Value.

The requester cannot select or manipulate the approval class merely to influence which role approves the requisition.

The exact thresholds/classification rules are a separate business-rule specification and remain to be supplied before implementation.

### FROZEN requisition visibility

**`SITE_ENGINEER`**

* Own requisitions only.

**`MATERIALS_MANAGER`**

* All requisitions within their own CPSE for read visibility.
* State-changing actions only where explicitly authorized by the workflow policy.

**`TECHNICAL_AUTHORITY`**

* Relevant Technical/High Value requisitions.
* Read-only visibility after handling.
* No modification authority after approval/rejection unless a separately frozen capability is defined.

**`CISF_SECURITY`**

* Requisitions for which gate-pass action is currently required.
* Access ends after the gate-pass action is completed.

**`VIGILANCE_AUDITOR`**

* Requisition access only when required for an explicitly authorized audit.
* Read-only.
* Cross-CPSE access only under the case-specific audit authorization defined in Section 8.

**`SUPER_ADMIN`**

* No automatic requisition visibility.
* No automatic workflow access.
* No cross-CPSE operational requisition access.

These visibility rules are part of the target authorization policy.

---

## 12. API Exposure

The default API posture is private/authenticated.

### FROZEN public surface

The only normal public production authentication/API entrypoints are:

* Login.
* Health/status.

Development-only documentation/OpenAPI may be exposed in development environments.

Google OAuth entry/callback will be intentionally reachable as part of the authentication flow when implemented, subject to its own validation and security requirements.

The following are **not public production business endpoints**:

* inventory operations,
* requisition operations,
* audit data,
* document operations,
* catalog/document ingestion,
* material matching,
* graph/business-data operations,
* benchmark,
* administrative operations,
* seed operations.

Public self-registration is disabled.

### Seed/admin provisioning

Seed operations are development/test-only or controlled deployment mechanisms.

Production endpoints must not expose a shared seed password or publicly provision privileged seed accounts.

Each API route must be classified by the authoritative authorization matrix. A route is not public merely because its current implementation lacks an authentication dependency.

---

## 13. Authentication and Security Events

Authentication/security telemetry is persisted in AUTH-005's `SecurityEvent` store, which is authoritative and independent of `SovereignAuditLedger`.

The target event set includes:

* `LOGIN_SUCCESS`
* `LOGIN_FAILURE`
* `GOOGLE_LOGIN`
* `SESSION_CREATED`
* `SESSION_REVOKED`
* `LOGOUT`
* `PASSWORD_CHANGED`
* `ACCOUNT_APPROVED`
* `ACCOUNT_REJECTED`
* `ACCOUNT_DISABLED`
* `ACCOUNT_LINKED`
* `AUTHORIZATION_FAILURE`
* `RATE_LIMIT_TRIGGERED`

Events contain no plaintext passwords, password hashes, raw session secrets, tokens, or client-controlled actor identity.

Anonymous events may have nullable user/session associations as defined by AUTH-005.

Events are not silently dual-written into the existing ledger.

---

## 14. Abuse Protection

Authentication-sensitive operations require abuse protection/rate limiting, including:

* Login.
* Account provisioning/administrative authentication operations as applicable.
* Recovery when implemented.
* Google callback when implemented.

Public signup is disabled and therefore is not a production target endpoint.

The repository does not establish a specific external rate-limit product.

AUTH-006 must define an application interface and integration point. Selecting a production shared store and numerical thresholds is a deployment/security-policy decision.

---

## 15. Step-Up Authentication

Designated sensitive operations may require step-up authentication, including:

* Password/security-setting changes.
* Recovery.
* Suspicious or new-device activity.
* High-risk administrative actions.

Step-up is a TARGET requirement for operations designated by policy.

Its mechanism and exact designated-operation list are later scoped implementation/security-policy work; AUTH-003 does not require step-up for every request.

---

## 16. Google OIDC

Google sign-in is a target architecture requirement using an OIDC authorization-code flow.

Persistent `OAuthIdentity` storage is explicitly deferred beyond AUTH-006 by AUTH-005.

When Google OIDC is implemented, validate:

* State.
* Callback/redirect URI.
* Issuer.
* Audience.
* Signature.
* Expiry.

Validated Google identity must resolve to or be explicitly linked to a local Samanvay account.

Google authentication never assigns a privileged Samanvay role automatically.

Provider validation, account-linking policy, and persistence implementation are later scoped work; no Google OAuth/OIDC flow currently exists in the repository.

---

## 17. Session Management

The target architecture supports:

* Server-side session revocation.
* Absolute expiration.
* Optional idle expiration.
* Eventual session-management/revocation UI.

Exact session schema, hash storage, FK behavior, timestamp semantics, index requirements, retention, and migration constraints are governed by AUTH-005.

AUTH-003 does not add another session schema.

---

## 18. Security Boundaries

Keep these questions separate:

| Layer                  | Question                                                      | Target authority                                                      |
| ---------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------- |
| Authentication         | “Who is this user?”                                           | Validated server-side session and current User record                 |
| Authorization          | “May this user perform this operation?”                       | Centralized permission/policy decision                                |
| Resource/Tenant Policy | “May this user perform this operation on this CPSE/resource?” | CPSE, ownership, operational-authority, and explicit exception checks |

Do not collapse these layers into one role check.

### Authentication and authorization outcomes

* Missing, malformed, expired, or revoked session: unauthenticated.
* A presented invalid credential must not be silently downgraded to anonymous behavior on protected/optional-auth routes where identity changes behavior.
* Inactive or unapproved account: no usable authenticated principal/session.
* Account-state failures must not unnecessarily disclose account state through credential-validation responses.
* Valid authenticated principal without the required permission: authenticated but unauthorized; deny before the business operation.
* Resource existence must not be disclosed solely because a caller supplied a valid ID.
* Protected resource not-found/denied responses must follow a non-enumerating policy; exact HTTP mapping is an implementation contract.

---

## 19. Target Architecture Diagram

```text
Browser
    ↓
Secure + HttpOnly + SameSite Cookie
    ↓
FastAPI
    ↓
Server-side AuthSession lookup / revocation / expiry
    ↓
Current User + active/approved account state
    ↓
Central Permission Policy
    ↓
CPSE / Tenant Policy
    ↓
Resource / Ownership / Operational-authority Policy
    ↓
Explicit Exception Policy where applicable
    ↓
Business Logic / Service
    ↓
PostgreSQL
```

This is the TARGET architecture. It is not the current runtime data flow.

---

## 20. FROZEN Decision Table

| Decision                                                       | FROZEN target                                                                                                            |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Browser authentication                                         | `Secure` + `HttpOnly` + appropriate `SameSite` cookie                                                                    |
| Authentication state                                           | Revocable server-side session defined by AUTH-005                                                                        |
| localStorage token                                             | Prohibited                                                                                                               |
| Unapproved account                                             | No usable authenticated session                                                                                          |
| Disabled account                                               | Cannot authenticate or use an existing session                                                                           |
| Backend authorization                                          | Mandatory and authoritative                                                                                              |
| Role authorization                                             | Centralized permission/policy layer                                                                                      |
| Public self-registration                                       | Disabled                                                                                                                 |
| Account provisioning                                           | Authenticated `SUPER_ADMIN`-authorized provisioning; server assigns role/CPSE/depot; new account starts unapproved       |
| Account approval                                               | Separate authenticated `SUPER_ADMIN`-authorized action                                                                   |
| Privileged role assignment                                     | Never client-selected                                                                                                    |
| Requisition creation                                           | `SITE_ENGINEER`                                                                                                          |
| Standard/Low Value approval                                    | `MATERIALS_MANAGER`                                                                                                      |
| Technical/High Value approval                                  | `TECHNICAL_AUTHORITY`                                                                                                    |
| Requisition rejection                                          | `MATERIALS_MANAGER` or `TECHNICAL_AUTHORITY`                                                                             |
| Gate Pass issuance                                             | `CISF_SECURITY`                                                                                                          |
| Requisition dispatch                                           | `MATERIALS_MANAGER`                                                                                                      |
| Requisition delivery/receipt                                   | `SITE_ENGINEER`                                                                                                          |
| Requisition audit/oversight                                    | `VIGILANCE_AUDITOR`, read-only and audit-scoped                                                                          |
| Site Engineer requisition visibility                           | Own requisitions                                                                                                         |
| Materials Manager requisition visibility                       | Own-CPSE requisitions                                                                                                    |
| Technical Authority requisition visibility                     | Relevant Technical/High Value requisitions                                                                               |
| CISF requisition visibility                                    | Requisitions requiring gate-pass action                                                                                  |
| Vigilance Auditor requisition visibility                       | Only when required for an explicitly authorized audit                                                                    |
| Super Admin requisition visibility                             | No automatic business-data visibility                                                                                    |
| Audit-domain operations                                        | `VIGILANCE_AUDITOR` may view records, create findings/observations, add feedback/comments, and view/export audit history |
| Audit/operational separation                                   | Audit permissions do not modify operational business records                                                             |
| Audit finding verification/closure                             | Separate management authority; not `VIGILANCE_AUDITOR` and not automatically `SUPER_ADMIN`                               |
| Audit management response                                      | `MATERIALS_MANAGER` for operational/material findings; `TECHNICAL_AUTHORITY` for technical findings                      |
| Cross-CPSE audit access                                        | Case-by-case explicit authorization for a specific audit; read-only and audit-purpose-only                               |
| Cross-CPSE material matching                                   | `MATCH_READ` gate enforced on `MATERIALS_MANAGER` before serving any cross-CPSE result; canonical/material-equivalence permitted; operational data never crosses CPSE boundaries |
| Cross-CPSE operational matching data                           | Not permitted merely because matching is cross-CPSE                                                                      |
| Cross-CPSE graph                                               | Canonical/material relationships permitted                                                                               |
| Cross-CPSE operational graph                                   | Not permitted                                                                                                            |
| Cross-CPSE documents                                           | Only for `VIGILANCE_AUDITOR` when required for an explicitly authorized audit                                            |
| Operational cross-CPSE access                                  | No automatic access                                                                                                      |
| Inventory create/add/update/status/verification/reconciliation | `MATERIALS_MANAGER`                                                                                                      |
| Inventory surplus/obsolete identification                      | `MATERIALS_MANAGER`                                                                                                      |
| Inventory dispatch to field/site                               | `MATERIALS_MANAGER`                                                                                                      |
| Inventory site receipt/confirmation                            | `SITE_ENGINEER`                                                                                                          |
| Inventory/audit oversight                                      | `VIGILANCE_AUDITOR`, read-only                                                                                           |
| Technical Authority general inventory                          | No                                                                                                                       |
| CISF Security general inventory                                | No                                                                                                                       |
| Super Admin inventory business access                          | No implicit grant                                                                                                        |
| Inventory disposal/write-off                                   | Outside Samanvay-AI; system may identify/flag/track only                                                                 |
| Document ingestion                                             | `MATERIALS_MANAGER` or `SUPER_ADMIN`, subject to CPSE/resource validation and audit                                      |
| Catalog ingestion                                              | `MATERIALS_MANAGER` or `SUPER_ADMIN`, subject to CPSE/resource validation and audit                                      |
| General inventory visibility                                   | Authenticated users only within their own CPSE and according to role/resource policy                                     |
| CPSE                                                           | Derived server-side from authenticated identity                                                                          |
| `X-CPSE-ID`                                                    | Never an authorization mechanism                                                                                         |
| Resource IDs                                                   | Require permission, tenant, ownership/operational checks                                                                 |
| Requisition transitions                                        | Explicit state-machine transitions with per-transition authorization                                                     |
| Client identity fields                                         | Untrusted                                                                                                                |
| Seed/admin provisioning                                        | Development-only or explicitly controlled; not public production auth                                                    |
| Seed password exposure                                         | Prohibited                                                                                                               |
| Public business endpoints                                      | None beyond explicitly allowlisted authentication/health functionality                                                   |
| Benchmark                                                      | Development/test-only; not normal production capability                                                                  |
| Google OIDC                                                    | Target architecture; `OAuthIdentity` persistence deferred beyond AUTH-006                                                |
| Session revocation                                             | Server-side                                                                                                              |
| Rate limiting                                                  | Required for auth-sensitive operations                                                                                   |
| Step-up authentication                                         | Required for operations designated as sensitive by policy                                                                |
| SUPER_ADMIN privilege                                          | System administration only; no security-control bypass                                                                   |

---

## 21. Repository Grounding: Current Behavior vs TARGET

The following describes inspected code, not the frozen target.

| Area                     | CURRENT repository behavior                                                                                                 | FROZEN TARGET                                                                                               |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Browser credential       | Frontend stores `samanvay_auth_token` in localStorage and adds a bearer Authorization header                                | Server-side session cookie; no browser-readable auth token                                                  |
| Session persistence      | No `AuthSession` model or server-side auth session table                                                                    | AUTH-005 server-side, revocable session                                                                     |
| Login                    | `POST /auth/login` checks bcrypt, `is_active`, `is_approved`, then returns signed JWT                                       | Establish session only for active and approved accounts                                                     |
| Signup                   | `POST /auth/signup` is public, accepts role/CPSE/depot, can accept `SUPER_ADMIN`, and returns JWT for an unapproved account | Public self-registration disabled; authenticated administrative provisioning only                           |
| Provisioning/approval    | User list/approve/reject are protected by direct `SUPER_ADMIN` checks; no protected account-create route exists             | `SUPER_ADMIN`-authorized provisioning plus separate approval                                                |
| Required user dependency | `get_current_user` validates bearer JWT and checks active state, but does not check approval on each request                | Session + current User lookup + active/approved policy                                                      |
| Optional identity        | `get_optional_user` can return `None` for missing/invalid JWT and allow route logic to continue                             | Optional authentication only where intentionally allowed; presented invalid credential must not downgrade   |
| Authorization            | `require_roles` and direct role comparisons; no centralized permission provider                                             | Reusable centralized permission policy                                                                      |
| CPSE                     | `verify_cpse_access` can use user CPSE, `X-CPSE-ID`, or fallback `OIL`; not a general tenant boundary                       | Server-derived CPSE; header cannot establish/override tenant authority                                      |
| Frontend route controls  | `ProtectedRoute` and UI role checks exist                                                                                   | UI-only; backend authoritative                                                                              |
| Security events          | No `SecurityEvent` model found; `SovereignAuditLedger` exists for business/statutory audit                                  | AUTH-005 `SecurityEvent` authoritative for auth telemetry                                                   |
| CSRF/rate limiting       | No auth cookie, CSRF implementation, or rate-limit middleware/service found                                                 | Cookie-authenticated unsafe requests require CSRF defense; auth-sensitive operations require abuse controls |
| Google OIDC              | No Google OAuth/OIDC route/provider validation found                                                                        | Target OIDC architecture                                                                                    |
| Seed behavior            | Startup seeding can create/reactivate/reapprove seed accounts; public seed route exposes seed information/credential        | Development/test-only or controlled deployment mechanism; no public production seed credential              |
| Public API posture       | Several business routes lack auth dependencies                                                                              | Default private/authenticated API                                                                           |
| Inventory visibility     | Several inventory reads are optional-auth/public and are not a general tenant boundary                                      | Authenticated own-CPSE visibility according to role/resource policy                                         |
| Inventory mutations      | Several mutations are currently unauthenticated or weakly authorized                                                        | Explicit role + tenant/resource authorization                                                               |
| Requisition mutations    | Several workflow mutations are optional-auth or public                                                                      | Authenticated explicit per-transition authorization                                                         |
| Audit operations         | Audit routes are currently public/weakly protected                                                                          | VIGILANCE_AUDITOR audit-domain policy                                                                       |
| Document ingestion       | Current routes are public and implementation behavior creates/associates records                                            | MATERIALS_MANAGER/SUPER_ADMIN with authenticated CPSE/resource policy                                       |
| Material matching        | Session-authenticated full match search; fail-closed MATCH_READ gate (MATERIALS_MANAGER); session CPSE authoritative, not X-CPSE-ID | Cross-CPSE canonical/material-equivalence permitted; operational data capped at caller CPSE                  |
| Graph operations         | Current graph routes are largely public and can use client-provided CPSE headers                                            | Canonical/material relationships may cross CPSE; operational graph remains CPSE-isolated                    |
| Benchmark                | No production endpoint (route removed); dev/test-helper only, never public                                                  | Development/test-only, explicitly not part of the public surface                                           |
| Account roles            | Existing data/code may contain `AUDITOR` references                                                                         | Target roles contain `VIGILANCE_AUDITOR`, not a new `AUDITOR` role                                          |

Relevant implementation anchors include:

* `backend/app/api/routers/auth.py`
* `backend/app/api/dependencies.py`
* `backend/app/core/security.py`
* `backend/app/models/tables.py`
* `backend/main.py`
* `backend/app/services/seeder.py`
* `frontend/src/context/AuthContext.tsx`
* `frontend/src/lib/api.ts`
* `frontend/src/components/ProtectedRoute.tsx`

---

## 22. Route/Operation Authorization Matrix

The matrix records current backend dependencies and role checks separately from target policy.

“Authenticated” means a valid, active, approved server-side session.

Unless marked otherwise, target API posture is private by default. A missing authentication dependency in the current implementation is not evidence of intentional public access.

`FROZEN` means the target policy is owner-approved.

`IMPLEMENTATION GAP` means a frozen target capability does not currently exist or is not currently enforced.

`SPECIFICATION DETAIL` means the architectural policy is frozen, but the exact implementation mechanism remains to be defined.

| Operation / current endpoint                           | Current auth                                            | Current role evidence                       | Target auth            | Target capability                                                                                   | Tenant/resource rule                                                                  | Status               |
| ------------------------------------------------------ | ------------------------------------------------------- | ------------------------------------------- | ---------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | -------------------- |
| Login — `POST /api/v1/auth/login`                      | No                                                      | N/A                                         | Public                 | Credential authentication only                                                                      | Tenant comes from verified User                                                       | FROZEN               |
| Logout — `POST /api/v1/auth/logout`                    | Not present                                             | N/A                                         | Authenticated session  | Revoke caller's session                                                                             | Session selected from cookie                                                          | IMPLEMENTATION GAP   |
| Session/CSRF bootstrap                                 | Not present                                             | N/A                                         | Authenticated session  | Session/CSRF support only                                                                           | Current session                                                                       | IMPLEMENTATION GAP   |
| Public signup — `POST /api/v1/auth/signup`             | No                                                      | Body can select role/CPSE/depot             | Not a target operation | No public self-registration                                                                         | N/A                                                                                   | FROZEN               |
| Account provisioning                                   | Public signup/startup seed currently create accounts    | No protected create-user check              | Authenticated          | `SUPER_ADMIN`-authorized provisioning                                                               | Server assigns/validates CPSE/depot                                                   | IMPLEMENTATION GAP   |
| User listing — `GET /api/v1/auth/users`                | Yes                                                     | Direct `SUPER_ADMIN` check                  | Authenticated          | System administration                                                                               | Administrative policy                                                                 | FROZEN               |
| User approval                                          | Yes                                                     | Direct `SUPER_ADMIN` check                  | Authenticated          | System administration                                                                               | Target user selected by ID; approval only                                             | FROZEN               |
| User rejection                                         | Yes                                                     | Direct `SUPER_ADMIN` check                  | Authenticated          | System administration                                                                               | Target user selected by ID; state validated                                           | FROZEN               |
| User role/CPSE/depot edit/disable                      | No route found                                          | N/A                                         | Authenticated          | Administrative capability to be specified within the frozen provisioning model                      | Server-side validation required                                                       | IMPLEMENTATION GAP   |
| Audit listing                                          | No                                                      | No role check                               | Authenticated          | `VIGILANCE_AUDITOR`                                                                                 | Relevant audit scope; explicit cross-CPSE authorization where applicable              | FROZEN               |
| Audit detail                                           | No                                                      | No role check                               | Authenticated          | `VIGILANCE_AUDITOR`                                                                                 | Resource authorization; no IDOR                                                       | FROZEN               |
| Audit-chain verification                               | No                                                      | No role check                               | Authenticated          | Audit oversight                                                                                     | Separate from finding closure authority                                               | FROZEN               |
| Audit export/history                                   | No                                                      | No role check                               | Authenticated          | `VIGILANCE_AUDITOR`                                                                                 | Only authorized audit records; cross-CPSE only under explicit audit authorization     | FROZEN               |
| Create audit finding/observation; add feedback/comment | Yes                                                     | Any authenticated user currently passes     | Authenticated          | `VIGILANCE_AUDITOR`                                                                                 | Audit-domain records only                                                             | FROZEN               |
| Verify/close audit finding                             | No dedicated route                                      | N/A                                         | Authenticated          | Separate management authority                                                                       | Exact existing-role mapping and implementation route remain to be specified           | SPECIFICATION DETAIL |
| Management response/settlement                         | No dedicated route                                      | N/A                                         | Authenticated          | `MATERIALS_MANAGER` for operational/material findings; `TECHNICAL_AUTHORITY` for technical findings | Finding-specific; does not itself authorize operational-record mutation               | FROZEN               |
| Inventory listing                                      | Optional JWT                                            | No role check                               | Authenticated          | Own-CPSE inventory according to role/resource policy                                                | Own CPSE; no cross-CPSE operational access                                            | FROZEN               |
| Inventory statistics                                   | Optional JWT                                            | No role check                               | Authenticated          | Own-CPSE inventory visibility according to role/resource policy                                     | Aggregates must be CPSE-scoped                                                        | FROZEN               |
| Inventory item access                                  | Optional JWT                                            | No role check                               | Authenticated          | Role/resource-scoped own-CPSE access                                                                | SKU selector only; tenant/resource check required                                     | FROZEN               |
| Inventory creation/addition                            | No                                                      | No role check                               | Authenticated          | `MATERIALS_MANAGER`                                                                                 | Authorized own-CPSE/depot context                                                     | FROZEN               |
| Inventory record update                                | No route found                                          | N/A                                         | Authenticated          | `MATERIALS_MANAGER`                                                                                 | Own-CPSE/resource/operational authority                                               | IMPLEMENTATION GAP   |
| Inventory status update                                | Yes                                                     | `MATERIALS_MANAGER` or `SUPER_ADMIN`        | Authenticated          | `MATERIALS_MANAGER` business capability                                                             | Own-CPSE/resource policy; `SUPER_ADMIN` does not inherit                              | FROZEN               |
| Stock verification/reconciliation                      | No specific route                                       | N/A                                         | Authenticated          | `MATERIALS_MANAGER`                                                                                 | Own-CPSE inventory scope                                                              | IMPLEMENTATION GAP   |
| Identify surplus/obsolete                              | Optional/no auth                                        | No role check                               | Authenticated          | `MATERIALS_MANAGER`                                                                                 | Own-CPSE inventory scope                                                              | FROZEN               |
| Track surplus/obsolete                                 | No dedicated target workflow                            | N/A                                         | Authenticated          | `MATERIALS_MANAGER` within inventory policy                                                         | Own CPSE                                                                              | IMPLEMENTATION GAP   |
| Dispose/write off surplus/obsolete                     | No target route                                         | N/A                                         | Outside Samanvay-AI    | No disposal authorization capability                                                                | External process                                                                      | FROZEN               |
| Inventory dispatch to field/site                       | Current dispatch route is requisition-based             | No current role check                       | Authenticated          | `MATERIALS_MANAGER`                                                                                 | Source/depot operational authority                                                    | FROZEN               |
| Site receipt/confirmation                              | Current delivery route has no role check                | No role check                               | Authenticated          | `SITE_ENGINEER`                                                                                     | Receiving CPSE/depot authority                                                        | FROZEN               |
| Document ingestion — `POST /api/v1/ingest/document`    | No                                                      | No role check                               | Authenticated          | `MATERIALS_MANAGER` or `SUPER_ADMIN`                                                                | Server-authorized CPSE/depot                                                          | FROZEN               |
| Catalog ingestion — `POST /api/v1/ingest/catalog`      | No                                                      | No role check                               | Authenticated          | `MATERIALS_MANAGER` or `SUPER_ADMIN`                                                                | Uploaded CPSE/depot cannot establish authority                                        | FROZEN               |
| Document listing                                       | No                                                      | No role check                               | Authenticated          | Own-CPSE document access; auditor exception                                                         | Cross-CPSE only under explicit audit authorization                                    | FROZEN               |
| Document detail                                        | No                                                      | No role check                               | Authenticated          | Own-CPSE document access; auditor exception                                                         | ID lookup requires resource authorization                                             | FROZEN               |
| Material search                                        | Optional JWT                                            | No role check                               | Authenticated          | Matching capability                                                                                 | Cross-CPSE canonical/material-equivalence allowed; operational fields remain scoped   | FROZEN               |
| Benchmark                                              | No                                                      | No role check                               | Development/test       | No production capability                                                                            | Development/test dataset only                                                         | FROZEN               |
| Graph discovery                                        | No                                                      | No role check                               | Authenticated          | Canonical/material graph access                                                                     | Cross-CPSE canonical/material relationships allowed; operational data scoped          | FROZEN               |
| Graph item properties                                  | No                                                      | No role check                               | Authenticated          | Resource-scoped graph access                                                                        | Operational properties require own-CPSE authority                                     | FROZEN               |
| Depot surplus graph                                    | No                                                      | No role check                               | Authenticated          | Operational graph access                                                                            | Depot must belong to caller's CPSE                                                    | FROZEN               |
| Logistics calculation                                  | No                                                      | No role check                               | Authenticated          | Operational graph capability                                                                        | Source/target depots must satisfy CPSE policy; no cross-CPSE operational route access | FROZEN               |
| Network topology                                       | No                                                      | No role check                               | Authenticated          | Graph/topology access                                                                               | Operational topology is CPSE-scoped                                                   | FROZEN               |
| Requisition list                                       | Optional JWT                                            | Literal `AUDITOR`/other conditional filters | Authenticated          | Role-specific frozen visibility                                                                     | Server-side per-record authorization                                                  | FROZEN               |
| Requisition view                                       | No                                                      | No role/ownership check                     | Authenticated          | Role-specific frozen visibility                                                                     | ID-only access prohibited                                                             | FROZEN               |
| Requisition create                                     | Optional JWT                                            | No role check                               | Authenticated          | `SITE_ENGINEER`                                                                                     | Authenticated CPSE/resource context                                                   | FROZEN               |
| Approve Standard/Low Value                             | Optional JWT                                            | No proper role check                        | Authenticated          | `MATERIALS_MANAGER`                                                                                 | Deterministic classification + supplying-CPSE/resource policy                         | FROZEN               |
| Approve Technical/High Value                           | Optional JWT                                            | No proper role check                        | Authenticated          | `TECHNICAL_AUTHORITY`                                                                               | Deterministic classification + supplying-CPSE/resource policy                         | FROZEN               |
| Requisition reject                                     | Optional JWT                                            | No role allowlist                           | Authenticated          | `MATERIALS_MANAGER` or `TECHNICAL_AUTHORITY`                                                        | State + resource/tenant policy                                                        | FROZEN               |
| Gate-pass issue                                        | Optional JWT                                            | No CISF role check                          | Authenticated          | `CISF_SECURITY`                                                                                     | Supplying-CPSE/requisition authority                                                  | FROZEN               |
| Dispatch                                               | No                                                      | No role check                               | Authenticated          | `MATERIALS_MANAGER`                                                                                 | Source/depot authority                                                                | FROZEN               |
| Deliver/Receive                                        | No                                                      | No role check                               | Authenticated          | `SITE_ENGINEER`                                                                                     | Receiving authority                                                                   | FROZEN               |
| Audit requisition oversight                            | Public/optional currently                               | Frontend only                               | Authenticated          | `VIGILANCE_AUDITOR`                                                                                 | Relevant records only; explicit audit authorization for cross-CPSE                    | FROZEN               |
| System administration                                  | User list/approve/reject protected; provisioning absent | Direct `SUPER_ADMIN` checks                 | Authenticated          | `SUPER_ADMIN`                                                                                       | Administrative resource policy; no workflow bypass                                    | FROZEN               |
| Seed-user listing/provision                            | Public                                                  | No role check                               | Development/test-only  | No production capability                                                                            | No public seed credential                                                             | FROZEN               |
| Seed operation                                         | Public                                                  | No role check                               | Development/test-only  | No production capability                                                                            | No public provisioning                                                                | FROZEN               |
| Health — `/health`                                     | No                                                      | N/A                                         | Public                 | Health/status only                                                                                  | No business data                                                                      | FROZEN               |
| API docs/OpenAPI                                       | Public defaults                                         | N/A                                         | Development-only       | No business permission                                                                              | Production exposure disabled or explicitly controlled                                 | FROZEN               |

---

## 23. Remaining Specification Work

The architectural authorization decisions in this document are frozen. The following items remain implementation/specification details and must not be reinterpreted as permission to redesign the architecture.

### 23.1 Permission vocabulary

Define the concrete permission identifiers and policy-provider implementation for the already-frozen role/capability matrix.

The implementation must preserve the role boundaries established here and must not introduce implicit inheritance.

### 23.2 Requisition classification rules

Define the deterministic business rules that classify requisitions into:

* Standard/Low Value
* Technical/High Value

The classification must be server-controlled and must not be selected by the requester merely to influence approval authority.

### 23.3 Audit finding closure authority mapping

The architectural rule is frozen:

* `VIGILANCE_AUDITOR` does not verify/close findings.
* `SUPER_ADMIN` does not automatically receive finding-closure authority.
* A separate management authority performs verification/closure.

If this must map to one of the six existing application roles, the exact mapping must be specified before implementation.

### 23.4 Case-specific cross-CPSE audit authorization

The architectural rule is frozen:

* cross-CPSE audit access is not automatic;
* it requires explicit authorization for a specific audit;
* authorized access is read-only and audit-purpose-only;
* the auditor may access the evidentiary set necessary for that audit.

The implementation must define how that authorization is represented, granted, checked, expired/revoked, and recorded in security telemetry.

### 23.5 Route/resource implementation

The exact route-to-permission mapping, repository queries, service-layer policy enforcement, and resource filtering must be implemented consistently with this document.

These are implementation details, not unresolved authorization decisions.

---

## 24. Completion Status

AUTH-003 target architecture and owner-approved authorization policy are **FROZEN**.

The following are explicitly frozen:

* server-side revocable sessions;
* secure browser authentication cookies;
* no localStorage authentication credentials;
* no public self-registration;
* `SUPER_ADMIN`-controlled account provisioning and approval;
* six-role target model;
* centralized authorization;
* backend-authoritative enforcement;
* CPSE tenant isolation;
* no automatic cross-CPSE operational access;
* explicit material-matching and canonical-graph cross-CPSE exceptions;
* controlled cross-CPSE document/audit access;
* frozen requisition workflow and visibility policy;
* frozen inventory operation and visibility policy;
* disposal/write-off outside Samanvay-AI;
* `MATERIALS_MANAGER`/`SUPER_ADMIN` ingestion authority;
* `VIGILANCE_AUDITOR` audit-domain authority;
* audit/operational separation;
* separate audit-finding closure authority;
* management-response role mapping;
* case-specific cross-CPSE audit authorization;
* development-only benchmark;
* private-by-default API;
* development-only/controlled seed operations;
* `SUPER_ADMIN` system-administration boundary;
* Google OIDC target;
* SecurityEvent telemetry;
* rate limiting;
* step-up authentication.

The remaining work is specification and implementation detail:

1. Concrete permission vocabulary/provider.
2. Deterministic Standard/Low versus Technical/High classification rules.
3. Exact existing-role mapping for the separate audit-finding closure authority, if required.
4. Mechanics of case-specific cross-CPSE audit authorization.
5. Detailed route/resource implementation of the frozen policies.

No remaining item authorizes an implementation agent to reopen or redesign the frozen security boundaries.

**AUTH-003 TARGET ARCHITECTURE — FROZEN**

**AUTHORIZATION POLICY — FROZEN**

**IMPLEMENTATION/SPECIFICATION DETAILS REMAINING — DOCUMENTED ABOVE**
