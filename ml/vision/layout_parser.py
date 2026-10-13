"""Layout-aware parser for material test certificates (MTCs).

Why this file exists
--------------------
OCR gives us a flat list of text pieces ("blocks"), each with a box
position on the page. Certificates are tables, so the meaning of a number
depends on WHERE it sits (which column, which row). The old regex parser
only saw the flat text and grabbed the wrong neighbouring words.

This module rebuilds rows and columns from the box positions:

    blocks -> rows -> header labels, chemistry table, mechanical table,
                      line items -> one JSON-friendly dict

Nothing here invents values. If a table cannot be found or looks wrong,
the field is left empty and a message is added to `review_flags`.

Main entry point:
    parse_certificate(blocks) -> dict      (see the docstring there)
"""

from __future__ import annotations

import logging
import math
import re
import statistics
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Rules you may need to edit (kept at the top on purpose)
# --------------------------------------------------------------------------

# Element column headers -> standard name. Keys are upper-case, no spaces/%/dots.
ELEMENTS: Dict[str, str] = {
    "C": "C", "MN": "Mn", "SI": "Si", "P": "P", "S": "S", "CR": "Cr",
    "NI": "Ni", "MO": "Mo", "V": "V", "CU": "Cu", "N": "N", "TI": "Ti",
    "NB": "Nb", "AL": "Al", "PB": "Pb", "B": "B", "W": "W", "CO": "Co",
    "CE": "CE", "PREN": "PREN",
}

# Mechanical column keywords -> property name. First match wins.
MECH_KEYWORDS: List[Tuple[str, str]] = [
    ("yield_strength", r"\byield|\by\.?\s?s\b|\brp\s?0[.,]?2|snervamento|streckgrenze"),
    ("tensile_strength", r"\btensile|\bu\.?t\.?s\b|\bt\.?s\b|\brm\b|rottura|zugfestigkeit"),
    ("elongation_pct", r"elongation|^e\s?%|\ball\.?\s?%|allongement|dehnung"),
    ("reduction_of_area_pct", r"reduction|redution|\br\.?\s?a\b|striction|contrazione|einschn"),
    ("hardness_hb", r"hardness|\bhb\b|\bbhn\b|durete|durezza|\bhrc\b"),
    ("carbon_equivalent", r"equivalent"),
]
STRENGTH_PROPS = {"yield_strength", "tensile_strength"}

# Words in the first column that mean "this row is a limit, not a measurement".
LIMIT_LABELS = {"min": "min", "minimum": "min", "max": "max", "maximum": "max",
                "spec": "spec", "limit": "spec", "requirement": "spec"}

COMPANY_WORDS = re.compile(
    r"\b(ltd|limited|llc|inc|gmbh|co\.|company|corp|solutions|industries|"
    r"industrial|fittings|group|business|pvt)\b", re.I)

# Standards to pick out of the full text (listed raw; not interpreted).
STANDARD_PATTERNS = [
    r"\bASTM\s*[A-Z]\s?\d{2,4}[A-Z]?(?:\s*S\d{5})?(?:[-/]\d{2,4}[A-Z]?)*",
    r"\bA\s?/?\s?SA\s?-?\s?\d{3}[A-Z]?\b",
    r"\bASME\s*S?[AB]\s?-?\s?16\.\d+(?:-\d{4})?",
    r"\bANSI\s*B\s?16\.\d+",
    r"\bNACE\s*MR\s?-?\s?0?1?\s?-?\s?75\b",
]

