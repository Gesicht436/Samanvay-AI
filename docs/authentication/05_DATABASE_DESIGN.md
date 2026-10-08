# AUTH-005 — Database & Session Design

**Project:** Samanvay-AI
**Branch:** `auth-development-shourya`
**Status:** Design
**Depends on:** AUTH-001, AUTH-002, AUTH-003, AUTH-004
**Next:** AUTH-006 — Authentication Implementation Design

---

## 1. Purpose

This document defines the database architecture required to support the target authentication and authorization system.

The design covers:

* User/account state
* Server-side authentication sessions
* Session lifecycle
* Session revocation
* Security events
* Account approval/activation
* OAuth identity association — historical logical model only, not part of the current target (see Section 23)
* Required indexes and constraints
* Migration requirements

This document defines the data model only.

It does not implement the models, migrations, routes, or services.

---

# 2. Design Principles

The database must support the following security properties:

1. Authentication state must be server-side.
2. Browser authentication must use a session cookie.
3. Sessions must be individually revocable.
4. Disabled accounts must invalidate usable authentication.
5. Unapproved accounts must not establish authenticated sessions.
6. User role and CPSE must come from trusted account data.
7. Session identifiers must not be stored in plaintext.
8. Security events must be auditable.
9. (Historical) If an external identity model is ever explicitly re-approved, external identities must be uniquely associated with the correct local user; no external identity persistence exists or is targeted today.
10. Database constraints should prevent invalid security states where practical.

---

# 3. Existing User Model

The current `User` model already contains:

* `id`
* `username`
* `email`
* `hashed_password`
* `full_name`
* `role`
* `cpse`
* `depot_id`
* `is_active`
* `is_approved`
* `created_at`

The target design should preserve these concepts unless a later migration explicitly changes them.

The current authentication system should NOT create a second user/account table.

---

# 4. User Account Requirements

The existing `User` entity remains the canonical local identity.

The following fields remain authoritative:

| Field             | Purpose                          |
| ----------------- | -------------------------------- |
| `id`              | Internal user identifier         |
| `username`        | Local login identity             |
| `email`           | Optional/unique contact identity |
| `hashed_password` | Local password authentication    |
| `full_name`       | Display identity                 |
| `role`            | Application role                 |
| `cpse`            | Tenant identity                  |
| `depot_id`        | Operational location             |
| `is_active`       | Account enabled/disabled         |
| `is_approved`     | Administrative approval state    |
| `created_at`      | Account creation timestamp       |

**Prototype credential store.** `hashed_password` stores the prototype's local credentials for development/demo authentication (the **prototype credential authority** of the submitted prototype). It is not the organization's authoritative credential store and does not represent organizational password ownership (`10_DECISIONS.md` D-CRED-1). Real organizational deployment delegates credential verification and password lifecycle to the organization-approved identity infrastructure; the exact provider/protocol is deployment-specific and unresolved.

Future account-management requirements may introduce additional timestamps such as:

* `updated_at`
* `approved_at`
* `approved_by`
* `disabled_at`

These should be introduced only when their operational semantics are defined.

### Account-state database constraints

The target database columns `users.is_active` and `users.is_approved` are both `BOOLEAN NOT NULL`, with database defaults matching the current application defaults: `TRUE` and `FALSE`, respectively. The current SQLAlchemy `default=` values are application-side defaults and do not prevent database rows from containing `NULL`.

Before adding `NOT NULL`, the migration must inspect existing NULLs and backfill them explicitly. To preserve the current authentication behavior, where a falsey value blocks login, NULL values map to `FALSE` for both columns unless reviewed account evidence establishes a different state. Review and document any exceptions before applying the constraint; do not silently promote an account to approved or active. New writes must not permit NULL.

---

# 5. Role Integrity

The existing application roles are:

* `SITE_ENGINEER`
* `MATERIALS_MANAGER`
* `TECHNICAL_AUTHORITY`
* `CISF_SECURITY`
* `VIGILANCE_AUDITOR`
* `SUPER_ADMIN`

The database must not allow a client request to arbitrarily create a privileged role through public signup.

Therefore:

> Role assignment is an authorization-controlled server operation, not a freely assignable signup field.

The exact permission mapping will be defined separately from the database schema.

