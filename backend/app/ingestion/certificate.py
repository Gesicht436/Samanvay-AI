"""
Mill Test Certificate (MTC) and Delivery Challan Parser (EN 10204 3.1 / 3.2).
Extracts structured inspection metadata, heat numbers, chemical compositions, mechanical properties,
and multi-item line descriptions from digital PDFs and scanned OCR documents.

Enhanced with:
  - ASTM Carbon Equivalent (CE) weldability formula computation.
  - Mechanical yield/tensile strength threshold cross-validation.
  - Granular document sub-classification (EN 10204 3.1, 3.2 with TPI, Challans, POs).
  - Expanded OCR domain spell-correction dictionary.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.app.ml.ner_tagger import extract_attributes

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# 1. Industrial OCR Character Post-Processing Dictionary
# -----------------------------------------------------------------------------

def normalize_mtc_text(text: str) -> str:
    """
    Corrects common OCR optical character misreads specific to industrial piping,
    valves, metallurgy grades, and ASTM/ASME specifications.
    """
    t = text
    # ASME / ANSI standard misreads
    t = re.sub(r"\bASME\s*816\b", "ASME B16", t, flags=re.IGNORECASE)
    t = re.sub(r"\bANSI\s*816\b", "ANSI B16", t, flags=re.IGNORECASE)
    t = re.sub(r"\b816\.([0-9])\b", r"B16.\1", t, flags=re.IGNORECASE)
    t = re.sub(r"\bB16\s+([0-9]+)\b", r"B16.\1", t, flags=re.IGNORECASE)
    t = re.sub(r"\bAPI\s*6\s*D\b", "API 6D", t, flags=re.IGNORECASE)
    t = re.sub(r"\bAPI\s*60\s*0\b", "API 600", t, flags=re.IGNORECASE)

    # ASTM Grade misreads
    t = re.sub(r"\bA\s*105\b", "ASTM A105", t, flags=re.IGNORECASE)
    t = re.sub(r"\bSA\s*105\b", "ASME SA105", t, flags=re.IGNORECASE)
    t = re.sub(r"\bA\s*815\b", "ASTM A815", t, flags=re.IGNORECASE)
    t = re.sub(r"\bA\s*182\b", "ASTM A182", t, flags=re.IGNORECASE)
    t = re.sub(r"\bA\s*350\b", "ASTM A350", t, flags=re.IGNORECASE)
    t = re.sub(r"\bA\s*216\b", "ASTM A216", t, flags=re.IGNORECASE)
    t = re.sub(r"\bVVCB\b", "WCB", t, flags=re.IGNORECASE)
    t = re.sub(r"\bVV-C-B\b", "WCB", t, flags=re.IGNORECASE)

    # Stainless & Alloy shorthands
    t = re.sub(r"\bSS\s*316\b", "SS316", t, flags=re.IGNORECASE)
    t = re.sub(r"\b316\s*L\b", "316L", t, flags=re.IGNORECASE)
    t = re.sub(r"\bSS\s*304\b", "SS304", t, flags=re.IGNORECASE)
    t = re.sub(r"\b304\s*L\b", "304L", t, flags=re.IGNORECASE)

    # Flange and Valve shorthand corrections
    t = re.sub(r"\bFig\.\b", "Flg.", t, flags=re.IGNORECASE)
    t = re.sub(r"\bFIg\.\b", "Flg.", t, flags=re.IGNORECASE)
    t = re.sub(r"\bHANGE\b", "FLANGE", t, flags=re.IGNORECASE)
    t = re.sub(r"\b\[NV\b", "INV", t, flags=re.IGNORECASE)
    t = re.sub(r"\b150\*\b", "150#", t)
    t = re.sub(r"\b300\*\b", "300#", t)
    t = re.sub(r"\b600\*\b", "600#", t)
    t = re.sub(r"\b900\*\b", "900#", t)
    t = re.sub(r"\bBLRTI\b", "BLRTJ", t, flags=re.IGNORECASE)
    t = re.sub(r"\baLRTJ\b", "BLRTJ", t)
    t = re.sub(r"\bWN\s*RF\b", "WNRF", t, flags=re.IGNORECASE)
    t = re.sub(r"\bSO\s*RF\b", "SORF", t, flags=re.IGNORECASE)
    t = re.sub(r"\bBL\s*RF\b", "BLRF", t, flags=re.IGNORECASE)

    # NACE and Sour Service
    t = re.sub(r"\bNACE\s*MR\s*0175\b", "NACE MR0175", t, flags=re.IGNORECASE)
    t = re.sub(r"\bISO\s*15156[-\s]*[1-3]?\b", "ISO 15156", t, flags=re.IGNORECASE)

    # Dimensions and Schedules
    t = re.sub(r"\b([0-9]{1,2})\s*N\s*B\b", r"\1 NB", t, flags=re.IGNORECASE)
    t = re.sub(r"\bSCH\s*([0-9]{1,3}[A-Z]?)\b", r"SCH \1", t, flags=re.IGNORECASE)
    return t


# -----------------------------------------------------------------------------
# 2. Chemical Composition Extraction & Carbon Equivalent Calculation
# -----------------------------------------------------------------------------

def extract_chemical_from_text(text: str) -> Dict[str, str]:
    """Extracts chemical elemental percentages from OCR text or certificate text."""
    chem: Dict[str, str] = {}
    elements = ["C", "Mn", "Si", "P", "S", "Cr", "Ni", "Mo", "Cu", "V", "Al", "Ti", "Nb", "N"]
    
    # 1. Key-value style: e.g. "C: 0.19%", "Mn = 0.66", "C 0.18"
    for el in elements:
        pat = rf"\b{el}\s*[:=\s]\s*([0-9]+\.[0-9]{{1,4}})\s*%?"
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            chem[el] = f"{val}%"

    # 2. Decimal percentage scan fallback
    if len(chem) < 2:
        floats = re.findall(r"\b0\.[0-9]{2,4}\b", text)
        if len(floats) >= 3:
            default_els = ["C", "Mn", "P", "S", "Si"]
            for i, f_val in enumerate(floats[:5]):
                if default_els[i] not in chem:
                    chem[default_els[i]] = f"{f_val}%"

    return chem


def compute_carbon_equivalent(chem_dict: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Computes ASTM / IIW Carbon Equivalent (CE) for weldability validation:
      CE = %C + %Mn/6 + (%Cr + %Mo + %V)/5 + (%Ni + %Cu)/15
    Standard threshold for ASTM A105 / A350 LF2: CE <= 0.43% (or <= 0.45% for thick sections).
    """
    def _parse_val(el: str) -> float:
        val_str = chem_dict.get(el, "0").replace("%", "").strip()
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    c = _parse_val("C")
    mn = _parse_val("Mn")
    cr = _parse_val("Cr")
    mo = _parse_val("Mo")
    v = _parse_val("V")
    ni = _parse_val("Ni")
    cu = _parse_val("Cu")

    if c <= 0.0:
        return None

    ce = c + (mn / 6.0) + ((cr + mo + v) / 5.0) + ((ni + cu) / 15.0)
    ce_rounded = round(ce, 3)

    # Weldability assessment
    max_safe_ce = 0.43
    is_weldable = ce_rounded <= max_safe_ce
    status = "EXCELLENT_WELDABILITY" if ce_rounded <= 0.40 else ("ACCEPTABLE_WELDABILITY" if is_weldable else "PREHEAT_REQUIRED_HIGH_CE")

    return {
        "carbon_equivalent": ce_rounded,
        "formula": "IIW (C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15)",
        "is_standard_weldable": is_weldable,
        "max_recommended_ce": max_safe_ce,
        "status": status
    }


