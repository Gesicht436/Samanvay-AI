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
    "LTCS": "ASTM A350 LF2",
    "LF-2": "ASTM A350 LF2",
    "A-350 LF2": "ASTM A350 LF2",
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
    "4IN": "100.0 mm",
    '4"': "100.0 mm",
    "4 INCH": "100.0 mm",
    "DN100": "100.0 mm"
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
    return text

def extract_metadata_from_dialect(text: str) -> dict:
    """Extract attributes from normalized text."""
    meta = {
        "item_type": None,
        "metallurgy": None,
        "temp_service": None,
        "pressure_class": None,
        "size_nb_mm": None,
        "facing_end": None
    }
    
    # Very basic regex extractions for metadata
    if "VALVE" in text:
        meta["item_type"] = "VALVE"
    elif "BLIND" in text:
        meta["item_type"] = "BLIND"
    elif "FLANGE" in text:
        meta["item_type"] = "FLANGE"
        
    if "ASTM" in text or "STEEL" in text or "INCONEL" in text or "HASTELLOY" in text:
        meta["metallurgy"] = text
        
    match_class = re.search(r'CLASS (\d+)', text)
    if match_class:
        meta["pressure_class"] = match_class.group(1)
        
    match_size = re.search(r'(\d+\.?\d*) mm', text)
    if match_size:
        meta["size_nb_mm"] = match_size.group(1)
        
    if "RF" in text:
        meta["facing_end"] = "RF"
    elif "RTJ" in text:
        meta["facing_end"] = "RTJ"
        
    return meta
