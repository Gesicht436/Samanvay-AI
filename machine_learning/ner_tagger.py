import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.app.contracts.matching import ExtractedMaterialAttributes

ENTITY_TYPES = (
    "ITEM_TYPE",
    "SIZE",
    "PRESSURE_RATING",
    "METALLURGY",
    "FACING_END",
    "STANDARD",
    "INDIAN_STANDARD",
    "OISD_STANDARD",
    "EIL_SPECIFICATION",
    "GEM_CATEGORY",
    "GEM_BID_NUMBER",
    "CPPP_TENDER_ID",
    "MESC_CODE",
    "MANUFACTURER",
    "PRODUCT_FORM",
    "COATING",
    "INSPECTION_CLASS",
    "DOCUMENT_NUMBER",
    "PROJECT",
    "END_CONNECTION",
    "TEMPERATURE_RATING",
    "PURCHASE_ORDER",
    "CERTIFICATE_NUMBER",
    "BID_NUMBER",
    "INSPECTION_AGENCY",
)

ITEM_TYPES = {
    "FLG": "FLANGE",
    "FLANGE": "FLANGE",
    "GATE VALVE": "GATE_VALVE",
    "BALL VALVE": "BALL_VALVE",
    "GLOBE VALVE": "GLOBE_VALVE",
    "VALVE": "VALVE",
    "GATE": "GATE_VALVE",
    "BALL": "BALL_VALVE",
    "BOLT": "BOLT",
    "STUD": "STUD_BOLT",
}
FACING_TYPES = {"WN": "WELD_NECK", "WNRF": "WELD_NECK_RAISED_FACE", "RF": "RAISED_FACE", "RTJ": "RING_TYPE_JOINT", "BW": "BUTT_WELD"}
_METALLURGY_TYPES = (
    ("A105N", "ASTM_A105N"),
    ("AISI 316", "SS316"),
    ("SS316", "SS316"),
    ("316L", "SS316L"),
    ("A105", "ASTM_A105"),
    ("WCB", "ASTM_A216_WCB"),
    ("B7", "ASTM_A193_B7"),
    ("316", "SS316"),
)
METALLURGY_TYPES = [
    (re.compile(rf"(?<![A-Z0-9]){re.escape(name)}(?![A-Z0-9])", re.IGNORECASE), value)
    for name, value in sorted(_METALLURGY_TYPES, key=lambda entry: len(entry[0]), reverse=True)
]
PN_TO_CLASS = {
    6: 150,
    10: 150,
    16: 150,
    25: 300,
    40: 300,
    50: 300,
    63: 600,
    64: 600,
    80: 600,
    100: 600,
    150: 900,
    250: 1500,
    320: 2500,
    420: 2500,
}

