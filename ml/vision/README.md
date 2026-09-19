# Document AI, Vision & Metallurgical MTC Engine (`ml/vision/`)

This directory processes scanned paper and digital **Material Test Certificates (MTCs)** per **EN 10204 Type 3.1 / 3.2**, performing automated optical character recognition, table extraction, and metallurgical chemistry verification.

---

## 1. File-by-File Breakdown

### `ocr_engine.py` — Dual-Path Document OCR Engine
- **Purpose:** Ingests PDF and image documents, dynamically choosing between ultra-fast digital stream parsing and computer vision OCR.
- **Key Classes:**
  - `OCREngine`:
    - `process_document(file_bytes: bytes, filename: str) -> Dict[str, Any]`:
      - **Fast-Path (PyMuPDF / fitz):** Inspects the PDF file stream. If native digital text layers are detected with high confidence ($> 85\%$ readable alphanumeric density), extracts text and table layout directly in $< 10\text{ ms}$.
      - **Vision Fallback (PaddleOCR PP-OCRv4):** If the PDF is a scanned bitmap or image (JPEG/PNG/TIFF), renders pages to 300 DPI images and invokes the computer vision pipeline.
      - **Image Preprocessing:** Deskewing, morphological filtering, Otsu adaptive threshold binarization, and Contrast Limited Adaptive Histogram Equalization (CLAHE) to handle poor scans, crumpled pages, and blue mill ink stamps.

### `mtc_parser.py` — EN 10204 Type 3.1 Inspection Certificate Parser
- **Purpose:** Extracts structured metallurgical and mechanical property records from raw OCR tokens.
- **Key Classes:**
  - `MTCParser`:
    - `parse_mtc(ocr_result: Dict[str, Any]) -> MTCRecord`:
      - Extracts **Heat / Melt Number** (e.g. `HT-8921A`).
      - Extracts **Chemical Ladle / Spectral Analysis:** $\% \text{C}, \% \text{Mn}, \% \text{Si}, \% \text{P}, \% \text{S}, \% \text{Cr}, \% \text{Mo}, \% \text{Ni}, \% \text{V}, \% \text{Cu}, \% \text{Ti}, \% \text{Nb}$.
      - Extracts **Mechanical Tensile Properties:** Tensile Strength ($R_m$ in MPa/ksi), Yield Strength ($R_{eH} / R_{p0.2}$ in MPa), Elongation percentage ($A\%$), and Hardness (HBW / HRC).
      - Extracts **Impact Toughness:** Charpy V-Notch test temperatures (e.g. $-46^\circ\text{C}$) and absorbed energy values (Joules).

### `chemistry.py` — Metallurgical Chemistry & Weldability Engine
- **Purpose:** Validates extracted elemental chemistry against ASTM chemical thresholds and computes metallurgical safety indexes.
- **Key Functions:**
  - `compute_carbon_equivalent(composition) -> float`:
    - Computes International Institute of Welding Carbon Equivalent:
      $$CE_{IIW} = \% \text{C} + \frac{\% \text{Mn}}{6} + \frac{\% \text{Cr} + \% \text{Mo} + \% \text{V}}{5} + \frac{\% \text{Ni} + \% \text{Cu}}{15}$$
    - Computes Ito-Bessyo cold cracking parameter ($P_{cm}$) for low-carbon pipeline steels:
      $$P_{cm} = \% \text{C} + \frac{\% \text{Si}}{30} + \frac{\% \text{Mn} + \% \text{Cu} + \% \text{Cr}}{20} + \frac{\% \text{Ni}}{60} + \frac{\% \text{Mo}}{15} + \frac{\% \text{V}}{10} + 5(\% \text{B})$$
  - `classify_weldability(ce) -> str`:
    - $CE \le 0.35$: Excellent weldability; no preheat required.
    - $0.35 < CE \le 0.43$: Good weldability; minor preheat for thick sections.
    - $CE > 0.43$: High crack risk; mandatory preheating ($150^\circ\text{C}-250^\circ\text{C}$) and low-hydrogen electrodes.
  - `compute_pren(composition) -> float`:
    - Calculates Pitting Resistance Equivalent Number for stainless/duplex steels:
      $$\text{PREN} = \% \text{Cr} + 3.3(\% \text{Mo}) + 16(\% \text{N})$$
  - `validate_composition(composition, grade)`: Checks each element against ASTM standard limits (e.g. ASTM A105 max Carbon $0.35\%$, max Manganese $1.06\%$, max Phosphorus $0.035\%$, max Sulfur $0.040\%$).

---

## 2. Engineering Standards for Juniors

1. **EN 10204:2004:** *Metallic Products — Types of Inspection Documents*. Learn the difference between **Type 2.1** (Declaration of compliance), **Type 2.2** (Non-specific test report), **Type 3.1** (Validated by manufacturer's authorized inspection representative independent of production), and **Type 3.2** (Validated by independent third-party inspection agency like Lloyd's, DNV, or TUV).
2. **ASTM A105 / A182 / A350:** Review Table 1 (Chemical Requirements) and Table 2 (Mechanical Requirements).

---

## 3. Code Example

```python
from ml.vision.chemistry import compute_carbon_equivalent, classify_weldability, validate_composition

# Sample chemistry from an ASTM A106 Grade B pipe MTC
sample_chemistry = {
    "C": 0.22,
    "Mn": 0.85,
    "Si": 0.25,
    "P": 0.015,
    "S": 0.010,
    "Cr": 0.12,
    "Mo": 0.04,
    "Ni": 0.08,
    "Cu": 0.10,
    "V": 0.02
}

ce = compute_carbon_equivalent(sample_chemistry)
weldability = classify_weldability(ce)
is_valid, violations = validate_composition(sample_chemistry, "ASTM A106 Gr B")

print(f"Carbon Equivalent (CE): {ce:.3f}")        # ~0.412
print(f"Weldability Rating: {weldability}")       # Good (Preheat optional)
print(f"ASTM Chemistry Compliant: {is_valid}")     # True
```
