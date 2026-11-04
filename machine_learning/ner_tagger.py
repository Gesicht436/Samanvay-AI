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
    "VLV GT": "VALVE",
    "VLV BL": "VALVE",
    "VLV GL": "VALVE",
    "VLV CHK": "VALVE",
    "VLV PSV": "VALVE",
    "VLV": "VALVE",
    "GATE": "GATE_VALVE",
    "BALL": "BALL_VALVE",
    "BOLT": "BOLT",
    "STUD BLT": "STUD_BOLT",
    "STUD BOLT": "STUD_BOLT",
    "STUD": "STUD_BOLT",
    "CHECK VALVE": "CHECK_VALVE",
    "NRV": "CHECK_VALVE",
    "BUTTERFLY VALVE": "BUTTERFLY_VALVE",
    "PIPE": "PIPE",
    "TUBE": "TUBE",
    "GASKET": "GASKET",
    "TEE": "TEE",
    "ELBOW": "ELBOW",
    "REDUCER": "REDUCER",
}
FACING_TYPES = {
    "WN": "WELD_NECK",
    "WNRF": "WELD_NECK_RAISED_FACE",
    "RF": "RAISED_FACE",
    "RTJ": "RING_TYPE_JOINT",
    "BW": "BUTT_WELD",
    "SW": "SOCKET_WELD",
    "FF": "FLAT_FACE",
}
_METALLURGY_TYPES = (
    ("A105N", "ASTM_A105N"),
    ("AISI 316", "SS316"),
    ("SS316", "SS316"),
    ("316L", "SS316L"),
    ("A105", "ASTM_A105"),
    ("WCB", "ASTM_A216_WCB"),
    ("B7", "ASTM_A193_B7"),
    ("316", "SS316"),
    ("IS 2062", "IS_2062"),
    ("IS2062", "IS_2062"),
    ("LF2", "ASTM_A350_LF2"),
    ("LF-2", "ASTM_A350_LF2"),
    ("A350 LF2", "ASTM_A350_LF2"),
    ("INCONEL 625", "INCONEL_625"),
    ("HASTELLOY C-276", "HASTELLOY_C276"),
    ("DUPLEX", "DUPLEX_SS"),
    ("SUPER DUPLEX", "SUPER_DUPLEX_SS"),
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


class DialectNormalizer:
    """Drop-in normalizer delegating to Hariom's OCR text normalizer and NER tagger."""

    def __init__(self):
        pass

    def normalize(self, query_text: str) -> dict[str, Any]:
        import re
        from OCR.normalization import normalize_text
        norm_text = normalize_text(query_text)
        extracted = extract_attributes(norm_text)
        data = extracted.model_dump()
        u = query_text.upper()

        item_type = data.get("item_type")
        if "STUD" in u or "BOLT" in u:
            item_type = "STUD_BOLT"
        elif "FLG" in u or "FLANGE" in u:
            item_type = "FLANGE"
        elif "PIPE" in u:
            item_type = "PIPE"
        elif "VLV" in u or "VALVE" in u:
            item_type = "VALVE"

        # Size NB
        size_nb = data.get("size_nb_mm")
        m_nb = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:MM\s+NB|NB)\b', u)
        if m_nb:
            size_nb = float(m_nb.group(1))
        else:
            m_in = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:IN|INCH(?:ES)?|")\b', u)
            if m_in:
                val = float(m_in.group(1))
                inch_to_nb = {
                    0.5: 15.0, 0.75: 20.0, 1.0: 25.0, 1.25: 32.0, 1.5: 40.0,
                    2.0: 50.0, 2.5: 65.0, 3.0: 80.0, 4.0: 100.0, 5.0: 125.0,
                    6.0: 150.0, 8.0: 200.0, 10.0: 250.0, 12.0: 300.0,
                    14.0: 350.0, 16.0: 400.0, 18.0: 450.0, 20.0: 500.0, 24.0: 600.0,
                }
                if val in inch_to_nb:
                    size_nb = inch_to_nb[val]

        # PN and Pressure
        m_pn = re.search(r'\bPN\s*(\d+(?:\.\d+)?)\b', u)
        pressure_bar = float(m_pn.group(1)) if m_pn else None

        m_class = re.search(r'\((\d+)[#]\)', u) or re.search(r'\bCLASS\s*(\d+)\b', u) or re.search(r'\b(\d+)\s*#\b', u)
        pressure_class = int(m_class.group(1)) if m_class else data.get("pressure_class")
        if not pressure_class and pressure_bar:
            pn_map = {10: 150, 16: 150, 20: 150, 25: 150, 40: 300, 50: 300, 100: 600, 160: 900, 250: 1500, 420: 2500}
            pressure_class = pn_map.get(int(pressure_bar), int(pressure_bar * 6))

        # MESC Code (4 parts, e.g. 03.10.45.19)
        mesc = data.get("mesc_code")
        oil_mat_code = None
        if mesc:
            parts = str(mesc).split(".")
            oil_mat_code = ".".join(parts[:4]) if len(parts) >= 4 else str(mesc)
        else:
            m_mesc = re.search(r'\b(\d{2}\.\d{2}\.\d{2}\.\d{2})(?:\.\d{2})?\b', u)
            if m_mesc:
                oil_mat_code = m_mesc.group(1)

        # IS Standard
        indian_standard = data.get("indian_standard")
        if not indian_standard or "IS" not in str(indian_standard):
            m_is = re.search(r'\b(IS\s+\d+(?:\s+Part\s+\d+)?(?:\s+Grade\s+[A-Z0-9]+)?)\b', u, re.IGNORECASE)
            if m_is:
                indian_standard = m_is.group(1)

        # OISD / EIL
        specs = []
        if data.get("oisd_standard"):
            specs.append(data["oisd_standard"])
        if data.get("eil_specification"):
            specs.append(data["eil_specification"])
        oil_std_spec = " / ".join(specs) if specs else None
        if not oil_std_spec:
            m_oil_spec = re.search(r'\b(OISD-[A-Z0-9-]+(?:\s*/\s*EIL\s*[0-9A-Z-]+)?|EIL\s*[0-9A-Z-]+)\b', u, re.IGNORECASE)
            if m_oil_spec:
                oil_std_spec = m_oil_spec.group(1)

        # MII
        m_mii = re.search(r'\b(Class-I|Class-II|Non-Local)\b', u, re.IGNORECASE)
        mii = m_mii.group(1) if m_mii else "Class-I"
        if mii.lower() == "class-i":
            mii = "Class-I"
        elif mii.lower() == "class-ii":
            mii = "Class-II"

        return {
            **data,
            "raw_description": query_text,
            "normalized_text": norm_text,
            "item_type": item_type,
            "size_nb_mm": size_nb,
            "pressure_class": pressure_class,
            "pressure_rating_bar": pressure_bar,
            "oil_material_code": oil_mat_code,
            "indian_standard": indian_standard,
            "oil_std_spec": oil_std_spec,
            "make_in_india_class": mii,
            "metallurgy": data.get("metallurgy") or data.get("material_grade"),
            "facing_end": data.get("facing_end") or data.get("end_connection"),
            "standard": data.get("standard"),
            "schedule": data.get("schedule"),
            "sour_service": bool("NACE" in u or "SOUR" in u),
        }


def extract_metadata_from_dialect(raw_description: str) -> dict[str, Any]:
    normalizer = DialectNormalizer()
    return normalizer.normalize(raw_description)
