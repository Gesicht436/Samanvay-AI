"""
Slot-Filling NER and Feature Engineering Attribute Normalizer.
Converts messy, abbreviated CPSE procurement descriptions across IOCL, ONGC, and BPCL
into standardized Pydantic ExtractedMaterialAttributes schemas.

Performance optimizations applied:
  - All regex patterns are compiled once at module load time (not per-call).
  - Thesaurus expansion patterns are also pre-compiled at import.
  - Results are cached with functools.lru_cache to avoid redundant work in bulk jobs.
  - Text normalization (unicode, whitespace, special chars) runs before regex matching.
  - Thesaurus expansion runs before item-type detection so canonical terms are matched.
"""

import re
import unicodedata
import logging
from functools import lru_cache
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from backend.app.contracts.material import ExtractedMaterialAttributes, ItemType, FacingEnd
from backend.app.matching.asme_rules import normalize_metallurgy
from backend.app.config import settings

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# 1. Physical Unit Conversion Dictionaries
# -----------------------------------------------------------------------------

INCH_TO_MM: Dict[str, float] = {
    "1/2": 15.0,
    "0.5": 15.0,
    "3/4": 20.0,
    "0.75": 20.0,
    "1": 25.0,
    "1.0": 25.0,
    "1.25": 32.0,
    "1 1/4": 32.0,
    "1.5": 40.0,
    "1 1/2": 40.0,
    "2": 50.0,
    "2.0": 50.0,
    "2.5": 65.0,
    "2 1/2": 65.0,
    "3": 80.0,
    "3.0": 80.0,
    "4": 100.0,
    "4.0": 100.0,
    "6": 150.0,
    "6.0": 150.0,
    "8": 200.0,
    "8.0": 200.0,
    "10": 250.0,
    "10.0": 250.0,
    "12": 300.0,
    "12.0": 300.0,
    "14": 350.0,
    "16": 400.0,
    "18": 450.0,
    "20": 500.0,
    "24": 600.0,
}

MM_TO_INCH: Dict[float, str] = {
    15.0: '1/2"',
    20.0: '3/4"',
    25.0: '1"',
    40.0: '1.5"',
    50.0: '2"',
    65.0: '2.5"',
    80.0: '3"',
    100.0: '4"',
    150.0: '6"',
    200.0: '8"',
    250.0: '10"',
    300.0: '12"',
}

# Metric Pressure (PN) to ASME Class mapping
PN_TO_CLASS: Dict[int, int] = {
    20: 150,
    50: 300,
    100: 600,
    150: 900,
    250: 1500,
    420: 2500,
}


# -----------------------------------------------------------------------------
# 1b. Refinery Dialect & Shorthand Expansion Thesaurus
#     Patterns are pre-compiled once here (not on each function call).
# -----------------------------------------------------------------------------

# Each entry: (compiled_pattern, replacement_string)
_THESAURUS_RAW: List[Tuple[str, str]] = [
    (r"\bNRV\b",            "CHECK VALVE"),
    (r"\bBFV\b",            "BUTTERFLY VALVE"),
    (r"\bGV\b",             "GATE VALVE"),
    (r"\bGLV\b",            "GLOBE VALVE"),
    (r"\bPLUG\s*VLV\b",     "PLUG VALVE"),
    (r"\bSPRF\b",           "SPECTACLE BLIND RF"),
    (r"\bTHRF\b",           "THREADED FLANGE RF"),
    (r"\bLTCS\b",           "LTCS ASTM A350 LF2"),
    (r"\bDSS\b",            "DUPLEX STAINLESS STEEL F51"),
    (r"\bSDSS\b",           "SUPER DUPLEX STAINLESS STEEL S32750"),
    (r"\bINCO\s*625\b",     "INCONEL 625"),
    (r"\bHAST-C\b",         "HASTELLOY C-276"),
    (r"\bMONEL\s*400\b",    "MONEL 400"),
    (r"\bIBR\b",            "IBR"),          # Keep IBR in place; just normalizes spacing
    (r"\bPSV\b",            "PRESSURE SAFETY VALVE"),
    (r"\bSRV\b",            "PRESSURE SAFETY VALVE"),
    (r"\bRV\b",             "PRESSURE RELIEF VALVE"),
    (r"\bCONTROL\s*VLV\b",  "CONTROL VALVE"),
    (r"\bCV\b",             "CONTROL VALVE"),
    (r"\bRED(?:UCER)?\b",   "REDUCER"),
]

REFINERY_THESAURUS: List[Tuple[re.Pattern, str]] = [
    (re.compile(pat, re.IGNORECASE), repl)
    for pat, repl in _THESAURUS_RAW
]


def expand_refinery_thesaurus(text: str) -> str:
    """
    Expands common CPSE refinery dialect shorthand terms and acronyms across
    IOCL, ONGC, and BPCL into standardized terminology.

    All patterns are pre-compiled at module load time, so this function
    simply applies them in sequence without any re.compile overhead.
    """
    if not text:
        return ""
    expanded = text
    for pattern, replacement in REFINERY_THESAURUS:
        expanded = pattern.sub(replacement, expanded)
    return expanded


