"""
AUTH-007 canonical permission vocabulary and role-to-permission mapping.

This module records the frozen AUTH-007 permission contract verbatim: the
canonical permission identifiers and the frozen role -> permission grants.

It defines *what* permissions exist and which roles hold them. It performs no
evaluation itself; authorization evaluation lives in
``backend/app/core/authorization.py``.

This module must not invent permissions or roles, and must not grant
``AUDIT_FINDING_MANAGE`` (it remains intentionally unassigned).
"""

from typing import FrozenSet, Mapping

# ── Canonical permission identifiers (AUTH-007 Section 2) ──────────────
ACCOUNT_PROVISION = "ACCOUNT_PROVISION"
ACCOUNT_APPROVE = "ACCOUNT_APPROVE"
ACCOUNT_REJECT = "ACCOUNT_REJECT"
ACCOUNT_DISABLE = "ACCOUNT_DISABLE"

REQUISITION_CREATE = "REQUISITION_CREATE"
REQUISITION_READ = "REQUISITION_READ"
REQUISITION_APPROVE_STANDARD = "REQUISITION_APPROVE_STANDARD"
REQUISITION_APPROVE_TECHNICAL = "REQUISITION_APPROVE_TECHNICAL"
REQUISITION_REJECT = "REQUISITION_REJECT"
REQUISITION_GATEPASS = "REQUISITION_GATEPASS"
REQUISITION_DISPATCH = "REQUISITION_DISPATCH"
REQUISITION_RECEIVE = "REQUISITION_RECEIVE"
REQUISITION_AUDIT = "REQUISITION_AUDIT"

INVENTORY_READ = "INVENTORY_READ"
INVENTORY_CREATE = "INVENTORY_CREATE"
INVENTORY_UPDATE = "INVENTORY_UPDATE"
INVENTORY_STATUS_CHANGE = "INVENTORY_STATUS_CHANGE"
INVENTORY_VERIFY = "INVENTORY_VERIFY"
INVENTORY_SURPLUS_IDENTIFY = "INVENTORY_SURPLUS_IDENTIFY"
INVENTORY_DISPATCH = "INVENTORY_DISPATCH"

INGEST_CATALOG = "INGEST_CATALOG"
INGEST_DOCUMENT = "INGEST_DOCUMENT"

AUDIT_READ = "AUDIT_READ"
AUDIT_FINDING_CREATE = "AUDIT_FINDING_CREATE"
AUDIT_FEEDBACK_CREATE = "AUDIT_FEEDBACK_CREATE"
AUDIT_EXPORT = "AUDIT_EXPORT"
AUDIT_FINDING_MANAGE = "AUDIT_FINDING_MANAGE"

MATCH_READ = "MATCH_READ"
GRAPH_READ = "GRAPH_READ"
DOCUMENT_READ = "DOCUMENT_READ"

SYSTEM_ADMIN = "SYSTEM_ADMIN"

ALL_PERMISSIONS: FrozenSet[str] = frozenset(
    {
        ACCOUNT_PROVISION,
        ACCOUNT_APPROVE,
        ACCOUNT_REJECT,
        ACCOUNT_DISABLE,
        REQUISITION_CREATE,
        REQUISITION_READ,
        REQUISITION_APPROVE_STANDARD,
        REQUISITION_APPROVE_TECHNICAL,
        REQUISITION_REJECT,
        REQUISITION_GATEPASS,
        REQUISITION_DISPATCH,
        REQUISITION_RECEIVE,
        REQUISITION_AUDIT,
        INVENTORY_READ,
        INVENTORY_CREATE,
        INVENTORY_UPDATE,
        INVENTORY_STATUS_CHANGE,
        INVENTORY_VERIFY,
        INVENTORY_SURPLUS_IDENTIFY,
        INVENTORY_DISPATCH,
        INGEST_CATALOG,
        INGEST_DOCUMENT,
        AUDIT_READ,
        AUDIT_FINDING_CREATE,
        AUDIT_FEEDBACK_CREATE,
        AUDIT_EXPORT,
        AUDIT_FINDING_MANAGE,
        MATCH_READ,
        GRAPH_READ,
        DOCUMENT_READ,
        SYSTEM_ADMIN,
    }
)

# ── Frozen valid roles (AUTH-007 Section 2) ────────────────────────────
SITE_ENGINEER = "SITE_ENGINEER"
MATERIALS_MANAGER = "MATERIALS_MANAGER"
TECHNICAL_AUTHORITY = "TECHNICAL_AUTHORITY"
CISF_SECURITY = "CISF_SECURITY"
VIGILANCE_AUDITOR = "VIGILANCE_AUDITOR"
SUPER_ADMIN = "SUPER_ADMIN"

