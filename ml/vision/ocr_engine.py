import os
from typing import Tuple

class OCREngine:
    def __init__(self):
        self.paddle_available = False
        self.fitz_available = False
        
        try:
            import fitz
            self.fitz_available = True
        except ImportError:
            pass
            
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
            self.paddle_available = True
        except ImportError:
            self.ocr = None

    def preprocess_image(self, image_path: str):
        # 300 DPI, contrast, deskew placeholder
        return image_path
        
    def classify_document(self, file_path: str) -> str:
        if file_path.lower().endswith('.pdf'):
            if self.fitz_available:
                import fitz
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                if len(text.strip()) > 100:
                    return 'digital_vector'
        return 'raster_scan'
        
    def extract_text(self, file_path: str) -> Tuple[str, float]:
        doc_type = self.classify_document(file_path)
        
        if doc_type == 'digital_vector' and self.fitz_available:
            import fitz
            doc = fitz.open(file_path)
            text = "\n".join([page.get_text() for page in doc])
            return text, 1.0
            
        if self.paddle_available:
            result = self.ocr.ocr(file_path, cls=True)
            text = ""
            conf_sum = 0
            count = 0
            for idx in range(len(result)):
                res = result[idx]
                if not res:
                    continue
                for line in res:
                    text += line[1][0] + "\n"
                    conf_sum += line[1][1]
                    count += 1
            avg_conf = (conf_sum / count) if count > 0 else 0.0
            return text, avg_conf
            
        return "OCR engine not fully available", 0.0
