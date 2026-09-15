# Material Deduplication & MTC Ingestion Studio (`app/deduplication`)

## 1. Overview
The `app/deduplication` directory implements the interactive material standardization studio at the `/deduplication` route.

It serves as the technical workbench where engineers can input raw procurement descriptions, inspect extracted engineering attributes, observe deterministic ASME safety evaluations, and test multi-modal OCR ingestion against real Mill Test Certificates (MTCs).

---

## 2. Key Components & Capabilities

### 1. Interactive Standardization Workbench
- Input Bar: Accepts raw, abbreviated strings from any ERP system (e.g., `FLG WNRF 4IN 300# A105`, `NRV 2IN 150# CS`, `BFV DN100 PN20 WCB`).
- Preset Query Buttons: Provides quick-fill buttons for common test queries across Flanges, Valves, Pipes, and Rotating Equipment.
- Sub-15ms Live Evaluation: Immediately calls `/api/v1/match/single` to parse attributes and query the candidate vector pool.

### 2. Physical Specification Attribute Grid
Displays extracted engineering properties in clean, structured cards:
- Component Type: Normalized mechanical classification (e.g. `FLANGE_WELD_NECK`).
- Nominal Bore: Metric millimeters (`100.0 mm`) and imperial representation (`4"`).
- Pressure Rating: ASME Class (`Class 300`) or Metric PN (`PN 50`).
- Material Grade: Canonical ASTM specification (e.g. `ASTM A105`, `ASTM A182 F316`).
- Facing Connection: Mating surface (e.g. `RF (Raised Face)`, `RTJ (Ring Type Joint)`).
- Governing Standard: Manufacturing standard (`ASME B16.5`, `API 600`, `ASME B36.10M`).
- Statutory Certification: Indicator for Indian Boiler Regulations (IBR 1950) compliance.

### 3. ASME Safety Invariant Result Card
- Tier Status Badge: Visual display of `TIER_1_IDENTICAL`, `TIER_2_SUBSTITUTE`, or `TIER_3_INCOMPATIBLE`.
- Compatibility Indicator: Green checkmark for safe deployment; Red warning for dangerous substitutions.
- Engineering Rationale: Detailed technical justification (e.g. why an upgrade is permitted or why down-rating is prohibited).

### 4. Candidate Pool Comparison Table
Lists the top 5 candidates retrieved from the master catalog:
- Displays Candidate SKU, Description, CPSE, and Confidence Score.
- Shows individual parameter match badges (`EXACT`, `UPGRADE`, `MISMATCH`).

### 5. Scanned Document & MTC Ingestion Studio
Allows users to evaluate the hardware-accelerated OCR and certificate parsing pipeline:
- Quick Preset Loaders: 7 buttons loading real sample images from `data/scanned_images`:
  - `Image (1)`: EN 10204 3.1 MTC (Flanges, 12 items extracted).
  - `Image (2)`: EN 10204 3.1.B Abnahmeprufzeugnis (Weld neck flanges).
  - `Image (3)`: High-pressure RTJ Blind Flange Certificate.
  - `Image (4)`: Delivery Challan with heat numbers.
  - `Image (5)`: Pneumatic Actuator Data Sheet.
  - `Image (6)`: Super Duplex Stainless Steel (ASTM A815 S32750) certificate.
  - `Image (7)`: Stainless Steel 316L sanitary fittings certificate.
- Custom File Upload: Drag-and-drop file input supporting JPEG, PNG, and PDF files.
- Tabular Extraction View: Renders extracted heat numbers, material grades, chemical analysis percentages (C, Mn, P, S, Cr, Mo), and mechanical properties.
