"""Image preprocessing module for document deskewing, CLAHE contrast tuning, and DPI normalization."""

import logging
import cv2
import numpy as np
from PIL import Image

from ml.vision.config import DEFAULT_CONFIG, OCRConfig

logger = logging.getLogger(__name__)


def normalize_dpi(image_np: np.ndarray, config: OCRConfig = DEFAULT_CONFIG) -> np.ndarray:
    """Rescales image to achieve a target resolution baseline (~300 DPI equivalent)."""
    h, w = image_np.shape[:2]
    min_dim = min(h, w)
    target_min_dim = 1600  # Standard A4 short edge at 300 DPI is ~2480px; 1600px is safe lower bound

    if min_dim < target_min_dim:
        scale = float(target_min_dim) / float(min_dim)
        new_w = int(round(w * scale))
        new_h = int(round(h * scale))
        return cv2.resize(image_np, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    return image_np


def estimate_deskew_angle(gray_np: np.ndarray) -> float:
    """Estimates skew angle between -45 and +45 degrees using horizontal projection variance via cv2."""
    h, w = gray_np.shape
    sample = (gray_np[::2, ::2] < 128).astype(np.float32)  # Binary foreground mask
    sh, sw = sample.shape
    center = (sw // 2, sh // 2)

    angles = np.linspace(-45.0, 45.0, 91)
    max_variance = -1.0
    best_angle = 0.0

    for angle in angles:
        M = cv2.getRotationMatrix2D(center, float(angle), 1.0)
        rot_mask = cv2.warpAffine(sample, M, (sw, sh), flags=cv2.INTER_NEAREST)
        proj = np.sum(rot_mask, axis=1)
        var = float(np.var(proj))
        if var > max_variance:
            max_variance = var
            best_angle = float(angle)

    return best_angle


def preprocess_page_image(
    image_input: Image.Image | np.ndarray, config: OCRConfig = DEFAULT_CONFIG
) -> np.ndarray:
    """Executes DPI normalization, deskew rotation, and CLAHE contrast enhancement."""
    if isinstance(image_input, Image.Image):
        img_np = np.array(image_input.convert("RGB"))
    else:
        img_np = image_input.copy()

    # 1. Normalize DPI
    rescaled = normalize_dpi(img_np, config)

    # Convert to Grayscale for Processing
    if len(rescaled.shape) == 3 and rescaled.shape[2] == 3:
        gray = cv2.cvtColor(rescaled, cv2.COLOR_RGB2GRAY)
    else:
        gray = rescaled.copy()

    # 2. Deskew
    skew_angle = estimate_deskew_angle(gray)
    if abs(skew_angle) >= 0.5:
        logger.info(f"Deskewing image by {skew_angle:.2f} degrees.")
        h, w = rescaled.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
        rescaled = cv2.warpAffine(
            rescaled, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        gray = cv2.cvtColor(rescaled, cv2.COLOR_RGB2GRAY)

    # 3. CLAHE Contrast Enhancement
    clahe = cv2.createCLAHE(
        clipLimit=config.clahe_clip_limit,
        tileGridSize=config.clahe_tile_grid_size,
    )
    enhanced_gray = clahe.apply(gray)

    # Convert back to 3-channel RGB for PaddleOCR engine compatibility
    out_rgb = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2RGB)
    return out_rgb
