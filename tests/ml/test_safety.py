import pytest

from machine_learning.safety import (
    _metallurgy_compatible,
    _standard_incompatible,
    safety_violations,
)


@pytest.mark.parametrize(
    ("query", "candidate", "expected"),
    [
        ({"size_nb_mm": 100}, {"size_nb_mm": 150}, "size mismatch"),
        ({"pressure_class": 600}, {"pressure_class": 300}, "pressure downgrade"),
        ({"metallurgy": "SS316"}, {"metallurgy": "ASTM_A105"}, "metallurgy downgrade"),
        ({"item_type": "VALVE"}, {"item_type": "BOLT"}, "item type mismatch"),
        (
            {"item_type": "GATE_VALVE", "standard": "API 600"},
            {"item_type": "GATE_VALVE", "standard": "API 608"},
            "incompatible standards",
        ),
    ],
)
def test_safety_violations_rejects_unsafe_candidate_fields(query, candidate, expected):
    assert any(expected in violation for violation in safety_violations(query, candidate))


def test_metallurgy_upgrade_direction_is_safe_but_downgrade_is_not():
    assert _metallurgy_compatible("ASTM_A105", "SS316")
    assert not _metallurgy_compatible("SS316", "ASTM_A105")


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ("API 600", "API 608", True),
        ("API 602", "API 609", True),
        ("API 600", "ASME B16.34", False),
        ("API 608", "ASME B16.34", False),
        ("API 600", "API 602", False),
    ],
)
def test_standard_compatibility_detects_valve_family_mismatches(first, second, expected):
    assert _standard_incompatible(first, second) is expected


@pytest.mark.parametrize(
    ("grade", "expected_rank"),
    [
        ("ASTM A105N", 0),
        ("SS316L", 2),
        ("ASTM A105N0", None),
        ("X316Y", None),
        ("22050", None),
    ],
)
def test_metallurgy_rank_requires_grade_boundaries(grade, expected_rank):
    from machine_learning.safety import _metallurgy_rank

    assert _metallurgy_rank(grade) == expected_rank
