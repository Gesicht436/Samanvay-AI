import json

with open('datasets/golden_benchmarks.json') as f:
    benchmarks = json.load(f)

print("=== ALL 50 TIER 1 SCENARIOS ===")
for b in benchmarks[:50]:
    print(f"{b['test_id']}: {b['scenario_description']}")

print("\n=== ALL 50 TIER 2 SCENARIOS ===")
for b in benchmarks[50:100]:
    print(f"{b['test_id']}: {b['scenario_description']}")

print("\n=== ALL 50 TIER 3 SCENARIOS ===")
for b in benchmarks[100:150]:
    print(f"{b['test_id']}: {b['scenario_description']}")