The existing `AUDITOR` versus `VIGILANCE_AUDITOR` inconsistency must be resolved during authorization implementation.

---

# 6. CPSE Integrity

`User.cpse` is the canonical tenant association for a normal user.

The database design must support the invariant:

`Authenticated User → User.cpse → Tenant Context`

rather than:

`HTTP Header → Tenant Context`

A client-controlled `X-CPSE-ID` must not modify the user's database identity or establish authorization.

---

# 7. Session Model

Introduce a dedicated server-side session table.

Proposed logical entity:

`AuthSession`

The target table name is `auth_sessions`. The target PostgreSQL table uses UUID for its primary key, generated by the application as a UUIDv4. This database identifier is not the browser credential. `user_id` is a required PostgreSQL `INTEGER` foreign key matching the existing `users.id` type.

Minimum fields:

| Field                | Type / Concept         | Purpose                            |
| -------------------- | ---------------------- | ---------------------------------- |
| `id`                 | PostgreSQL `UUID`       | Required database primary-key identifier; generated as UUIDv4 |
| `session_token_hash` | `VARCHAR(64)`           | Required lowercase hexadecimal SHA-256 digest of the browser secret; unique |
| `user_id`            | PostgreSQL `INTEGER`    | Required FK to `users.id`          |
| `created_at`         | `TIMESTAMP WITH TIME ZONE` | Required; UTC session creation time |
| `last_seen_at`       | `TIMESTAMP WITH TIME ZONE` | Required; UTC time of last accepted use |
| `expires_at`         | `TIMESTAMP WITH TIME ZONE` | Required; UTC absolute expiration |
| `revoked_at`         | `TIMESTAMP WITH TIME ZONE` | Nullable; UTC revocation time      |

Optional metadata:

* `user_agent`
* `ip_address`
* `device_label`
* `revocation_reason`

These fields are for session management and security analysis and must not become authorization credentials.

All listed timestamps use timezone-aware PostgreSQL `TIMESTAMP WITH TIME ZONE` (`DateTime(timezone=True)` in SQLAlchemy). Application values and database defaults are UTC instants. `created_at`, `last_seen_at`, and `expires_at` are NOT NULL; `revoked_at` is nullable until revocation.

---

# 8. Session Identifier Storage

The raw browser session identifier must NOT be stored in plaintext in PostgreSQL.

The browser receives a 256-bit cryptographically random secret, encoded as unpadded base64url text in the cookie. This secret is distinct from the database UUID primary key.

The database stores:

`SHA-256(raw 32-byte session secret)` as lowercase 64-character hexadecimal text in `VARCHAR(64) NOT NULL`.

The hash is deterministic so the server can hash a presented cookie secret and perform an exact equality lookup against the unique `session_token_hash` index. The raw browser secret is never stored in PostgreSQL. A separate server-side pepper/key is not required: the secret is high-entropy random data rather than a human-chosen password. The secret must not be logged.

When a request arrives:

`base64url cookie secret`
→ decode to the original 32 bytes and SHA-256 hash
→ database lookup
→ session record
→ user lookup
→ account-state validation

This reduces the impact of database disclosure.

---

# 9. Session Identifier Properties

The browser session secret must be:

* Cryptographically random
* High entropy
* Unpredictable
* Unique
* Not derived from user ID
* Not derived from username
* Not derived from timestamp
* Not derived from password

The database record identifier (`AuthSession.id`, UUIDv4), browser session secret (32 random bytes, base64url encoded), and stored session-secret hash (SHA-256 lowercase hex) are three separate values and must never be substituted for one another.

---

# 10. Session Lifecycle

Target lifecycle:

```text
LOGIN
  ↓
Credential Verification
  ↓
Account State Check
  ↓
Generate Random Session Secret
  ↓
Store Session Hash
  ↓
Set Secure HttpOnly Cookie
  ↓
Authenticated Requests
  ↓
Update last_seen_at
  ↓
Logout / Expiration / Revocation
  ↓
Session Invalid
```

---

# 11. Session Creation

A session may be created only after:

1. User exists.
2. Password authentication succeeds (local bcrypt verification today). OAuth/OIDC is not part of the current target (Section 23); the credential-authority direction is External Organizational Authority / Federation (`10_DECISIONS.md` D-CRED-1), with the exact protocol/provider still an open architecture decision.
3. User is active.
4. User is approved.
5. Authentication policy permits login.

