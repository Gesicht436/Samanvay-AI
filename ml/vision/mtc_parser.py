import re

class MTCParser:
    def __init__(self):
        pass
        
    def parse_header(self, text: str) -> dict:
        return {
            "heat_no": self._extract_regex(text, r'Heat No[.:\s]+([A-Z0-9-]+)'),
            "certificate_no": self._extract_regex(text, r'Certificate No[.:\s]+([A-Z0-9-]+)'),
            "po_reference": self._extract_regex(text, r'PO No[.:\s]+([A-Z0-9-]+)'),
            "manufacturer": "UNKNOWN",
            "tpi_agency": "UNKNOWN"
        }
        
    def parse_chemical_composition(self, text: str) -> dict:
        elements = ["C", "Mn", "Si", "P", "S", "Cr", "Mo", "Ni", "V", "Cu"]
        comp = {}
        for el in elements:
            # Mock extraction
            match = re.search(rf'{el}\s*[:=]?\s*(\d+\.\d+)', text)
            if match:
                comp[el] = float(match.group(1))
        return comp
        
    def parse_mechanical_properties(self, text: str) -> dict:
        return {
            "yield_strength": self._extract_float(text, r'Yield Strength.*?(\d+\.?\d*)'),
            "tensile_strength": self._extract_float(text, r'Tensile Strength.*?(\d+\.?\d*)'),
            "elongation": self._extract_float(text, r'Elongation.*?(\d+\.?\d*)'),
            "charpy_impact": self._extract_float(text, r'Impact.*?(\d+\.?\d*)')
        }
        
    def validate_against_astm(self, composition: dict, grade: str) -> tuple[bool, list[str]]:
        violations = []
        # Mock validation
        if "C" in composition and composition["C"] > 0.35:
            violations.append("Carbon exceeds ASTM limits")
        return len(violations) == 0, violations
        
    def parse_full_mtc(self, text: str) -> dict:
        return {
            "header": self.parse_header(text),
            "chemistry": self.parse_chemical_composition(text),
            "mechanical": self.parse_mechanical_properties(text)
        }
        
    def _extract_regex(self, text, pattern):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1) if m else None
        
    def _extract_float(self, text, pattern):
        m = re.search(pattern, text, re.IGNORECASE)
        return float(m.group(1)) if m else None
