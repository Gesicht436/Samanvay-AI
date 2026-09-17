import pytest

def test_dialect_normalization():
    text = "S.S. Pipe"
    normalized = text.replace("S.S.", "STAINLESS STEEL")
    assert normalized == "STAINLESS STEEL Pipe"

def test_slot_extraction():
    # Mock NER output
    text = "100mm Flange 300#"
    extracted_slots = {
        "size": "100mm",
        "item_type": "Flange",
        "rating": "300#"
    }
    assert extracted_slots["size"] == "100mm"
    assert extracted_slots["item_type"] == "Flange"
