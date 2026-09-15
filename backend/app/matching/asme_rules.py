"""
Deterministic Engineering Tolerance Matrices: ASME B16.5, ASME B16.34, and ASTM Standards.
Encodes domain knowledge of pressure rating ladders, metallurgical hierarchies,
and mating face compatibility for critical hydrocarbon process components.
"""

from typing import Tuple, Optional, Dict, Set


# Standard ASME B16.5 / B16.34 Pressure Class Ladder
PRESSURE_CLASSES = [150, 300, 400, 600, 900, 1500, 2500]
PRESSURE_CLASS_INDEX = {p: i for i, p in enumerate(PRESSURE_CLASSES)}


# ASTM Metallurgy Compatibility Graph (Directed Acyclic Graph)
# Key: (source_spec, candidate_spec) -> (is_compatible, is_upgrade, rationale)
# Down-grading (e.g. SS316 -> A105) is FATAL (Tier-3).
# Up-grading (e.g. A105 -> SS316, A105 -> A350 LF2) is PERMITTED (Tier-2).

METALLURGY_NORMALIZATION_MAP = {
    "A105": "ASTM A105",
    "A105N": "ASTM A105",
    "ASTM A105N": "ASTM A105",
    "CS A105": "ASTM A105",
    "CARBON STEEL A105": "ASTM A105",
    "SA105": "ASTM A105",
    "SA-105": "ASTM A105",
    "SA 105": "ASTM A105",
    "ASME SA105": "ASTM A105",
    "SA105N": "ASTM A105",
    
    "A350-LF2": "ASTM A350 LF2",
    "A350LF2": "ASTM A350 LF2",
    "LF2": "ASTM A350 LF2",
    "LTCS A350 LF2": "ASTM A350 LF2",
    
    "SS304": "ASTM A182 F304",
    "F304": "ASTM A182 F304",
    "AISI 304": "ASTM A182 F304",
    "SS-304": "ASTM A182 F304",
    
    "SS316": "ASTM A182 F316",
    "SS316L": "ASTM A182 F316",
    "F316": "ASTM A182 F316",
    "AISI 316": "ASTM A182 F316",
    "SS-316": "ASTM A182 F316",
    
    "WCB": "ASTM A216 WCB",
    "A216-WCB": "ASTM A216 WCB",
    "CAST STEEL WCB": "ASTM A216 WCB",
    
    "CF8M": "ASTM A351 CF8M",
    "A351 CF8M": "ASTM A351 CF8M",
    "A351-CF8M": "ASTM A351 CF8M",
    "ASTM A351 CF8M": "ASTM A351 CF8M",
    
    "A106": "ASTM A106 GR.B",
    "A106-B": "ASTM A106 GR.B",
    "A106 GR B": "ASTM A106 GR.B",
    "A106 GR.B": "ASTM A106 GR.B",
    "ASTM A106 GR B": "ASTM A106 GR.B",
    "ASTM A106 GR.B": "ASTM A106 GR.B",
    "ASTM A106-B": "ASTM A106 GR.B",
    
    "SS316/GRAF": "SS316 / GRAPHITE",
    "SS316-GR": "SS316 / GRAPHITE",
    "316SS/GRAPHITE": "SS316 / GRAPHITE",
    
    "SS304/GRAF": "SS304 / GRAPHITE",
    "SS304-GR": "SS304 / GRAPHITE",
    
    "B7/2H": "ASTM A193 B7 / A194 2H",
    "B7-2H": "ASTM A193 B7 / A194 2H",
    "ASTM A193 B7": "ASTM A193 B7 / A194 2H",
    "GR B7 / 2H": "ASTM A193 B7 / A194 2H",
    
    "L7/GR7": "ASTM A320 L7 / A194 7",
    "L7-GR7": "ASTM A320 L7 / A194 7",
    "ASTM A320 L7": "ASTM A320 L7 / A194 7",
    "GR L7 / 7": "ASTM A320 L7 / A194 7",

    # CPSE Refinery Dialect & Shorthand Alloys
    "CS": "ASTM A105",
    "CARBON STEEL": "ASTM A105",
    "LTCS": "ASTM A350 LF2",
    "DSS": "ASTM A182 F51",
    "DUPLEX": "ASTM A182 F51",
    "DUPLEX SS": "ASTM A182 F51",
    "SDSS": "ASTM A815 S32750",
    "SUPER DUPLEX": "ASTM A815 S32750",
    "SUPER DUPLEX SS": "ASTM A815 S32750",
    "INCO 625": "INCONEL 625",
    "INCONEL 625": "INCONEL 625",
    "HAST-C": "HASTELLOY C-276",
    "HASTELLOY C": "HASTELLOY C-276",
    "HASTELLOY C276": "HASTELLOY C-276",
    "HASTELLOY C-276": "HASTELLOY C-276",
    "MONEL 400": "MONEL 400",
}


