"""Tests for ml/vision/layout_parser.py.

The fixtures are real OCR output (text + box positions) from our 7 sample
certificates. Expected numbers below are values printed on those photos.
Run:  python -m pytest tests/unit/test_layout_parser.py -q
"""

import json
from pathlib import Path

from ml.vision.layout_parser import (
    group_rows, parse_cell, parse_certificate, split_merged_numbers, to_blocks,
)
from ml.vision.spec_detect import detect_en10204_type

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "ocr_blocks"


def load(name):
    return json.loads((FIXTURES / f"{name}_blocks.json").read_text(encoding="utf-8"))


def parse(name):
    return parse_certificate(load(name), detect_type=detect_en10204_type)


def by_item(result, item):
    return next(r for r in result["records"] if r["item_no"] == item)


def by_heat(result, heat):
    return next(r for r in result["records"] if r["heat_no"] == heat)


# ---------------- small helpers ----------------

def test_parse_cell_decimals_and_ranges():
    assert parse_cell("0.23") == [0.23]
    assert parse_cell("0,180") == [0.18]            # decimal comma
    assert parse_cell("750,0") == [750.0]
    assert parse_cell("163/165") == [163.0, 165.0]  # two readings
    assert parse_cell("254,255") == [254.0, 255.0]  # two readings, not 254.255


def test_parse_cell_rejects_limits_and_words():
    for text in ["<0.35", ">485", "0.60~1.05", "0.03-", "Max", "GOOD", ""]:
        assert parse_cell(text) is None


def test_split_merged_numbers():
    blocks = to_blocks([{"text": "0,190 0.960", "score": 0.9, "box": [0, 0, 100, 10]}])
    parts = split_merged_numbers(blocks)
    assert [b.text for b in parts] == ["0,190", "0.960"]
    assert parts[0].x1 <= parts[1].x0 + 1


def test_group_rows_orders_left_to_right():
    raw = [{"text": "B", "score": 1, "box": [50, 10, 60, 20]},
           {"text": "A", "score": 1, "box": [10, 11, 20, 21]},
           {"text": "C", "score": 1, "box": [10, 60, 20, 70]}]
    rows = group_rows(to_blocks(raw))
    assert [[b.text for b in r] for r in rows] == [["A", "B"], ["C"]]


def test_bad_blocks_are_skipped_not_fatal():
    blocks = to_blocks([{"text": "ok", "score": 1, "box": [0, 0, 5, 5]},
                        {"text": "no box"}, "garbage", None])
    assert [b.text for b in blocks] == ["ok"]


# ---------------- empty / malformed / missing ----------------

def test_empty_input_is_flagged():
    result = parse_certificate([])
    assert result["records"] == [] and result["review_flags"]


def test_malformed_ocr_text_does_not_crash():
    junk = [{"text": "@@## ~~", "score": 0.2, "box": [0, 0, 40, 10]},
            {"text": "1 2 3", "score": 0.3, "box": [0, 20, 40, 30]}]
    result = parse_certificate(junk)
    assert result["document_type"] != "mill_test_certificate"
    assert result["review_flags"]


def test_missing_chemistry_header_is_flagged():
    elements = {"C%", "Mn%", "P%", "S%", "Si%", "Cu%", "Ni%", "Cr%", "Mo%", "V%"}
    blocks = [b for b in load("IMG_8826") if b["text"] not in elements]
    result = parse_certificate(blocks)
    assert result["records"] == []
    assert result["review_flags"]


# ---------------- real certificates ----------------

def test_8826_clean_table():
    r = parse("IMG_8826")
    assert r["document_type"] == "mill_test_certificate"
    assert r["header"]["certificate_no"] == "B339004F1"
    assert r["header"]["heat_no"] == "KS00827"
    assert len(r["records"]) == 1
    rec = r["records"][0]
    assert rec["chemistry"]["C"] == 0.23 and rec["chemistry"]["Mn"] == 0.87
    assert rec["mechanical"]["yield_strength_mpa"] == 288.0
    assert rec["mechanical"]["tensile_strength_mpa"] == 535.0
    assert rec["mechanical"]["elongation_pct"] == 31.0
    assert [i["quantity"] for i in r["line_items"]] == [9, 5, 6]
    assert r["records_reliable"]


def test_8828_item_numbers_join_chemistry_and_heat():
    r = parse("IMG_8828")
    assert len(r["records"]) == 10
    first, sixth = by_item(r, "1"), by_item(r, "6")
    assert first["heat_no"] == "504" and first["mechanical"]["tensile_strength_mpa"] == 495.0
    assert first["chemistry"]["C"] == 0.19
    assert sixth["heat_no"] == "106"
    assert r["header"]["certificate_no"] == "MTC20201289"


def test_8830_decimal_commas_and_merged_cells():
    r = parse("IMG_8830")
    assert len(r["records"]) == 10
    assert r["header"]["certificate_no"] == "002937 / 03 - BS"
    first, last = by_item(r, "20"), by_item(r, "29")
    assert first["chemistry"]["C"] == 0.18 and first["chemistry"]["Mn"] == 0.96
    assert by_item(r, "22")["chemistry"]["Mn"] == 0.96      # was merged with C by OCR
    assert first["mechanical"]["elongation_pct"] == 32.6
    assert last["mechanical"]["yield_strength_mpa"] == 368.0
    assert first["heat_no"] == "5A4040-114"


def test_9055_heats_and_hardness_readings():
    r = parse("IMG_9055")
    assert r["header"]["certificate_no"] == "DMI/TC/22-23/581"
    assert [x["heat_no"] for x in r["records"]] == ["PS-1155", "PS-1156", "PS-1157"]
    assert by_heat(r, "PS-1156")["mechanical"]["yield_strength_mpa"] == 672.0
    assert by_heat(r, "PS-1157")["chemistry"]["Cr"] == 24.926
    assert by_heat(r, "PS-1157")["mechanical"]["hardness_hb"] == [262.0, 265.0]
    assert len(r["line_items"]) == 4


def test_9056_one_row_table_with_min_max_limits():
    r = parse("IMG_9056")
    assert len(r["records"]) == 1
    rec = r["records"][0]
    assert rec["heat_no"] == "QL200926"
    assert rec["chemistry"]["C"] == 0.024 and rec["chemistry"]["Ni"] == 11.17
    assert rec["mechanical"]["yield_strength_mpa"] == 292.0
    assert rec["mechanical"]["elongation_pct"] == 56.0
    assert r["limits"]["max"]["Ni"] == 14.0
    assert r["header"]["manufacturer"] == "Qili"
    assert "certificate number not found" in r["review_flags"]   # the photo has none


def test_9054_actuator_sheet_is_not_a_certificate():
    r = parse("IMG_9054")
    assert r["document_type"] != "mill_test_certificate"
    assert r["records"] == [] and r["review_flags"]


def test_8829_known_hard_case_is_flagged_not_trusted():
    # This photo's table is split into fragments by OCR. We only require that
    # the parser admits it cannot be trusted.
    r = parse("IMG_8829")
    assert r["records_reliable"] is False
    assert r["review_flags"]
