# AUTH-007 — Permission & Authorization Contract

**Project:** Samanvay-AI
**Branch:** `auth-development-shourya`
**Status:** Frozen permission and authorization contract; concrete implementation contract for AUTH-006
**Depends on:** AUTH-003, AUTH-004, AUTH-005, AUTH-006
**Scope:** Canonical permission vocabulary, role-to-permission mapping, authorization evaluation contract, resource-policy boundaries, CPSE isolation rules, workflow authorization rules, audit-scope rules, and the policy-provider interface

This document defines the concrete permission and authorization contract used by the Samanvay-AI authentication/authorization implementation. It is an implementation contract. It must not introduce new architectural decisions that contradict AUTH-002 through AUTH-006.

---

## 1. Purpose

Define the canonical permission vocabulary, role-to-permission mapping, authorization evaluation contract, resource-policy boundaries, CPSE isolation rules, workflow authorization rules, audit-scope rules, and policy-provider interface for the Samanvay-AI authentication/authorization implementation.

This document is an implementation contract.

It must not introduce new architectural decisions that contradict AUTH-002 through AUTH-006.

---

## 2. Core Permission Vocabulary

Use exactly these canonical permission identifiers:

```text
ACCOUNT_PROVISION
ACCOUNT_APPROVE
ACCOUNT_REJECT
ACCOUNT_DISABLE

REQUISITION_CREATE
REQUISITION_READ
REQUISITION_APPROVE_STANDARD
REQUISITION_APPROVE_TECHNICAL
REQUISITION_REJECT
REQUISITION_GATEPASS
REQUISITION_DISPATCH
REQUISITION_RECEIVE
REQUISITION_AUDIT

INVENTORY_READ
INVENTORY_CREATE
INVENTORY_UPDATE
INVENTORY_STATUS_CHANGE
INVENTORY_VERIFY
INVENTORY_SURPLUS_IDENTIFY
INVENTORY_DISPATCH

INGEST_CATALOG
INGEST_DOCUMENT

AUDIT_READ
AUDIT_FINDING_CREATE
AUDIT_FEEDBACK_CREATE
AUDIT_EXPORT
AUDIT_FINDING_MANAGE

MATCH_READ
GRAPH_READ
DOCUMENT_READ

SYSTEM_ADMIN
```

Important:

* `AUDIT_FINDING_MANAGE` is intentionally unassigned.
* Do NOT assign it to VIGILANCE_AUDITOR.
* Do NOT assign it to SUPER_ADMIN.
* Do NOT invent a finding-closure authority.
* `AUDITOR` is not a valid target role.
* The valid roles remain:

  * `SITE_ENGINEER`
  * `MATERIALS_MANAGER`
  * `TECHNICAL_AUTHORITY`
  * `CISF_SECURITY`
  * `VIGILANCE_AUDITOR`
  * `SUPER_ADMIN`

---

## 3. Role-to-Permission Mapping

### SITE_ENGINEER

```text
REQUISITION_CREATE
REQUISITION_READ
REQUISITION_RECEIVE
```

### MATERIALS_MANAGER

```text
REQUISITION_READ
REQUISITION_APPROVE_STANDARD
REQUISITION_REJECT
REQUISITION_DISPATCH

INVENTORY_READ
INVENTORY_CREATE
INVENTORY_UPDATE
INVENTORY_STATUS_CHANGE
INVENTORY_VERIFY
INVENTORY_SURPLUS_IDENTIFY
INVENTORY_DISPATCH

INGEST_CATALOG
INGEST_DOCUMENT
```

### TECHNICAL_AUTHORITY

```text
REQUISITION_READ
REQUISITION_APPROVE_TECHNICAL
REQUISITION_REJECT
```

### CISF_SECURITY

```text
REQUISITION_READ
REQUISITION_GATEPASS
```

### VIGILANCE_AUDITOR