VALID_ROLES: FrozenSet[str] = frozenset(
    {
        "SITE_ENGINEER",
        "MATERIALS_MANAGER",
        TECHNICAL_AUTHORITY,
        CISF_SECURITY,
        VIGILANCE_AUDITOR,
        SUPER_ADMIN,
    }
)
# ── Frozen role -> permission grants (AUTH-007 Section 3) ──────────────
#
# AUDIT_FINDING_MANAGE is intentionally absent from every grant set.
# MATCH_READ / GRAPH_READ are intentionally absent: they are governed by
# resource policy (AUTH-007 Section 4), not by a universal role grant.
ROLE_PERMISSIONS: Mapping[str, FrozenSet[str]] = {
    SITE_ENGINEER: frozenset(
        {
            REQUISITION_CREATE,
            REQUISITION_READ,
            REQUISITION_RECEIVE,
        }
    ),
    MATERIALS_MANAGER: frozenset(
        {
            REQUISITION_READ,
            REQUISITION_APPROVE_STANDARD,
            REQUISITION_REJECT,
            REQUISITION_DISPATCH,
            INVENTORY_READ,
            INVENTORY_CREATE,
            INVENTORY_UPDATE,
            INVENTORY_STATUS_CHANGE,
            INVENTORY_VERIFY,
            INVENTORY_SURPLUS_IDENTIFY,
            INVENTORY_DISPATCH,
            INGEST_CATALOG,
            INGEST_DOCUMENT,
        }
    ),
    TECHNICAL_AUTHORITY: frozenset(
        {
            REQUISITION_READ,
            REQUISITION_APPROVE_TECHNICAL,
            REQUISITION_REJECT,
        }
    ),
    CISF_SECURITY: frozenset(
        {
            REQUISITION_READ,
            REQUISITION_GATEPASS,
        }
    ),
    VIGILANCE_AUDITOR: frozenset(
        {
            REQUISITION_AUDIT,
            AUDIT_READ,
            AUDIT_FINDING_CREATE,
            AUDIT_FEEDBACK_CREATE,
            AUDIT_EXPORT,
            DOCUMENT_READ,
        }
    ),
    SUPER_ADMIN: frozenset(
        {
            ACCOUNT_PROVISION,
            ACCOUNT_APPROVE,
            ACCOUNT_REJECT,
            ACCOUNT_DISABLE,
            SYSTEM_ADMIN,
        }
    ),
}

# ── Permission classification (drives authorization evaluation) ────────
#
# Account/system permissions are RBAC-only and are not tenant-resource scoped.
ACCOUNT_SCOPED_PERMISSIONS: FrozenSet[str] = frozenset(
    {ACCOUNT_PROVISION, ACCOUNT_APPROVE, ACCOUNT_REJECT, ACCOUNT_DISABLE, SYSTEM_ADMIN}
)

# Operational permissions require an own-CPSE resource boundary.
TENANT_SCOPED_PERMISSIONS: FrozenSet[str] = frozenset(
    {
        REQUISITION_CREATE,
        REQUISITION_READ,
        REQUISITION_APPROVE_STANDARD,
        REQUISITION_APPROVE_TECHNICAL,
        REQUISITION_REJECT,
        REQUISITION_GATEPASS,
        REQUISITION_DISPATCH,
        REQUISITION_RECEIVE,
        INVENTORY_READ,
        INVENTORY_CREATE,
        INVENTORY_UPDATE,
        INVENTORY_STATUS_CHANGE,
        INVENTORY_VERIFY,
        INVENTORY_SURPLUS_IDENTIFY,
        INVENTORY_DISPATCH,
        INGEST_CATALOG,
        INGEST_DOCUMENT,
    }
)

# Audit permissions are audit-domain scoped. Cross-CPSE audit evidence requires
# a valid server-side audit authorization grant.
AUDIT_SCOPED_PERMISSIONS: FrozenSet[str] = frozenset(
    {
        REQUISITION_AUDIT,
        AUDIT_READ,
        AUDIT_FINDING_CREATE,
        AUDIT_FEEDBACK_CREATE,
        AUDIT_EXPORT,
        AUDIT_FINDING_MANAGE,
    }
)

# Resource-policy-governed read permissions (AUTH-007 Section 4).
RESOURCE_POLICY_PERMISSIONS: FrozenSet[str] = frozenset(
    {MATCH_READ, GRAPH_READ, DOCUMENT_READ}
)


def role_has_permission(role: str, permission: str) -> bool:
    """Return True only when the frozen mapping grants the permission to the role.

    SUPER_ADMIN receives no implicit bypass: it holds exactly its frozen grants.
    """
    return permission in ROLE_PERMISSIONS.get(role, frozenset())