Then:

* Generate new session secret.
* Store only its hash.
* Associate session with `user_id`.
* Set creation/expiration timestamps.
* Set browser cookie.

No session should be created for an unapproved account.

---

# 12. Session Expiration

The session must have an absolute expiration:

`expires_at`

The application may also implement idle expiration using:

`last_seen_at`

The exact duration is an implementation/configuration decision.

The database must support both mechanisms.

Recommended distinction:

* **Absolute expiry:** maximum lifetime of a session.
* **Idle expiry:** maximum period without activity.

The final durations must be configurable rather than hard-coded into database logic.

---

# 13. Session Revocation

A session becomes invalid when:

* `revoked_at IS NOT NULL`
* `expires_at <= current_time`
* associated user is inactive
* authentication policy otherwise invalidates it

Logout should set:

`revoked_at = current_time`

rather than merely deleting browser state.

---

# 14. Account Disablement

The session table should not duplicate account state.

Instead:

`AuthSession.user_id`
→ `User.is_active`

Every authenticated request must validate the current account state.

This prevents a disabled user from continuing to use an existing session.

---

# 15. Session Deletion vs Revocation

Preferred model:

**Revocation is the authoritative state transition.**

A revoked or expired session is first soft-revoked/expired and retained for a defined operational retention period. Physical deletion is permitted only after that period and only under the FK behavior in Section 27. Deleting a session sets retained event references to NULL; the `SecurityEvent` row itself remains.

This preserves the ability to reason about:

* when the session was revoked
* why it was revoked
* security investigations
* session-management history

Therefore:

`active session → revoked/expired session → retention period → optional cleanup`

rather than:

`active session → immediate deletion`

---

# 16. Session Indexes

Required indexes should include:

### Active-session lookup by `session_token_hash`

Create a unique B-tree index on `session_token_hash`. This is the primary cookie-to-session lookup and enforces one session row per hash.

### `user_id`

Supports:

* Session center
* Revoke all sessions
* Account disablement handling
* User session lookup

### Expiry cleanup by `expires_at`

Supports:

* Expired-session cleanup

### Revoked-session filtering by `revoked_at`

Supports:

* Session cleanup
* Session state queries

Use a B-tree index supporting revoked-session queries. Also support active-per-user lookup with a composite `(user_id, expires_at)` index restricted to rows where `revoked_at IS NULL`; do not use a time-dependent partial-index predicate.

---

# 17. Session Constraints

The database should enforce where practical:

* Session must reference an existing user.
* Session identifier hash must be unique.
* `expires_at` must be later than `created_at`.
* `revoked_at`, when present, should not precede `created_at`.

The `user_id` FK uses `ON DELETE CASCADE`: deleting a local user removes that user's session credentials. This does not delete security events because their user/session FKs use `ON DELETE SET NULL` (Section 27).

The database should not attempt to encode all application authorization logic as constraints.

---

# 18. Security Event Model

Introduce a dedicated security-event entity.

Proposed logical entity:

`SecurityEvent`

The target table name is `security_events`. This target model is authoritative for authentication/security telemetry. `id` is a required PostgreSQL `UUID` primary key generated as UUIDv4. `user_id` is a nullable PostgreSQL `INTEGER` FK to `users.id`; `session_id` is a nullable PostgreSQL `UUID` FK to `auth_sessions.id`.

Purpose:

Store authentication and authorization security events independently from normal business audit records.

Minimum fields:

| Field        | Purpose                                   |
| ------------ | ----------------------------------------- |
| `id`         | PostgreSQL `UUID` primary key, UUIDv4; NOT NULL |
| `event_type` | Required security event category           |
| `user_id`    | Nullable PostgreSQL `INTEGER` FK to `users.id` |
| `session_id` | Nullable PostgreSQL `UUID` FK to `auth_sessions.id` |
| `created_at` | Required `TIMESTAMP WITH TIME ZONE`, UTC   |
| `success`    | Required success/failure indicator         |
| `ip_address` | Nullable request source where appropriate  |
| `user_agent` | Nullable client information where appropriate |
| `metadata`   | Required PostgreSQL `JSONB`; structured non-secret context |

