"""
Slot-Filling NER and Feature Engineering Attribute Normalizer.
Converts messy, abbreviated CPSE procurement descriptions across IOCL, ONGC, and BPCL
into standardized Pydantic ExtractedMaterialAttributes schemas.
"""

import re
import logging
from typing import Optional, Dict, Any, Tuple
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
# -----------------------------------------------------------------------------

REFINERY_THESAURUS = [
    (r"\bNRV\b", "CHECK VALVE"),
    (r"\bBFV\b", "BUTTERFLY VALVE"),
    (r"\bGV\b", "GATE VALVE"),
    (r"\bGLV\b", "GLOBE VALVE"),
    (r"\bPLUG\s*VLV\b", "PLUG VALVE"),
    (r"\bSPRF\b", "SPECTACLE BLIND RF"),
    (r"\bTHRF\b", "THREADED FLANGE RF"),
    (r"\bLTCS\b", "LTCS ASTM A350 LF2"),
    (r"\bDSS\b", "DUPLEX STAINLESS STEEL F51"),
    (r"\bSDSS\b", "SUPER DUPLEX STAINLESS STEEL S32750"),
    (r"\bINCO\s*625\b", "INCONEL 625"),
    (r"\bHAST-C\b", "HASTELLOY C-276"),
    (r"\bMONEL\s*400\b", "MONEL 400"),
]


def expand_refinery_thesaurus(text: str) -> str:
    """
    Expands common CPSE refinery dialect shorthand terms and acronyms across
    IOCL, ONGC, and BPCL into standardized terminology.
    """
    if not text:
        return ""
    expanded = text
    for pattern, replacement in REFINERY_THESAURUS:
        expanded = re.sub(pattern, replacement, expanded, flags=re.IGNORECASE)
    return expanded


# -----------------------------------------------------------------------------
# 2. Regular Expression Extraction Heuristics
# -----------------------------------------------------------------------------

