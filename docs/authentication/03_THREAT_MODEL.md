# AUTH-004 — Threat Model & Security Requirements

**Project:** Samanvay-AI
**Authentication Branch:** `auth-development-shourya`
**Status:** Design / Security Requirements
**Depends on:** AUTH-001, AUTH-002, AUTH-003
**Next:** AUTH-005 — Database & Session Design

---

## 1. Purpose

This document defines the security threats, trust boundaries, abuse cases, and mandatory security requirements for the Samanvay-AI authentication and authorization subsystem.

The requirements are derived from the repository reconnaissance and authorization audit.

**Control status:** Statements labeled **Current risk**, **Current behavior**, or **Current status** describe the repository as inspected. Security requirements, objectives, invariants, and acceptance criteria are **TARGET/FUTURE** controls unless explicitly labeled as current behavior; they do not imply that those controls exist today.

The authentication subsystem must protect:

* User identity
* Authentication credentials
* Sessions
* Account state
* Roles and permissions
* CPSE tenant boundaries
* Business resources
* Administrative operations
* Workflow transitions
* Security/audit events

Security decisions must be enforced by the backend. Frontend controls are not security boundaries.

---

# 2. Security Objectives

The authentication system must guarantee:

### O1 — Authentication Integrity

Only a valid, active, approved account can establish an authenticated session.

### O2 — Session Integrity

An authenticated browser session must be represented by a server-side session and a secure browser cookie.

### O3 — Authorization Integrity

A valid login must not automatically grant permission to perform arbitrary operations.

### O4 — Tenant Isolation

A user's CPSE must be derived from trusted server-side identity and must not be established by a client-controlled header or request field.

### O5 — Resource Authorization

Possessing a resource ID must never be sufficient to access or modify that resource.

### O6 — Administrative Protection

Administrative and account-management operations must require explicit administrative authorization.

### O7 — Workflow Integrity

Business workflow transitions must be authorized individually rather than being exposed as unrestricted mutations.

### O8 — Auditability

Security-sensitive authentication, authorization, administrative, and workflow actions must generate appropriate security events.

### O9 — Abuse Resistance

Authentication and account-management endpoints must resist brute-force, credential-stuffing, enumeration, and automated abuse.

### O10 — Revocability

Sessions must be revocable server-side, including when an account is disabled or a session is explicitly logged out.

---

# 3. Assets

The following are security-sensitive assets.

| Asset                     | Protection Requirement                                          |
| ------------------------- | --------------------------------------------------------------- |
| User credentials          | Never expose or log plaintext passwords                         |
| Password hashes           | Store using approved password hashing mechanism                 |
| Session identifiers       | Confidential, unpredictable, revocable                          |
| Authentication cookies    | Secure, HttpOnly, appropriate SameSite policy                   |
| User identity             | Must originate from authenticated server-side session           |
| User role                 | Must originate from trusted account data                        |
| User CPSE                 | Must originate from trusted account/session data                |
| Permissions               | Must be determined server-side                                  |
| CPSE-scoped resources     | Must not cross tenant boundaries without explicit authorization |
| Requisitions              | Must enforce ownership/operational authorization                |
| Inventory records         | Must enforce CPSE/resource authorization                        |
| Documents                 | Must enforce authorization before access                        |
| Audit records             | Must not be publicly mutable                                    |
| Administrative operations | Must require explicit privileged authorization                  |
| Security events           | Must preserve security-relevant history                         |
| OAuth identity            | Must be validated before account linking                        |
| Account approval state    | Must be enforced by authentication                              |
| Account active state      | Must be enforced for session use                                |

---

# 4. Trust Boundaries

## TB-01 — Browser → Backend

The browser is an untrusted client.

Never trust:

* role
* user ID
* CPSE ID
* depot ID
* approval status
* requester identity
* approver identity
* issuing officer
* workflow actor

provided by the browser.

These values may be supplied for display or request context, but authorization must be derived from trusted server-side identity and policy.

---

## TB-02 — Authentication → Authorization