`SecurityEvent.created_at` is NOT NULL and stores a UTC instant. `SecurityEvent.user_id` and `session_id` are nullable to support anonymous events and retained history after account/session deletion.

---

# 19. Security Event Types

The system should support at minimum:

* `LOGIN_SUCCESS`
* `LOGIN_FAILURE`
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

Additional event types may be added without changing the fundamental model.

---

# 20. Security Event Rules

Security events must never contain:

* Plaintext passwords
* Password hashes
* Raw session secrets
* OAuth client secrets
* Access tokens
* Refresh tokens

Sensitive request data must be excluded or sanitized before persistence.

---

# 21. Anonymous Security Events

Some events occur before a user can be identified.

For example:

`LOGIN_FAILURE`

may correspond to an unknown username.

Therefore:

`user_id = NULL`

must be supported for appropriate security events.

---

# 22. Session ↔ Security Event Relationship

Where possible:

`SecurityEvent.session_id → AuthSession.id`

This allows investigators to associate:

`login → session → logout/revocation`

However, events must remain valid when no session exists.

Examples:

* Failed login
* Invalid credentials
* Rate-limit trigger

Therefore the relationship is optional.

When present, this is an FK to the session UUID and uses `ON DELETE SET NULL`. Historical events remain even if a session row is eventually purged.

---

# 23. OAuth Identity Model

### Status: retired from the current target (Sections 23–25 are historical)

Google OIDC / OAuth identity persistence is **not part of the current authentication target**. No `OAuthIdentity` table exists, no migration creates one, and none may be created without an explicit approved task. Sections 23–25 are retained only as a historical logical model in case an external identity mechanism is ever explicitly re-approved; they must not be implemented as-is.

The credential-authority direction is External Organizational Authority / Federation (`10_DECISIONS.md` D-CRED-1); the exact protocol/provider remains an OPEN ARCHITECTURE DECISION.

If an external identity model is ever re-approved, it requires a persistent mapping between the external identity and the local user, using a dedicated entity rather than provider-specific identity fields on `User`.

Historical logical entity:

`OAuthIdentity`

In the historical model, the table name is `oauth_identities`; `id` is a required PostgreSQL `UUID` primary key generated as UUIDv4. `user_id` is a required PostgreSQL `INTEGER` FK matching `users.id`.

Minimum fields:

| Field              | Purpose                              |
| ------------------ | ------------------------------------ |
| `id`               | PostgreSQL `UUID` primary key, UUIDv4; NOT NULL |
| `user_id`          | PostgreSQL `INTEGER` FK to `users.id`; NOT NULL |
| `provider`         | `VARCHAR(32) NOT NULL`; identity provider |
| `provider_subject` | `VARCHAR(255) NOT NULL`; provider stable subject |
| `created_at`       | Required `TIMESTAMP WITH TIME ZONE`, UTC |
| `last_login_at`    | Nullable `TIMESTAMP WITH TIME ZONE`, UTC until first login |

Both timestamp fields are timezone-aware PostgreSQL timestamps (`DateTime(timezone=True)`). `created_at` is required; `last_login_at` is nullable.

---

# 24. OAuth Identity Uniqueness

The combination:

`provider + provider_subject`

must be unique.

This prevents one external identity from being associated with multiple local accounts.

Example:

`google + 123456789`

must identify one local identity mapping.

Use a unique B-tree constraint/index over `(provider, provider_subject)`; add a lookup index only if query plans show the unique index does not satisfy the lookup.

Email address alone must NOT be treated as the permanent external identity key.

---

# 25. OAuth Account Linking

The database relationship must represent:

`External Identity → Local User`

not:

`External Identity → Local Role`

The local user's role remains an application authorization property.

Google authentication must not grant:

`SUPER_ADMIN`

or any other privileged role.

---

# 26. Foreign-Key Relationships

Target logical relationships:

```text
User
 │
 ├──< AuthSession
 │
 ├──< SecurityEvent
 │
 └──< OAuthIdentity (historical only — not implemented)
```

Where:

`AuthSession.user_id → User.id`

`SecurityEvent.user_id → User.id`

`SecurityEvent.session_id → AuthSession.id`

`OAuthIdentity.user_id → User.id` (historical model only — not implemented)

---

# 27. Deletion Strategy

