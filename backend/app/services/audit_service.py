import csv
import io
import hashlib
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.tables import AuditLog, IdempotencyKey
from backend.app.schemas.audit import AuditLogEntry
from backend.app.core.security import compute_audit_hash
import json
from datetime import datetime

class AuditVerificationResponse:
    def __init__(self, is_valid: bool, invalid_entries: List[str] = None):
        self.is_valid = is_valid
        self.invalid_entries = invalid_entries or []

def create_audit_entry(db: Session, request: Dict[str, Any]) -> AuditLog:
    # Fetch previous entry to get the previous hash
    prev_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = prev_log.current_hash if prev_log else "GENESIS"

    # Convert payload to string for hashing
    payload_str = json.dumps(request.get("payload", {}), sort_keys=True)
    
    # Compute new hash
    content_to_hash = f"{prev_hash}{request.get('action')}{request.get('actor')}{payload_str}"
    current_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()

    new_log = AuditLog(
        action=request.get("action"),
        actor=request.get("actor"),
        payload=request.get("payload", {}),
        previous_hash=prev_hash,
        current_hash=current_hash,
        timestamp=datetime.utcnow()
    )
    
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

def verify_chain(db: Session) -> AuditVerificationResponse:
    logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    invalid_entries = []
    
    expected_prev_hash = "GENESIS"
    for log in logs:
        if log.previous_hash != expected_prev_hash:
            invalid_entries.append(f"Log {log.id}: Invalid previous hash")
            continue
            
        payload_str = json.dumps(log.payload, sort_keys=True)
        content_to_hash = f"{log.previous_hash}{log.action}{log.actor}{payload_str}"
        computed_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()
        
        if computed_hash != log.current_hash:
            invalid_entries.append(f"Log {log.id}: Invalid current hash")
            
        expected_prev_hash = log.current_hash
        
    return AuditVerificationResponse(is_valid=len(invalid_entries) == 0, invalid_entries=invalid_entries)

def export_csv(db: Session, filters: Dict[str, Any]) -> str:
    query = db.query(AuditLog)
    # Apply basic filters if needed...
    logs = query.order_by(AuditLog.id.asc()).all()
    
    output = io.StringIO()
    # Write UTF-8 BOM
    output.write('\ufeff')
    writer = csv.writer(output, dialect='excel')
    
    writer.writerow(['id', 'timestamp', 'action', 'actor', 'payload', 'previous_hash', 'current_hash'])
    for log in logs:
        writer.writerow([
            log.id, 
            log.timestamp.isoformat() if log.timestamp else "", 
            log.action, 
            log.actor, 
            json.dumps(log.payload), 
            log.previous_hash, 
            log.current_hash
        ])
        
    return output.getvalue()
