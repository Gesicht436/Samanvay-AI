"""
High-Performance Multi-Modal OCR Engine for Scanned Certificates, Challans, and MTCs.
Includes image pre-processing (contrast enhancement, deskewing, binarization),
multi-engine cascading (Windows Media OCR -> PaddleOCR -> EasyOCR),
and confidence-driven enhancement retries.
"""

import io
import math
import asyncio
import logging
import concurrent.futures
from typing import Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np

logger = logging.getLogger(__name__)

_ocr_engine = None
_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)


# -----------------------------------------------------------------------------
# 1. Computer Vision & Image Pre-Processing Transforms
# -----------------------------------------------------------------------------

def estimate_skew_angle(img_gray: Image.Image) -> float:
    """
    Estimates document skew angle in degrees using projection profile variance.
    Supports pure NumPy and Pillow without requiring heavy external CV runtimes.
    """
    try:
        # Resize to thumbnail for speed
        thumb = img_gray.resize((400, int(400 * img_gray.height / max(1, img_gray.width))), Image.Resampling.BILINEAR)
        arr = np.array(thumb, dtype=np.uint8)
        
        # Invert and threshold to binary
        binary = (arr < 128).astype(np.float32)
        
        best_score = -1.0
        best_angle = 0.0
        
        # Test angles between -10 and +10 degrees in steps of 1 degree
        for angle in range(-10, 11, 1):
            if angle == 0:
                rotated = binary
            else:
                rot_img = Image.fromarray((binary * 255).astype(np.uint8)).rotate(
                    angle, resample=Image.Resampling.NEAREST, expand=False
                )
                rotated = np.array(rot_img, dtype=np.float32) / 255.0
            
            # Row projection profile: variance of horizontal pixel sums
            row_sums = np.sum(rotated, axis=1)
            score = np.var(row_sums)
            if score > best_score:
                best_score = score
                best_angle = float(angle)
                
        # Return skew only if noticeable (> 0.5 degrees)
        return best_angle if abs(best_angle) >= 0.5 else 0.0
    except Exception as e:
        logger.debug(f"Skew angle estimation skipped: {e}")
        return 0.0


def preprocess_image_for_ocr(
    pil_img: Image.Image,
    apply_deskew: bool = True,
    apply_contrast: bool = True,
    apply_binarization: bool = False
) -> Image.Image:
    """
    Applies image enhancement pipeline to maximize OCR character recognition:
      1. Resolution normalization: Upscales low-DPI mobile scans.
      2. Orientation & deskewing: Corrects tilted certificate scans.
      3. Grayscale conversion and local contrast stretching.
      4. Optional adaptive binarization for faint dot-matrix receipts.
    """
    img = pil_img.copy()

    # Step 1: Convert RGBA to RGB
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Step 2: Resolution normalization (ensure minimum width of 1600px for clear font strokes)
    min_width = 1600
    if img.width < min_width:
        scale = min_width / max(1, img.width)
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.Resampling.BICUBIC)

    # Step 3: Grayscale conversion
    gray = img.convert("L")

    # Step 4: Deskewing
    if apply_deskew:
        angle = estimate_skew_angle(gray)
        if abs(angle) >= 0.5:
            gray = gray.rotate(-angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=255)

    # Step 5: Contrast enhancement & Unsharp Mask sharpening
    if apply_contrast:
        # Autocontrast to stretch histogram
        gray = ImageOps.autocontrast(gray, cutoff=1)
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(1.4)
        sharpener = ImageEnhance.Sharpness(gray)
        gray = sharpener.enhance(1.3)

    # Step 6: Adaptive Thresholding (Otsu-style binarization fallback for faint scans)
    if apply_binarization:
        arr = np.array(gray, dtype=np.uint8)
        # Calculate Otsu threshold
        hist, _ = np.histogram(arr, bins=256, range=(0, 256))
        total = arr.size
        current_max, threshold = 0, 128
        sum_total = np.dot(np.arange(256), hist)
        sum_back, weight_back = 0, 0

        for t in range(256):
            weight_back += hist[t]
            if weight_back == 0:
                continue
            weight_fore = total - weight_back
            if weight_fore == 0:
                break
            sum_back += t * hist[t]
            mean_back = sum_back / weight_back
            mean_fore = (sum_total - sum_back) / weight_fore
            between_var = weight_back * weight_fore * ((mean_back - mean_fore) ** 2)
            if between_var > current_max:
                current_max = between_var
                threshold = t

        bin_arr = np.where(arr > threshold, 255, 0).astype(np.uint8)
        gray = Image.fromarray(bin_arr)

    return gray


# -----------------------------------------------------------------------------
# 2. Multi-Engine OCR Loader & Dispatcher
# -----------------------------------------------------------------------------

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


def run_ocr(image_bytes: bytes, auto_enhance_retry: bool = True) -> str:
    """
    Runs optical character recognition on image bytes.
    If the initial pass yields sparse or low-confidence text (< 30 characters),
    automatically enhances contrast/binarization and retries.
    """
    engine = get_ocr_engine()
    if engine == "MOCK" or engine is None:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            return f"[SCANNED_IMAGE: format={img.format}, size={img.size}, mode={img.mode}]"
        except Exception:
            return ""

    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        logger.error(f"[-] Failed to decode image bytes for OCR: {e}")
        return ""

    text = _execute_engine_ocr(engine, pil_img, image_bytes)

    # If extraction is sparse or failed, apply pre-processing enhancements and retry
    if auto_enhance_retry and len(text.strip()) < 35:
        logger.debug("[+] Initial OCR extraction sparse (<35 chars). Applying adaptive enhancement retry...")
        try:
            enhanced_img = preprocess_image_for_ocr(
                pil_img,
                apply_deskew=True,
                apply_contrast=True,
                apply_binarization=True
            )
            buf = io.BytesIO()
            enhanced_img.save(buf, format="PNG")
            enhanced_bytes = buf.getvalue()
            enhanced_text = _execute_engine_ocr(engine, enhanced_img, enhanced_bytes)
            if len(enhanced_text.strip()) > len(text.strip()):
                return enhanced_text
        except Exception as err:
            logger.debug(f"Enhancement retry skipped: {err}")

    return text


def _execute_engine_ocr(engine: Any, img: Image.Image, raw_bytes: bytes) -> str:
    """Internal helper to dispatch OCR call to the active backend."""
    if engine == "WINOCR":
        try:
            import winocr
            future = _thread_pool.submit(lambda: asyncio.run(winocr.recognize_pil(img, "en")))
            result = future.result(timeout=15.0)
            if hasattr(result, "lines") and result.lines:
                return "\n".join([l.text.strip() for l in result.lines if l.text.strip()])
            return getattr(result, "text", "")
        except Exception as e:
            logger.error(f"[-] Windows OCR execution failed: {e}")
            return ""

    if hasattr(engine, "ocr"):
        # PaddleOCR branch
        try:
            result = engine.ocr(raw_bytes, cls=True)
            if not result or result[0] is None:
                return ""
            lines = [line[1][0] for line in result[0] if line[1][1] >= 0.50]
            return " ".join(lines)
        except Exception as e:
            logger.error(f"[-] PaddleOCR failed: {e}")
            return ""

    if hasattr(engine, "readtext"):
        # EasyOCR branch
        try:
            results = engine.readtext(raw_bytes)
            return " ".join([res[1] for res in results if res[2] >= 0.50])
        except Exception as e:
            logger.error(f"[-] EasyOCR failed: {e}")
            return ""

    return ""
