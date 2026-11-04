# Raw Ingestion Documents & Ground Truth Benchmarks

The `data/raw` folder contains synthetic EN 10204 Type 3.1 Mill Test Certificates (MTCs) and material delivery challans paired with comprehensive ground truth JSON annotations. These files serve as the benchmark evaluation harness for the OCR and document intelligence pipelines.

---

## File Inventory

### 1. Document Artifacts
- **`sample_mtc_flange_01.pdf`**: Carbon steel weld neck flange (`ASTM A105N`, 4" Class 300 RF, PO `PO-IOCL-PNP-77410`).
- **`sample_mtc_valve_02.pdf`**: Cast steel gate valve (`ASTM A216 WCB`, 2" Class 150 RF, PO `PO-ONGC-HZR-55102`).
- **`sample_mtc_flange_ss_03.pdf`**: Austenitic stainless steel blind flange (`ASTM A182 F316L`, 6" Class 600 RTJ, PO `PO-BPCL-MUM-99301`).
- **`sample_mtc_bolt_04.pdf`**: Alloy steel stud bolts with heavy hex nuts (`ASTM A193 Gr. B7` / `ASTM A194 Gr. 2H`, PO `PO-IOCL-MTH-11029`).
- **`sample_challan_valve_05.pdf`**: Commercial delivery gate pass / delivery challan with dispatch quantities, carrier transport details, and consignee references.

### 2. `sample_mtc_ground_truth.json` (Ground Truth Evaluation Benchmark)
- **Purpose**: Provides exact ground truth values to compute Character Error Rate (CER), Word Error Rate (WER), and field-level precision/recall during automated test runs (`tests/unit/test_ocr_and_mtc.py`).
- **Annotated Fields**:
  - `doc_type`: Standard document classification string.
  - `cert_no` & `po_no`: Strict alphanumeric identifier strings.
  - `material_grade` & `standard`: Governing ASTM/ASME specifications.
  - `heat_no`: Heat/melt number traceability.
  - `chemical`: Array of chemical elements with exact mass fraction percentages (e.g. $\%C$, $\%Mn$, $\%Si$, $\%P$, $\%S$, $\%Cr$, $\%Ni$, $\%Mo$).
  - `mechanical`: Physical test measurements including Yield Strength ($\text{MPa}$), Tensile Strength ($\text{MPa}$), Elongation ($\%$) and Hardness ($\text{HBW}$ / $\text{HRC}$).
