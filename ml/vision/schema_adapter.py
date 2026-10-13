"""Turn parse_certificate() output into the team's ExtractedMaterialAttributes.

One ExtractedMaterialAttributes is produced per delivered line item.
Rules of this file:
  * Only values that are PRINTED in the description are extracted. A bare
    number (e.g. "150" with no "LB"/"CLASS") is NOT assumed to be a pressure class.
  * Anything not found stays None and is listed in `missing_attributes`;
    the item is then marked is_incomplete + requires_hitl.
  * Tables flagged unreliable never put chemistry/mechanical data on an item.
  * Size is passed to the schema as inches ("1.5 IN"); the schema's own
    validator converts it to mm. The exact NPS in inches is kept in
    properties["size_nps_inch"].
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

ITEM_TYPES = [  # (regex, name) - first match wins; OCR confuses l/I so FIg = Flg
    (r"\bFLANGES?\b|\bF[LI]G\b", "FLANGE"),
    (r"\bE[LI]+BOW\b", "ELBOW"),
    (r"\bTEE\b", "TEE"),
    (r"\bREDUCER\b", "REDUCER"),
    (r"\bCAP\b", "CAP"),
    (r"\bPIPE\b", "PIPE"),
]
ATTACHMENTS = [
    (r"\bWELD(?:ING)?\s*NECK\b|\bWN\b", "WELD_NECK"),
    (r"\bSLIP\s*ON\b|\bSO\b", "SLIP_ON"),
    (r"\bBLIND\b", "BLIND"),
]
# Fields that must be present, else the item is incomplete and goes to human review.
# Pressure class is required for flanges only. NOTE: this choice needs team confirmation.
CORE_FIELDS = {"FLANGE": ["item_type", "size_nb_mm", "pressure_class", "metallurgy"]}
DEFAULT_CORE = ["item_type", "size_nb_mm", "metallurgy"]


def parse_size_inches(text: str) -> Optional[float]:
    """'1 1/2"' -> 1.5, '3/4"' -> 0.75, '8"' -> 8.0. Needs an inch mark; otherwise None."""
    m = re.search(r'(?<![\d.])(\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)\s*(?:"|\u201d|\'\'|\bIN\b|\bINCH\b)', text, re.I)
    if not m:
        return None
    parts = m.group(1).split()
    total = 0.0
    for p in parts:
        if "/" in p:
            num, den = p.split("/")
            total += int(num) / int(den)
        else:
            total += float(p)
    return total


def parse_description(desc: str) -> Dict[str, Any]:
    """Pull printed attributes out of one description line."""
    out: Dict[str, Any] = {}
    for pattern, name in ITEM_TYPES:
        if re.search(pattern, desc, re.I):
            out["item_type"] = name
            break
    inches = parse_size_inches(desc)
    if inches is not None:
        out["size_inch"] = inches
    m = re.search(r"\b(\d{2,4})\s*(?:LBS?|#)(?!\w)", desc, re.I) or re.search(r"\bCLASS\s*-?\s*(\d{2,4})\b", desc, re.I)
    if m:
        out["pressure_class"] = int(m.group(1))
    m = re.search(r"\bSCH(?:EDULE)?\.?\s*-?\s*(\d+[A-Z]*|XXS|XS|STD)\b", desc, re.I)
    if m:
        out["schedule"] = f"SCH {m.group(1).upper()}"
    m = re.search(r"\b(RFFE|RTJ|RF|FF|FLAT\s*FACE|RAISED\s*FACE|BW)\b", desc, re.I)
    if m:
        face = re.sub(r"\s+", " ", m.group(1).upper())
        out["facing_end"] = {"FLAT FACE": "FF", "RAISED FACE": "RF"}.get(face, face)
    for pattern, name in ATTACHMENTS:
        if re.search(pattern, desc, re.I):
            out["attachment"] = name
            break
    m = re.search(r"\b(ASME|ANSI)\s*B\s?16\.\d+", desc, re.I)
    if m:
        out["standard"] = re.sub(r"\s+", " ", m.group(0).upper()).replace("B 16", "B16")
    m = re.search(r"\bASTM\s*[A-Z]\s?\d{2,4}[A-Z]?(?:\s*S\d{5})?", desc, re.I)
    if m:
        out["metallurgy"] = re.sub(r"\s+", " ", m.group(0).upper())
    return out


def _fallbacks_from_header(header: Dict[str, Any], found: Dict[str, Any]) -> Dict[str, Any]:
    """Fill gaps from document-level text (e.g. 'GOODS: FORGED STEEL ASTM A105 FLANGE')."""
    found = dict(found)
    text = header.get("material_description") or ""
    if "item_type" not in found:
        for pattern, name in ITEM_TYPES:
            if re.search(pattern, text, re.I):
                found["item_type"] = name
                break
    if "metallurgy" not in found:
        # 1) "ASTM A105" printed in the material text, 2) a bare "A105",
        # 3) a stainless grade like "316L/1.4404"; otherwise leave it empty.
        for pattern in (r"\bASTM\s*[A-Z]\s?\d{2,4}[A-Z]?(?:\s*S\d{5})?", r"\bA\d{3}[A-Z]?\b",
                        r"\b\d{3}L?\b(?:\s*/\s*\d\.\d{4})?"):
            m = re.search(pattern, text, re.I)
            if m:
                found["metallurgy"] = re.sub(r"\s+", "", m.group(0)) if pattern.startswith(r"\b\d") else re.sub(r"\s+", " ", m.group(0).upper())
                break
    return found


def _record_for(item: Dict[str, Any], records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for r in records:
        if item.get("item_no") and r["item_no"] == item["item_no"]:
            return r
    for r in records:
        if item.get("heat_no") and r["heat_no"] == item["heat_no"] and r["item_no"] is None:
            return r
    return records[0] if len(records) == 1 else None


def to_attribute_dicts(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """One dict per line item, ready for ExtractedMaterialAttributes(**d)."""
    if parsed.get("document_type") != "mill_test_certificate":
        return []
    header = parsed.get("header", {})
    items = parsed.get("line_items") or [{"item_no": None, "heat_no": header.get("heat_no"),
                                          "quantity": None, "description": header.get("material_description") or ""}]
    reliable = parsed.get("records_reliable", False)
    flags = [f for f in parsed.get("review_flags", []) if f != "certificate number not found"]

    results: List[Dict[str, Any]] = []
    for item in items:
        found = _fallbacks_from_header(header, parse_description(item["description"]))
        record = _record_for(item, parsed.get("records", [])) if reliable else None

        props: Dict[str, Any] = {
            "certificate_no": header.get("certificate_no"),
            "heat_no": (record or {}).get("heat_no") or item.get("heat_no"),
            "line_item_no": item.get("item_no"),
            "quantity": item.get("quantity"),
            "description_raw": item["description"],
            "en10204_type": header.get("en10204_type"),
            "manufacturer": header.get("manufacturer") or header.get("issuer"),
            "customer": header.get("customer"),
        }
        if "attachment" in found:
            props["attachment"] = found["attachment"]
        if "size_inch" in found:
            props["size_nps_inch"] = found["size_inch"]
        if record:
            props["chemistry"] = record["chemistry"]
            props["mechanical"] = record["mechanical"]

        attrs: Dict[str, Any] = {
            "item_type": found.get("item_type"),
            "size": f"{found['size_inch']:g} IN" if "size_inch" in found else None,
            "pressure_class": found.get("pressure_class"),
            "schedule": found.get("schedule"),
            "metallurgy": found.get("metallurgy"),
            "facing_end": found.get("facing_end"),
            "standard": found.get("standard"),
            "properties": props,
        }
        core = CORE_FIELDS.get(attrs["item_type"], DEFAULT_CORE)
        missing = [f for f in core if attrs.get("size" if f == "size_nb_mm" else f) is None]
        attrs["missing_attributes"] = missing
        attrs["is_incomplete"] = bool(missing)
        attrs["confidence_score"] = float(parsed.get("ocr", {}).get("avg_confidence", 1.0))
        attrs["requires_hitl"] = bool(missing) or not reliable or bool(flags)
        results.append(attrs)
    return results


def to_extracted_attributes(parsed: Dict[str, Any]) -> list:
    """Same as to_attribute_dicts but returns the team's Pydantic models."""
    from backend.app.schemas.material import ExtractedMaterialAttributes
    return [ExtractedMaterialAttributes(**d) for d in to_attribute_dicts(parsed)]