Successful authentication proves identity.

It does NOT prove authorization for every operation.

The backend must perform:

`Authenticated Identity → Permission → Tenant Policy → Resource Policy`

before sensitive operations.

---

## TB-03 — User Identity → CPSE

The authenticated user's CPSE is trusted server-side.

`X-CPSE-ID` must never establish authorization.

A client-controlled CPSE header may be treated only as non-authoritative request context where explicitly required.

---

## TB-04 — Resource ID → Resource Access

A resource identifier is untrusted input.

Example:

`GET /requisitions/123`

must not imply:

`user may access requisition 123`

The backend must independently determine whether the authenticated user is authorized to access resource `123`.

---

## TB-05 — OAuth Provider → Application

Google identity is an external trust boundary.

The application must validate the OAuth/OIDC response before establishing a local Samanvay-AI session.

Google authentication must not automatically determine privileged Samanvay-AI authorization.

---

# 5. Threat Actors

## A1 — Unauthenticated Internet User

Capabilities:

* Send arbitrary HTTP requests
* Modify request bodies
* Modify headers
* Guess resource IDs
* Call public endpoints directly
* Attempt credential attacks

Primary threats:

* Unauthorized mutations
* Account enumeration
* Brute force
* IDOR
* Tenant bypass
* Seed/admin abuse

---

## A2 — Authenticated Low-Privilege User

Capabilities:

* Possess a valid session
* Access endpoints available to their permissions

Primary threats:

* Horizontal privilege escalation
* Cross-CPSE access
* IDOR
* Vertical privilege escalation
* Unauthorized workflow transitions

---

## A3 — Compromised Browser Session

Assumption:

An attacker obtains a user's valid session credential.

**TARGET/FUTURE controls** should limit damage through:

* Session expiry
* Server-side revocation
* Account disabling
* Session management
* Secure cookie attributes
* Step-up authentication for sensitive actions

---

## A4 — Malicious Privileged User

A privileged user may intentionally attempt unauthorized access beyond their legitimate operational authority.

**TARGET/FUTURE controls:**

* Explicit permission model
* CPSE policy
* Resource authorization
* Audit logging
* Sensitive-action controls

---

# 6. Primary Threat Model

## T01 — Unapproved Account Authentication

### Current risk

The existing signup flow creates an unapproved account but returns a JWT, while `/auth/me` checks active state without enforcing approval.

### Threat

A newly registered but unapproved account may obtain usable authenticated access.

### Requirement

`is_approved=false` must prevent creation of a usable authenticated session.

### Security requirement

**SEC-AUTH-001**

> An account that is not approved must not receive an authenticated session.

This is a **TARGET/FUTURE** control. The current signup route issues a JWT before approval; current-user resolution checks active state but does not check approval. See T22 for the privilege-escalation consequence when signup also accepts a privileged role.

---

# 7. T02 — Disabled Account Access

### Current behavior

Login rejects inactive accounts. Required-auth routes using `get_current_user` reload the account and reject it when `is_active=false` on each request. Routes using `get_optional_user` do not check `is_active` or `is_approved`; they can still resolve an inactive account from a valid token. The **TARGET/FUTURE** architecture must define consistent account-state enforcement across required-auth and optional-auth routes.

### Threat

A user account may be disabled after a session has already been created.

### TARGET/FUTURE requirement

Disabled accounts must not authenticate and existing sessions must not remain usable indefinitely.

**SEC-AUTH-002**

> Authentication must reject inactive accounts.

**SEC-AUTH-003**

> Session validation must enforce account active state.

---

# 8. T03 — Token Theft / Client-Side Credential Exposure

### Current risk

Authentication currently uses JWTs stored in browser `localStorage`.

### Threat

Client-side credential exposure can allow an attacker to obtain a reusable bearer credential.

### TARGET/FUTURE requirement

Move browser authentication to:

* Server-side sessions
* Secure cookie
* HttpOnly cookie
* Appropriate SameSite configuration
* Server-side revocation

