# Rotating Machinery, Electric Drive & Shaft Sealing Rules

The `rules/rotating` module encodes strict operational constraints for pumps, compressors, electric drives, rolling element bearings, and mechanical seal flush plans based on **API 610, API 617, API 618, API 682, API 692, IS/IEC 60079, and ISO 15**.

---

## File Breakdown & Mechanical Invariants

### 1. `pumps.py` (API 610 / ISO 13709 Centrifugal Process Pumps)
- **Mounting Configuration (OH1 vs. OH2)**: For hydrocarbon pump temperatures $> 150^\circ\text{C}$, substituting an `OH1` foot-mounted pump for an `OH2` centerline-mounted pump triggers thermal growth shaft misalignment, destroying bearings and seals within hours.
- **API 610 Material Classes Hierarchy**:
  $$\text{S-1 (Cast Iron)} < \text{S-3 (Carbon Steel)} < \text{S-5 (12\% Cr)} < \text{S-6 (Sour 12\% Cr)} < \text{C-6 (12\% Cr SS)} < \text{A-8 (SS 316)} < \text{D-1 (Duplex)} < \text{D-2 (Super Duplex)}$$
  Downgrades are blocked as unapproved metallurgical compromises.
- **Wear Ring Galling Differential Invariant (API 610 Clause 6.7.2)**: To prevent catastrophic galling seizure and rotor lockup, mating casing and impeller wear rings must maintain a minimum hardness differential of **$\ge 50\text{ HB}$**.
- **Delivery Flow Rate**: Rejects replacement pumps whose flow delivery capacity is lower than process suction demands ($Q_c < Q_q$).

### 2. `compressors.py` (API 618 Reciprocating & API 617 Centrifugal Units)
- **API 618 Cylinder Valve Inversion Trap**: Reciprocating compressor cylinder valves are strictly directional. Installing a discharge valve into a suction port prevents fresh gas admission and causes extreme re-compression gas heating ($> 250^\circ\text{C}$), detonating the cylinder head.
- **API 692 Dry Gas Seals (DGS)**: In toxic or flammable high-pressure gas service, downgrading a tandem dual dry gas seal with an inert $N_2$ buffer to a single dry gas seal is blocked as an explosive gas escape trap.
- **API 617 Sour Impeller Metallurgy**: High-strength precipitation-hardened steels (`17-4PH`) in sour hydrocarbon duty mandate `H1150M` double-aging to prevent catastrophic impeller burst.

### 3. `motors.py` (IS/IEC 60079 & IEEE 841 Electric Drives)
- **Hazardous Area Ex Protection**: In refinery Zone 1 or Zone 2 hazardous areas, motors must carry flameproof certification (`Ex d IIC T4 Gb`). Proposing standard industrial non-Ex motors into hazardous zones is blocked as a **Fatal Vapor Ignition Trap**.
- **Pole Count / Synchronous Speed Invariant**: Substituting a 2-pole ($3000\text{ RPM}$) motor for a 4-pole ($1500\text{ RPM}$) pump drive quadruples dynamic head ($H \propto N^2$), rupturing pump casings and downstream piping.
- **Electrical Parity**: Strictly enforces voltage, frequency ($50\text{ Hz}$ Indian grid), and rated kW output capacity.

### 4. `seals.py` (API 682 Mechanical Seals & Flush Plans)
- **API 682 Flush Plan Downgrade**: Dual pressurized barrier systems (`Plan 53A`, `Plan 53B`, `Plan 53C`, `Plan 54`) maintain clean external barrier fluid above process stuffing box pressure. Downgrading to single unpressurized seals (`Plan 11`, `Plan 21`, `Plan 32`) in toxic, carcinogenic, or light hydrocarbon duty is blocked as a toxic seal blowout trap.
- **Elastomer O-Ring Hierarchy**:
  $$\text{NBR / Nitrile } (100^\circ\text{C max}) < \text{EPDM } (140^\circ\text{C}) < \text{Viton / FKM } (200^\circ\text{C}) < \text{Kalrez / FFKM } (315^\circ\text{C})$$

### 5. `bearings.py` (ISO 15 Rolling Element Bearings)
- **Radial Internal Clearance Invariant**:
  $$\text{C2 (Tight)} < \text{CN (Normal)} < \text{C3 (Increased)} < \text{C4 (Extra Increased)}$$
  In high-temperature pumps and motors, operating heat expands the shaft and bearing inner ring. Substituting normal clearance (`CN`) where `C3` is specified eliminates running clearance, causing thermal seizure and shaft snap.
- **Bearing Type Invariant**: Roller bearings (high radial load) and angular contact ball bearings (thrust load) cannot cross-substitute.
