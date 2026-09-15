import json
import os
from backend.app.ingestion.pdf_parser import process_document

filename = "doc7.jpeg"
filepath = os.path.join("data", "raw", filename)

if not os.path.exists(filepath):
    print(f"File not found at {filepath}")
else:
    print(f"Reading {filename} with OCR...")
    with open(filepath, "rb") as f:
        file_bytes = f.read()

    result = process_document(file_bytes, filename)

    print("\n================== PARSED METADATA ==================")
    print(json.dumps(result["parsed_metadata"], indent=2))
    print(f"\nConfidence: {result['confidence']}")