# Material Master Taxonomies & Ontologies

The `data/taxonomies` directory contains standardized ontologies, commodity classification hierarchies, and the national canonical material master catalog.

---

## File Inventory & Ontological Standards

### 1. `canonical_master.csv` (National Canonical Material Master)
- **Item Count**: 2,201 unique engineering items.
- **Purpose**: Serves as the golden reference standard against which divergent CPSE catalog entries are harmonized and deduplicated.
- **Key Columns**:
  - `canonical_id`: Persistent identifier (e.g. `CANON-FLG-WN-0001`).
  - `item_type`: Canonical category (`FLANGE`, `VALVE`, `GASKET`, `BOLT`, `PIPE`, `FITTING`).
  - `size_nb_mm`: Nominal Bore in millimeters ($15.0 \dots 1200.0\text{ mm}$).
  - `size_inch`: Fractional imperial representation ($1/2" \dots 48"$).
  - `pressure_class`: Normalized ASME rating ($150, 300, 600, 900, 1500, 2500$).
  - `metallurgy`: Standard ASTM alloy specification.
  - `facing_end`: Sealing face or end preparation (`RF`, `RTJ`, `FF`, `BW`, `SW`, `NPT`).
  - `unspsc_code` & `gem_category_id`: Direct cross-references to national procurement portals.

### 2. `gem_categories.csv` (Government e-Marketplace - GeM)
- Maps oil & gas mechanical spares into official GeM public procurement categories:
  - `GEM-VALVE-GATE`: Gate Valves - Cast & Forged Steel
  - `GEM-VALVE-BALL`: Ball Valves - High Pressure Hydrocarbon
  - `GEM-FLANGE-WN`: Weld Neck Flanges - ASME B16.5
  - `GEM-BOLT-STUD`: Alloy Steel Stud Bolts with Heavy Hex Nuts - ASTM A193
- Enables CPSE procurement officers to instantly cross-post surplus inventory to the national GeM marketplace.

### 3. `unspsc_v26.csv` (UNSPSC Version 26 Commodity Hierarchy)
- Four-level hierarchical classification (Segment $\rightarrow$ Family $\rightarrow$ Class $\rightarrow$ Commodity):
  - `40000000`: Industrial Manufacturing and Processing Machinery and Accessories
  - `40140000`: Fluid and gas distribution
  - `40141600`: Valves (`40141611` Gate, `40141604` Ball, `40141602` Globe, `40141601` Check)
  - `40171500`: Industrial pipe fittings (`40171501` Flanges, `40171502` Elbows, `40171503` Tees)
  - `31160000`: Hardware and Fasteners (`31161501` Stud Bolts, `31161618` Spiral Wound Gaskets)
