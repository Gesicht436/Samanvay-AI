ASTM_LIMITS = {
    "A105": {"C": (0.0, 0.35), "Mn": (0.60, 1.05), "P": (0.0, 0.035), "S": (0.0, 0.040), "Si": (0.10, 0.35)},
    "A350 LF2": {"C": (0.0, 0.30), "Mn": (0.60, 1.35), "P": (0.0, 0.035), "S": (0.0, 0.040), "Si": (0.15, 0.30)},
    "A182 F304": {"C": (0.0, 0.08), "Mn": (0.0, 2.00), "P": (0.0, 0.045), "S": (0.0, 0.030), "Si": (0.0, 1.00), "Cr": (18.0, 20.0), "Ni": (8.0, 11.0)},
    "A182 F316": {"C": (0.0, 0.08), "Mn": (0.0, 2.00), "P": (0.0, 0.045), "S": (0.0, 0.030), "Si": (0.0, 1.00), "Cr": (16.0, 18.0), "Ni": (10.0, 14.0), "Mo": (2.0, 3.0)},
}

def compute_carbon_equivalent(composition: dict) -> float:
    """IIW Carbon Equivalent Formula"""
    C = composition.get("C", 0.0)
    Mn = composition.get("Mn", 0.0)
    Cr = composition.get("Cr", 0.0)
    Mo = composition.get("Mo", 0.0)
    V = composition.get("V", 0.0)
    Ni = composition.get("Ni", 0.0)
    Cu = composition.get("Cu", 0.0)
    
    ce = C + (Mn / 6) + ((Cr + Mo + V) / 5) + ((Ni + Cu) / 15)
    return float(ce)

def classify_weldability(ce: float) -> str:
    if ce <= 0.43:
        return 'STANDARD_WELDABLE'
    return 'PREHEAT_REQUIRED_HIGH_CE'

def compute_pren(composition: dict) -> float:
    """Pitting Resistance Equivalent Number"""
    Cr = composition.get("Cr", 0.0)
    Mo = composition.get("Mo", 0.0)
    N = composition.get("N", 0.0)
    return float(Cr + 3.3 * Mo + 16 * N)

def validate_composition(composition: dict, grade: str) -> tuple[bool, list[str]]:
    violations = []
    if grade not in ASTM_LIMITS:
        return True, ["Grade limits not found in ASTM_LIMITS dict, passing by default."]
        
    limits = ASTM_LIMITS[grade]
    for el, (min_val, max_val) in limits.items():
        val = composition.get(el)
        if val is not None:
            if val < min_val:
                violations.append(f"{el} is below minimum ({val} < {min_val})")
            elif val > max_val:
                violations.append(f"{el} is above maximum ({val} > {max_val})")
                
    return len(violations) == 0, violations
