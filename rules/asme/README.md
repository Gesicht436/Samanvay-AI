# ASME Standards Codification Module (`rules/asme/`)

This directory codifies the **American Society of Mechanical Engineers (ASME)** piping and flange design standards into deterministic safety checks. These rules govern pressure retention, flange mechanical interfaces, gasket dynamics, and dimensional compatibility across refinery and offshore pipeline systems.

---

## 1. File-by-File Breakdown

### `pressure_class.py` — ASME B16.5 / B16.47 Pressure Class Ratings
- **Purpose:** Validates that candidate piping components meet or exceed the required pressure-temperature envelope.
- **Key Functions:**
  - `_normalize_class(value)`: Converts varying notations (e.g., `"300#"`, `"Class 300"`, `"CL300"`, `"300 LB"`, `"PN50"`) into standard integer ratings (`150`, `300`, `400`, `600`, `900`, `1500`, `2500`).
  - `check_pressure_class(query_class, candidate_class)`: Compares nominal classes. Lower candidate class results in immediate rejection (`TIER_4_INCOMPATIBLE`). Equal class yields `TIER_1_EXACT`. Higher candidate class yields `TIER_2_SUPERSET` with a caveat regarding heavier bolt/flange weights.
  - `check_pressure_rating_psi(material_group, pressure_class, design_temp_c)`: Calculates the exact allowable working pressure in PSI at operating temperature using ASME B16.5 Table 2-1.1 (Carbon Steel) and Table 2-2.2 (316 SS).

### `facings.py` — ASME B16.5 Flange Facings
- **Purpose:** Enforces mechanical sealing interface compatibility between mating flanges.
- **Key Functions:**
  - `check_flange_facing(query_facing, candidate_facing, query_material, candidate_material)`:
    - Supported facings: `RF` (Raised Face, 0.06" or 0.25" serrated), `FF` (Flat Face), `RTJ` (Ring Type Joint).
    - **Brittle Cast Iron Rule:** ASME B16.5 strictly prohibits mating Raised Face (RF) flanges to Flat Face (FF) brittle grey iron equipment (e.g. ASTM A126) because tightening bolts exerts a bending moment across the flange that fractures cast iron flanges.
    - **RTJ Rule:** RTJ flanges utilize metallic ring gaskets (octagonal or oval) in machined grooves and cannot mate directly with RF or FF flanges without catastrophic leakage.

### `fittings.py` — ASME B16.11 Forged & ASME B16.9 Buttweld Fittings
- **Purpose:** Validates rating correlation between fittings and mating pipe schedules.
- **Key Functions:**
  - `check_forged_fittings_rating(fitting_class, pipe_schedule)`: Under ASME B16.11, Class 3000 forged socket weld / threaded fittings correlate to Schedule 80 / XS pipe; Class 6000 correlates to Schedule 160 pipe; Class 2000 correlates to Schedule 40.
  - `check_buttweld_elbow_radius(query_radius, candidate_radius)`: Distinguishes Long Radius (LR, $R = 1.5D$) from Short Radius (SR, $R = 1.0D$) and 3D/5D bends. SR elbows induce significantly higher pressure drop and cannot be pigged; substituting SR for LR triggers `TIER_4_INCOMPATIBLE`.
  - `check_pipeline_fittings_smys(query_grade, candidate_grade)`: Enforces Specified Minimum Yield Strength (SMYS) under MSS SP-75 (WPHY 42 through WPHY 70).

### `gaskets.py` — ASME B16.20 & B16.21 Sealing Elements
- **Purpose:** Verifies gasket metallurgy, filler materials, and seating mechanics.
- **Key Functions:**
  - `check_gasket_compatibility(query_gasket, candidate_gasket, design_temp, design_pressure)`:
    - Compares Spiral Wound Gaskets (SPWD with Graphite, PTFE, or Mica filler), Ring Type Joints (Soft Iron, SS316, Inconel 625), and Compressed Non-Asbestos Fiber (CNAF).
    - Checks inner ring requirements: ASME B16.20 mandates inner rings for all Class 900+ spiral wound gaskets and all PTFE-filled gaskets to prevent inward radial buckling into the flow stream.

### `flange_insulation.py` — Cathodic Protection Dielectric Kits
- **Purpose:** Enforces electrical isolation kit specs for buried or subsea pipeline galvanic protection.
- **Key Functions:**
  - `check_flange_insulation_kit(query_kit, candidate_kit)`:
    - Distinguishes **Type E** (Full Face, isolates entire flange face and eliminates foreign bridging), **Type F** (Raised Face only), and **Type D** (RTJ insulating gaskets).
    - Checks retainer material (G-10 epoxy glass, phenolic) and sleeve/washer dielectric breakdown voltage.

### `large_flanges.py` — ASME B16.47 Series A vs Series B
- **Purpose:** Prevents cross-mating between Series A (MSS SP-44) and Series B (API 605) flanges (sizes 26" to 60").
- **Key Functions:**
  - `check_large_flange_series(query_series, candidate_series, size_inch)`:
    - Series A flanges have thicker flanges, larger bolt circles, and fewer but larger bolts; designed for heavy pipeline valves.
    - Series B flanges have smaller bolt circles and more compact dimensions; designed for process equipment nozzles.
    - **Direct substitution is mechanically impossible** due to mismatched bolt pitch circle diameters (PCD).

### `line_blinds.py` — ASME B16.48 Spectacle Blinds & Spacers
- **Purpose:** Governs positive pipeline isolation devices.
- **Key Functions:**
  - `check_line_blind_compatibility(query_blind, candidate_blind)`:
    - Evaluates Spectacle Blinds (Figure-8), Spade / Paddle Blinds, and Paddle Spacers.
    - Ensures pressure rating and inside diameter (ID) match mating ASME B16.5 flange bore.

---

## 2. Tech Stack & Dependencies

- **Language:** Python 3.11+
- **Typing:** `typing.Optional`, `typing.Dict`, `typing.Tuple`, `typing.Any`
- **Schemas:** `backend.app.schemas.material.DynamicCompatibilityTier`
- **Testing:** PyTest (`tests/unit/test_tolerance.py`)

---

## 3. Engineering Theory & Learning Resources

For junior engineers:
1. **ASME B16.5:** *Pipe Flanges and Flanged Fittings: NPS 1/2 through NPS 24 Metric/Inch Standard*. Study Section 2 (Pressure-Temperature Ratings) and Section 6 (Flange Dimensions).
2. **ASME B16.47:** *Large Diameter Steel Flanges: NPS 26 Through NPS 60*. Understand why MSS SP-44 (Series A) and API 605 (Series B) exist in parallel.
3. **Flange Bolting & Torque Dynamics:** Review the *ASME PCC-1: Guidelines for Pressure Boundary Bolted Flange Joint Assembly*.

---

## 4. Code Example

```python
from rules.asme.pressure_class import check_pressure_class
from rules.asme.facings import check_flange_facing

# Verify pressure rating upgrade
res_class = check_pressure_class(query_class=150, candidate_class=300)
print(res_class["tier"])  # DynamicCompatibilityTier.TIER_2_SUPERSET

# Verify RF to FF safety rule on cast iron
res_facing = check_flange_facing(
    query_facing="FF", candidate_facing="RF",
    query_material="ASTM A126", candidate_material="ASTM A105"
)
print(res_facing["tier"])  # DynamicCompatibilityTier.TIER_4_INCOMPATIBLE
print(res_facing["violations"])  # ['MATING_RF_TO_FF_CAST_IRON_PROHIBITED']
```
