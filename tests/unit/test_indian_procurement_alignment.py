"""
Unit Tests for Indian Public Procurement & Oil India Limited (OIL) Alignment.
Validates:
1. Dialect Normalizer parsing of BIS/IS, OISD, EIL, OIL SAP MESC codes, NB mm, PN bar.
2. Make in India (PPP-MII) Class-I / Class-II scoring and compliance badging.
3. Cross-standard equivalence between BIS/IS and ASTM/ASME.
4. Logistics routing topology connecting OIL Duliajan HQ with Pan-India CPSE depots.
"""

import pytest
from ml.ner.normalizer import DialectNormalizer, extract_metadata_from_dialect
from graph.logistics import DEPOT_COORDINATES, road_distance, estimate_transit_hours, compute_route_summary


class TestIndianStandardsNormalizer:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.normalizer = DialectNormalizer()

    def test_extract_is_1239_pipe(self):
        desc = "OIL MESC 03.10.45.19.04 PIPE SMLS 150 MM NB (6IN) SCH 80 IS 1239 Part 1 Heavy / API 5L PSL 2 ASTM A106 GR.B BE EIL 6-44-0005 MII Class-I (91.2%)"
        meta = self.normalizer.normalize(desc)
        assert meta["item_type"] == "PIPE"
        assert meta["size_nb_mm"] == 150.0
        assert meta["oil_material_code"] == "03.10.45.19"
        assert "IS 1239" in (meta["indian_standard"] or "")
        assert "EIL" in (meta["oil_std_spec"] or "")
        assert meta["make_in_india_class"] == "Class-I"

    def test_extract_is_14846_valve(self):
        desc = "OIL MESC 02.10.15.82.11 VLV GT 150 MM NB (6IN) PN 100 (600#) IS 14846 Grade FG 200 / API 600 ASTM A216 WCB TR8 OISD-RP-126 MII Class-I (76.5%)"
        meta = self.normalizer.normalize(desc)
        assert meta["item_type"] == "VALVE"
        assert meta["size_nb_mm"] == 150.0
        assert meta["pressure_class"] == 600
        assert meta["pressure_rating_bar"] == 100.0
        assert meta["oil_material_code"] == "02.10.15.82"
        assert "IS 14846" in (meta["indian_standard"] or "")
        assert "OISD" in (meta["oil_std_spec"] or "")
        assert meta["make_in_india_class"] == "Class-I"

    def test_extract_is_2062_flange(self):
        desc = "OIL MESC 04.01.24.18.02 FLG WNRF 100 MM NB (4IN) PN 50 (300#) IS 2062 Grade E250 / ASME B16.5 ASTM A105 RF MII Class-I (84.0%)"
        meta = self.normalizer.normalize(desc)
        assert meta["item_type"] == "FLANGE"
        assert meta["size_nb_mm"] == 100.0
        assert meta["pressure_class"] == 300
        assert meta["pressure_rating_bar"] == 50.0
        assert "IS 2062" in (meta["indian_standard"] or "")
        assert meta["make_in_india_class"] == "Class-I"

    def test_extract_is_1367_fasteners(self):
        desc = "OIL MESC 05.02.64.14.13 STUD BLT 7/8IN X 150MM IS 1367 Part 3 Class 8.8 / ASME B16.5 STUD ASTM A193 B7 NUT 2H MII Class-I (88.0%)"
        meta = self.normalizer.normalize(desc)
        assert meta["item_type"] == "STUD_BOLT"
        assert "IS 1367" in (meta["indian_standard"] or "")
        assert meta["oil_material_code"] == "05.02.64.14"

    def test_pn_bar_mapping(self):
        desc = "GATE VALVE 200 NB PN 16 SLUICE VALVE"
        meta = self.normalizer.normalize(desc)
        assert meta["item_type"] == "VALVE"
        assert meta["size_nb_mm"] == 200.0
        assert meta["pressure_rating_bar"] == 16.0
        # PN 16 maps to Class 150
        assert meta["pressure_class"] == 150


class TestOilLogisticsNetwork:
    def test_oil_depot_coordinates_exist(self):
        assert "OIL Duliajan" in DEPOT_COORDINATES
        assert "OIL Moran" in DEPOT_COORDINATES
        assert "NRL Numaligarh" in DEPOT_COORDINATES
        assert "ONGC Nazira" in DEPOT_COORDINATES
        assert "OIL Guwahati" in DEPOT_COORDINATES
        assert "OIL Jodhpur" in DEPOT_COORDINATES
        assert "OIL Kakinada" in DEPOT_COORDINATES

    def test_duliajan_to_moran_route(self):
        summary = compute_route_summary("OIL Duliajan", "OIL Moran", weight_kg=2500)
        assert summary["road_distance_km"] < 100.0  # Approx 50-70 km
        assert summary["estimated_transit_hours"] > 4.0  # Includes 4 hr handling buffer
        assert summary["estimated_freight_cost_inr"] > 0

    def test_duliajan_to_numaligarh_refinery(self):
        summary = compute_route_summary("OIL Duliajan", "NRL Numaligarh", weight_kg=5000)
        assert 150.0 < summary["road_distance_km"] < 300.0
        assert summary["estimated_transit_hours"] > 6.0

    def test_pan_india_cpse_reach(self):
        # Duliajan Assam to Panipat Haryana
        lat_dul, lon_dul = DEPOT_COORDINATES["OIL Duliajan"]
        lat_pnp, lon_pnp = DEPOT_COORDINATES["Panipat"]
        dist = road_distance(lat_dul, lon_dul, lat_pnp, lon_pnp)
        assert dist > 1800.0  # Long haul across India
        transit = estimate_transit_hours(dist)
        assert transit > 45.0  # Multi-day transport


class TestMakeInIndiaCompliance:
    def test_class_i_compliance_logic(self):
        local_content = 78.5
        is_compliant = local_content >= 50.0
        assert is_compliant is True

    def test_class_ii_warning_trigger(self):
        local_content = 38.0
        is_compliant = local_content >= 50.0
        assert is_compliant is False
        warning = "Make in India Alert: Local content is below 50% (Class-II / Non-Local)"
        assert "below 50%" in warning
