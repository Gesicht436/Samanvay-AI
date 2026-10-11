"""
Unit tests for Prompt 3 maintainability improvements:
1. Consolidated Neo4j configuration across callers and production validation failure.
2. Immutable depot coordinates registry and logistics compatibility.
3. Safe partial updates in Neo4jSyncer (omitted fields, None, valid updates, CLEAR sentinel, clear_fields).
4. Table-driven item-type parameterized tests and dataset-wide classification validation.
"""

from __future__ import annotations

import csv
from pathlib import Path
from types import MappingProxyType
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from backend.app.core.config import Settings, get_neo4j_config
from graph.logistics import (
    DEPOT_COORDINATES,
    get_nearest_depots,
    haversine_distance,
    road_distance,
    compute_route_summary,
)
from graph.seed_graph import GraphSeeder, extract_item_type
from graph.syncer import CLEAR, Neo4jSyncer


# ===========================================================================
# 1. CONSOLIDATED NEO4J CONFIGURATION TESTS
# ===========================================================================

class TestConsolidatedNeo4jConfig:
    """Verifies that Neo4j configuration is consolidated into backend.app.core.config."""

    def test_shared_get_neo4j_config_returns_expected_tuple(self):
        """get_neo4j_config must return (uri, user, password, driver_kwargs) without credentials in kwargs."""
        s = Settings(
            debug=True,
            neo4j_uri="bolt://test-cluster:7687",
            neo4j_user="test_admin",
            neo4j_password="secure_password_123",
            neo4j_connection_timeout=20,
            neo4j_max_connection_lifetime=1800,
            neo4j_max_connection_pool_size=30,
            neo4j_connection_acquisition_timeout=50,
        )
        uri, user, password, kwargs = get_neo4j_config(s)

        assert uri == "bolt://test-cluster:7687"
        assert user == "test_admin"
        assert password == "secure_password_123"
        assert kwargs == {
            "connection_timeout": 20,
            "max_connection_lifetime": 1800,
            "max_connection_pool_size": 30,
            "connection_acquisition_timeout": 50,
        }
        # Credentials must never leak into driver_kwargs
        assert "password" not in kwargs
        assert "user" not in kwargs
        assert "uri" not in kwargs

    def test_shared_get_neo4j_config_defaults_to_app_settings(self):
        """Omitting settings_obj parameter uses the application settings singleton."""
        uri, user, password, kwargs = get_neo4j_config()
        assert uri.startswith("bolt://") or uri.startswith("neo4j://")
        assert isinstance(user, str)
        assert isinstance(password, str)
        assert "connection_timeout" in kwargs
        assert "max_connection_pool_size" in kwargs

    def test_invalid_production_password_fails_clearly(self):
        """In production (debug=False), factory default password 'neo4j' must raise ValueError."""
        with pytest.raises(ValueError, match="Insecure Neo4j configuration"):
            Settings(
                debug=False,
                neo4j_password="neo4j",
                neo4j_uri="bolt://prod:7687",
            )

    def test_graph_querier_uses_shared_config(self):
        """GraphQuerier must retrieve its configuration via get_neo4j_config."""
        mock_driver = MagicMock()
        mock_tuple = (
            "bolt://shared-host:7687",
            "neo4j_user",
            "shared_pass",
            {"connection_timeout": 15, "max_connection_lifetime": 3600, "max_connection_pool_size": 50, "connection_acquisition_timeout": 60},
        )

        with (
            patch("graph.queries.NEO4J_AVAILABLE", True),
            patch("graph.queries.GraphDatabase") as mock_gdb,
            patch("graph.queries.get_neo4j_config", return_value=mock_tuple) as mock_cfg,
        ):
            mock_gdb.driver.return_value = mock_driver
            from graph.queries import GraphQuerier

            q = GraphQuerier(requesting_cpse="OIL")
            mock_cfg.assert_called_once()
            mock_gdb.driver.assert_called_once_with(
                "bolt://shared-host:7687",
                auth=("neo4j_user", "shared_pass"),
                connection_timeout=15,
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60,
            )

    def test_neo4j_syncer_uses_shared_config(self):
        """Neo4jSyncer must retrieve its configuration via get_neo4j_config."""
        mock_driver = MagicMock()
        mock_tuple = (
            "bolt://syncer-host:7687",
            "syncer_user",
            "syncer_pass",
            {"connection_timeout": 25, "max_connection_lifetime": 2000, "max_connection_pool_size": 40, "connection_acquisition_timeout": 50},
        )

        with (
            patch("graph.syncer.GraphDatabase") as mock_gdb,
            patch("graph.syncer.get_neo4j_config", return_value=mock_tuple) as mock_cfg,
        ):
            mock_gdb.driver.return_value = mock_driver
            s = Neo4jSyncer()
            mock_cfg.assert_called_once()
            mock_gdb.driver.assert_called_once_with(
                "bolt://syncer-host:7687",
                auth=("syncer_user", "syncer_pass"),
                connection_timeout=25,
                max_connection_lifetime=2000,
                max_connection_pool_size=40,
                connection_acquisition_timeout=50,
            )

    def test_graph_seeder_uses_shared_config(self):
        """GraphSeeder must retrieve its configuration via get_neo4j_config."""
        mock_driver = MagicMock()
        mock_tuple = (
            "bolt://seeder-host:7687",
            "seeder_user",
            "seeder_pass",
            {"connection_timeout": 10, "max_connection_lifetime": 1000, "max_connection_pool_size": 20, "connection_acquisition_timeout": 30},
        )

        with (
            patch("graph.seed_graph.GraphDatabase") as mock_gdb,
            patch("graph.seed_graph.get_neo4j_config", return_value=mock_tuple) as mock_cfg,
        ):
            mock_gdb.driver.return_value = mock_driver
            seeder = GraphSeeder()
            mock_cfg.assert_called_once()
            mock_gdb.driver.assert_called_once_with(
                "bolt://seeder-host:7687",
                auth=("seeder_user", "seeder_pass"),
                connection_timeout=10,
                max_connection_lifetime=1000,
                max_connection_pool_size=20,
                connection_acquisition_timeout=30,
            )