```text
REQUISITION_AUDIT

AUDIT_READ
AUDIT_FINDING_CREATE
AUDIT_FEEDBACK_CREATE
AUDIT_EXPORT

DOCUMENT_READ
```

VIGILANCE_AUDITOR may also receive audit-authorized evidentiary reads according to the audit resource policy.

These are read-only audit-scope accesses and must never become operational mutation authority.

### SUPER_ADMIN

```text
ACCOUNT_PROVISION
ACCOUNT_APPROVE
ACCOUNT_REJECT
ACCOUNT_DISABLE
SYSTEM_ADMIN
```

SUPER_ADMIN does NOT automatically receive operational permissions.

SUPER_ADMIN does NOT automatically receive:

* requisition workflow authority
* inventory authority
* audit authority
* cross-CPSE operational access
* resource ownership bypass
* tenant-isolation bypass
* security-control bypass

---

## 4. Permissions Intentionally Governed by Resource Policy

The following permissions are not assigned universally to a role merely because the identifier exists:

```text
MATCH_READ
GRAPH_READ
DOCUMENT_READ
```

Their effective scope depends on resource classification and the policies defined below.

Do not turn these into unrestricted global permissions.

---

## 5. Authorization Evaluation Contract

The canonical authorization operation is:

```text
evaluate(request: AuthorizationRequest) -> AuthorizationDecision
```

The request contains:

```text
subject
action
resource
context
```

Example:

```json
{
  "subject": {
    "userId": "usr_9812345",
    "role": "SITE_ENGINEER",
    "cpseId": "CPSE_A_CORP"
  },
  "action": {
    "permission": "REQUISITION_READ"
  },
  "resource": {
    "resourceType": "Requisition",
    "resourceId": "req_554102",
    "resourceCpseId": "CPSE_A_CORP",
    "resourceWorkflowState": "PENDING",
    "ownerId": "usr_9812345"
  },
  "context": {
    "auditAuthorizationGrant": null,
    "requestId": "server-generated-request-id",
    "ipAddress": "server-observed",
    "timestamp": "server-generated"
  }
}
```

Resource attributes are authoritative server-side values.

Client-supplied resource attributes MUST NOT establish authorization.

The authorization decision is:

```json
{
  "decision": "ALLOW",
  "reasonCode": "RBAC_AND_RESOURCE_POLICY_VALID",
  "constraints": {
    "cpseId": {
      "operator": "EQ",
      "value": "CPSE_A_CORP"
    },
    "ownerId": {
      "operator": "EQ",
      "value": "usr_9812345"
    }
  }
}
```

A decision may contain structured query constraints.

For single-resource mutation, constraints may be omitted when the resource has already been resolved and validated.

For collection queries, authorization constraints must be translated into query-level filtering.

---

## 6. Fail-Closed Rules

Authorization MUST fail closed.

The decision must be `DENY` when any authorization-critical input is:

* unknown
* missing
* malformed
* invalid
* stale
* inconsistent
* outside the subject's CPSE
* outside the subject's resource scope
* associated with an invalid audit grant
* associated with an invalid workflow state
* associated with an unknown permission
* associated with an unknown role

Do not convert authorization uncertainty into anonymous access.

Do not silently downgrade invalid authentication into an unauthenticated request.

---

## 7. Policy Composition

Authorization is the composition of:

```text
Authentication
AND
RBAC permission
AND
CPSE/tenant policy
AND
resource policy
AND
workflow policy where applicable
AND
audit-scope policy where applicable
```

An RBAC permission alone does not automatically authorize access to every resource.

A valid audit permission does not automatically authorize operational mutation.

An authenticated user does not automatically receive cross-CPSE access.

---

## 8. Policy Evaluation Architecture

The target architecture is:

```text
Router
  ↓
Authentication dependency
  ↓
Authorization Policy
  ↓
Structured Authorization Decision
  ↓
Service
  ↓
Repository / Database
```

The policy layer must be reusable and centralized.

Do NOT implement authorization as scattered route-only role comparisons.

The policy engine must NOT:

