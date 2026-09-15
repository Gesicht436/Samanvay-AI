# Deterministic Safety Rules, Logistics & Active Learning (`backend/app/matching`)

## 1. Overview
The `matching` package is the core engineering intelligence engine of Samanvay-AI. It combines deterministic safety tolerance validation, inter-CPSE logistics routing, and online active learning.

In hydrocarbon processing facilities, an incorrect equipment substitution can cause fatal explosions, cryogenic fractures, or environmental leaks. Unlike consumer search systems that rely on probabilistic language models, Samanvay-AI enforces safety using **100% deterministic, vectorized engineering rules** derived from international and Indian statutory codes:
- **ASME B16.5 & ASME B16.34**: Pressure rating ladders and flange mating faces.
- **ASTM Standards**: Metallurgy directed acyclic graphs and chemical compatibility.
- **ASME B36.10M / B36.19M**: Pipe wall thickness and schedule invariants.
- **NACE MR0175 / ISO 15156**: Sour service cracking resistance in hydrogen sulfide (H2S) environments.
- **ASME B16.47**: Large diameter flange bolting patterns (Series A vs Series B).
- **Indian Boiler Regulations (IBR 1950)**: Form III-C statutory steam service compliance.
- **IS/IEC 60079 & API 682 & ISO 15**: Flameproof motors, mechanical seals, and industrial bearings.

---

## 2. Directory Structure

```
backend/app/matching/
|-- active_learning.py           # Online dual-indexed feedback cache and dynamic reranker
|-- asme_rules.py                # ASME pressure ladders and ASTM metallurgy directed graph
|-- logistics.py                 # GIS multi-depot Haversine matrix, locks, and CISF gate passes
|-- piping_spec_rules.py         # Pipe schedules, NACE sour service, large flanges, and IBR rules
|-- rotating_rules.py            # Flameproof motors, mechanical seal plans, and bearing clearances
|-- tolerance.py                 # Master candidate pool evaluation and tier assignment orchestrator
`-- README.md                    # This file
```

---

## 3. The Three Equivalence Tiers

Every item evaluated by `tolerance.py` is categorized into one of three strict tiers:

```
[Candidate Item]
       |
       v
Does it violate any physical dimension, lower pressure class, or down-grade metallurgy?
      /          \
    Yes           No
    /              \
[TIER-3: INCOMPATIBLE]   Does it exceed requirements (higher class, superior alloy, heavier wall)?
(Hard safety reject;            /                  \
 unsafe for deployment)        Yes                  No
                               /                     \
                   [TIER-2: SUBSTITUTE]     [TIER-1: IDENTICAL]
                   (Valid safe upgrade;     (100% specification parity;
                    flagged for HITL)        safe direct drop-in)