# ===========================================================================
# 2. IMMUTABLE DEPOT COORDINATES TESTS
# ===========================================================================

class TestImmutableDepotCoordinates:
    """Verifies that DEPOT_COORDINATES is strictly immutable while remaining fully compatible."""

    def test_depot_coordinates_is_mapping_proxy(self):
        """DEPOT_COORDINATES must be an instance of MappingProxyType."""
        assert isinstance(DEPOT_COORDINATES, MappingProxyType)

    def test_cannot_assign_new_depot(self):
        """Callers must not be able to insert new depot entries."""
        with pytest.raises(TypeError):
            DEPOT_COORDINATES["New Depot"] = (25.0, 80.0)  # type: ignore[index]

    def test_cannot_mutate_existing_depot(self):
        """Callers must not be able to modify existing depot coordinates."""
        with pytest.raises(TypeError):
            DEPOT_COORDINATES["Duliajan"] = (0.0, 0.0)  # type: ignore[index]

    def test_cannot_delete_depot(self):
        """Callers must not be able to delete depot entries."""
        with pytest.raises(TypeError):
            del DEPOT_COORDINATES["Duliajan"]  # type: ignore[misc]

    def test_cannot_clear_registry(self):
        """Calling mutating methods like clear() must fail."""
        with pytest.raises(AttributeError):
            DEPOT_COORDINATES.clear()  # type: ignore[attr-defined]

    def test_cannot_pop_entry(self):
        """Calling pop() must fail on MappingProxyType."""
        with pytest.raises(AttributeError):
            DEPOT_COORDINATES.pop("Duliajan")  # type: ignore[attr-defined]

    def test_cannot_mutate_nested_coordinates(self):
        """Nested coordinate tuples must be immutable tuples, preventing in-place alteration."""
        coord = DEPOT_COORDINATES["Duliajan"]
        assert isinstance(coord, tuple)
        assert len(coord) == 2
        with pytest.raises(TypeError):
            coord[0] = 99.0  # type: ignore[index]

    def test_nearest_depots_still_works_with_immutable_registry(self):
        """get_nearest_depots must function identically and return sorted nearest depots."""
        nearest = get_nearest_depots("Duliajan", top_n=3)
        assert len(nearest) == 3
        # First entry should be the closest neighbour (e.g. Digboi or Moran)
        assert all("depot_id" in d and "distance_km" in d for d in nearest)
        # Distances must be sorted ascending
        distances = [d["distance_km"] for d in nearest]
        assert distances == sorted(distances)

    def test_route_summary_still_works(self):
        """compute_route_summary must compute valid distances between depots in the registry."""
        summary = compute_route_summary("Duliajan", "Panipat", weight_kg=2000.0)
        assert summary["source"] == "Duliajan"
        assert summary["target"] == "Panipat"
        assert summary["road_distance_km"] > 1000.0
        assert summary["estimated_transit_hours"] > 0.0
        assert summary["estimated_freight_cost_inr"] > 0.0
        assert summary["co2_saved_kg"] >= 0.0

    def test_distance_calculations_still_work(self):
        """Direct haversine and road distance calculations with registry coordinates."""
        lat1, lon1 = DEPOT_COORDINATES["OIL Duliajan"]
        lat2, lon2 = DEPOT_COORDINATES["OIL Moran"]
        hav = haversine_distance(lat1, lon1, lat2, lon2)
        road = road_distance(lat1, lon1, lat2, lon2)
        assert hav > 0.0
        assert road > hav