RE_ITEM_TYPES = [
    (r"\b(FLG[-\s]?BL(?:D|RF|RTJ)?|BLIND\s*FLANGE|FLANGE[,\s]*BLIND|BLD\s*FLG|BLRF|BLRTJ|BLRTI|BLIND\s*CLASS|BLIND|SPRF|SPECTACLE\s*BLIND|SPEC\s*BLD|FIG(?:URE)?[-\s]?8)\b", ItemType.FLANGE_BLIND.value),
    (r"\b(FLG[-\s]?SO(?:RF|RTJ)?|SLIP[-\s]?ON\s*FLANGE|FLANGE[,\s]*SLIP[-\s]?ON|SO\s*FLG|SORF|SLIP\s*ON|THRF|THREADED\s*FLANGE)\b", ItemType.FLANGE_SLIP_ON.value),
    (r"\b(FLG[-\s]?WN(?:RF|RTJ)?|WELD(?:ING)?\s*NECK\s*FLANGE|FLANGE[,\s]*WELD(?:ING)?\s*NECK|WNRF|WNRTJ|WELD(?:ING)?\s*NECK|WN\s*FLG|WN\s*FIG)\b", ItemType.FLANGE_WELD_NECK.value),
    (r"\b(VLV[-\s]?GT|GATE\s*VALVE|VALVE[,\s]*GATE|GT\s*VLV|\bGV\b)\b", ItemType.GATE_VALVE.value),
    (r"\b(VLV[-\s]?BL|BALL\s*VALVE|VALVE[,\s]*BALL|BL\s*VLV)\b", ItemType.BALL_VALVE.value),
    (r"\b(VLV[-\s]?GLB?|GLOBE\s*VALVE|VALVE[,\s]*GLOBE|GLB?\s*VLV|\bGLV\b)\b", ItemType.GLOBE_VALVE.value),
    (r"\b(VLV[-\s]?CHK|CHECK\s*VALVE|VALVE[,\s]*CHECK|CHK\s*VLV|\bNRV\b|NON[-\s]?RETURN\s*(?:VALVE|VLV)?)\b", ItemType.CHECK_VALVE.value),
    (r"\b(VLV[-\s]?BF|BUTTERFLY\s*VALVE|VALVE[,\s]*BUTTERFLY|BF\s*VLV|\bBFV\b)\b", ItemType.BUTTERFLY_VALVE.value),
    (r"\b(VLV[-\s]?PLUG|PLUG\s*VALVE|VALVE[,\s]*PLUG|PLUG\s*VLV)\b", ItemType.PLUG_VALVE.value),
    (r"\b(PIPE[-\s]?SMLS|SEAMLESS\s*PIPE|PIPE[,\s]*SEAMLESS|PIPE\s+SMLS)\b", ItemType.PIPE_SEAMLESS.value),
    (r"\b(GSKT[-\s]?SP?WD?|SPIRAL\s*WOUND\s*GASKET|GASKET[,\s]*SPIRAL\s*WOUND)\b", ItemType.SPIRAL_WOUND_GASKET.value),
    (r"\b(STUDBLT|STUD\s*BOLTS?|BOLT[-\s]?STUD)\b", ItemType.STUD_BOLT.value),
    (r"\b(FLAMEPROOF\s*MOTOR|EX[-\s]?D\s*MOTOR|MOTOR\s*EX|ELECTRIC\s*MOTOR|MTR)\b", ItemType.MOTOR_FLAMEPROOF.value),
    (r"\b(MECH[-\s]?SEAL|MECHANICAL\s*SEAL|CARTRIDGE\s*SEAL|SEAL\s*MECH)\b", ItemType.MECHANICAL_SEAL.value),
    (r"\b(ROLLER\s*BEARING|BALL\s*BEARING|BEARING|BRG)\b", ItemType.BEARING_ROLLER.value),
    (r"\b(CENTRIFUGAL\s*PUMP|PMP\s*CENT|PUMP[,\s]*CENTRIFUGAL|PMP)\b", ItemType.PUMP_CENTRIFUGAL.value),
    (r"\b(ARMOURED\s*CABLE|ARM\s*CBL|CABLE[,\s]*ARMOURED)\b", ItemType.CABLE_ARMOURED.value),
    (r"\b(ELBOW[,\s]*(?:45|90)?|45\s*(?:DEG)?\s*ELBOW|90\s*(?:DEG)?\s*ELBOW|ELBOW\s*45\s*LR|ELBOW\s*90\s*LR)\b", ItemType.ELBOW_BUTTWELD.value),
    (r"\b(ACTUATOR|PNEUMATIC\s*ACTUATOR|ACTUATOR\s*TYPE:\s*PNEUMATIC)\b", ItemType.ACTUATOR_PNEUMATIC.value),
    (r"\b(FERRULE|BPE\s*FERRULE)\b", ItemType.FERRULE_FITTING.value),
    (r"\bFLG\b", ItemType.FLANGE_WELD_NECK.value),
    (r"\bFLANGES?\b", ItemType.FLANGE_WELD_NECK.value),
]

RE_FACING = [
    (r"\b(RTJ|BLRTJ|WNRTJ|BLRTI|RING\s*TYPE\s*JOINT)\b", FacingEnd.RTJ.value),
    (r"\b(WNRF|BLRF|SORF|RF|RFFE|RAISED\s*FACE|SPRF|THRF)\b", FacingEnd.RF.value),
    (r"\b(FF|FLAT\s*FACE)\b", FacingEnd.FF.value),
    (r"\b(BW|BUTT\s*WELD(?:ED)?|BE)\b", FacingEnd.BW.value),
    (r"\b(SW|SOCKET\s*WELD(?:ED)?)\b", FacingEnd.SW.value),
    (r"\b(THRD|THREAD(?:ED)?|NPT|THRF)\b", FacingEnd.THRD.value),
]

