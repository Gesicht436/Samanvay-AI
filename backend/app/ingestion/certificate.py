import re

from backend.app.contracts.ingestion import ChemicalComposition, MechanicalProperty, MTCRecord


def _field(text: str, *labels: str) -> str | None:
    label = "|".join(re.escape(item) for item in labels)
    # Certificates use both ``Label: value`` and a two-line ``Label:\nvalue``
    # layout. Match the label at a line start and use the next non-empty line
    # when the value is printed below it.
    match = re.search(rf"(?:^|\n)\s*(?:{label})\s*[:#-]?\s*([^\n|]*)", text, re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).strip()
    if value:
        return value
    for line in text[match.end():].splitlines():
        value = line.strip()
        if value:
            return value
    return None


def _number(text: str, *labels: str) -> float | None:
    value = _field(text, *labels)
    if not value:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
    return float(match.group()) if match else None


def mechanical_table_values(text: str) -> dict[str, float]:
    """Read the common header-row/value-row mechanical-properties table."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    start = next((index for index, line in enumerate(lines) if "mechanical" in line.lower()), None)
    if start is None:
        return {}

    headers: list[str] = []
    values: list[float] = []
    for line in lines[start + 1:]:
        lowered = line.lower()
        if "yield" in lowered:
            headers.append("yield_strength_mpa")
        elif "tensile" in lowered:
            headers.append("tensile_strength_mpa")
        elif "elongation" in lowered:
            headers.append("elongation_pct")
        elif re.fullmatch(r"-?\d+(?:\.\d+)?", line.replace(",", "")):
            values.append(float(line.replace(",", "")))
            if headers and len(values) >= len(headers):
                break

    return {header: values[index] for index, header in enumerate(headers) if index < len(values)}


_ELEMENTS = {
    "C": "Carbon",
    "CARBON": "Carbon",
    "MN": "Manganese",
    "MANGANESE": "Manganese",
    "SI": "Silicon",
    "SILICON": "Silicon",
    "S": "Sulfur",
    "SULFUR": "Sulfur",
    "P": "Phosphorus",
    "PHOSPHORUS": "Phosphorus",
    "CR": "Chromium",
    "CHROMIUM": "Chromium",
    "NI": "Nickel",
    "NICKEL": "Nickel",
    "MO": "Molybdenum",
    "MOLYBDENUM": "Molybdenum",
    "CU": "Copper",
    "COPPER": "Copper",
    "V": "Vanadium",
    "VANADIUM": "Vanadium",
    "NB": "Niobium",
    "NIOBIUM": "Niobium",
    "N": "Nitrogen",
    "NITROGEN": "Nitrogen",
    "AL": "Aluminium",
    "ALUMINUM": "Aluminium",
    "ALUMINIUM": "Aluminium",
    "W": "Tungsten",
    "TUNGSTEN": "Tungsten",
    "CO": "Cobalt",
    "COBALT": "Cobalt",
    "TI": "Titanium",
    "TITANIUM": "Titanium",
    "B": "Boron",
    "BORON": "Boron",
}
_ELEMENT_TOKENS = sorted(_ELEMENTS, key=len, reverse=True)
_NUMBER_PATTERN = r"([+-]?\d+(?:\.\d+)?)"


def chemical_composition_values(text: str) -> list[ChemicalComposition]:
    """Extract labelled chemistry and header/value chemistry tables from MTC text."""
    found: dict[str, ChemicalComposition] = {}
    label_pattern = "|".join(re.escape(token) for token in _ELEMENT_TOKENS)
    inline_pattern = re.compile(
        rf"(?<![A-Za-z])({label_pattern})(?![A-Za-z])\s*[:=]?\s*{_NUMBER_PATTERN}\s*(%)?",
        re.IGNORECASE,
    )
    for match in inline_pattern.finditer(text):
        element = _ELEMENTS[match.group(1).upper()]
        found[element] = ChemicalComposition(
            element=element,
            value=float(match.group(2)),
            unit=match.group(3) or "%",
        )

    lines = [line.strip().replace("|", " ") for line in text.splitlines() if line.strip()]
    in_chemistry = False
    headers: list[str] = []
    for line in lines:
        lowered = line.casefold()
        if "chemical" in lowered or "chemistry" in lowered:
            in_chemistry = True
            headers = []
            continue
        if in_chemistry and "mechanical" in lowered:
            in_chemistry = False
            headers = []
        if not in_chemistry:
            continue
        tokens = re.findall(r"[A-Za-z]+", line)
        normalized_tokens = [token.upper() for token in tokens]
        if len(normalized_tokens) >= 2 and all(token in _ELEMENTS for token in normalized_tokens):
            headers = [_ELEMENTS[token] for token in normalized_tokens]
            continue
        if not headers:
            continue
        values = [float(value.replace(",", "")) for value in re.findall(r"(?<![A-Za-z])[-+]?\d+(?:,\d{3})*(?:\.\d+)?", line)]
        if len(values) < len(headers):
            continue
        for element, value in zip(headers, values):
            found[element] = ChemicalComposition(element=element, value=value, unit="%")
        headers = []

    return list(found.values())


def mechanical_property_values(text: str) -> list[MechanicalProperty]:
    extracted = mechanical_table_values(text)
    definitions = {
        "yield_strength": ("yield strength", "yield"),
        "tensile_strength": ("tensile strength", "tensile"),
        "elongation": ("elongation",),
        "hardness": ("hardness",),
        "impact_energy": ("impact energy", "charpy"),
    }
    properties: dict[str, MechanicalProperty] = {}
    for property_name, labels in definitions.items():
        for label in labels:
            match = re.search(
                rf"(?:^|\n)\s*{re.escape(label)}(?:\s*\([^)\n]*\))?\s*[:#-]?\s*{_NUMBER_PATTERN}",
                text,
                re.IGNORECASE,
            )
            if match:
                unit_match = re.search(r"\(([^)]+)\)", match.group())
                properties[property_name] = MechanicalProperty(
                    property=property_name,
                    value=float(match.group(1)),
                    unit=unit_match.group(1) if unit_match else None,
                )
                break
        if property_name not in properties and property_name in extracted:
            properties[property_name] = MechanicalProperty(
                property=property_name,
                value=extracted[property_name],
                unit="%" if property_name == "elongation" else "MPa" if property_name.endswith("strength") else None,
            )
    return list(properties.values())


def parse_mtc(text: str) -> MTCRecord:
    # Preserve line boundaries: field extraction relies on one labelled value
    # per line, while still normalizing uneven OCR spacing within a line.
    normalized = "\n".join(" ".join(line.split()) for line in text.replace('″', '"').splitlines())
    quantity = _field(normalized, "qty", "quantity")
    return MTCRecord(
        cert_no=_field(normalized, "certificate no", "cert no", "certificate number"),
        po_no=_field(normalized, "po no", "purchase order"),
        description=_field(normalized, "product description", "description", "item description"),
        standard=_field(normalized, "governing standard", "standard"),
        material_grade=_field(normalized, "material specification", "material grade", "grade"),
        heat_no=_field(normalized, "heat / batch no", "heat batch no", "heat no", "heat number"),
        qty=quantity,
        chemical_composition=chemical_composition_values(normalized),
        mechanical_properties=mechanical_property_values(normalized),
    )



# ── Full MTC Intelligence Parser & Schema Conversion ────────────────────────

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
    Supports chemistry, mechanical properties, carbon equivalent, and schema conversion.
    """

    def parse_header(self, text: str) -> dict:
        cert_no = self._search_patterns(text, [
            r'(?:Certificate|Cert|TC)\s*(?:No|Number|#)[.:\s]+([A-Z0-9/_-]+)',
            r'EN\s*10204\s*3\.[12]\s*[:\s|]+(?:Certificate\s*No:?\s*)?([A-Z0-9/_-]+)',
            r'MTC[/\s]+([0-9]{4}[/\s]+[0-9]+)',
        ])

        heat_no = self._search_patterns(text, [
            r'(?:Heat|Melt|Cast|Batch)\s*(?:No|Number|#)[.:\s]+([A-Z0-9_-]+)',
            r'HT-([0-9]{4}-[0-9]+)',
            r'Heat[.:\s]+([A-Z0-9]+)',
        ])

        po_no = self._search_patterns(text, [
            r'(?:Purchase\s*Order|PO|P\.O\.)\s*(?:No|Number|#)?[.:\s]+([A-Z0-9_-]+)',
            r'PO-([A-Z0-9_-]+)',
        ])

        material_grade = self._search_patterns(text, [
            r'(?:Material\s*Grade|Grade|Steel\s*Grade)[.:\s]+(ASTM\s+[A-Z0-9.-]+(?:\s+(?:GR\.?|CLASS)\s*[A-Z0-9]+)?)',
            r'(?:Material\s*Grade|Grade|Spec)[.:\s]+([A-Z0-9.-]+(?:\s+(?:GR\.?|CLASS)\s*[A-Z0-9]+)?)',
            r'\b(ASTM\s+A[0-9]{3}[A-Z0-9.-]*)\b',
            r'\b(A350\s+LF2|A105|A182\s+F316L?|A182\s+F304L?|A182\s+F51|A106\s+GR\.?\s*B|A193\s+B7)\b',
        ])
        if material_grade:
            material_grade = material_grade.split("\n")[0].split("|")[0].strip()

        spec = None
        if "EN 10204 3.2" in text or "3.2" in text:
            spec = "EN 10204 3.2"
        elif "EN 10204 3.1" in text or "3.1" in text:
            spec = "EN 10204 3.1"

        manufacturer = self._find_known_entity(text, KNOWN_MANUFACTURERS)
        if not manufacturer:
            m = re.search(r'Manufacturer[.:\s]+([^\n\r|,]+)', text, re.IGNORECASE)
            if m:
                manufacturer = m.group(1).strip()

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
            "manufacturer": manufacturer,
            "tpi_agency": tpi_agency,
        }

    def parse_chemical_composition(self, text: str) -> dict[str, float]:
        elements = ["C", "Mn", "Si", "P", "S", "Cr", "Ni", "Mo", "V", "Cu", "N", "Nb", "Ti"]
        comp: dict[str, float] = {}

        for el in elements:
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

    def parse_mechanical_properties(self, text: str) -> dict[str, float]:
        props: dict[str, float] = {}

        ys = self._extract_float(text, [
            r'(?:Yield\s*Strength|YS|Re|Rp0\.2)(?:\s*\([^)]*\))?[.:\s=]+([0-9]+\.?[0-9]*)\s*(?:MPa|N/mm2)?',
            r'\bRe\b(?:\s*\([^)]*\))?[.:\s=]+([0-9]+)',
        ])
        if ys:
            props["yield_strength_mpa"] = ys

        ts = self._extract_float(text, [
            r'(?:Tensile\s*Strength|UTS|Rm)(?:\s*\([^)]*\))?[.:\s=]+([0-9]+\.?[0-9]*)\s*(?:MPa|N/mm2)?',
            r'\bRm\b(?:\s*\([^)]*\))?[.:\s=]+([0-9]+)',
        ])
        if ts:
            props["tensile_strength_mpa"] = ts

        el = self._extract_float(text, [
            r'(?:Elongation|EL|A5|A%|A)(?:\s*\([^)]*\))?[.:\s=]+([0-9]+\.?[0-9]*)\s*%?',
            r'Elongation\s*\(A5\)\s*[:=]\s*([0-9]+)',
        ])
        if el:
            props["elongation_pct"] = el

        imp = self._extract_float(text, [
            r'(?:Charpy|Impact|CVN)(?:\s*\([^)]*\))?[^:\n\r]*[:=]+([0-9]+\.?[0-9]*)\s*(?:J|Joules)?',
            r'Toughness\s*[:=]\s*([0-9]+)\s*J',
        ])
        if imp:
            props["impact_joules_charpy"] = imp

        hb = self._extract_float(text, [
            r'(?:Hardness|Brinell|HBW|HB|HRC)(?:\s*\([^)]*\))?[.:\s=]+([0-9]+\.?[0-9]*)',
        ])
        if hb:
            props["hardness_hb"] = hb

        return props

    def parse_full_mtc(self, raw_text: str, confidence_score: float = 1.0) -> dict:
        from backend.app.ingestion.chemistry import (
            compute_carbon_equivalent,
            classify_weldability,
            compute_pren,
            validate_composition,
            validate_mechanical_properties,
        )

        header = self.parse_header(raw_text)
        chemistry = self.parse_chemical_composition(raw_text)
        mechanical = self.parse_mechanical_properties(raw_text)

        ce = compute_carbon_equivalent(chemistry)
        weldability = classify_weldability(ce)
        pren_val = compute_pren(chemistry)

        grade = header.get("material_grade") or ""
        chem_valid, chem_violations = validate_composition(chemistry, grade)
        mech_valid, mech_violations = validate_mechanical_properties(mechanical, grade)

        has_data = bool(chemistry or mechanical)
        is_conforming = (chem_valid and mech_valid) if has_data else False
        all_violations = (chem_violations + mech_violations) if has_data else ["No chemical or mechanical data extracted from document."]

        size_nb_mm = self._extract_dimension_size(raw_text)
        pressure_class = self._extract_pressure_class(raw_text)
        schedule = self._extract_schedule(raw_text)
        facing_end = self._extract_facing(raw_text)
        item_type = self._extract_item_type(raw_text)

        missing_attrs = []
        if not size_nb_mm:
            missing_attrs.append("size_nb_mm")
        if not pressure_class and item_type in ("FLANGE", "GATE_VALVE", "VALVE"):
            missing_attrs.append("pressure_class")
        if not schedule and item_type == "PIPE":
            missing_attrs.append("schedule")
        if not header.get("material_grade"):
            missing_attrs.append("material_grade")

        is_incomplete = len(missing_attrs) > 0 or confidence_score < 0.70 or not has_data
        requires_hitl = is_incomplete or not is_conforming

        return {
            "header": header,
            "chemical_composition": chemistry,
            "carbon_equivalent_iiw": ce,
            "weldability": weldability,
            "pren": pren_val,
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

    def to_material_attributes(self, parsed_mtc: dict):
        from backend.app.schemas.material import ExtractedMaterialAttributes

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
            "astm_conformance": parsed_mtc.get("conforms_to_astm", False),
            "non_conformance_warnings": parsed_mtc.get("non_conformance_warnings", []),
        }

        return ExtractedMaterialAttributes(
            item_type=parsed_mtc.get("item_type"),
            size_nb_mm=parsed_mtc.get("size_nb_mm"),
            pressure_class=parsed_mtc.get("pressure_class"),
            schedule=parsed_mtc.get("schedule"),
            metallurgy=header.get("material_grade"),
            facing_end=parsed_mtc.get("facing_end"),
            standard=header.get("specification"),
            properties=props,
            is_incomplete=parsed_mtc.get("is_incomplete", False),
            missing_attributes=parsed_mtc.get("missing_attributes", []),
            confidence_score=parsed_mtc.get("confidence_score", 1.0),
            requires_hitl=parsed_mtc.get("requires_hitl", False),
        )

    def _search_patterns(self, text: str, patterns: list[str]) -> str | None:
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _extract_float(self, text: str, patterns: list[str]) -> float | None:
        s = self._search_patterns(text, patterns)
        if s:
            try:
                return float(s)
            except ValueError:
                pass
        return None

    def _find_known_entity(self, text: str, entities: list[str]) -> str | None:
        t_upper = text.upper()
        for ent in entities:
            if ent in t_upper:
                return ent
        return None

    def _extract_dimension_size(self, text: str) -> float | None:
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

    def _extract_pressure_class(self, text: str) -> int | None:
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

    def _extract_schedule(self, text: str) -> str | None:
        m = re.search(r'\b(?:SCH|SCHEDULE)\s*([0-9]+[A-Z]?|STD|XS|XXS)\b', text, re.IGNORECASE)
        if m:
            return f"SCH {m.group(1).upper()}"
        return None

    def _extract_facing(self, text: str) -> str | None:
        m = re.search(r'\b(RF|RTJ|FF|BW|SW)\b', text, re.IGNORECASE)
        return m.group(1).upper() if m else None

    def _extract_item_type(self, text: str) -> str | None:
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
        return None