# ===========================================================================
# 3. SAFE PARTIAL UPDATES TESTS
# ===========================================================================

class TestSafePartialUpdates:
    """Verifies update_item partial update semantics (omitted, None, CLEAR, clear_fields)."""

    def _create_mock_syncer(self):
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch("graph.syncer.GraphDatabase.driver", return_value=mock_driver):
            syncer = Neo4jSyncer(uri="bolt://test:7687", user="u", password="p")
        return syncer, mock_session

    def test_omitted_fields_leave_properties_unchanged(self):
        """When fields are omitted, the Cypher query must NOT contain SET or REMOVE for them."""
        syncer, mock_session = self._create_mock_syncer()
        mock_result = MagicMock()
        mock_result.single.return_value = {
            "item": {"sku_code": "OIL-TEST-1", "heat_no": "EXISTING_HEAT"},
            "stock": {"quantity": 100, "days_idle": 75},
        }
        mock_session.run.return_value = mock_result

        # Update only days_idle; all other fields omitted
        res = syncer.update_item("OIL-TEST-1", days_idle=75)

        executed_query, executed_params = mock_session.run.call_args[0]
        # Query must only set stock.days_idle
        assert "stock.days_idle = $set_stock_days_idle" in executed_query
        assert "item.heat_no" not in executed_query
        assert "stock.quantity" not in executed_query
        assert "REMOVE" not in executed_query
        assert executed_params["set_stock_days_idle"] == 75
        assert executed_params["sku_code"] == "OIL-TEST-1"
        assert res["item"]["heat_no"] == "EXISTING_HEAT"

    def test_explicit_none_leaves_properties_unchanged(self):
        """Passing None for a property must NOT clear or overwrite it."""
        syncer, mock_session = self._create_mock_syncer()
        mock_result = MagicMock()
        mock_result.single.return_value = {
            "item": {"sku_code": "OIL-TEST-2", "heat_no": "UNCHANGED_HEAT"},
            "stock": {"quantity": 50, "days_idle": 10},
        }
        mock_session.run.return_value = mock_result

        # Pass heat_no=None explicitly and valid quantity=50
        res = syncer.update_item("OIL-TEST-2", heat_no=None, quantity=50)

        executed_query, executed_params = mock_session.run.call_args[0]
        assert "stock.quantity = $set_stock_quantity" in executed_query
        # heat_no must NOT appear in SET or REMOVE
        assert "item.heat_no" not in executed_query
        assert "REMOVE" not in executed_query
        assert executed_params["set_stock_quantity"] == 50

    def test_valid_updates_on_both_nodes(self):
        """Updating properties across both InventoryItem and StockInfo produces expected SET clauses."""
        syncer, mock_session = self._create_mock_syncer()
        mock_result = MagicMock()
        mock_result.single.return_value = {
            "item": {"sku_code": "OIL-TEST-3", "heat_no": "NEW-HEAT-99"},
            "stock": {"quantity": 88, "unit_cost_inr": 1500.0},
        }
        mock_session.run.return_value = mock_result

        res = syncer.update_item(
            "OIL-TEST-3",
            heat_no="NEW-HEAT-99",
            quantity=88,
            unit_cost_inr=1500.0,
        )

        executed_query, executed_params = mock_session.run.call_args[0]
        assert "item.heat_no = $set_item_heat_no" in executed_query
        assert "stock.quantity = $set_stock_quantity" in executed_query
        assert "stock.unit_cost_inr = $set_stock_unit_cost_inr" in executed_query
        assert executed_params["set_item_heat_no"] == "NEW-HEAT-99"
        assert executed_params["set_stock_quantity"] == 88
        assert executed_params["set_stock_unit_cost_inr"] == 1500.0

    def test_explicit_clearing_via_clear_sentinel(self):
        """Passing CLEAR sentinel explicitly removes the property via Cypher REMOVE."""
        syncer, mock_session = self._create_mock_syncer()
        mock_result = MagicMock()
        mock_result.single.return_value = {
            "item": {"sku_code": "OIL-TEST-4"},
            "stock": {"quantity": 20},
        }
        mock_session.run.return_value = mock_result

        syncer.update_item("OIL-TEST-4", heat_no=CLEAR, quantity=20)

        executed_query, executed_params = mock_session.run.call_args[0]
        assert "REMOVE item.heat_no" in executed_query
        assert "stock.quantity = $set_stock_quantity" in executed_query

    def test_explicit_clearing_via_clear_fields(self):
        """Listing property names in clear_fields explicitly removes them via Cypher REMOVE."""
        syncer, mock_session = self._create_mock_syncer()
        mock_result = MagicMock()
        mock_result.single.return_value = {
            "item": {"sku_code": "OIL-TEST-5"},
            "stock": {"quantity": 10},
        }
        mock_session.run.return_value = mock_result

        syncer.update_item("OIL-TEST-5", clear_fields=["heat_no", "days_idle"])

        executed_query, executed_params = mock_session.run.call_args[0]
        assert "REMOVE item.heat_no" in executed_query
        assert "REMOVE stock.days_idle" in executed_query
        assert "SET" not in executed_query

    def test_no_apoc_called_in_partial_update(self):
        """Standard Cypher query must not invoke any APOC procedures."""
        syncer, mock_session = self._create_mock_syncer()
        mock_result = MagicMock()
        mock_result.single.return_value = {"item": {}, "stock": {}}
        mock_session.run.return_value = mock_result

        syncer.update_item("OIL-TEST-6", heat_no="HT-1", days_idle=5)
        executed_query, _ = mock_session.run.call_args[0]
        assert "apoc." not in executed_query.lower()

    def test_nonexistent_sku_raises_value_error(self):
        """Updating an unknown SKU must raise ValueError."""
        syncer, mock_session = self._create_mock_syncer()
        mock_result = MagicMock()
        mock_result.single.return_value = None
        mock_session.run.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            syncer.update_item("NON-EXISTENT-SKU", days_idle=10)


