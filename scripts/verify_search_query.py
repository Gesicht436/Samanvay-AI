import sys
sys.path.insert(0, ".")
from backend.app.graph.queries import search_inter_cpse_spares, find_inter_cpse_spares
from fastapi.testclient import TestClient
from backend.app.main import app

queries = [
    '10" pipe',
    '10 inch pipe',
    'PIPE 10 INCH',
    'FLANGE 4IN 300#',
    'VALVE GATE 2"',
    'MOTOR 37KW',
    'ONGC-MAT-0004182',
    'ALL'
]

print("=== Direct search_inter_cpse_spares Test ===")
for q in queries:
    res = search_inter_cpse_spares(q, limit=5)
    print(f"\nQuery: '{q}' -> {len(res)} results")
    for r in res[:3]:
        score = r.get("match_score", "N/A")
        print(f"  [Score {score}] {r['owner_cpse']} | {r['equivalent_sku']} | {r['description'][:65]} (Qty: {r['available_qty']})")

print("\n=== FastAPI /api/v1/graph/discover Test ===")
client = TestClient(app)
resp = client.get("/api/v1/graph/discover", params={"query": '10" pipe'})
assert resp.status_code == 200
data = resp.json()
print(f"API /discover query='10\" pipe' -> status {resp.status_code}, count: {data['count']}, total spares: {data['total_available_spares']}")
for s in data["spares"][:3]:
    print(f"  {s['owner_cpse']} | {s['equivalent_sku']} | {s['description'][:65]} (Score: {s.get('match_score')})")

print("\n=== Fallback /api/v1/graph/spares/10%22%20pipe Test ===")
resp2 = client.get("/api/v1/graph/spares/10\" pipe")
assert resp2.status_code == 200
data2 = resp2.json()
print(f"API /spares query='10\" pipe' -> status {resp2.status_code}, total spares: {data2['total_available_spares']}")
for s in data2["spares"][:3]:
    print(f"  {s['owner_cpse']} | {s['equivalent_sku']} | {s['description'][:65]}")

print("\nAll Backend Tests Passed Successfully!")
