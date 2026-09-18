import json
with open('datasets/golden_benchmarks.json') as f:
    benchmarks = json.load(f)

q_keys = set()
c_keys = set()
for b in benchmarks:
    q_keys.update(b['query_part'].get('properties', {}).keys())
    c_keys.update(b['candidate_part'].get('properties', {}).keys())

print("Query property keys:", sorted(list(q_keys)))
print("Candidate property keys:", sorted(list(c_keys)))