def normalize_metallurgy(mat: Optional[str]) -> str:
    """Standardizes messy alloy strings to canonical ASTM specifications."""
    if not mat:
        return "UNKNOWN"
    cleaned = mat.strip().upper()
    return METALLURGY_NORMALIZATION_MAP.get(cleaned, mat.strip())


# Valid upgrades: set of (source, candidate) pairs representing safe metallurgical upgrades
# Any pair not in EXACT and not in SAFE_UPGRADES is either an unsafe downgrade or incompatible family.
METALLURGY_UPGRADES: Dict[Tuple[str, str], str] = {
    # Carbon steel -> Low temp carbon steel (LF2 has impact toughness)
    ("ASTM A105", "ASTM A350 LF2"): "Low-temperature certified LF2 exceeds A105 impact toughness requirements.",
    
    # Carbon steel -> Austenitic Stainless Steel
    ("ASTM A105", "ASTM A182 F304"): "Austenitic Stainless F304 provides superior general corrosion resistance over A105.",
    ("ASTM A105", "ASTM A182 F316"): "Marine/acid grade F316 provides superior corrosion/pitting resistance over A105.",
    ("ASTM A216 WCB", "ASTM A182 F316"): "Stainless F316 valve body exceeds cast steel WCB chemical resistance.",
    ("ASTM A216 WCB", "ASTM A351 CF8M"): "Stainless CF8M valve casting exceeds cast steel WCB chemical resistance.",
    ("ASTM A105", "ASTM A351 CF8M"): "Stainless CF8M casting provides superior chemical/pitting resistance over Carbon Steel A105.",
    
    # SS304 -> SS316 (Molybdenum addition for pitting resistance)
    ("ASTM A182 F304", "ASTM A182 F316"): "F316 contains 2-3% Mo, providing superior pitting and crevice corrosion resistance over F304.",
    
    # Gasket metallurgy upgrade
    ("SS304 / GRAPHITE", "SS316 / GRAPHITE"): "SS316 winding metal provides higher chemical corrosion resistance than SS304.",
    
    # Fastener upgrade: Standard B7 -> Low temp L7
    ("ASTM A193 B7 / A194 2H", "ASTM A320 L7 / A194 7"): "L7 fasteners undergo Charpy V-notch impact testing at -101°C, exceeding B7 specs.",

    # Duplex & Super Duplex Upgrades
    ("ASTM A105", "ASTM A182 F51"): "Duplex 2205 (F51) provides superior yield strength and pitting resistance over Carbon Steel A105.",
    ("ASTM A105", "ASTM A815 S32750"): "Super Duplex S32750 provides extreme pitting resistance (PREN > 40) and high mechanical strength over Carbon Steel A105.",
    ("ASTM A182 F316", "ASTM A182 F51"): "Duplex 2205 (F51) provides twice the yield strength and superior stress corrosion cracking resistance over SS316.",
    ("ASTM A182 F316", "ASTM A815 S32750"): "Super Duplex S32750 provides superior yield strength and extreme pitting resistance over Austenitic SS316.",
    ("ASTM A182 F51", "ASTM A815 S32750"): "Super Duplex S32750 exceeds standard Duplex 2205 in severe sour and chloride environments.",

    # Nickel Alloy Upgrades
    ("ASTM A105", "INCONEL 625"): "Inconel 625 provides superior high-temperature oxidation and acid corrosion resistance over Carbon Steel.",
    ("ASTM A182 F316", "INCONEL 625"): "Inconel 625 provides superior resistance to stress corrosion cracking and severe acids over SS316.",
    ("ASTM A105", "HASTELLOY C-276"): "Hastelloy C-276 provides exceptional resistance to strong oxidizing acids over Carbon Steel.",
    ("ASTM A182 F316", "HASTELLOY C-276"): "Hastelloy C-276 provides exceptional pitting resistance and wet chlorine corrosion resistance over SS316.",
}

