import unicodedata
import re

DIALECT_THESAURUS = {
    "NRV": "CHECK VALVE",
    "NON RETURN VLV": "CHECK VALVE",
    "CHK VLV": "CHECK VALVE",
    "BFV": "BUTTERFLY VALVE",
    "BFLY VLV": "BUTTERFLY VALVE",
    "SPRF": "SPECTACLE BLIND RF",
    "SP BLIND": "SPECTACLE BLIND RF",
    "SPEC BLIND": "SPECTACLE BLIND RF",
    "FLG": "FLANGE",
    "WNRF": "WELD NECK RF FLANGE",
    "WN": "WELD NECK",
    "LTCS": "ASTM A350 LF2",
    "LF-2": "ASTM A350 LF2",
    "A-350 LF2": "ASTM A350 LF2",
    "A105": "ASTM A105",
    "A-105": "ASTM A105",
    "DSS": "DUPLEX STAINLESS STEEL",
    "UNS S31803": "DUPLEX STAINLESS STEEL",
    "F51": "DUPLEX STAINLESS STEEL",
    "SDSS": "SUPER DUPLEX STAINLESS",
    "UNS S32750": "SUPER DUPLEX STAINLESS",
    "F53": "SUPER DUPLEX STAINLESS",
    "INCO 625": "INCONEL 625",
    "ALLOY 625": "INCONEL 625",
    "HAST-C": "HASTELLOY C-276",
    "C-276": "HASTELLOY C-276",
    "PN 20": "CLASS 150",
    "PN 50": "CLASS 300",
    "PN 100": "CLASS 600",
    "150#": "CLASS 150",
    "300#": "CLASS 300",
    "600#": "CLASS 600",
    "900#": "CLASS 900",
    "1500#": "CLASS 1500",
    "2500#": "CLASS 2500",
    "4IN": "100.0 mm",
    '4"': "100.0 mm",
    "4 INCH": "100.0 mm",
    "DN100": "100.0 mm",
}


def unicode_normalize(text: str) -> str:
    """Apply NFKC normalization"""
    return unicodedata.normalize("NFKC", text)


def normalize_description(raw_text: str) -> str:
    """Apply NFKC + thesaurus replacement"""
    text = unicode_normalize(raw_text).upper()
    for k, v in sorted(DIALECT_THESAURUS.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(r'\b' + re.escape(k) + r'\b')
        text = pattern.sub(v, text)
        if k == '4"':
            text = text.replace('4"', '100.0 mm')
        if "#" in k:
            text = text.replace(k, v)
    return text


def extract_metadata_from_dialect(text: str) -> dict:
    """Extract attributes from normalized text."""
    meta = {
        "item_type": None,
        "metallurgy": None,
        "temp_service": None,
        "pressure_class": None,
        "size_nb_mm": None,
        "facing_end": None,
    }

    # Item Type extractions
    if "FLANGE" in text or "FLG" in text or "WNRF" in text:
        meta["item_type"] = "FLANGE"
    elif "VALVE" in text:
        meta["item_type"] = "VALVE"
    elif "BLIND" in text:
        meta["item_type"] = "BLIND"
    elif "PIPE" in text:
        meta["item_type"] = "PIPE"

    # Metallurgy
    if "A105" in text or "ASTM A105" in text:
        meta["metallurgy"] = "ASTM A105"
    elif "LF2" in text or "A350" in text:
        meta["metallurgy"] = "ASTM A350 LF2"
    elif "F316" in text or "CF8M" in text:
        meta["metallurgy"] = "ASTM A182 F316"
    elif "ASTM" in text or "STEEL" in text or "INCONEL" in text or "HASTELLOY" in text:
        meta["metallurgy"] = text

    # Pressure Class
    match_class = re.search(r'(?:CLASS|#)\s*(\d+)|(\d+)\s*#', text)
    if match_class:
        meta["pressure_class"] = match_class.group(1) or match_class.group(2)

    # Size
    match_size = re.search(r'(\d+\.?\d*)\s*mm', text, re.IGNORECASE)
    if match_size:
        meta["size_nb_mm"] = match_size.group(1)
    else:
        match_inch = re.search(r'(\d+)\s*(?:IN|INCH|")', text, re.IGNORECASE)
        if match_inch:
            inches = float(match_inch.group(1))
            meta["size_nb_mm"] = str(inches * 25.0)

    # Facing
    if "RF" in text:
        meta["facing_end"] = "RF"
    elif "RTJ" in text:
        meta["facing_end"] = "RTJ"

    return meta


class DialectNormalizer:
    """Class wrapper for dialect normalization and slot extraction."""

    def __init__(self, thesaurus=None):
        self.thesaurus = thesaurus or DIALECT_THESAURUS

    def normalize(self, raw_text: str) -> dict:
        normalized_text = normalize_description(raw_text)
        metadata = extract_metadata_from_dialect(normalized_text)
        metadata["normalized_description"] = normalized_text
        if metadata.get("size_nb_mm"):
            try:
                metadata["size_nb_mm"] = float(metadata["size_nb_mm"])
            except (ValueError, TypeError):
                pass
        if metadata.get("pressure_class"):
            try:
                metadata["pressure_class"] = int(metadata["pressure_class"])
            except (ValueError, TypeError):
                pass
        return metadata
