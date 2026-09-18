export interface MTCInspectionData {
  document_id: string;
  filename: string;
  doc_type: string;
  is_scanned: boolean;
  confidence_score: number;
  requires_hitl: boolean;
  is_incomplete: boolean;
  missing_attributes: string[];
  extracted_attributes: {
    item_type: string;
    size_nb_mm: number;
    pressure_class: number;
    schedule: string;
    metallurgy: string;
    facing_end: string;
    standard: string;
    properties: Record<string, any>;
  };
  chemistry: Record<string, number>;
  carbon_equivalent_iiw: number;
  weldability: 'STANDARD_WELDABLE' | 'PREHEAT_REQUIRED' | 'HIGH_CRACKING_RISK';
  pren: number | null;
  mechanical: {
    yield_strength_mpa?: number;
    tensile_strength_mpa?: number;
    elongation_pct?: number;
    impact_joules_charpy?: number;
    hardness_hb?: number;
  };
  astm_conformance: boolean;
  warnings: string[];
  raw_text: string;
  bounding_boxes: Array<{
    text: string;
    confidence: number;
    box: [number, number, number, number]; // [x0, y0, x1, y1] normalized 0..100
    fieldKey?: string;
  }>;
}

export const MTC_PRESETS: Record<string, MTCInspectionData> = {
  'preset-1': {
    document_id: 'doc-lt-a105-01',
    filename: 'MTC_L&T_Hazira_ASTM_A105_WN_Flange.pdf',
    doc_type: 'MTC_EN10204_3.1',
    is_scanned: false,
    confidence_score: 0.984,
    requires_hitl: false,
    is_incomplete: false,
    missing_attributes: [],
    extracted_attributes: {
      item_type: 'FLANGE',
      size_nb_mm: 100.0,
      pressure_class: 300,
      schedule: 'SCH 40',
      metallurgy: 'ASTM A105',
      facing_end: 'RF',
      standard: 'EN 10204 3.1',
      properties: {
        certificate_no: 'MTC/2026/5516',
        heat_no: 'HT-2025-20300',
        po_no: 'PO-MOPNG-505403',
        manufacturer: 'Larsen & Toubro Heavy Engineering, Hazira',
        tpi_agency: 'Bureau Veritas (India) Private Limited',
      },
    },
    chemistry: {
      C: 0.22,
      Mn: 0.85,
      Si: 0.25,
      P: 0.015,
      S: 0.012,
      Cr: 0.15,
      Ni: 0.1,
      Mo: 0.05,
      V: 0.02,
      Cu: 0.1,
    },
    carbon_equivalent_iiw: 0.41,
    weldability: 'STANDARD_WELDABLE',
    pren: null,
    mechanical: {
      yield_strength_mpa: 310.0,
      tensile_strength_mpa: 520.0,
      elongation_pct: 26.0,
      hardness_hb: 165.0,
    },
    astm_conformance: true,
    warnings: [],
    raw_text: `LARSEN & TOUBRO HEAVY ENGINEERING WORKS, HAZIRA
INSPECTION CERTIFICATE EN 10204 TYPE 3.1
Certificate No: MTC/2026/5516 | Date: 12-FEB-2026
Purchase Order: PO-MOPNG-505403 | Line Item: 0010
Third Party Inspection: Bureau Veritas (India) Private Limited

PRODUCT DESCRIPTION:
WELD NECK FLANGE 4" (DN 100) CLASS 300 RF SCH 40
Material Specification: ASTM A105 / ASME SA105 (2023 Edition)
Melt / Cast Heat No: HT-2025-20300 | Quantity: 24 PCS

CHEMICAL COMPOSITION (LADLE ANALYSIS, WEIGHT %):
C: 0.22% | Mn: 0.85% | Si: 0.25% | P: 0.015% | S: 0.012%
Cr: 0.15% | Ni: 0.10% | Mo: 0.05% | V: 0.02% | Cu: 0.10%
Carbon Equivalent (IIW Formula): 0.41% [WELDABLE]

MECHANICAL TEST RESULTS:
Yield Strength (Re / 0.2% Proof): 310 MPa (Min. Spec: 250 MPa)
Tensile Strength (Rm): 520 MPa (Spec Range: 485 - 655 MPa)
Elongation (A5 gauge): 26.0% (Min. Spec: 22%)
Brinell Hardness: 165 HBW (Max Spec: 187 HBW)

NON-DESTRUCTIVE & PRESSURE TEST:
Ultrasonic Test (UT): 100% Volumetric OK as per ASME Sec VIII Div 1
Hydrostatic Test: 77.5 bar (1125 psi) held 120s - No Leakage.
Certified by Quality Assurance Chief Metallurgist & TPI Inspector.`,
    bounding_boxes: [
      { text: 'Certificate No: MTC/2026/5516', confidence: 0.99, box: [10, 8, 45, 12], fieldKey: 'certificate_no' },
      { text: 'Heat No: HT-2025-20300', confidence: 0.98, box: [10, 26, 48, 30], fieldKey: 'heat_no' },
      { text: 'Material: ASTM A105', confidence: 0.99, box: [10, 22, 50, 26], fieldKey: 'metallurgy' },
      { text: 'C: 0.22% | Mn: 0.85%', confidence: 0.97, box: [10, 36, 60, 40], fieldKey: 'chemistry' },
      { text: 'Yield Strength: 310 MPa', confidence: 0.98, box: [10, 52, 55, 56], fieldKey: 'yield_strength_mpa' },
      { text: 'Tensile Strength: 520 MPa', confidence: 0.98, box: [10, 56, 55, 60], fieldKey: 'tensile_strength_mpa' },
      { text: 'Carbon Equivalent: 0.41%', confidence: 0.96, box: [10, 44, 52, 48], fieldKey: 'carbon_equivalent' },
    ],
  },

  'preset-2': {
    document_id: 'doc-bhel-a350-02',
    filename: 'MTC_BHEL_Trichy_ASTM_A350_LF2_Cryogenic_Valve.pdf',
    doc_type: 'MTC_EN10204_3.2',
    is_scanned: false,
    confidence_score: 0.975,
    requires_hitl: false,
    is_incomplete: false,
    missing_attributes: [],
    extracted_attributes: {
      item_type: 'GATE_VALVE',
      size_nb_mm: 150.0,
      pressure_class: 600,
      schedule: 'SCH 80',
      metallurgy: 'ASTM A350 LF2',
      facing_end: 'RTJ',
      standard: 'EN 10204 3.2',
      properties: {
        certificate_no: 'BHEL/QA/2026/8941',
        heat_no: 'HT-LF2-9014',
        po_no: 'PO-ONGC-URAN-9921',
        manufacturer: 'Bharat Heavy Electricals Limited (BHEL), Tiruchirappalli',
        tpi_agency: 'Engineers India Limited (EIL)',
      },
    },
    chemistry: {
      C: 0.20,
      Mn: 1.15,
      Si: 0.28,
      P: 0.012,
      S: 0.008,
      Cr: 0.12,
      Ni: 0.22,
      Mo: 0.06,
      V: 0.02,
      Cu: 0.15,
    },
    carbon_equivalent_iiw: 0.45,
    weldability: 'PREHEAT_REQUIRED',
    pren: null,
    mechanical: {
      yield_strength_mpa: 285.0,
      tensile_strength_mpa: 510.0,
      elongation_pct: 28.0,
      impact_joules_charpy: 38.0,
      hardness_hb: 170.0,
    },
    astm_conformance: true,
    warnings: [
      'Weldability alert: IIW Carbon Equivalent (0.45%) requires minimum 100°C preheat per ASME Sec IX before welding.',
    ],
    raw_text: `BHARAT HEAVY ELECTRICALS LIMITED, TRICHY
TEST CERTIFICATE EN 10204 3.2 (JOINT INSPECTION)
Certificate No: BHEL/QA/2026/8941 | Date: 18-JAN-2026
Client: ONGC Uran Gas Processing Terminal | PO: PO-ONGC-URAN-9921
TPI Inspection Agency: Engineers India Limited (EIL)

PRODUCT SPECIFICATION:
GATE VALVE BODY FORGING 6" CLASS 600 RTJ SCH 80
Specification: ASTM A350 Grade LF2 Class 1 (Cryogenic Duty)
Melt Heat Number: HT-LF2-9014 | Condition: Normalized and Tempered

CHEMICAL PROPERTIES (% WT):
C: 0.20 | Mn: 1.15 | Si: 0.28 | P: 0.012 | S: 0.008
Cr: 0.12 | Ni: 0.22 | Mo: 0.06 | V: 0.02 | Cu: 0.15
IIW Carbon Equivalent: 0.45% (Preheat Protocol Mandated)

MECHANICAL & CHARPY V-NOTCH IMPACT (-46°C):
Yield Strength: 285 MPa (Min: 250 MPa)
Tensile Strength: 510 MPa (Range: 485-655 MPa)
Elongation: 28.0% (Min: 22%)
Charpy V-Notch Average at -46°C: 38.0 Joules (ASTM A350 Spec Min: 20 J individual, 27 J avg)
Hardness: 170 HBW (NACE MR0175 Max: 187 HBW)`,
    bounding_boxes: [
      { text: 'Certificate No: BHEL/QA/2026/8941', confidence: 0.98, box: [10, 8, 48, 12], fieldKey: 'certificate_no' },
      { text: 'Heat No: HT-LF2-9014', confidence: 0.99, box: [10, 25, 42, 29], fieldKey: 'heat_no' },
      { text: 'Material: ASTM A350 Grade LF2', confidence: 0.99, box: [10, 21, 55, 25], fieldKey: 'metallurgy' },
      { text: 'Charpy Impact: 38.0 J at -46C', confidence: 0.96, box: [10, 60, 60, 64], fieldKey: 'impact_joules_charpy' },
    ],
  },

  'preset-3': {
    document_id: 'doc-pennar-ss316l-03',
    filename: 'MTC_Pennar_ASTM_A182_F316L_Flange.pdf',
    doc_type: 'MTC_EN10204_3.1',
    is_scanned: false,
    confidence_score: 0.991,
    requires_hitl: false,
    is_incomplete: false,
    missing_attributes: [],
    extracted_attributes: {
      item_type: 'FLANGE',
      size_nb_mm: 50.0,
      pressure_class: 150,
      schedule: 'SCH 10S',
      metallurgy: 'ASTM A182 F316L',
      facing_end: 'RF',
      standard: 'EN 10204 3.1',
      properties: {
        certificate_no: 'PEN/MTC/2026/1102',
        heat_no: 'HT-SS-6842',
        po_no: 'PO-BPCL-KOCHI-4412',
        manufacturer: 'Pennar Industries Limited, Hyderabad',
        tpi_agency: 'Lloyds Register Quality Assurance (LRQA)',
      },
    },
    chemistry: {
      C: 0.022,
      Mn: 1.45,
      Si: 0.45,
      P: 0.022,
      S: 0.005,
      Cr: 17.2,
      Ni: 11.4,
      Mo: 2.15,
      V: 0.01,
      Cu: 0.12,
      N: 0.045,
    },
    carbon_equivalent_iiw: 0.32,
    weldability: 'STANDARD_WELDABLE',
    pren: 25.02,
    mechanical: {
      yield_strength_mpa: 245.0,
      tensile_strength_mpa: 565.0,
      elongation_pct: 44.0,
      hardness_hb: 152.0,
    },
    astm_conformance: true,
    warnings: [],
    raw_text: `PENNAR INDUSTRIES LIMITED, HYDERABAD
EN 10204 3.1 INSPECTION CERTIFICATE
Certificate: PEN/MTC/2026/1102 | Date: 04-FEB-2026
Client: BPCL Kochi Refinery | PO: PO-BPCL-KOCHI-4412
Inspection Agency: Lloyds Register Quality Assurance

MATERIAL DETAILS:
BLIND FLANGE 2" (DN 50) 150# RF
Grade: ASTM A182 / ASME SA182 Grade F316L (Low Carbon Austenitic Stainless Steel)
Heat / Melt No: HT-SS-6842 | Solution Annealed 1050°C Quenched

CHEMICAL ASSAY (%):
C: 0.022 (Max 0.030) | Mn: 1.45 | Si: 0.45 | P: 0.022 | S: 0.005
Cr: 17.20 | Ni: 11.40 | Mo: 2.15 | N: 0.045
Pitting Resistance Equivalent (PREN = Cr + 3.3Mo + 16N): 25.02 [CORROSION RESISTANT]

MECHANICAL DATA:
Yield Strength (Rp0.2): 245 MPa (Min: 170 MPa)
Tensile Strength (Rm): 565 MPa (Min: 485 MPa)
Elongation (A5): 44% (Min: 30%)
Hardness: 152 HBW (Max: 217 HBW)
Intergranular Corrosion (IGC) Test: Passed ASTM A262 Practice E - No ditching observed.`,
    bounding_boxes: [
      { text: 'Grade: ASTM A182 F316L', confidence: 0.99, box: [10, 20, 52, 24], fieldKey: 'metallurgy' },
      { text: 'PREN: 25.02', confidence: 0.97, box: [10, 48, 40, 52], fieldKey: 'pren' },
    ],
  },

  'preset-4': {
    document_id: 'doc-scan-bad-c-04',
    filename: 'Scanned_Damaged_MTC_Vendor_X_CS_Flange.pdf',
    doc_type: 'RASTER_SCAN',
    is_scanned: true,
    confidence_score: 0.812,
    requires_hitl: true,
    is_incomplete: false,
    missing_attributes: [],
    extracted_attributes: {
      item_type: 'FLANGE',
      size_nb_mm: 200.0,
      pressure_class: 150,
      schedule: 'SCH 40',
      metallurgy: 'ASTM A105',
      facing_end: 'RF',
      standard: 'EN 10204 3.1',
      properties: {
        certificate_no: 'VND/SCAN/2026/099',
        heat_no: 'HT-BAD-2099',
        po_no: 'PO-MOPNG-EMERGENCY',
        manufacturer: 'Unregistered Forgings Pvt Ltd',
        tpi_agency: 'INTERNAL_MILL_INSPECTION',
      },
    },
    chemistry: {
      C: 0.38,
      Mn: 1.25,
      Si: 0.32,
      P: 0.042,
      S: 0.038,
      Cr: 0.25,
      Ni: 0.15,
      Mo: 0.08,
      V: 0.04,
      Cu: 0.18,
    },
    carbon_equivalent_iiw: 0.67,
    weldability: 'HIGH_CRACKING_RISK',
    pren: null,
    mechanical: {
      yield_strength_mpa: 360.0,
      tensile_strength_mpa: 640.0,
      elongation_pct: 18.0,
      hardness_hb: 205.0,
    },
    astm_conformance: false,
    warnings: [
      'ASTM NON-CONFORMANCE: Carbon content (0.38%) exceeds ASTM A105 maximum permissible limit (0.35%).',
      'HIGH CRACKING RISK: IIW Carbon Equivalent (0.67%) exceeds 0.48% threshold. High susceptibility to hydrogen-induced cold cracking.',
      'HITL REQUIRED: OCR Confidence (81.2%) is below auto-approval threshold of 95%. Mandatory materials supervisor review.',
    ],
    raw_text: `[SCANNED SMUDGED VENDOR CERTIFICATE - EASYOCR INFERRED]
CERTIFICATE NO: VND/SCAN/2026/099
HEAT NO: HT-BAD-2099 | PO: PO-MOPNG-EMERGENCY
MATERIAL: ASTM A105 CARBON STEEL WN FLANGE 8" 150# RF
MANUFACTURER: Unregistered Forgings Pvt Ltd

CHEMISTRY LADLE:
C: 0.38% (OUT OF SPEC)
Mn: 1.25% | Si: 0.32% | P: 0.042% | S: 0.038%
Cr: 0.25% | Ni: 0.15% | Mo: 0.08% | V: 0.04% | Cu: 0.18%
Calculated IIW CE: 0.67%

MECHANICAL:
Yield Strength: 360 MPa
Tensile Strength: 640 MPa
Elongation: 18% (Sub-standard ductility)
Hardness: 205 HBW (Exceeds ASTM A105 max 187 HBW)

CAUTION: Document flagged for human-in-the-loop metallurgical review due to ASTM boundary violation.`,
    bounding_boxes: [
      { text: 'C: 0.38%', confidence: 0.81, box: [10, 35, 35, 39], fieldKey: 'chemistry' },
      { text: 'Hardness: 205 HBW', confidence: 0.79, box: [10, 62, 45, 66], fieldKey: 'hardness_hb' },
    ],
  },
};