# -----------------------------------------------------------------------------
# 1c. Text Normalization
#     Runs before all other processing to ensure consistent tokenization.
# -----------------------------------------------------------------------------

# Collapse multiple spaces / tabs / newlines into a single space
_RE_MULTI_SPACE = re.compile(r"[\s\t\r\n]+")
# Remove non-printable control characters (except normal whitespace)
_RE_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def normalize_text(raw: str) -> str:
    """
    Pre-processing step applied before regex matching:
      1. Strip leading/trailing whitespace.
      2. Normalize unicode (NFKC): converts fullwidth, ligatures, etc. to ASCII equivalents.
      3. Remove non-printable control characters.
      4. Collapse multiple consecutive whitespace into a single space.
      5. Convert to uppercase so all downstream patterns can use re.IGNORECASE without overhead.
    """
    if not raw:
        return ""
    # Normalize unicode (e.g. \u2019 -> ', \uff14 -> 4, \u00b5 -> u)
    s = unicodedata.normalize("NFKC", raw)
    s = _RE_CONTROL_CHARS.sub(" ", s)
    s = _RE_MULTI_SPACE.sub(" ", s).strip()
    return s.upper()


# -----------------------------------------------------------------------------
# 2. Pre-Compiled Regular Expression Extraction Heuristics
#    Compiling here (module load) means zero re.compile overhead per request.
# -----------------------------------------------------------------------------

# Each item in RE_ITEM_TYPES: (compiled_pattern, ItemType_value_string)
_ITEM_TYPE_RAW: List[Tuple[str, str]] = [
    # -- Flanges (most specific first) -----------------------------------------
    (r"\b(FLG[-\s]?BL(?:D|RF|RTJ)?|BLIND\s*FLANGE|FLANGE[,\s]*BLIND|BLD\s*FLG|BLRF|BLRTJ|BLRTI|BLIND\s*CLASS|BLIND|SPRF|SPECTACLE\s*BLIND|SPEC\s*BLD|FIG(?:URE)?[-\s]?8)\b",
     ItemType.FLANGE_BLIND.value),

    (r"\b(FLG[-\s]?SO(?:RF|RTJ)?|SLIP[-\s]?ON\s*FLANGE|FLANGE[,\s]*SLIP[-\s]?ON|SO\s*FLG|SORF|SLIP\s*ON|THRF|THREADED\s*FLANGE)\b",
     ItemType.FLANGE_SLIP_ON.value),

    (r"\b(FLG[-\s]?WN(?:RF|RTJ)?|WELD(?:ING)?\s*NECK\s*FLANGE|FLANGE[,\s]*WELD(?:ING)?\s*NECK|WNRF|WNRTJ|WELD(?:ING)?\s*NECK|WN\s*FLG|WN\s*FIG)\b",
     ItemType.FLANGE_WELD_NECK.value),

    # -- Valves ----------------------------------------------------------------
    (r"\b(VLV[-\s]?GT|GATE\s*VALVE|VALVE[,\s]*GATE|GT\s*VLV|\bGV\b)\b",
     ItemType.GATE_VALVE.value),

    (r"\b(VLV[-\s]?BL|BALL\s*VALVE|VALVE[,\s]*BALL|BL\s*VLV)\b",
     ItemType.BALL_VALVE.value),

    (r"\b(VLV[-\s]?GLB?|GLOBE\s*VALVE|VALVE[,\s]*GLOBE|GLB?\s*VLV|\bGLV\b)\b",
     ItemType.GLOBE_VALVE.value),

    (r"\b(VLV[-\s]?CHK|CHECK\s*VALVE|VALVE[,\s]*CHECK|CHK\s*VLV|\bNRV\b|NON[-\s]?RETURN\s*(?:VALVE|VLV)?)\b",
     ItemType.CHECK_VALVE.value),

    (r"\b(VLV[-\s]?BF|BUTTERFLY\s*VALVE|VALVE[,\s]*BUTTERFLY|BF\s*VLV|\bBFV\b)\b",
     ItemType.BUTTERFLY_VALVE.value),

    (r"\b(VLV[-\s]?PLUG|PLUG\s*VALVE|VALVE[,\s]*PLUG|PLUG\s*VLV)\b",
     ItemType.PLUG_VALVE.value),

    # New: Control Valve (CV / CONTROL VLV)
    (r"\b(CONTROL\s*VALVE|VALVE[,\s]*CONTROL|CONTROL\s*VLV|\bCV\b)\b",
     ItemType.GATE_VALVE.value),   # maps to GATE_VALVE as closest piping type; tolerance engine can differentiate via standard

    # New: Pressure Safety / Relief Valve (PSV / SRV / PRV / RV)
    (r"\b(PRESSURE\s*(?:SAFETY|RELIEF)\s*VALVE|(?:PSV|PRV|SRV|RV)\b|SAFETY\s*VALVE)\b",
     ItemType.GATE_VALVE.value),   # maps to GATE_VALVE for tolerance purposes

    # -- Pipe & Fittings -------------------------------------------------------
    (r"\b(PIPE[-\s]?(?:SMLS|SEAMLESS|ERW|CS|SS)?|SEAMLESS\s*PIPE|PIPE[,\s]*SEAMLESS|PIPE\s+SMLS|PIPES?|CS\s+PIPE|SS\s+PIPE)\b",
     ItemType.PIPE_SEAMLESS.value),

    # New: Reducer (butt-weld concentric / eccentric)
    (r"\b(REDUCER|RDCR|CONC(?:ENTRIC)?\s*RED(?:UCER)?|ECC(?:ENTRIC)?\s*RED(?:UCER)?)\b",
     ItemType.ELBOW_BUTTWELD.value),   # maps to ELBOW_BUTTWELD as closest fitting type

    (r"\b(ELBOW[,\s]*(?:45|90)?|45\s*(?:DEG)?\s*ELBOW|90\s*(?:DEG)?\s*ELBOW|ELBOW\s*45\s*LR|ELBOW\s*90\s*LR)\b",
     ItemType.ELBOW_BUTTWELD.value),

    # -- Gaskets & Bolts -------------------------------------------------------
    (r"\b(GSKT[-\s]?SP?WD?|SPIRAL\s*WOUND\s*GASKET|GASKET[,\s]*SPIRAL\s*WOUND)\b",
     ItemType.SPIRAL_WOUND_GASKET.value),

    (r"\b(STUDBLT|STUD\s*BOLTS?|BOLT[-\s]?STUD)\b",
     ItemType.STUD_BOLT.value),

    # -- Rotating & Electrical -------------------------------------------------
    (r"\b(FLAMEPROOF\s*MOTOR|EX[-\s]?D\s*MOTOR|MOTOR\s*EX|ELECTRIC\s*MOTOR|MTR|MOTORS?)\b",
     ItemType.MOTOR_FLAMEPROOF.value),

    (r"\b(MECH[-\s]?SEAL|MECHANICAL\s*SEAL|CARTRIDGE\s*SEAL|SEAL\s*MECH|SEALS?)\b",
     ItemType.MECHANICAL_SEAL.value),

    (r"\b(ROLLER\s*BEARING|BALL\s*BEARING|BEARINGS?|BRG)\b",
     ItemType.BEARING_ROLLER.value),

    (r"\b(CENTRIFUGAL\s*PUMP|PMP\s*CENT|PUMP[,\s]*CENTRIFUGAL|PUMPS?|PMP)\b",
     ItemType.PUMP_CENTRIFUGAL.value),

    (r"\b(ARMOURED\s*CABLE|ARM\s*CBL|CABLE[,\s]*ARMOURED)\b",
     ItemType.CABLE_ARMOURED.value),

    (r"\b(ACTUATOR|PNEUMATIC\s*ACTUATOR|ACTUATOR\s*TYPE:\s*PNEUMATIC)\b",
     ItemType.ACTUATOR_PNEUMATIC.value),

    (r"\b(FERRULE|BPE\s*FERRULE)\b",
     ItemType.FERRULE_FITTING.value),

    # Generic flange fallback (least specific — must remain last)
    (r"\bFLG\b",       ItemType.FLANGE_WELD_NECK.value),
    (r"\bFLANGES?\b",  ItemType.FLANGE_WELD_NECK.value),
]

