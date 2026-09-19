# Datasets & Training Corpora (`datasets/`)

This directory maintains the training, evaluation, and benchmark datasets used by **Samanvay-AI**'s machine learning, natural language processing, and computer vision models.

---

## 1. Directory Structure

```
datasets/
├── inventory_catalog.csv     # 5,001 items multi-CPSE master catalog
├── golden_benchmarks.json    # 100+ expert-annotated matching benchmark pairs
├── ocr_payloads.json         # Material Test Certificate OCR payloads
└── generators/               # Dataset generation scripts & synthetic corruptors
    └── generate_datasets.py  # Procedural dialect and catalog generator
```

---

## 2. Dataset Synthesis Methodology

Public sector hydrocarbon catalogs cannot be published publicly due to national critical infrastructure confidentiality. To train and evaluate models with 100% realism without compromising sovereign operational security, Samanvay-AI utilizes **Domain-Constrained Synthetic Generation**:

1. **Vocabulary Sampling:** Real mechanical engineering vocabularies sampled from ASME B16.5, ASTM A105/A182/A216, API 6D/600/610, and TEMA.
2. **Dialect Simulation:**
   - **IOCL Style:** Extreme truncation, space-delimited abbreviations (`"VLV CHK 2IN 600# A105 SW"`).
   - **ONGC Style:** Comma-separated, verbose offshore specifications with explicit NACE tags (`"VALVE, CHECK, 2\", CL 600, ASTM A105, SOCKET WELD, NACE MR0175"`).
   - **Metric SAP Style:** European nominal sizes and pressure bars (`"DN50 PN100 CHECK VALVE A105"`).
3. **Noise Injection:** Controlled character drops, OCR character confusion (`O` vs `0`, `I` vs `1`), metric/imperial mixing (`100mm` vs `4\"`), and missing optional fields.

---

## 3. Regenerating Datasets

To regenerate or scale the datasets up to 50,000+ items:

```bash
# Run the dataset generator
python datasets/generators/generate_datasets.py --count 10000 --output datasets/inventory_catalog.csv
```
