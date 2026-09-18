import json

with open('datasets/golden_benchmarks.json') as f:
    benchmarks = json.load(f)

t2 = [b for b in benchmarks if b["expected_tier"] == "TIER_2_SUBSTITUTE"]
for b in t2[:25]:
    print(f"{b['test_id']}: {b['scenario_description']}")
    print(f"  Q: {b['query_part']}")
    print(f"  C: {b['candidate_part']}")
