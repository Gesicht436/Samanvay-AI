import sys
sys.path.insert(0, ".")
import csv
import re
from pathlib import Path
from backend.app.ml.ner_tagger import extract_attributes

def test_search(query_text, source_cpse="IOCL"):
    attrs = extract_attributes(query_text)
    print(f"Query: {query_text}")
    print(f"Extracted: item_type={attrs.item_type}, size_nb={attrs.size_nb_mm}, size_inch={attrs.size_inch}")

    tokens = [t.strip().upper() for t in re.split(r'[\s,/\-]+', query_text) if len(t.strip()) > 0 and t.strip() not in ['INCH', 'IN', 'A', 'THE', 'FOR', 'OF']]
    print(f"Tokens: {tokens}")

    catalogs_dir = Path("data/mock_cpes_catalogs")
    candidates = []
    for cpse in ["ongc", "bpcl", "iocl"]:
        fpath = catalogs_dir / f"{cpse}_materials.csv"
        if not fpath.exists():
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                score = 0
                desc = row["raw_description"].upper()
                itype = row.get("extracted_item_type", "")
                try:
                    s_nb = float(row.get("extracted_size_nb_mm", 0))
                except:
                    s_nb = 0

                # 1. Item Type Match
                if attrs.item_type and itype == attrs.item_type:
                    score += 15
                elif "PIPE" in query_text.upper() and ("PIPE" in desc or "SMLS" in desc):
                    score += 10

                # 2. Size Match (10" or 250mm)
                if attrs.size_nb_mm and abs(s_nb - attrs.size_nb_mm) < 1.0:
                    score += 15
                elif '10"' in query_text and ('10"' in desc or '10 INCH' in desc or 'DN250' in desc):
                    score += 10

                # 3. Token Matches
                for t in tokens:
                    if t in desc:
                        score += 4

                if score > 15:
                    candidates.append({
                        "sku": row["local_code"],
                        "cpse": row["cpse"],
                        "desc": row["raw_description"],
                        "qty": int(row["quantity"]),
                        "score": score,
                    })

    candidates.sort(key=lambda x: -x["score"])
    print(f"\nFound {len(candidates)} candidates:")
    for c in candidates[:10]:
        print(f"  [Score {c['score']}] {c['cpse']} | {c['sku']} | {c['desc']} (Qty: {c['qty']})")

test_search('10" pipe')
print("="*60)
test_search('10 inch pipe')
