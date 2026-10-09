"""Layout metadata for OCR blocks, with an optional LayoutLMv3 adapter."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LayoutRegion:
    label: str
    block_indexes: list[int]


class LayoutAnalyzer:
    """Group OCR blocks into useful document regions without requiring a model."""

    def analyze(self, blocks: list[dict[str, Any]], image_height: float) -> list[LayoutRegion]:
        if not blocks:
            return []
        table = [index for index, block in enumerate(blocks) if block.get("y", 0) > image_height * 0.2]
        header = [index for index, block in enumerate(blocks) if block.get("y", 0) <= image_height * 0.2]
        regions = []
        if header:
            regions.append(LayoutRegion("header", header))
        if table:
            regions.append(LayoutRegion("body", table))
        return regions


class LayoutLMv3Analyzer(LayoutAnalyzer):
    """Optional model hook; loading is explicit so basic ingestion stays lightweight."""

    def __init__(self, model_name: str = "microsoft/layoutlmv3-base") -> None:
        self.model_name = model_name
        self.available = False
        try:
            from transformers import LayoutLMv3Processor  # noqa: F401

            self.available = True
        except ImportError:
            self.available = False