"""
Unit tests for Samanvay-AI Knowledge Graph Schema, CSV Validation, Access Scoping, and Compatibility Search.

All tests run completely with mocks; no live Neo4j credentials or database server required.
"""

from unittest.mock import MagicMock
import pytest

from graph.schema import NodeTypes, RelTypes, VALID_CPSES
from graph.seed_graph import validate_cpse_name, parse_csv_row
from graph.queries import GraphQuerier


# =====================================================================
# 1. GRAPH SCHEMA RECONCILIATION TESTS
# =====================================================================

def test_approved_schema_node_types():
    """Verifies that NodeTypes matches the approved schema exactly and contains no forbidden nodes."""
    expected_nodes = {
        "Item",
        "ItemType",
        "InventoryItem",
        "StockInfo",
        "Location",
        "State",
        "PurchaseOrder",
        "CPPPTender",
        "CPSE",
        "MaterialSpecification",
    }
    actual_nodes = {n.value for n in NodeTypes}
    assert actual_nodes == expected_nodes, f"NodeTypes does not match approved schema: {actual_nodes ^ expected_nodes}"

    forbidden_nodes = {
        "Depot",
        "CanonicalMaterial",
        "Heat",
        "Size",
        "PressureClass",
        "MaterialGrade",
        "RawDescription",
        "Standard",
        "HSNCode",
        "MESCCode",
        "GeMCategory",
        "IndianStandard",
        "OilSpecification",
        "OilMaterialCode",
    }
    for fn in forbidden_nodes:
        assert fn not in actual_nodes, f"Forbidden node '{fn}' detected in NodeTypes!"


def test_approved_schema_rel_types():
    """Verifies that RelTypes matches the approved schema relationships."""
    expected_rels = {
        "HAS_ITEM_TYPE",
        "HAS_ITEM",
        "HAS_STOCK_INFO",
        "STORED_AT",
        "IN_STATE",
        "ORDERED_BY",
        "PART_OF_TENDER",
        "OPERATED_BY",
        "HAS_SPECIFICATION",
    }
    actual_rels = {r.value for r in RelTypes}
    assert actual_rels == expected_rels, f"RelTypes does not match approved schema: {actual_rels ^ expected_rels}"


def test_valid_cpses_registry():
    """Verifies the single source of truth for CPSE organizations."""
    expected_cpses = {"OIL", "NRL", "IOCL", "ONGC", "BPCL", "HPCL", "GAIL"}
    assert VALID_CPSES == expected_cpses


# =====================================================================
# 2. CPSE VALIDATION & CSV PARSER TESTS
# =====================================================================

def test_validate_cpse_name_valid_values():
    """Validates that all registered CPSEs succeed, with whitespace trimmed and case normalized."""
    for cpse in ["OIL", "NRL", "IOCL", "ONGC", "BPCL", "HPCL", "GAIL"]:
        assert validate_cpse_name(cpse) == cpse
        assert validate_cpse_name(f"  {cpse}  ") == cpse
        assert validate_cpse_name(cpse.lower()) == cpse


def test_validate_cpse_name_missing():
    """Validates that missing CPSE values raise ValueError with descriptive reason."""
    with pytest.raises(ValueError) as exc_info:
        validate_cpse_name(None)
    assert "Missing 'cpse_name'" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info_row:
        validate_cpse_name(None, row_number=42)
    assert "Row 42: Missing 'cpse_name'" in str(exc_info_row.value)


def test_validate_cpse_name_blank():
    """Validates that blank/empty CPSE values raise ValueError."""
    for blank_val in ["", "   ", "\t\n"]:
        with pytest.raises(ValueError) as exc_info:
            validate_cpse_name(blank_val, row_number=10)
        assert "Row 10: Blank 'cpse_name'" in str(exc_info.value)


def test_validate_cpse_name_unknown_never_defaults_to_oil():
    """Validates that unknown CPSE values are rejected and NEVER silently defaulted to OIL."""
    unknown_values = ["UNKNOWN", "TATA", "RELIANCE", "ABC_CORP", "INVALID"]
    for unk in unknown_values:
        with pytest.raises(ValueError) as exc_info:
            validate_cpse_name(unk, row_number=99)
        msg = str(exc_info.value)
        assert "Row 99: Invalid CPSE" in msg
        assert unk in msg
        assert "OIL" not in msg or "Must be one of registered CPSEs" in msg


