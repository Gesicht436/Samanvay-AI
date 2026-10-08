Owner: Shourya Mishra
Project: Samanvay-AI / BharatCodex
Scope: Application Authentication, Authorization, Tenant Isolation & Security Controls
Status: In Progress / Security Hardening Phase

1. Objective

Design and implement a secure application security layer for Samanvay-AI that:

Authenticates users with organizational username/password credentials, establishing a server-side application session after verification.
Records the credential-authority direction — External Organizational Authority / Federation (`10_DECISIONS.md` D-CRED-1): Samanvay must not become the authoritative organizational password store. The current implementation verifies credentials against the local account store with bcrypt, no external organizational identity authority is integrated, and the exact protocol/provider remains an OPEN ARCHITECTURE DECISION.
Establishes a secure application session after successful authentication.
Enforces role-based permissions.
Enforces CPSE/tenant isolation.
Protects sensitive application operations through explicit authorization checks.
Records security-relevant authorization failures for monitoring and investigation.
Prevents privilege escalation and cross-CPSE access.
2. Authentication Architecture

Model: Organizational username/password + server-side session

The intended user-facing credential model is organizational username/password. The current repository implementation verifies credentials locally with bcrypt against the application's account store and then establishes a server-side session.

User
  ↓
Samanvay-AI authentication endpoint (local bcrypt verification today)
  ↓
Account-state checks (is_active + is_approved)
  ↓
Samanvay-AI server-side session (HttpOnly session cookie)
  ↓
Authorization

The credential-authority direction is decided — External Organizational Authority / Federation (`10_DECISIONS.md` D-CRED-1): an external organizational authority owns credential verification and password storage, and Samanvay must not become the authoritative organizational password store. The exact protocol/provider/integration mechanism remains an OPEN ARCHITECTURE DECISION, to be determined from the organization's actual identity infrastructure before implementation. No external organizational credential authority (LDAP, Active Directory, OIDC, SAML, directory, federation, or otherwise) is currently implemented, and none may be invented or assumed without an explicit approved task.

Session-cookie security remains mandatory: `__Host-samanvay_session` in production, HttpOnly, SameSite=Lax, Secure in production, hashed session-secret storage, CSRF protection, login rate limiting, revocation, and account-state checks.

Out of scope:

Google Login
OIDC/SAML/SSO implementation unless explicitly re-approved later
JWT-based authentication architecture
Bearer-token API authentication
localStorage/sessionStorage authentication credentials
Independent identity provider
3. Authorization Model

Authorization follows:

Authenticated User
       ↓
Role
       ↓
Permission
       ↓
Resource / CPSE Scope
       ↓
Allow / Deny

The system uses explicit permissions rather than relying solely on frontend visibility or role names.

Authorization must be enforced server-side.

4. Tenant / CPSE Isolation

Every protected resource or operation must respect the user's authorized CPSE scope.

Security requirement:

A user authenticated for CPSE-A must not be able to access or mutate CPSE-B resources merely by manipulating IDs, requests, or frontend state.

Cross-CPSE operations require explicit authorization where the architecture permits them.

5. Protected Security Areas

My implementation scope covers authorization boundaries across:

Area	Security Responsibility
Requisitions	Tenant/resource authorization
Inventory	Read + mutation authorization
Ingest	Mutation + document read authorization
Graph	CPSE-scoped authorization
Matching	Match access authorization
Audit	Audit authorization
Accounts	Account administration
Provisioning	Provisioning authorization + telemetry
Documents	Document read authorization
Frontend session	Session-authenticated UX
CSRF	Request-origin/token protection
Security telemetry	Authorization/security failure recording
6. Completed Authorization Work

The implemented security-hardening tasks include:

AUTH-5A: Requisition authorization
AUTH-5B: Requisition tenant/resource boundaries
AUTH-5C: Seed/bootstrap hardening
AUTH-5D: Audit authorization
AUTH-5F: Ingest mutation authorization
AUTH-5G: Graph authorization
AUTH-5H: Inventory read authorization
AUTH-5I: Inventory mutation authorization
AUTH-5J.1: Account administration
AUTH-5J.2: Match authorization boundary
AUTH-5J.3: Provisioning telemetry and production documentation gating
AUTH-5K: Inventory/document read hardening
AUTH-006 Phase 2: Frontend session-authentication UX
7. Session Security

