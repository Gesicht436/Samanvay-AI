"""
Mill Test Certificate (MTC) and Delivery Challan Parser (EN 10204 3.1 / 3.2).
Extracts structured inspection metadata, heat numbers, chemical compositions, mechanical properties,
and multi-item line descriptions from digital PDFs and scanned OCR documents.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from backend.app.ml.ner_tagger import extract_attributes

logger = logging.getLogger(__name__)


def normalize_mtc_text(text: str) -> str:
    """Corrects common OCR character misreads found in industrial piping certificates."""
    t = text
    t = re.sub(r"\bASME\s*816\b", "ASME B16", t, flags=re.IGNORECASE)
    t = re.sub(r"\bANSI\s*816\b", "ANSI B16", t, flags=re.IGNORECASE)
    t = re.sub(r"\b816\.([0-9])\b", r"B16.\1", t, flags=re.IGNORECASE)
    t = re.sub(r"\bA\s*105\b", "ASTM A105", t, flags=re.IGNORECASE)
    t = re.sub(r"\bSA\s*105\b", "ASME SA105", t, flags=re.IGNORECASE)
    t = re.sub(r"\bA\s*815\b", "ASTM A815", t, flags=re.IGNORECASE)
    t = re.sub(r"\bA\s*182\b", "ASTM A182", t, flags=re.IGNORECASE)
    t = re.sub(r"\bFig\.\b", "Flg.", t, flags=re.IGNORECASE)
    t = re.sub(r"\bFIg\.\b", "Flg.", t, flags=re.IGNORECASE)
    t = re.sub(r"\b\[NV\b", "INV", t, flags=re.IGNORECASE)
    t = re.sub(r"\b150\*\b", "150#", t)
    t = re.sub(r"\b300\*\b", "300#", t)
    t = re.sub(r"\b600\*\b", "600#", t)
    t = re.sub(r"\b900\*\b", "900#", t)
    t = re.sub(r"\bBLRTI\b", "BLRTJ", t, flags=re.IGNORECASE)
    t = re.sub(r"\baLRTJ\b", "BLRTJ", t)
    return t


def extract_chemical_from_text(text: str) -> Dict[str, str]:
    """Extracts chemical elemental percentages from OCR text or certificate text."""
    chem: Dict[str, str] = {}
    elements = ["C", "Mn", "Si", "P", "S", "Cr", "Ni", "Mo", "Cu", "V", "Al", "Ti"]
    
    # 1. Key-value style: e.g. "C: 0.19%", "Mn = 0.66"
    for el in elements:
        pat = rf"\b{el}\s*[:=\s]\s*([0-9]+\.[0-9]+)\s*%?"
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


def extract_mechanical_from_text(text: str) -> Dict[str, str]:
    """Extracts mechanical properties (Tensile, Yield, Elongation, Hardness) from text."""
    mech: Dict[str, str] = {}

    # Tensile strength (Rm)
    m_ts = re.search(r"(?:Tensile\s*(?:Strength)?|Rm|T\.S\.)\s*(?:\(?[A-Za-z]+\)?)?[:\s]*(?:Min\.?)?\s*([0-9]{3,4})\s*(?:MPa|N/mm2|KSI)?", text, re.IGNORECASE)
    if m_ts:
        mech["tensile"] = f"{m_ts.group(1)} MPa"

    # Yield strength (ReH / Rp0.2)
    m_ys = re.search(r"(?:Yield\s*(?:Strength)?|ReH|Rp0\.2|Y\.S\.)\s*(?:\(?[A-Za-z]+\)?)?[:\s]*(?:Min\.?)?\s*([0-9]{3,4})\s*(?:MPa|N/mm2|KSI)?", text, re.IGNORECASE)
    if m_ys:
        mech["yield"] = f"{m_ys.group(1)} MPa"

    # Elongation (A / A5)
    m_el = re.search(r"(?:Elongation|Elong|A5?)\s*(?:\(?[A-Za-z%]+\)?)?[:\s]*(?:Min\.?)?\s*([0-9]{1,2}(?:\.[0-9]+)?)\s*%", text, re.IGNORECASE)
    if m_el:
        mech["elongation"] = f"{m_el.group(1)}%"
    else:
        m_el2 = re.search(r"\bElongation\b.*?([1-4][0-9])\b", text, re.IGNORECASE | re.DOTALL)
        if m_el2:
            mech["elongation"] = f"{m_el2.group(1)}%"

    # Hardness (HB / HRC / HBW)
    m_hb = re.search(r"(?:Hardness|HBW?|HRC|HV)\s*(?:\(?[A-Za-z]+\)?)?[:\s]*(?:Max\.?)?\s*([0-9]{2,3})\s*(?:HBW?|HRC|HV)?", text, re.IGNORECASE)
    if m_hb:
        mech["hardness"] = f"{m_hb.group(1)} HB"

    # Heat Treatment
    m_ht = re.search(r"\b(NORMALIZED(?:\s*[0-9]+DEG(?:\s*C(?:ENTIGRADE)?)?)?|QUENCHED\s*(?:&|AND)\s*TEMPERED|ANNEALED|SOLUTION\s*ANNEALED)\b", text, re.IGNORECASE)
    if m_ht:
        mech["heat_treatment"] = m_ht.group(1).strip()

    return mech


def parse_mtc_tables(tables: List[List[List[Optional[str]]]], full_text: str) -> Dict[str, Any]:
    """
    Parses tables extracted by pdfplumber or OCR lines into structured MTC dictionary.
    """
    norm_text = normalize_mtc_text(full_text)
    clean_text = " ".join(norm_text.split())
    lines = norm_text.splitlines()

    metadata: Dict[str, Any] = {
        "cert_no": None,
        "po_no": None,
        "heat_no": None,
        "description": None,
        "material_grade": None,
        "standard": None,
        "qty": None,
        "manufacturer": None,
        "nace_compliant": False,
        "chemical": None,
        "mechanical": None,
        "chemical_dict": {},
        "mechanical_dict": {},
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
    for line in lines[:40]:
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

    # Pattern for formal MTC IDs like DMI/TC/22-23/581
    if not metadata["cert_no"]:
        m_dm = re.search(r"\b([A-Z]{2,4}/(?:TC|MTC)/[A-Z0-9/-]+)\b", norm_text, re.IGNORECASE)
        if m_dm:
            metadata["cert_no"] = m_dm.group(1).strip()

    # Pattern for German Abnahmeprüfzeugnis
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

    # 3. Chemical and Mechanical tables (digital PDF or OCR text extraction)
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

    # Fallback text-based chemical and mechanical extraction for scanned OCR documents
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

    # NACE MR0175 / ISO 15156 sour service detection
    if re.search(r"\b(NACE|MR0175|MR[-\s]?0175|ISO\s*15156)\b", norm_text, re.IGNORECASE):
        metadata["nace_compliant"] = True
        metadata["is_sour_service"] = True

    # 4. Multi-Item Line Extraction
    extracted_items = []
    lines = norm_text.splitlines()

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
            # Only record if meaningful mechanical attributes could be recognized
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
            # Prefer items with specific physical dimensions and ratings over generic category headers
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

