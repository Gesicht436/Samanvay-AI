"""Tests for ml/vision/schema_adapter.py (parser output -> ExtractedMaterialAttributes).

Expected values are printed on the sample certificates. Where a value is NOT
printed (e.g. a bare '150' with no LB/CLASS) the adapter must leave it empty.
"""

import json
from pathlib import Path

from ml.vision.layout_parser import parse_certificate
from ml.vision.schema_adapter import parse_description, parse_size_inches, to_attribute_dicts

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "ocr_blocks"


def adapt(name):
    blocks = json.loads((FIXTURES / f"{name}_blocks.json").read_text(encoding="utf-8"))
    return to_attribute_dicts(parse_certificate(blocks))


def test_size_parsing_handles_fractions():
    assert parse_size_inches('1 1/2"') == 1.5
    assert parse_size_inches('3/4"') == 0.75
    assert parse_size_inches('2 1/2"') == 2.5
    assert parse_size_inches('8"') == 8.0
    assert parse_size_inches("150 WN RF") is None       # no inch mark: not a size
    # The "5" in "B16.5" must not be read as part of the size that follows it.
    assert parse_size_inches('ANSI B16.5 1/2"') == 0.5
    assert parse_size_inches('ANSI B16.5 3/4"') == 0.75
    assert parse_size_inches('ASME B16.5 1 1/2"') == 1.5


def test_bare_number_is_not_a_pressure_class():
    assert "pressure_class" not in parse_description("FLANGE ASME B16.5 150 WN RF SCH40")
    assert parse_description("1\" 300LB SCH 160 WN")["pressure_class"] == 300
    assert parse_description("SLIP ON IN CLASS 600 RF")["pressure_class"] == 600


def test_8826_items_have_all_printed_fields():
    items = adapt("IMG_8826")
    assert len(items) == 3
    first = items[0]
    assert first["item_type"] == "FLANGE" and first["size"] == "1 IN"
    assert first["pressure_class"] == 300 and first["schedule"] == "SCH 160"
    assert first["metallurgy"] == "ASTM A105" and first["standard"] == "ASME B16.5"
    assert first["facing_end"] == "RFFE"                  # kept as printed, not guessed
    assert first["properties"]["attachment"] == "WELD_NECK"
    assert first["properties"]["heat_no"] == "KS00827"
    assert first["properties"]["chemistry"]["C"] == 0.23
    assert items[2]["size"] == "0.75 IN"                  # 3/4"
    assert first["requires_hitl"] is False and first["is_incomplete"] is False


def test_8828_item_type_and_grade_come_from_header_text():
    items = adapt("IMG_8828")
    blind = next(i for i in items if i["properties"]["line_item_no"] == "8")
    assert blind["item_type"] == "FLANGE" and blind["size"] == "0.5 IN"
    assert blind["pressure_class"] == 150 and blind["facing_end"] == "RF"
    assert blind["properties"]["attachment"] == "BLIND"
    assert blind["metallurgy"] == "ASTM A105"


def test_8830_missing_size_and_class_go_to_review():
    items = adapt("IMG_8830")
    first = items[0]                                       # the OCR lost this size
    assert first["size"] is None and first["pressure_class"] is None
    assert {"size_nb_mm", "pressure_class"} <= set(first["missing_attributes"])
    assert first["is_incomplete"] and first["requires_hitl"]
    assert first["properties"]["heat_no"] == "5A4040-114"


def test_9055_elbows_do_not_require_pressure_class():
    items = adapt("IMG_9055")
    assert len(items) == 4
    assert items[0]["item_type"] == "ELBOW" and items[0]["size"] == "1.5 IN"
    assert items[0]["schedule"] == "SCH 40" and items[0]["facing_end"] == "BW"
    assert items[0]["metallurgy"] == "ASTM A815 S32750"
    assert "pressure_class" not in items[0]["missing_attributes"]
    assert items[2]["properties"]["heat_no"] == "PS-1157"


def test_unreliable_tables_never_leak_into_items():
    items = adapt("IMG_8829")
    assert items and all(i["requires_hitl"] for i in items)
    assert all("chemistry" not in i["properties"] for i in items)


def test_non_certificate_gives_no_items():
    assert adapt("IMG_9054") == []
    assert to_attribute_dicts({}) == []


def test_real_pydantic_model_accepts_the_dicts():
    """Runs only where the backend package is importable (your laptop)."""
    try:
        from backend.app.schemas.material import ExtractedMaterialAttributes
    except ImportError:
        return
    for name in ("IMG_8826", "IMG_8828", "IMG_9055"):
        for d in adapt(name):
            model = ExtractedMaterialAttributes(**d)
            assert model.properties["heat_no"]
    first = ExtractedMaterialAttributes(**adapt("IMG_9055")[0])
    assert first.size_nb_mm == 38.1                        # 1.5 in x 25.4 (the schema's own rule)
