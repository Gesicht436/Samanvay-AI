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
