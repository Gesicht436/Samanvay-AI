"""Centralized configuration for the OCR pipeline."""

from dataclasses import dataclass


@dataclass
class OCRConfig:
    min_confidence: float = 0.40
    digital_page_char_limit: int = 50
    printable_char_ratio_min: float = 0.70

    target_dpi: int = 300
    clahe_clip_limit: float = 2.0
    clahe_tile_grid_size: tuple[int, int] = (8, 8)
    max_image_pixels: int = 25_000_000

    max_page_limit: int = 50
    max_file_size_bytes: int = 25 * 1024 * 1024

    row_height_ratio: float = 0.5


DEFAULT_CONFIG = OCRConfig()
