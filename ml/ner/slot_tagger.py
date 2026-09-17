import re
from typing import Optional

try:
    from backend.app.schemas.material import ExtractedMaterialAttributes
except ImportError:
    # Fallback if not found for testing
    from pydantic import BaseModel
    class ExtractedMaterialAttributes(BaseModel):
        item_type: Optional[str] = None
        size: Optional[str] = None
        pressure_class: Optional[str] = None
        metallurgy: Optional[str] = None
        facing: Optional[str] = None
        schedule: Optional[str] = None
        standard: Optional[str] = None
        confidence: float = 1.0

class SlotTagger:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.has_model = False
        if model_path:
            try:
                import onnxruntime
                self.has_model = True
            except ImportError:
                pass
                
    def tag(self, text: str) -> ExtractedMaterialAttributes:
        if self.has_model:
            # Placeholder for actual ONNX inference
            pass
        return self._fallback_regex_tagger(text)
        
    def _fallback_regex_tagger(self, text: str) -> ExtractedMaterialAttributes:
        text = text.upper()
        attrs = {}
        
        # Item Type
        item_types = ["FLANGE", "VALVE", "PIPE", "ELBOW", "TEE", "REDUCER", "BLIND"]
        for it in item_types:
            if it in text:
                attrs["item_type"] = it
                break
                
        # Size
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:INCH|IN|"|MM|NPS|DN)', text)
        if size_match:
            attrs["size"] = size_match.group(0)
            
        # Class
        class_match = re.search(r'(?:CLASS|#|PN)\s*(\d+)', text)
        if class_match:
            attrs["pressure_class"] = class_match.group(0)
            
        # Material
        mat_match = re.search(r'ASTM\s+[A-Z\d-]+(?:\s+[A-Z\d-]+)?', text)
        if mat_match:
            attrs["metallurgy"] = mat_match.group(0)
            
        # Facing
        facings = ["RF", "RTJ", "FF", "BW", "SW", "NPT"]
        for f in facings:
            if re.search(rf'\b{f}\b', text):
                attrs["facing"] = f
                break
                
        # Schedule
        sch_match = re.search(r'(?:SCH|SCHEDULE)\s*(\d+[A-Z]?)', text)
        if sch_match:
            attrs["schedule"] = sch_match.group(0)
            
        # Standard
        std_match = re.search(r'(?:ASME|API|ASTM)\s+[A-Z\d\.]+', text)
        if std_match:
            attrs["standard"] = std_match.group(0)
            
        return ExtractedMaterialAttributes(**attrs, confidence=0.8)
