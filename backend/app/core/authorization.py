"""
AUTH-007 centralized authorization policy provider.

Canonical contract (AUTH-007 Sections 5, 16, 17):

    evaluate(request: AuthorizationRequest) -> AuthorizationDecision

The provider evaluates RBAC permission, CPSE/tenant boundary, resource policy,
workflow state, and audit scope. It fails closed, returns structured reason
codes, and may return structured query constraints so the repository layer can
translate them into parameterized SQLAlchemy filters.

The provider intentionally does NOT:
  * generate raw SQL
  * execute database queries
  * perform business mutations
  * grant permissions or create audit grants
  * provide a universal SUPER_ADMIN bypass

A decision is specific to the requested action/resource/context and must not be
reused blindly for a different action or resource.

Implementation note (documented, not an architecture change): AUTH-007 Section 5
permits a decision to carry structured constraints for collection/single-resource
use. When no server resource context is supplied, this provider returns the RBAC
decision plus a ``cpseId`` constraint that the repository layer MUST apply. When a
server resource context is supplied, CPSE/ownership/audit-scope are enforced here.
"""

from dataclasses import dataclass, field
from typing import FrozenSet, Optional, Tuple

from backend.app.core import permissions as perm

# ── Decisions ──────────────────────────────────────────────────────────
ALLOW = "ALLOW"
DENY = "DENY"

# Allow reason codes
ALLOW_RBAC_AND_RESOURCE_POLICY_VALID = "RBAC_AND_RESOURCE_POLICY_VALID"
ALLOW_RESOURCE_POLICY = "RESOURCE_POLICY_VALID"

# Deny reason codes (all fail-closed)
DENY_UNKNOWN_PERMISSION = "UNKNOWN_PERMISSION"
DENY_UNKNOWN_ROLE = "UNKNOWN_ROLE"
DENY_UNAUTHENTICATED = "UNAUTHENTICATED"
DENY_ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"
DENY_ACCOUNT_UNAPPROVED = "ACCOUNT_UNAPPROVED"
DENY_PERMISSION_NOT_GRANTED = "PERMISSION_NOT_GRANTED"
DENY_MISSING_RESOURCE_ATTRIBUTES = "MISSING_RESOURCE_ATTRIBUTES"
DENY_TENANT_MISMATCH = "TENANT_MISMATCH"
DENY_RESOURCE_OWNERSHIP = "RESOURCE_OWNERSHIP"
DENY_INVALID_WORKFLOW_STATE = "INVALID_WORKFLOW_STATE"
DENY_INVALID_AUDIT_GRANT = "INVALID_AUDIT_GRANT"


@dataclass(frozen=True)
class AuditAuthorizationGrant:
    """Server-validated case-specific cross-CPSE audit authorization grant.

    Never constructed from raw client input. Read-only, audit-purpose-only.
    """

    grant_id: str
    auditor_user_id: Optional[int]
    authorized_cpse_ids: FrozenSet[str]
    purpose: Optional[str] = None
    revoked: bool = False


@dataclass(frozen=True)
class Subject:
    """Server-derived principal. Never populated from client-controlled fields."""

    user_id: Optional[int]
    role: Optional[str]
    cpse_id: Optional[str] = None
    depot_id: Optional[str] = None
    is_active: bool = False
    is_approved: bool = False


@dataclass(frozen=True)
class Action:
    permission: str


@dataclass(frozen=True)
class Resource:
    """Server-resolved resource attributes (authoritative server-side values)."""

    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_cpse_id: Optional[str] = None
    resource_workflow_state: Optional[str] = None
    owner_id: Optional[str] = None


@dataclass(frozen=True)
class AuthorizationContext:
    audit_authorization_grant: Optional[AuditAuthorizationGrant] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass(frozen=True)
class Constraint:
    field: str
    operator: str
    value: object


@dataclass(frozen=True)
class AuthorizationRequest:
    subject: Subject
    action: Action
    resource: Resource = field(default_factory=Resource)
    context: AuthorizationContext = field(default_factory=AuthorizationContext)


@dataclass(frozen=True)
class AuthorizationDecision:
    decision: str
    reason_code: str
    constraints: Tuple[Constraint, ...] = ()


def _deny(reason_code: str) -> AuthorizationDecision:
    return AuthorizationDecision(DENY, reason_code)


def _allow(reason_code: str = ALLOW_RBAC_AND_RESOURCE_POLICY_VALID,
           constraints: Tuple[Constraint, ...] = ()) -> AuthorizationDecision:
    return AuthorizationDecision(ALLOW, reason_code, constraints)


def evaluate(request: AuthorizationRequest) -> AuthorizationDecision:
    """Evaluate one authorization request. Fails closed on any uncertainty."""
    if request is None or request.subject is None or request.action is None:
        return _deny(DENY_UNAUTHENTICATED)

    subject = request.subject
    permission = request.action.permission

    # ── Subject validity ──────────────────────────────────────────────
    if not permission or permission not in perm.ALL_PERMISSIONS:
        return _deny(DENY_UNKNOWN_PERMISSION)
    if not subject.role or subject.role not in perm.VALID_ROLES:
        return _deny(DENY_UNKNOWN_ROLE)
    if subject.user_id is None:
        return _deny(DENY_UNAUTHENTICATED)
    if not subject.is_active:
        return _deny(DENY_ACCOUNT_INACTIVE)
    if not subject.is_approved:
        return _deny(DENY_ACCOUNT_UNAPPROVED)

    # ── Account/system administration: RBAC only ──────────────────────
    if permission in perm.ACCOUNT_SCOPED_PERMISSIONS:
        if perm.role_has_permission(subject.role, permission):
            return _allow(ALLOW_RBAC_AND_RESOURCE_POLICY_VALID)
        return _deny(DENY_PERMISSION_NOT_GRANTED)

    # ── Resource-policy governed reads ────────────────────────────────
    if permission in perm.RESOURCE_POLICY_PERMISSIONS:
        # RBAC-first: the caller's role must actually hold the permission before
        # the resource-policy evaluator may issue an unconditional ALLOW.
        if not perm.role_has_permission(subject.role, permission):
            return _deny(DENY_PERMISSION_NOT_GRANTED)
        return _evaluate_resource_policy(request)

    # ── Audit-scope permissions ───────────────────────────────────────
    if permission in perm.AUDIT_SCOPED_PERMISSIONS:
        return _evaluate_audit_scope(request)

    # ── Tenant-scoped operational permissions ─────────────────────────
    if not perm.role_has_permission(subject.role, permission):
        return _deny(DENY_PERMISSION_NOT_GRANTED)
    return _evaluate_tenant_scope(request)