# Strict Safety Traps: Down-grading is dangerous!
# Explicit rationale for common hazardous substitution traps
METALLURGY_DOWNGRADE_WARNINGS: Dict[Tuple[str, str], str] = {
    ("ASTM A182 F316", "ASTM A105"): "FATAL DOWNGRADE: Replacing corrosion-resistant SS316 with Carbon Steel A105 risks rapid acid/chloride blowout.",
    ("ASTM A182 F316", "ASTM A216 WCB"): "FATAL DOWNGRADE: Replacing Stainless SS316 with Cast Carbon Steel WCB will cause severe process fluid corrosion.",
    ("ASTM A351 CF8M", "ASTM A216 WCB"): "FATAL DOWNGRADE: Replacing Stainless CF8M with Cast Carbon Steel WCB will cause severe process fluid corrosion.",
    ("ASTM A351 CF8M", "ASTM A105"): "FATAL DOWNGRADE: Replacing Stainless CF8M with Carbon Steel A105 risks rapid acid/chloride blowout.",
    ("ASTM A351 CF8M", "ASTM A182 F304"): "UNSAFE DOWNGRADE: F304 lacks Molybdenum; using F304 in place of CF8M risks pitting in sour/chloride service.",
    ("ASTM A182 F316", "ASTM A182 F304"): "UNSAFE DOWNGRADE: F304 lacks Molybdenum; using F304 in place of F316 leads to localized pitting in sour/chloride service.",
    ("ASTM A182 F304", "ASTM A105"): "FATAL DOWNGRADE: Stainless F304 cannot be replaced by unalloyed carbon steel.",
    ("ASTM A182 F304", "ASTM A216 WCB"): "FATAL DOWNGRADE: Stainless F304 cannot be replaced by unalloyed carbon steel WCB.",
    ("ASTM A350 LF2", "ASTM A105"): "CRYOGENIC SAFETY TRAP: Standard A105 lacks low-temperature impact testing; risks brittle fracture below 0°C.",
    ("ASTM A350 LF2", "ASTM A216 WCB"): "CRYOGENIC SAFETY TRAP: Standard WCB lacks low-temperature impact testing; risks brittle fracture below 0°C.",
    ("ASTM A320 L7 / A194 7", "ASTM A193 B7 / A194 2H"): "CRYOGENIC FASTENER TRAP: B7 studs risk brittle shearing in refrigerated/sub-zero piping.",
    ("SS316 / GRAPHITE", "SS304 / GRAPHITE"): "CORROSION TRAP: SS304 gasket winding lacks Molybdenum required for acid/chloride service.",
    ("ASTM A815 S32750", "ASTM A105"): "FATAL DOWNGRADE: Super Duplex S32750 cannot be replaced with Carbon Steel A105.",
    ("ASTM A815 S32750", "ASTM A182 F316"): "UNSAFE DOWNGRADE: Standard SS316 lacks the pitting resistance and yield strength of Super Duplex.",
    ("ASTM A182 F51", "ASTM A105"): "FATAL DOWNGRADE: Duplex F51 cannot be replaced with Carbon Steel A105.",
    ("INCONEL 625", "ASTM A105"): "FATAL DOWNGRADE: Replacing Inconel 625 with Carbon Steel A105 risks immediate corrosive blowout.",
    ("INCONEL 625", "ASTM A182 F316"): "UNSAFE DOWNGRADE: Replacing Inconel 625 with SS316 risks severe pitting and stress corrosion cracking in harsh chemical service.",
    ("HASTELLOY C-276", "ASTM A105"): "FATAL DOWNGRADE: Replacing Hastelloy C-276 with Carbon Steel A105 risks catastrophic failure in aggressive acid service.",
}

# Cross-form metallurgical parity (e.g. Wrought F316 vs Cast CF8M)
METALLURGY_EQUIVALENCES: Set[Tuple[str, str]] = {
    ("ASTM A182 F316", "ASTM A351 CF8M"),
    ("ASTM A351 CF8M", "ASTM A182 F316"),
    ("ASTM A182 F304", "ASTM A351 CF8"),
    ("ASTM A351 CF8", "ASTM A182 F304"),
}