**SEC-SESSION-001**

> Browser authentication credentials must not be stored in application localStorage.

**SEC-SESSION-002**

> Authentication sessions must be represented by server-side session records.

**SEC-SESSION-003**

> Browser session identifiers must be transmitted using a Secure, HttpOnly cookie.

---

# 9. T04 — Session Hijacking / Session Fixation

### Threat

An attacker attempts to reuse or predict a session identifier, or causes a victim to authenticate into an attacker-controlled session.

### Requirements

**SEC-SESSION-004**

> Session identifiers must be cryptographically unpredictable.

**SEC-SESSION-005**

> A new authenticated session must use a newly generated session identity.

**SEC-SESSION-006**

> Session identifiers must not be exposed in application logs.

---

# 10. T05 — Session Persistence After Logout

### Current risk

Current logout only removes browser state.

### Threat

A previously issued credential remains valid.

### Requirement

Logout must revoke the server-side session.

**SEC-SESSION-007**

> Logout must revoke the current server-side session.

---

# 11. T06 — Session Persistence After Account Disablement

### Threat

An administrator disables an account while an authenticated credential still exists. In the current code, required-auth routes reject that credential after the account is disabled; optional-auth routes do not enforce the active flag (see T02). The **TARGET/FUTURE** control must apply consistently to all authenticated session use.

### Requirement

Session validation must consider account state.

**SEC-SESSION-008**

> A disabled account must not be able to continue using an existing authenticated session.

---

# 12. T07 — Broken Role Authorization

### Current risk

Role checks are decentralized and inconsistent.

The declared role is `VIGILANCE_AUDITOR`, but the requisition list handler compares against the literal `AUDITOR`. This is a role-name/authorization inconsistency; the canonical role vocabulary and its checks must be consistent in the **TARGET/FUTURE** policy.

### Threat

A route may accidentally implement incomplete or incorrect role checks.

### Requirement

Use centralized permission-based authorization.

**SEC-AUTHZ-001**

> Authorization decisions must be based on centralized permissions/policies rather than scattered route-specific role checks.

---

# 13. T08 — Vertical Privilege Escalation

### Example

A SITE_ENGINEER attempts an administrative endpoint.

### Requirement

The backend must independently verify the permission required by every privileged operation.

**SEC-AUTHZ-002**

> Authentication alone must never grant administrative authorization.

**SEC-AUTHZ-003**

> Administrative operations must require explicit administrative permission.

---

# 14. T09 — Horizontal Privilege Escalation / IDOR

### Example

User A requests:

`/requisitions/<User-B-resource-id>`

### Threat

The application returns or modifies another user's resource solely because the identifier is valid.

### Requirement

Every ID-addressed resource must undergo authorization checks.

**SEC-RESOURCE-001**

> Resource identifiers must never be treated as authorization credentials.

**SEC-RESOURCE-002**

> Resource access must verify the authenticated user's permission and applicable ownership, operational authority, and CPSE policy.

---

# 15. T10 — CPSE Tenant Bypass

### Current risk

The existing implementation can resolve CPSE using `X-CPSE-ID` for anonymous callers and uses CPSE resolution inconsistently.

### Threat

A client changes:

`X-CPSE-ID: IOCL`

to:

`X-CPSE-ID: ONGC`

and attempts to access or mutate another tenant's resources.

### Requirement

Authenticated identity must determine tenant context.

**SEC-TENANT-001**

> The authenticated user's CPSE must be derived from trusted account/session data.

**SEC-TENANT-002**

> `X-CPSE-ID` must never establish authorization.

**SEC-TENANT-003**

> Cross-CPSE access must require an explicit privileged capability and explicit policy.

---

# 16. T11 — Client-Controlled Identity

The following request values must never establish authorization:

* `user_id`
* `role`
* `cpse_id`
* `depot_id`
* `requester`
* `approved_by`
* `issuing_officer`

**SEC-IDENTITY-001**

> Actor identity must always be derived from the authenticated server-side session.

---

