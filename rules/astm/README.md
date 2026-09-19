# ASTM Standards & Metallurgy Graph Module (`rules/astm/`)

This directory codifies the **American Society for Testing and Materials (ASTM)** material specifications into deterministic metallurgical verification routines and Directed Acyclic Graph (DAG) traversals.

---

## 1. File-by-File Breakdown

### `metallurgy_dag.py` — Metallurgical Directed Acyclic Graph Engine
- **Purpose:** Models the partial ordering of metallurgical compatibility across carbon steels, low-temperature alloys, stainless steels, and exotic nickel alloys.
- **Key Classes & Data Structures:**
  - `METALLURGY_DAG`: A directed graph where directed edges $A ightarrow B$ indicate that alloy $B$ is a certified metallurgical superset (upgrade) of alloy $A$.
  - Material Families:
    - **Carbon Steel (CS):** ASTM A105 (Forgings), ASTM A106 Gr B/C (Seamless Pipe), ASTM A216 WCB/WCC (Castings), ASTM A234 WPB (Fittings).
    - **Low-Temp Carbon Steel (LTCS):** ASTM A350 LF2 (Forgings), ASTM A333 Gr 6 (Pipe), ASTM A352 LCC (Castings). Rated down to $-46^\circ	ext{C}$.
    - **Austenitic Stainless Steel (SS):** ASTM A182 F304/F304L, ASTM A182 F316/F316L (Molybdenum-bearing for pitting resistance), ASTM A182 F321/F347 (Titanium/Niobium stabilized against intergranular corrosion).
    - **Duplex & Super Duplex:** ASTM A182 F51 (2205 Duplex), ASTM A182 F53 (2507 Super Duplex, PREN $> 42$).
    - **Nickel Alloys:** Inconel 625 (UNS N06625), Hastelloy C-276, Monel 400.
- **Key Functions:**
  - `_find_material_info(name)`: Canonicalizes trade names and grades.
  - `check_metallurgy_compatibility(query_mat, candidate_mat, service_env)`:
    - Evaluates whether candidate material can safely substitute query material.
    - **Inversion Prohibitions:** Rejects downgrade substitutions (e.g., CS in place of SS316L in acidic/corrosive service).
    - **Sensitization Checks:** Rejects non-stabilized austenitic stainless steels (e.g., standard 304) when operating in the sensitization carbide precipitation range ($425^\circ	ext{C} - 860^\circ	ext{C}$).

### `fasteners.py` — ASTM A193 / A194 / A320 Bolting Integrity
- **Purpose:** Evaluates pressure vessel and flange stud bolts and nuts for tensile strength, low-temperature toughness, and sour gas compatibility.
- **Key Functions:**
  - `check_fastener_integrity(query_bolt, candidate_bolt, query_nut, candidate_nut, temp_c, sour_service)`:
    - **High-Temperature Bolting (ASTM A193):**
      - Grade B7 (Cr-Mo steel, $-29^\circ	ext{C}$ to $400^\circ	ext{C}$), paired with ASTM A194 Gr 2H nuts.
      - Grade B16 (Cr-Mo-V alloy steel, creep resistant up to $525^\circ	ext{C}$), paired with ASTM A194 Gr 7 nuts.
      - Grade B8 / B8M (Austenitic SS304 / SS316), paired with ASTM A194 Gr 8 / 8M nuts.
    - **Low-Temperature Bolting (ASTM A320):**
      - Grade L7 / L7M (Impact tested down to $-101^\circ	ext{C}$). Mandatory substitution for Grade B7 when design temperature $< -29^\circ	ext{C}$.
    - **NACE Sour Service Bolting:**
      - Restricts bolting to Grade B7M / L7M with maximum hardness $\le 22	ext{ HRC}$ and 100% hardness testing per NACE MR0175. Standard B7 studs in sour gas environment trigger catastrophic Sulfide Stress Cracking (SSC).

---

## 2. Theoretical Metallurgy & Concepts for Juniors

### 1. Pitting Resistance Equivalent Number (PREN):
$$	ext{PREN} = \% 	ext{Cr} + 3.3(\% 	ext{Mo} + 0.5\% 	ext{W}) + 16(\% 	ext{N})$$
- PREN measures resistance to localized chloride pitting.
- Standard 304 SS: $	ext{PREN} pprox 18$
- Standard 316L SS: $	ext{PREN} pprox 23-25$
- Duplex 2205: $	ext{PREN} pprox 35$
- Super Duplex 2507: $	ext{PREN} \ge 42$
- *Junior takeaway:* A material with higher PREN can substitute for lower PREN in seawater/chloride service, but never the reverse.

### 2. Low-Temperature Ductile-to-Brittle Transition (DBTT):
- Carbon steels exhibit body-centered cubic (BCC) crystalline structure, undergoing sudden catastrophic brittle failure below their DBTT.
- ASTM A105 is limited to $-29^\circ	ext{C}$. For lower temperatures down to $-46^\circ	ext{C}$, fine-grained normalized ASTM A350 LF2 with Charpy V-Notch impact testing is mandatory.

---

## 3. Code Example

```python
from rules.astm.metallurgy_dag import check_metallurgy_compatibility
from rules.astm.fasteners import check_fastener_integrity

# Test metallurgical upgrade (A105 CS -> A350 LF2 LTCS)
compat = check_metallurgy_compatibility(
    query_mat="ASTM A105",
    candidate_mat="ASTM A350 LF2",
    service_env="GENERAL_HYDROCARBON"
)
print(compat["tier"])  # DynamicCompatibilityTier.TIER_2_SUPERSET

# Test low-temperature fastener safety
bolt_check = check_fastener_integrity(
    query_bolt="ASTM A320 L7",
    candidate_bolt="ASTM A193 B7",  # Dangerous downgrade at -40C
    query_nut="ASTM A194 7",
    candidate_nut="ASTM A194 2H",
    temp_c=-40.0,
    sour_service=False
)
print(bolt_check["is_compatible"])  # False
print(bolt_check["violations"])     # ['B7_BOLTING_NOT_SUITABLE_BELOW_MINUS_29C']
```
