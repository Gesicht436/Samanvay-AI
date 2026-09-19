# Rotating Machinery Standards (`rules/rotating/`)

This directory codifies engineering rules for pumps, compressors, induction motors, hydrodynamic bearings, and mechanical shaft seals per American Petroleum Institute (API) and International Electrotechnical Commission (IEC) standards.

---

## 1. File-by-File Breakdown

### `pumps.py` — API 610 Centrifugal Pumps
- **Purpose:** Verifies refinery process centrifugal pumps and hydraulic performance parameters.
- **Key Functions:**
  - `check_centrifugal_pump(query_pump, candidate_pump)`:
    - **Pump Configurations:** API 610 Overhung (OH2, OH3), Between Bearings (BB1, BB2, BB3 multistage, BB5 double casing barrel), and Vertically Suspended (VS4, VS6).
    - **Net Positive Suction Head (NPSH) Margin:**
      $$	ext{Margin} = 	ext{NPSH}_a - 	ext{NPSH}_r \ge 1.0	ext{ m (or } 10\%)$$
      If candidate pump has higher $	ext{NPSH}_r$ than query, cavitation risk triggers rejection.
    - **Best Efficiency Point (BEP) Flow Rate:** Verifies that candidate operating point lies within $80\% - 110\%$ of BEP.

### `compressors.py` — API 617 / 618 Process Gas Compressors
- **Purpose:** Governs centrifugal/axial process compressors (API 617) and reciprocating compressors (API 618).
- **Key Functions:**
  - `check_compressor_compatibility(query_comp, candidate_comp)`:
    - Compares mass flow rate (Nm³/hr), suction pressure, pressure ratio ($r_p = P_d / P_s$), and discharge gas temperature.
    - Enforces maximum discharge temperature limits ($< 135^\circ	ext{C}$ for hydrogen service to avoid embrittlement).

### `motors.py` — IEC 60034 / NEMA MG-1 Electric Motors
- **Purpose:** Evaluates high-voltage and low-voltage three-phase squirrel-cage induction motors.
- **Key Functions:**
  - `check_motor_compatibility(query_motor, candidate_motor)`:
    - **Hazardous Area Protection:** IEC 60079 Ex classifications: **Ex d** (Flameproof enclosure), **Ex e** (Increased safety), **Ex p** (Pressurized). A safe area motor cannot substitute in Zone 1/Zone 2 explosive gas atmospheres.
    - **Efficiency Classes:** IE2 (High), IE3 (Premium), IE4 (Super Premium).
    - **Insulation & Duty:** Class F insulation with Class B temperature rise ($80	ext{ K}$ limit); S1 continuous duty.

### `seals.py` — API 682 Mechanical Shaft Seals & Piping Plans
- **Purpose:** Validates shaft sealing containment to eliminate VOC emissions and hazardous fluid leakage.
- **Key Functions:**
  - `check_mechanical_seal_and_elastomer(query_seal, candidate_seal)`:
    - **Arrangements:** Arrangement 1 (Single seal), Arrangement 2 (Dual unpressurized buffer fluid), Arrangement 3 (Dual pressurized barrier fluid with pressure $> P_{seal chamber} + 1.4	ext{ bar}$).
    - **Face Materials:** Silicon Carbide (SiC) vs Reaction Bonded SiC, Tungsten Carbide (TC), Carbon Graphite.
    - **O-Ring Elastomers:** FKM (Viton), FFKM (Kalrez, $-20^\circ	ext{C}$ to $320^\circ	ext{C}$), EPDM (steam/hot water), NBR (mineral oil).

### `bearings.py` — ISO 281 Bearing Life & Tolerances
- **Purpose:** Verifies anti-friction and hydrodynamic sleeve bearings.
- **Key Functions:**
  - `check_bearing_compatibility(query_bearing, candidate_bearing)`:
    - Calculates rating life $L_{10h}$ (minimum 25,000 continuous hours for API 610 pumps).
    - Checks internal radial clearance classes: C2, Normal, C3, C4.

---

## 2. Engineering Theory & Learning Resources

1. **API Standard 610 (12th Edition):** *Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries*.
2. **API Standard 682 (4th Edition):** *Pumps — Shaft Sealing Systems for Centrifugal and Rotary Pumps*. Master Piping Plans 11, 23, 52, 53A, 53B, 54.
3. **IEC 60079:** *Explosive Atmospheres*. Learn Zone 0, Zone 1, and Zone 2 gas group classifications (IIA, IIB, IIC for Hydrogen).

---

## 3. Code Example

```python
from rules.rotating.pumps import check_centrifugal_pump
from rules.rotating.motors import check_motor_compatibility

# Verify API 610 pump replacement
res_pump = check_centrifugal_pump(
    query_pump={"pump_type": "OH2", "flow_m3h": 100, "head_m": 80, "npshr_m": 2.5},
    candidate_pump={"pump_type": "OH2", "flow_m3h": 105, "head_m": 82, "npshr_m": 2.2}
)
print(res_pump["is_compatible"])  # True (Lower NPSHr is safer)

# Check hazardous area motor substitution
res_motor = check_motor_compatibility(
    query_motor={"power_kw": 45, "ex_class": "Ex d IIC T4", "voltage_v": 415},
    candidate_motor={"power_kw": 45, "ex_class": "Safe Area Non-Ex", "voltage_v": 415}
)
print(res_motor["is_compatible"])  # False
print(res_motor["violations"])     # ['HAZARDOUS_AREA_EX_RATING_MISSING']
```
