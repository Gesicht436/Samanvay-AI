"""
Unit tests for Samanvay Canonical Material Schema (SCMS-27).
Validates Pydantic contracts, alias normalization, and catalog data consistency.
"""

from pathlib import Path
import pandas as pd
import pytest

from backend.app.contracts.canonical_schema import (
    CANONICAL_COLUMNS,
    COLUMN_ALIASES,
    MANDATORY_COLUMNS,
    CanonicalMaterialItem,
    normalize_catalog_row,
)


def test_canonical_columns_specification():
    """Verify SCMS-27 specifies exactly 27 canonical columns across tiers 1 to 5."""
    assert len(CANONICAL_COLUMNS) == 27
    assert "sku_code" in CANONICAL_COLUMNS
    assert "canonical_id" in CANONICAL_COLUMNS
    assert "cpse" in CANONICAL_COLUMNS
    assert "depot_id" in CANONICAL_COLUMNS
    assert "depot_location" in CANONICAL_COLUMNS
    assert "item_type" in CANONICAL_COLUMNS
    assert "description" in CANONICAL_COLUMNS
    assert "size_nb_mm" in CANONICAL_COLUMNS
    assert "pressure_class" in CANONICAL_COLUMNS
    assert "pressure_rating_bar" in CANONICAL_COLUMNS
    assert "metallurgy" in CANONICAL_COLUMNS
    assert "facing_end" in CANONICAL_COLUMNS
    assert "schedule" in CANONICAL_COLUMNS
    assert "standard" in CANONICAL_COLUMNS
    assert "indian_standard" in CANONICAL_COLUMNS
    assert "oil_std_spec" in CANONICAL_COLUMNS
    assert "make_in_india_class" in CANONICAL_COLUMNS
    assert "local_content_percentage" in CANONICAL_COLUMNS
    assert "oil_material_code" in CANONICAL_COLUMNS
    assert "gem_category_id" in CANONICAL_COLUMNS
    assert "cppp_tender_ref" in CANONICAL_COLUMNS
    assert "po_no" in CANONICAL_COLUMNS
    assert "quantity" in CANONICAL_COLUMNS
    assert "unit_cost_inr" in CANONICAL_COLUMNS
    assert "status" in CANONICAL_COLUMNS
    assert "days_idle" in CANONICAL_COLUMNS
    assert "is_broadcasted_surplus" in CANONICAL_COLUMNS


def test_normalize_catalog_row_legacy_aliases():
    """Validates that legacy vendor and CPSE ERP headers map correctly to SCMS-27."""
    legacy_row = {
        "cpse_name": "iocl",
        "raw_description": "VLV GT 150 MM CL300 ASTM A105 RF",
        "local_code": "IOCL-MAT-9901",
        "nominal_bore_mm": 150.0,
        "extracted_item_type": "GATE_VALVE",
        "extracted_pressure_class": 300,
        "extracted_metallurgy": "ASTM A105",
        "extracted_facing": "RF",
        "extracted_standard": "API 600",
        "idle_days": 400,
        "mesc_code": "02.14.05.21",
        "gem_category": "GeM/CAT/VALVES/GATE",
        "cppp_tender_id": "CPPP-TND-9901",
        "quantity": 25,
        "unit_cost_inr": 18500.0,
        "depot_location": "Panipat Refinery, Haryana",
    }

    normalized = normalize_catalog_row(legacy_row)

    assert normalized["cpse"] == "IOCL"
    assert normalized["description"] == "VLV GT 150 MM CL300 ASTM A105 RF"
    assert normalized["sku_code"] == "IOCL-MAT-9901"
    assert normalized["size_nb_mm"] == 150.0
    assert normalized["item_type"] == "GATE_VALVE"
    assert normalized["pressure_class"] == 300
    assert normalized["metallurgy"] == "ASTM A105"
    assert normalized["facing_end"] == "RF"
    assert normalized["standard"] == "API 600"
    assert normalized["days_idle"] == 400
    assert normalized["oil_material_code"] == "02.14.05.21"
    assert normalized["gem_category_id"] == "GeM/CAT/VALVES/GATE"
    assert normalized["cppp_tender_ref"] == "CPPP-TND-9901"
    assert normalized["status"] == "SURPLUS_DECLARED"
    assert normalized["is_broadcasted_surplus"] is True
    assert normalized["depot_id"] == "IOCL_PANIPAT_REFINERY"


def test_canonical_material_item_validation():
    """Validates strongly-typed Pydantic model instantiations and constraints."""
    item = CanonicalMaterialItem(
        sku_code="BPCL-FLG-001",
        cpse="bpcl",
        depot_id="DEPOT-BPCL-MUM",
        depot_location="Mumbai Refinery, Mahul, Maharashtra",
        item_type="FLANGE_WELD_NECK",
        description="FLG WN 4IN CL300 ASTM A105 RF",
        size_nb_mm=100.0,
        pressure_class=300,
        quantity=15,
        unit_cost_inr=4500.0,
    )

    assert item.cpse == "BPCL"
    assert item.quantity == 15
    assert item.unit_cost_inr == 4500.0
    assert item.status == "TO_BE_CONSUMED"
    assert item.make_in_india_class == "Class-I"
    assert item.local_content_percentage == 75.0


def test_canonical_material_item_negative_rejections():
    """Validates rejection of invalid negative quantities and costs."""
    with pytest.raises(ValueError):
        CanonicalMaterialItem(
            sku_code="SKU-ERR-1",
            cpse="ONGC",
            depot_id="DEPOT-ONGC",
            depot_location="Hazira Plant, Gujarat",
            description="Test Item",
            quantity=-5,
            unit_cost_inr=100.0,
        )

    with pytest.raises(ValueError):
        CanonicalMaterialItem(
            sku_code="SKU-ERR-2",
            cpse="ONGC",
            depot_id="DEPOT-ONGC",
            depot_location="Hazira Plant, Gujarat",
            description="Test Item",
            quantity=10,
            unit_cost_inr=-50.0,
        )


def test_catalogs_conformance():
    """Verifies all CSV catalogs in data/catalogs conform to SCMS-27 schemas."""
    catalogs_dir = Path(__file__).resolve().parent.parent.parent / "data" / "catalogs"
    csv_files = list(catalogs_dir.glob("*.csv"))
    assert len(csv_files) >= 4, f"Expected at least 4 catalog CSVs, found {len(csv_files)}"

    for csv_file in csv_files:
        df = pd.read_csv(csv_file, nrows=20)
        cols = set(df.columns)

        # All catalogs must possess mandatory identity and financial columns
        for mand in MANDATORY_COLUMNS:
            assert mand in cols, f"{csv_file.name} missing mandatory column '{mand}'"

        # Validate rows through Pydantic model
        for _, row in df.iterrows():
            norm = normalize_catalog_row(row.to_dict())
            item = CanonicalMaterialItem(**norm)
            assert item.sku_code
            assert item.cpse in ("IOCL", "ONGC", "BPCL", "HPCL", "GAIL", "OIL", "NRL")
            assert item.quantity >= 0
            assert item.unit_cost_inr >= 0.0