_EXTENDED_PATTERNS = {
    "indian_standard": r"\bIS\s*(?:CODE\s*)?[-:]?\s*\d{3,5}(?:\s*[:/-]\s*\d{2,4})?\b",
    "oisd_standard": r"\bOISD(?:\s*[-/]?\s*(?:STD|RP|GDN))?\s*[-:]?\s*\d{1,4}(?:\s*[/.-]\s*\d{2,4})?\b",
    "eil_specification": r"\bEIL(?:\s+(?:SPEC(?:IFICATION)?|STD))?\s*[-:/ ]+\s*[A-Z0-9][A-Z0-9./-]*",
    "gem_category": r"\bGEM\s+CATEGORY(?:\s*(?:ID|CODE))?\s*[:#-]?\s*([A-Z0-9][A-Z0-9./_-]*)",
    "gem_bid_number": r"\bGEM\s+BID\s*(?:NO\.?|NUMBER|ID|#)?\s*[:#-]?\s*([A-Z0-9][A-Z0-9_./-]*)",
    "cppp_tender_id": r"\b(?:CPPP(?:\s+TENDER)?|CENTRAL\s+PUBLIC\s+PROCUREMENT\s+PORTAL)\s*(?:TENDER\s*)?(?:ID|NO\.?)?\s*[:#-]?\s*([A-Z0-9][A-Z0-9_./-]*)",
    "mesc_code": r"\bMESC\s*[-:]?\s*([A-Z0-9][A-Z0-9./-]*)",
    "manufacturer": r"\b(?:MANUFACTURER|MFR\.?|MAKE)\s*[:#-]?\s*(.+?)(?=\s+(?:PRODUCT\s+FORM|COATING|INSPECTION\s+CLASS|TPI|INSPECTION\s+AGENCY|DOCUMENT\s+NO|PROJECT|END\s+CONNECTION|TEMPERATURE|PO\s*[-:]|CERTIFICATE)|$)",
    "product_form": r"\b(?:PRODUCT\s+FORM|FORM)\s*[:#-]?\s*(FORGED|CAST|WROUGHT|SEAMLESS|WELDED|PLATE|BAR|PIPE|TUBE)\b",
    "coating": r"\b(3LPE|3LPP|FBE|EPOXY|GALVANI[ZS]ED|HOT[- ]DIP\s+GALVANI[ZS]ED|PTFE|NYLON|RUBBER[- ]LINED)\b",
    "inspection_class": r"\b(?:INSPECTION|ITP|QC)\s+CLASS\s*[:#-]?\s*([A-Z0-9-]+)",
    "document_number": r"\b(?:DOCUMENT|DOC\.?)\s*(?:NO\.?|NUMBER|#)\s*[:#-]?\s*([A-Z0-9][A-Z0-9_./-]*)",
    "project": r"\bPROJECT\s*[:#-]?\s*(.+?)(?=\s+(?:END\s+CONNECTION|TEMPERATURE|PO\s*[-:]|CERTIFICATE|BID\s*(?:NO|NUMBER))|$)",
    "end_connection": r"\b(FLANGED|BUTT[- ]WELD(?:ED)?|SOCKET[- ]WELD(?:ED)?|THREADED|NPT|BSP)\b",
    "purchase_order": r"\b(?:(?:PURCHASE\s+ORDER|P\.?O\.?)\s*(?:NO\.?|NUMBER|#)?\s*[:#-]?\s*)?(PO[-/][A-Z0-9][A-Z0-9_./-]*)|\b(?:PURCHASE\s+ORDER|P\.?O\.?)\s*(?:NO\.?|NUMBER|#)\s*[:#-]?\s*([A-Z0-9][A-Z0-9_./-]*)",
    "certificate_number": r"\b(?:CERTIFICATE|CERT\.?)\s*(?:(?:NO\.?|NUMBER|#)\s*[:#-]?\s*)?([A-Z0-9][A-Z0-9_./-]*\d[A-Z0-9_./-]*)",
    "bid_number": r"\b(?:BID|TENDER)\s*(?:NO\.?|NUMBER|ID|#)\s*[:#-]?\s*([A-Z0-9][A-Z0-9_./-]*)",
    "inspection_agency": r"\b(?:TPI|INSPECTION\s+AGENCY)\s*[:#-]?\s*([A-Z][A-Z0-9 &.-]+?)(?=\s+(?:INSPECTION\s+CLASS|DOCUMENT\s+NO|PROJECT)|$)",
}


def _first(pattern: str, text: str, flags: int = re.IGNORECASE) -> str | None:
    match = re.search(pattern, text, flags)
    return match.group(1) if match else None


def normalize_size(raw: str) -> float | None:
    match = re.fullmatch(
        r"\s*(?:(?:DN|NB)\s*)?(?P<number>\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)"
        r"\s*(?P<unit>MM|MILLIMETERS?|MILLIMETRES?|IN|INCH(?:ES)?|[\"'])?\s*(?:NB)?\s*",
        raw,
        re.IGNORECASE,
    )
    if not match:
        return None
    number_text = match.group("number").split()
    if len(number_text) == 2:
        whole, fraction = number_text
        numerator, denominator = fraction.split("/")
        if int(denominator) == 0:
            return None
        number = float(whole) + int(numerator) / int(denominator)
    elif "/" in number_text[0]:
        numerator, denominator = number_text[0].split("/")
        if int(denominator) == 0:
            return None
        number = int(numerator) / int(denominator)
    else:
        number = float(number_text[0])
    unit = (match.group("unit") or "").upper()
    return number * 25.4 if unit in {"IN", "INCH", "INCHES", '"', "'"} or "/" in match.group("number") else number


