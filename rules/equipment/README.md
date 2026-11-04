# Equipment, Thermal & Tank Safety Tolerance Rules

The `rules/equipment` module governs process equipment integrity, atmospheric storage tank safety, heat exchanger tube bundles, line filtration, and Corrosion Under Insulation (CUI) prevention based on **TEMA Standards, API 2000, ISO 16852, ASTM C795, and ASTM C552**.

---

## File Breakdown & Process Invariants

### 1. `heat_exchangers.py` (TEMA 10th Ed. & ASME Section VIII)
- **TEMA Construction Class Hierarchy**:
  $$\text{TEMA R (Severe Refinery Duty)} > \text{TEMA C (Commercial Industrial)} > \text{TEMA B (Chemical Process)}$$
  Downgrading TEMA R specifications to TEMA C or B is blocked as an unapproved tube bundle erosion and premature failure trap.
- **Seamless vs. Welded Tubing**: In critical reboilers, high-pressure hydrocarbon service, or hydrogen rich circuits, welded tubing (`ASTM A249`) is prohibited as a substitute for seamless tubing (`ASTM A213`).
- **BWG Wall Specification**: Minimum Wall (MW) specified tubes cannot be substituted with Average Wall (AW) tubes due to localized thin spots leading to buckling under external shell pressure.
- **U-Bend Solution Annealing (TEMA R RCB-2.31)**: Cold-bent U-tubes in austenitic stainless steel mandate post-bending solution annealing to eliminate residual forming stresses and prevent chloride stress corrosion cracking (Cl-SCC).

### 2. `tank_safety.py` (API 2000 / API 650 / ISO 16852)
- **API 2000 Pressure/Vacuum Relief Valves (PVRV)**: In-breathing venting capacity ($\text{Nm}^3/\text{hr}$) must equal or exceed maximum liquid pump-out displacement. Installing an under-sized replacement valve is blocked as a **Storage Tank Vacuum Implosion Trap**.
- **ISO 16852 Flame & Detonation Arrestors**: End-of-line deflagration arrestors cannot quench supersonic detonation shock waves within closed flare or vapor recovery headers. In-line detonation arrestors are strictly mandatory.
- **Protective Coating Systems**: Rejects incompatible paint systems (e.g. utility alkyd applied over chemical-resistant epoxy-phenolic tank linings).

### 3. `thermal_insulation.py` (ASTM C795 / ASTM C552 / NACE SP0198)
- **Corrosion Under Insulation (CUI) on Stainless Steel**: Between $50^\circ\text{C}$ and $150^\circ\text{C}$, thermal insulation over austenitic stainless steel (`SS304`, `SS316`) or duplex alloys must comply with **ASTM C795** (leachable chlorides $< 50\text{ ppm}$ with active sodium silicate inhibitors). Non-inhibited insulation triggers a **Chloride External Stress Corrosion Cracking (Cl-ESCC) Trap**.
- **ASTM C552 Cryogenic Cellular Glass**: Cryogenic lines ($-162^\circ\text{C}$ LNG / $-42^\circ\text{C}$ LPG) require $100\%$ closed-cell cellular glass. Fibrous or open-cell insulation allows atmospheric moisture infiltration, freezing into solid ice that buckles the jacketing and causes boiling runaway.

### 4. `strainers_traps.py` (Line Filtration & Steam Systems)
- **Pump Suction NPSHr Protection**: Pump suction strainers with mesh finer than 40-mesh starve pump Net Positive Suction Head required ($NPSH_r$), triggering a cavitation trap.
- **Filter Micron Rating**: Prohibits micron rating downgrades (e.g. candidate $25\ \mu\text{m} >$ required $10\ \mu\text{m}$) that allow erosive particulate passage into mechanical seals.
- **Thread Type Incompatibility**: Thread geometry mismatches (e.g. `NPT` vs `BSPT`) cannot create pressure-tight seals and are blocked as leakage traps.