def _evaluate_tenant_scope(request: AuthorizationRequest) -> AuthorizationDecision:
    subject = request.subject
    resource = request.resource

    # Resource context supplied: enforce CPSE boundary and ownership.
    if resource.resource_type:
        if resource.resource_cpse_id is None:
            return _deny(DENY_MISSING_RESOURCE_ATTRIBUTES)
        if not subject.cpse_id or subject.cpse_id != resource.resource_cpse_id:
            return _deny(DENY_TENANT_MISMATCH)

        # SITE_ENGINEER requisition visibility is own-requisitions-only.
        if (
            resource.resource_type == "Requisition"
            and subject.role == perm.SITE_ENGINEER
            and resource.owner_id is not None
            and str(resource.owner_id) != str(subject.user_id)
        ):
            return _deny(DENY_RESOURCE_OWNERSHIP)

        return _allow(
            ALLOW_RBAC_AND_RESOURCE_POLICY_VALID,
            (Constraint("cpseId", "EQ", subject.cpse_id),),
        )

    # No resource context: return constraints for the repository layer to apply.
    if not subject.cpse_id:
        return _deny(DENY_MISSING_RESOURCE_ATTRIBUTES)
    return _allow(
        ALLOW_RBAC_AND_RESOURCE_POLICY_VALID,
        (Constraint("cpseId", "EQ", subject.cpse_id),),
    )


def _evaluate_audit_scope(request: AuthorizationRequest) -> AuthorizationDecision:
    subject = request.subject
    resource = request.resource

    if not perm.role_has_permission(subject.role, request.action.permission):
        return _deny(DENY_PERMISSION_NOT_GRANTED)

    if resource.resource_type:
        if resource.resource_cpse_id is None:
            return _deny(DENY_MISSING_RESOURCE_ATTRIBUTES)
        if resource.resource_cpse_id != subject.cpse_id:
            grant = request.context.audit_authorization_grant
            if (
                grant is None
                or grant.revoked
                or resource.resource_cpse_id not in grant.authorized_cpse_ids
            ):
                return _deny(DENY_INVALID_AUDIT_GRANT)
        return _allow(
            ALLOW_RBAC_AND_RESOURCE_POLICY_VALID,
            (Constraint("cpseId", "EQ", resource.resource_cpse_id),),
        )

    if not subject.cpse_id:
        return _deny(DENY_MISSING_RESOURCE_ATTRIBUTES)
    return _allow(
        ALLOW_RBAC_AND_RESOURCE_POLICY_VALID,
        (Constraint("cpseId", "EQ", subject.cpse_id),),
    )


def _evaluate_resource_policy(request: AuthorizationRequest) -> AuthorizationDecision:
    subject = request.subject
    permission = request.action.permission
    resource = request.resource

    if permission in (perm.MATCH_READ, perm.GRAPH_READ):
        # Cross-CPSE canonical/material information is permitted; operational
        # data must remain scoped, so an operational-scope constraint is returned.
        constraints = (
            (Constraint("operationalScope", "EQ", subject.cpse_id),)
            if subject.cpse_id
            else ()
        )
        return _allow(ALLOW_RESOURCE_POLICY, constraints)

    # DOCUMENT_READ: own-CPSE by default; cross-CPSE only with a valid audit grant.
    if not subject.cpse_id:
        return _deny(DENY_MISSING_RESOURCE_ATTRIBUTES)
    if resource.resource_type:
        if resource.resource_cpse_id is None:
            return _deny(DENY_MISSING_RESOURCE_ATTRIBUTES)
        if resource.resource_cpse_id != subject.cpse_id:
            grant = request.context.audit_authorization_grant
            if (
                grant is None
                or grant.revoked
                or resource.resource_cpse_id not in grant.authorized_cpse_ids
            ):
                return _deny(DENY_INVALID_AUDIT_GRANT)
        return _allow(
            ALLOW_RBAC_AND_RESOURCE_POLICY_VALID,
            (Constraint("cpseId", "EQ", resource.resource_cpse_id),),
        )
    return _allow(
        ALLOW_RESOURCE_POLICY, (Constraint("cpseId", "EQ", subject.cpse_id),)
    )


def build_subject(user) -> Subject:
    """Build a server-derived Subject from an authenticated User ORM record."""
    return Subject(
        user_id=getattr(user, "id", None),
        role=getattr(user, "role", None),
        cpse_id=getattr(user, "cpse", None),
        depot_id=getattr(user, "depot_id", None),
        is_active=bool(getattr(user, "is_active", False)),
        is_approved=bool(getattr(user, "is_approved", False)),
    )