* generate raw SQL
* execute database queries directly
* perform business mutations
* grant permissions
* create audit grants
* bypass CPSE isolation
* bypass resource ownership
* bypass workflow state
* grant SUPER_ADMIN an implicit universal bypass

Repository code translates structured authorization constraints into parameterized SQLAlchemy queries.

---

## 9. Requisition Resource Policy

Authorization evaluation order:

```text
Authentication
→ Permission
→ CPSE boundary
→ Requisition ownership/visibility
→ Workflow state
→ Classification where applicable
→ Audit authorization where applicable
```

Ordinary operational access requires:

```text
subject.cpseId == requisition.cpseId
```

A mismatch must result in:

```text
TENANT_MISMATCH
```

SUPER_ADMIN does not bypass this rule.

### SITE_ENGINEER

Can:

* create requisitions according to `REQUISITION_CREATE`
* read own requisitions within own CPSE
* receive/deliver according to `REQUISITION_RECEIVE`

Receive requires:

* same CPSE
* authorized recipient/site relationship
* valid delivery workflow state

### MATERIALS_MANAGER

Can:

* read requisitions in own CPSE
* approve Standard/Low Value requisitions when awaiting the appropriate approval
* reject according to valid workflow
* dispatch according to valid workflow

### TECHNICAL_AUTHORITY

Can:

* read relevant Technical/High Value requisitions within own CPSE
* approve only Technical/High Value requisitions awaiting technical approval
* reject according to valid workflow

After approval/rejection, TECHNICAL_AUTHORITY has continued read-only visibility where required by the frozen architecture, but does not gain further modification authority merely from having handled the requisition.

### CISF_SECURITY

Can:

* read requisitions needed for gate-pass action
* issue gate pass only when the requisition is in the valid gate-pass-required state

Access ends after the gate-pass action unless another explicit permission/policy grants access.

### VIGILANCE_AUDITOR

Does not receive ordinary operational requisition authority.

Requisition access is audit-scope access only.

Cross-CPSE requisition access requires a valid server-side audit authorization grant.

Audit access is read-only.

### SUPER_ADMIN

Does not receive implicit requisition workflow permissions.

---

## 10. Requisition Visibility

The frozen visibility rules are:

```text
SITE_ENGINEER
→ own requisitions only

MATERIALS_MANAGER
→ all requisitions in own CPSE

TECHNICAL_AUTHORITY
→ relevant Technical/High Value requisitions in own CPSE

CISF_SECURITY
→ requisitions while gate-pass action is required

VIGILANCE_AUDITOR
→ only when required for explicitly authorized audit

SUPER_ADMIN
→ no implicit workflow visibility
```

Collection queries must be constrained at query level.

Do NOT fetch all records and filter them afterward in application memory.

---

## 11. Requisition Classification

Classification is deterministic and server-controlled.

The requester cannot choose a category merely to influence the approver.

The exact classification thresholds/rules remain a separate business-rule specification.

Do NOT invent numerical thresholds in this document.

The authorization policy must consume the classification result rather than allowing the client to select it.

---

## 12. Inventory Resource Policy

### MATERIALS_MANAGER

Within the user's own CPSE:

* `INVENTORY_READ`
* `INVENTORY_CREATE`
* `INVENTORY_UPDATE`
* `INVENTORY_STATUS_CHANGE`
* `INVENTORY_VERIFY`
* `INVENTORY_SURPLUS_IDENTIFY`
* `INVENTORY_DISPATCH`

### SITE_ENGINEER

No general inventory permission.

Material receipt occurs through the authorized requisition workflow.

### VIGILANCE_AUDITOR

Read-only inventory evidence when required for an authorized audit.

Cross-CPSE inventory access requires a valid server-side audit grant.

### TECHNICAL_AUTHORITY

No general inventory read permission.

### CISF_SECURITY

No general inventory read permission.

### SUPER_ADMIN

No implicit inventory visibility or workflow authority.

Inventory access requires:

```text
subject.cpseId == inventory.cpseId
```

Client-provided CPSE fields cannot establish authorization.

Status changes additionally require:

* correct role/permission
* same CPSE
* valid current state
* valid state transition

Surplus identification is NOT disposal authorization.

Actual disposal/write-off authority remains outside Samanvay-AI.

Inventory dispatch requires:

* MATERIALS_MANAGER authority
* same CPSE
* operational scope
* valid workflow/state

---

## 13. Audit Resource Policy

RBAC establishes audit capability.

Audit scope establishes which evidence the auditor may access.

### VIGILANCE_AUDITOR

Can:

* view audit records
* create audit findings/observations
* add audit feedback/comments
* export audit history/evidence
* read authorized supporting evidence

This authority is audit-domain only.

It does NOT grant:

* requisition modification
* inventory modification
* dispatch
* delivery
* gate-pass authority
* system administration
* operational workflow authority

### Cross-CPSE audit access

Cross-CPSE access requires:

```text
VIGILANCE_AUDITOR
AND
appropriate audit permission
AND
valid server-side audit authorization grant
AND
resource within grant scope
```

The grant is server validated.

It is NOT a raw client-provided authorization token.

A grant contains conceptually:

```text
audit/case ID
auditor
authorized CPSE(s)
resource/domain scope
purpose
issue time
expiry
revocation state
```

The grant may expand read-only evidence scope.

It must NEVER grant:

* operational mutation
* approval
* rejection
* dispatch
* gate-pass
* system administration
* tenant bypass outside the grant
* unrestricted access to unrelated resources

The audit grant cannot grant `AUDIT_FINDING_MANAGE`.

`AUDIT_FINDING_MANAGE` remains intentionally unassigned.

The exact finding-closure authority remains an unresolved business/organizational decision.

---

## 14. Documents, Matching, and Graph Policy

### MATCH_READ

Cross-CPSE canonical/material-equivalence information is allowed.

It must NOT expose unrelated operational information from another CPSE, including:

* stock
* inventory
* depots
* requisitions
* logistics
* operational state

### GRAPH_READ

Cross-CPSE canonical/material relationships are allowed.

Operational graph information remains CPSE-isolated, including:

* inventory/stock
* depots
* logistics routes
* requisitions

### DOCUMENT_READ

Default:

```text
own-CPSE documents only
```

VIGILANCE_AUDITOR may access cross-CPSE documents only when required by an explicit valid audit authorization.

Information classification determines scope.

Cross-CPSE canonical information does NOT implicitly grant cross-CPSE operational access.

No read permission automatically grants mutation authority.

---

## 15. CPSE/Tenant Isolation

CPSE is a real tenant boundary.

For ordinary operational access:

```text
subject.cpseId == resource.cpseId
```

Client-controlled fields MUST NOT establish tenant authorization.

In particular:

* `X-CPSE-ID` must never establish authorization.
* Client-selected CPSE values must never establish authorization.
* Client-selected role values must never establish authorization.
* Client-selected depot values must never establish authorization.

The server derives the authenticated user's identity and CPSE from the authenticated session/account.

Cross-CPSE operational access is prohibited by default.

SUPER_ADMIN is NOT an exception.

The only explicitly frozen cross-CPSE information classes are:

* canonical/material-equivalence information through `MATCH_READ`
* canonical/material relationships through `GRAPH_READ`
* explicitly authorized cross-CPSE audit evidence through a valid audit grant

---

## 16. Policy Provider Interface

The implementation must expose a canonical provider interface conceptually equivalent to:

```text
evaluate(request: AuthorizationRequest) -> AuthorizationDecision
```

The request contains:

```text
subject
action
resource
context
```

The decision contains:

```text
decision: ALLOW | DENY
reasonCode
constraints: optional structured constraints
```

The provider must:

* evaluate the requested action against the subject
* evaluate role/permission
* evaluate CPSE boundary
* evaluate resource policy
* evaluate workflow state when relevant
* evaluate audit scope when relevant
* fail closed
* return structured reason codes
* return structured query constraints when required