# -----------------------------------------------------------------------------
# 3. Mechanical Property Extraction & ASTM Strength Validation
# -----------------------------------------------------------------------------

def extract_mechanical_from_text(text: str) -> Dict[str, str]:
    """Extracts mechanical properties (Tensile, Yield, Elongation, Hardness) from text."""
    mech: Dict[str, str] = {}

    # Tensile strength (Rm)
    m_ts = re.search(
        r"(?:Tensile\s*(?:Strength)?|Rm|T\.S\.)\s*(?:\(?[A-Za-z]+\)?)?[:\s]*(?:Min\.?)?\s*([0-9]{3,4})\s*(?:MPa|N/mm2|KSI)?",
        text,
        re.IGNORECASE
    )
    if m_ts:
        mech["tensile"] = f"{m_ts.group(1)} MPa"

    # Yield strength (ReH / Rp0.2)
    m_ys = re.search(
        r"(?:Yield\s*(?:Strength)?|ReH|Rp0\.2|Y\.S\.)\s*(?:\(?[A-Za-z]+\)?)?[:\s]*(?:Min\.?)?\s*([0-9]{3,4})\s*(?:MPa|N/mm2|KSI)?",
        text,
        re.IGNORECASE
    )
    if m_ys:
        mech["yield"] = f"{m_ys.group(1)} MPa"

    # Elongation (A / A5)
    m_el = re.search(
        r"(?:Elongation|Elong|A5?)\s*(?:\(?[A-Za-z%]+\)?)?[:\s]*(?:Min\.?)?\s*([0-9]{1,2}(?:\.[0-9]+)?)\s*%",
        text,
        re.IGNORECASE
    )
    if m_el:
        mech["elongation"] = f"{m_el.group(1)}%"
    else:
        m_el2 = re.search(r"\bElongation\b.*?([1-4][0-9])\b", text, re.IGNORECASE | re.DOTALL)
        if m_el2:
            mech["elongation"] = f"{m_el2.group(1)}%"

    # Hardness (HB / HRC / HBW)
    m_hb = re.search(
        r"(?:Hardness|HBW?|HRC|HV)\s*(?:\(?[A-Za-z]+\)?)?[:\s]*(?:Max\.?)?\s*([0-9]{2,3})\s*(?:HBW?|HRC|HV)?",
        text,
        re.IGNORECASE
    )
    if m_hb:
        mech["hardness"] = f"{m_hb.group(1)} HB"

    # Heat Treatment
    m_ht = re.search(
        r"\b(NORMALIZED(?:\s*[0-9]+DEG(?:\s*C(?:ENTIGRADE)?)?)?|QUENCHED\s*(?:&|AND)\s*TEMPERED|ANNEALED|SOLUTION\s*ANNEALED)\b",
        text,
        re.IGNORECASE
    )
    if m_ht:
        mech["heat_treatment"] = m_ht.group(1).strip()

    return mech