# 17. T12 — Unauthorized Business Mutations

### Current audit finding

Several consequential operations were identified as callable without authentication, including operational mutations.

### Threat

An unauthenticated attacker can directly manipulate business state.

### Requirement

Business mutations must default to authenticated access.

**SEC-API-001**

> Business mutations must not be publicly accessible unless explicitly classified as public.

**SEC-API-002**

> Every mutation must define its required authentication and authorization policy.

---

# 18. T13 — Requisition Workflow Bypass

Target workflow:

`CREATE → PENDING → APPROVED / REJECTED → GATE PASS → DISPATCHED → DELIVERED`

### Threat

A caller directly invokes a later-stage endpoint without completing the required previous transition, or changes the state of an unrelated requisition by supplying its ID. In the current code, approval/rejection services do not validate the requisition's current state; dispatch/delivery set their status without a state check or required authentication; gate-pass generation checks for `APPROVED` but its route uses optional authentication.

### Requirement

Every transition must validate:

1. The current state of the requisition.
2. That the requested state transition is valid from that current state.
3. The authenticated actor's identity and permission for that transition.
4. Applicable CPSE, resource-ownership, and operational-authority policy.
5. Business invariants for the transition.

Knowing a requisition ID must not be sufficient to invoke a later workflow stage. The client must not directly assign an arbitrary state.

**SEC-WORKFLOW-001**

> Requisition state transitions must be explicit and server-authorized.

**SEC-WORKFLOW-002**

> A client must not directly assign an arbitrary workflow state.

---

# 19. T14 — Public Seed/Admin Provisioning

### Current risk

The audit identified public seed functionality capable of exposing seed credentials and provisioning privileged seed accounts.

### Threat

Unauthenticated users obtain or trigger privileged account creation.

### Requirement

Seed/admin provisioning must not be publicly available in production.

**SEC-ADMIN-001**

> Seed-user provisioning must be development/test-only or explicitly protected by an administrative deployment mechanism.

**SEC-ADMIN-002**

> Seed endpoints must never disclose privileged account passwords.

**SEC-ADMIN-003**

> Production authentication must not depend on a shared hard-coded seed password.

---

# 20. T15 — Account Enumeration

### Current behavior

Login returns the same 401 detail for an unknown username and an incorrect password. Other public paths disclose account existence or information: signup returns distinct duplicate-username and duplicate-email responses, while `/auth/seed-users` returns seed-user information and the configured default seed credential. Treat these as current enumeration/disclosure paths; the login response alone does not cover them.

### Threat

Different responses allow attackers to determine whether a username/account exists.

### TARGET/FUTURE requirement

Authentication and recovery flows should avoid unnecessary account-existence disclosure.

**SEC-ABUSE-001**

> Login failure responses should not reveal whether a username exists.

Where different HTTP statuses are required internally, externally observable responses should be designed to minimize enumeration.

---

# 21. T16 — Brute Force / Credential Stuffing

### Current status

No login rate limiter or credential-stuffing control was found in the application code. The following are **TARGET/FUTURE** requirements, not existing controls.

### Threat

An attacker repeatedly submits passwords against an account.

### Requirement

Authentication endpoints must implement rate limiting and abuse controls.

**SEC-ABUSE-002**

> Login attempts must be rate-limited.

**SEC-ABUSE-003**

> Signup and recovery-related endpoints must have appropriate abuse controls.

**SEC-ABUSE-004**

> Security events must record relevant rate-limit triggers without storing plaintext credentials.

---

# 22. T17 — Password Exposure

### Requirement

**SEC-PASSWORD-001**

> Plaintext passwords must never be stored.

**SEC-PASSWORD-002**

> Plaintext passwords must never be logged.

**SEC-PASSWORD-003**

> Password verification must use the approved password-hashing mechanism.

---

# 23. T18 — Google OAuth Account-Linking Abuse

### Current status

No Google OAuth/OIDC endpoints, provider identifiers, or token-validation flow were found in the repository. This section defines **TARGET/FUTURE** requirements only; Google authentication is not an existing control.