# ===========================================================================
# 4. TABLE-DRIVEN ITEM-TYPE TESTS & DATASET-WIDE VALIDATION
# ===========================================================================

class TestTableDrivenItemTypeExtraction:
    """Table-driven test suite for extract_item_type spanning all categories, variants, and false positives."""

    @pytest.mark.parametrize(
        ("raw_description", "expected_type"),
        [
            # ── 1. Valves ──────────────────────────────────────────
            ("OIL MESC 02.14.23.21.58 VLV BL 500 MM NB (20IN) PN 100", "Ball Valve"),
            ("BALL VALVE 2IN 150# RF FLANGED ASTM A216 WCB", "Ball Valve"),
            ("VLV-BL 50 MM NB PN 40 FLOATING BALL", "Ball Valve"),
            ("VLV GT 100 MM NB (4IN) PN 20 (150#) ASTM A216 WCB", "Gate Valve"),
            ("GATE-VALVE OS&Y RISING STEM 6 INCH 300#", "Gate Valve"),
            ("VLV GL 25 MM NB (1IN) PN 250 (1500#) GLOBE", "Globe Valve"),
            ("GLOBE-VALVE 50 MM NB CLASS 800 SW A105", "Globe Valve"),
            ("OIL MESC 02.16.14.52.19 VLV CHK 300 MM NB (12IN) PN 20", "Check Valve"),
            ("SWING CHECK-VALVE 8IN 300# FLANGED RF", "Check Valve"),
            ("OIL MESC 02.40.20.39.22 VLV PSV 40 MM NB (1.5IN) PN 100", "Safety Relief Valve"),
            ("SAFETY RELIEF VALVE ORIFICE D 1X2 INCH", "Safety Relief Valve"),
            ("RELIEF VALVE 3/4IN X 1IN 150#", "Safety Relief Valve"),
            ("VLV-BFV 200 MM NB WAFER TYPE BUTTERFLY", "Butterfly Valve"),
            ("BUTTERFLY VALVE 12IN 150# LEVER OPERATED", "Butterfly Valve"),
            ("PLUG VALVE 4IN 300# LUBRICATED REGULAR PATTERN", "Plug Valve"),
            ("VLV-PLG 50 MM NB SLEEVED PLUG", "Plug Valve"),
            ("CONTROL VALVE GLOBE 2IN WITH PNEUMATIC ACTUATOR", "Control Valve"),
            ("VLV-CTL 80 MM NB 300# LINEAR CHARACTERISTIC", "Control Valve"),
            ("NEEDLE VALVE 1/2IN NPT 6000 PSI 316SS", "Needle Valve"),
            ("VLV-NDL 1/4IN OD INTEGRAL BONNET", "Needle Valve"),
            ("GENERIC INDUSTRIAL VALVE PN 16", "Valve"),

            # ── 2. Pipe Fittings ───────────────────────────────────
            ("OIL MESC 04.20.64.37.79 ELB 90 LR 200 MM NB SCH 40", "Elbow"),
            ("ELB-90 SR 50 MM NB SCH 80 ASTM A234 WPB", "Elbow"),
            ("BUTTWELD 90 DEG ELBOW 4IN SCH 40", "Elbow"),
            ("OIL MESC 04.20.25.82.41 TEE EQ 40 MM NB SCH 40", "Tee"),
            ("TEE-EQ 100 MM NB SCH 80 ASTM A234 WPB", "Tee"),
            ("REDUCING TEE 6IN X 4IN SCH 40 BW", "Tee"),
            ("OIL MESC 04.20.24.97.78 RED CONC 15 MM NB SCH 160", "Reducer"),
            ("RED-CONC 100X80 MM NB SCH 40", "Reducer"),
            ("ECCENTRIC REDUCER 8IN X 6IN SCH 40 ASTM A234", "Reducer"),
            ("HEX NIPPLE 1IN NPT 3000# ASTM A105", "Nipple"),
            ("SWAGE NIP 2IN X 1IN SCH 80", "Nipple"),
            ("FULL COUPLING 1IN 3000# SW ASTM A105", "Coupling"),
            ("HALF CPLG 1/2IN NPT 3000#", "Coupling"),
            ("PIPE UNION 2IN 3000# THREADED NPT", "Union"),
            ("PIPE CAP FITTING 4IN SCH 40 BUTTWELD", "Cap"),
            ("BW FITTING 6IN SCH 40 END PREPARATION", "Butt Weld Fitting"),
            ("INSTRUMENT FITTING 1/2IN OD COMPRESSION", "Fitting"),

            # ── 3. Gaskets & Seals ─────────────────────────────────
            ("OIL MESC 04.35.89.82.22 GSKT SWG 80 MM NB PN 20", "Spiral Wound Gasket"),
            ("GSKT-SWG 150# 6IN CS/SS304/GRAPHITE", "Spiral Wound Gasket"),
            ("SPIRAL WOUND GASKET 4IN 300# ASME B16.20", "Spiral Wound Gasket"),
            ("GSKT RTJ R-24 SOFT IRON RING TYPE JOINT", "Ring Type Joint Gasket"),
            ("RTJ GASKET OCTAGONAL 8IN 600#", "Ring Type Joint Gasket"),
            ("COMPRESSED NON ASBESTOS GASKET 2IN 150#", "Gasket"),
            ("CARTRIDGE MECHANICAL SEAL FOR CENTRIFUGAL PUMP", "Mechanical Seal"),
            ("MECH-SEAL 45 MM SHAFT TANDEM ARRANGEMENT", "Mechanical Seal"),
            ("VITON O-RING 50 MM ID X 3 MM CS", "O-Ring"),

            # ── 4. Flanges ─────────────────────────────────────────
            ("OIL MESC 04.01.30.66.80 FLG WN-RTJ 300 MM NB PN 100", "Weld Neck Flange"),
            ("FLG-WN 100 MM NB 150# SCH 40 ASTM A105", "Weld Neck Flange"),
            ("WELD NECK FLANGE 6IN 300# RF ASME B16.5", "Weld Neck Flange"),
            ("FLG BL 50 MM NB 150# BLIND FLANGE", "Blind Flange"),
            ("BLIND FLANGE 8IN 300# RF ASTM A105", "Blind Flange"),
            ("FLG SO 80 MM NB 150# SLIP ON FLANGE", "Slip-On Flange"),
            ("SLIP ON FLANGE 4IN 150# RF ASME B16.5", "Slip-On Flange"),
            ("CARBON STEEL FLANGE 6IN 300# RF", "Flange"),
            ("SPECTACLE BLIND FLANGE 6IN 300#", "Blind Flange"),

            # ── 5. Pipes & Tubes ───────────────────────────────────
            ("OIL MESC 03.10.94.72.29 PIPE SMLS 500 MM NB SCH 160", "Seamless Pipe"),
            ("PIPE-SMLS 20 MM NB SCH 20 API 5L X65", "Seamless Pipe"),
            ("LINE PIPE, SEAMLESS 8IN SCH 40 API 5L GR.B", "Seamless Pipe"),
            ("OIL MESC 03.10.36.65.84 PIPE ERW 50 MM NB SCH XXS", "ERW Pipe"),
            ("LINE PIPE, ELECTRIC RESISTANCE WELDED 12IN", "ERW Pipe"),
            ("CARBON STEEL PIPE 4IN SCH 40", "Pipe"),
            ("SS316 INSTRUMENT TUBING 1/2IN OD X 0.049IN WT", "Tube"),

            # ── 6. Pumps & Spares ──────────────────────────────────
            ("OIL MESC 06.10.84.64.84 PUMP SHAFT SLEEVE 50 MM NB", "Pump Shaft Sleeve"),
            ("SHAFT SLEEVE FOR SULZER BOILER FEED PUMP", "Pump Shaft Sleeve"),
            ("PUMP IMPELLER CLOSED TYPE 316SS 250 MM DIA", "Pump Impeller"),
            ("PUMP CASING VOLUTE FOR BB2 PROCESS PUMP", "Pump Casing"),
            ("CENTRIFUGAL PUMP HORIZONTAL END SUCTION API 610", "Centrifugal Pump"),

            # ── 7. Fasteners ───────────────────────────────────────
            ("OIL MESC 05.02.64.14.13 STUD BLT 5/8IN X 150MM", "Stud Bolt"),
            ("STUD-BLT 7/8IN X 120MM ASTM A193 B7", "Stud Bolt"),
            ("STUD BOLT WITH 2 HEAVY HEX NUTS 1IN X 180MM", "Stud Bolt"),
            ("HEX BOLT M16 X 60MM GRADE 8.8 GALVANIZED", "Bolt"),
            ("HEAVY HEX NUTS 2H 1IN ASTM A194", "Nut"),
            ("HEX NUT M20 GRADE 8", "Nut"),

            # ── 8. Mechanical Parts ────────────────────────────────
            ("CERAMIC SLEEVE 50 MM OD X 200 MM L", "Shaft Sleeve"),
            ("BACKUP RING PTFE 50 MM OD", "Ring"),
            ("DEEP GROOVE BALL BEARING SKF 6208 2RS", "Bearing"),

            # ── 9. Fallback & Unknown ──────────────────────────────
            ("TOTALLY UNRECOGNIZED WIDGET XYZ 12345", "General Material"),
            ("", "General Material"),
            ("   ", "General Material"),
        ],
    )
    def test_parameterized_classification(self, raw_description: str, expected_type: str):
        """Validates that candidate descriptions match their exact target item type."""
        assert extract_item_type(raw_description) == expected_type

    @pytest.mark.parametrize(
        ("description_with_substring", "forbidden_category"),
        [
            ("HIGH CAPACITY WATER HEATER TANK", "Cap"),
            ("SPRING LOADED DIAPHRAGM ACTUATOR", "Ring"),
            ("BORING BAR TOOLING INSERT", "Ring"),
            ("MOORING BUOY ANCHOR CHAIN", "Ring"),
            ("STAINLESS STEEL STRUCTURAL BEAM", "Tee"),
            ("STEEL PLATE 25 MM THICKNESS", "Tee"),
            ("MANIPULATE HOIST ASSEMBLY", "Nipple"),
            ("POTATO TUBER EXTRACT PREPARATION", "Tube"),
            ("MINUTE TIMER RELAY SWITCH", "Nut"),
            ("PEANUT SHELL ABRASIVE BLASTING MEDIA", "Nut"),
        ],
    )
    def test_false_positive_prevention(self, description_with_substring: str, forbidden_category: str):
        """Tokens inside unrelated words must NOT trigger false-positive classification."""
        classified = extract_item_type(description_with_substring)
        assert classified != forbidden_category

    def test_whitespace_and_case_insensitivity(self):
        """Mixed casing, irregular whitespace, and tabs must not affect classification."""
        assert extract_item_type("  vlv   bl   50 mm   ") == "Ball Valve"
        assert extract_item_type("Vlv\t\tBl\n50 Mm") == "Ball Valve"
        assert extract_item_type("elb-90    lr   100mm") == "Elbow"

    def test_none_input_returns_general_material(self):
        """None input gracefully defaults to 'General Material' without raising."""
        assert extract_item_type(None) == "General Material"


