"""
EN 10204 3.1 / 3.2 Material Test Certificate (MTC) & Procurement Intake Parser.

Extracts:
1. Header: Heat/Melt No, Certificate No, Purchase Order (PO), Manufacturer, TPI Agency.
2. Chemical Composition: C, Mn, Si, P, S, Cr, Ni, Mo, V, Cu, N.
3. Carbon Equivalent (IIW CE) & PREN Calculations.
4. Mechanical Properties: Yield Strength, Tensile Strength, Elongation, Charpy Impact, Hardness.
5. ASTM Non-Conformance Detection & Graceful Degradation Handling.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

from backend.app.schemas.material import ExtractedMaterialAttributes
from ml.vision.chemistry import (
    compute_carbon_equivalent,
    classify_weldability,
    compute_pren,
    validate_composition,
    validate_mechanical_properties,
)


KNOWN_TPI_AGENCIES = [
    "BUREAU VERITAS", "LLOYD'S REGISTER", "LLOYDS", "DNV", "DNV GL",
    "TUV", "TÜV", "ENGINEERS INDIA LIMITED", "EIL", "INDIAN REGISTER OF SHIPPING", "IRS",
    "SGS", "INTERTEK", "CEIL", "ABS", "AMERICAN BUREAU OF SHIPPING"
]

KNOWN_MANUFACTURERS = [
    "LARSEN & TOUBRO", "L&T", "STEEL AUTHORITY OF INDIA", "SAIL", "JINDAL STEEL",
    "JINDAL", "TATA STEEL", "BHARAT HEAVY ELECTRICALS", "BHEL", "WELSPUN",
    "RATNAMANI", "MSL", "MAHARASHTRA SEAMLESS", "ISMT", "TUBACEX", "SANDVIK"
]


class MTCParser:
    """
    Parses raw text extracted from MTC certificates, invoices, and inspection challans.
    """

    def parse_header(self, text: str) -> Dict[str, Any]:
        """
        Extracts certificate header metadata: Cert No, Heat No, PO No, Manufacturer, TPI.
        """
        # Certificate Number
        cert_no = self._search_patterns(text, [
            r'(?:Certificate|Cert|TC)\s*(?:No|Number|#)[.:\s]+([A-Z0-9/_-]+)',
            r'EN\s*10204\s*3\.[12]\s*[:\s|]+(?:Certificate\s*No:?\s*)?([A-Z0-9/_-]+)',
            r'MTC[/\s]+([0-9]{4}[/\s]+[0-9]+)',
        ])

        # Heat / Melt Number
        heat_no = self._search_patterns(text, [
            r'(?:Heat|Melt|Cast|Batch)\s*(?:No|Number|#)[.:\s]+([A-Z0-9_-]+)',
            r'HT-([0-9]{4}-[0-9]+)',
            r'Heat[.:\s]+([A-Z0-9]+)',
        ])

        # PO Number
        po_no = self._search_patterns(text, [
            r'(?:Purchase\s*Order|PO|P\.O\.)\s*(?:No|Number|#)?[.:\s]+([A-Z0-9_-]+)',
            r'PO-([A-Z0-9_-]+)',
        ])

        # Material Grade
        material_grade = self._search_patterns(text, [
            r'(?:Material\s*Grade|Grade|Steel\s*Grade)[.:\s]+(ASTM\s+[A-Z0-9.-]+(?:\s+(?:GR\.?|CLASS)\s*[A-Z0-9]+)?)',
            r'(?:Material\s*Grade|Grade|Spec)[.:\s]+([A-Z0-9.-]+(?:\s+(?:GR\.?|CLASS)\s*[A-Z0-9]+)?)',
            r'\b(ASTM\s+A[0-9]{3}[A-Z0-9.-]*)\b',
            r'\b(A350\s+LF2|A105|A182\s+F316L?|A182\s+F304L?|A182\s+F51|A106\s+GR\.?\s*B|A193\s+B7)\b',
        ])
        if material_grade:
            material_grade = material_grade.split("\n")[0].split("|")[0].strip()

        # Specification
        spec = "EN 10204 3.1"
        if "3.2" in text:
            spec = "EN 10204 3.2"

        # Manufacturer
        manufacturer = self._find_known_entity(text, KNOWN_MANUFACTURERS)
        if not manufacturer:
            m = re.search(r'Manufacturer[.:\s]+([^\n\r|,]+)', text, re.IGNORECASE)
            if m:
                manufacturer = m.group(1).strip()

        # TPI Agency
        tpi_agency = self._find_known_entity(text, KNOWN_TPI_AGENCIES)
        if not tpi_agency:
            m = re.search(r'(?:Third\s*Party\s*Inspection|TPI|Inspected\s*by)[.:\s]+([^\n\r|,]+)', text, re.IGNORECASE)
            if m:
                tpi_agency = m.group(1).strip()

        return {
            "certificate_no": cert_no,
            "heat_no": heat_no,
            "po_no": po_no,
            "material_grade": material_grade,
            "specification": spec,
            "manufacturer": manufacturer or "UNKNOWN_MANUFACTURER",
            "tpi_agency": tpi_agency or "INTERNAL_MILL_INSPECTION",
        }

    def parse_chemical_composition(self, text: str) -> Dict[str, float]:
        """
        Extracts chemical elemental percentages: C, Mn, Si, P, S, Cr, Ni, Mo, V, Cu, N.
        """
        elements = ["C", "Mn", "Si", "P", "S", "Cr", "Ni", "Mo", "V", "Cu", "N", "Nb", "Ti"]
        comp: Dict[str, float] = {}

        for el in elements:
            # Pattern 1: e.g. "C: 0.18%" or "C = 0.18" or "C 0.180"
            pattern1 = rf'\b{el}\s*[:=]\s*([0-9]+\.?[0-9]*)\s*%?'
            m = re.search(pattern1, text, re.IGNORECASE)
            if m:
                try:
                    val = float(m.group(1))
                    if 0.0 <= val <= 35.0:
                        comp[el] = val
                        continue
                except ValueError:
                    pass

            # Pattern 2: Bar pipe separated "C: 0.18 | Mn: 1.05"
            pattern2 = rf'\b{el}\s*[:\s]\s*([0-9]+\.[0-9]+)'
            m2 = re.search(pattern2, text)
            if m2:
                try:
                    val = float(m2.group(1))
                    if 0.0 <= val <= 35.0:
                        comp[el] = val
                except ValueError:
                    pass

        return comp

    def parse_mechanical_properties(self, text: str) -> Dict[str, float]:
        """
        Extracts yield strength, tensile strength, elongation, Charpy impact, and hardness.
        """
        props: Dict[str, float] = {}

        # Yield Strength (Re / Rp0.2)
        ys = self._extract_float(text, [
            r'(?:Yield\s*Strength|YS|Re|Rp0\.2)(?:\s*\([^)]*\))?[.:\s=]+([0-9]+\.?[0-9]*)\s*(?:MPa|N/mm2)?',
            r'\bRe\b(?:\s*\([^)]*\))?[.:\s=]+([0-9]+)',
        ])
        if ys:
            props["yield_strength_mpa"] = ys

        # Tensile Strength (Rm)
        ts = self._extract_float(text, [
            r'(?:Tensile\s*Strength|UTS|Rm)(?:\s*\([^)]*\))?[.:\s=]+([0-9]+\.?[0-9]*)\s*(?:MPa|N/mm2)?',
            r'\bRm\b(?:\s*\([^)]*\))?[.:\s=]+([0-9]+)',
        ])
        if ts:
            props["tensile_strength_mpa"] = ts

        # Elongation (A / A5)
        el = self._extract_float(text, [
            r'(?:Elongation|EL|A5|A%|A)(?:\s*\([^)]*\))?[.:\s=]+([0-9]+\.?[0-9]*)\s*%?',
            r'Elongation\s*\(A5\)\s*[:=]\s*([0-9]+)',
        ])
        if el:
            props["elongation_pct"] = el

        # Charpy V-Notch Impact Toughness (Joules)
        imp = self._extract_float(text, [
            r'(?:Charpy|Impact|CVN)(?:\s*\([^)]*\))?[^:\n\r]*[:=]+([0-9]+\.?[0-9]*)\s*(?:J|Joules)?',
            r'Toughness\s*[:=]\s*([0-9]+)\s*J',
        ])
        if imp:
            props["impact_joules_charpy"] = imp

        # Hardness (HBW / HRC / HRB)
        hb = self._extract_float(text, [
            r'(?:Hardness|Brinell|HBW|HB|HRC)(?:\s*\([^)]*\))?[.:\s=]+([0-9]+\.?[0-9]*)',
        ])
        if hb:
            props["hardness_hb"] = hb

        return props

    def parse_full_mtc(self, raw_text: str, confidence_score: float = 1.0) -> Dict[str, Any]:
        """
        Performs end-to-end MTC intelligence extraction and computes Carbon Equivalent,
        PREN, and ASTM conformance checks.
        """
        header = self.parse_header(raw_text)
        chemistry = self.parse_chemical_composition(raw_text)
        mechanical = self.parse_mechanical_properties(raw_text)

        # Carbon Equivalent (IIW)
        ce = compute_carbon_equivalent(chemistry)
        weldability = classify_weldability(ce)

        # PREN (Pitting Resistance)
        pren = compute_pren(chemistry)

        # ASTM Validation
        grade = header.get("material_grade") or ""
        chem_valid, chem_violations = validate_composition(chemistry, grade)
        mech_valid, mech_violations = validate_mechanical_properties(mechanical, grade)

        is_conforming = chem_valid and mech_valid
        all_violations = chem_violations + mech_violations

        # Detect item type / dimensions from description in text
        size_nb_mm = self._extract_dimension_size(raw_text)
        pressure_class = self._extract_pressure_class(raw_text)
        schedule = self._extract_schedule(raw_text)
        facing_end = self._extract_facing(raw_text)
        item_type = self._extract_item_type(raw_text)

        # Graceful degradation assessment
        missing_attrs = []
        if not size_nb_mm:
            missing_attrs.append("size_nb_mm")
        if not pressure_class and item_type in ("FLANGE", "GATE_VALVE", "VALVE"):
            missing_attrs.append("pressure_class")
        if not schedule and item_type == "PIPE":
            missing_attrs.append("schedule")
        if not header.get("material_grade"):
            missing_attrs.append("material_grade")

        is_incomplete = len(missing_attrs) > 0 or confidence_score < 0.70
        requires_hitl = is_incomplete or not is_conforming

        return {
            "header": header,
            "chemical_composition": chemistry,
            "carbon_equivalent_iiw": ce,
            "weldability": weldability,
            "pren": pren,
            "mechanical_properties": mechanical,
            "conforms_to_astm": is_conforming,
            "non_conformance_warnings": all_violations,
            "item_type": item_type,
            "size_nb_mm": size_nb_mm,
            "pressure_class": pressure_class,
            "schedule": schedule,
            "facing_end": facing_end,
            "is_incomplete": is_incomplete,
            "missing_attributes": missing_attrs,
            "requires_hitl": requires_hitl,
            "confidence_score": confidence_score,
        }

    def to_material_attributes(self, parsed_mtc: Dict[str, Any]) -> ExtractedMaterialAttributes:
        """
        Converts parsed MTC data into the canonical ExtractedMaterialAttributes schema.
        """
        header = parsed_mtc.get("header", {})
        props = {
            "heat_no": header.get("heat_no"),
            "certificate_no": header.get("certificate_no"),
            "po_no": header.get("po_no"),
            "manufacturer": header.get("manufacturer"),
            "tpi_agency": header.get("tpi_agency"),
            "carbon_equivalent_iiw": parsed_mtc.get("carbon_equivalent_iiw"),
            "weldability": parsed_mtc.get("weldability"),
            "pren": parsed_mtc.get("pren"),
            "chemistry": parsed_mtc.get("chemical_composition", {}),
            "mechanical": parsed_mtc.get("mechanical_properties", {}),
            "astm_conformance": parsed_mtc.get("conforms_to_astm", True),
            "non_conformance_warnings": parsed_mtc.get("non_conformance_warnings", []),
        }

        return ExtractedMaterialAttributes(
            item_type=parsed_mtc.get("item_type"),
            size_nb_mm=parsed_mtc.get("size_nb_mm"),
            pressure_class=parsed_mtc.get("pressure_class"),
            schedule=parsed_mtc.get("schedule"),
            metallurgy=header.get("material_grade"),
            facing_end=parsed_mtc.get("facing_end"),
            standard=header.get("specification", "EN 10204 3.1"),
            properties=props,
            is_incomplete=parsed_mtc.get("is_incomplete", False),
            missing_attributes=parsed_mtc.get("missing_attributes", []),
            confidence_score=parsed_mtc.get("confidence_score", 1.0),
            requires_hitl=parsed_mtc.get("requires_hitl", False),
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _search_patterns(self, text: str, patterns: List[str]) -> Optional[str]:
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _extract_float(self, text: str, patterns: List[str]) -> Optional[float]:
        s = self._search_patterns(text, patterns)
        if s:
            try:
                return float(s)
            except ValueError:
                pass
        return None

    def _find_known_entity(self, text: str, entities: List[str]) -> Optional[str]:
        t_upper = text.upper()
        for ent in entities:
            if ent in t_upper:
                return ent
        return None

    def _extract_dimension_size(self, text: str) -> Optional[float]:
        # Look for e.g. 4", 4IN, 100 mm, DN100
        m = re.search(r'\b([0-9]+(?:\.[0-9]+)?)\s*(?:INCH|IN|")\b', text, re.IGNORECASE)
        if m:
            try:
                return round(float(m.group(1)) * 25.4, 2)
            except ValueError:
                pass

        m2 = re.search(r'\b(?:DN|NB)\s*([0-9]+)\b', text, re.IGNORECASE)
        if m2:
            try:
                return float(m2.group(1))
            except ValueError:
                pass

        m3 = re.search(r'\b([0-9]+(?:\.[0-9]+)?)\s*MM\b', text, re.IGNORECASE)
        if m3:
            try:
                return float(m3.group(1))
            except ValueError:
                pass
        return None

    def _extract_pressure_class(self, text: str) -> Optional[int]:
        m = re.search(r'\b(?:CLASS|#)\s*([0-9]{3,4})\b', text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
        m2 = re.search(r'\b([0-9]{3,4})\s*(?:#|LBS|CLASS)\b', text, re.IGNORECASE)
        if m2:
            try:
                return int(m2.group(1))
            except ValueError:
                pass
        return None

    def _extract_schedule(self, text: str) -> Optional[str]:
        m = re.search(r'\b(?:SCH|SCHEDULE)\s*([0-9]+[A-Z]?|STD|XS|XXS)\b', text, re.IGNORECASE)
        if m:
            return f"SCH {m.group(1).upper()}"
        return None

    def _extract_facing(self, text: str) -> Optional[str]:
        m = re.search(r'\b(RF|RTJ|FF|BW|SW)\b', text, re.IGNORECASE)
        return m.group(1).upper() if m else None

    def _extract_item_type(self, text: str) -> Optional[str]:
        t = text.upper()
        if "FLANGE" in t:
            return "FLANGE"
        if "GATE VALVE" in t:
            return "GATE_VALVE"
        if "VALVE" in t:
            return "VALVE"
        if "PIPE" in t:
            return "PIPE"
        if "STUD" in t or "BOLT" in t:
            return "STUD_BOLT"
        if "GASKET" in t:
            return "GASKET"
        if "PUMP" in t:
            return "PUMP"
        return "UNKNOWN_EQUIPMENT"