Authentication records contain security history.

Therefore, user deletion must not casually cascade-delete all security history.

The following FK actions are the target database contract:

| Foreign key | Nullability | `ON DELETE` | Effect |
| --- | --- | --- | --- |
| `AuthSession.user_id → users.id` | NOT NULL | `CASCADE` | User deletion removes that user's sessions. |
| `SecurityEvent.user_id → users.id` | NULL | `SET NULL` | Event history remains; the relational user link is cleared. |
| `SecurityEvent.session_id → auth_sessions.id` | NULL | `SET NULL` | Event history remains when a session is purged. |
| `OAuthIdentity.user_id → users.id` | NOT NULL | `CASCADE` | Historical model only (not implemented); would remove provider mappings, not security events. |

SecurityEvent rows are retained under the approved event-retention policy and are never cascade-deleted by user/session deletion. If an FK is cleared, only non-secret metadata may retain a necessary historical actor/session reference. A user hard-delete cascades its AuthSession rows immediately; the linked SecurityEvent rows remain with nullable user/session links cleared. User hard-deletion and legal retention policy remain product/compliance decisions.

Target behavior:

* Sessions are soft-revoked and retained through the operational retention period, then may be physically purged.
* (Historical) OAuth identities would be cascade-deleted with their local user; no such table exists.
* Security events are retained according to the event-retention policy; nullable FK links are set to NULL on deletion.

No destructive cascade should be introduced without explicit review.

---

# 28. Database Transaction Boundaries

Authentication state changes should be transactional where necessary.

Examples:

### Session creation

```text
Validate account
    ↓
Create session
    ↓
Commit
    ↓
Send session cookie
```

### Logout

```text
Validate session
    ↓
Revoke session
    ↓
Commit
    ↓
Clear browser cookie
```

### Account disablement

```text
Disable account
    ↓
Apply account-state change
    ↓
Commit
    ↓
Existing sessions fail subsequent validation
```

The exact transaction implementation belongs to the implementation task.

`AuthSession` state changes and their corresponding `SecurityEvent` inserts must use the same PostgreSQL transaction. Both commit or both roll back. For session creation, do not issue a success cookie unless the transaction commits. For logout/revocation, do not report success or clear the cookie unless revocation and its event commit; persistence failure is an operation failure and must be surfaced for retry/operations handling. Login-failure events have no session-state write but must not include credentials. No event is dual-written to `SovereignAuditLedger` as part of this transaction.

### SecurityEvent and SovereignAuditLedger boundary

`SecurityEvent` is authoritative for authentication/security telemetry. Existing `SovereignAuditLedger` remains the existing business/statutory hash-chain ledger; this design does not alter it. Authentication events, including session create/revoke/logout, are written only to `SecurityEvent` and are not duplicated in `SovereignAuditLedger`. The two stores are intentionally independent and have no FK/link. This avoids dual-write atomicity and hash-chain ordering changes; a future requirement to duplicate an event must be separately designed and must not be assumed by this schema.

---

# 29. Migration Requirements

The repository currently has no Alembic/revision framework. Startup calls `Base.metadata.create_all()`, which may create missing tables but does not safely evolve existing tables, add constraints, or backfill data. Production schema evolution requires a reviewed, versioned migration mechanism/process; `create_all()` alone is insufficient for modifying the persistent PostgreSQL schema. This document does not select or install a migration framework.

The migration and deployment plan must account for:

1. Preserve existing `User.id` values and existing bcrypt password hashes; do not create a parallel user table.
2. Inspect and backfill NULL `is_active`/`is_approved` values using the explicit policy in Section 4 before enforcing NOT NULL.
3. Inspect existing role values, including the `AUDITOR` versus `VIGILANCE_AUDITOR` inconsistency; do not silently rewrite roles as a side effect of schema migration.
4. Inspect email uniqueness and case-collision behavior before adding/changing email constraints or normalization.
5. Inspect CPSE/depot values and preserve valid existing associations; do not detach users from tenant/location data.
6. Preserve all existing `SovereignAuditLedger` rows and hash-chain values unchanged.
7. Create `AuthSession` and `SecurityEvent` tables, indexes, FKs, nullability, and constraints safely. Do not create an `OAuthIdentity` table — no OAuth identity persistence exists in the current target (Section 23 is historical).
8. Define deployment ordering: apply and verify the schema migration before deploying application code that requires the new tables/constraints. Coordinate application rollout with the completed JWT cutover recorded in Section 30; do not rely on `create_all()` to upgrade existing volumes.