# ===========================================================================
# 5. DATASET-WIDE VALIDATION TEST
# ===========================================================================

class TestDatasetWideCatalogValidation:
    """Classifies every non-empty raw_description in datasets/inventory_catalog.csv."""

    def test_dataset_wide_classification_coverage(self):
        """
        Parses inventory_catalog.csv, runs extract_item_type across all rows,
        and reports classification metrics and any unclassified rows.
        """
        csv_path = Path("datasets/inventory_catalog.csv")
        assert csv_path.exists(), f"Dataset file not found at {csv_path}"

        total_rows = 0
        non_empty_rows = 0
        classified_rows = 0
        unclassified_rows: list[dict[str, str]] = []
        category_counts: dict[str, int] = {}

        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, 1):
                total_rows += 1
                desc = (row.get("raw_description") or "").strip()
                if not desc:
                    continue
                non_empty_rows += 1

                cat = extract_item_type(desc)
                category_counts[cat] = category_counts.get(cat, 0) + 1

                if cat == "General Material":
                    unclassified_rows.append({
                        "row": str(idx),
                        "sku": row.get("sku_code", ""),
                        "description": desc,
                    })
                else:
                    classified_rows += 1

        coverage_pct = (classified_rows / non_empty_rows) * 100.0 if non_empty_rows else 0.0

        # Formatted diagnostic report for test logs
        print("\n" + "=" * 60)
        print("DATASET-WIDE CLASSIFICATION SUMMARY")
        print("=" * 60)
        print(f"Total CSV Rows:                 {total_rows}")
        print(f"Non-Empty Descriptions:         {non_empty_rows}")
        print(f"Successfully Classified Rows:   {classified_rows} ({coverage_pct:.2f}%)")
        print(f"Unclassified Rows (General):    {len(unclassified_rows)}")
        print(f"Distinct Categories Identified: {len(category_counts)}")
        print("-" * 60)
        print("Category Distribution:")
        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            print(f"  {cat:30s} : {count:5d}")
        if unclassified_rows:
            print("-" * 60)
            print("First 10 Unclassified Rows:")
            for item in unclassified_rows[:10]:
                print(f"  Row {item['row']} [{item['sku']}]: {item['description'][:80]}")
        print("=" * 60)

        # Invariants:
        assert total_rows > 0
        assert non_empty_rows > 0
        # High classification rate: the vast majority of domain catalog records
        # must map into concrete engineering categories
        assert coverage_pct >= 95.0, (
            f"Classification coverage ({coverage_pct:.2f}%) fell below 95% threshold. "
            f"Unclassified count: {len(unclassified_rows)}"
        )
