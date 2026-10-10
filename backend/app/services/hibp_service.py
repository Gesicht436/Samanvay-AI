"""HAVE_I_BEEN_PWNED Pwned Passwords range lookup (k-anonymity).

Privacy-preserving password-breached check.

Only the first five hex characters of the SHA-1 hash are sent to the HIBP
range API. The plaintext password and the full 40-character SHA-1 hash never
leave the process, and the suffix comparison is performed locally on the
returned suffix list. No email or breach data is used by this module.
"""

import hashlib

import httpx

_API_BASE_URL = "https://api.pwnedpasswords.com"
_REQUEST_TIMEOUT = httpx.Timeout(5.0, read=5.0)

# Generic, non-revealing message shown when the password is known to be breached.
_BREACHED_PASSWORD_MESSAGE = (
    "This password has been exposed in a data breach. Please choose a different password."
)

# Shown when HIBP itself cannot be reached or misbehaves; the caller retries
# instead of silently accepting the unchecked password.
_RETRYABLE_VERIFICATION_MESSAGE = (
    "Password breach verification is temporarily unavailable. Please retry verification later."
)
# Valid hexadecimal characters allowed in a HIBP range suffix.
_HEX_CHARS = frozenset("0123456789abcdefABCDEF")

# Digits allowed in a HIBP range breach count (non-negative integer only).
_DIGITS = frozenset("0123456789")



class HIBPVerificationError(Exception):
    """Raised when HIBP verification cannot be completed (retryable)."""


def _sha1_hex(password: str) -> str:
    """Return the lowercase SHA-1 hex digest of *password*."""
    return hashlib.sha1(password.encode("utf-8")).hexdigest()


def _parse_range_text(text: str) -> dict[str, int]:
    """Parse raw HIBP range text into a ``suffix -> count`` mapping.

    Every non-empty line must be ``<35-hex-suffix>:<non-negative-integer>``.
    Any line that violates this contract causes the entire response to be
    rejected with :class:`HIBPVerificationError`; malformed lines are never
    silently dropped, because dropping them would change the breach count
    seen by the caller.
    """
    breaches = {}
    for line in text.splitlines():
        if not line:
            continue
        if ":" not in line:
            raise HIBPVerificationError(
                "HIBP response line is missing the ':' separator."
            )
        suffix, count_str = line.split(":", 1)
        if len(suffix) != 35 or not all(c in _HEX_CHARS for c in suffix):
            raise HIBPVerificationError(
                "HIBP response contains a suffix that is not 35 hex characters."
            )
        if not count_str or not all(c in _DIGITS for c in count_str):
            raise HIBPVerificationError(
                "HIBP response count is not a non-negative integer."
            )
        count = int(count_str)
        if count < 0:
            raise HIBPVerificationError(
                "HIBP response contains a negative breach count."
            )
        breaches[suffix] = count
    return breaches


def _fetch_range(client: httpx.Client, prefix: str) -> dict[str, int]:
    """Issue the k-anonymity range request and parse the response."""
    response = client.get(f"{_API_BASE_URL}/range/{prefix}")
    response.raise_for_status()
    return _parse_range_text(response.text)


def check_password_against_hibp(password: str, client: httpx.Client | None = None) -> int:
    """Return the number of HIBP breaches for *password*.

    Security properties:
    - Only the first five hex characters (SHA-1 range prefix) leave the process.
    - The plaintext password and the full 40-character SHA-1 hash are never sent
      or logged.
    - The suffix comparison happens locally.

    Returns 0 when *password* is not known to HIBP.
    Raises HIBPVerificationError when the request fails, the response is
    malformed, or the verification could not be completed (retryable).
    """
    lookup_hash = _sha1_hex(password)
    prefix = lookup_hash[:5].upper()
    suffix = lookup_hash[5:].upper()

    http_client = client if client is not None else httpx.Client(timeout=_REQUEST_TIMEOUT)
    try:
        try:
            breaches = _fetch_range(http_client, prefix)
        except (httpx.HTTPError, ValueError) as exc:
            raise HIBPVerificationError(_RETRYABLE_VERIFICATION_MESSAGE) from exc
    finally:
        if client is None:
            http_client.close()

    if not breaches:
        raise HIBPVerificationError("Unexpected HIBP response format.")

    count = breaches.get(suffix)
    if count is None:
        return 0
    return count