Existing users must not accidentally become:

* inactive
* unapproved
* roleless
* detached from their CPSE

because of the migration.

### Seed/deployment interaction

Startup currently invokes `seed_users_if_empty`. For matching seed accounts, this code can reactivate and reapprove the account and restore its configured role. Before the authentication cutover, deployment planning must explicitly account for this behavior so startup seeding cannot undo reviewed account-state or role changes. The migration must not treat seed data as a source of authority for current administrative state without an explicit reviewed policy.

### Database privilege and reachability note

The current Docker Compose configuration publishes PostgreSQL on port 5432; the backend connects using the configured database user, and the initialization SQL grants that user database privileges. Before treating this authentication schema as production-ready, review database network exposure and runtime database privileges for the production deployment. This design does not change Compose or select a privilege model.

---

# 30. JWT Transition (Completed)

The application no longer uses JWT authentication; the JWT-era description below is historical.

The architecture uses server-side sessions.

Legacy JWTs were stateless and were never stored in PostgreSQL; they were not migrated into `AuthSession`. All current authentication uses server-side sessions.

Cutover behavior (executed by AUTH-006):

```text
Old JWT
   ↓
No longer accepted after migration cutover
   ↓
User performs normal login
   ↓
New server-side session created
```

At the declared application cutover, backend instances stopped accepting old JWT bearer credentials and require the server-side session mechanism. Users authenticate again to obtain sessions. (Historical guidance: rolling deployment must coordinate traffic draining/replacement so old and new instances do not leave an indefinite mixed JWT/session acceptance period; no such compatibility window exists today.)

The cutover audit covered every route using `get_optional_user` or other optional identity, in addition to routes that required JWTs. No route retains old optional-JWT behavior after the cutover.

No temporary compatibility layer remains; no hybrid JWT/session authentication mode is permitted.

---

# 31. Cookie/Database Relationship

The database stores:

`hash(session_secret)`

The browser stores:

`session_secret`

The browser does NOT receive:

* database session ID
* user role
* CPSE authorization token
* permission token

Authorization is resolved server-side.

---

# 32. Performance Considerations

Authentication lookup occurs frequently.

The session lookup path should therefore be efficient:

```text
session cookie
      ↓
hash
      ↓
indexed session_token_hash
      ↓
user_id
      ↓
indexed User lookup
      ↓
account state
      ↓
authorization
```

Required target indexes must support the actual lookup patterns without broad table scans:

* `AuthSession.session_token_hash`: unique B-tree for exact presented-secret-hash lookup.
* `AuthSession.user_id`: B-tree for user session listing/revocation.
* `AuthSession.expires_at`: B-tree for expiry cleanup.
* `AuthSession.revoked_at`: index/filter support for revoked-session queries; use a partial index for `revoked_at IS NOT NULL` where useful.
* Active sessions by user: composite `(user_id, expires_at)` B-tree with predicate `revoked_at IS NULL`.
* `SecurityEvent(user_id, created_at)`: supports user history, with nullable `user_id` for anonymous events.
* `SecurityEvent(session_id, created_at)`: supports session history; `session_id` is nullable.
* `SecurityEvent(event_type, created_at)`: supports event-type/time-window investigations.
* (Historical only, not part of the current target) `OAuthIdentity(provider, provider_subject)`: unique B-tree for external identity lookup.

Confirm indexes against the final query plans during implementation; do not create time-dependent partial-index predicates such as `expires_at > now()`.

---

# 33. Security Requirements Mapped to Database Design

| Requirement                  | Database Support                     |
| ---------------------------- | ------------------------------------ |
| Server-side sessions         | `AuthSession`                        |
| Session revocation           | `revoked_at`                         |
| Session expiry               | `expires_at`                         |
| Idle tracking                | `last_seen_at`                       |
| Session ownership            | `user_id` FK                         |
| Disabled-account enforcement | `User.is_active`                     |
| Approval enforcement         | `User.is_approved`                   |
| Security audit               | `SecurityEvent`                      |
| OAuth identity               | Not part of the current target; `OAuthIdentity` is a historical logical model only (Section 23) |
| External identity uniqueness | Not part of the current target; historical provider + subject unique constraint |
| Tenant identity              | `User.cpse`                          |
| Role identity                | `User.role`                          |