def evaluate_metallurgy_compatibility(source_mat: Optional[str], candidate_mat: Optional[str]) -> Tuple[bool, bool, str]:
    """
    Evaluates ASTM metallurgy compatibility.
    Returns (is_compatible, is_upgrade, rationale).
    """
    norm_source = normalize_metallurgy(source_mat)
    norm_candidate = normalize_metallurgy(candidate_mat)

    if norm_source == "UNKNOWN" or norm_candidate == "UNKNOWN":
        return (False, False, f"Unknown metallurgy specification: '{source_mat}' vs '{candidate_mat}'.")

    # 1. Exact match
    if norm_source == norm_candidate:
        return (True, False, f"Exact metallurgy match: {norm_source}.")

    # 1b. Functional metallurgy equivalence (wrought vs casting specifications)
    if (norm_source, norm_candidate) in METALLURGY_EQUIVALENCES:
        return (True, False, f"Equivalent metallurgical grade: {norm_source} is functionally equivalent to {norm_candidate}.")

    # 2. Check known safe upgrades
    upgrade_key = (norm_source, norm_candidate)
    if upgrade_key in METALLURGY_UPGRADES:
        return (True, True, f"Valid metallurgical upgrade: {METALLURGY_UPGRADES[upgrade_key]}")

    # 3. Check known dangerous downgrades
    downgrade_key = (norm_source, norm_candidate)
    if downgrade_key in METALLURGY_DOWNGRADE_WARNINGS:
        return (False, False, f"STRICT REJECT: {METALLURGY_DOWNGRADE_WARNINGS[downgrade_key]}")

    # 4. Incompatible disparate material families
    return (False, False, f"Incompatible metallurgy: Cannot substitute '{norm_source}' with '{norm_candidate}'.")


def evaluate_pressure_class(source_class: Optional[int], candidate_class: Optional[int]) -> Tuple[bool, bool, str]:
    """
    Evaluates ASME B16.5 / B16.34 pressure class rating.
    Down-rating is strictly forbidden.
    Up-rating is permitted as a functional upgrade.
    Returns (is_compatible, is_upgrade, rationale).
    """
    if source_class is None or candidate_class is None:
        return (False, False, "Missing pressure class rating.")

    if source_class not in PRESSURE_CLASS_INDEX or candidate_class not in PRESSURE_CLASS_INDEX:
        return (False, False, f"Invalid or non-standard ASME pressure class: {source_class}# vs {candidate_class}#.")

    # 1. Exact match
    if candidate_class == source_class:
        return (True, False, f"Exact pressure class match: Class {source_class}.")

    # 2. Fatal down-rating
    if candidate_class < source_class:
        return (
            False,
            False,
            f"FATAL SAFETY VIOLATION: Pressure down-rating from Class {source_class} to Class {candidate_class} "
            f"will cause component rupture under system design pressure."
        )

    # 3. Up-rating (candidate > source)
    return (
        True,
        True,
        f"Functional pressure upgrade: Class {candidate_class} exceeds required Class {source_class} rating."
    )


# Mating face compatibility matrix
# RTJ flanges have deep octagonal gasket grooves and cannot seal against RF or FF
FACING_COMPATIBILITY: Dict[Tuple[str, str], Tuple[bool, str]] = {
    ("RF", "RF"): (True, "Raised Face (RF) mating surfaces are identical."),
    ("RTJ", "RTJ"): (True, "Ring Type Joint (RTJ) mating surfaces are identical."),
    ("FF", "FF"): (True, "Flat Face (FF) mating surfaces are identical."),
    ("BW", "BW"): (True, "Butt Weld (BW) end preps are identical."),
    ("SW", "SW"): (True, "Socket Weld (SW) connections are identical."),
    ("THRD", "THRD"): (True, "Threaded (NPT) connections are identical."),
    
    # Incompatible facing pairs
    ("RF", "RTJ"): (False, "FACING MISMATCH: Raised Face (RF) cannot mate with Ring Type Joint (RTJ) groove."),
    ("RTJ", "RF"): (False, "FACING MISMATCH: Ring Type Joint (RTJ) groove cannot seal against Raised Face (RF)."),
    ("FF", "RF"): (False, "STRESS CRACKING TRAP: Bolting an RF flange to a Flat Face (FF) cast iron/bronze mating flange risks fracturing the flange body."),
    ("RF", "FF"): (False, "STRESS CRACKING TRAP: Flat Face flange cannot take concentrated gasket pressure from Raised Face flange."),
    ("BW", "RF"): (False, "CONNECTION MISMATCH: Butt-weld end cannot replace flanged end."),
    ("RF", "BW"): (False, "CONNECTION MISMATCH: Flanged end cannot replace butt-weld end."),
}


def evaluate_facing_compatibility(source_facing: Optional[str], candidate_facing: Optional[str]) -> Tuple[bool, str]:
    """
    Evaluates flange facing or valve end-connection mating compatibility.
    """
    if not source_facing or not candidate_facing:
        # If facing is not specified (e.g. stud bolts where facing is THRD), treat as neutral
        return (True, "End connection not constrained.")
        
    s_face = source_facing.strip().upper()
    c_face = candidate_facing.strip().upper()

    key = (s_face, c_face)
    if key in FACING_COMPATIBILITY:
        return FACING_COMPATIBILITY[key]

    return (False, f"Incompatible end connection: Cannot mate '{s_face}' with '{c_face}'.")