```

---

## 4. Rule Implementations Explained

### A. ASME Pressure Rating Ladder (`asme_rules.py`)
Standard ASME pressure classes follow an ascending ladder:
`Class 150 < Class 300 < Class 400 < Class 600 < Class 900 < Class 1500 < Class 2500`

- Permitted Upgrade: A requested Class 300 line may safely install a Class 600 valve (Class 600 exceeds the pressure containment rating of Class 300).
- Fatal Downgrade: A requested Class 600 line CANNOT install a Class 300 valve. Doing so risks immediate rupture under line operating pressure.

### B. ASTM Metallurgy Compatibility Graph (`asme_rules.py`)
Component metallurgy is modeled as a Directed Acyclic Graph (DAG):
- Permitted Upgrades:
  - `ASTM A105` (Carbon Steel) -> `ASTM A350 LF2` (Impact tested for low temperature service).
  - `ASTM A105` -> `ASTM A182 F304` or `F316` (Austenitic Stainless Steel for corrosion resistance).
  - `ASTM A105` -> `ASTM A182 F51` (Duplex 2205: higher strength and pitting resistance).
  - `ASTM A105` -> `ASTM A815 S32750` (Super Duplex: extreme PREN > 40 rating).
  - `ASTM A105` -> `INCONEL 625` or `HASTELLOY C-276` (Severe acid/chloride resistance).
- Fatal Downgrade Traps:
  - `ASTM A182 F316` -> `ASTM A105`: Fatal downgrade. Replacing acid-resistant stainless with carbon steel causes rapid wall blowout.
  - `ASTM A182 F316` -> `ASTM A182 F304`: Unsafe downgrade. F304 lacks Molybdenum (2-3% Mo in F316); causes localized pitting in chloride/sour environments.
  - `ASTM A350 LF2` -> `ASTM A105`: Cryogenic safety trap. Standard A105 lacks Charpy V-notch impact testing; shatters under sub-zero temperatures.

### C. Mating Surface Compatibility (`asme_rules.py`)
- Raised Face (RF) flanges mate with spiral wound or sheet gaskets.
- Ring Type Joint (RTJ) flanges have deep trapezoidal grooves for metallic octagonal rings.
- An RTJ flange CANNOT mate with an RF flange; the gasket will fail to compress and blow out.

### D. Piping Schedules & Large Flanges (`piping_spec_rules.py`)
- Pipe Schedules: ASME B36.10M wall thickness ladder (`SCH 10 < SCH 20 < SCH 40/STD < SCH 80/XS < SCH 160 < XXS`). Installing a lighter schedule than requested thins the pressure boundary and is rejected as Tier-3.
- ASME B16.47 Series A vs Series B: For large pipes (26" to 60" NB), Series A (MSS SP-44) and Series B (API 605) have completely different bolt circles and hole counts. They are strictly non-interchangeable.

### E. NACE MR0175 / ISO 15156 Sour Service (`piping_spec_rules.py`)
Natural gas or crude containing hydrogen sulfide (H2S) causes Sulfide Stress Cracking (SSC) in regular steels. A line requiring NACE compliance rejects standard non-NACE materials as Tier-3.

### F. Indian Boiler Regulations (IBR 1950) (`piping_spec_rules.py`)
Steam lines operating under IBR statutory jurisdiction require IBR Form III-C certification by law. Installing a non-IBR certified item into an IBR system constitutes a statutory violation and is rejected.

### G. Rotating Equipment Rules (`rotating_rules.py`)
- Electric Motors: Evaluates IS/IEC 60079-1 flameproof enclosures (`Ex d IIC T4`), power rating (+0% to +25% margin allowed), pole count (2P, 4P, 6P), and synchronous RPM (3000, 1500, 1000).
- Mechanical Seals: Enforces API 682 seal flush plans (Plan 11, Plan 23, Plan 52, Plan 53A, Plan 54).
- Bearings: Evaluates ISO 15 bearing inner bore millimeter dimensions and radial clearance (C3 vs C4 vs CN).

---

## 5. Active Learning & Dynamic Reranker (`active_learning.py`)

To incorporate engineer decisions without waiting for batch model retraining:
1. When an engineer approves or rejects a candidate in the HITL triage UI (`/hitl`), the decision is logged in `ActiveLearningCache`.
2. The cache maintains a dual index:
   - Query Fingerprint Index: Normalized query string (`FLGWNRF4IN300A105`) + Candidate ID.
   - SKU Index: Source SKU code + Candidate ID.
3. During subsequent matching (`apply_dynamic_reranking`):
   - Approved items receive a confidence boost ($\ge 0.95$), an audit badge `[VERIFIED BY HUMAN EXPERT]`, and bubble to Rank #1.
   - Rejected items are demoted to Tier-3 Incompatible, confidence is penalized, and they sink behind valid inventory.

---

## 6. Logistics & Requisition Engine (`logistics.py`)

Connects 12 major Indian CPSE refinery locations across IOCL, ONGC, and BPCL:
- Coordinate Matrix: Panipat, Mathura, Koyali, Paradip, Barauni, Guwahati, Digboi, Hazira, Uran, Mumbai Mahul, Kochi, Bina.
- Haversine Formula: Computes great-circle distance and applies road tortuosity factor ($1.28\times$) for realistic highway routing.
- Cost & Transit Estimation: Calculates road freight charges in INR and estimated transit lead time in days.
- Atomic Reservation Locks: Tracks reserved surplus quantities to prevent two refineries from concurrently claiming the same spare part.
- Digital CISF Gate Pass: Generates printable passes with verification hash and scannable SVG QR codes for refinery gate security.