RE_ITEM_TYPES: List[Tuple[re.Pattern, str]] = [
    (re.compile(pat, re.IGNORECASE), itype)
    for pat, itype in _ITEM_TYPE_RAW
]

_FACING_RAW: List[Tuple[str, str]] = [
    (r"\b(RTJ|BLRTJ|WNRTJ|BLRTI|RING\s*TYPE\s*JOINT)\b",  FacingEnd.RTJ.value),
    (r"\b(WNRF|BLRF|SORF|RF|RFFE|RAISED\s*FACE|SPRF|THRF)\b", FacingEnd.RF.value),
    (r"\b(FF|FLAT\s*FACE)\b",                               FacingEnd.FF.value),
    (r"\b(BW|BUTT\s*WELD(?:ED)?|BE)\b",                    FacingEnd.BW.value),
    (r"\b(SW|SOCKET\s*WELD(?:ED)?)\b",                     FacingEnd.SW.value),
    (r"\b(THRD|THREAD(?:ED)?|NPT|THRF)\b",                 FacingEnd.THRD.value),
]

RE_FACING: List[Tuple[re.Pattern, str]] = [
    (re.compile(pat, re.IGNORECASE), face)
    for pat, face in _FACING_RAW
]

_PRESSURE_RAW: List[str] = [
    r"\bCLASS\s*([0-9]{3,4})\b",
    r"\bCL[-\s]?([0-9]{3,4})\b",
    r"(?:^|[\s,-])([0-9]{3,4})\s*[\*#](?:$|[\s,-])",
    r"\b([0-9]{3,4})\s*LB(?:S)?\b",
    r"\bPN[-\s]?([0-9]{2,3})\b",
    r"\b(150|300|600|900|1500|2500)\s*(?:WN|SO|BL|RF|RTJ|SW|BW|LB|#)\b",
    r"\bCLASS\s*(?:ISO|150)\b",
]

RE_PRESSURE: List[re.Pattern] = [
    re.compile(pat, re.IGNORECASE) for pat in _PRESSURE_RAW
]

