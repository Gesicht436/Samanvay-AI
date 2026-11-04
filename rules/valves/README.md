# Industrial Valves & Overpressure Protection Rules

The `rules/valves` module implements critical flow isolation, overpressure relief, fire containment, and valve trim durability rules based on **API 600, API 6D, API 607, API 609, API 594, API 520, API 526, and ASME Section VIII**.

---

## File Breakdown & Valve Standards

### 1. `trim.py` (API 600 Steel Gate Valve Trim Ladder)
- **Standard Trim Order**:
  $$\text{Trim 1 (13\% Cr 410 SS)} < \text{Trim 8 (410 + Stellite Universal)} < \text{Trim 5 (Full Stellite Hardface)} < \text{Trim 12 (316 + Stellite Sour)} < \text{Trim 16 (Monel HF Alkylation)}$$
- **Trim Downgrade Rapid Washout Trap**: Demoting Trim 5 or Trim 8 to Trim 1 in abrasive, erosive, or high-velocity slurry causes rapid seat wire-drawing and internal passing, blocked as **Tier 3 (Incompatible)**.
- **Trim Upgrade**: Upgrading from Trim 1 to Trim 8 (hardfaced seats) is permitted as a safe drop-in replacement.

### 2. `bore.py` (API 6D Pipeline Scraping & Piggability)
- **Full Bore (FB) vs. Reduced Bore (RB)**: In cross-country hydrocarbon transmission pipelines requiring regular operational cleaning or intelligent inline inspection (ILI), installing a Reduced Bore valve is strictly blocked as a **Pipeline PIG Blockage Trap**.
- **Full Bore Replacement**: Full bore valves can replace reduced bore valves as direct equivalents ($Score = 0.98$).

### 3. `fire_safe.py` (API 607 / API 6FA / API 609 Fire Safety)
- **Hydrocarbon Fire Disaster Trap**: In flammable hydrocarbon refinery service, valves must carry certified fire-safe testing per **API 607 / ISO 10497** (retaining tight metal-to-metal shutoff after 30 minutes in a $750^\circ\text{C}-1000^\circ\text{C}$ furnace fire). Supplying a standard soft-seated non-fire-safe valve is a life-safety violation blocked as **Tier 3**.
- **API 609 Butterfly Valve Categories**:
  - **Category A**: Concentric resilient rubber-lined valves (utility/water duty).
  - **Category B**: High-performance double/triple offset metal-seated valves. Substituting Category A into Category B duty leads to immediate elastomer blowout.
- **API 594 Check Valves**: Retainerless body designs mandated for fugitive emission prevention.

### 4. `psv.py` (API 520 / API 526 Pressure Safety Relief Valves)
- **API 526 Orifice Area Hierarchy**:
  $$D < E < F < G < H < J < K < L < M < N < P < Q < R < T$$
- **Overpressure Vessel Detonation Trap**: Proposing a relief valve with an orifice letter lower than required (e.g., Orifice D for Orifice F) severely restricts emergency volumetric venting capacity during a runaway thermal fire case, leading to catastrophic vessel rupture.
- **Cold Differential Test Pressure (CDTP)**: Set pressure tolerance deviation exceeding $\pm 0.1\text{ bar}$ is rejected.

### 5. `rupture_disks.py` (ASME Section VIII Div 1 UG-127 & ISO 4126-2)
- **Non-Fragmenting Mandate Upstream of PSVs**: Installing a fragmenting rupture disk upstream of a safety relief valve is blocked as a **PSV Nozzle Clogging Trap**. When a fragmenting disk bursts, torn metallic petals shear off and lodge inside the downstream PSV nozzle, jamming the relief disc shut.
- **Reverse Buckling vs. Forward Acting**: In pulsating cyclic pressure duty, forward-acting tension-loaded disks suffer premature metal fatigue. Reverse buckling disks are required.
