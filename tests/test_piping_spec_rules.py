"""
Unit tests for Domain Expansion Piping, Gasket, Fastener, Sour Service, and Schedule rules.
Tests ASME B36.10M, NACE MR0175, ASME B16.47, ASME B16.20, and ASTM A193/A194.
"""

import pytest
from backend.app.contracts.material import ExtractedMaterialAttributes, ItemType, FacingEnd
from backend.app.contracts.matching import EquivalenceTier
from backend.app.matching.tolerance import evaluate_compatibility
from backend.app.ml.ner_tagger import extract_attributes


class TestPipeScheduleRules:
    """ASME B36.10M / B36.19M Pipe Schedule and Wall Thickness Tests."""

    def test_exact_schedule_parity(self):
        source = ExtractedMaterialAttributes(
            item_type="PIPE_SEAMLESS",
            size_nb_mm=100.0,
            metallurgy="ASTM A106 GR.B",
            schedule="SCH 40",
            facing_end="BW"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="PIPE_SEAMLESS",
            size_nb_mm=100.0,
            metallurgy="ASTM A106 GR.B",
            schedule="SCH 40",
            facing_end="BW"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_1_IDENTICAL
        assert res.is_compatible is True

    def test_schedule_upgrade_tier2(self):
        # Request Sch 40, Offer Sch 80 (heavier wall thickness)
        source = ExtractedMaterialAttributes(
            item_type="PIPE_SEAMLESS",
            size_nb_mm=100.0,
            metallurgy="ASTM A106 GR.B",
            schedule="SCH 40",
            facing_end="BW"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="PIPE_SEAMLESS",
            size_nb_mm=100.0,
            metallurgy="ASTM A106 GR.B",
            schedule="SCH 80",
            facing_end="BW"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_2_SUBSTITUTE
        assert res.is_compatible is True
        assert any(p.parameter == "Pipe Schedule / Wall Thickness" and p.status == "UPGRADE" for p in res.parameter_checks)

    def test_schedule_downgrade_fatal_tier3(self):
        # Request Sch 80 (extra strong), Offer Sch 40 (standard) -> Fatal burst risk!
        source = ExtractedMaterialAttributes(
            item_type="PIPE_SEAMLESS",
            size_nb_mm=100.0,
            metallurgy="ASTM A106 GR.B",
            schedule="SCH 80",
            facing_end="BW"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="PIPE_SEAMLESS",
            size_nb_mm=100.0,
            metallurgy="ASTM A106 GR.B",
            schedule="SCH 40",
            facing_end="BW"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert res.is_compatible is False
        assert any(v.field == "schedule" for v in res.violations)


class TestSourServiceNACERules:
    """NACE MR0175 / ISO 15156 Sour Service (H2S) Invariant Tests."""

    def test_sour_service_parity_tier1(self):
        source = ExtractedMaterialAttributes(
            item_type="GATE_VALVE",
            size_nb_mm=50.0,
            pressure_class=300,
            metallurgy="ASTM A216 WCB",
            facing_end="RF",
            is_sour_service=True
        )
        candidate = ExtractedMaterialAttributes(
            item_type="GATE_VALVE",
            size_nb_mm=50.0,
            pressure_class=300,
            metallurgy="ASTM A216 WCB",
            facing_end="RF",
            is_sour_service=True
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_1_IDENTICAL
        assert res.is_compatible is True

    def test_sour_service_missing_fatal_tier3(self):
        # Source requires NACE sour service; candidate is standard commercial non-NACE
        source = ExtractedMaterialAttributes(
            item_type="GATE_VALVE",
            size_nb_mm=50.0,
            pressure_class=300,
            metallurgy="ASTM A216 WCB",
            facing_end="RF",
            is_sour_service=True
        )
        candidate = ExtractedMaterialAttributes(
            item_type="GATE_VALVE",
            size_nb_mm=50.0,
            pressure_class=300,
            metallurgy="ASTM A216 WCB",
            facing_end="RF",
            is_sour_service=False
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert res.is_compatible is False
        assert any("NACE" in v.rule_name for v in res.violations)

    def test_non_sour_to_sour_upgrade_tier2(self):
        # Source is standard service; candidate has NACE sour service compliance
        source = ExtractedMaterialAttributes(
            item_type="GATE_VALVE",
            size_nb_mm=50.0,
            pressure_class=300,
            metallurgy="ASTM A216 WCB",
            facing_end="RF",
            is_sour_service=False
        )
        candidate = ExtractedMaterialAttributes(
            item_type="GATE_VALVE",
            size_nb_mm=50.0,
            pressure_class=300,
            metallurgy="ASTM A216 WCB",
            facing_end="RF",
            is_sour_service=True
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_2_SUBSTITUTE
        assert res.is_compatible is True
        assert any(p.parameter == "Sour Service (NACE MR0175)" and p.status == "UPGRADE" for p in res.parameter_checks)


class TestLargeFlangeSeriesRules:
    """ASME B16.47 Series A vs Series B Large Flange Tests (NPS 26-60)."""

    def test_series_a_parity_tier1(self):
        source = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=700.0, # 28"
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RF",
            flange_series="SERIES_A"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=700.0,
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RF",
            flange_series="SERIES_A"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_1_IDENTICAL
        assert res.is_compatible is True

    def test_series_a_vs_series_b_mismatch_fatal_tier3(self):
        # Series A (MSS SP-44) and Series B (API 605) have different bolt circles and hole counts
        source = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=700.0,
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RF",
            flange_series="SERIES_A"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=700.0,
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RF",
            flange_series="SERIES_B"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert res.is_compatible is False
        assert any(v.field == "flange_series" for v in res.violations)


class TestGasketAndFastenerRules:
    """ASME B16.20 Gaskets and ASTM A193/A194 Fasteners."""

    def test_gasket_graphite_filler_exact(self):
        source = ExtractedMaterialAttributes(
            item_type="SPIRAL_WOUND_GASKET",
            size_nb_mm=100.0,
            pressure_class=300,
            gasket_type="SPIRAL_WOUND",
            gasket_filler="GRAPHITE"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="SPIRAL_WOUND_GASKET",
            size_nb_mm=100.0,
            pressure_class=300,
            gasket_type="SPIRAL_WOUND",
            gasket_filler="GRAPHITE"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_1_IDENTICAL
        assert res.is_compatible is True

    def test_gasket_ptfe_filler_hazard_fatal_tier3(self):
        # Substituting graphite with PTFE in high-temp hydrocarbon service is a fire/creep hazard
        source = ExtractedMaterialAttributes(
            item_type="SPIRAL_WOUND_GASKET",
            size_nb_mm=100.0,
            pressure_class=300,
            gasket_type="SPIRAL_WOUND",
            gasket_filler="GRAPHITE"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="SPIRAL_WOUND_GASKET",
            size_nb_mm=100.0,
            pressure_class=300,
            gasket_type="SPIRAL_WOUND",
            gasket_filler="PTFE"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert res.is_compatible is False
        assert any(v.field == "gasket_filler" for v in res.violations)

    def test_cryogenic_fastener_downgrade_fatal_tier3(self):
        # Substituting L7 (Charpy tested at -101°C) with standard B7 risks brittle fracture
        source = ExtractedMaterialAttributes(
            item_type="STUD_BOLT",
            size_nb_mm=25.0,
            bolt_grade="ASTM A320 L7"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="STUD_BOLT",
            size_nb_mm=25.0,
            bolt_grade="ASTM A193 B7"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert res.is_compatible is False
        assert any(v.field == "bolt_grade" for v in res.violations)

    def test_fastener_cryogenic_upgrade_tier2(self):
        # B7 to L7 is a valid impact toughness upgrade
        source = ExtractedMaterialAttributes(
            item_type="STUD_BOLT",
            size_nb_mm=25.0,
            bolt_grade="ASTM A193 B7"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="STUD_BOLT",
            size_nb_mm=25.0,
            bolt_grade="ASTM A320 L7"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_2_SUBSTITUTE
        assert res.is_compatible is True


class TestNERAttributeExtractionDomainExpansion:
    """Tests that raw procurement text strings extract the new domain attributes."""

    def test_extract_schedule(self):
        attrs = extract_attributes("PIPE SMLS 4IN SCH 80 ASTM A106 GR B BW")
        assert attrs.item_type == "PIPE_SEAMLESS"
        assert attrs.schedule == "SCH 80"
        assert attrs.size_nb_mm == 100.0

    def test_extract_sour_service(self):
        attrs = extract_attributes("GATE VALVE 2IN 300# WCB RF NACE MR0175 SOUR SERVICE")
        assert attrs.item_type == "GATE_VALVE"
        assert attrs.is_sour_service is True
        assert attrs.pressure_class == 300

    def test_extract_large_flange_series(self):
        attrs = extract_attributes("FLANGE WN 28IN 300# A105 RF ASME B16.47 SERIES A")
        assert attrs.item_type == "FLANGE_WELD_NECK"
        assert attrs.flange_series == "SERIES_A"
        assert attrs.standard == "ASME B16.47"

    def test_extract_gasket_filler(self):
        attrs = extract_attributes("GASKET SPIRAL WOUND 4IN 300# SS316 GRAPHITE FILLER ASME B16.20")
        assert attrs.item_type == "SPIRAL_WOUND_GASKET"
        assert attrs.gasket_type == "SPIRAL_WOUND"
        assert attrs.gasket_filler == "GRAPHITE"

    def test_extract_fasteners(self):
        attrs = extract_attributes("STUD BOLT 1IN X 150MM ASTM A320 L7 WITH 2 HEAVY HEX NUTS A194 7")
        assert attrs.item_type == "STUD_BOLT"
        assert attrs.bolt_grade == "ASTM A320 L7"
        assert attrs.nut_grade == "ASTM A194 7"