def normalize_pressure(raw: str) -> int | None:
    match = re.search(r"\bPN\s*[-]?\s*(\d+)\b", raw, re.IGNORECASE)
    if match:
        nominal_pressure = int(match.group(1))
        mapped_class = PN_TO_CLASS.get(nominal_pressure)
        if mapped_class is not None:
            return mapped_class
    match = re.search(r"\b(?:CLASS|CL)\s*-?\s*(\d+)\b|\b(\d+)\s*(?:#|LBS?)(?![A-Z])", raw, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1) or match.group(2))


def _normalize_metallurgy(raw: str) -> str | None:
    return next((value for pattern, value in METALLURGY_TYPES if pattern.search(raw)), None)


def _extended_attributes(raw_description: str) -> dict[str, Any]:
    attributes: dict[str, Any] = {}
    for field, pattern in _EXTENDED_PATTERNS.items():
        match = re.search(pattern, raw_description, re.IGNORECASE | re.MULTILINE)
        if match:
            value = next(
                (group for group in match.groups() if group is not None),
                match.group(),
            ).strip(" \t:;,.")
            attributes[field] = value
    temperature = re.search(
        r"\b(?:TEMPERATURE|TEMP\.?)\s*(?:RATING)?\s*[:#-]?\s*(-?\d+(?:\.\d+)?)\s*(?:°?\s*[CF])?\b",
        raw_description,
        re.IGNORECASE,
    )
    if temperature:
        attributes["temperature_rating"] = float(temperature.group(1))
    return attributes


def _regex_attributes(raw_description: str) -> ExtractedMaterialAttributes:
    text = " ".join(raw_description.upper().split())
    size_text = text
    metadata_fields = (
        "indian_standard",
        "oisd_standard",
        "eil_specification",
        "gem_category",
        "gem_bid_number",
        "cppp_tender_id",
        "mesc_code",
        "document_number",
        "purchase_order",
        "certificate_number",
        "bid_number",
    )
    for field in metadata_fields:
        size_text = re.sub(
            _EXTENDED_PATTERNS[field],
            lambda match: " " * len(match.group()),
            size_text,
            flags=re.IGNORECASE,
        )
    size_text = re.sub(
        r"\b(?:ASME|API|ASTM|NACE|BS|DIN|EN|ISO)\s*[A-Z]{0,4}\s*\d+[A-Z]?(?:[./:-]\d+[A-Z0-9]*)*",
        lambda match: " " * len(match.group()),
        size_text,
        flags=re.IGNORECASE,
    )
    size_text = re.sub(
        r"\b(?:CLASS|CL)\s*-?\s*\d+|\bPN\s*-?\s*\d+|\b\d+\s*(?:#|LBS?)(?![A-Z])",
        lambda match: " " * len(match.group()),
        size_text,
        flags=re.IGNORECASE,
    )
    item_type = next(
        (
            value
            for key, value in sorted(ITEM_TYPES.items(), key=lambda item: len(item[0]), reverse=True)
            if re.search(rf"\b{re.escape(key)}\b", text)
        ),
        None,
    )
    facing = next((value for key, value in FACING_TYPES.items() if re.search(rf"\b{re.escape(key)}\b", text)), None)
    grade = _normalize_metallurgy(text)
    normalized_size_mm = re.search(r"\bSIZE_NB_MM\s*=\s*(\d+(?:\.\d+)?)", text)
    normalized_size_in = re.search(r"\bSIZE_IN\s*=\s*(\d+(?:\.\d+)?)", text)
    if normalized_size_mm:
        size_nb_mm = float(normalized_size_mm.group(1))
    elif normalized_size_in:
        size_nb_mm = round(float(normalized_size_in.group(1)) * 25.4, 2)
    else:
        size_raw = _first(
            r"\b((?:(?:DN|NB)\s*)?(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)"
            r"\s*(?:MM|MILLIMETERS?|MILLIMETRES?|IN|INCH(?:ES)?|[\"'])?(?:\s*NB)?)"
            r"(?=\s|$|[,;/)])",
            size_text,
        )
        size_nb_mm = normalize_size(size_raw) if size_raw else None
    normalized_pressure = re.search(r"\bCLASS\s*=\s*(\d+)\b", text)
    pressure_raw = None if normalized_pressure else _first(
        r"\b((?:CLASS|CL)\s*-?\s*\d+|PN\s*-?\s*\d+|\d+\s*(?:#|LBS?))(?=\s|$|[,;/])",
        text,
    )
    standard = _first(
        r"\b((?:ASME|API|ASTM|NACE|BS|DIN|EN|ISO)\s*[A-Z]{0,4}\s*\d+[A-Z]?(?:[./:-]\d+[A-Z0-9]*)*)",
        text,
    )
    return ExtractedMaterialAttributes(
        raw_description=raw_description,
        item_type=item_type,
        size_nb_mm=size_nb_mm,
        pressure_class=(
            int(normalized_pressure.group(1))
            if normalized_pressure
            else normalize_pressure(pressure_raw) if pressure_raw else None
        ),
        metallurgy=grade,
        material_grade=grade,
        facing_end=facing,
        standard=standard.strip() if standard else None,
        **_extended_attributes(raw_description),
    )


