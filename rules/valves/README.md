# Industrial Valve Engineering Standards (`rules/valves/`)

This directory codifies valve mechanical designs, pipeline piggability, fire-safe testing, pressure relief sizing, and API valve trim numbers.

---

## 1. File-by-File Breakdown

### `bore.py` — API 6D Full Bore (FB) vs Reduced Bore (RB)
- **Purpose:** Enforces bore diameter compatibility and intelligent piggability requirements.
- **Key Functions:**
  - `check_valve_bore(query_bore, candidate_bore)`:
    - **Full Bore / Full Port (FB):** Valve bore has an unobstructed circular opening equal to or greater than the mating pipe internal diameter. Mandatory for lines subject to scraper/intelligent pipeline inspection gauges (PIGs).
    - **Reduced Bore (RB):** Bore is typically one nominal size smaller (e.g. 6" valve has 4" bore).
    - Substituting an RB valve on a line specified for FB results in immediate **rejection (`TIER_4_INCOMPATIBLE`)** due to pipeline pig jamming risks.

### `fire_safe.py` — API 607 / API 6FA / ISO 10497 Fire Safety
- **Purpose:** Verifies that soft-seated ball, plug, or butterfly valves maintain seal integrity during and after a refinery fire.
- **Key Functions:**
  - `check_fire_safe_and_categories(query_valve, candidate_valve)`:
    - Fire-safe valves feature primary soft seals (PTFE, PEEK) and secondary metal-to-metal backup seats. When a fire destroys the soft seal, the closure element shifts against the metal backup seat to prevent fuel feeding the fire.
    - If query requires `fire_safe=True`, candidate must have certified API 607 / API 6FA documentation.

### `trim.py` — API 600 / API 602 Standard Trim Metallurgies
- **Purpose:** Evaluates internal wetted components (stem, seat surface, disc/wedge facing).
- **Key Functions:**
  - `check_valve_trim(query_trim, candidate_trim)`:
    - Maps standard API trim designations:
      - **Trim 1:** $13\%	ext{ Cr}$ (F6a stem and seats, general utility).
      - **Trim 5:** Hardfaced Stellite ($Co-Cr-W$ alloy, severe erosive/high temp).
      - **Trim 8:** Universal Trim ($13\%	ext{ Cr}$ stem + Stellite faced seats).
      - **Trim 10:** 316 Stainless Steel (corrosive chemical services).
      - **Trim 12:** 316 Stainless Steel with Stellite hardfacing.
    - Upgrading from Trim 1 to Trim 8 is permitted (`TIER_2_SUPERSET`), while downgrading from Trim 8/Trim 5 to Trim 1 triggers rejection.

### `psv.py` — API 520 / API 526 Pressure Safety Relief Valves (PSV)
- **Purpose:** Governs overpressure relief protection sizing and discharge capacity.
- **Key Functions:**
  - `check_psv_orifice_and_pressure(query_psv, candidate_psv)`:
    - Compares standard API 526 orifice designations (**D** through **T**, where D = $0.110	ext{ in}^2$ and T = $26.00	ext{ in}^2$).
    - Verifies set pressure ($P_{set}$) and backpressure limits (balanced bellows vs conventional valve designs).

### `rupture_disks.py` — ASME Sec VIII Div 1 & ISO 4126-2 Rupture Discs
- **Purpose:** Verifies non-reclosing pressure relief safety devices.
- **Key Functions:**
  - `check_rupture_disk(query_disk, candidate_disk)`:
    - Forward-acting vs Reverse-buckling discs.
    - Operating ratio: Reverse-buckling discs permit operating up to $90\%$ of burst pressure without metal fatigue, compared to $70\%$ for forward-acting tension discs.

---

## 2. Engineering Theory & Learning Resources

1. **API Standard 6D:** *Specification for Pipeline and Piping Valves*. Study Section 5 for dimensional bore tolerances.
2. **API Standard 520 Part I & II:** *Sizing, Selection, and Installation of Pressure-relieving Devices in Refineries*.
3. **API Recommended Practice 598:** *Valve Inspection and Testing* (Shell hydrostatic, low-pressure gas seat leakage rates).

---

## 3. Code Example

```python
from rules.valves.bore import check_valve_bore
from rules.valves.trim import check_valve_trim

# Verify full bore piggability restriction
res_bore = check_valve_bore(query_bore="FULL_BORE", candidate_bore="REDUCED_BORE")
print(res_bore["is_compatible"])  # False
print(res_bore["violations"])     # ['REDUCED_BORE_CANNOT_SUBSTITUTE_FOR_FULL_BORE_PIGGABLE']

# Verify trim upgrade (Trim 1 -> Trim 8)
res_trim = check_valve_trim(query_trim="TRIM 1", candidate_trim="TRIM 8")
print(res_trim["tier"])  # DynamicCompatibilityTier.TIER_2_SUPERSET
```
