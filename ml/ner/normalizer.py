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
    "SLUICE VALVE": "GATE VALVE",
    "SLUICE VLV": "GATE VALVE",
    "MS TUBE": "PIPE",
    "MS PIPE": "PIPE",
    "GI PIPE": "PIPE",
    "ERW PIPE": "PIPE",
    "SEAMLESS PIPE": "PIPE",
    "FE 410": "IS 3589 FE 410",
    "FE 450": "IS 3589 FE 450",
    "E250": "IS 2062 E250",
    "E350": "IS 2062 E350",
    "FG 200": "IS 14846 FG 200",
    "FG 260": "IS 14846 FG 260",
    "MII CLASS 1": "CLASS-I",
    "MII CLASS 2": "CLASS-II",
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
    """Extract attributes from normalized text including Indian standards and procurement metadata."""
    meta = {
        "item_type": None,
        "metallurgy": None,
        "temp_service": None,
        "pressure_class": None,
        "pressure_rating_bar": None,
        "size_nb_mm": None,
        "facing_end": None,
        "indian_standard": None,
        "oil_std_spec": None,
        "oil_material_code": None,
        "gem_category_id": None,
        "cppp_tender_ref": None,
        "make_in_india_class": None,
    }

    # Item Type extractions
    if "VALVE" in text or "VLV" in text or "NRV" in text or "BFV" in text:
        meta["item_type"] = "VALVE"
    elif "FLANGE" in text or "FLG" in text or "WNRF" in text:
        meta["item_type"] = "FLANGE"
    elif "BLIND" in text:
        meta["item_type"] = "BLIND"
    elif "PIPE" in text:
        meta["item_type"] = "PIPE"
    elif "STUD" in text or "BOLT" in text:
        meta["item_type"] = "STUD_BOLT"
    elif "GASKET" in text or "GSKT" in text:
        meta["item_type"] = "GASKET"
    elif "ELBOW" in text or "TEE" in text or "REDUCER" in text or "FITTING" in text:
        meta["item_type"] = "FITTING"
    elif "PUMP" in text:
        meta["item_type"] = "PUMP_SPARE"

    # Indian Standard (BIS / IS)
    match_is = re.search(r'\b(IS\s*(?:1239|3589|2062|14846|13095|5312|778|1367|1363|9890|6392)(?:\s*(?:PART|PT)\.?\s*\d+)?)\b', text, re.IGNORECASE)
    if match_is:
        meta["indian_standard"] = match_is.group(1).strip()

    # OISD & EIL Standards
    match_oisd = re.search(r'\b(OISD[\-\s]*(?:STD[\-\s]*|RP[\-\s]*)?(?:118|141|126|179|166))\b', text, re.IGNORECASE)
    match_eil = re.search(r'\b(EIL[\-\s]*(?:6\-44\-)?(?:0005|0012|0001))\b', text, re.IGNORECASE)
    if match_oisd and match_eil:
        meta["oil_std_spec"] = f"{match_oisd.group(1)} / {match_eil.group(1)}"
    elif match_oisd:
        meta["oil_std_spec"] = match_oisd.group(1)
    elif match_eil:
        meta["oil_std_spec"] = match_eil.group(1)

    # OIL SAP MESC Code (8-digit)
    match_oil_code = re.search(r'\b(0[1-6]\.\d{2}\.\d{2}\.\d{2})\b', text)
    if match_oil_code:
        meta["oil_material_code"] = match_oil_code.group(1)

    # GeM Category ID
    match_gem = re.search(r'\b(GEM\/(?:CAT|OIL)\/[A-Z0-9_\/]+)\b', text, re.IGNORECASE)
    if match_gem:
        meta["gem_category_id"] = match_gem.group(1)

    # CPPP Tender Reference
    match_cppp = re.search(r'\b(202\d_[A-Z0-9]+_\d+_\d|OIL\/[A-Z0-9\/]+)\b', text, re.IGNORECASE)
    if match_cppp:
        meta["cppp_tender_ref"] = match_cppp.group(1)

    # Make in India Class
    if "CLASS-I" in text or "CLASS 1" in text or "MAKE IN INDIA" in text:
        meta["make_in_india_class"] = "Class-I"
    elif "CLASS-II" in text or "CLASS 2" in text:
        meta["make_in_india_class"] = "Class-II"
    elif "NON-LOCAL" in text:
        meta["make_in_india_class"] = "Non-Local"

    # Metallurgy
    if "IS 2062" in text or "E250" in text or "E350" in text:
        meta["metallurgy"] = "IS 2062 E250 / ASTM A105"
    elif "IS 1239" in text:
        meta["metallurgy"] = "IS 1239 / ASTM A106"
    elif "IS 3589" in text or "FE 410" in text or "FE 450" in text:
        meta["metallurgy"] = "IS 3589 FE 410 / API 5L"
    elif "IS 14846" in text or "FG 200" in text or "FG 260" in text:
        meta["metallurgy"] = "IS 14846 FG 200 / WCB"
    elif "IS 1367" in text:
        meta["metallurgy"] = "IS 1367 CL 8.8 / ASTM A193 B7"
    elif "A105" in text:
        meta["metallurgy"] = "ASTM A105"
    elif "LF2" in text or "A350" in text:
        meta["metallurgy"] = "ASTM A350 LF2"
    elif "WCB" in text or "A216" in text:
        meta["metallurgy"] = "ASTM A216 WCB"
    elif "LCB" in text or "A352" in text:
        meta["metallurgy"] = "ASTM A352 LCB"
    elif "A106" in text:
        meta["metallurgy"] = "ASTM A106 GR.B"
    elif "A333" in text:
        meta["metallurgy"] = "ASTM A333 GR.6"
    elif "A234" in text or "WPB" in text:
        meta["metallurgy"] = "ASTM A234 WPB"
    elif "A420" in text or "WPL6" in text:
        meta["metallurgy"] = "ASTM A420 WPL6"
    elif "B7" in text and ("A193" in text or "STUD" in text or "BOLT" in text):
        meta["metallurgy"] = "ASTM A193 B7"
    elif "B16" in text and ("A193" in text or "STUD" in text or "BOLT" in text):
        meta["metallurgy"] = "ASTM A193 B16"
    elif "L7" in text and ("A320" in text or "STUD" in text or "BOLT" in text):
        meta["metallurgy"] = "ASTM A320 L7"
    elif "B8M" in text:
        meta["metallurgy"] = "ASTM A193 B8M"
    elif "B7M" in text:
        meta["metallurgy"] = "ASTM A193 B7M"
    elif "F316" in text or "CF8M" in text or "TP316" in text or "SS316" in text:
        meta["metallurgy"] = "ASTM A182 F316"
    elif "F304" in text or "TP304" in text or "SS304" in text:
        meta["metallurgy"] = "ASTM A182 F304"
    elif "F53" in text or "SUPER DUPLEX" in text:
        meta["metallurgy"] = "ASTM A182 F53"
    elif "F51" in text or "DUPLEX" in text:
        meta["metallurgy"] = "ASTM A182 F51"
    elif "API 5L" in text or "API5L" in text:
        m = re.search(r'API\s*5L\s*(?:X\d+|GR\.?[A-Z0-9]+)?', text)
        meta["metallurgy"] = m.group(0) if m else "API 5L GR.B"
    elif "ASTM" in text or "STEEL" in text or "INCONEL" in text or "HASTELLOY" in text:
        m = re.search(r'(?:ASTM\s+[A-Z0-9]+(?:\s+[A-Z0-9]+)?|INCONEL\s+\w+|HASTELLOY\s+\w+|STAINLESS\s+STEEL|CARBON\s+STEEL)', text)
        meta["metallurgy"] = m.group(0) if m else text[:60]

    # Pressure Class & Bar (PN)
    match_class = re.search(r'(?:CLASS|#)\s*(\d+)|(\d+)\s*#', text)
    if match_class:
        meta["pressure_class"] = match_class.group(1) or match_class.group(2)

    match_pn = re.search(r'PN\s*(\d+)', text)
    if match_pn:
        pn_val = int(match_pn.group(1))
        meta["pressure_rating_bar"] = float(pn_val)
        pn_map = {10: 150, 16: 150, 20: 150, 25: 300, 40: 300, 50: 300, 64: 600, 100: 600, 150: 900, 250: 1500, 420: 2500}
        if not meta["pressure_class"]:
            meta["pressure_class"] = str(pn_map.get(pn_val, pn_val))

    # Size: NB mm, mm, DN, M-thread, or inches
    match_nb = re.search(r'(\d+(?:\.\d+)?)\s*(?:MM)?\s*NB\b|\bNB\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if match_nb:
        nb_val = match_nb.group(1) or match_nb.group(2)
        meta["size_nb_mm"] = str(float(nb_val))
    else:
        match_size = re.search(r'(\d+\.?\d*)\s*mm', text, re.IGNORECASE)
        if match_size:
            meta["size_nb_mm"] = match_size.group(1)
        else:
            match_dn = re.search(r'\bDN\s*(\d+)\b', text)
            if match_dn:
                meta["size_nb_mm"] = str(float(match_dn.group(1)))
            else:
                match_m = re.search(r'\bM(\d+)\b', text)
                if match_m:
                    meta["size_nb_mm"] = str(float(match_m.group(1)))
                else:
                    match_frac = re.search(r'(\d+)/(\d+)\s*(?:IN|INCH|")', text, re.IGNORECASE)
                    if match_frac:
                        num, den = float(match_frac.group(1)), float(match_frac.group(2))
                        meta["size_nb_mm"] = str(round((num / den) * 25.4, 1))
                    else:
                        match_inch = re.search(r'(\d+\.?\d*)\s*(?:IN|INCH|")', text, re.IGNORECASE)
                        if match_inch:
                            inches = float(match_inch.group(1))
                            meta["size_nb_mm"] = str(inches * 25.4)

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
        raw_pn = re.search(r'PN\s*(\d+)', raw_text, re.IGNORECASE)
        normalized_text = normalize_description(raw_text)
        metadata = extract_metadata_from_dialect(normalized_text)
        metadata["normalized_description"] = normalized_text
        if raw_pn and not metadata.get("pressure_rating_bar"):
            metadata["pressure_rating_bar"] = float(raw_pn.group(1))
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
        if metadata.get("pressure_rating_bar"):
            try:
                metadata["pressure_rating_bar"] = float(metadata["pressure_rating_bar"])
            except (ValueError, TypeError):
                pass
        return metadata

    normalize_description = normalize
