"""Chemistry calculations and supported-grade composition checks for MTCs."""

import re
from collections.abc import Iterable

from backend.app.contracts.ingestion import ChemicalComposition

_ELEMENT_ALIASES = {
    "C": "C",
    "CARBON": "C",
    "MN": "MN",
    "MANGANESE": "MN",
    "SI": "SI",
    "SILICON": "SI",
    "P": "P",
    "PHOSPHORUS": "P",
    "S": "S",
    "SULFUR": "S",
    "SULPHUR": "S",
    "CR": "CR",
    "CHROMIUM": "CR",
    "NI": "NI",
    "NICKEL": "NI",
    "MO": "MO",
    "MOLYBDENUM": "MO",
    "V": "V",
    "VANADIUM": "V",
    "CU": "CU",
    "COPPER": "CU",
    "N": "N",
    "NITROGEN": "N",
}

_GRADE_LIMITS: dict[str, dict[str, tuple[float, float]]] = {
    "A105": {
        "C": (0.0, 0.35),
        "MN": (0.60, 1.05),
        "SI": (0.10, 0.35),
        "P": (0.0, 0.035),
        "S": (0.0, 0.040),
        "CR": (0.0, 0.30),
        "NI": (0.0, 0.40),
        "MO": (0.0, 0.12),
        "V": (0.0, 0.08),
        "CU": (0.0, 0.40),
    },
    "F316": {
        "C": (0.0, 0.08),
        "MN": (0.0, 2.0),
        "SI": (0.0, 1.0),
        "P": (0.0, 0.045),
        "S": (0.0, 0.030),
        "CR": (16.0, 18.0),
        "NI": (10.0, 14.0),
        "MO": (2.0, 3.0),
    },
}


def composition_by_symbol(
    composition: Iterable[ChemicalComposition],
) -> dict[str, float]:
    values: dict[str, float] = {}
    for entry in composition:
        element = _ELEMENT_ALIASES.get(entry.element.strip().upper())
        if element and entry.value is not None:
            values[element] = entry.value
    return values


def carbon_equivalent_iiw(composition: dict[str, float]) -> float | None:
    carbon = composition.get("C")
    manganese = composition.get("MN")
    if carbon is None or manganese is None:
        return None
    return (
        carbon
        + manganese / 6
        + (composition.get("CR", 0.0) + composition.get("MO", 0.0) + composition.get("V", 0.0)) / 5
        + (composition.get("NI", 0.0) + composition.get("CU", 0.0)) / 15
    )


def classify_weldability(value: float | None) -> str | None:
    if value is None:
        return None
    if value <= 0.35:
        return "excellent"
    if value <= 0.45:
        return "good"
    if value <= 0.60:
        return "moderate"
    return "poor"


def pren(composition: dict[str, float]) -> float | None:
    chromium = composition.get("CR")
    molybdenum = composition.get("MO")
    nitrogen = composition.get("N")
    if chromium is None or molybdenum is None or nitrogen is None:
        return None
    return chromium + 3.3 * molybdenum + 16 * nitrogen


def astm_chemistry_conformance(
    composition: dict[str, float],
    material_grade: str | None,
) -> tuple[bool, list[str]]:
    grade_text = (material_grade or "").upper()
    grade = "F316" if re.search(r"\bF\s*316(?:L)?\b", grade_text) else (
        "A105" if re.search(r"\bA\s*105(?:N)?\b", grade_text) else None
    )
    if grade is None:
        return False, [f"No ASTM chemistry limits are configured for grade {material_grade or 'unknown'}."]

    warnings: list[str] = []
    for element, (minimum, maximum) in _GRADE_LIMITS[grade].items():
        value = composition.get(element)
        if value is None:
            warnings.append(f"Cannot verify {element}: no value was parsed from the certificate.")
        elif not minimum <= value <= maximum:
            warnings.append(
                f"{element} value {value:g}% is outside the configured {grade} range "
                f"{minimum:g}%–{maximum:g}%."
            )
    return not warnings, warnings
