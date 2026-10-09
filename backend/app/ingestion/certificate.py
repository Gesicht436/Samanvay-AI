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