---

# 34. What This Design Does NOT Solve

The database schema alone does not solve:

* Authorization policy
* CPSE resource policy
* IDOR
* Workflow authorization
* Rate limiting
* CSRF
* XSS
* Password reset
* Google token validation
* Step-up authentication
* API access policy

Those require application-layer controls.

---

# 35. Open Decisions Before Implementation

The following must be finalized before implementation:

### D-005-01 — Session lifetime

Define:

* Absolute lifetime
* Idle timeout
* Remember-me behavior, if any

### D-005-02 — Session concurrency

Decide whether users may have:

* Unlimited sessions
* Limited concurrent sessions
* Explicit session-management controls

### D-005-03 — Session metadata

Decide which of:

* IP
* User agent
* Device label

will be retained.

### D-005-04 — Security-event retention

Define security-event and revoked/expired-session retention periods and cleanup schedule, consistent with statutory and operational requirements.

### D-005-05 — JWT cutover release window (resolved)

The JWT cutover was executed by AUTH-006; Section 30 records the completed behavior. No JWT acceptance window remains.

### D-005-06 — Migration mechanism

**Intentionally unresolved:** The repository specifies no migration framework. A versioned production migration process is mandatory, but framework selection belongs to deployment/tooling planning and must be completed before migration implementation. `create_all()` is not an upgrade mechanism.

---

# 36. AUTH-005 Acceptance Criteria

AUTH-005 is complete when:

1. User remains the canonical local identity.
2. Server-side authentication sessions have a dedicated model.
3. Raw session secrets are not stored in the database.
4. Sessions can expire.
5. Sessions can be revoked.
6. Sessions reference users.
7. Disabled/unauthorized account state can invalidate sessions.
8. Security events have a dedicated persistence model.
9. Security events can represent anonymous events.
10. Security events do not store authentication secrets.
11. `AuthSession` and `SecurityEvent` exact PostgreSQL types, nullability, UTC timestamp semantics, hash representation, and lookup are defined.
12. FK types and `ON DELETE` actions are defined; retained security events survive session/user deletion.
13. `User.is_active` and `User.is_approved` target `NOT NULL` constraints and a NULL backfill policy are defined.
14. Required session/security-event indexes match the target query patterns.
15. `SecurityEvent` is authoritative for auth telemetry; its relationship and failure/atomicity behavior versus `SovereignAuditLedger` are explicit.
16. Migration requirements preserve user IDs, bcrypt hashes, role/tenant data, and existing audit history; production migration is explicitly not delegated to `create_all()`.
17. Startup seeding behavior is an explicit migration/deployment consideration.
18. JWTs were not migrated; the cutover and optional-identity route audit were completed (Section 30).
19. PostgreSQL network exposure/runtime privileges are called out for production review.
20. No `OAuthIdentity` table is implemented or required; Google OIDC is not part of the current target (Section 23 is historical).
21. Remaining open items are only session/product or deployment/tooling decisions, not unresolved schema types or FK behavior.

---

# 37. Next Task

**AUTH-006 — Session & Authentication Implementation Design**

AUTH-006 should define the application-layer implementation before Claude begins coding:

```text
Cookie
  ↓
Session dependency
  ↓
User/account state
  ↓
Permission policy
  ↓
CPSE policy
  ↓
Resource authorization
  ↓
Business service
```

AUTH-006 will define:

* Authentication dependency
* Session lookup
* Login flow
* Logout flow
* Cookie behavior
* Authorization dependency
* Permission model
* Account-state checks
* Error behavior
* Security-event integration
* Migration/cutover behavior

OAuthIdentity persistence and Google OIDC are not part of the current target; Section 23 is historical reference only. The credential-authority direction is External Organizational Authority / Federation (`10_DECISIONS.md` D-CRED-1); the exact protocol/provider remains an OPEN ARCHITECTURE DECISION.

---

AUTH-005 revised after repository verification. Documentation only; no source code, migrations, dependencies, or runtime behavior changed.
