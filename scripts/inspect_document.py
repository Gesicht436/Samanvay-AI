"""
Samanvay-AI Document Inspection CLI Utility.
Runs end-to-end OCR and PDF extraction on any scanned certificate, challan, or PDF,
printing a formatted terminal breakdown of physical attributes, chemical analysis,
mechanical properties, weldability (Carbon Equivalent), and line items.

Usage:
  uv run python scripts/inspect_document.py data/raw/sample_mtc_flange_01.pdf
  uv run python scripts/inspect_document.py "data/scanned_images/Image (1).jpeg"
  uv run python scripts/inspect_document.py <any_file> --json
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.ingestion.pdf_parser import process_document


def print_banner(title: str):
    print("\n" + "=" * 75)
    print(f"  {title.upper()}")
    print("=" * 75)


def print_section(title: str):
    print(f"\n--- [ {title} ] " + "-" * (65 - len(title)))


def inspect_file(file_path: Path, output_json: bool = False):
    if not file_path.exists():
        print(f"Error: File not found at '{file_path}'")
        sys.exit(1)

    print(f"Reading and analyzing: {file_path.name} ({file_path.stat().st_size:,} bytes)...")
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    result = process_document(file_bytes, file_path.name)

    if output_json:
        print(json.dumps(result, indent=2))
        return

    meta = result.get("parsed_metadata", {})
    attrs = meta.get("extracted_attributes", {})

    print_banner(f"Document Analysis: {result['filename']}")

    # 1. General Document Metadata
    print_section("1. Core Document Classification")
    print(f"  Document Type        : {result.get('doc_type')} ({result.get('doc_subtype')})")
    print(f"  Processing Pipeline  : {'Scanned Image / OCR' if result.get('is_scanned') else 'Digital Native PDF Stream'}")
    print(f"  Extraction Latency   : {result.get('processing_time_ms', 0):.2f} ms")
    print(f"  Page Count           : {result.get('page_count', 1)}")
    print(f"  Parser Confidence    : {result.get('confidence', 0.0) * 100:.1f}%")

    # 2. Certificate Tracking Identifiers
    print_section("2. Tracking & Enterprise Identifiers")
    print(f"  Certificate No (MTC) : {meta.get('cert_no') or 'N/A'}")
    print(f"  Purchase Order (PO)  : {meta.get('po_no') or 'N/A'}")
    print(f"  Heat / Batch Number  : {meta.get('heat_no') or 'N/A'}")
    print(f"  Manufacturer / Mill  : {meta.get('manufacturer') or 'N/A'}")
    print(f"  Governing Standard   : {meta.get('standard') or attrs.get('standard') or 'N/A'}")
    print(f"  Material Grade       : {meta.get('material_grade') or attrs.get('metallurgy') or 'N/A'}")

    # 3. Primary Standardized Physical Specifications
    print_section("3. Normalized Physical Specifications (NER Extractor)")
    print(f"  Primary Description  : {meta.get('primary_item') or meta.get('description') or 'N/A'}")
    print(f"  Normalized Item Type : {attrs.get('item_type') or 'N/A'}")
    print(f"  Nominal Bore (NB)    : {attrs.get('size_nb_mm')} mm ({attrs.get('size_inch') or 'N/A'}) [DN: {attrs.get('dn_code') or 'N/A'}]")
    print(f"  Pressure Class       : Class {attrs.get('pressure_class') or 'N/A'}")
    print(f"  Facing / End Connect : {attrs.get('facing_end') or 'N/A'}")
    print(f"  Standard Metallurgy  : {attrs.get('metallurgy') or 'N/A'}")
    print(f"  Pipe Schedule        : {attrs.get('schedule') or 'N/A'}")
    print(f"  NACE Sour Service    : {'YES (Compliant)' if meta.get('nace_compliant') or attrs.get('is_sour_service') else 'Standard / Non-Sour'}")
    print(f"  IBR Steam Certified  : {'YES (Indian Boiler Regulations 1950)' if meta.get('is_ibr_certified') or attrs.get('is_ibr_certified') else 'Non-IBR'}")

    # 4. Chemical Composition & Carbon Equivalent (CE)
    chem = meta.get("chemical_dict", {})
    ce = meta.get("carbon_equivalent")
    if chem:
        print_section("4. Chemical Composition & Weldability Verification")
        elements_str = " | ".join([f"{k}: {v}" for k, v in chem.items()])
        print(f"  Elemental Analysis   : {elements_str}")
        if ce:
            print(f"  Carbon Equivalent CE: {ce['carbon_equivalent']}% (Limit: <={ce['max_recommended_ce']}%)")
            print(f"  Weldability Status   : {ce['status']} (Weldable: {ce['is_standard_weldable']})")
    else:
        print_section("4. Chemical Composition")
        print("  No tabular chemical elemental breakdown present in this document.")

    # 5. Mechanical Properties
    mech = meta.get("mechanical_dict", {})
    if mech:
        print_section("5. Mechanical Test Properties")
        for k, v in mech.items():
            print(f"  {k.title():20}: {v}")
    
    # 6. Safety & Validation Warnings
    warnings = meta.get("validation_warnings", [])
    if warnings:
        print_section("6. Safety & Compliance Warnings")
        for w in warnings:
            print(f"  [!] WARNING: {w}")

    # 7. Multi-Item Line Items
    items = meta.get("extracted_items", [])
    if items:
        print_section(f"7. Extracted Line Items ({len(items)} Found)")
        for idx, itm in enumerate(items, 1):
            it_attrs = itm.get("attributes", {})
            desc = itm.get("raw_line", "")
            type_str = it_attrs.get("item_type") or "UNKNOWN"
            size_str = f"{it_attrs.get('size_nb_mm')} mm" if it_attrs.get("size_nb_mm") else ""
            cl_str = f"Class {it_attrs.get('pressure_class')}" if it_attrs.get("pressure_class") else ""
            summary = " - ".join(filter(None, [type_str, size_str, cl_str]))
            print(f"  Line {idx:02d}: {desc[:55]:55} -> [{summary}]")

    print("\n" + "=" * 75 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Samanvay-AI Document OCR & PDF Inspector")
    parser.add_argument("file_path", type=str, help="Path to PDF or image file to inspect")
    parser.add_argument("--json", action="store_true", help="Print raw JSON output instead of formatted report")
    args = parser.parse_args()

    inspect_file(Path(args.file_path), output_json=args.json)