### Threat

An attacker attempts to associate an external Google identity with an existing privileged local account.

### Requirements

Google OIDC must validate:

* Authorization state
* ID-token signature
* Issuer
* Audience
* Expiration
* Required identity claims

**SEC-OAUTH-001**

> Google authentication must use the authorization-code/OIDC flow.

**SEC-OAUTH-002**

> The application must validate the Google identity before creating a local session.

**SEC-OAUTH-003**

> Google authentication must not automatically assign privileged application roles.

**SEC-OAUTH-004**

> Account linking must require explicit and validated local-account association rules.

---

# 24. T19 — CSRF Against Cookie Authentication

Moving from bearer tokens to cookies introduces browser cross-site request considerations. `HttpOnly` prevents script from reading a cookie value; it does not prevent the browser from attaching that cookie to a cross-site request and therefore does not eliminate CSRF.

### TARGET/FUTURE requirement

Cookie-authenticated state-changing operations must have an appropriate CSRF defense.

Possible implementation mechanisms may be selected during implementation design, but the final system must have an explicit CSRF strategy.

**SEC-CSRF-001**

> Cookie-authenticated state-changing requests must be protected against CSRF.

---

# 25. T20 — Sensitive Action Abuse

Some operations deserve stronger authentication than ordinary browsing.

Examples:

* Password change
* Email/security setting changes
* Account recovery
* High-risk administrative actions
* Security-sensitive account linking

**SEC-STEPUP-001**

> Sensitive actions must support step-up authentication where defined by policy.

---

# 26. T21 — Security Event Loss

### Threat

Security-relevant actions occur without an auditable record.

### Required events

At minimum:

* LOGIN_SUCCESS
* LOGIN_FAILURE
* GOOGLE_LOGIN
* SESSION_CREATED
* SESSION_REVOKED
* LOGOUT
* PASSWORD_CHANGED
* ACCOUNT_APPROVED
* ACCOUNT_REJECTED
* ACCOUNT_DISABLED
* ACCOUNT_LINKED
* AUTHORIZATION_FAILURE
* RATE_LIMIT_TRIGGERED

**SEC-AUDIT-001**

> Security-sensitive authentication and authorization events must be recorded.

**SEC-AUDIT-002**

> Security logs must not contain plaintext passwords or raw session identifiers.

---

# 27. T22 — Self-Assigned SUPER_ADMIN Through Public Signup

### Current behavior

Public signup accepts a client-submitted role. `SUPER_ADMIN` is included in the accepted `UserRole` enum. Signup creates the account with `is_approved=false` but returns a JWT immediately. Required current-user resolution checks `is_active` but not `is_approved`, then loads the database user's role. As a result, an unauthenticated caller can request `SUPER_ADMIN`, receive a usable token, and pass endpoints that authorize by comparing the resolved user's role to `SUPER_ADMIN`, including user listing, approval, and rejection.

### Threat

An unauthenticated caller self-assigns administrative authority through signup and uses the immediately issued credential to invoke Super Admin operations before approval.

### TARGET/FUTURE control

Publicly supplied role values must not grant privileged authority. Privileged roles must be assigned only through a trusted, explicitly authorized administrative process, and an unapproved account must not resolve as an authorized principal.

**SEC-AUTHZ-004**

> A caller must not be able to assign or obtain privileged authorization through public registration or other client-controlled account fields.

---

# 28. T23 — Invalid Credentials on Optional-Authentication Routes

### Current behavior

`get_optional_user` returns `None` when credentials are absent, malformed, expired, or otherwise fail token decoding. It does not reject the request or distinguish an invalid credential from an anonymous request. Routes using it can therefore continue through their anonymous behavior even when a caller supplied an invalid token. On requisition routes, for example, authenticated callers receive some requester/CPSE checks while anonymous callers bypass those checks; invalid credentials take the anonymous path. The dependency also does not check active or approved account state.

### Threat

