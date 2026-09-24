"""
Samanvay-AI SHA-256 Digital Seal & Audit Chain Primitives.

Provides cryptographic hash computation for:
- Sovereign CVC/CAG audit ledger tamper-evident hash chain
- CISF gate pass digital seals
- API idempotency request body hashing
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import bcrypt
import jwt

from backend.app.core.config import settings


# Genesis root hash constant for the first audit ledger entry
GENESIS_ROOT_64_HEX = "0" * 64


def compute_sha256(data: str) -> str:
    """Compute SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_audit_hash(
    prev_hash: str,
    log_id: str,
    timestamp: str,
    actor: str,
    action: str,
    reference_id: str,
    details: str,
) -> str:
    """
    Compute the cryptographic chain hash for a sovereign audit ledger entry.

    Hash_i = SHA256(prev_hash_{i-1} || LogID || Timestamp || Actor || Action || RefID || Details)

    This creates a mathematically tamper-evident hash chain: retroactively
    deleting, altering, or re-ordering any historical row breaks all
    subsequent hash seals.
    """
    payload = f"{prev_hash}|{log_id}|{timestamp}|{actor}|{action}|{reference_id}|{details}"
    return compute_sha256(payload)


def compute_gate_pass_seal(
    gate_pass_no: str,
    vehicle_no: str,
    driver_id: str,
    sku_code: str,
    quantity: int,
    issuing_officer: str,
    timestamp: str,
) -> str:
    """
    Compute SHA-256 digital seal for a CISF Material Gate Pass.

    Seal = SHA256(gate_pass_no || vehicle_no || driver_id || sku_code || qty || officer || timestamp)
    """
    payload = (
        f"{gate_pass_no}|{vehicle_no}|{driver_id}|{sku_code}"
        f"|{quantity}|{issuing_officer}|{timestamp}"
    )
    return compute_sha256(payload)


def compute_request_hash(body: dict[str, Any]) -> str:
    """
    Compute a deterministic SHA-256 hash of a normalized request body
    for idempotency key verification.

    JSON keys are sorted to ensure deterministic serialization.
    """
    normalized = json.dumps(body, sort_keys=True, default=str)
    return compute_sha256(normalized)


def verify_audit_chain(entries: list[dict[str, Any]]) -> tuple[bool, int | None]:
    """
    Verify the integrity of the entire audit ledger hash chain.

    Returns:
        (is_valid, first_broken_index):
        - (True, None) if chain is fully intact
        - (False, index) if chain is broken at the given index
    """
    if not entries:
        return True, None

    for i, entry in enumerate(entries):
        if i == 0:
            expected_prev = GENESIS_ROOT_64_HEX
        else:
            expected_prev = entries[i - 1]["sha256_hash"]

        if entry["prev_hash"] != expected_prev:
            return False, i

        recomputed = compute_audit_hash(
            prev_hash=entry["prev_hash"],
            log_id=entry["log_id"],
            timestamp=entry["timestamp"],
            actor=entry["actor_name"],
            action=entry["action_name"],
            reference_id=entry["reference_id"],
            details=entry["details"],
        )

        if recomputed != entry["sha256_hash"]:
            return False, i

    return True, None


def generate_timestamp_iso() -> str:
    """Generate an ISO 8601 timestamp in UTC for audit entries."""
    return datetime.now(timezone.utc).isoformat()


# ── Password Hashing & Authentication ─────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt-hashed password."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate a secure bcrypt hash of a plain password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token embedding tenant and role claims."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.PyJWTError:
        return None
