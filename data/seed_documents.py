"""
seed_documents.py
Synthesizes sample Mill Test Certificates (MTCs compliant with EN 10204 3.1) and Delivery Challans.
Used by Smariddih (Document Intelligence Lead) to benchmark PyMuPDF, PaddleOCR, and key-value extraction.
Author: Data Pipelines & Taxonomy Lead (Shaurya)
"""

import os
import json
import random
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DATA_DIR = Path(__file__).resolve().parent
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

MTC_SAMPLES = [
    {
        "filename": "sample_mtc_flange_01.pdf",
        "doc_type": "MILL TEST CERTIFICATE (EN 10204 3.1)",
        "cert_no": "MTC-2025-FLG-8819",
        "po_no": "PO-IOCL-PNP-77410",
        "description": "WELD NECK FLANGE 4 INCH CLASS 300 RF",
        "standard": "ASME B16.5 / NACE MR0175",
        "material_grade": "ASTM A105N (NORMALIZED)",
        "heat_no": "HT-98421-B",
        "qty": "45 PCS",
        "chemical": [["C%", "Mn%", "Si%", "P%", "S%"], ["0.19", "0.92", "0.24", "0.015", "0.012"]],
        "mechanical": [["Yield (MPa)", "Tensile (MPa)", "Elongation (%)", "Hardness (HBW)"], ["310", "525", "29.5", "156"]]
    },
    {
        "filename": "sample_mtc_valve_02.pdf",
        "doc_type": "INSPECTION TEST CERTIFICATE (EN 10204 3.1)",
        "cert_no": "MTC-2025-VLV-4491",
        "po_no": "PO-ONGC-HZR-55102",
        "description": "GATE VALVE 2 INCH CLASS 150 RF FLANGED",
        "standard": "API 600 / ASME B16.34",
        "material_grade": "ASTM A216 WCB",
        "heat_no": "HT-77104-K",
        "qty": "20 PCS",
        "chemical": [["C%", "Mn%", "Si%", "P%", "S%"], ["0.22", "0.85", "0.38", "0.018", "0.014"]],
        "mechanical": [["Yield (MPa)", "Tensile (MPa)", "Elongation (%)", "Hardness (HBW)"], ["275", "510", "26.0", "168"]]
    },
    {
        "filename": "sample_mtc_flange_ss_03.pdf",
        "doc_type": "MATERIAL TEST REPORT (EN 10204 3.1)",
        "cert_no": "MTC-2025-SS-1109",
        "po_no": "PO-BPCL-MUM-99301",
        "description": "FLANGE BLIND 6 INCH CLASS 600 RTJ",
        "standard": "ASME B16.5",
        "material_grade": "ASTM A182 F316L",
        "heat_no": "HT-33190-X",
        "qty": "15 PCS",
        "chemical": [["C%", "Mn%", "Cr%", "Ni%", "Mo%"], ["0.024", "1.45", "16.85", "10.40", "2.15"]],
        "mechanical": [["Yield (MPa)", "Tensile (MPa)", "Elongation (%)", "Hardness (HBW)"], ["245", "570", "42.0", "172"]]
    },
    {
        "filename": "sample_mtc_bolt_04.pdf",
        "doc_type": "FASTENER QUALITY CERTIFICATE (EN 10204 3.1)",
        "cert_no": "MTC-2025-BLT-3320",
        "po_no": "PO-IOCL-MTH-11928",
        "description": "STUD BOLTS WITH 2 HEAVY HEX NUTS 1\" X 8\"",
        "standard": "ASME B18.2.1 / ASTM A193",
        "material_grade": "ASTM A193 B7 / A194 2H",
        "heat_no": "HT-55201-P",
        "qty": "250 SETS",
        "chemical": [["C%", "Cr%", "Mo%", "P%", "S%"], ["0.41", "0.95", "0.21", "0.012", "0.009"]],
        "mechanical": [["Yield (MPa)", "Tensile (MPa)", "Elongation (%)", "Hardness (HRC)"], ["795", "920", "17.5", "32"]]
    },
    {
        "filename": "sample_challan_valve_05.pdf",
        "doc_type": "DELIVERY CHALLAN / MATERIAL INWARD SLIP",
        "cert_no": "DC-2025-99014",
        "po_no": "PO-ONGC-URN-66289",
        "description": "BALL VALVE 4 INCH CLASS 300 BW ENDS",
        "standard": "API 6D",
        "material_grade": "ASTM A216 WCB / SS316 TRIM",
        "heat_no": "HT-11983-M",
        "qty": "12 PCS",
        "chemical": [["C%", "Mn%", "Si%", "P%", "S%"], ["0.21", "0.88", "0.35", "0.016", "0.011"]],
        "mechanical": [["Hydro Shell (bar)", "Hydro Seat (bar)", "Air Seat (bar)", "Visual"], ["77.0", "56.5", "6.0", "ACCEPTED"]]
    }
]