A caller can present unusable credentials and receive the behavior reserved by the handler for anonymous callers, bypassing checks that execute only when a user resolves.

### TARGET/FUTURE control

Routes must be explicitly classified as public or authenticated. On an authenticated route, absent, invalid, malformed, expired, inactive-account, or otherwise unusable credentials must fail authentication. Optional identity may be used only on explicitly public routes with clearly defined anonymous and authenticated policies; invalid presented credentials must not silently downgrade to anonymous behavior.

**SEC-AUTH-004**

> Invalid or unusable credentials must not be treated as anonymous credentials on routes whose behavior depends on authenticated identity.

---

# 29. T24 — Unauthenticated Public Data Exposure

### Current behavior

Several read routes have no authentication dependency and return business or audit information, including audit entries/exports, requisitions, inventory and HITL data, graph/depot information, and ingested document metadata or raw-text previews. Some routes are globally scoped; others accept caller-supplied identifiers or filters. These responses can be accessed without first establishing an identity.

### Threat

An unauthenticated caller reads sensitive business information directly through a public endpoint or enumerates records. This is distinct from IDOR: IDOR concerns an authenticated caller accessing a resource outside their authority by supplying its identifier, while public data exposure requires no authenticated identity at all.

### TARGET/FUTURE control

Sensitive data must be protected by default. Each intentionally public read must be explicitly classified and limited to approved data; all other reads must require authentication and applicable tenant, role, and resource authorization. Client-supplied IDs and filters must not establish access rights.

**SEC-API-003**

> Sensitive business, audit, inventory, requisition, and document data must not be exposed by an endpoint unless that endpoint is explicitly approved for public access and returns only approved public data.

---

# 30. T25 — Cross-Site Scripting Against Browser Authentication

### Current behavior

The current frontend stores its bearer JWT in `localStorage`, which same-origin JavaScript can read. An XSS flaw could therefore expose a reusable bearer token. A future `HttpOnly` cookie prevents JavaScript from reading the cookie value, reducing direct credential theft; it does not prevent injected script from issuing authenticated same-origin requests while running in the victim's browser.

### Threat

Injected script steals a localStorage token or uses the victim's active browser session to perform actions. Cookie-based authentication changes the credential-exfiltration risk but does not make XSS harmless.

### TARGET/FUTURE control

Prevent and mitigate script injection using context-appropriate output handling and browser security controls. Do not expose session credentials to application JavaScript. Continue to apply authorization on every sensitive request.

**SEC-XSS-001**

> Browser authentication must limit script access to reusable credentials, and the application must apply appropriate controls against script injection.

---

# 31. Security Requirements by Layer

## Identity Layer

Must guarantee:

* Trusted user identity
* Trusted account state
* Trusted role
* Trusted CPSE
* No client-controlled identity substitution

---

## Authentication Layer

Must guarantee:

* Password verification
* Active-account enforcement
* Approval enforcement
* Secure session creation
* Google OIDC validation
* Authentication abuse controls

---

## Authorization Layer

Must guarantee:

* Permission-based authorization
* Centralized policy
* Explicit administrative authorization
* No role-only shortcuts where resource policy is required

---

## Tenant Layer

Must guarantee:

* Server-derived CPSE
* No authorization through `X-CPSE-ID`
* Cross-CPSE access only through explicit policy

---

## Resource Layer

Must guarantee:

* Resource-level authorization
* Ownership/operational-authority checks
* CPSE checks
* No IDOR

---

## Workflow Layer

Must guarantee:

* Valid state transitions
* Actor authorization
* State-dependent permissions
* No client-controlled arbitrary state changes

---

# 32. Security Invariants

These are **TARGET/FUTURE invariants**. They are not all true of the current repository; current deviations are described in the threat sections above.

### INV-001

No unapproved account can establish a usable authenticated session.

### INV-002

No inactive account can authenticate or use an authenticated session.

### INV-003

No client-controlled role can grant authorization.

### INV-004

No client-controlled CPSE can grant tenant access.

### INV-005