class NERTagger:
    def __init__(self, model_path: str | Path = "machine_learning/model_weights/ner_deberta", pipeline: Any = None) -> None:
        self.pipeline = pipeline
        if pipeline is None and Path(model_path).exists():
            try:
                from transformers import pipeline as hf_pipeline
                self.pipeline = hf_pipeline("token-classification", model=str(model_path), tokenizer=str(model_path), aggregation_strategy="simple")
            except (ImportError, OSError):
                self.pipeline = None

    def extract_attributes(self, raw_description: str) -> ExtractedMaterialAttributes:
        attributes = _regex_attributes(raw_description)
        if self.pipeline is None:
            return attributes
        entities = self.pipeline(raw_description)
        by_label = {str(entity.get("entity_group", "")): str(entity.get("word", "")) for entity in entities}
        item_type = by_label.get("ITEM_TYPE")
        size = normalize_size(by_label["SIZE"]) if by_label.get("SIZE") else None
        pressure = normalize_pressure(by_label["PRESSURE_RATING"]) if by_label.get("PRESSURE_RATING") else None
        metallurgy = _normalize_metallurgy(by_label["METALLURGY"]) if by_label.get("METALLURGY") else None
        model_attributes = {
            "indian_standard": by_label.get("INDIAN_STANDARD"),
            "oisd_standard": by_label.get("OISD_STANDARD"),
            "eil_specification": by_label.get("EIL_SPECIFICATION"),
            "gem_category": by_label.get("GEM_CATEGORY"),
            "gem_bid_number": by_label.get("GEM_BID_NUMBER"),
            "cppp_tender_id": by_label.get("CPPP_TENDER_ID"),
            "mesc_code": by_label.get("MESC_CODE"),
            "manufacturer": by_label.get("MANUFACTURER"),
            "product_form": by_label.get("PRODUCT_FORM"),
            "coating": by_label.get("COATING"),
            "inspection_class": by_label.get("INSPECTION_CLASS"),
            "document_number": by_label.get("DOCUMENT_NUMBER"),
            "project": by_label.get("PROJECT"),
            "end_connection": by_label.get("END_CONNECTION"),
            "purchase_order": by_label.get("PURCHASE_ORDER"),
            "certificate_number": by_label.get("CERTIFICATE_NUMBER"),
            "bid_number": by_label.get("BID_NUMBER"),
            "inspection_agency": by_label.get("INSPECTION_AGENCY"),
        }
        if by_label.get("TEMPERATURE_RATING"):
            temperature = re.search(r"-?\d+(?:\.\d+)?", by_label["TEMPERATURE_RATING"])
            model_attributes["temperature_rating"] = float(temperature.group()) if temperature else None
        for name, value in model_attributes.items():
            if value is None:
                model_attributes[name] = getattr(attributes, name)
        for name, value in _extended_attributes(raw_description).items():
            if model_attributes.get(name) is None:
                model_attributes[name] = value
        return attributes.model_copy(
            update={
                "item_type": item_type or attributes.item_type,
                "size_nb_mm": size if size is not None else attributes.size_nb_mm,
                "pressure_class": pressure if pressure is not None else attributes.pressure_class,
                "metallurgy": metallurgy or attributes.metallurgy,
                "material_grade": metallurgy or attributes.material_grade,
                "facing_end": by_label.get("FACING_END") or attributes.facing_end,
                "standard": by_label.get("STANDARD") or attributes.standard,
                **model_attributes,
            }
        )


@lru_cache(maxsize=1)
def _get_default_tagger() -> NERTagger:
    return NERTagger()


def extract_attributes(raw_description: str) -> ExtractedMaterialAttributes:
    return _get_default_tagger().extract_attributes(raw_description)
