"""Strict detection of the EN 10204 inspection document type."""

import re
from typing import Optional

_EN10204_RE = re.compile(
    r"\bEN\s*10204\s*(?::\s*2004)?\s*[-/,:]?\s*(?:TYPE\s*)?3\s*\.\s*([12])\s*[AB]?\b",
    re.IGNORECASE,
)


def detect_en10204_type(text: str) -> Optional[str]:
    """Return 'EN 10204 3.1' or 'EN 10204 3.2' only if exactly one type is stated.

    Returns None when no type is stated or when both appear. The caller must then
    flag the document for review. Never infers the type from a bare '3.1' or '3.2',
    which also occur inside measurements.
    """
    found = {m.group(1) for m in _EN10204_RE.finditer(text or "")}
    if len(found) != 1:
        return None
    return f"EN 10204 3.{found.pop()}"