# Header labels. Each field has regexes that must match at the START of a
# block. The value is whatever follows the label, or a neighbouring block.
HEADER_LABELS: Dict[str, List[str]] = {
    "certificate_no": [
        r"cert(?:ificate)?\.?\s*(?:no|number|nr)\b\.?",
        r"abnahmepr\w*\s*nr\.?",
    ],
    "order_no": [r"(?:best\.?\s*nr\.?\s*/\s*)?order\s*(?:no|number|nr)\b\.?"],
    "po_no": [r"p\.?\s?o\.?\s*(?:no|number|nr)\b\.?", r"purchase\s*order\s*(?:no\.?)?"],
    "customer": [r"customer\s*:", r"customer$", r"buyer\b\s*:?", r"name\s+of\s+buyer",
                 r"besteller\s*/\s*customer\s*:?"],
    "manufacturer": [r"producer\b", r"manufacturer\b", r"provider\b"],
    "heat_no": [r"heat\s*(?:no|number|nr)\b\.?"],
    "material_description": [r"material\s*:?$", r"material\s*:", r"goods\s*:",
                             r"raw\s+material\s+specification\s*:?"],
    "issue_date": [r"(?:issue\s+)?date\s*:?", r"datum\s*/\s*date"],
}

# --------------------------------------------------------------------------
# Small data helpers
# --------------------------------------------------------------------------