def validate_mechanical_thresholds(material_grade: Optional[str], mech_dict: Dict[str, str]) -> List[str]:
    """
    Validates extracted mechanical properties against statutory ASTM minimum standards.
    Emits warnings if values are below ASTM thresholds.
    """
    warnings = []
    if not material_grade:
        return warnings

    mat_upper = material_grade.upper()

    def _parse_num(val_str: Optional[str]) -> Optional[float]:
        if not val_str:
            return None
        m = re.search(r"([0-9]+(?:\.[0-9]+)?)", val_str)
        return float(m.group(1)) if m else None

    yield_val = _parse_num(mech_dict.get("yield"))
    tensile_val = _parse_num(mech_dict.get("tensile"))

    # ASTM A105 Carbon Steel Forgings (Min Yield: 250 MPa, Min Tensile: 485 MPa)
    if "A105" in mat_upper:
        if yield_val is not None and yield_val < 250:
            warnings.append(f"ASTM A105 Yield Strength ({yield_val} MPa) is below standard minimum (250 MPa).")
        if tensile_val is not None and tensile_val < 485:
            warnings.append(f"ASTM A105 Tensile Strength ({tensile_val} MPa) is below standard minimum (485 MPa).")

    # ASTM A350 LF2 Low Temp Carbon Steel (Min Yield: 250 MPa, Min Tensile: 485 MPa)
    elif "LF2" in mat_upper or "A350" in mat_upper:
        if yield_val is not None and yield_val < 250:
            warnings.append(f"ASTM A350 LF2 Yield Strength ({yield_val} MPa) is below standard minimum (250 MPa).")

    # ASTM A182 F316 / F316L Stainless Steel (Min Yield: 205 MPa for 316, 170 MPa for 316L)
    elif "316" in mat_upper or "F316" in mat_upper:
        min_y = 170 if "316L" in mat_upper else 205
        if yield_val is not None and yield_val < min_y:
            warnings.append(f"Stainless Steel F316 Yield Strength ({yield_val} MPa) is below standard minimum ({min_y} MPa).")

    return warnings


# -----------------------------------------------------------------------------
# 4. Granular Document Type Classification
# -----------------------------------------------------------------------------