def generate_pdf(doc_info):
    pdf_path = RAW_DIR / doc_info["filename"]
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#003366'),
        alignment=1, # Center
        spaceAfter=10
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#222222'),
        spaceBefore=8,
        spaceAfter=4,
        fontName="Helvetica-Bold"
    )
    cell_style = ParagraphStyle('TableCell', parent=styles['Normal'], fontSize=8, leading=10)
    bold_cell_style = ParagraphStyle('BoldTableCell', parent=styles['Normal'], fontSize=8, leading=10, fontName="Helvetica-Bold")
    
    story = []
    
    # Header Title
    story.append(Paragraph(f"<b>BHARAT HEAVY PROCESS SPARES & FORGINGS LTD.</b>", title_style))
    story.append(Paragraph(f"<b>{doc_info['doc_type']}</b>", ParagraphStyle('Sub', parent=title_style, fontSize=11, leading=14, textColor=colors.darkgray)))
    story.append(Spacer(1, 10))
    
    # Metadata Table
    meta_data = [
        [Paragraph("<b>Certificate No:</b>", cell_style), Paragraph(doc_info["cert_no"], cell_style),
         Paragraph("<b>Date:</b>", cell_style), Paragraph("15-AUG-2025", cell_style)],
        [Paragraph("<b>Purchase Order:</b>", cell_style), Paragraph(doc_info["po_no"], cell_style),
         Paragraph("<b>Heat / Batch No:</b>", bold_cell_style), Paragraph(f"<b>{doc_info['heat_no']}</b>", bold_cell_style)],
        [Paragraph("<b>Product Description:</b>", bold_cell_style), Paragraph(doc_info["description"], bold_cell_style),
         Paragraph("<b>Quantity:</b>", cell_style), Paragraph(doc_info["qty"], cell_style)],
        [Paragraph("<b>Material Specification:</b>", bold_cell_style), Paragraph(f"<b>{doc_info['material_grade']}</b>", bold_cell_style),
         Paragraph("<b>Governing Standard:</b>", cell_style), Paragraph(doc_info["standard"], cell_style)]
    ]
    t_meta = Table(meta_data, colWidths=[120, 180, 100, 140])
    t_meta.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FA')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))
    
    # Chemical Composition Table
    story.append(Paragraph("1. CHEMICAL COMPOSITION (PRODUCT ANALYSIS)", section_style))
    chem_headers = [Paragraph(f"<b>{h}</b>", bold_cell_style) for h in doc_info["chemical"][0]]
    chem_vals = [Paragraph(v, cell_style) for v in doc_info["chemical"][1]]
    t_chem = Table([chem_headers, chem_vals], colWidths=[108]*len(chem_headers))
    t_chem.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E9ECEF')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_chem)
    story.append(Spacer(1, 10))
    
    # Mechanical Properties Table
    story.append(Paragraph("2. MECHANICAL TEST PROPERTIES", section_style))
    mech_headers = [Paragraph(f"<b>{h}</b>", bold_cell_style) for h in doc_info["mechanical"][0]]
    mech_vals = [Paragraph(v, cell_style) for v in doc_info["mechanical"][1]]
    t_mech = Table([mech_headers, mech_vals], colWidths=[135]*len(mech_headers))
    t_mech.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E9ECEF')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_mech)
    story.append(Spacer(1, 14))
    
    # Certification statement & signatures
    statement = ("We hereby certify that the material described above has been manufactured, sampled, tested and inspected "
                 "in accordance with the specification requirements and meets all chemical, mechanical, and dimensional criteria.")
    story.append(Paragraph(statement, ParagraphStyle('CertStmt', parent=styles['Normal'], fontSize=7.5, leading=9, textColor=colors.darkgray)))
    story.append(Spacer(1, 14))
    
    sig_data = [
        [Paragraph("<b>Quality Assurance Inspector</b>", cell_style), Paragraph("<b>Authorized Third-Party Inspector (TPI)</b>", cell_style)],
        [Paragraph("Certified QA Seal / Stamp [APPROVED]", cell_style), Paragraph("Bureau Veritas / TUV Rheinland [ENDORSED]", cell_style)]
    ]
    t_sig = Table(sig_data, colWidths=[270, 270])
    t_sig.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_sig)
    
    doc.build(story)
    print(f"[+] Generated PDF certificate: {pdf_path.name}")

def main():
    print("Generating sample Mill Test Certificates (MTC) and Challan PDFs in data/raw/...")
    for doc_info in MTC_SAMPLES:
        generate_pdf(doc_info)
        
    gt_file = RAW_DIR / "sample_mtc_ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(MTC_SAMPLES, f, indent=2)
    print(f"[+] Wrote ground truth metadata to {gt_file.name}")

if __name__ == "__main__":
    main()
