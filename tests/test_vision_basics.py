"""Unit tests for the Phase 1 vision scaffold (PaddleOCR 3.x output format)."""

import pytest

from ml.vision.engine import PaddleOCREngine
from ml.vision.exceptions import EngineCrashError
from ml.vision.layout import group_into_lines, lines_to_text
from ml.vision.schemas import Block


def B(text, x0, y0, x1, y1):
    return Block(text=text, confidence=0.9, bbox=(x0, y0, x1, y1), page_num=1)


def test_same_line_with_slightly_different_tops_stays_together():
    lines = group_into_lines([B("ASTM", 10, 11.9, 40, 23.9), B("A105", 50, 12.1, 90, 24.1)])
    assert lines_to_text(lines) == ["ASTM A105"]


def test_distinct_lines_are_separated_and_ordered():
    lines = group_into_lines([B("B", 0, 40, 10, 52), B("A", 0, 0, 10, 12)])
    assert lines_to_text(lines) == ["A", "B"]


def test_low_confidence_tokens_are_kept():
    res = [{"rec_texts": ["0.18"], "rec_scores": [0.12],
            "rec_polys": [[[0, 0], [10, 0], [10, 5], [0, 5]]]}]
    out = PaddleOCREngine._parse(res)
    assert out == [("0.18", pytest.approx(0.12), (0.0, 0.0, 10.0, 5.0))]


def test_empty_result_returns_empty_list():
    assert PaddleOCREngine._parse([]) == []
    assert PaddleOCREngine._parse([None]) == []


def test_unknown_output_shape_raises():
    with pytest.raises(EngineCrashError, match="Unrecognized OCR output shape"):
        PaddleOCREngine._parse(["garbage"])