"""
Tests for Prompt 2 improvements to Samanvay-AI.

Covers:
  Task 1 — Depot coordinate deduplication in get_nearest_depots
  Task 2 — compute_co2_saved_per_tonne semantics, units, and deprecation alias
  Task 3 — Rejection of default Neo4j password in production
  Task 4 — extract_item_type word-boundary regex and real CSV descriptions
  Task 5 — Driver configuration arguments passed correctly
  Task 6 — Orphaned PurchaseOrder and CPPPTender cleanup in delete_inventory_item

All tests run with mocks only. No live Neo4j database is required.
"""

from __future__ import annotations

import warnings
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Task 1 — Depot coordinate deduplication
# ---------------------------------------------------------------------------
from graph.logistics import (
    DEPOT_COORDINATES,
    _coord_key,
    _COORD_ROUND_DIGITS,
    compute_co2_saved_per_tonne,
    compute_co2_saved,
    get_nearest_depots,
    haversine_distance,
    road_distance,
    compute_route_summary,
)
from graph.seed_graph import extract_item_type


class TestDepotDeduplication:
    """Task 1: get_nearest_depots must not return duplicate physical locations."""

    def test_no_duplicate_physical_locations_in_results(self):
        """All aliases of OIL Duliajan share the same coords; only one must appear."""
        results = get_nearest_depots("OIL Duliajan", top_n=20)
        seen_keys = set()
        for r in results:
            lat, lon = DEPOT_COORDINATES[r["depot_id"]]
            key = _coord_key(lat, lon)
            assert key not in seen_keys, (
                f"Duplicate coordinate key {key!r} found for depot_id={r['depot_id']!r}"
            )
            seen_keys.add(key)

    def test_origin_depot_excluded_from_results(self):
        """The origin depot (and its aliases) must never appear in the result list."""
        origin = "OIL Duliajan"
        olat, olon = DEPOT_COORDINATES[origin]
        origin_key = _coord_key(olat, olon)
        results = get_nearest_depots(origin, top_n=20)
        for r in results:
            lat, lon = DEPOT_COORDINATES[r["depot_id"]]
            assert _coord_key(lat, lon) != origin_key, (
                f"Origin key {origin_key!r} appeared in results as {r['depot_id']!r}"
            )

    def test_nearby_distinct_coordinates_both_appear(self):
        """Two depots with different rounded coords must both appear in results."""
        # OIL Digboi (27.3826, 95.6262) and "Digboi" (27.3834, 95.6228) differ
        # at 4 decimal places: keys are (27.3826, 95.6262) vs (27.3834, 95.6228).
        key_a = _coord_key(27.3826, 95.6262)
        key_b = _coord_key(27.3834, 95.6228)
        assert key_a != key_b, "Test precondition: keys must differ"

        results = get_nearest_depots("OIL Duliajan", top_n=30)
        depot_ids = [r["depot_id"] for r in results]
        # Both the OIL Digboi entry and the plain "Digboi" entry represent
        # different coords, so at least one from each key group must be present
        keys_in_results = set()
        for r in results:
            lat, lon = DEPOT_COORDINATES[r["depot_id"]]
            keys_in_results.add(_coord_key(lat, lon))
        assert key_a in keys_in_results, "OIL Digboi coordinate not found in results"
        assert key_b in keys_in_results, "Digboi coordinate not found in results"

    def test_results_sorted_ascending_by_distance(self):
        """Returned depots must be in ascending distance order."""
        results = get_nearest_depots("OIL Moran", top_n=10)
        distances = [r["distance_km"] for r in results]
        assert distances == sorted(distances), "Results not sorted by distance"

    def test_top_n_respected(self):
        """At most top_n results returned."""
        for n in [1, 3, 5]:
            results = get_nearest_depots("OIL Jorhat", top_n=n)
            assert len(results) <= n

    def test_unknown_depot_returns_empty(self):
        """Unknown depot_id returns []."""
        assert get_nearest_depots("COMPLETELY_UNKNOWN_DEPOT_XYZ") == []

    def test_deterministic_tie_breaking(self):
        """Calling get_nearest_depots twice gives identical results."""
        r1 = get_nearest_depots("Panipat", top_n=5)
        r2 = get_nearest_depots("Panipat", top_n=5)
        assert r1 == r2

    def test_coord_key_precision(self):
        """_coord_key uses _COORD_ROUND_DIGITS rounding."""
        lat, lon = 27.35751, 95.31884
        key = _coord_key(lat, lon)
        assert key == (round(lat, _COORD_ROUND_DIGITS), round(lon, _COORD_ROUND_DIGITS))

    def test_alias_entries_share_same_key(self):
        """All three Duliajan alias entries round to the same key."""
        coords = [
            DEPOT_COORDINATES["OIL Duliajan"],
            DEPOT_COORDINATES["Duliajan"],
            DEPOT_COORDINATES["OIL Central Materials Warehouse, Duliajan, Assam"],
        ]
        keys = [_coord_key(*c) for c in coords]
        assert len(set(keys)) == 1, "All Duliajan aliases must share the same coord key"


