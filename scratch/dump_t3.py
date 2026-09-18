import json

with open('datasets/golden_benchmarks.json') as f:
    benchmarks = json.load(f)

t3 = [b for b in benchmarks if b["expected_tier"] == "TIER_3_INCOMPATIBLE"]
for b in t3:
    print(f"{b['test_id']}: code={b['expected_violation_code']} std={b['target_standard']}")
    print(f"  desc: {b['scenario_description']}")
    print(f"  Q: {b['query_part']}")
    print(f"  C: {b['candidate_part']}")
    print()
