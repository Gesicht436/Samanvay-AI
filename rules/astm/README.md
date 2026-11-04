# ASTM Metallurgy & Fasteners Tolerance Rules

The `rules/astm` module governs material compatibility, corrosion resistance hierarchies, high-temperature creep resistance, and fastener stud-nut mechanical integrity based on **ASTM, ASME Section II, and NACE MR0175/ISO 15156**.

---

## Metallurgy Directed Acyclic Graph (DAG) Hierarchy

```mermaid
graph TD
    CS["Level 0: Carbon Steel<br>(A105, A216 WCB, A106-B, A234 WPB)"] --> LTCS["Level 1: Low-Temp Carbon Steel<br>(A350 LF2, A352 LCB, A333 Gr.6, A420 WPL6)"]
    LTCS --> SS304["Level 2: Austenitic 304 Family<br>(A182 F304/F304L, CF8/CF3, TP304, F321, F347)"]
    SS304 --> SS316["Level 3: Molybdenum Stainless<br>(A182 F316/F316L, CF8M/CF3M, TP316)"]
    SS316 --> DUPLEX["Level 4: Duplex 2205<br>(A182 F51, UNS S31803)"]
    DUPLEX --> SDUPLEX["Level 5: Super Duplex 2507<br>(A182 F53, UNS S32750)"]
    SDUPLEX --> NICKEL["Level 6: Nickel Superalloys<br>(Inconel 625, Hastelloy C-276, Monel 400)"]

    subgraph Creep_Branch ["Cr-Mo High-Temperature Creep Branch"]
        F11["Level 10: 1.25Cr-0.5Mo<br>(A182 F11, WC6, P11)"] --> F22["Level 11: 2.25Cr-1Mo<br>(A182 F22, WC9, P22)"]
        F22 --> F5["Level 12: 5Cr-0.5Mo<br>(A182 F5, C5, P5)"]
        F5 --> F91["Level 13: 9Cr-1Mo-V<br>(A182 F91, C12A, P91)"]
    end
```

---

## File Breakdown

### 1. `metallurgy_dag.py` (Safe-Upgrade Directed Acyclic Graph)
- **Monotonic Upgrade Law**: Moving **UP** the hierarchy (e.g. replacing Carbon Steel with 316L Stainless Steel) is permitted as a safe engineering upgrade (**Tier 2**). Moving **DOWN** the hierarchy is an unapproved downgrade blocked as **Tier 3 (Incompatible)** due to fatal corrosion, stress cracking, or thermal degradation.
- **Creep vs Austenitic Isolation**: Cr-Mo creep steels (`F11`, `F22`, `F91`) operate under high-temperature stress rupture mechanics ($> 450^\circ\text{C}$). Substituting standard austenitic stainless steel into a Cr-Mo line without re-rating is blocked as a high-temperature creep cracking trap.
- **Low-Temperature Toughness Invariant**: In cryogenic service ($< -29^\circ\text{C}$), standard carbon steel (`A105`, `WCB`) undergoes ductile-to-brittle transition; Charpy V-notch tested materials (`A350 LF2`, `A333 Gr.6`) are strictly mandatory.

### 2. `fasteners.py` (ASTM A193 / A194 / A320 Fastener Integrity)
- **Stud-to-Nut Metallurgical Pairing**:
  - `A193 Gr. B7` (High-temp Cr-Mo alloy stud) mandates `ASTM A194 Gr. 2H` (Heavy hex heat-treated carbon steel nut). Pairing B7 studs with standard Grade 2 commercial nuts causes catastrophic thread shear under bolting torque.
  - `A193 Gr. B16` ($450^\circ\text{C}-540^\circ\text{C}$ creep duty) requires `A194 Gr. 7` or `Gr. 4`.
  - `A320 Gr. L7` (Low-temperature $-101^\circ\text{C}$) mandates `A194 Gr. 7` impact-tested nuts.
  - `NACE MR0175` Sour Service: Maximum hardness $22\text{ HRC}$; mandates `A193 Gr. B7M` paired with `A194 Gr. 2HM`.
- **Liquid Metal Embrittlement (LME) Trap**: Above $200^\circ\text{C} - 250^\circ\text{C}$, cadmium-plated, zinc-electroplated, or hot-dip galvanized fasteners suffer molten zinc/cadmium diffusion along grain boundaries, causing rapid intergranular catastrophic fracture. High-temperature lines strictly block galvanized/cadmium bolting.
- **Yield Strength Parity**: Rejects any replacement fastener where candidate yield strength is lower than design specifications.