@dataclass
class Block:
    """One piece of OCR text with its box (x0, y0 = top-left; x1, y1 = bottom-right)."""

    text: str
    score: float
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def yc(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def height(self) -> float:
        return max(self.y1 - self.y0, 1.0)


def to_blocks(raw: Iterable[Any]) -> List[Block]:
    """Accept OCR output in either form and return Block objects.

    Form 1: dicts like {"text": ..., "score": ..., "box": [x0, y0, x1, y1]}
    Form 2: tuples like (text, score, (x0, y0, x1, y1))  <- PaddleOCREngine.predict
    Items that have no usable box are skipped (and logged), never guessed.
    """
    blocks: List[Block] = []
    for item in raw:
        try:
            if isinstance(item, dict):
                text, score, box = item["text"], item.get("score", 1.0), item["box"]
            else:
                text, score, box = item[0], item[1], item[2]
            x0, y0, x1, y1 = (float(v) for v in box)
            if str(text).strip():
                blocks.append(Block(str(text).strip(), float(score), x0, y0, x1, y1))
        except (KeyError, IndexError, TypeError, ValueError):
            logger.warning("Skipping OCR block with bad format: %r", item)
    return blocks


_NUMBER = re.compile(r"^[+-]?\d+(?:[.,]\d+)?$")


def parse_cell(token: str) -> Optional[List[float]]:
    """Turn one printed cell into a list of numbers, or None if it is not a number.

    "0.23" -> [0.23]      "0,180" -> [0.18] (decimal comma)
    "163/165" -> [163, 165]   "254,255" -> [254, 255] (two readings, not 254.255)
    "<0.35", "0.6~1.05", "Max" -> None (limits and words are not measurements)
    """
    tok = token.strip()
    if re.fullmatch(r"\d+/\d+", tok):
        return [float(p) for p in tok.split("/")]
    if re.fullmatch(r"\d{2,}[,]\d{3}", tok):          # 254,255
        return [float(p) for p in tok.split(",")]
    if _NUMBER.match(tok):
        return [float(tok.replace(",", "."))]
    return None


def is_plain_int(text: str, max_digits: int = 4) -> bool:
    return bool(re.fullmatch(rf"\d{{1,{max_digits}}}", text.strip()))


def split_merged_numbers(blocks: List[Block]) -> List[Block]:
    """Split blocks like "0,190 0.960" (two cells merged by OCR) into two blocks.

    The box is cut in proportion to where each token sits in the text.
    Only blocks made entirely of numbers are split.
    """
    out: List[Block] = []
    for b in blocks:
        parts = b.text.split()
        if len(parts) >= 2 and all(parse_cell(p) is not None for p in parts):
            total = len(b.text)
            width = b.x1 - b.x0
            pos = 0
            for p in parts:
                start = b.text.index(p, pos)
                pos = start + len(p)
                x0 = b.x0 + width * start / total
                x1 = b.x0 + width * (start + len(p)) / total
                out.append(Block(p, b.score, x0, b.y0, x1, b.y1))
        else:
            out.append(b)
    return out


def group_rows(blocks: List[Block]) -> List[List[Block]]:
    """Group blocks that sit on the same line, each row sorted left to right."""
    if not blocks:
        return []
    tolerance = 0.6 * statistics.median(b.height for b in blocks)
    ordered = sorted(blocks, key=lambda b: b.yc)
    rows: List[List[Block]] = []
    current: List[Block] = []
    row_y = 0.0
    for b in ordered:
        if current and abs(b.yc - row_y) > tolerance:
            rows.append(current)
            current = []
        if not current:
            row_y = b.yc
        current.append(b)
    if current:
        rows.append(current)
    return [sorted(r, key=lambda b: b.x0) for r in rows]


# --------------------------------------------------------------------------
# Column anchors (where each table column sits on the page)
# --------------------------------------------------------------------------


@dataclass
class Anchor:
    name: str          # e.g. "Mn" or "yield_strength"
    xc: float          # horizontal centre of the column header
    row: int           # index of the row the header text was found in
    unit: Optional[str] = None


def element_name(text: str) -> Optional[str]:
    key = re.sub(r"[%\s.]", "", text).upper()
    return ELEMENTS.get(key) if len(text) <= 8 else None


def _cluster(anchors: List[Anchor], gap: float = 35.0) -> List[List[Anchor]]:
    """Group anchors whose x positions are within `gap` pixels of each other."""
    groups: List[List[Anchor]] = []
    for a in sorted(anchors, key=lambda a: a.xc):
        if groups and a.xc - groups[-1][-1].xc <= gap:
            groups[-1].append(a)
        else:
            groups.append([a])
    return groups


def find_chemistry_anchors(rows: List[List[Block]]) -> List[Anchor]:
    """Header row = a row with at least 4 element symbols (C, Mn, Si, ...)."""
    best: List[Anchor] = []
    for i, row in enumerate(rows):
        found = [Anchor(element_name(b.text), b.xc, i) for b in row if element_name(b.text)]
        # Same element twice in one row means this is not a header row.
        if len(found) >= 4 and len({a.name for a in found}) == len(found):
            if len(found) > len(best):
                best = found
    return best


def find_mechanical_anchors(rows: List[List[Block]]) -> List[Anchor]:
    """Find mechanical column headers by keyword; the lowest header row wins a clash."""
    candidates: List[Anchor] = []
    for i, row in enumerate(rows):
        for b in row:
            if len(b.text) > 28:
                continue
            low = b.text.lower().strip()
            for prop, pattern in MECH_KEYWORDS:
                if re.search(pattern, low):
                    name = "hardness_hrc" if prop == "hardness_hb" and "hrc" in low else prop
                    candidates.append(Anchor(name, b.xc, i, _unit_in_text(low)))
                    break
    anchors: List[Anchor] = []
    for group in _cluster(candidates):
        lowest = max(group, key=lambda a: a.row)
        name = lowest.name
        if any(a.name == "hardness_hrc" for a in group):
            name = "hardness_hrc"
        unit = next((a.unit for a in group if a.unit), None)
        anchors.append(Anchor(name, sum(a.xc for a in group) / len(group), lowest.row, unit))
    return anchors


def _unit_in_text(low: str) -> Optional[str]:
    if "psi" in low:
        return "psi"
    if re.search(r"mpa|n/mm", low):
        return "mpa"
    return None


def attach_units(anchors: List[Anchor], rows: List[List[Block]], last_row: int) -> None:
    """Strength columns need a unit (MPa vs PSI). Look near the header for it."""
    first = min((a.row for a in anchors), default=0)
    for a in anchors:
        if a.name not in STRENGTH_PROPS or a.unit:
            continue
        best, best_dist = None, 90.0
        for row in rows[max(first - 4, 0): last_row + 4]:
            for b in row:
                unit = _unit_in_text(b.text.lower())
                if unit and abs(b.xc - a.xc) < best_dist:
                    best, best_dist = unit, abs(b.xc - a.xc)
        a.unit = best


# --------------------------------------------------------------------------
# Reading a table (chemistry or mechanical)
# --------------------------------------------------------------------------

HEAT_HEADER = re.compile(r"^(heat|ht\s*/?\s*lt|ht|lot|melt|cast)", re.I)
ITEM_HEADER = re.compile(r"^(item|no\.?|sr\.?\s?no\.?|s\.?\s?no\.?|sl\.?)$", re.I)
HEAT_LIKE = re.compile(r"^(?=.*\d)(?=.*[A-Za-z\-])[A-Za-z0-9][A-Za-z0-9\-/]{3,}$")


def _left_headers(rows: List[List[Block]], first_row: int, left_of: float) -> Tuple[Optional[Block], Optional[Block]]:
    """Find the 'Heat No.' and 'Item/No.' header blocks that sit left of the data columns."""
    heat = item = None
    for row in rows[max(first_row - 3, 0): first_row + 3]:
        for b in row:
            if b.xc >= left_of:
                continue
            if heat is None and HEAT_HEADER.match(b.text.strip()):
                heat = b
            elif item is None and ITEM_HEADER.match(b.text.strip()):
                item = b
    return heat, item


def read_table(rows: List[List[Block]], anchors: List[Anchor]) -> Dict[str, Any]:
    """Read data rows under a header made of `anchors`.

    Returns {"rows": [{"item_no", "heat_no", "values": {name: value}}...],
             "limits": {"min": {...}, "max": {...}}}
    """
    if not anchors:
        return {"rows": [], "limits": {}}
    anchors = sorted(anchors, key=lambda a: a.xc)
    last_header_row = max(a.row for a in anchors)
    spacing = statistics.median(
        [b.xc - a.xc for a, b in zip(anchors, anchors[1:])] or [80.0])
    reach = max(25.0, 0.6 * spacing)
    needed = max(2, math.ceil(0.5 * len(anchors)))
    first_x = anchors[0].xc
    heat_hdr, item_hdr = _left_headers(rows, anchors[0].row, first_x)

    result: Dict[str, Any] = {"rows": [], "limits": {}}
    seen_data = False
    for row in rows[last_header_row + 1:]:
        cells: Dict[str, Any] = {}
        left: List[Block] = []
        for b in row:
            nums = parse_cell(b.text)
            anchor = min(anchors, key=lambda a: abs(a.xc - b.xc))
            if nums is not None and abs(anchor.xc - b.xc) <= reach and b.xc > first_x - reach:
                cells[anchor.name] = nums[0] if len(nums) == 1 else nums
            elif b.xc < first_x - reach:
                left.append(b)
        label = " ".join(b.text for b in left).strip().lower()
        label_kind = LIMIT_LABELS.get(label)

        if label_kind and len(cells) >= needed:          # a "Min" / "Max" row
            result["limits"][label_kind] = cells
            seen_data = True
            continue
        if len(cells) >= needed:
            result["rows"].append({"item_no": _pick_item(left, item_hdr),
                                   "heat_no": _pick_heat(left, heat_hdr),
                                   "values": cells})
            seen_data = True
        elif seen_data:
            break                                         # table ended
        elif row[0].yc - rows[last_header_row][0].yc > 400:
            break                                         # gave up looking
    return result


def _pick_item(left: List[Block], header: Optional[Block]) -> Optional[str]:
    ints = [b for b in left if is_plain_int(b.text)]
    if header is not None and ints:
        return min(ints, key=lambda b: abs(b.xc - header.xc)).text
    return ints[0].text if ints and left and left[0] is ints[0] else None


def _pick_heat(left: List[Block], header: Optional[Block]) -> Optional[str]:
    if header is not None:
        near = [b for b in left if abs(b.xc - header.xc) < 45]
        if near:
            return _valid_heat(min(near, key=lambda b: abs(b.xc - header.xc)).text)
    for b in left:
        if HEAT_LIKE.match(b.text):
            return b.text
    return None


def _valid_heat(text: Optional[str]) -> Optional[str]:
    """Keep a heat number only if it looks like one (letters+digits, or 3+ digits)."""
    if text and (HEAT_LIKE.match(text) or re.fullmatch(r"\d{3,}", text)):
        return text
    return None


# --------------------------------------------------------------------------
# Line items (the "what was delivered" table)
# --------------------------------------------------------------------------


def find_line_items(rows: List[List[Block]]) -> List[Dict[str, Any]]:
    """Best-effort read of the delivered-items table (description, quantity, heat)."""
    header_idx = next((i for i, r in enumerate(rows)
                       if any(re.search(r"description|descrizione", b.text, re.I) and len(b.text) < 30
                              for b in r)), None)
    if header_idx is None:
        return []
    zone = rows[max(header_idx - 1, 0): header_idx + 4]
    flat = [b for r in zone for b in r]
    desc_hdr = next(b for b in flat if re.search(r"description|descrizione", b.text, re.I))
    item_hdr = next((b for b in sorted(flat, key=lambda b: b.x0)
                     if ITEM_HEADER.match(b.text.strip()) or b.text.strip().lower() in ("srno", "sr no")), None)
    heat_hdr = next((b for b in flat if HEAT_HEADER.match(b.text.strip()) and len(b.text) < 14), None)
    qty_hdr = next((b for b in flat if re.match(r"^(qty|quantity|quantita|pcs)\b", b.text.strip(), re.I)), None)

    # Description region: between the id/quantity columns on each side of it.
    ids = [h for h in (item_hdr, heat_hdr, qty_hdr) if h is not None]
    left_edge = max([h.x1 for h in ids if h.xc < desc_hdr.xc] or [0.0])
    right_edge = min([h.x0 for h in ids if h.xc > desc_hdr.xc] or [1e9])

    items: List[Dict[str, Any]] = []
    for row in rows[header_idx + 1:]:
        first = row[0]
        if items and any(element_name(b.text) or re.search(r"tensile|yield|heat\s*treat", b.text, re.I)
                         for b in row) and not is_plain_int(first.text):
            break                                  # a chemistry/mechanical header: table is over
        starts_item = item_hdr is not None and is_plain_int(first.text) and abs(first.xc - item_hdr.xc) < 60
        if starts_item and any(it["item_no"] == first.text for it in items):
            break                                  # item numbers started again: next table
        if starts_item:
            items.append({"item_no": first.text, "heat_no": None, "quantity": None, "_parts": []})
            current = items[-1]
        elif items and _is_continuation(row, left_edge, right_edge, items[-1]):
            current = items[-1]
        else:
            if items:
                break
            continue
        for b in row:
            if b is first and starts_item:
                continue
            if heat_hdr is not None and abs(b.xc - heat_hdr.xc) < 60 and HEAT_LIKE.match(b.text):
                current["heat_no"] = b.text
            elif qty_hdr is not None and abs(b.xc - qty_hdr.xc) < 50 and is_plain_int(b.text, 6):
                current["quantity"] = int(b.text)
            elif left_edge <= b.xc <= right_edge and not re.fullmatch(r"\d+[.,]\d+", b.text):
                current["_parts"].append(b.text)
        current["_y"] = row[0].yc
    for it in items:
        it["description"] = " ".join(it.pop("_parts")).strip()
        it.pop("_y", None)
    return [it for it in items if it["description"]]


def _is_continuation(row: List[Block], left_edge: float, right_edge: float, last: Dict[str, Any]) -> bool:
    """A second text line that belongs to the previous item (e.g. 9055 descriptions)."""
    if is_plain_int(row[0].text):
        return False
    gap = row[0].yc - last.get("_y", row[0].yc)
    inside = [b for b in row if left_edge <= b.xc <= right_edge]
    return 0 < gap < 40 and bool(inside) and not any(
        re.search(r"chemical|mechanical|analisi|properties", b.text, re.I) for b in row)


# --------------------------------------------------------------------------
# Header fields (certificate no., PO, customer, ...)
# --------------------------------------------------------------------------


def _clean_value(value: str) -> str:
    value = re.split(r"\s+(?:DT\.?|DATED)\b", value, maxsplit=1, flags=re.I)[0]
    return value.strip(" :.-\u2013")


def _is_label(text: str) -> bool:
    """True for text that is itself a field label (so it cannot be a value)."""
    t = text.strip()
    return t.endswith(":") or any(re.match(p, t, re.I) for pats in HEADER_LABELS.values() for p in pats)


def _neighbour_value(label: Block, blocks: List[Block], need_digit: bool, wrap: bool = False) -> Optional[str]:
    """Value in the block to the right on the same row, else the block just below."""
    height = label.height
    right = [b for b in blocks if b is not label and b.x0 >= label.x1 - 8
             and abs(b.yc - label.yc) < 0.6 * height and b.x0 - label.x1 < 260
             and not _is_label(b.text)]
    below = [b for b in blocks if b.y0 >= label.y1 - 4 and b.y0 - label.y1 < 2.2 * height
             and b.x0 < label.x1 and b.x1 > label.x0 and not _is_label(b.text)]
    for group in (sorted(right, key=lambda b: (abs(b.yc - label.yc), b.x0)), sorted(below, key=lambda b: b.y0)):
        for b in group[:1]:
            text = _clean_value(b.text)
            if text and not text.endswith(":") and (not need_digit or re.search(r"\d", text)):
                if wrap:
                    text = _join_wrapped(b, blocks, text)
                return text
    return None


def _join_wrapped(first: Block, blocks: List[Block], text: str) -> str:
    """Add a second text line printed directly under `first` (a wrapped cell)."""
    for b in sorted(blocks, key=lambda b: b.y0):
        same_cell = (b is not first and b.y0 >= first.y0 + 0.5 * first.height
                     and b.y0 - first.y1 < 0.6 * first.height
                     and b.x0 < first.x1 and b.x1 > first.x0 and not b.text.endswith(":"))
        if same_cell:
            return f"{text} {b.text}".strip()
    return text


def parse_header_fields(blocks: List[Block]) -> Dict[str, Optional[str]]:
    fields: Dict[str, Optional[str]] = {k: None for k in HEADER_LABELS}
    for field, patterns in HEADER_LABELS.items():
        for b in sorted(blocks, key=lambda b: (b.y0, b.x0)):
            text = b.text.strip()
            for pat in patterns:
                m = re.match(pat, text, re.I)
                if not m:
                    continue
                rest = _clean_value(text[m.end():])
                # "Customer Code: B339" is a different label, not a customer name.
                if field == "customer" and re.match(r"\s*code", text[m.end():], re.I):
                    continue
                if field == "material_description" and len(rest) > 60:
                    continue
                need_digit = field in ("issue_date", "certificate_no", "order_no", "po_no", "heat_no")
                value = rest or _neighbour_value(b, blocks, need_digit, wrap=(field == "customer"))
                if value and (not need_digit or re.search(r"\d", value)):
                    fields[field] = value
                    break
            if fields[field]:
                break
    return fields


def find_issuer(blocks: List[Block]) -> Optional[str]:
    """Company name printed in the letterhead (top of the page)."""
    if not blocks:
        return None
    page_height = max(b.y1 for b in blocks)
    for b in sorted(blocks, key=lambda b: (b.y0, b.x0)):
        if b.y0 > 0.12 * page_height:
            break
        if COMPANY_WORDS.search(b.text) and re.search(r"[A-Za-z]{3}", b.text):
            return b.text.split(",")[0].strip()
    return None


def find_standards(text: str) -> List[str]:
    found: List[str] = []
    for pat in STANDARD_PATTERNS:
        for m in re.finditer(pat, text, re.I):
            s = re.sub(r"\s+", " ", m.group(0)).strip()
            if s not in found:
                found.append(s)
    return found


# --------------------------------------------------------------------------
# Putting it together
# --------------------------------------------------------------------------


def _merge_records(chem: Dict[str, Any], mech_tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Join chemistry rows and mechanical rows that describe the same item/heat."""
    records: List[Dict[str, Any]] = []

    def find(item: Optional[str], heat: Optional[str]) -> Optional[Dict[str, Any]]:
        for rec in records:
            if rec["item_no"] == item and rec["heat_no"] == heat:
                return rec
        for rec in records:
            if item and rec["item_no"] == item:
                return rec
            if not item and heat and rec["heat_no"] == heat and rec["item_no"] is None:
                return rec
        return None

    def add(table_row: Dict[str, Any], kind: str) -> None:
        item, heat = table_row["item_no"], table_row["heat_no"]
        rec = find(item, heat)
        if rec is None:
            rec = {"item_no": item, "heat_no": heat, "chemistry": {}, "mechanical": {}}
            records.append(rec)
        rec["heat_no"] = rec["heat_no"] or heat
        values = dict(table_row["values"])
        if "carbon_equivalent" in values:          # printed in the mechanical table
            rec["chemistry"]["CE"] = values.pop("carbon_equivalent")
        rec[kind].update(values)

    for r in chem.get("rows", []):
        add(r, "chemistry")
    for table in mech_tables:
        for r in table.get("rows", []):
            add(r, "mechanical")
    return records


def parse_certificate(raw_blocks: Iterable[Any], detect_type=None) -> Dict[str, Any]:
    """Parse one certificate from OCR blocks.

    `raw_blocks`: list of {"text", "score", "box"} dicts or (text, score, box) tuples.
    `detect_type`: optional function(text) -> "EN 10204 3.1" | None (your spec_detect).

    Returns a dict:
      document_type    "mill_test_certificate" | "data_sheet" | "unknown"
      header           certificate_no, order_no, po_no, customer, manufacturer,
                       issuer, heat_no, material_description, issue_date,
                       en10204_type, standards (list, raw strings)
      records          one per item/heat: item_no, heat_no, chemistry, mechanical
      records_reliable False when the tables look misread (do not use the records)
      limits           min/max rows printed in the tables (when present)
      line_items       best-effort delivered items (item_no, heat_no, quantity, description)
      ocr              block count and confidence
      review_flags     plain-English reasons a human should double-check
    """
    blocks = split_merged_numbers(to_blocks(raw_blocks))
    flags: List[str] = []
    if not blocks:
        return {"document_type": "unknown", "header": {}, "records": [], "records_reliable": False,
                "limits": {}, "line_items": [], "ocr": {"blocks": 0}, "review_flags": ["no OCR text found"]}

    rows = group_rows(blocks)
    full_text = "\n".join(" ".join(b.text for b in r) for r in rows)
    scores = [b.score for b in blocks]

    # ---- document type -------------------------------------------------
    looks_like_cert = bool(re.search(r"certificate|pr\u00fcfzeugnis|pruefzeugnis|10204|test report", full_text, re.I))
    chem_anchors = find_chemistry_anchors(rows)
    if looks_like_cert and chem_anchors:
        doc_type = "mill_test_certificate"
    elif re.search(r"data\s*sheet", full_text, re.I):
        doc_type = "data_sheet"
    else:
        doc_type = "unknown"
    if doc_type != "mill_test_certificate":
        flags.append("not recognised as a material test certificate")

    # ---- header ---------------------------------------------------------
    header: Dict[str, Any] = parse_header_fields(blocks)
    header["issuer"] = find_issuer(blocks)
    header["en10204_type"] = detect_type(full_text) if detect_type else None
    header["standards"] = find_standards(full_text)

    records: List[Dict[str, Any]] = []
    limits: Dict[str, Any] = {}
    line_items: List[Dict[str, Any]] = []
    if doc_type == "mill_test_certificate":
        # ---- chemistry --------------------------------------------------
        chem = read_table(rows, chem_anchors)
        if not chem["rows"]:
            flags.append("chemistry table found but no readable data rows")
        # ---- mechanical -------------------------------------------------
        mech_tables: List[Dict[str, Any]] = []
        mech_anchors = find_mechanical_anchors(rows)
        for zone in _zones(mech_anchors, rows):
            table = read_table(rows, zone)
            if table["rows"]:
                last = max(a.row for a in zone)
                attach_units(zone, rows, last + 1)
                _rename_with_units(table, zone)
                mech_tables.append(table)
        if not mech_tables:
            flags.append("no mechanical properties table found")

        records = _merge_records(chem, mech_tables)
        for t in [chem] + mech_tables:
            for kind, vals in t.get("limits", {}).items():
                limits.setdefault(kind, {}).update(vals)
        line_items = find_line_items(rows)

        # A single heat number printed in the header applies to rows with none.
        if header.get("heat_no"):
            for rec in records:
                rec["heat_no"] = rec["heat_no"] or header["heat_no"]
        elif not header.get("heat_no") and len({r["heat_no"] for r in records if r["heat_no"]}) == 1:
            header["heat_no"] = next(r["heat_no"] for r in records if r["heat_no"])

        if any("yield_strength" in r["mechanical"] or "tensile_strength" in r["mechanical"] for r in records):
            flags.append("strength unit not found next to the column header (not assumed)")
        if records and chem["rows"] and mech_tables and len(chem["rows"]) != sum(len(t["rows"]) for t in mech_tables):
            flags.append("chemistry and mechanical tables have different row counts")
        if not header.get("certificate_no"):
            flags.append("certificate number not found")
        if any(not 0 <= v <= 100 for r in records for v in r["chemistry"].values() if isinstance(v, float)
               and r["chemistry"].get("CE") != v and v != r["chemistry"].get("PREN")):
            flags.append("chemistry value outside 0-100 %: table was probably misread")
        if any(r["chemistry"].get("C", 0) > 1.0 for r in records):
            flags.append("carbon above 1.0 %: please check the chemistry rows against the photo")
        if any(r["heat_no"] is None and r["item_no"] is None for r in records) and len(records) > 1:
            flags.append("some rows have neither item nor heat number")

    unreliable = ("outside 0-100", "carbon above 1.0", "different row counts", "neither item nor heat")
    records_reliable = bool(records) and not any(u in f for f in flags for u in unreliable)
    if records and not records_reliable:
        flags.append("records are NOT reliable: send this document to human review")

    if scores and statistics.mean(scores) < 0.9:
        flags.append("low average OCR confidence")

    return {
        "document_type": doc_type,
        "header": header,
        "records": records,
        "records_reliable": records_reliable,
        "limits": limits,
        "line_items": line_items,
        "ocr": {"blocks": len(blocks),
                "avg_confidence": round(statistics.mean(scores), 3),
                "min_confidence": round(min(scores), 3)},
        "review_flags": flags,
    }


def _zones(anchors: List[Anchor], rows: List[List[Block]]) -> List[List[Anchor]]:
    """Split mechanical anchors into separate tables when they are far apart vertically."""
    if not anchors:
        return []
    anchors = sorted(anchors, key=lambda a: a.row)
    zones: List[List[Anchor]] = [[anchors[0]]]
    for a in anchors[1:]:
        gap = rows[a.row][0].yc - rows[zones[-1][-1].row][0].yc
        if gap < 160:
            zones[-1].append(a)
        else:
            zones.append([a])
    return zones


def _rename_with_units(table: Dict[str, Any], anchors: List[Anchor]) -> None:
    """yield_strength + unit 'mpa' -> yield_strength_mpa. No unit -> name stays plain."""
    units = {a.name: a.unit for a in anchors if a.unit}

    def rename(values: Dict[str, Any]) -> Dict[str, Any]:
        return {(f"{k}_{units[k]}" if k in STRENGTH_PROPS and k in units else k): v
                for k, v in values.items()}

    for r in table["rows"]:
        r["values"] = rename(r["values"])
    for kind in list(table["limits"]):
        table["limits"][kind] = rename(table["limits"][kind])
