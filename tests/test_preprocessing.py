"""Unit tests for image preprocessing pipeline."""

import numpy as np
from ml.vision.preprocessing import (
    estimate_deskew_angle,
    normalize_dpi,
    preprocess_page_image,
)


def test_normalize_dpi_upscales_small_images():
    small_img = np.zeros((400, 500, 3), dtype=np.uint8)
    rescaled = normalize_dpi(small_img)
    assert min(rescaled.shape[:2]) == 1600


def test_normalize_dpi_preserves_large_images():
    large_img = np.zeros((2000, 2500, 3), dtype=np.uint8)
    rescaled = normalize_dpi(large_img)
    assert rescaled.shape == large_img.shape


def test_preprocess_page_image_returns_valid_rgb_array():
    img_np = np.full((300, 400, 3), 200, dtype=np.uint8)
    out = preprocess_page_image(img_np)
    assert out.ndim == 3
    assert out.shape[2] == 3
    assert min(out.shape[:2]) >= 1600