No resource ID alone can grant resource access.

### INV-006

No ordinary authenticated user can perform an administrative operation without the required permission.

### INV-007

No client can arbitrarily advance a requisition workflow state.

### INV-008

No production endpoint can expose privileged seed credentials.

### INV-009

Logout must invalidate the corresponding server-side session.

### INV-010

Security-sensitive actions must produce appropriate security events.

---

# 33. Security Test Categories

The implementation must eventually be tested against these categories.

## Authentication Tests

* Valid login
* Invalid password
* Unknown username
* Unapproved account
* Disabled account
* Session creation
* Session expiry
* Logout
* Revoked session

## Authorization Tests

For every protected endpoint:

* Unauthenticated request
* Correct permission
* Missing permission
* Incorrect role
* Privilege escalation attempt

## Tenant Tests

* Same-CPSE access
* Cross-CPSE read
* Cross-CPSE mutation
* Forged `X-CPSE-ID`
* Client-supplied CPSE field
* Privileged cross-CPSE operation

## Resource Tests

* Own resource
* Another user's resource
* Nonexistent resource
* Forged resource ID
* Cross-tenant resource ID

## Workflow Tests

* Valid transition
* Invalid transition
* Unauthorized transition
* Skipping state
* Replaying transition
* Client-controlled state

## Session Tests

* Cookie attributes
* Session revocation
* Disabled-user session
* Expired session
* Concurrent sessions
* Session fixation attempt

## Abuse Tests

* Repeated login failures
* Credential stuffing
* Enumeration behavior
* Signup abuse
* Rate-limit enforcement

## OAuth Tests

* Invalid state
* Invalid issuer
* Invalid audience
* Expired identity token
* Invalid signature
* Unauthorized account linking
* Privileged-role escalation attempt

---

# 34. Security Acceptance Criteria

These are **TARGET/FUTURE** acceptance criteria. AUTH-004 is considered satisfied when the implementation design and subsequent implementation can demonstrate:

1. Browser authentication uses server-side sessions rather than localStorage JWTs.
2. Unapproved users cannot establish usable sessions.
3. Disabled users cannot authenticate or use existing sessions.
4. Logout revokes the server-side session.
5. Backend authorization is centralized and permission-based.
6. Resource-level authorization exists.
7. CPSE is derived from trusted identity.
8. `X-CPSE-ID` cannot establish authorization.
9. Business mutations require explicit authorization.
10. Requisition transitions are state- and permission-controlled.
11. Public seed/admin provisioning is removed or development-only.
12. Seed credentials are never exposed.
13. Authentication endpoints have abuse protection.
14. Cookie-based authentication has an explicit CSRF defense.
15. Google OIDC validates external identity correctly.
16. Sensitive operations support appropriate step-up authentication.
17. Security events are recorded.
18. Security-sensitive secrets and credentials are not logged.
19. Automated tests cover authentication, authorization, tenant isolation, resource access, workflow transitions, session behavior, and abuse cases.

---

# 35. Threat Model Decision

The authentication subsystem is treated as a **security boundary**, not merely a login feature.

The implementation must therefore follow:

`Identity`
→ `Authentication`
→ `Permission`
→ `CPSE Policy`
→ `Resource Authorization`
→ `Business Operation`
→ `Audit`

No layer may be skipped for a sensitive operation.

---

# 36. Explicit Non-Goals for AUTH-004

This document does NOT implement:

* Database schema
* Session table
* API code
* Frontend authentication changes
* Google OAuth code
* Password reset implementation
* Email verification implementation
* Rate-limit infrastructure
* Complete business authorization refactor

Those belong to later tasks.

---

# 37. Next Task

**AUTH-005 — Database & Session Design**

AUTH-005 must define:

* User/account schema changes
* Session schema
* Session lifecycle
* Indexes
* Constraints
* Revocation model
* Expiration model
* Security-event persistence requirements
* Migration strategy
* Relationship between User, Session, and security events

No implementation should begin until AUTH-005 is approved.
