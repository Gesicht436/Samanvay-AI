import math
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field

# 1. EXPANDED CPSE DIALECT THESAURUS
EXPANDED_THESAURUS: Dict[str, str] = {
    "CS": "Carbon Steel", "SS": "Stainless Steel", "AS": "Alloy Steel",
    "LTCS": "Low Temperature Carbon Steel", "NACE": "NACE MR0175 Compliant",
    "A105": "ASTM A105", "A350": "ASTM A350", "LF2": "ASTM A350 LF2",
    "316L": "SS 316L", "304L": "SS 304L", "F316": "ASTM A182 F316", "F304": "ASTM A182 F304",
    "CL": "Class", "CL150": "Class 150", "CL300": "Class 300", "CL600": "Class 600",
    "150#": "Class 150", "300#": "Class 300", "600#": "Class 600",
    "RF": "Raised Face", "FF": "Flat Face", "RTJ": "Ring Type Joint", "SW": "Socket Weld",
    "NPT": "National Pipe Thread", "BW": "Butt Weld", "VLV": "Valve", "GTR": "Gate Valve",
    "GLB": "Globe Valve", "CHK": "Check Valve", "BLL": "Ball Valve", "FLG": "Flange",
    "WN": "Weld Neck Flange", "SO": "Slip On Flange", "BLD": "Blind Flange", "FTG": "Fitting",
    "ELB": "Elbow", "TEE": "Equal Tee", "RED": "Reducer", "SCH": "Schedule"
}

# 2. DATA STRUCTURES
@dataclass
class Block:
    text: str
    score: float
    bbox: List[float] = field(default_factory=list)

@dataclass
class Page:
    page_number: int
    needs_ocr: bool = False
    blocks: List[Block] = field(default_factory=list)

@dataclass
class DocumentExtraction:
    pages: List[Page] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def raw_text(self) -> str:
        text_runs = []
        for page in self.pages:
            for block in page.blocks:
                if block.text.strip():
                    text_runs.append(block.text.strip())
        return "\n".join(text_runs)

    @property
    def confidence(self) -> float:
        scores = [b.score for p in self.pages for b in p.blocks if b.score is not None]
        return float(sum(scores) / len(scores)) if scores else 0.0

    def to_mtc_input(self) -> Tuple[str, float]:
        return self.raw_text, self.confidence

# 3. TEXT NORMALIZATION
def normalize_text(text: str) -> str:
    if not text:
        return ""
    sorted_keys = sorted(EXPANDED_THESAURUS.keys(), key=len, reverse=True)
    for key in sorted_keys:
        value = EXPANDED_THESAURUS[key]
        escaped_key = re.escape(key)
        pattern = re.compile(rf'(?<!\w){escaped_key}(?!\w)', re.IGNORECASE)
        text = pattern.sub(value, text)
    return text.strip()

# 4. HARMONIZED OCR ENGINE
class UnifiedPaddleOCREngine:
    def __init__(self, lang: str = 'en', min_confidence: float = 0.4):
        self.min_confidence = min_confidence
        from paddleocr import PaddleOCR
        try:
            self.ocr_engine = PaddleOCR(
                lang=lang,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=True,
                enable_mkldnn=False,
                enable_hpi=False
            )
        except TypeError:
            self.ocr_engine = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def _preprocess_image(self, image_input: Any) -> Any:
        import cv2
        import numpy as np

        if isinstance(image_input, str):
            img = cv2.imread(image_input)
        elif isinstance(image_input, np.ndarray):
            img = image_input
        else:
            return image_input

        if img is None:
            return image_input

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        norm_img = cv2.normalize(gray, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        return cv2.fastNlMeansDenoising(norm_img, h=10)

    def extract_page_raster(self, page_image: Any, page_num: int) -> Page:
        preprocessed = self._preprocess_image(page_image)
        try:
            raw_results = self.ocr_engine.ocr(preprocessed, cls=True)
        except TypeError:
            raw_results = self.ocr_engine.ocr(preprocessed)

        blocks: List[Block] = []
        if raw_results and raw_results[0]:
            for line in raw_results[0]:
                box, (text, score) = line[0], line[1]
                if float(score) < self.min_confidence:
                    continue

                y_min = min(pt[1] for pt in box)
                x_min = min(pt[0] for pt in box)
                blocks.append(Block(
                    text=normalize_text(text),
                    score=float(score),
                    bbox=[x_min, y_min, max(pt[0] for pt in box), max(pt[1] for pt in box)]
                ))

        # Spatial sorting: (y // 8, x) for row alignment
        blocks.sort(key=lambda b: (math.floor(b.bbox[1] / 8.0) if b.bbox else 0, b.bbox[0] if b.bbox else 0))
        return Page(page_number=page_num, needs_ocr=True, blocks=blocks)

    def process_pdf_per_page(self, pdf_path: str) -> DocumentExtraction:
        import fitz  # PyMuPDF
        import numpy as np

        doc_extraction = DocumentExtraction()
        doc = fitz.open(pdf_path)

        for page_idx, page in enumerate(doc):
            words = page.get_text("words")
            if len(words) > 10:
                blocks = []
                for w in words:
                    blocks.append(Block(
                        text=normalize_text(w[4]),
                        score=1.0,
                        bbox=[w[0], w[1], w[2], w[3]]
                    ))
                blocks.sort(key=lambda b: (math.floor(b.bbox[1] / 8.0) if b.bbox else 0, b.bbox[0] if b.bbox else 0))
                doc_extraction.pages.append(Page(page_number=page_idx + 1, needs_ocr=False, blocks=blocks))
            else:
                pix = page.get_pixmap(dpi=300)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                page_obj = self.extract_page_raster(img, page_num=page_idx + 1)
                doc_extraction.pages.append(page_obj)

        return doc_extraction