def test_parse_csv_row_valid():
    """Tests parsing a valid CSV row into the approved schema structure."""
    raw_row = {
        "sku_code": "IOCL-VLV-0001",
        "raw_description": "High Pressure Gate Valve 100mm 20 bar WCB",
        "nominal_bore_mm": "100.0",
        "pressure_rating_bar": "20.0",
        "quantity": "5",
        "unit_cost_inr": "25000.0",
        "days_idle": "120",
        "depot_location": "Panipat Refinery",
        "location_state": "Haryana",
        "po_no": "PO-IOCL-9988",
        "cpse_name": "IOCL",
    }
    parsed = parse_csv_row(raw_row, row_number=1)
    assert parsed["sku_code"] == "IOCL-VLV-0001"
    assert parsed["cpse_name"] == "IOCL"
    assert parsed["item_type"] == "Gate Valve"
    assert parsed["nominal_bore_mm"] == 100.0
    assert parsed["pressure_rating_bar"] == 20.0
    assert parsed["quantity"] == 5
    assert parsed["unit_cost_inr"] == 25000.0
    assert parsed["days_idle"] == 120
    assert parsed["depot_location"] == "Panipat Refinery"
    assert parsed["location_state"] == "Haryana"


def test_parse_csv_row_missing_cpse_rejected():
    """Tests that parse_csv_row rejects rows missing cpse_name with row number reporting."""
    raw_row = {
        "sku_code": "TEST-SKU",
        "raw_description": "Ball Valve",
    }
    with pytest.raises(ValueError) as exc_info:
        parse_csv_row(raw_row, row_number=55)
    assert "Row 55: Missing 'cpse_name'" in str(exc_info.value)


# =====================================================================
# 3. CPSE-SCOPED READS & PRIVACY ENFORCEMENT TESTS (MOCK DRIVER)
# =====================================================================

def _create_mock_querier(requesting_cpse=None, allow_cross_cpse=False):
    """Creates a GraphQuerier instance with mocked Neo4j driver and session."""
    querier = GraphQuerier(
        uri="bolt://localhost:7687",
        user="mock_user",
        password="mock_password",
        requesting_cpse=requesting_cpse,
        allow_cross_cpse=allow_cross_cpse,
    )
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    querier.driver = mock_driver
    return querier, mock_session


def test_get_item_by_sku_same_cpse_authorized():
    """In-tenant query returns full item subgraph including commercial price and PO number."""
    querier, mock_session = _create_mock_querier(requesting_cpse="OIL")

    mock_record = {
        "root_item": "Item",
        "item_type": "Stud Bolt",
        "item": {"sku_code": "OIL-STU-00001", "nominal_bore_mm": 25.0},
        "stock": {"quantity": 50, "days_idle": 180, "unit_cost_inr": 1250.0},
        "location": "Duliajan",
        "state": "Assam",
        "po_no": "PO-OIL-2024-001",
        "tender_id": "TND-OIL-01",
        "tender_ref": "REF-01",
        "cpse": "OIL",
        "specification": {"raw_description": "Stud Bolt B7"},
    }
    mock_session.run.return_value.single.return_value = mock_record

    res = querier.get_item_by_sku("OIL-STU-00001")
    assert res["cpse"] == "OIL"
    assert res["stock"]["unit_cost_inr"] == 1250.0
    assert res["po_no"] == "PO-OIL-2024-001"
    assert res["tender_id"] == "TND-OIL-01"


def test_get_item_by_sku_cross_cpse_unauthorized_fails():
    """Cross-tenant access without allow_cross_cpse raises PermissionError (SKU alone grants no access)."""
    querier, mock_session = _create_mock_querier(requesting_cpse="IOCL", allow_cross_cpse=False)

    mock_record = {
        "cpse": "OIL",
        "item": {"sku_code": "OIL-STU-00001"},
        "stock": {"quantity": 50, "unit_cost_inr": 1250.0},
    }
    mock_session.run.return_value.single.return_value = mock_record

    with pytest.raises(PermissionError) as exc_info:
        querier.get_item_by_sku("OIL-STU-00001")

    assert "Access denied" in str(exc_info.value)
    assert "IOCL" in str(exc_info.value)
    assert "OIL" in str(exc_info.value)


def test_get_item_by_sku_cross_cpse_authorized_strips_prices():
    """Cross-tenant access with allow_cross_cpse=True succeeds but strictly strips prices and tenders."""
    querier, mock_session = _create_mock_querier(requesting_cpse="IOCL", allow_cross_cpse=True)

    mock_record = {
        "root_item": "Item",
        "item_type": "Stud Bolt",
        "item": {"sku_code": "OIL-STU-00001"},
        "stock": {"quantity": 50, "days_idle": 180, "unit_cost_inr": 1250.0},
        "location": "Duliajan",
        "state": "Assam",
        "po_no": "PO-OIL-2024-001",
        "tender_id": "TND-OIL-01",
        "tender_ref": "REF-01",
        "cpse": "OIL",
        "specification": {"raw_description": "Stud Bolt B7"},
    }
    mock_session.run.return_value.single.return_value = mock_record

    res = querier.get_item_by_sku("OIL-STU-00001")
    assert res["cpse"] == "OIL"
    assert "unit_cost_inr" not in res["stock"]
    assert res["po_no"] is None
    assert res["tender_id"] is None
    assert res["tender_ref"] is None
    assert res["stock"]["quantity"] == 50


