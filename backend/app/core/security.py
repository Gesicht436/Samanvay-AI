"""
Samanvay-AI SHA-256 Digital Seal & Audit Chain Primitives.

Provides cryptographic hash computation for:
- Sovereign CVC/CAG audit ledger tamper-evident hash chain
- CISF gate pass digital seals
- API idempotency request body hashing
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


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
