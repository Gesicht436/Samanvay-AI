"""Chemistry calculations, ASTM limits, and supported-grade composition checks for MTCs."""

import re
from collections.abc import Iterable
from typing import Any, Dict, List, Optional, Tuple

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

ASTM_LIMITS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "A105": {
        "C": (0.0, 0.35), "Mn": (0.60, 1.05), "P": (0.0, 0.035), "S": (0.0, 0.040), "Si": (0.10, 0.35),
        "Cu": (0.0, 0.40), "Ni": (0.0, 0.40), "Cr": (0.0, 0.30), "Mo": (0.0, 0.12), "V": (0.0, 0.08)
    },
    "ASTM A105": {
        "C": (0.0, 0.35), "Mn": (0.60, 1.05), "P": (0.0, 0.035), "S": (0.0, 0.040), "Si": (0.10, 0.35),
        "Cu": (0.0, 0.40), "Ni": (0.0, 0.40), "Cr": (0.0, 0.30), "Mo": (0.0, 0.12), "V": (0.0, 0.08)
    },
    "A350 LF2": {
        "C": (0.0, 0.30), "Mn": (0.60, 1.35), "P": (0.0, 0.035), "S": (0.0, 0.040), "Si": (0.15, 0.30),
        "Cu": (0.0, 0.40), "Ni": (0.0, 0.40), "Cr": (0.0, 0.30), "Mo": (0.0, 0.12), "V": (0.0, 0.08)
    },
    "ASTM A350 LF2": {
        "C": (0.0, 0.30), "Mn": (0.60, 1.35), "P": (0.0, 0.035), "S": (0.0, 0.040), "Si": (0.15, 0.30),
        "Cu": (0.0, 0.40), "Ni": (0.0, 0.40), "Cr": (0.0, 0.30), "Mo": (0.0, 0.12), "V": (0.0, 0.08)
    },
    "A106 GR.B": {
        "C": (0.0, 0.30), "Mn": (0.29, 1.06), "P": (0.0, 0.035), "S": (0.0, 0.035), "Si": (0.10, 1.00),
        "Cr": (0.0, 0.40), "Cu": (0.0, 0.40), "Mo": (0.0, 0.15), "Ni": (0.0, 0.40), "V": (0.0, 0.08)
    },
    "ASTM A106 GR.B": {
        "C": (0.0, 0.30), "Mn": (0.29, 1.06), "P": (0.0, 0.035), "S": (0.0, 0.035), "Si": (0.10, 1.00),
        "Cr": (0.0, 0.40), "Cu": (0.0, 0.40), "Mo": (0.0, 0.15), "Ni": (0.0, 0.40), "V": (0.0, 0.08)
    },
    "A182 F304": {
        "C": (0.0, 0.08), "Mn": (0.0, 2.00), "P": (0.0, 0.045), "S": (0.0, 0.030), "Si": (0.0, 1.00),
        "Cr": (18.0, 20.0), "Ni": (8.0, 11.0)
    },
    "ASTM A182 F304": {
        "C": (0.0, 0.08), "Mn": (0.0, 2.00), "P": (0.0, 0.045), "S": (0.0, 0.030), "Si": (0.0, 1.00),
        "Cr": (18.0, 20.0), "Ni": (8.0, 11.0)
    },
    "A182 F316": {
        "C": (0.0, 0.08), "Mn": (0.0, 2.00), "P": (0.0, 0.045), "S": (0.0, 0.030), "Si": (0.0, 1.00),
        "Cr": (16.0, 18.0), "Ni": (10.0, 14.0), "Mo": (2.00, 3.00)
    },
    "ASTM A182 F316": {
        "C": (0.0, 0.08), "Mn": (0.0, 2.00), "P": (0.0, 0.045), "S": (0.0, 0.030), "Si": (0.0, 1.00),
        "Cr": (16.0, 18.0), "Ni": (10.0, 14.0), "Mo": (2.00, 3.00)
    },
    "A182 F316L": {
        "C": (0.0, 0.030), "Mn": (0.0, 2.00), "P": (0.0, 0.045), "S": (0.0, 0.030), "Si": (0.0, 1.00),
        "Cr": (16.0, 18.0), "Ni": (10.0, 15.0), "Mo": (2.00, 3.00)
    },
    "ASTM A182 F316L": {
        "C": (0.0, 0.030), "Mn": (0.0, 2.00), "P": (0.0, 0.045), "S": (0.0, 0.030), "Si": (0.0, 1.00),
        "Cr": (16.0, 18.0), "Ni": (10.0, 15.0), "Mo": (2.00, 3.00)
    },
    "A182 F51": {
        "C": (0.0, 0.030), "Mn": (0.0, 2.00), "P": (0.0, 0.030), "S": (0.0, 0.020), "Si": (0.0, 1.00),
        "Cr": (21.0, 23.0), "Ni": (4.5, 6.5), "Mo": (2.5, 3.5), "N": (0.08, 0.20)
    },
    "ASTM A182 F51": {
        "C": (0.0, 0.030), "Mn": (0.0, 2.00), "P": (0.0, 0.030), "S": (0.0, 0.020), "Si": (0.0, 1.00),
        "Cr": (21.0, 23.0), "Ni": (4.5, 6.5), "Mo": (2.5, 3.5), "N": (0.08, 0.20)
    },
    "A193 B7": {
        "C": (0.37, 0.49), "Mn": (0.65, 1.10), "P": (0.0, 0.035), "S": (0.0, 0.040), "Si": (0.15, 0.35),
        "Cr": (0.75, 1.20), "Mo": (0.15, 0.25)
    },
    "ASTM A193 B7": {
        "C": (0.37, 0.49), "Mn": (0.65, 1.10), "P": (0.0, 0.035), "S": (0.0, 0.040), "Si": (0.15, 0.35),
        "Cr": (0.75, 1.20), "Mo": (0.15, 0.25)
    }
}