_SIZE_INCH_RAW: List[str] = [
    r'(?:^|[\s,-])([0-9]{1,2}(?:\s+[0-9]/[0-9])?|\d+/\d+)\s*(?:\"|\'\''  r"|'|INCH|IN)?\s*(?:150|300|600|900|1500)[\*#]",
    r'(?:^|[\s,-])([0-9]+(?:\.[0-9]+)?|\d+/\d+|\d+\s+\d+/\d+)\s*(?:INCH|IN|"|\'\''  r"|')(?=[\s,-]|$)",
    r'\b([0-9]{1,2}(?:\.[0-9]+)?|\d+/\d+|\d+\s+\d+/\d+)\s*NB\b',
]

RE_SIZE_INCH: List[re.Pattern] = [
    re.compile(pat, re.IGNORECASE) for pat in _SIZE_INCH_RAW
]

RE_SIZE_DN: List[re.Pattern] = [
    re.compile(r'\bDN[-\s]?([0-9]{2,3})\b', re.IGNORECASE),
]

RE_SIZE_MM: List[re.Pattern] = [
    re.compile(r'\b([0-9]{2,3})\s*MM\b', re.IGNORECASE),
]

_METALLURGY_RAW: List[Tuple[str, str]] = [
    (r"\b(CF8M|A351[-\s]?CF8M|ASTM\s*A351\s*CF8M)\b",                               "ASTM A351 CF8M"),
    (r"\b(A106[-\s]?[A-C]?|ASTM\s*A106(?:\s*GR\.?\s*[A-C])?)\b",                    "ASTM A106 GR.B"),
    (r"\b(A350[-\s]?LF2|LF2|LTCS(?:\s*A350\s*LF2)?)\b",                              "ASTM A350 LF2"),
    (r"\b(A815[A-Z0-9-\s]*S32750|ASTM\s*A815[A-Z0-9-\s]*S32750|S32750|SDSS|SUPER\s*DUPLEX)\b", "ASTM A815 S32750"),
    (r"\b(DSS|DUPLEX\s*(?:SS|STAINLESS)?|UNS\s*S31803|S31803|ASTM\s*A182\s*F51|F51)\b", "ASTM A182 F51"),
    (r"\b(INCO(?:NEL)?\s*625|UNS\s*N06625)\b",                                        "INCONEL 625"),
    (r"\b(HAST(?:ELLOY)?\s*[-]?C(?:276)?|UNS\s*N10276)\b",                           "HASTELLOY C-276"),
    (r"\b(MONEL\s*(?:400)?|UNS\s*N04400)\b",                                          "MONEL 400"),
    (r"\b(316L\s*/\s*1\.4404|316L|1\.4404|ASTM\s*A182\s*F316L)\b",                   "ASTM A182 F316L"),
    (r"\b(SS316|F316|AISI\s*316|SS-316|ASTM\s*A182\s*F316)\b",                        "ASTM A182 F316"),
    (r"\b(SS304L?|F304|AISI\s*304|SS-304|ASTM\s*A182\s*F304)\b",                      "ASTM A182 F304"),
    (r"\b(A216[-\s]?WCB|WCB|CAST\s*STEEL\s*WCB)\b",                                  "ASTM A216 WCB"),
    (r"\b(S?A105N?|CS\s*A105|CARBON\s*STEEL\s*A105|A\s*/\s*SA\s*105|ASTM\s*A\s*105|A105|\bCS\b)\b", "ASTM A105"),
    (r"\b(API\s*5L(?:\s*GR\.?\s*[A-Z0-9]+)?|5L\s*GR\.?\s*[A-Z0-9]+)\b",             "API 5L GR.B"),
    (r"\b(A333[-\s]?GR\.?6|ASTM\s*A333(?:\s*GR\.?\s*6)?|A333)\b",                   "ASTM A333 GR.6"),
    (r"\b(A312[-\s]?TP316L?|ASTM\s*A312(?:\s*TP316L?)?)\b",                         "ASTM A312 TP316L"),
    (r"\b(SS316[/-]GR(?:AF)?|316SS/GRAPHITE|SS316\s*/\s*GRAPHITE)\b",                 "SS316 / GRAPHITE"),
    (r"\b(SS304[/-]GR(?:AF)?|SS304\s*/\s*GRAPHITE)\b",                                "SS304 / GRAPHITE"),
    (r"\b(B7[/-]2H|ASTM\s*A193\s*B7)\b",                                              "ASTM A193 B7 / A194 2H"),
    (r"\b(L7[/-]GR7|ASTM\s*A320\s*L7)\b",                                             "ASTM A320 L7 / A194 7"),
]

RE_METALLURGY: List[Tuple[re.Pattern, str]] = [
    (re.compile(pat, re.IGNORECASE), mat)
    for pat, mat in _METALLURGY_RAW
]

