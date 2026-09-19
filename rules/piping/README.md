# Process Piping & Pipeline Standards (`rules/piping/`)

This directory codifies piping, pipe schedules, API 5L line pipes, high-pressure instrumentation tubing, and sour service metallurgy.

---

## 1. File-by-File Breakdown

### `schedules.py` — ASME B36.10M / B36.19M Pipe Schedules
- **Purpose:** Enforces dimensional outer diameter (OD), inner diameter (ID), and wall thickness compatibility.
- **Key Functions:**
  - `normalize_schedule(val)`: Standardizes schedule aliases (`"SCH 40"`, `"40"`, `"STD"`, `"SCH 80"`, `"XS"`, `"XXS"`).
  - `check_pipe_schedule(query_sch, candidate_sch, nominal_size)`:
    - Compares schedule wall thicknesses. A heavier schedule pipe provides higher burst pressure but reduces internal flow area.
    - When candidate has heavier wall: outputs `TIER_2_SUPERSET` or `TIER_3_FUNCTIONAL_EQUIVALENT` with internal flow restriction warning.
    - When candidate has lighter wall: outputs immediate `TIER_4_INCOMPATIBLE` (burst danger).
  - `check_coating_thickness(query_coating, candidate_coating)`: Validates 3-Layer Polyethylene (3LPE) or Fusion Bonded Epoxy (FBE) thickness.

### `nace.py` — NACE MR0175 / ISO 15156 Sour Service Compliance
- **Purpose:** Serves as the unconditional gatekeeper for sour gas ($H_2S$) upstream environments.
- **Key Functions:**
  - `check_nace_sour_service(query_nace, candidate_nace, candidate_material, hardness_hrc)`:
    - In wet $H_2S$ environments, atomic hydrogen diffuses into metal lattices causing catastrophic **Sulfide Stress Cracking (SSC)** and **Hydrogen Induced Cracking (HIC)**.
    - Mandates maximum hardness $\le 22	ext{ HRC}$ for carbon steels and requires post-weld heat treatment (PWHT).
    - If query requires NACE and candidate lacks NACE certification: **Hard Reject (`TIER_4_INCOMPATIBLE`)**.

### `line_pipe.py` — API 5L Line Pipe Specifications
- **Purpose:** Validates cross-country hydrocarbon transport pipelines.
- **Key Functions:**
  - `check_line_pipe_quality(query_pipe, candidate_pipe)`:
    - Evaluates **Product Specification Levels (PSL 1 vs PSL 2)**. PSL 2 mandates mandatory Charpy V-Notch fracture toughness testing, maximum carbon equivalent ($CE_{IIW} \le 0.43$), and restricted phosphorus/sulfur chemistry. PSL 1 cannot substitute for PSL 2.
    - Compares grades: Grade B, X42, X52, X60, X65, X70, X80. Higher yield strength allows thinner walls.

### `tubing.py` — High-Pressure Instrumentation Tubing
- **Purpose:** Enforces tolerances for compression fitting assemblies (e.g. Swagelok, Parker Hannifin).
- **Key Functions:**
  - `check_instrumentation_tubing(query_tube, candidate_tube)`:
    - Unlike pipe (governed by NPS and nominal schedules), tubing is governed by exact Outside Diameter (OD) and measured wall thickness.
    - Enforces tube hardness limit ($< 80	ext{ HRB}$ for austenitic stainless steel ASTM A269/A213) to ensure ferrules can bite into the tube wall for a gas-tight seal.

### `expansion_joints.py` — EJMA Metallic & Elastomeric Bellows
- **Purpose:** Validates piping thermal expansion absorption devices per Expansion Joint Manufacturers Association (EJMA).
- **Key Functions:**
  - `check_expansion_joint_and_hose(query_joint, candidate_joint)`:
    - Compares axial compression, lateral offset, and angular deflection capabilities.
    - Checks tie rod assemblies and inner protective liners for high-velocity steam or particulate flows.

---

## 2. Engineering Formulas for Juniors

### 1. Barlow's Formula for Pipe Internal Design Pressure:
$$P = rac{2 \cdot S \cdot t}{D} \cdot F \cdot E \cdot T$$
- $P$ = Internal design pressure
- $S$ = Specified Minimum Yield Strength (SMYS) of the pipe material
- $t$ = Nominal wall thickness
- $D$ = Outside diameter
- $F$ = Design factor (0.72 for cross-country pipelines, 0.40 for high-density refinery areas per ASME B31.8)
- $E$ = Longitudinal joint factor (1.0 for seamless, 0.85 for ERW)
- $T$ = Temperature derating factor

### 2. Carbon Equivalent (CE) for Weldability:
$$CE_{IIW} = C + rac{Mn}{6} + rac{Cr + Mo + V}{5} + rac{Ni + Cu}{15}$$
- If $CE > 0.43$, preheating is mandatory before welding to avoid heat-affected zone (HAZ) hydrogen cracking.

---

## 3. Code Example

```python
from rules.piping.schedules import check_pipe_schedule
from rules.piping.nace import check_nace_sour_service

# Compare pipe schedule 40 vs candidate schedule 80
sch_res = check_pipe_schedule(query_sch="SCH 40", candidate_sch="SCH 80", nominal_size="6 INCH")
print(sch_res["tier"])  # DynamicCompatibilityTier.TIER_2_SUPERSET
print(sch_res["warnings"])  # ['HEAVIER_WALL_THICKNESS_RESTRICTS_INTERNAL_DIAMETER']

# Check NACE compliance
nace_res = check_nace_sour_service(query_nace=True, candidate_nace=False)
print(nace_res["tier"])  # DynamicCompatibilityTier.TIER_4_INCOMPATIBLE
```