RE_PRESSURE = [
    r"\bCLASS\s*([0-9]{3,4})\b",
    r"\bCL[-\s]?([0-9]{3,4})\b",
    r"(?:^|[\s,-])([0-9]{3,4})\s*[\*#](?:$|[\s,-])",
    r"\b([0-9]{3,4})\s*LB(?:S)?\b",
    r"\bPN[-\s]?([0-9]{2,3})\b",
    r"\b(150|300|600|900|1500|2500)\s*(?:WN|SO|BL|RF|RTJ|SW|BW|LB|#)\b",
    r"\bCLASS\s*(?:ISO|150)\b",
]

RE_SIZE_INCH = [
    r'(?:^|[\s,-])([0-9]{1,2}(?:\s+[0-9]/[0-9])?|\d+/\d+)\s*(?:\"|\'\'|\'|INCH|IN)?\s*(?:150|300|600|900|1500)[\*#]',
    r'(?:^|[\s,-])([0-9]+(?:\.[0-9]+)?|\d+/\d+|\d+\s+\d+/\d+)\s*(?:INCH|IN|"|\'\'|\')(?=[\s,-]|$)',
    r'\b([0-9]{1,2}(?:\.[0-9]+)?|\d+/\d+|\d+\s+\d+/\d+)\s*NB\b',
]

RE_SIZE_DN = [
    r'\bDN[-\s]?([0-9]{2,3})\b',
]

RE_SIZE_MM = [
    r'\b([0-9]{2,3})\s*MM\b',
]

RE_METALLURGY = [
    (r"\b(CF8M|A351[-\s]?CF8M|ASTM\s*A351\s*CF8M)\b", "ASTM A351 CF8M"),
    (r"\b(A106[-\s]?[A-C]?|ASTM\s*A106(?:\s*GR\.?\s*[A-C])?)\b", "ASTM A106 GR.B"),
    (r"\b(A350[-\s]?LF2|LF2|LTCS(?:\s*A350\s*LF2)?)\b", "ASTM A350 LF2"),
    (r"\b(A815[A-Z0-9-\s]*S32750|ASTM\s*A815[A-Z0-9-\s]*S32750|S32750|SDSS|SUPER\s*DUPLEX)\b", "ASTM A815 S32750"),
    (r"\b(DSS|DUPLEX\s*(?:SS|STAINLESS)?|UNS\s*S31803|S31803|ASTM\s*A182\s*F51|F51)\b", "ASTM A182 F51"),
    (r"\b(INCO(?:NEL)?\s*625|UNS\s*N06625)\b", "INCONEL 625"),
    (r"\b(HAST(?:ELLOY)?\s*[-]?C(?:276)?|UNS\s*N10276)\b", "HASTELLOY C-276"),
    (r"\b(MONEL\s*(?:400)?|UNS\s*N04400)\b", "MONEL 400"),
    (r"\b(316L\s*/\s*1\.4404|316L|1\.4404|ASTM\s*A182\s*F316L)\b", "ASTM A182 F316L"),
    (r"\b(SS316|F316|AISI\s*316|SS-316|ASTM\s*A182\s*F316)\b", "ASTM A182 F316"),
    (r"\b(SS304L?|F304|AISI\s*304|SS-304|ASTM\s*A182\s*F304)\b", "ASTM A182 F304"),
    (r"\b(A216[-\s]?WCB|WCB|CAST\s*STEEL\s*WCB)\b", "ASTM A216 WCB"),
    (r"\b(S?A105N?|CS\s*A105|CARBON\s*STEEL\s*A105|A\s*/\s*SA\s*105|ASTM\s*A\s*105|A105|\bCS\b)\b", "ASTM A105"),
    (r"\b(SS316[/-]GR(?:AF)?|316SS/GRAPHITE|SS316\s*/\s*GRAPHITE)\b", "SS316 / GRAPHITE"),
    (r"\b(SS304[/-]GR(?:AF)?|SS304\s*/\s*GRAPHITE)\b", "SS304 / GRAPHITE"),
    (r"\b(B7[/-]2H|ASTM\s*A193\s*B7)\b", "ASTM A193 B7 / A194 2H"),
    (r"\b(L7[/-]GR7|ASTM\s*A320\s*L7)\b", "ASTM A320 L7 / A194 7"),
]