_STANDARDS_RAW: List[Tuple[str, str]] = [
    (r"\b(ASME\s*B16\.5|ANSI/ASME\s*B16\.5|B16\.5|ANSI\s*B16\.5)\b",  "ASME B16.5"),
    (r"\b(ASME\s*B16\.47|B16\.47)\b",                                    "ASME B16.47"),
    (r"\b(ASME\s*B16\.9|B16\.9)\b",                                      "ASME B16.9"),
    (r"\b(ASME\s*B36\.10M?|B36\.10)\b",                                  "ASME B36.10M"),
    (r"\b(ASME\s*B36\.19M?|B36\.19)\b",                                  "ASME B36.19M"),
    (r"\b(API\s*600)\b",                                                  "API 600"),
    (r"\b(API\s*6D)\b",                                                   "API 6D"),
    (r"\b(BS\s*1873)\b",                                                  "BS 1873"),
    (r"\b(ASME\s*B16\.34|B16\.34)\b",                                    "ASME B16.34"),
    (r"\b(ASME\s*B16\.20|B16\.20)\b",                                    "ASME B16.20"),
    (r"\b(ASME\s*B18\.2\.1|B18\.2\.1)\b",                                "ASME B18.2.1"),
    (r"\b(NACE\s*MR0175|NACE\s*MR[-\s]?0175|ISO\s*15156)\b",            "NACE MR0175"),
    (r"\b(EN\s*10204(?:\s*[-:]?\s*(?:3\.1\.?B?|2\.2|3\.2))?)\b",        "EN 10204 3.1"),
]

RE_STANDARDS: List[Tuple[re.Pattern, str]] = [
    (re.compile(pat, re.IGNORECASE), std)
    for pat, std in _STANDARDS_RAW
]

# Individual compiled patterns used for multi-attribute extraction
_RE_POWER_KW    = re.compile(r"\b([0-9]+(?:\.[0-9]+)?)\s*KW\b", re.IGNORECASE)
_RE_POWER_HP    = re.compile(r"\b([0-9]+(?:\.[0-9]+)?)\s*HP\b", re.IGNORECASE)
_RE_POLES       = re.compile(r"\b([2468])\s*P(?:OLE)?S?\b", re.IGNORECASE)
_RE_RPM         = re.compile(r"\b(750|1000|1500|3000|[0-9]{3,4})\s*RPM\b", re.IGNORECASE)
_RE_EX_D        = re.compile(r"\b(EX[-\s]?D(?:\s*IIC\s*T[1-6])?|FLAMEPROOF)\b", re.IGNORECASE)
_RE_EX_E        = re.compile(r"\b(EX[-\s]?E|INCREASED\s*SAFETY)\b", re.IGNORECASE)
_RE_NON_EX      = re.compile(r"\b(NON[-\s]?EX|SAFE\s*AREA)\b", re.IGNORECASE)
_RE_SEAL_PLAN   = re.compile(r"\b(PLAN\s*(?:11|23|52|53A|54))\b", re.IGNORECASE)
_RE_BRG_CLEAR   = re.compile(r"\b(C2|C3|C4|CN|C0)\b", re.IGNORECASE)
_RE_BRG_CODE    = re.compile(r"\b6[23]([0-9]{2})\b", re.IGNORECASE)
_RE_BRG_BORE    = re.compile(r"\b([0-9]{2,3})\s*MM\s*(?:BORE|SLEEVE|SHAFT)?\b", re.IGNORECASE)
_RE_FLOW        = re.compile(r"\b([0-9]+(?:\.[0-9]+)?)\s*M3/?(?:HR|H)\b", re.IGNORECASE)
_RE_HEAD        = re.compile(r"\b([0-9]+(?:\.[0-9]+)?)\s*M(?:TR)?(?:\s*HEAD)?\b", re.IGNORECASE)
_RE_SCHEDULE    = re.compile(r"\b(SCH[-\s]?(?:5S?|10S?|20|30|40S?|60|80S?|100|120|140|160|STD|XS|XXS))\b", re.IGNORECASE)
_RE_STD_WALL    = re.compile(r"\b(STD|STANDARD\s*WALL)\b", re.IGNORECASE)
_RE_XS_WALL     = re.compile(r"\b(XS|EXTRA\s*STRONG)\b", re.IGNORECASE)
_RE_XXS_WALL    = re.compile(r"\b(XXS|DOUBLE\s*EXTRA\s*STRONG)\b", re.IGNORECASE)
_RE_NACE        = re.compile(r"\b(NACE|SOUR|MR0175|MR[-\s]?0175|ISO[-\s]?15156|HIC\s*TEST(?:ED)?)\b", re.IGNORECASE)
_RE_NON_SOUR    = re.compile(r"\b(NON[-\s]?SOUR|SWEET)\b", re.IGNORECASE)
_RE_NON_IBR     = re.compile(r"\b(NON[-\s]?IBR)\b", re.IGNORECASE)
_RE_IBR         = re.compile(r"\b(IBR|INDIAN\s*BOILER\s*REG(?:ULATION)?S?)\b", re.IGNORECASE)
_RE_SERIES_A    = re.compile(r"\b(SERIES[-\s]?A|MSS[-\s]?SP[-\s]?44|SP[-\s]?44|SER\.?\s*A)\b", re.IGNORECASE)
_RE_SERIES_B    = re.compile(r"\b(SERIES[-\s]?B|API[-\s]?605|SER\.?\s*B)\b", re.IGNORECASE)
_RE_SWG         = re.compile(r"\b(SPIRAL[-\s]?WOUND|SPWD|SWG)\b", re.IGNORECASE)
_RE_OCT         = re.compile(r"\b(OCTAGONAL|OCT)\b", re.IGNORECASE)
_RE_OVAL        = re.compile(r"\b(OVAL)\b", re.IGNORECASE)
_RE_RTJ_RING    = re.compile(r"\b(RTJ|RING[-\s]?JOINT)\b", re.IGNORECASE)
_RE_GRAPHITE    = re.compile(r"\b(GRAPHITE|GRAF|FLEXIBLE\s*GRAPHITE)\b", re.IGNORECASE)
_RE_PTFE        = re.compile(r"\b(PTFE|TEFLON)\b", re.IGNORECASE)
_RE_B7          = re.compile(r"\b(B7M?|A193[-\s]?B7M?|ASTM\s*A193\s*B7M?)\b", re.IGNORECASE)
_RE_L7          = re.compile(r"\b(L7M?|A320[-\s]?L7M?|ASTM\s*A320\s*L7M?)\b", re.IGNORECASE)
_RE_B8          = re.compile(r"\b(B8M?|A193[-\s]?B8M?|ASTM\s*A193\s*B8M?)\b", re.IGNORECASE)
_RE_2H          = re.compile(r"\b(2H|A194[-\s]?2H|ASTM\s*A194\s*2H)\b", re.IGNORECASE)
_RE_GR7         = re.compile(r"\b(GR\.?\s*7|A194[-\s]?7|ASTM\s*A194\s*7)\b", re.IGNORECASE)
_RE_8M          = re.compile(r"\b(8M|A194[-\s]?8M|ASTM\s*A194\s*8M)\b", re.IGNORECASE)