ASTM_MECHANICAL_LIMITS: Dict[str, Dict[str, float]] = {
    "A105": {"yield_strength_min": 250.0, "tensile_strength_min": 485.0, "elongation_min": 22.0},
    "ASTM A105": {"yield_strength_min": 250.0, "tensile_strength_min": 485.0, "elongation_min": 22.0},
    "A350 LF2": {"yield_strength_min": 250.0, "tensile_strength_min": 485.0, "elongation_min": 22.0, "impact_min_joules": 20.0},
    "ASTM A350 LF2": {"yield_strength_min": 250.0, "tensile_strength_min": 485.0, "elongation_min": 22.0, "impact_min_joules": 20.0},
    "A106 GR.B": {"yield_strength_min": 240.0, "tensile_strength_min": 415.0, "elongation_min": 30.0},
    "ASTM A106 GR.B": {"yield_strength_min": 240.0, "tensile_strength_min": 415.0, "elongation_min": 30.0},
    "A182 F304": {"yield_strength_min": 205.0, "tensile_strength_min": 515.0, "elongation_min": 30.0},
    "ASTM A182 F304": {"yield_strength_min": 205.0, "tensile_strength_min": 515.0, "elongation_min": 30.0},
    "A182 F316": {"yield_strength_min": 205.0, "tensile_strength_min": 515.0, "elongation_min": 30.0},
    "ASTM A182 F316": {"yield_strength_min": 205.0, "tensile_strength_min": 515.0, "elongation_min": 30.0},
    "A182 F316L": {"yield_strength_min": 170.0, "tensile_strength_min": 485.0, "elongation_min": 30.0},
    "ASTM A182 F316L": {"yield_strength_min": 170.0, "tensile_strength_min": 485.0, "elongation_min": 30.0},
    "A182 F51": {"yield_strength_min": 450.0, "tensile_strength_min": 620.0, "elongation_min": 25.0, "impact_min_joules": 40.0},
    "ASTM A182 F51": {"yield_strength_min": 450.0, "tensile_strength_min": 620.0, "elongation_min": 25.0, "impact_min_joules": 40.0},
    "A193 B7": {"yield_strength_min": 725.0, "tensile_strength_min": 860.0, "elongation_min": 16.0},
    "ASTM A193 B7": {"yield_strength_min": 725.0, "tensile_strength_min": 860.0, "elongation_min": 16.0},
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


def compute_carbon_equivalent(composition: Dict[str, float]) -> Optional[float]:
    """
    International Institute of Welding (IIW) Carbon Equivalent Formula:
    CE = C + Mn/6 + (Cr + Mo + V)/5 + (Ni + Cu)/15
    """
    if not composition:
        return None

    norm = {k.upper(): v for k, v in composition.items()}
    if "C" not in norm:
        return None

    c = norm.get("C", 0.0)
    mn = norm.get("MN", 0.0)
    cr = norm.get("CR", 0.0)
    mo = norm.get("MO", 0.0)
    v = norm.get("V", 0.0)
    ni = norm.get("NI", 0.0)
    cu = norm.get("CU", 0.0)

    ce = c + (mn / 6.0) + ((cr + mo + v) / 5.0) + ((ni + cu) / 15.0)
    return round(float(ce), 4)


def carbon_equivalent_iiw(composition: dict[str, float]) -> float | None:
    return compute_carbon_equivalent(composition)


def classify_weldability(ce: Optional[float]) -> Optional[str]:
    """
    Classifies weldability according to refinery piping standards.
    - CE <= 0.43%: STANDARD_WELDABLE
    - CE > 0.43%: PREHEAT_REQUIRED_HIGH_CE
    """
    if ce is None:
        return None
    if ce <= 0.43:
        return "STANDARD_WELDABLE"
    return "PREHEAT_REQUIRED_HIGH_CE"


def compute_pren(composition: Dict[str, float]) -> Optional[float]:
    """
    Pitting Resistance Equivalent Number (PREN) for stainless and duplex alloys:
    PREN = Cr + 3.3 * Mo + 16 * N
    """
    if not composition:
        return None

    norm = {k.upper(): v for k, v in composition.items()}
    if "CR" not in norm:
        return None

    cr = norm.get("CR", 0.0)
    mo = norm.get("MO", 0.0)
    n = norm.get("N", 0.0)
    return round(float(cr + 3.3 * mo + 16.0 * n), 2)


def pren(composition: dict[str, float]) -> float | None:
    return compute_pren(composition)


def validate_composition(composition: Dict[str, float], grade: str) -> Tuple[bool, List[str]]:
    """
    Validates chemical composition against ASTM standard limits.
    """
    if not composition:
        return False, ["No chemical elemental data extracted for validation."]
    if not grade:
        return False, ["Material grade is missing; cannot validate composition."]

    violations: List[str] = []
    norm_grade = grade.strip().upper()

    limits = None
    for k, v in ASTM_LIMITS.items():
        if k.upper() == norm_grade or k.upper() in norm_grade:
            limits = v
            break

    if not limits:
        return True, [f"Grade '{grade}' limits not explicitly registered; skipped."]

    for el, (min_val, max_val) in limits.items():
        val = composition.get(el) or composition.get(el.upper()) or composition.get(el.capitalize())
        if val is not None:
            if val < min_val:
                violations.append(f"{el} content ({val}%) is below ASTM minimum ({min_val}%)")
            elif val > max_val:
                violations.append(f"{el} content ({val}%) exceeds ASTM maximum ({max_val}%)")

    return len(violations) == 0, violations


def validate_mechanical_properties(properties: Dict[str, Any], grade: str) -> Tuple[bool, List[str]]:
    """
    Validates mechanical tensile, yield, elongation, and impact values against ASTM limits.
    """
    if not properties:
        return False, ["No mechanical test properties extracted for validation."]
    if not grade:
        return False, ["Material grade is missing; cannot validate mechanical properties."]

    violations: List[str] = []
    norm_grade = grade.strip().upper()

    limits = None
    for k, v in ASTM_MECHANICAL_LIMITS.items():
        if k.upper() == norm_grade or k.upper() in norm_grade:
            limits = v
            break

    if not limits:
        return True, [f"Mechanical limits for '{grade}' not explicitly registered; passing by default."]

    ys = properties.get("yield_strength_mpa") or properties.get("yield_strength")
    if ys is not None and "yield_strength_min" in limits:
        if float(ys) < limits["yield_strength_min"]:
            violations.append(f"Yield strength ({ys} MPa) is below ASTM minimum ({limits['yield_strength_min']} MPa)")

    ts = properties.get("tensile_strength_mpa") or properties.get("tensile_strength")
    if ts is not None and "tensile_strength_min" in limits:
        if float(ts) < limits["tensile_strength_min"]:
            violations.append(f"Tensile strength ({ts} MPa) is below ASTM minimum ({limits['tensile_strength_min']} MPa)")

    el = properties.get("elongation_pct") or properties.get("elongation")
    if el is not None and "elongation_min" in limits:
        if float(el) < limits["elongation_min"]:
            violations.append(f"Elongation ({el}%) is below ASTM minimum ({limits['elongation_min']}%)")

    imp = properties.get("impact_joules_charpy") or properties.get("charpy_impact")
    if imp is not None and "impact_min_joules" in limits:
        if float(imp) < limits["impact_min_joules"]:
            violations.append(f"Charpy impact energy ({imp} J) is below ASTM minimum ({limits['impact_min_joules']} J)")

    return len(violations) == 0, violations


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

    norm = {k.upper(): v for k, v in composition.items()}
    warnings: list[str] = []
    limits = ASTM_LIMITS.get(grade, {})
    for element, (minimum, maximum) in limits.items():
        value = norm.get(element.upper())
        if value is None:
            warnings.append(f"Cannot verify {element}: no value was parsed from the certificate.")
        elif not minimum <= value <= maximum:
            warnings.append(
                f"{element} value {value:g}% is outside the configured {grade} range "
                f"{minimum:g}%–{maximum:g}%."
            )
    return not warnings, warnings
