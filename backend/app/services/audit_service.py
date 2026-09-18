import csv
import io
import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.tables import SovereignAuditLedger
from backend.app.core.security import (
    compute_audit_hash,
    verify_audit_chain as verify_chain_func,
    GENESIS_ROOT_64_HEX,
)


class AuditVerificationResponse:
    def __init__(self, is_valid: bool, invalid_entries: Optional[List[str]] = None, total_verified: int = 0):
        self.is_valid = is_valid
        self.invalid_entries = invalid_entries or []
        self.total_verified = total_verified


def create_audit_entry(db: Session, request: Dict[str, Any]) -> SovereignAuditLedger:
    """
    Creates an immutable cryptographic audit record anchored to the previous block's SHA-256 seal.
    """
    # 1. Fetch previous entry to get parent hash link
    prev_log = db.query(SovereignAuditLedger).order_by(SovereignAuditLedger.timestamp.desc()).first()
    prev_hash = prev_log.sha256_hash if prev_log else GENESIS_ROOT_64_HEX

    log_id = request.get("log_id") or f"LOG-{uuid.uuid4().hex[:8].upper()}"
    now_utc = datetime.now(timezone.utc)
    timestamp_str = now_utc.isoformat()

    actor_name = request.get("actor") or request.get("actor_name", "SYSTEM")
    actor_role = request.get("actor_role", "OPERATOR")
    action_category = request.get("action_category", "GENERAL")
    action_name = request.get("action") or request.get("action_name", "UNSPECIFIED")
    cpse = request.get("cpse", "IOCL")
    depot = request.get("depot", "DEFAULT_DEPOT")
    reference_id = request.get("reference_id", "REF-000")

    payload_data = request.get("payload", {})
    if isinstance(payload_data, dict):
        details_str = json.dumps(payload_data, sort_keys=True)
    else:
        details_str = str(payload_data)

    # 2. Compute SHA-256 seal
    current_hash = compute_audit_hash(
        prev_hash=prev_hash,
        log_id=log_id,
        timestamp=timestamp_str,
        actor=actor_name,
        action=action_name,
        reference_id=reference_id,
        details=details_str,
    )

    new_log = SovereignAuditLedger(
        log_id=log_id,
        timestamp=now_utc,
        action_category=action_category,
        action_name=action_name,
        actor_name=actor_name,
        actor_role=actor_role,
        cpse=cpse,
        depot=depot,
        reference_id=reference_id,
        details=details_str,
        prev_hash=prev_hash,
        sha256_hash=current_hash,
        is_verified=True,
    )

    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


def list_audit_entries(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    cpse: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns chronological audit entries with pagination and category filtering.
    """
    query = db.query(SovereignAuditLedger)
    if category and category != "ALL":
        query = query.filter(SovereignAuditLedger.action_category == category)
    if cpse and cpse != "ALL":
        query = query.filter(SovereignAuditLedger.cpse == cpse)

    total = query.count()
    logs = query.order_by(SovereignAuditLedger.timestamp.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "entries": [
            {
                "log_id": log.log_id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                "action_category": log.action_category,
                "action_name": log.action_name,
                "actor_name": log.actor_name,
                "actor_role": log.actor_role,
                "cpse": log.cpse,
                "depot": log.depot,
                "reference_id": log.reference_id,
                "details": log.details,
                "prev_hash": log.prev_hash,
                "sha256_hash": log.sha256_hash,
                "is_verified": log.is_verified,
            }
            for log in logs
        ],
    }


def get_audit_entry_by_id(db: Session, log_id: str) -> Optional[SovereignAuditLedger]:
    return db.query(SovereignAuditLedger).filter(SovereignAuditLedger.log_id == log_id).first()


def verify_chain(db: Session) -> AuditVerificationResponse:
    """
    Verifies the cryptographic SHA-256 seal continuity across all ledger entries.
    """
    logs = db.query(SovereignAuditLedger).order_by(SovereignAuditLedger.timestamp.asc()).all()
    if not logs:
        return AuditVerificationResponse(is_valid=True, total_verified=0)

    entries_for_verification = [
        {
            "log_id": log.log_id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "",
            "actor_name": log.actor_name,
            "action_name": log.action_name,
            "reference_id": log.reference_id,
            "details": log.details,
            "prev_hash": log.prev_hash,
            "sha256_hash": log.sha256_hash,
        }
        for log in logs
    ]

    is_valid, broken_idx = verify_chain_func(entries_for_verification)
    invalid_entries = []
    if not is_valid and broken_idx is not None:
        broken_log = logs[broken_idx]
        invalid_entries.append(
            f"Log {broken_log.log_id} at height #{broken_idx}: Hash mismatch or parent continuity break"
        )

    return AuditVerificationResponse(
        is_valid=is_valid,
        invalid_entries=invalid_entries,
        total_verified=len(logs),
    )


def export_csv(db: Session, filters: Dict[str, Any]) -> str:
    """
    Exports sovereign audit ledger records in RFC 4180 CSV format with UTF-8 BOM.
    """
    query = db.query(SovereignAuditLedger)
    if "category" in filters and filters["category"]:
        query = query.filter(SovereignAuditLedger.action_category == filters["category"])
    if "cpse" in filters and filters["cpse"]:
        query = query.filter(SovereignAuditLedger.cpse == filters["cpse"])

    logs = query.order_by(SovereignAuditLedger.timestamp.asc()).all()

    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM
    writer = csv.writer(output, dialect="excel")

    writer.writerow([
        "log_id",
        "timestamp_utc",
        "action_category",
        "action_name",
        "actor_name",
        "actor_role",
        "cpse",
        "depot",
        "reference_id",
        "details",
        "prev_hash",
        "sha256_hash",
    ])

    for log in logs:
        writer.writerow([
            log.log_id,
            log.timestamp.isoformat() if log.timestamp else "",
            log.action_category,
            log.action_name,
            log.actor_name,
            log.actor_role,
            log.cpse,
            log.depot,
            log.reference_id,
            log.details,
            log.prev_hash,
            log.sha256_hash,
        ])

    return output.getvalue()
