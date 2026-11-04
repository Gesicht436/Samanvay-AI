# Process Piping & Pipeline Engineering Rules

The `rules/piping` module implements mechanical design rules, wall thickness hierarchies, sour service integrity, and lethal fluid containment based on **ASME B31.3, API 5L, ASME B36.10M/B36.19M, NACE MR0175/ISO 15156, ASTM A269, and EJMA**.

---

## File Breakdown & Process Invariants

### 1. `schedules.py` (ASME B36.10M / B36.19M Wall Thickness Ladder)
- **Schedule Ladder**:
  $$\text{SCH 5} < \text{SCH 10} < \text{SCH 20} < \text{SCH 30} < \text{STD / SCH 40} < \text{SCH 60} < \text{XS / SCH 80} < \text{SCH 100} < \text{SCH 120} < \text{SCH 160} < \text{XXS}$$
- **Down-Schedule Prohibition**: Specifying a thinner wall pipe than required by line design pressure and corrosion allowance triggers a catastrophic internal burst hazard blocked as **Tier 3 (Incompatible)**.
- **Schedule Upgrade**: Upgrading to a heavier schedule (e.g. `SCH 40` $\rightarrow$ `SCH 80`) is permitted as **Tier 2 (Substitute)** provided flow velocity reductions are within operational bounds.

### 2. `line_pipe.py` (API 5L & ASME B31.3 Fluid Services)
- **API 5L PSL 1 vs. PSL 2**: In high-pressure gas transmission pipelines, `PSL 1` line pipe lacks mandatory Charpy V-notch fracture toughness testing and chemistry ceilings ($CE \le 0.43$). Substituting PSL 1 for PSL 2 is blocked as a brittle pipeline rupture trap.
- **ASME B31.3 Category M Lethal Toxic Service**: In lethal fluid service, threaded NPT joints are strictly prohibited; $100\%$ radiographed full-penetration buttwelds are mandatory.
- **Seamless vs. Welded Pipe**: High-pressure hydrogen lines and critical refinery transfer lines prohibit welded pipe (`ERW`, `LSAW`) in place of seamless (`SMLS`).

### 3. `nace.py` (NACE MR0175 / ISO 15156 Sour Hydrocarbon Service)
- **Sour Gas Hardness Ceiling**: Wet $H_2S$ sour hydrocarbon duty induces Sulfide Stress Cracking (SSC) and Hydrogen-Induced Cracking (HIC) in hardened steels. All carbon steels in sour duty must be certified with hardness $\le 22\text{ HRC}$.
- **Non-NACE Rejection**: Supplying standard commercial steel without NACE certification into sour duty triggers an immediate **Tier 3 (Hard Reject)**.

### 4. `tubing.py` (ASTM A269 Instrumentation Small-Bore Tubing)
- **Metric vs. Fractional Imperial Blowout Trap**: Mating metric compression fittings ($12.0\text{ mm}$ OD) onto imperial tubing ($1/2" = 12.7\text{ mm}$ OD) or vice versa prevents proper dual-ferrule swaging, causing violent tube blowout under high impulse pressure (up to $6,000\text{ PSI}$).
- **Ferrule Swaging Hardness Invariant**: Instrument tubing must be fully annealed with maximum hardness $\le 90\text{ HRB}$. Tubes exceeding $90\text{ HRB}$ cannot coin into the front ferrule, vibrating loose under plant pulsation.

### 5. `expansion_joints.py` (EJMA Standards & Flexible Hoses)
- **Tied vs. Unrestrained Bellows**: Tied metallic expansion joints contain internal pressure thrust forces ($F = P \times A$). Installing an unrestrained bellows where tied joints are required shears anchor guides and ruptures the thin convoluted bellows membrane.
- **Hose Braid Integrity**: High-pressure cyclic duty requires double-braided flexible metallic hoses (`ISO 10380`); single-braid downgrades are rejected.