def detect_granular_document_type(raw_text: str) -> Tuple[str, str]:
    """
    Returns (doc_type, doc_subtype) for precise document categorization:
      - MTC_EN10204_3_1: Inspection Certificate 3.1
      - MTC_EN10204_3_2: Inspection Certificate 3.2 (Independent TPI Verified)
      - DELIVERY_CHALLAN: Dispatch challan / inward slip
      - PURCHASE_ORDER: Purchase Order requisition
      - VALVE_HYDRO_TEST_REPORT: Pressure test certificate
      - FASTENER_QUALITY_CERTIFICATE: Stud bolt & nut inspection certificate
    """
    upper = raw_text.upper()

    # 1. Delivery Challan / Inward Slip
    if any(k in upper for k in ["DELIVERY CHALLAN", "DISPATCH CHALLAN", "INWARD SLIP", "MATERIAL INWARD", "GATE ENTRY"]):
        return "DELIVERY_CHALLAN", "DELIVERY_CHALLAN_CPSE"

    # 2. Purchase Order
    if any(k in upper for k in ["PURCHASE ORDER", "PO REQUISITION", "ORDER CONFIRMATION"]) and "MILL TEST" not in upper:
        return "PURCHASE_ORDER", "PURCHASE_ORDER_STANDARD"

    # 3. Valve Hydro-Test Report
    if any(k in upper for k in ["HYDROSTATIC TEST", "HYDRO TEST REPORT", "SHELL TEST", "SEAT TEST"]):
        return "VALVE_TEST_REPORT", "VALVE_HYDRO_TEST_REPORT"

    # 4. Fastener Certificate
    if any(k in upper for k in ["FASTENER QUALITY", "STUD BOLT TEST", "NUT TEST", "ASTM A193", "ASTM A194"]):
        if "FLANGE" not in upper and "VALVE" not in upper:
            return "FASTENER_QUALITY_CERTIFICATE", "FASTENER_QUALITY_CERTIFICATE"

    # 5. Inspection Certificate EN 10204 3.2 (Third Party Inspection)
    if any(k in upper for k in ["3.2", "EN 10204 3.2", "TPI", "THIRD PARTY INSPECTION", "LLOYD", "BUREAU VERITAS", "DNV", "TUV"]):
        return "MTC_CERTIFICATE", "MTC_EN10204_3_2"

    # 6. Default MTC EN 10204 3.1
    return "MTC_CERTIFICATE", "MTC_EN10204_3_1"


# -----------------------------------------------------------------------------
# 5. Full MTC Table and Multi-Item Parser
# -----------------------------------------------------------------------------