RE_STANDARDS = [
    (r"\b(ASME\s*B16\.5|ANSI/ASME\s*B16\.5|B16\.5|ANSI\s*B16\.5)\b", "ASME B16.5"),
    (r"\b(ASME\s*B16\.47|B16\.47)\b", "ASME B16.47"),
    (r"\b(ASME\s*B16\.9|B16\.9)\b", "ASME B16.9"),
    (r"\b(ASME\s*B36\.10M?|B36\.10)\b", "ASME B36.10M"),
    (r"\b(ASME\s*B36\.19M?|B36\.19)\b", "ASME B36.19M"),
    (r"\b(API\s*600)\b", "API 600"),
    (r"\b(API\s*6D)\b", "API 6D"),
    (r"\b(BS\s*1873)\b", "BS 1873"),
    (r"\b(ASME\s*B16\.34|B16\.34)\b", "ASME B16.34"),
    (r"\b(ASME\s*B16\.20|B16\.20)\b", "ASME B16.20"),
    (r"\b(ASME\s*B18\.2\.1|B18\.2\.1)\b", "ASME B18.2.1"),
    (r"\b(NACE\s*MR0175|NACE\s*MR[-\s]?0175|ISO\s*15156)\b", "NACE MR0175"),
    (r"\b(EN\s*10204(?:\s*[-:]?\s*(?:3\.1\.?B?|2\.2|3\.2))?)\b", "EN 10204 3.1"),
]


# -----------------------------------------------------------------------------
# 3. Deterministic Attribute Extraction Implementation
# -----------------------------------------------------------------------------

