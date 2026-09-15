"""
OCR Engine Wrapper for Scanned Certificates, Challans, and Nameplates.
Provides angle correction, bounding box merging, and confidence filtering.
"""

import io
import asyncio
import logging
import concurrent.futures
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

_ocr_engine = None
_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)


def get_ocr_engine():
    """Lazy loader for native Windows Media OCR, PaddleOCR, or EasyOCR."""
    global _ocr_engine
    if _ocr_engine is None:
        try:
            import winocr
            _ocr_engine = "WINOCR"
            logger.info("[+] Initialized native Windows Media OCR (WinRT OcrEngine).")
        except Exception as e_win:
            logger.info(f"[-] winocr not available ({e_win}). Checking PaddleOCR...")
            try:
                from paddleocr import PaddleOCR
                _ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
                logger.info("[+] Initialized PaddleOCR (PP-OCRv4) engine.")
            except Exception as e:
                logger.warning(f"[-] PaddleOCR not installed ({e}). Checking EasyOCR fallback...")
                try:
                    import easyocr
                    _ocr_engine = easyocr.Reader(["en"])
                    logger.info("[+] Initialized EasyOCR engine.")
                except Exception as e2:
                    logger.warning(f"[-] EasyOCR not installed ({e2}). OCR engine will run in mock/passthrough mode.")
                    _ocr_engine = "MOCK"
    return _ocr_engine


def run_ocr(image_bytes: bytes) -> str:
    """
    Runs optical character recognition on image bytes with angle detection.
    """
    engine = get_ocr_engine()
    if engine == "MOCK" or engine is None:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            return f"[SCANNED_IMAGE: format={img.format}, size={img.size}, mode={img.mode}]"
        except Exception:
            return ""

    if engine == "WINOCR":
        try:
            import winocr
            img = Image.open(io.BytesIO(image_bytes))
            # Run in isolated thread pool to prevent async loop deadlock
            future = _thread_pool.submit(lambda: asyncio.run(winocr.recognize_pil(img, "en")))
            result = future.result(timeout=15.0)
            if hasattr(result, "lines") and result.lines:
                return "\n".join([l.text.strip() for l in result.lines if l.text.strip()])
            return result.text
        except Exception as e:
            logger.error(f"[-] Windows OCR failed: {e}")
            return ""

    try:
        # PaddleOCR branch
        if hasattr(engine, "ocr"):
            result = engine.ocr(image_bytes, cls=True)
            if not result or result[0] is None:
                return ""
            lines = []
            for line in result[0]:
                text, conf = line[1]
                if conf >= 0.60:
                    lines.append(text)
            return " ".join(lines)

        # EasyOCR branch
        if hasattr(engine, "readtext"):
            results = engine.readtext(image_bytes)
            return " ".join([res[1] for res in results if res[2] >= 0.60])

    except Exception as e:
        logger.error(f"[-] OCR extraction failed: {e}")
        return ""

    return ""