The application session is responsible for maintaining authenticated application state after identity verification.

Security expectations:

Server-side authentication checks remain authoritative.
Protected API operations require an authenticated session.
Frontend state must not be treated as proof of authorization.
Sensitive operations must be protected by backend authorization.
Users should not be unnecessarily forced to re-authenticate during an active valid session.
8. CSRF Protection

State-changing browser requests require CSRF protection.

The security layer validates:

Request origin where applicable.
CSRF token where required.

Denied CSRF requests must preserve the existing HTTP/security semantics while producing security telemetry.

9. Security Telemetry

Authorization/security failures are recorded using the existing security-event mechanism.

Canonical event:

AUTHORIZATION_FAILURE

Telemetry requirements:

success = false
Server-side actor identity where available
Existing reason/action conventions
No passwords, tokens, session secrets, or sensitive credentials
Consistent event generation across protected authorization boundaries

Current telemetry hardening covers missing instrumentation around:

CSRF origin denial
CSRF token denial
Missing CPSE context
Cross-CPSE requisition operations
Self-approval / segregation-of-duties violation

Existing require_permission and require_any_permission authorization-failure telemetry remains the canonical implementation and should not be duplicated.

10. Segregation of Duties

Certain workflow operations require separation between requester and approver.

Example:

Requester ─────X────→ Approve own requisition

A requester must not approve their own requisition where the workflow requires independent approval.

This denial must be enforced server-side and recorded as an authorization failure.

11. Security Boundaries

The security implementation must preserve:

Authentication boundaries
RBAC
Permission checks
CPSE isolation
Resource ownership
CSRF semantics
Workflow-state rules
Audit integrity
Session security

Security telemetry must observe and record security decisions rather than alter the underlying authorization decision.

12. Audit Separation

Two concepts remain distinct:

SecurityEvent

Used for:

Authentication/security events
Authorization failures
Security monitoring
Operational security telemetry

SovereignAuditLedger

Used for:

Business/sovereign audit trail
Material/workflow/audit history

Authentication and authorization telemetry must not be unnecessarily duplicated into the SovereignAuditLedger.

13. Current Architecture Constraints

The following are deliberately not part of the current implementation scope:

New identity provider
Google authentication
External organizational credential integration — target direction selected (`10_DECISIONS.md` D-CRED-1), exact protocol/provider an open architecture decision, not implemented
OIDC/SSO implementation
JWT architecture replacement
Bearer-token or localStorage authentication
New RBAC model
New permission system
New database schema solely for telemetry
SovereignAuditLedger redesign
Cross-CPSE audit-grant lifecycle redesign
Frontend authorization as a replacement for backend authorization
14. Verification Standard

Every security implementation must pass four gates:

Gate 1 — Code correctness

Authorization is enforced at the correct backend boundary.

Gate 2 — Security invariant

A user cannot bypass authorization through manipulated resource IDs, CPSE IDs, or frontend state.

Gate 3 — Telemetry

Relevant security denials generate the canonical security event.

Gate 4 — Regression

Existing authentication, RBAC, CPSE isolation, CSRF, and workflow behavior remains unchanged.

15. Definition of Done

My authentication/security work is considered complete when:

The session-cookie authentication architecture is respected; the credential-authority direction (External Organizational Authority / Federation, `10_DECISIONS.md` D-CRED-1) is honored, and its exact protocol/provider remains an explicit open architecture decision that is not invented.
No external identity provider is assumed or introduced without an explicit approved task.
Protected APIs enforce authentication.
Permissions are enforced server-side.
CPSE/resource boundaries are enforced.
Sensitive mutations are authorization-protected.
CSRF protections remain intact.
Segregation-of-duties rules are enforced.
Authorization failures generate canonical security telemetry.
No secrets or credentials are exposed through telemetry.
Existing security behavior is not weakened.
Focused security tests pass where the database/test environment is available.
Database/environment limitations are explicitly reported rather than bypassed or faked.
16. Primary Deliverable

A production-oriented authentication and authorization security layer for Samanvay-AI that pairs organizational username/password session authentication with application-level session management, RBAC, permission enforcement, CPSE isolation, workflow authorization, CSRF protection, and security telemetry.