def test_get_item_by_sku_unscoped_rejected():
    """Unscoped request without requesting_cpse and without allow_cross_cpse raises PermissionError."""
    querier, _ = _create_mock_querier(requesting_cpse=None, allow_cross_cpse=False)
    with pytest.raises(PermissionError) as exc_info:
        querier.get_item_by_sku("OIL-STU-00001")
    assert "Access denied" in str(exc_info.value)


def test_get_cpse_surplus_same_cpse_authorized():
    """In-tenant surplus retrieval includes unit costs."""
    querier, mock_session = _create_mock_querier(requesting_cpse="OIL")
    mock_session.run.return_value = [
        {"sku_code": "OIL-VLV-1", "cpse": "OIL", "quantity": 10, "unit_cost_inr": 4000.0, "days_idle": 100}
    ]

    res = querier.get_cpse_surplus("OIL")
    assert len(res) == 1
    assert res[0]["unit_cost_inr"] == 4000.0


def test_get_cpse_surplus_cross_cpse_unauthorized_fails():
    """Attempting to access another CPSE's surplus without allow_cross_cpse raises PermissionError."""
    querier, _ = _create_mock_querier(requesting_cpse="BPCL", allow_cross_cpse=False)
    with pytest.raises(PermissionError) as exc_info:
        querier.get_cpse_surplus("OIL")
    assert "Access denied" in str(exc_info.value)
    assert "BPCL" in str(exc_info.value)


def test_get_cpse_surplus_cross_cpse_authorized_strips_prices():
    """Accessing another CPSE's surplus with allow_cross_cpse=True strips unit costs."""
    querier, mock_session = _create_mock_querier(requesting_cpse="BPCL", allow_cross_cpse=True)
    mock_session.run.return_value = [
        {"sku_code": "OIL-VLV-1", "cpse": "OIL", "quantity": 10, "unit_cost_inr": 4000.0, "days_idle": 100}
    ]

    res = querier.get_cpse_surplus("OIL")
    assert len(res) == 1
    assert "unit_cost_inr" not in res[0]
    assert res[0]["sku_code"] == "OIL-VLV-1"


# =====================================================================
# 4. PHYSICAL COMPATIBILITY SEARCH TESTS (find_compatible_surplus)
# =====================================================================

def test_find_compatible_surplus_missing_parameters_rejected():
    """Verifies that missing or non-positive engineering properties raise ValueError."""
    querier, _ = _create_mock_querier(requesting_cpse="OIL")

    # Missing item_type
    with pytest.raises(ValueError) as exc:
        querier.find_compatible_surplus("", nominal_bore_mm=100.0, pressure_rating_bar=20.0)
    assert "item_type" in str(exc.value)

    # Missing / non-positive nominal_bore_mm
    with pytest.raises(ValueError) as exc:
        querier.find_compatible_surplus("Gate Valve", nominal_bore_mm=0.0, pressure_rating_bar=20.0)
    assert "nominal_bore_mm" in str(exc.value)

    # Missing / non-positive pressure_rating_bar
    with pytest.raises(ValueError) as exc:
        querier.find_compatible_surplus("Gate Valve", nominal_bore_mm=100.0, pressure_rating_bar=-5.0)
    assert "pressure_rating_bar" in str(exc.value)


def test_find_compatible_surplus_exact_and_upgrade_classification():
    """Tests exact match vs safe pressure upgrade classification and commercial privacy filtering."""
    querier, mock_session = _create_mock_querier(requesting_cpse="IOCL", allow_cross_cpse=True)

    mock_candidates = [
        {
            "sku_code": "IOCL-VLV-100",
            "item_type": "Gate Valve",
            "nominal_bore_mm": 100.0,
            "pressure_rating_bar": 20.0,
            "quantity": 2,
            "unit_cost_inr": 50000.0,
            "cpse": "IOCL",
            "days_idle": 150,
        },
        {
            "sku_code": "OIL-VLV-200",
            "item_type": "Gate Valve",
            "nominal_bore_mm": 100.0,
            "pressure_rating_bar": 50.0,  # Safe upgrade
            "quantity": 4,
            "unit_cost_inr": 85000.0,     # Should be stripped for non-IOCL
            "cpse": "OIL",
            "days_idle": 210,
        },
    ]
    mock_session.run.return_value = mock_candidates

    results = querier.find_compatible_surplus(
        item_type="Gate Valve",
        nominal_bore_mm=100.0,
        pressure_rating_bar=20.0,
        allow_cross_cpse=True,
    )

    assert len(results) == 2

    # Item 1: IOCL (Same CPSE) -> Exact match, price preserved
    assert results[0]["sku_code"] == "IOCL-VLV-100"
    assert results[0]["compatibility_status"] == "EXACT_SPECIFICATION_MATCH"
    assert results[0]["unit_cost_inr"] == 50000.0

    # Item 2: OIL (Cross CPSE) -> Safe pressure upgrade, price stripped
    assert results[1]["sku_code"] == "OIL-VLV-200"
    assert results[1]["compatibility_status"] == "SAFE_PRESSURE_UPGRADE"
    assert "unit_cost_inr" not in results[1]
