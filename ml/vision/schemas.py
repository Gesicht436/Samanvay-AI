"""Data contracts for layout blocks, extracted fields and results."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Block:
    text: str
    confidence: float
    bbox: tuple[float, float, float, float]
    page_num: int


@dataclass
class FieldValue:
    name: str
    raw: str
    value: Optional[Any] = None
    confidence: float = 0.0
    page: int = 1
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    flags: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    fields: dict[str, FieldValue] = field(default_factory=dict)
    needs_review: bool = False
    review_reasons: list[str] = field(default_factory=list)
    timings_ms: dict[str, float] = field(default_factory=dict)
    pages_digital: int = 0
    pages_raster: int = 0