def parse_mtc_tables(tables: List[List[List[Optional[str]]]], full_text: str) -> Dict[str, Any]:
    """
    Parses tables extracted by pdfplumber or OCR lines into a comprehensive MTC dictionary
    with chemical, mechanical, multi-item descriptions, and compliance validations.
    """
    norm_text = normalize_mtc_text(full_text)
    clean_text = " ".join(norm_text.split())
    lines = norm_text.splitlines()

    doc_type, doc_subtype = detect_granular_document_type(norm_text)

    metadata: Dict[str, Any] = {
        "cert_no": None,
        "po_no": None,
        "heat_no": None,
        "description": None,
        "material_grade": None,
        "standard": None,
        "qty": None,
        "manufacturer": None,
        "doc_subtype": doc_subtype,
        "nace_compliant": False,
        "is_ibr_certified": False,
        "chemical": None,
        "mechanical": None,
        "chemical_dict": {},
        "mechanical_dict": {},
        "carbon_equivalent": None,
        "validation_warnings": [],
        "extracted_items": [],
    }

    # 1. Parse Key-Value Metadata from Table 0 if digital PDF
    if tables and len(tables) > 0:
        meta_table = tables[0]
        for row in meta_table:
            if not row:
                continue
            for i in range(0, len(row) - 1, 2):
                key = str(row[i] or "").strip().lower()
                val = str(row[i + 1] or "").strip().replace("\n", " ")

                if "cert" in key and not metadata["cert_no"]:
                    metadata["cert_no"] = val
                elif "purchase order" in key or "po" in key:
                    metadata["po_no"] = val
                elif "heat" in key or "batch" in key:
                    metadata["heat_no"] = val
                elif "product description" in key or "description" in key:
                    metadata["description"] = val
                elif "material" in key or "grade" in key:
                    metadata["material_grade"] = val
                elif "standard" in key or "governing" in key:
                    metadata["standard"] = val
                elif "quantity" in key or "qty" in key:
                    metadata["qty"] = val

    # 2. Line-by-line check for exact key-value pairs in header
    for line in lines[:45]:
        l_clean = line.strip()
        if not metadata["cert_no"]:
            m_c = re.search(
                r"(?:Cert\.?\s*No\.?|Certificate\s*No\.?|Inspection\s*certificate\s*no\.?|INV\.?\s*NO\.?)\s*[:\s]\s*([A-Z0-9/-]+(?:\s*/\s*[A-Z0-9-]+)?)",
                l_clean,
                re.IGNORECASE,
            )
            if m_c:
                c_val = m_c.group(1).strip()
                if c_val.upper() not in ["DATE", "TPI", "INVOICE", "ACCORDING", "QTY"] and len(c_val) > 2:
                    metadata["cert_no"] = c_val

        if not metadata["po_no"]:
            m_p = re.search(
                r"(?:PO\s*No\.?|Purchase\s*Order|Best\.?Nr\.?\s*/\s*Order\s*no\.?|Order\s*No\.?)\s*[:\s]\s*([A-Z0-9/_-]+)",
                l_clean,
                re.IGNORECASE,
            )
            if m_p:
                p_val = m_p.group(1).strip()
                if p_val.upper() not in ["JINDAL", "CUSTOMER", "DATE", "ARTICLE", "CLIENT"] and len(p_val) > 2:
                    metadata["po_no"] = p_val

    # Regex fallbacks for certificate header fields
    if not metadata["cert_no"]:
        m = re.search(
            r"(?:Certificate\s*No\.?|Cert\.?\s*No\.?|Inspection\s*certificate\s*no\.?|MTC\s*No\.?|INV\.?\s*NO\.?|DC\s*No\.?)[:\s]*([A-Z0-9/-]+(?:\s*/\s*[A-Z0-9-]+)?)",
            clean_text,
            re.IGNORECASE,
        )
        if m:
            c = m.group(1).strip()
            if c.upper() not in ["DATE", "TPI", "INVOICE", "ACCORDING", "QTY"] and len(c) > 2:
                metadata["cert_no"] = c

    # Formal MTC ID pattern like DMI/TC/22-23/581
    if not metadata["cert_no"]:
        m_dm = re.search(r"\b([A-Z]{2,4}/(?:TC|MTC)/[A-Z0-9/-]+)\b", norm_text, re.IGNORECASE)
        if m_dm:
            metadata["cert_no"] = m_dm.group(1).strip()

    # German Abnahmeprüfzeugnis pattern
    if not metadata["cert_no"]:
        m_ab = re.search(r"Abnahmepr[a-zA-Z\W]*Nr\.?[:\s]*([0-9A-Z/ -]+?)(?:\s+[0-9]{4}|\s+Inspection|\n|$)", norm_text, re.IGNORECASE)
        if m_ab:
            metadata["cert_no"] = m_ab.group(1).strip()

    if not metadata["po_no"]:
        m_po = re.search(r"\b(PO/[A-Z0-9/_-]+|FPS\s*[-–]\s*[0-9]+)\b", norm_text, re.IGNORECASE)
        if m_po:
            metadata["po_no"] = m_po.group(1).replace(" ", "").strip()

    if not metadata["po_no"]:
        m = re.search(
            r"(?:Purchase\s*Order|PO\s*No\.?|Order\s*No\.?|Best\.?Nr\.?\s*/\s*Order\s*no\.?|P\.O\.\s*NO\.?)[:\s]*([A-Z0-9/_-]+)",
            clean_text,
            re.IGNORECASE,
        )
        if m:
            p = m.group(1).strip()
            if p.upper() not in ["ARTICLE", "CLIENT", "DATE"] and len(p) > 2:
                metadata["po_no"] = p

    if not metadata["heat_no"]:
        m = re.search(
            r"(?:Heat\s*(?:/\s*Batch)?\s*(?:No\.?|Number)|HT/LT\s*No\.?|Charge\s*No\.?)[:\s]*([A-Z0-9-]+)",
            clean_text,
            re.IGNORECASE,
        )
        if m:
            metadata["heat_no"] = m.group(1).strip()

    if not metadata["material_grade"]:
        m = re.search(
            r"\b(ASTM\s*A105[A-Z0-9-]*|ASTM\s*A815[A-Z0-9-\s]*S32750|ASTM\s*A182[A-Z0-9-\s]*|ASTM\s*A216\s*WCB|ASTM\s*A350\s*LF2|316L(?:\s*/\s*1\.4404)?|SA105|A105)\b",
            clean_text,
            re.IGNORECASE,
        )
        if m:
            metadata["material_grade"] = m.group(1).strip()

    if not metadata["standard"]:
        m = re.search(
            r"\b(ASME\s*B16\.5[A-Z0-9-]*|ASME\s*B16\.9[A-Z0-9-]*|ASME\s*B16\.20|ASME\s*B16\.34|API\s*600|API\s*6D|EN\s*10204(?:\s*[-:]?\s*(?:3\.1\.?B?|2\.2|3\.2))?)\b",
            clean_text,
            re.IGNORECASE,
        )
        if m:
            metadata["standard"] = m.group(1).strip()

    # 3. Chemical and Mechanical tables
    if len(tables) > 1:
        chem_table = tables[1]
        if len(chem_table) >= 2:
            headers = [str(c or "").strip() for c in chem_table[0]]
            values = [str(c or "").strip() for c in chem_table[1]]
            metadata["chemical"] = [headers, values]
            metadata["chemical_dict"] = {h: v for h, v in zip(headers, values) if h and v}

    if len(tables) > 2:
        mech_table = tables[2]
        if len(mech_table) >= 2:
            headers = [str(c or "").strip() for c in mech_table[0]]
            values = [str(c or "").strip() for c in mech_table[1]]
            metadata["mechanical"] = [headers, values]
            metadata["mechanical_dict"] = {h: v for h, v in zip(headers, values) if h and v}

    # Text fallback for chemical and mechanical
    if not metadata["chemical_dict"]:
        text_chem = extract_chemical_from_text(norm_text)
        if text_chem:
            metadata["chemical_dict"] = text_chem
            metadata["chemical"] = [list(text_chem.keys()), list(text_chem.values())]

    if not metadata["mechanical_dict"]:
        text_mech = extract_mechanical_from_text(norm_text)
        if text_mech:
            metadata["mechanical_dict"] = text_mech
            metadata["mechanical"] = [list(text_mech.keys()), list(text_mech.values())]

    # Carbon Equivalent (CE) computation
    if metadata["chemical_dict"]:
        ce_res = compute_carbon_equivalent(metadata["chemical_dict"])
        if ce_res:
            metadata["carbon_equivalent"] = ce_res
            if not ce_res["is_standard_weldable"]:
                metadata["validation_warnings"].append(
                    f"Elevated Carbon Equivalent ({ce_res['carbon_equivalent']}%) exceeds standard weldability limit (0.43%). Preheat required."
                )

    # Mechanical threshold validation
    mech_warnings = validate_mechanical_thresholds(metadata["material_grade"], metadata["mechanical_dict"])
    if mech_warnings:
        metadata["validation_warnings"].extend(mech_warnings)

    # Manufacturer / Provider detection
    m_prov = re.search(r"(?:PROVIDER|MANUFACTURER|MILL|SUPPLIER)[:\s]*([A-Z0-9\s.,&-]+?)(?:\n|BUYER|GOODS|CERTIFICATE|ORDER|$)", norm_text, re.IGNORECASE)
    if m_prov:
        prov = m_prov.group(1).strip()
        if len(prov) > 3 and prov.upper() not in ["GENERAL", "THE", "ORDER", "QUALITY"]:
            metadata["manufacturer"] = prov
    if not metadata["manufacturer"]:
        if "MAG GENERAL" in norm_text:
            metadata["manufacturer"] = "MAG GENERAL BUSINESS"
        elif "JINDAL" in norm_text:
            metadata["manufacturer"] = "Jindal Steel & Power Ltd."
        elif "VIRAJ" in norm_text:
            metadata["manufacturer"] = "Viraj Profiles Ltd."

    # NACE and IBR Compliance
    if re.search(r"\b(NACE|MR0175|MR[-\s]?0175|ISO\s*15156)\b", norm_text, re.IGNORECASE):
        metadata["nace_compliant"] = True
        metadata["is_sour_service"] = True

    if re.search(r"\b(IBR|INDIAN\s*BOILER\s*REG(?:ULATION)?S?)\b", norm_text, re.IGNORECASE):
        if not re.search(r"\b(NON[-\s]?IBR)\b", norm_text, re.IGNORECASE):
            metadata["is_ibr_certified"] = True

    # 4. Multi-Item Line Extraction
    extracted_items = []
    for line in lines:
        l = line.strip()
        if len(l) < 5:
            continue
        u = l.upper()

        # Skip non-product narrative sections
        if any(h in u for h in [
            "WE HEREBY", "MANUFACTURING", "TEST REPORT", "ALL PRODUCTS",
            "TEST CERTIFICATE BELONGS", "NON DESTRUCTIVE", "CHEMICAL COMPOSITION",
            "MECHANICAL PROPERTIES", "REQUIREMENTS", "HEAT NO", "CUSTOMER CODE",
        ]):
            continue

        # Check for item markers
        is_item = False
        if any(k in u for k in [
            "SLIP ON", "WELDING NECK", "WELD NECK", "WN FLG", "BLIND",
            "FLANGE", "HANGE", "FLG", "ELBOW", "VALVE", "ACTUATOR", "FERRULE", "SCH 40", "SCH 160", "SCH40", "SCH160"
        ]):
            if u not in ["DESCRIPTION", "ITEM DESCRIPTION", "PRODUCTS DESCRIPTION", "PRODUCT", "PRODUCT DESCRIPTION"]:
                is_item = True
        elif re.search(r"\b(?:[0-9]+(?:\s*[0-9]/[0-9])?|\d+/\d+)\s*(?:\"|IN|INCH)?\s*(?:150|300|600|900|1500)#?\s*(?:BLRF|WNRF|BLRTJ|WNRTJ|SORF|RF|RTJ|WN|BL|SO)\b", u):
            is_item = True

        if is_item:
            # Enrich item description if missing global standard or material
            enrich_text = l
            if metadata["material_grade"] and not any(m in enrich_text.upper() for m in ["A105", "316", "304", "WCB", "LF2", "S32750"]):
                enrich_text += f", {metadata['material_grade']}"
            if metadata["standard"] and not any(s in enrich_text.upper() for s in ["B16.5", "B16.9", "B16.34", "API"]):
                enrich_text += f", {metadata['standard']}"

            item_attrs = extract_attributes(enrich_text)
            if item_attrs.item_type or item_attrs.size_nb_mm or item_attrs.pressure_class:
                extracted_items.append({
                    "raw_line": l,
                    "enriched_text": enrich_text,
                    "attributes": item_attrs.model_dump(),
                })

    metadata["extracted_items"] = extracted_items

    # 5. Set Primary Description & Extracted Attributes
    if not metadata["description"]:
        if extracted_items:
            sorted_items = sorted(
                extracted_items,
                key=lambda x: (
                    1 if x["attributes"].get("size_nb_mm") else 0,
                    1 if x["attributes"].get("pressure_class") else 0,
                    1 if x["attributes"].get("facing_end") else 0,
                    len(x["raw_line"]),
                ),
                reverse=True,
            )
            metadata["description"] = sorted_items[0]["raw_line"]
            primary_specs = sorted_items[0]["attributes"]
        else:
            m = re.search(r"(?:Product\s*Description)[:\s]*([^,;]+?)(?:Quantity|Material|$)", clean_text, re.IGNORECASE)
            if m:
                metadata["description"] = m.group(1).strip()
            else:
                metadata["description"] = clean_text[:200]
            desc_to_parse = metadata["description"]
            extracted_specs = extract_attributes(desc_to_parse)
            if not extracted_specs.metallurgy and metadata["material_grade"]:
                extracted_specs.metallurgy = metadata["material_grade"]
            if not extracted_specs.standard and metadata["standard"]:
                extracted_specs.standard = metadata["standard"]
            primary_specs = extracted_specs.model_dump()
    else:
        desc_to_parse = metadata["description"]
        extracted_specs = extract_attributes(desc_to_parse)
        if not extracted_specs.metallurgy and metadata["material_grade"]:
            extracted_specs.metallurgy = metadata["material_grade"]
        if not extracted_specs.standard and metadata["standard"]:
            extracted_specs.standard = metadata["standard"]
        primary_specs = extracted_specs.model_dump()

    metadata["extracted_attributes"] = primary_specs
    metadata["items_count"] = len(extracted_items)
    metadata["primary_item"] = metadata.get("description")
    return metadata
