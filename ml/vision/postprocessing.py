"""Postprocessing and domain thesaurus substitution module for OCR tokens."""

import json
import re
from pathlib import Path

THESAURUS_PATH = Path(__file__).parent / "thesaurus.json"


def load_thesaurus() -> dict:
    if THESAURUS_PATH.exists():
        with open(THESAURUS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"material_standards": {}, "item_types": {}}


_THESAURUS = load_thesaurus()


def sanitize_text(text: str) -> str:
    """Performs single-pass idempotent text cleaning by stripping non-printable characters."""
    if not text:
        return ""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return " ".join(cleaned.split())


def fix_numeric_ambiguities(val_str: str) -> str:
    """Fixes misrecognized characters in numeric/chemical percentage strings."""
    if not val_str:
        return val_str
    
    # Replace misrecognized O/o or l/I after decimal point or between digits
    s = re.sub(r"(?<=\d\.)[Oo](?=\d|\b)", "0", val_str)
    s = re.sub(r"(?<=\d\.)[lI](?=\d|\b)", "1", s)
    s = re.sub(r"(?<=\d)[Oo](?=\d|\b)", "0", s)
    s = re.sub(r"(?<=\d)[lI](?=\d|\b)", "1", s)
    return s


def apply_domain_thesaurus(text: str) -> str:
    """Standardizes common MTC component and material standard abbreviations."""
    if not text:
        return text

    sanitized = sanitize_text(text)
    tokens = sanitized.split()
    normalized_tokens = []

    mat_map = _THESAURUS.get("material_standards", {})
    item_map = _THESAURUS.get("item_types", {})

    for token in tokens:
        upper_tok = token.upper().strip(",")
        if upper_tok in mat_map:
            normalized_tokens.append(mat_map[upper_tok])
        elif upper_tok in item_map:
            normalized_tokens.append(item_map[upper_tok])
        else:
            normalized_tokens.append(token)

    return " ".join(normalized_tokens)


def postprocess_token(text: str) -> tuple[str, str]:
    """Returns a tuple of (clean_normalized_text, raw_original_text)."""
    raw_text = text or ""
    sanitized = sanitize_text(raw_text)
    normalized = apply_domain_thesaurus(sanitized)
    return normalized, raw_text