# -----------------------------------------------------------------------------
# 3. Deterministic Attribute Extraction Implementation
# -----------------------------------------------------------------------------

@lru_cache(maxsize=2048)
def extract_attributes(raw_description: str) -> ExtractedMaterialAttributes:
    """
    Extracts and standardizes technical physical properties from raw text descriptions.

    The result is cached by the exact input string (lru_cache). This means that
    in bulk matching jobs where the same description appears multiple times, the
    full regex pipeline only runs once per unique string.

    Processing order:
      1. Normalize text (unicode, whitespace, uppercase)
      2. Expand CPSE dialect thesaurus (NRV -> CHECK VALVE, etc.)
      3. Extract all attributes via pre-compiled regex patterns
      4. Apply default standard inferencing
      5. Score extraction confidence
    """
    if not raw_description:
        return ExtractedMaterialAttributes(raw_description="")

    # Step 1: Normalize unicode, whitespace, control chars
    text = normalize_text(raw_description)

    # Step 2: Expand refinery dialect shorthand BEFORE any pattern matching
    # This ensures downstream patterns fire on canonical terms.
    # We add padding spaces so word-boundary patterns work at string edges.
    norm_text = f" {expand_refinery_thesaurus(text)} "

    # 1. Item Type Extraction
    item_type: Optional[str] = None
    for pattern, itype in RE_ITEM_TYPES:
        if pattern.search(norm_text):
            item_type = itype
            break

    # 2. Pressure Class Extraction
    pressure_class: Optional[int] = None
    for p_pat in RE_PRESSURE:
        m = p_pat.search(norm_text)
        if m and m.groups():
            val_str = m.group(1).upper()
            val = 150 if val_str == "ISO" else int(val_str)
            if "PN" in p_pat.pattern:
                pressure_class = PN_TO_CLASS.get(val, 150)
            else:
                pressure_class = val
            break

    # 3. Size Extraction (Bore mm, Inch, DN)
    size_nb_mm: Optional[float] = None
    size_inch: Optional[str] = None
    dn_code: Optional[str] = None

    # Check DN format
    for dn_pat in RE_SIZE_DN:
        m = dn_pat.search(norm_text)
        if m:
            dn_val = int(m.group(1))
            size_nb_mm = float(dn_val)
            dn_code = f"DN{dn_val}"
            size_inch = MM_TO_INCH.get(size_nb_mm, f'{dn_val/25.0:.1f}"')
            break

    # Check Metric MM format
    if size_nb_mm is None:
        for mm_pat in RE_SIZE_MM:
            m = mm_pat.search(norm_text)
            if m:
                mm_val = float(m.group(1))
                size_nb_mm = mm_val
                dn_code = f"DN{int(mm_val)}"
                size_inch = MM_TO_INCH.get(size_nb_mm, f'{mm_val/25.0:.1f}"')
                break

    # Check Imperial Inch format
    if size_nb_mm is None:
        for in_pat in RE_SIZE_INCH:
            m = in_pat.search(norm_text)
            if m:
                inch_val = m.group(1).strip()
                if inch_val in INCH_TO_MM:
                    size_nb_mm = INCH_TO_MM[inch_val]
                    size_inch = f'{inch_val}"'
                    dn_code = f"DN{int(size_nb_mm)}"
                break

    # 4. Metallurgy Extraction
    metallurgy: Optional[str] = None
    for m_pat, mat_name in RE_METALLURGY:
        if m_pat.search(norm_text):
            metallurgy = mat_name
            break
    if not metallurgy:
        # Fallback to the normalization map in asme_rules
        metallurgy = normalize_metallurgy(raw_description.strip())
        if metallurgy == "UNKNOWN" or metallurgy.strip().upper() == raw_description.strip().upper():
            metallurgy = None

    # 5. Facing / End Connection Extraction
    facing_end: Optional[str] = None
    for f_pat, face_name in RE_FACING:
        if f_pat.search(norm_text):
            facing_end = face_name
            break

    # 6. Governing Standard Extraction
    standard: Optional[str] = None
    for s_pat, std_name in RE_STANDARDS:
        if s_pat.search(norm_text):
            standard = std_name
            break

    # Default standard inferencing if omitted
    if not standard:
        if item_type in [ItemType.FLANGE_WELD_NECK.value, ItemType.FLANGE_BLIND.value, ItemType.FLANGE_SLIP_ON.value]:
            standard = "ASME B16.5"
        elif item_type == ItemType.GATE_VALVE.value:
            standard = "API 600"
        elif item_type == ItemType.BALL_VALVE.value:
            standard = "API 6D"
        elif item_type == ItemType.BUTTERFLY_VALVE.value:
            standard = "API 609"
        elif item_type == ItemType.PLUG_VALVE.value:
            standard = "API 599"
        elif item_type == ItemType.SPIRAL_WOUND_GASKET.value:
            standard = "ASME B16.20"
        elif item_type == ItemType.STUD_BOLT.value:
            standard = "ASME B18.2.1"
        elif item_type == ItemType.MOTOR_FLAMEPROOF.value:
            standard = "IS/IEC 60079-1"
        elif item_type == ItemType.MECHANICAL_SEAL.value:
            standard = "API 682"
        elif item_type == ItemType.BEARING_ROLLER.value:
            standard = "ISO 15"
        elif item_type == ItemType.PUMP_CENTRIFUGAL.value:
            standard = "API 610"
        elif item_type == ItemType.PIPE_SEAMLESS.value:
            standard = "ASME B36.10M"
        elif item_type == ItemType.ELBOW_BUTTWELD.value:
            standard = "ASME B16.9"

    if item_type == ItemType.PIPE_SEAMLESS.value and not facing_end:
        facing_end = "BW"

    # 7. Rotating & Electrical Attributes Extraction
    power_kw: Optional[float] = None
    m_kw = _RE_POWER_KW.search(norm_text)
    if m_kw:
        power_kw = float(m_kw.group(1))
    else:
        m_hp = _RE_POWER_HP.search(norm_text)
        if m_hp:
            power_kw = round(float(m_hp.group(1)) * 0.7457, 1)

    poles: Optional[int] = None
    m_pole = _RE_POLES.search(norm_text)
    if m_pole:
        poles = int(m_pole.group(1))

    speed_rpm: Optional[int] = None
    m_rpm = _RE_RPM.search(norm_text)
    if m_rpm:
        speed_rpm = int(m_rpm.group(1))
        if poles is None:
            if speed_rpm >= 2800:
                poles = 2
            elif speed_rpm >= 1400:
                poles = 4
            elif speed_rpm >= 900:
                poles = 6
    elif poles is not None:
        speed_rpm = 3000 if poles == 2 else 1500 if poles == 4 else 1000

    hazardous_cert: Optional[str] = None
    if _RE_EX_D.search(norm_text):
        hazardous_cert = "Ex d IIC T4"
    elif _RE_EX_E.search(norm_text):
        hazardous_cert = "Ex e"
    elif _RE_NON_EX.search(norm_text):
        hazardous_cert = "Non-Ex"

    seal_plan: Optional[str] = None
    m_plan = _RE_SEAL_PLAN.search(norm_text)
    if m_plan:
        seal_plan = m_plan.group(1).replace("  ", " ").strip()

    bearing_bore_mm: Optional[float] = None
    bearing_clearance: Optional[str] = None
    m_clr = _RE_BRG_CLEAR.search(norm_text)
    if m_clr:
        bearing_clearance = m_clr.group(1)

    m_brg = _RE_BRG_CODE.search(norm_text)
    if m_brg:
        code_digit = int(m_brg.group(1))
        bearing_bore_mm = float(code_digit * 5)

    m_bore = _RE_BRG_BORE.search(norm_text)
    if m_bore and bearing_bore_mm is None:
        bearing_bore_mm = float(m_bore.group(1))

    flow_m3h: Optional[float] = None
    m_flow = _RE_FLOW.search(norm_text)
    if m_flow:
        flow_m3h = float(m_flow.group(1))

    head_m: Optional[float] = None
    m_head = _RE_HEAD.search(norm_text)
    if m_head and item_type == ItemType.PUMP_CENTRIFUGAL.value:
        head_m = float(m_head.group(1))

    # 8. Pipe Schedule Extraction (ASME B36.10M / B36.19M)
    schedule: Optional[str] = None
    m_sch = _RE_SCHEDULE.search(norm_text)
    if m_sch:
        schedule = m_sch.group(1).replace("-", " ").strip()
    elif _RE_STD_WALL.search(norm_text) and item_type in [
        ItemType.PIPE_SEAMLESS.value, ItemType.ELBOW_BUTTWELD.value, ItemType.FLANGE_WELD_NECK.value
    ]:
        schedule = "STD"
    elif _RE_XS_WALL.search(norm_text) and item_type in [
        ItemType.PIPE_SEAMLESS.value, ItemType.ELBOW_BUTTWELD.value, ItemType.FLANGE_WELD_NECK.value
    ]:
        schedule = "XS"
    elif _RE_XXS_WALL.search(norm_text):
        schedule = "XXS"

    # 9. Sour Service & NACE Extraction (NACE MR0175 / ISO 15156)
    is_sour_service: Optional[bool] = None
    if _RE_NACE.search(norm_text):
        is_sour_service = False if _RE_NON_SOUR.search(norm_text) else True

    # 9b. Indian Boiler Regulations (IBR 1950) Statutory Compliance
    is_ibr_certified: Optional[bool] = None
    if _RE_NON_IBR.search(norm_text):
        is_ibr_certified = False
    elif _RE_IBR.search(norm_text):
        is_ibr_certified = True

    # 10. Large Diameter Flange Series (ASME B16.47)
    flange_series: Optional[str] = None
    if _RE_SERIES_A.search(norm_text):
        flange_series = "SERIES_A"
    elif _RE_SERIES_B.search(norm_text):
        flange_series = "SERIES_B"

    # 11. Gasket Profile & Filler (ASME B16.20)
    gasket_type: Optional[str] = None
    gasket_filler: Optional[str] = None
    if item_type == ItemType.SPIRAL_WOUND_GASKET.value or "GSKT" in norm_text or "GASKET" in norm_text:
        if _RE_SWG.search(norm_text):
            gasket_type = "SPIRAL_WOUND"
        elif _RE_OCT.search(norm_text):
            gasket_type = "RING_JOINT_OCTAGONAL"
        elif _RE_OVAL.search(norm_text):
            gasket_type = "RING_JOINT_OVAL"
        elif _RE_RTJ_RING.search(norm_text):
            gasket_type = "RING_JOINT_OCTAGONAL"

        if _RE_GRAPHITE.search(norm_text):
            gasket_filler = "GRAPHITE"
        elif _RE_PTFE.search(norm_text):
            gasket_filler = "PTFE"

    # 12. Fastener Stud Bolt & Nut Grades (ASTM A193 / A194 / A320)
    bolt_grade: Optional[str] = None
    nut_grade: Optional[str] = None
    if item_type == ItemType.STUD_BOLT.value or "STUD" in norm_text or "BOLT" in norm_text:
        if _RE_B7.search(norm_text):
            bolt_grade = "ASTM A193 B7"
        elif _RE_L7.search(norm_text):
            bolt_grade = "ASTM A320 L7"
        elif _RE_B8.search(norm_text):
            bolt_grade = "ASTM A193 B8M"

        if _RE_2H.search(norm_text):
            nut_grade = "ASTM A194 2H"
        elif _RE_GR7.search(norm_text):
            nut_grade = "ASTM A194 7"
        elif _RE_8M.search(norm_text):
            nut_grade = "ASTM A194 8M"

    # Extraction confidence scoring based on equipment domain
    is_rotating = item_type in [
        ItemType.MOTOR_FLAMEPROOF.value,
        ItemType.MECHANICAL_SEAL.value,
        ItemType.BEARING_ROLLER.value,
        ItemType.PUMP_CENTRIFUGAL.value,
    ] or power_kw is not None or seal_plan is not None or bearing_bore_mm is not None

    if is_rotating:
        if item_type == ItemType.MOTOR_FLAMEPROOF.value or power_kw is not None:
            relevant_fields = [item_type, power_kw, speed_rpm, hazardous_cert]
        elif item_type == ItemType.MECHANICAL_SEAL.value or seal_plan is not None:
            relevant_fields = [item_type, size_nb_mm, seal_plan]
        elif item_type == ItemType.BEARING_ROLLER.value or bearing_bore_mm is not None:
            relevant_fields = [item_type, bearing_bore_mm, bearing_clearance]
        else:
            relevant_fields = [item_type, flow_m3h, head_m]
    else:
        # Static piping / valves / fittings: 5 core attributes
        relevant_fields = [item_type, size_nb_mm, pressure_class, metallurgy, facing_end]

    valid_count = sum(1 for f in relevant_fields if f is not None)
    confidence = round(valid_count / len(relevant_fields), 2)

    return ExtractedMaterialAttributes(
        item_type=item_type,
        size_nb_mm=size_nb_mm,
        size_inch=size_inch,
        dn_code=dn_code,
        pressure_class=pressure_class,
        metallurgy=metallurgy,
        facing_end=facing_end,
        standard=standard,
        power_kw=power_kw,
        speed_rpm=speed_rpm,
        poles=poles,
        hazardous_cert=hazardous_cert,
        seal_plan=seal_plan,
        bearing_bore_mm=bearing_bore_mm,
        bearing_clearance=bearing_clearance,
        flow_m3h=flow_m3h,
        head_m=head_m,
        schedule=schedule,
        is_sour_service=is_sour_service,
        is_ibr_certified=is_ibr_certified,
        flange_series=flange_series,
        gasket_type=gasket_type,
        gasket_filler=gasket_filler,
        bolt_grade=bolt_grade,
        nut_grade=nut_grade,
        raw_description=raw_description.strip(),
        extraction_confidence=confidence
    )


# Function alias for compatibility with test suites and benchmarks
extract_material_attributes = extract_attributes
