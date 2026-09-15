import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

PSI_TO_MPA = 0.00689476

class MTCMetadata(BaseModel):
    document_type: str = "MTC"
    certificate_type: Optional[str] = None
    heat_numbers: List[str] = Field(default_factory=list)
    material_grade: Optional[str] = None
    governing_standard: Optional[str] = None
    product_description: Optional[str] = None
    yield_strength_mpa: Optional[float] = None
    tensile_strength_mpa: Optional[float] = None
    elongation_pct: Optional[float] = None
    unit_system: str = "METRIC"

def parse_mtc_certificate(text: str) -> Dict[str, Any]:
    extracted = MTCMetadata()

    if re.search(r"\b(ACTUATOR DATA SHEET|VALVE DATA SHEET)\b", text, re.IGNORECASE):
        extracted.document_type = "EQUIPMENT_DATASHEET"
        model_m = re.search(r"Model\s*[:.\-]?\s*([A-Z0-9\-\./]+)", text, re.IGNORECASE)
        if model_m:
            extracted.product_description = f"Actuator Model: {model_m.group(1).strip()}"
        return extracted.model_dump()

    cert_match = re.search(r"EN\s*10204\s*[-/:]?\s*(?:TYPE\s*)?(3\.1\.?B?|3\.2|2\.2)", text, re.IGNORECASE)
    if cert_match:
        extracted.certificate_type = f"EN 10204 {cert_match.group(1).upper()}"
    elif re.search(r"\b3\.1\.?B?\b", text):
        extracted.certificate_type = "EN 10204 3.1"

    std_match = re.search(
        r"\b((?:ASME|ANSI)\s*B\s*16\.[0-9]+[a-z]?|API\s*(?:6D|6A|5L)|ASTM\s*[A-Z]\d+(?:/[A-Z]\d+)*|MSS\s*SP[- ]\d+)",
        text,
        re.IGNORECASE,
    )
    if std_match:
        extracted.governing_standard = std_match.group(1).strip()

    grade_match = re.search(
        r"(?:GRADE|MATERIAL|SPEC|SPECIFICATION|WERKSTOFF)\s*[:.\-]?\s*"
        r"([A-Z0-9]{2,}(?:\s*[-/]\s*[A-Z0-9]+)*(?:\s*(?:LF2|LF3|S32750|316L|304L|A105N|A105|1\.4404))?)",
        text,
        re.IGNORECASE,
    )
    if grade_match:
        extracted.material_grade = grade_match.group(1).strip()
    else:
        fallback_grade = re.search(
            r"\b(ASTM\s+A\d+[A-Z]?|S32750|316L\s*/\s*1\.4404|SS316L|A105N?|A350\s+LF2)\b",
            text,
            re.IGNORECASE,
        )
        if fallback_grade:
            extracted.material_grade = fallback_grade.group(1).strip()

    heat_candidates = re.findall(r"\b(?:PS-\d+|[0-9]{3,6}|5A\d+-\d+|[A-Z]{1,2}\d{4,6}|QL\d+)\b", text)
    valid_heats = list(dict.fromkeys([h for h in heat_candidates if len(h) >= 3 and not h.startswith("10204")]))
    extracted.heat_numbers = valid_heats[:15]

    is_psi = bool(re.search(r"\b(PSI|Y\.S\s*\(PSI\)|T\.S\s*\(PSI\)|LBS)\b", text, re.IGNORECASE))
    if is_psi:
        extracted.unit_system = "IMPERIAL_PSI"

    ts_match = re.search(r"(?:TENSILE|U\.T\.S|ROTTURA|ZUGFESTIGKEIT|T\.S\s*\(PSI\))\s*[:.\-]?\s*(\d{3,6}(?:\.\d+)?)", text, re.IGNORECASE)
    if ts_match:
        raw_ts = float(ts_match.group(1))
        extracted.tensile_strength_mpa = round(raw_ts * PSI_TO_MPA, 2) if is_psi else raw_ts

    ys_match = re.search(r"(?:YIELD|Y\.S|SNERVAMENTO|STRECKGRENZE|Y\.S\s*\(PSI\))\s*[:.\-]?\s*(\d{3,6}(?:\.\d+)?)", text, re.IGNORECASE)
    if ys_match:
        raw_ys = float(ys_match.group(1))
        extracted.yield_strength_mpa = round(raw_ys * PSI_TO_MPA, 2) if is_psi else raw_ys

    el_match = re.search(r"(?:ELONGATION|EL|A%|ALLONGEMENT|DEHNUNG)\s*[:.\-]?\s*(\d{1,2}(?:\.\d+)?)", text, re.IGNORECASE)
    if el_match:
        extracted.elongation_pct = float(el_match.group(1))

    desc_match = re.search(r"(?:DESCRIPTION|ITEM\s+DESCRIPTION|PRODUCT|GEGENSTAND|COMMODITY)\s*[:.\-]?\s*([^\n\r]+)", text, re.IGNORECASE)
    if desc_match:
        extracted.product_description = desc_match.group(1).strip()

    return extracted.model_dump()