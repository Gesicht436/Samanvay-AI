import pytest

import machine_learning.ner_tagger as ner_tagger_module
from machine_learning.ner_tagger import NERTagger


def test_ner_pipeline_normalizes_all_six_entity_groups():
    tagger = NERTagger(
        pipeline=lambda _: [
            {"entity_group": "ITEM_TYPE", "word": "GATE VALVE"},
            {"entity_group": "SIZE", "word": "1 1/2 inch"},
            {"entity_group": "PRESSURE_RATING", "word": "PN100"},
            {"entity_group": "METALLURGY", "word": "316L"},
            {"entity_group": "FACING_END", "word": "RTJ"},
            {"entity_group": "STANDARD", "word": "API 600"},
        ]
    )

    attributes = tagger.extract_attributes("unstructured")

    assert attributes.item_type == "GATE VALVE"
    assert attributes.size_nb_mm == pytest.approx(38.1)
    assert attributes.pressure_class == 600
    assert attributes.metallurgy == "SS316L"
    assert attributes.material_grade == "SS316L"
    assert attributes.facing_end == "RTJ"
    assert attributes.standard == "API 600"


def test_ner_pipeline_consumes_industry_specific_entity_groups():
    tagger = NERTagger(
        pipeline=lambda _: [
            {"entity_group": "INDIAN_STANDARD", "word": "IS 1239"},
            {"entity_group": "OISD_STANDARD", "word": "OISD-STD-141"},
            {"entity_group": "GEM_CATEGORY", "word": "40141600"},
            {"entity_group": "TEMPERATURE_RATING", "word": "120 C"},
        ]
    )

    attributes = tagger.extract_attributes("unstructured")

    assert attributes.indian_standard == "IS 1239"
    assert attributes.oisd_standard == "OISD-STD-141"
    assert attributes.gem_category == "40141600"
    assert attributes.temperature_rating == 120


def test_certificate_numbers_are_not_misread_as_nominal_sizes():
    attributes = NERTagger().extract_attributes("Certificate No: MTC-7")

    assert attributes.certificate_number == "MTC-7"
    assert attributes.size_nb_mm is None


def test_extract_attributes_reuses_lazy_module_singleton(monkeypatch):
    calls = []

    class FakeTagger:
        def extract_attributes(self, text):
            calls.append(text)
            return text

    def build_tagger():
        calls.append("constructed")
        return FakeTagger()

    ner_tagger_module._get_default_tagger.cache_clear()
    monkeypatch.setattr(ner_tagger_module, "NERTagger", build_tagger)
    try:
        assert ner_tagger_module.extract_attributes("first") == "first"
        assert ner_tagger_module.extract_attributes("second") == "second"
        assert calls == ["constructed", "first", "second"]
    finally:
        ner_tagger_module._get_default_tagger.cache_clear()
