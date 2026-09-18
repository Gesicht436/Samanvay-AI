import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
from rules.tolerance import evaluate_pair

with open('datasets/golden_benchmarks.json') as f:
    benchmarks = json.load(f)

print(f"Total benchmarks: {len(benchmarks)}")

# Check counts by tier
tiers = {}
for b in benchmarks:
    t = b["expected_tier"]
    tiers[t] = tiers.get(t, 0) + 1
print("Tier distribution:", tiers)

# Let's inspect each tier's scenarios
print("\n--- SAMPLE TIER 1 ---")
t1 = [b for b in benchmarks if b["expected_tier"] == "TIER_1_IDENTICAL"]
for b in t1[:10]:
    print(b["test_id"], "::", b["scenario_description"])
    print("  Q:", b["query_part"])
    print("  C:", b["candidate_part"])

print("\n--- SAMPLE TIER 2 ---")
t2 = [b for b in benchmarks if b["expected_tier"] == "TIER_2_SUBSTITUTE"]
for b in t2[:5]:
    print(b["test_id"], "::", b["scenario_description"])
    print("  Q:", b["query_part"])
    print("  C:", b["candidate_part"])

print("\n--- SAMPLE TIER 3 ---")
t3 = [b for b in benchmarks if b["expected_tier"] == "TIER_3_INCOMPATIBLE"]
for b in t3[:5]:
    print(b["test_id"], "::", b["scenario_description"])
    print("  Q:", b["query_part"])
    print("  C:", b["candidate_part"])