The provider must NOT:

* generate raw SQL
* execute business mutations
* modify resources
* create permissions
* create audit grants
* silently broaden scope
* provide a universal SUPER_ADMIN bypass

The decision is specific to the requested action/resource/context.

A decision must NOT be blindly reused for a different action or resource.

---

## 17. Structured Authorization Constraints

Collection-level authorization must produce structured constraints where necessary.

Example:

```json
{
  "constraints": {
    "cpseId": {
      "operator": "EQ",
      "value": "CPSE_A_CORP"
    },
    "ownerId": {
      "operator": "EQ",
      "value": "usr_9812345"
    }
  }
}
```

The repository/data-access layer is responsible for translating these constraints into parameterized SQLAlchemy queries.

The authorization provider must never construct raw SQL.

This prevents authorization from becoming coupled to database implementation details.

---

## 18. Security Invariants

Record these as explicit invariants:

1. Authentication is separate from authorization.
2. Authentication does not imply authorization.
3. Client-controlled identity fields cannot establish authorization.
4. Client-controlled CPSE fields cannot establish tenant authority.
5. SUPER_ADMIN has no universal authorization bypass.
6. Cross-CPSE operational access is denied by default.
7. Audit grants can expand only explicitly authorized read-only evidence scope.
8. Audit grants cannot grant operational mutation or system administration.
9. Unknown or missing authorization data results in DENY.
10. Collection authorization must be enforced at query level.
11. Authorization policy must be centralized and reusable.
12. The policy provider must not execute raw SQL.
13. The policy provider must not perform business mutations.
14. `AUDITOR` is not a valid target role.
15. `AUDIT_FINDING_MANAGE` remains intentionally unassigned.
16. Requisition classification is server-controlled and deterministic.
17. Surplus identification does not equal disposal authority.
18. Cross-CPSE canonical/material information does not imply cross-CPSE operational access.

---

## 19. Relationship to AUTH-003 through AUTH-006

* AUTH-003 defines the target authentication/authorization architecture.
* AUTH-004 defines the threat model and security threats.
* AUTH-005 defines the database/session design.
* AUTH-006 defines the implementation design.
* AUTH-007 defines the concrete permission vocabulary and authorization policy contract used by implementation.

AUTH-007 must not reopen or contradict frozen decisions from AUTH-003 through AUTH-006.

---

## 20. Intentionally Unresolved Decisions

Explicitly preserve these as unresolved:

1. Exact requisition classification thresholds/rules.
2. Exact authority responsible for finding closure / `AUDIT_FINDING_MANAGE`.
3. Exact representation/lifecycle implementation of cross-CPSE audit authorization grants.
4. Session expiry, idle timeout, concurrency, and retention product/deployment values.
5. Rate-limit provider and exact production thresholds.
6. Production browser origin.
7. Migration framework/tool selection.

These are not permission to invent architecture during implementation.

---

## 21. Acceptance Criteria

The document is complete only if:

* all canonical permissions are listed exactly
* all six valid roles are listed
* role-to-permission mapping is explicit
* `AUDIT_FINDING_MANAGE` remains unassigned
* `AUDITOR` is explicitly excluded
* authorization request/decision contract is defined
* fail-closed behavior is defined
* structured constraints are defined
* policy composition is defined
* requisition authorization is defined
* inventory authorization is defined
* audit authorization is defined
* cross-CPSE audit scope is defined
* matching/graph/document scope is defined
* CPSE isolation is defined
* SUPER_ADMIN bypass prohibition is explicit
* policy provider boundaries are explicit
* raw SQL/business mutation restrictions are explicit
* unresolved business/deployment decisions are clearly separated from frozen authorization policy
* no implementation code is included

---

## Revision Note

AUTH-007 permission and authorization contract documented from the frozen authentication architecture decisions. Documentation only; no source code, database schema, migrations, dependencies, or runtime behavior changed.
