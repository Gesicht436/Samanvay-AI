import sys
sys.path.insert(0, ".")
from backend.app.ml.ner_tagger import extract_attributes

queries = [
    '10" pipe',
    '10 inch pipe',
    'PIPE 10 INCH',
    'PIPE SEAMLESS 10" SCH 40',
    '10" seamless pipe',
    'PIPE 10" ASTM A106',
    '10 IN PIPE'
]
for q in queries:
    attrs = extract_attributes(q)
    print(f"Query: {q:26} -> item_type={attrs.item_type!r:16} size_nb={attrs.size_nb_mm} size_inch={attrs.size_inch}")
