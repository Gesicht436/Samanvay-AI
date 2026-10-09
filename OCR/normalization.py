"""Canonicalize OCR text without changing the source document."""

import re

_ABBREVIATIONS = {
    "FLG": "FLANGE",
    "FL": "FLANGE",
    "BL FLG": "BLIND FLANGE",
    "SO FLG": "SLIP-ON FLANGE",
    "WN FLG": "WELD NECK FLANGE",
    "VLV": "VALVE",
    "V/V": "VALVE",
    "GV": "GATE VALVE",
    "GT VLV": "GATE VALVE",
    "BV": "BALL VALVE",
    "GLV": "GLOBE VALVE",
    "WNRF": "WELD NECK RAISED FACE",
    "WN": "WELD NECK",
    "RF": "RAISED FACE",
    "FF": "FLAT FACE",
    "RTJ": "RING TYPE JOINT",
    "BW": "BUTT WELD",
    "SW": "SOCKET WELD",
    "THD": "THREADED",
    "NPT": "NATIONAL PIPE THREAD",
    "BSP": "BRITISH STANDARD PIPE",
    "CS": "CARBON STEEL",
    "MS": "MILD STEEL",
    "SS": "STAINLESS STEEL",
    "CI": "CAST IRON",
    "DI": "DUCTILE IRON",
    "GI": "GALVANIZED IRON",
    "HDG": "HOT DIP GALVANIZED",
    "SMLS": "SEAMLESS",
    "ERW": "ELECTRIC RESISTANCE WELDED",
    "SAW": "SUBMERGED ARC WELDED",
    "SCH": "SCHEDULE",
    "MOC": "MATERIAL OF CONSTRUCTION",
    "MTC": "MATERIAL TEST CERTIFICATE",
    "TC": "TEST CERTIFICATE",
    "HT": "HEAT TREATMENT",
    "PMI": "POSITIVE MATERIAL IDENTIFICATION",
    "NACE": "NACE INTERNATIONAL",
    "BIS": "BUREAU OF INDIAN STANDARDS",
    "ISI": "INDIAN STANDARDS INSTITUTION",
    "OISD": "OIL INDUSTRY SAFETY DIRECTORATE",
    "EIL": "ENGINEERS INDIA LIMITED",
    "GEM": "GOVERNMENT E-MARKETPLACE",
    "CPPP": "CENTRAL PUBLIC PROCUREMENT PORTAL",
    "MESC": "MATERIAL ENGINEERING SPECIFICATION",
    "CPWD": "CENTRAL PUBLIC WORKS DEPARTMENT",
    "IOCL": "INDIAN OIL CORPORATION",
    "ONGC": "OIL AND NATURAL GAS CORPORATION",
    "BPCL": "BHARAT PETROLEUM",
    "HPCL": "HINDUSTAN PETROLEUM",
    "RIL": "RELIANCE INDUSTRIES",
    "TPI": "THIRD PARTY INSPECTION",
    "ITP": "INSPECTION AND TEST PLAN",
    "QAP": "QUALITY ASSURANCE PLAN",
    "WPS": "WELDING PROCEDURE SPECIFICATION",
    "PQR": "PROCEDURE QUALIFICATION RECORD",
    "UT": "ULTRASONIC TESTING",
    "RT": "RADIOGRAPHIC TESTING",
    "MT": "MAGNETIC PARTICLE TESTING",
    "PT": "DYE PENETRANT TESTING",
    "WO": "WORK ORDER",
    "QTY": "QUANTITY",
    "MFR": "MANUFACTURER",
    "MFG": "MANUFACTURING",
    "OD": "OUTSIDE DIAMETER",
    "ID": "INSIDE DIAMETER",
    "NB": "NOMINAL BORE",
    "DN": "NOMINAL DIAMETER",
    "P&ID": "PIPING AND INSTRUMENTATION DIAGRAM",
    "P&F": "PROCESS AND FLOW",
    "FBE": "FUSION BONDED EPOXY",
    "3LPE": "THREE LAYER POLYETHYLENE",
    "3LPP": "THREE LAYER POLYPROPYLENE",
    "API": "AMERICAN PETROLEUM INSTITUTE",
    "ASME": "AMERICAN SOCIETY OF MECHANICAL ENGINEERS",
    "ASTM": "AMERICAN SOCIETY FOR TESTING AND MATERIALS",
    "ANSI": "AMERICAN NATIONAL STANDARDS INSTITUTE",
    "AISI": "AMERICAN IRON AND STEEL INSTITUTE",
}
DIALECT_THESAURUS = _ABBREVIATIONS


def normalize_text(text: str) -> str:
    """Normalize common OCR variants and procurement / engineering shorthand."""
    normalized = text.replace("\u00d7", "x").replace("\u2033", '"').replace("\u2019", "'")
    normalized = re.sub(
        r"(?<![A-Z0-9])DN\s*(\d+(?:\.\d+)?)\b",
        r"SIZE_NB_MM=\1",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"(?<![A-Z0-9])(\d+(?:\.\d+)?)\s*(?:mm|millimet(?:er|re)s?)\b",
        r"SIZE_NB_MM=\1",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"(?<![A-Z0-9])(\d+(?:\.\d+)?)\s*(?:in|inch(?:es)?)\b",
        r"SIZE_IN=\1",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"(?<![A-Z0-9])(\d+)\s*#|#\s*(\d+)\b",
        lambda match: f" CLASS={match.group(1) or match.group(2)}",
        normalized,
    )
    normalized = re.sub(
        r"(?<![A-Z0-9])(?:CLASS|CL)\s*-?\s*(\d+)\b",
        r"CLASS=\1",
        normalized,
        flags=re.IGNORECASE,
    )
    for abbreviation, expanded in sorted(_ABBREVIATIONS.items(), key=lambda item: len(item[0]), reverse=True):
        normalized = re.sub(
            rf"(?<![A-Z0-9_]){re.escape(abbreviation)}(?![A-Z0-9_])",
            expanded,
            normalized,
            flags=re.IGNORECASE,
        )
    normalized = re.sub(r"[ \t]+", " ", normalized)
    return "\n".join(line.strip() for line in normalized.splitlines() if line.strip()).strip()
