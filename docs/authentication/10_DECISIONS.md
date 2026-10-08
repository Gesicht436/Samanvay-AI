# Authentication Architecture — Decision Log

This file records implementation-level architecture decisions taken after the
frozen AUTH-002 … AUTH-007 documents. Frozen decisions in those documents
remain authoritative unless explicitly amended here.

---

## 5J.3 — Account-management implementation decisions

Branch: `auth-development-shourya` · Source: AUTH-5J.3 architecture decisions

### D-5J.3-1 — `ACCOUNT_PROVISIONED` security event — ADOPTED

The frozen AUTH-006 §7 event vocabulary is amended to add
`ACCOUNT_PROVISIONED`.

* `POST /api/v1/auth/users` emits exactly one `ACCOUNT_PROVISIONED` event per
  successful provisioning.
* The event identifies the authenticated provisioning actor (`user_id`), the
  actor session (`session_id`), and the target account (`target_user_id` and
  `target_username` in sanitized metadata).
* The `User` INSERT and the `ACCOUNT_PROVISIONED` event are committed
  atomically in the same database transaction.
* Passwords, password hashes, session secrets, session-token hashes, CSRF
  tokens, and other secrets must never enter event metadata.

### D-5J.3-2 — Account disable/enable — RESERVED (not implemented)

`ACCOUNT_DISABLE` remains defined in AUTH-007 but is intentionally
unimplemented and reserved pending future architectural specification. No
disable endpoint, enable endpoint, `ACCOUNT_ENABLE` permission, role-edit
endpoint, or CPSE/depot-edit endpoint may be created, and no lifecycle
behavior for them may be invented, until that specification exists.

### D-5J.3-3 — Provisioning CPSE/depot server-side validation — UNRESOLVED

The frozen architecture requires the server to assign/validate CPSE and depot
during account provisioning, but the repository currently has no canonical
CPSE/depot catalog. The source of that catalog (configuration, reference
table, enumeration, or derivation from existing tenant data) is an open,
future architectural/data-source decision. 5J.3 must not invent a catalog,
table, model, or enum for it. Client-supplied CPSE/depot values remain
provisioning payload data only and never establish authorization authority
(AUTH-007 §18 invariants 3–4 continue to apply).

### D-5J.3-4 — Production documentation/OpenAPI gating — ADOPTED (implemented)

Frozen requirement implemented: when `APP_ENV` is `production`/`prod`, the
application is constructed without `/docs`, `/redoc`, and `/openapi.json`
(404). Non-production deployments keep the existing documentation/OpenAPI
behavior.

---

## Credential authority — architecture decision

Source: Task 16B credential-authority reconciliation. This is the canonical
record of the credential-authority direction referenced by
`02_ARCHITECTURE.md`, `05_DATABASE_DESIGN.md`, `06_IMPLEMENTATION_DESIGN.md`,
`11_SHOURYA_SECURITY_SPEC.md`, and the system runbook.

### D-CRED-1 — Credential authority direction — ACCEPTED (implementation pending identity-provider decision)

**Decision.** Samanvay will use an external organizational credential
authority/federation as the authoritative source for organizational
username/password verification. Samanvay must not become the authoritative
password store for organizational credentials.

**Status.** Accepted architectural direction; implementation pending the
identity-provider integration decision. Exact protocol/provider:
**OPEN ARCHITECTURE DECISION**. No specific identity protocol, provider, or
integration mechanism has been selected, and none may be assumed by the
application until that decision is formally made.

**Context.** Maintaining a second authoritative credential store alongside
the organization's own would create duplicated credential state, credential
synchronization problems, independent password lifecycle management,
unnecessary credential security exposure, and account
deprovisioning/lifecycle divergence between the organization and the
application. These are the architectural reasons for the selected target
direction; they are not claims of a vulnerability in the current
development system.

**Chosen direction: External Organizational Authority / Federation.**

```text
User
  │
  │ Organizational username + password
  ▼
Samanvay authentication entry point
  │
  │ credential verification
  ▼
External Organizational Credential Authority
  │
  │ successful authentication
  ▼
Samanvay establishes server-side application session
  │
  ▼
__Host-samanvay_session
  │
  ▼
Authenticated application use
```

**Current implementation.** Local bcrypt credential verification exists
today: `users.hashed_password` → bcrypt verification → server-side
`AuthSession` → hashed session secret → `__Host-samanvay_session` HttpOnly
cookie. No external credential authority is integrated; the codebase
contains no LDAP, Active Directory, OIDC, SAML, Kerberos, SCIM, directory,
or REST identity integration.

**Target architecture.** Verification runs at the external organizational
credential authority; on successful authentication, Samanvay still creates
the existing server-side `AuthSession` (random session secret → SHA-256
hash stored server-side → `__Host-samanvay_session`, HttpOnly +
SameSite=Lax + Secure in production). The session architecture is unchanged
by this decision.

**Responsibility boundary.**

| External Organizational Authority | Samanvay |
| --- | --- |
| Identity | Application session |
| Credential verification | Authorization |
| Password storage | RBAC |
| Password policy | CPSE/resource boundaries |
| Password lifecycle | CSRF protection |
| Credential rotation | Application security events |
| Credential reset | Session revocation |
| Credential disablement at the identity authority | Account/application-state enforcement |

The external authority authenticates the user; Samanvay decides what that
authenticated user is allowed to do inside the application.

**What remains unresolved.** The exact identity protocol/provider/
integration mechanism for the external authority. It must be determined
from the organization's actual identity infrastructure before any
implementation begins. The eventual migration away from local
`users.hashed_password` organizational password storage is a future
implementation/migration task, to be specified only after the integration
contract exists.

**Consequences.**

* Until the integration contract is formally specified, the current
  local-bcrypt implementation is preserved unchanged: no code, schema,
  migration, login-flow, session, CSRF, or authorization changes.
* No provider or protocol may be documented, referenced, or coded as
  selected, assumed, or implemented.
* Password verification continues against the local account store.
* Session design, RBAC, and authorization are unaffected by this decision.
