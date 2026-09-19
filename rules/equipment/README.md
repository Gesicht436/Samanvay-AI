# Static Process Equipment Standards (`rules/equipment/`)

This directory codifies engineering rules for static heat transfer, fluid separation, storage tanks, and thermal insulation systems across downstream hydrocarbon processing units.

---

## 1. File-by-File Breakdown

### `heat_exchangers.py` — TEMA Shell & Tube Heat Exchangers
- **Purpose:** Enforces standards from the **Tubular Exchanger Manufacturers Association (TEMA)** and ASME Section VIII Div 1.
- **Key Functions:**
  - `check_heat_exchanger_tubes(query_tube, candidate_tube)`:
    - Compares tube outer diameter (OD, e.g. 3/4", 1") and Birmingham Wire Gauge (BWG wall thickness).
    - Checks tube material (Cu-Ni 90/10, Titanium Gr 2, SS316L, Carbon Steel).
    - Verifies tube pitch (Triangular $30^\circ$, Rotated Triangular $60^\circ$, Square $90^\circ$) and impingement protection requirements for high-velocity two-phase inlet nozzles.
    - Validates TEMA classes: **TEMA R** (Severe petroleum refinery duty), **TEMA C** (Commercial/general chemical duty), and **TEMA B** (Chemical process service).

### `strainers_traps.py` — Pipeline Strainers & Steam Traps
- **Purpose:** Verifies particulate filtration elements and thermodynamic steam condensate discharge.
- **Key Functions:**
  - `check_strainer_filter_and_steam_trap(query_eq, candidate_eq)`:
    - **Strainers:** Y-Type, T-Type, and Basket Strainers. Validates screen perforation size (mesh number or mm perforation) and open area ratio (minimum 3:1 net free area vs pipe flow area).
    - **Steam Traps:** Inverted Bucket (mechanical), Thermodynamic Disc, and Thermostatic Bimetallic traps. Verifies maximum allowable operating differential pressure ($\Delta P_{\max}$) and condensate discharge capacity (kg/hr).

### `tank_safety.py` — API 650 / API 620 Tank Protection
- **Purpose:** Governs atmospheric storage tank safety venting, emergency venting, and protective coatings.
- **Key Functions:**
  - `check_tank_safety_and_paint(query_tank, candidate_tank)`:
    - Evaluates Pressure/Vacuum Relief Valves (PVRV / Breather Valves per API 2000).
    - Evaluates Deflagration and Detonation Flame Arresters per ISO 16852 / NFPA 69.
    - Validates external epoxy/polyurethane tank coating systems against atmospheric corrosive marine environments (ISO 12944 Corrosivity Categories C3, C4, C5M).

### `thermal_insulation.py` — Hot/Cold Insulation & CUI Mitigation
- **Purpose:** Prevents **Corrosion Under Insulation (CUI)**, the leading cause of unexpected piping failures in chemical plants.
- **Key Functions:**
  - `check_thermal_insulation_cui(query_insul, candidate_insul)`:
    - Evaluates Hot Insulation materials: Rock Mineral Wool, Calcium Silicate, Pyrogenic Silica Aerogel blanket.
    - Evaluates Cold/Cryogenic Insulation: Cellular Glass (Foamglas, non-absorbent to liquid hydrocarbons), Polyisocyanurate (PIR).
    - **Chloride Stress Corrosion Cracking (ESCC) Rule:** Prohibits insulation containing leachable chlorides over austenitic stainless steel piping (ASTM C795 compliance mandatory).

---

## 2. Engineering Theory & Learning Resources

1. **TEMA Standards (10th Edition):** Study Section 5 (TEMA Structural and Thermal Tolerances) and tube layout aerodynamics.
2. **API Standard 2000:** *Venting Atmospheric and Low-pressure Storage Tanks*. Understand thermal inbreathing/outbreathing and emergency fire exposure venting formulas.
3. **NACE SP0198:** *Control of Corrosion Under Thermal Insulation and Fireproofing Materials*. Understand how trapped moisture in cyclic $50^\circ	ext{C}-175^\circ	ext{C}$ zones destroys steel.

---

## 3. Code Example

```python
from rules.equipment.thermal_insulation import check_thermal_insulation_cui

# Attempting to use generic rockwool on SS316 pipe in marine environment
eval_result = check_thermal_insulation_cui(
    query_insul={"pipe_material": "SS316", "temp_c": 120, "astm_c795_certified": True},
    candidate_insul={"pipe_material": "SS316", "temp_c": 120, "astm_c795_certified": False}
)
print(eval_result["is_compatible"])  # False
print(eval_result["violations"])     # ['LEACHABLE_CHLORIDES_RISK_ON_AUSTENITIC_SS_CUI']
```
