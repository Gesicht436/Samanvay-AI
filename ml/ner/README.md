# Named Entity Recognition & Dialect Normalization (`ml/ner/`)

This directory extracts structured mechanical attributes from messy, unstructured ERP item descriptions.

---

## 1. File-by-File Breakdown

### `normalizer.py` — Dialect Normalizer & Text Cleaner
- **Purpose:** Preprocesses raw ERP strings into a standardized canonical vocabulary before NER slot tagging.
- **Key Functions & Classes:**
  - `unicode_normalize(text: str) -> str`: Normalizes text using Unicode NFKC (Compatibility Decomposition followed by Canonical Composition), resolving special characters, fractional symbols (½ $\rightarrow$ 1/2, ¾ $\rightarrow$ 3/4), and non-breaking spaces.
  - `normalize_description(raw_text: str) -> str`:
    - Expands thousands of CPSE abbreviations:
      - `"VLV"`, `"V/"` $\rightarrow$ `"VALVE"`
      - `"CS"` $\rightarrow$ `"CARBON STEEL"`
      - `"SS"`, `"316SS"` $\rightarrow$ `"STAINLESS STEEL 316"`
      - `"150#"`, `"CL150"`, `"150LB"` $\rightarrow$ `"CLASS 150"`
      - `"BW"`, `"B/W"` $\rightarrow$ `"BUTTWELD"`
      - `"SW"` $\rightarrow$ `"SOCKET WELD"`
      - `"RF"` $\rightarrow$ `"RAISED FACE"`
  - `extract_metadata_from_dialect(text: str) -> dict`: Fast regex extraction for standard tokens.
  - `DialectNormalizer`: Object-oriented interface encapsulating domain thesauri.

### `slot_tagger.py` — DeBERTa-v3 Slot Extraction Engine
- **Purpose:** Applies transformer token classification to tag exact slot spans.
- **Key Classes:**
  - `SlotTagger`:
    - `extract_slots(text: str) -> PhysicalAttributes`:
      - Extracts key physical attributes:
        - `item_type`: e.g. `"BALL_VALVE"`, `"PIPE"`, `"FLANGE"`
        - `size`: e.g. `"4 INCH"`, `"DN100"`, `"100 MM"`
        - `pressure_class`: e.g. `150`, `300`, `600`, `900`
        - `material_grade`: e.g. `"ASTM A105"`, `"ASTM A216 WCB"`, `"SS316L"`
        - `schedule`: e.g. `"SCH 40"`, `"SCH 80"`, `"STD"`
        - `facing`: e.g. `"RF"`, `"RTJ"`, `"FF"`
        - `trim`: e.g. `"TRIM 8"`, `"TRIM 5"`
        - `nace_compliant`: Boolean flag based on sour gas keywords.

---

## 2. Theory: Sequence Labeling with DeBERTa-v3

### 1. Disentangled Attention Mechanism:
- Standard BERT represents each word as a single vector summing content and position.
- DeBERTa represents each token with two separate vectors: **Content Vector** and **Relative Position Vector**. Attention between token $i$ and token $j$ is computed across content-to-content, content-to-position, and position-to-content matrices.
- This prevents positional shifts from corrupting token semantics in dense industrial codes like `"4 IN 300# RF"`.

### 2. BIO Tagging Scheme:
- Tokens are tagged using Beginning (`B-`), Inside (`I-`), and Outside (`O-`) annotations:
  - `4`: `B-SIZE`
  - `INCH`: `I-SIZE`
  - `300#`: `B-PRESSURE_CLASS`
  - `RF`: `B-FACING`

---

## 3. Code Example

```python
from ml.ner.normalizer import normalize_description
from ml.ner.slot_tagger import SlotTagger

raw_erp_line = "VLV BALL 6\" 600# A105 RF FB TR8 NACE"

# 1. Normalize dialect abbreviations
cleaned = normalize_description(raw_erp_line)
print("Normalized:", cleaned)
# Output: "VALVE BALL 6 INCH CLASS 600 ASTM A105 RAISED FACE FULL BORE TRIM 8 NACE"

# 2. Extract structured physical attributes
tagger = SlotTagger()
attributes = tagger.extract_slots(cleaned)
print("Item Type:", attributes.item_type)       # BALL_VALVE
print("Size:", attributes.size)                 # 6 INCH
print("Class:", attributes.pressure_class)      # 600
print("Material:", attributes.material_grade)   # ASTM A105
print("NACE:", attributes.nace_compliant)       # True
```