def extract_attributes(raw_description: str) -> ExtractedMaterialAttributes:
    """
    Extracts and standardizes technical physical properties from raw text descriptions.
    """
    if not raw_description:
        return ExtractedMaterialAttributes(raw_description="")

    text = raw_description.strip()
    norm_text = f" {text.upper()} "

    # 1. Item Type Extraction
    item_type: Optional[str] = None
    for pattern, itype in RE_ITEM_TYPES:
        if re.search(pattern, norm_text, re.IGNORECASE):
            item_type = itype
            break

    # 2. Pressure Class Extraction
    pressure_class: Optional[int] = None
    for p_pat in RE_PRESSURE:
        m = re.search(p_pat, norm_text, re.IGNORECASE)
        if m and m.groups():
            val_str = m.group(1).upper()
            val = 150 if val_str == "ISO" else int(val_str)
            if "PN" in p_pat:
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
        m = re.search(dn_pat, norm_text, re.IGNORECASE)
        if m:
            dn_val = int(m.group(1))
            size_nb_mm = float(dn_val)
            dn_code = f"DN{dn_val}"
            size_inch = MM_TO_INCH.get(size_nb_mm, f'{dn_val/25.0:.1f}"')
            break

    # Check Metric MM format
    if size_nb_mm is None:
        for mm_pat in RE_SIZE_MM:
            m = re.search(mm_pat, norm_text, re.IGNORECASE)
            if m:
                mm_val = float(m.group(1))
                size_nb_mm = mm_val
                dn_code = f"DN{int(mm_val)}"
                size_inch = MM_TO_INCH.get(size_nb_mm, f'{mm_val/25.0:.1f}"')
                break

    # Check Imperial Inch format
    if size_nb_mm is None:
        for in_pat in RE_SIZE_INCH:
            m = re.search(in_pat, norm_text, re.IGNORECASE)
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
        if re.search(m_pat, norm_text, re.IGNORECASE):
            metallurgy = mat_name
            break
    if not metallurgy:
        # Fallback check
        metallurgy = normalize_metallurgy(text)
        if metallurgy == "UNKNOWN" or metallurgy.strip().upper() == text.strip().upper():
            metallurgy = None

    # 5. Facing / End Connection Extraction
    facing_end: Optional[str] = None
    for f_pat, face_name in RE_FACING:
        if re.search(f_pat, norm_text, re.IGNORECASE):
            facing_end = face_name
            break

    # 6. Governing Standard Extraction
    standard: Optional[str] = None
    for s_pat, std_name in RE_STANDARDS:
        if re.search(s_pat, norm_text, re.IGNORECASE):
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

    # 7. Rotating & Electrical Attributes Extraction
    power_kw: Optional[float] = None
    m_kw = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*KW\b", norm_text)
    if m_kw:
        power_kw = float(m_kw.group(1))
    else:
        m_hp = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*HP\b", norm_text)
        if m_hp:
            power_kw = round(float(m_hp.group(1)) * 0.7457, 1)

    poles: Optional[int] = None
    m_pole = re.search(r"\b([2468])\s*P(?:OLE)?S?\b", norm_text)
    if m_pole:
        poles = int(m_pole.group(1))

    speed_rpm: Optional[int] = None
    m_rpm = re.search(r"\b(750|1000|1500|3000|[0-9]{3,4})\s*RPM\b", norm_text)
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
    if re.search(r"\b(EX[-\s]?D(?:\s*IIC\s*T[1-6])?|FLAMEPROOF)\b", norm_text):
        hazardous_cert = "Ex d IIC T4"
    elif re.search(r"\b(EX[-\s]?E|INCREASED\s*SAFETY)\b", norm_text):
        hazardous_cert = "Ex e"
    elif re.search(r"\b(NON[-\s]?EX|SAFE\s*AREA)\b", norm_text):
        hazardous_cert = "Non-Ex"

    seal_plan: Optional[str] = None
    m_plan = re.search(r"\b(PLAN\s*(?:11|23|52|53A|54))\b", norm_text)
    if m_plan:
        seal_plan = m_plan.group(1).replace("  ", " ").strip()

    bearing_bore_mm: Optional[float] = None
    bearing_clearance: Optional[str] = None
    m_clr = re.search(r"\b(C2|C3|C4|CN|C0)\b", norm_text)
    if m_clr:
        bearing_clearance = m_clr.group(1)

    m_brg = re.search(r"\b6[23]([0-9]{2})\b", norm_text)
    if m_brg:
        code_digit = int(m_brg.group(1))
        bearing_bore_mm = float(code_digit * 5)

    m_bore = re.search(r"\b([0-9]{2,3})\s*MM\s*(?:BORE|SLEEVE|SHAFT)?\b", norm_text)
    if m_bore and bearing_bore_mm is None:
        bearing_bore_mm = float(m_bore.group(1))

    flow_m3h: Optional[float] = None
    m_flow = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*M3/?(?:HR|H)\b", norm_text)
    if m_flow:
        flow_m3h = float(m_flow.group(1))

    head_m: Optional[float] = None
    m_head = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*M(?:TR)?(?:\s*HEAD)?\b", norm_text)
    if m_head and item_type == ItemType.PUMP_CENTRIFUGAL.value:
        head_m = float(m_head.group(1))

    # 8. Pipe Schedule Extraction (ASME B36.10M / B36.19M)
    schedule: Optional[str] = None
    m_sch = re.search(r"\b(SCH[-\s]?(?:5S?|10S?|20|30|40S?|60|80S?|100|120|140|160|STD|XS|XXS))\b", norm_text)
    if m_sch:
        schedule = m_sch.group(1).replace("-", " ").strip()
    elif re.search(r"\b(STD|STANDARD\s*WALL)\b", norm_text) and item_type in [ItemType.PIPE_SEAMLESS.value, ItemType.ELBOW_BUTTWELD.value, ItemType.FLANGE_WELD_NECK.value]:
        schedule = "STD"
    elif re.search(r"\b(XS|EXTRA\s*STRONG)\b", norm_text) and item_type in [ItemType.PIPE_SEAMLESS.value, ItemType.ELBOW_BUTTWELD.value, ItemType.FLANGE_WELD_NECK.value]:
        schedule = "XS"
    elif re.search(r"\b(XXS|DOUBLE\s*EXTRA\s*STRONG)\b", norm_text):
        schedule = "XXS"

    # 9. Sour Service & NACE Extraction (NACE MR0175 / ISO 15156)
    is_sour_service: Optional[bool] = None
    if re.search(r"\b(NACE|SOUR|MR0175|MR[-\s]?0175|ISO[-\s]?15156|HIC\s*TEST(?:ED)?)\b", norm_text):
        if re.search(r"\b(NON[-\s]?SOUR|SWEET)\b", norm_text):
            is_sour_service = False
        else:
            is_sour_service = True

    # 9b. Indian Boiler Regulations (IBR 1950) Statutory Compliance
    is_ibr_certified: Optional[bool] = None
    if re.search(r"\b(NON[-\s]?IBR)\b", norm_text):
        is_ibr_certified = False
    elif re.search(r"\b(IBR|INDIAN\s*BOILER\s*REG(?:ULATION)?S?)\b", norm_text):
        is_ibr_certified = True

    # 10. Large Diameter Flange Series (ASME B16.47)
    flange_series: Optional[str] = None
    if re.search(r"\b(SERIES[-\s]?A|MSS[-\s]?SP[-\s]?44|SP[-\s]?44|SER\.?\s*A)\b", norm_text):
        flange_series = "SERIES_A"
    elif re.search(r"\b(SERIES[-\s]?B|API[-\s]?605|SER\.?\s*B)\b", norm_text):
        flange_series = "SERIES_B"

    # 11. Gasket Profile & Filler (ASME B16.20)
    gasket_type: Optional[str] = None
    gasket_filler: Optional[str] = None
    if item_type == ItemType.SPIRAL_WOUND_GASKET.value or "GSKT" in norm_text or "GASKET" in norm_text:
        if re.search(r"\b(SPIRAL[-\s]?WOUND|SPWD|SWG)\b", norm_text):
            gasket_type = "SPIRAL_WOUND"
        elif re.search(r"\b(OCTAGONAL|OCT)\b", norm_text):
            gasket_type = "RING_JOINT_OCTAGONAL"
        elif re.search(r"\b(OVAL)\b", norm_text):
            gasket_type = "RING_JOINT_OVAL"
        elif re.search(r"\b(RTJ|RING[-\s]?JOINT)\b", norm_text):
            gasket_type = "RING_JOINT_OCTAGONAL"

        if re.search(r"\b(GRAPHITE|GRAF|FLEXIBLE\s*GRAPHITE)\b", norm_text):
            gasket_filler = "GRAPHITE"
        elif re.search(r"\b(PTFE|TEFLON)\b", norm_text):
            gasket_filler = "PTFE"

    # 12. Fastener Stud Bolt & Nut Grades (ASTM A193 / A194 / A320)
    bolt_grade: Optional[str] = None
    nut_grade: Optional[str] = None
    if item_type == ItemType.STUD_BOLT.value or "STUD" in norm_text or "BOLT" in norm_text:
        if re.search(r"\b(B7M?|A193[-\s]?B7M?|ASTM\s*A193\s*B7M?)\b", norm_text):
            bolt_grade = "ASTM A193 B7"
        elif re.search(r"\b(L7M?|A320[-\s]?L7M?|ASTM\s*A320\s*L7M?)\b", norm_text):
            bolt_grade = "ASTM A320 L7"
        elif re.search(r"\b(B8M?|A193[-\s]?B8M?|ASTM\s*A193\s*B8M?)\b", norm_text):
            bolt_grade = "ASTM A193 B8M"

        if re.search(r"\b(2H|A194[-\s]?2H|ASTM\s*A194\s*2H)\b", norm_text):
            nut_grade = "ASTM A194 2H"
        elif re.search(r"\b(GR\.?\s*7|A194[-\s]?7|ASTM\s*A194\s*7)\b", norm_text):
            nut_grade = "ASTM A194 7"
        elif re.search(r"\b(8M|A194[-\s]?8M|ASTM\s*A194\s*8M)\b", norm_text):
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
        raw_description=text,
        extraction_confidence=confidence
    )


# Function alias for compatibility with test suites and benchmarks
extract_material_attributes = extract_attributes
