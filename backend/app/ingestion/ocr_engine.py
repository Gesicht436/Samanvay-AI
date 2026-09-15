import os
import tempfile
from paddleocr import PaddleOCR

os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"

_OCR_INSTANCE = None

def get_ocr_instance():
    global _OCR_INSTANCE
    if _OCR_INSTANCE is None:
        _OCR_INSTANCE = PaddleOCR(
            lang="en",
            enable_mkldnn=False,
            ocr_version="PP-OCRv4"
        )
    return _OCR_INSTANCE

def run_ocr(image_bytes: bytes, min_confidence: float = 0.60):
    ocr = get_ocr_instance()
    
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        result = ocr.ocr(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    if not result:
        return "", 0.0

    lines = []
    confidences = []

    # Handle both new PaddleX dict output and standard list output
    entries = result[0] if isinstance(result, list) and len(result) > 0 else result
    if isinstance(entries, dict):
        texts = entries.get("rec_texts", entries.get("texts", []))
        scores = entries.get("rec_scores", entries.get("scores", []))
        for t, s in zip(texts, scores):
            if s >= min_confidence and str(t).strip():
                lines.append(str(t).strip())
                confidences.append(float(s))
    elif isinstance(entries, list):
        for item in entries:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                content = item[1]
                if isinstance(content, (list, tuple)) and len(content) >= 2:
                    t, s = content[0], content[1]
                else:
                    t, s = str(content), 1.0
                if float(s) >= min_confidence and str(t).strip():
                    lines.append(str(t).strip())
                    confidences.append(float(s))

    reconstructed_text = "\n".join(lines)
    mean_conf = float(sum(confidences) / len(confidences)) if confidences else 0.0
    return reconstructed_text, round(mean_conf, 4)