# ---------------------------------------------------------------------------
# Task 2 — CO₂ calculation semantics
# ---------------------------------------------------------------------------
class TestCO2Savings:
    """Task 2: compute_co2_saved_per_tonne units, formula, edge cases."""

    def test_zero_distance_returns_max_savings(self):
        """At 0 km road distance the full saving (100 kg/t) is returned."""
        result = compute_co2_saved_per_tonne(0.0)
        # (10_000 * 10 - 0 * 60) / 1000 = 100.0
        assert result == pytest.approx(100.0)

    def test_known_calculation_500km(self):
        """500 km domestic road trip: (100_000 - 30_000) / 1000 = 70.0 kg CO₂/t."""
        result = compute_co2_saved_per_tonne(500.0)
        expected = max(0.0, (10_000.0 * 10.0) - (500.0 * 60.0)) / 1000.0
        assert result == pytest.approx(expected)
        assert result == pytest.approx(70.0)

    def test_known_calculation_1000km(self):
        """1 000 km trip: (100_000 - 60_000) / 1000 = 40.0 kg CO₂/t."""
        result = compute_co2_saved_per_tonne(1000.0)
        assert result == pytest.approx(40.0)

    def test_breakeven_distance_clamps_to_zero(self):
        """Beyond ~1667 km savings are negative; function clamps to 0.0."""
        # At exactly 10_000*10/60 ≈ 1666.67 km savings = 0
        result_long = compute_co2_saved_per_tonne(2000.0)
        assert result_long == pytest.approx(0.0)

    def test_very_long_distance_returns_zero_not_negative(self):
        """Extreme distance must never return a negative value."""
        result = compute_co2_saved_per_tonne(5000.0)
        assert result == 0.0

    def test_different_shipment_tonnages(self):
        """
        compute_co2_saved_per_tonne is per-tonne; callers must multiply by weight.
        Total savings for 5 tonnes at 500 km = 70.0 * 5 = 350 kg.
        """
        per_tonne = compute_co2_saved_per_tonne(500.0)
        total_5t = per_tonne * 5.0
        assert total_5t == pytest.approx(350.0)

    def test_deprecated_alias_still_works_and_warns(self):
        """compute_co2_saved is a deprecated alias; it must warn and return same value."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = compute_co2_saved(500.0)
        assert result == pytest.approx(compute_co2_saved_per_tonne(500.0))
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "compute_co2_saved_per_tonne" in str(w[0].message)

    def test_compute_route_summary_co2_uses_renamed_function(self):
        """compute_route_summary must use compute_co2_saved_per_tonne (not the alias)."""
        summary = compute_route_summary("OIL Duliajan", "Panipat", weight_kg=2000.0)
        assert "co2_saved_kg" in summary
        dist = summary["road_distance_km"]
        per_tonne = compute_co2_saved_per_tonne(dist)
        expected_total = round(per_tonne * (2000.0 / 1000.0), 2)
        assert summary["co2_saved_kg"] == pytest.approx(expected_total)


# ---------------------------------------------------------------------------
# Task 3 — Reject default Neo4j password in production
# ---------------------------------------------------------------------------
class TestNeo4jProductionPasswordPolicy:
    """Task 3: Settings must reject factory-default Neo4j password in production."""

    def test_default_password_rejected_in_production(self):
        """debug=False + password='neo4j' (factory default) → ValueError."""
        from pydantic import ValidationError
        from backend.app.core.config import Settings

        with pytest.raises((ValueError, ValidationError)):
            Settings(
                debug=False,
                neo4j_password="neo4j",
                neo4j_uri="bolt://prod-server:7687",
            )

    def test_custom_password_accepted_in_production(self):
        """debug=False + a non-default password → no error."""
        from backend.app.core.config import Settings

        s = Settings(
            debug=False,
            neo4j_password="my_strong_production_password_42",
            neo4j_uri="bolt://prod-server:7687",
        )
        assert s.neo4j_password == "my_strong_production_password_42"

    def test_default_password_allowed_in_debug_mode(self):
        """debug=True + password='neo4j' → allowed (local dev workflow)."""
        from backend.app.core.config import Settings

        s = Settings(debug=True, neo4j_password="neo4j")
        assert s.debug is True
        assert s.neo4j_password == "neo4j"

    def test_production_config_fields_accessible(self):
        """Driver reliability fields are present and have sane defaults."""
        from backend.app.core.config import Settings

        s = Settings(debug=True)
        assert s.neo4j_connection_timeout > 0
        assert s.neo4j_max_connection_lifetime > 0
        assert s.neo4j_max_connection_pool_size > 0
        assert s.neo4j_connection_acquisition_timeout > 0


# ---------------------------------------------------------------------------
# Task 4 — extract_item_type word-boundary regression tests
# ---------------------------------------------------------------------------
class TestExtractItemType:
    """Task 4: Real CSV descriptions and false-positive guards."""

    # Real descriptions from inventory_catalog.csv
    def test_stud_bolt(self):
        desc = "OIL MESC 05.02.64.14.13 STUD BLT 5/8IN X 150MM IS 1367 Part 3 Class 8.8"
        assert extract_item_type(desc) == "Stud Bolt"

    def test_ball_valve_vlv_bl(self):
        desc = "OIL MESC 02.14.23.21.58 VLV BL 500 MM NB (20IN) PN 100 (600#)"
        assert extract_item_type(desc) == "Ball Valve"

    def test_safety_relief_valve_vlv_psv(self):
        desc = "OIL MESC 02.40.20.39.22 VLV PSV 40 MM NB (1.5IN) PN 100 (600#)"
        assert extract_item_type(desc) == "Safety Relief Valve"

    def test_globe_valve_vlv_gl(self):
        desc = "OIL MESC 02.12.77.10.86 VLV GL 25 MM NB (1IN) PN 250 (1500#)"
        assert extract_item_type(desc) == "Globe Valve"

    def test_check_valve_vlv_chk(self):
        desc = "OIL MESC 02.16.14.52.19 VLV CHK 300 MM NB (12IN) PN 20 (150#)"
        assert extract_item_type(desc) == "Check Valve"

    def test_elbow_90lr_real_csv(self):
        """Real CSV: BUTTWELD FITTING, ELBOW 90 DEG LONG RADIUS"""
        desc = (
            "BUTTWELD FITTING, ELBOW 90 DEG LONG RADIUS, 4 INCH, SCH 80, "
            "ASTM A420 WPL6, IS 1239 Part 2 / IS 2062, ASME B16.9"
        )
        assert extract_item_type(desc) == "Elbow"

    def test_elbow_elb_abbreviation(self):
        desc = "OIL MESC 04.20.64.37.79 ELB 90 LR 200 MM NB (8IN) SCH 40"
        assert extract_item_type(desc) == "Elbow"

    def test_reducer_conc(self):
        desc = "OIL MESC 04.20.24.97.78 RED CONC 15 MM NB (1/2IN) SCH 160"
        assert extract_item_type(desc) == "Reducer"

    def test_tee_eq(self):
        desc = "OIL MESC 04.20.25.82.41 TEE EQ 40 MM NB (1.5IN) SCH 40"
        assert extract_item_type(desc) == "Tee"

    def test_spiral_wound_gasket(self):
        desc = "OIL MESC 04.35.89.82.22 GSKT SWG 80 MM NB (3IN) PN 20 (150#)"
        assert extract_item_type(desc) == "Spiral Wound Gasket"

    def test_weld_neck_flange_rtj(self):
        desc = "OIL MESC 04.01.30.66.80 FLG WN-RTJ 300 MM NB (12IN) PN 100 (600#)"
        assert extract_item_type(desc) == "Weld Neck Flange"

    def test_seamless_pipe(self):
        desc = "OIL MESC 03.10.94.72.29 PIPE SMLS 500 MM NB (20IN) SCH 160"
        assert extract_item_type(desc) == "Seamless Pipe"

    def test_pump_shaft_sleeve(self):
        desc = "OIL MESC 06.10.84.64.84 PUMP SHAFT SLEEVE 50 MM NB (2IN)"
        assert extract_item_type(desc) == "Pump Shaft Sleeve"

    def test_gate_valve_long_desc(self):
        desc = "High Pressure Gate Valve 100mm 20 bar WCB"
        assert extract_item_type(desc) == "Gate Valve"

    # False-positive guards
    def test_no_false_positive_cap_in_capacity(self):
        """'CAPACITY' must not trigger Cap classification."""
        desc = "PUMP WITH CAPACITY 500 LPM AND FLOW FITTING"
        # Should NOT return Cap (no standalone CAP + FITTING)
        result = extract_item_type(desc)
        assert result != "Cap"

    def test_no_false_positive_ring_in_spring(self):
        """'SPRING' must not trigger Ring classification."""
        desc = "COIL SPRING ASSEMBLY FOR VALVE ACTUATOR"
        result = extract_item_type(desc)
        assert result != "Ring"

    def test_no_false_positive_tee_in_steel(self):
        """'STEEL' must not trigger Tee classification."""
        desc = "STAINLESS STEEL PIPE 50 MM SCH 40"
        result = extract_item_type(desc)
        assert result != "Tee"
        assert result == "Pipe"

    def test_no_false_positive_nip_in_unrelated(self):
        """Short 'NIP' token should only match at word boundary."""
        # Description that contains NIP as part of longer words or unrelated context
        desc = "NIPPLE CONNECTOR 25MM THREADED END"
        assert extract_item_type(desc) == "Nipple"

    def test_buttweld_fitting_elbow_desc(self):
        """Specific: buttweld fitting with elbow — ELBOW fires before generic fitting."""
        desc = "BUTTWELD FITTING ELBOW 90 DEG LR 6 INCH SCH 40 ASTM A234 WPB"
        assert extract_item_type(desc) == "Elbow"

    def test_generic_valve_fallback(self):
        """Unrecognized valve description falls through to generic Valve."""
        desc = "ROTARY VALVE 50MM SPECIAL DESIGN"
        assert extract_item_type(desc) == "Valve"

    def test_empty_string_returns_general_material(self):
        assert extract_item_type("") == "General Material"

    def test_none_returns_general_material(self):
        assert extract_item_type(None) == "General Material"

    def test_completely_unrecognized_returns_general_material(self):
        desc = "SOME COMPLETELY UNKNOWN ITEM WITH NO KEYWORDS"
        assert extract_item_type(desc) == "General Material"

    def test_punctuation_variants_elbow(self):
        """Comma and slash punctuation in real descriptions must not break matching."""
        desc = "FITTING, ELBOW, 90 DEG / 2 INCH / SCH 80"
        assert extract_item_type(desc) == "Elbow"


# ---------------------------------------------------------------------------
# Task 5 — Driver configuration arguments
# ---------------------------------------------------------------------------
class TestDriverConfiguration:
    """Task 5: Driver must be constructed with reliability settings from config."""

    def test_queries_driver_receives_reliability_kwargs(self):
        """GraphQuerier must pass connection pool settings to GraphDatabase.driver."""
        from backend.app.core.config import Settings

        mock_settings = Settings(
            debug=True,
            neo4j_password="test_pass",
            neo4j_connection_timeout=30,
            neo4j_max_connection_lifetime=1800,
            neo4j_max_connection_pool_size=25,
            neo4j_connection_acquisition_timeout=45,
        )

        mock_driver = MagicMock()

        with (
            patch("graph.queries.NEO4J_AVAILABLE", True),
            patch("graph.queries.GraphDatabase") as mock_gdb,
            patch("graph.queries._get_neo4j_config") as mock_cfg,
        ):
            mock_gdb.driver.return_value = mock_driver
            mock_cfg.return_value = (
                "bolt://localhost:7687",
                "neo4j",
                "test_pass",
                {
                    "connection_timeout": 30,
                    "max_connection_lifetime": 1800,
                    "max_connection_pool_size": 25,
                    "connection_acquisition_timeout": 45,
                },
            )
            from graph.queries import GraphQuerier
            q = GraphQuerier(requesting_cpse="OIL")

        mock_gdb.driver.assert_called_once_with(
            "bolt://localhost:7687",
            auth=("neo4j", "test_pass"),
            connection_timeout=30,
            max_connection_lifetime=1800,
            max_connection_pool_size=25,
            connection_acquisition_timeout=45,
        )

    def test_syncer_driver_receives_reliability_kwargs(self):
        """Neo4jSyncer must pass connection pool settings to GraphDatabase.driver."""
        mock_driver = MagicMock()

        with (
            patch("graph.syncer.GraphDatabase") as mock_gdb,
            patch("graph.syncer._get_neo4j_config") as mock_cfg,
        ):
            mock_gdb.driver.return_value = mock_driver
            mock_cfg.return_value = (
                "bolt://localhost:7687",
                "neo4j",
                "test_pass",
                {
                    "connection_timeout": 15,
                    "max_connection_lifetime": 3600,
                    "max_connection_pool_size": 50,
                    "connection_acquisition_timeout": 60,
                },
            )
            from graph.syncer import Neo4jSyncer
            s = Neo4jSyncer()

        mock_gdb.driver.assert_called_once_with(
            "bolt://localhost:7687",
            auth=("neo4j", "test_pass"),
            connection_timeout=15,
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=60,
        )

    def test_config_has_all_driver_reliability_fields(self):
        """All four driver reliability settings are accessible on Settings."""
        from backend.app.core.config import Settings
        s = Settings(debug=True)
        assert hasattr(s, "neo4j_connection_timeout")
        assert hasattr(s, "neo4j_max_connection_lifetime")
        assert hasattr(s, "neo4j_max_connection_pool_size")
        assert hasattr(s, "neo4j_connection_acquisition_timeout")


# ---------------------------------------------------------------------------
# Task 6 — Orphaned PO and Tender cleanup
# ---------------------------------------------------------------------------
class TestOrphanedPOAndTenderCleanup:
    """Task 6: delete_inventory_item must safely clean up orphaned POs and Tenders."""

    def _make_syncer_with_mock_driver(self):
        """Returns (Neo4jSyncer instance, mock_session)."""
        from graph.syncer import Neo4jSyncer

        syncer = object.__new__(Neo4jSyncer)  # bypass __init__ / driver init
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        syncer.driver = mock_driver
        return syncer, mock_session

    def test_delete_inventory_item_calls_cleanup_query(self):
        """delete_inventory_item must execute a single Cypher query via session."""
        syncer, mock_session = self._make_syncer_with_mock_driver()
        syncer.delete_inventory_item("OIL-VLV-001")

        mock_session.run.assert_called_once()
        cypher_call_args = mock_session.run.call_args
        query_str = cypher_call_args[0][0]  # first positional arg = query string
        # Verify key structural keywords are present
        assert "ORDERED_BY" in query_str
        assert "PART_OF_TENDER" in query_str
        assert "DETACH DELETE" in query_str
        assert "still_referenced" in query_str or "count(" in query_str.lower()

    def test_sync_event_delete_calls_delete_inventory_item(self):
        """sync_event with DELETE for inventory_items delegates to delete_inventory_item."""
        from graph.syncer import Neo4jSyncer

        syncer = object.__new__(Neo4jSyncer)
        syncer.delete_inventory_item = MagicMock()

        syncer.sync_event(
            table_name="inventory_items",
            operation="DELETE",
            payload={"sku_code": "OIL-VLV-001"},
        )
        syncer.delete_inventory_item.assert_called_once_with("OIL-VLV-001")

    def test_sync_event_delete_with_missing_sku_does_nothing(self):
        """sync_event with DELETE and no sku_code must not call delete_inventory_item."""
        from graph.syncer import Neo4jSyncer

        syncer = object.__new__(Neo4jSyncer)
        syncer.delete_inventory_item = MagicMock()

        syncer.sync_event(
            table_name="inventory_items",
            operation="DELETE",
            payload={},  # no sku_code
        )
        syncer.delete_inventory_item.assert_not_called()

    def test_delete_query_contains_orphan_protection_logic(self):
        """The Cypher query must check remaining references before deleting PO/Tender."""
        syncer, mock_session = self._make_syncer_with_mock_driver()
        syncer.delete_inventory_item("TEST-SKU-999")

        query_str = mock_session.run.call_args[0][0]
        # PO deletion must be conditional on no remaining references
        assert "still_referenced" in query_str or "count(other_item)" in query_str
        # Tender deletion must be conditional on no remaining PO references
        assert "po_count" in query_str or "count(remaining_po)" in query_str

    def test_sku_code_passed_as_parameter_not_interpolated(self):
        """SKU code must be passed as a Cypher parameter, not string-interpolated."""
        syncer, mock_session = self._make_syncer_with_mock_driver()
        syncer.delete_inventory_item("INJECTION-SKU'; DROP DATABASE neo4j")

        call_kwargs = mock_session.run.call_args[1]
        call_args = mock_session.run.call_args[0]
        # sku_code should appear as a parameter, not inside the query string
        # Either as keyword arg or dict param
        all_params = dict(call_kwargs)
        if len(call_args) > 1:
            all_params.update(call_args[1] if isinstance(call_args[1], dict) else {})
        assert any("INJECTION-SKU" in str(v) for v in all_params.values()), (
            "sku_code must be passed as a Cypher parameter value"
        )
        # Verify it's NOT in the query string itself
        query_str = call_args[0]
        assert "INJECTION-SKU" not in query_str
