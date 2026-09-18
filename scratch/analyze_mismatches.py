import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
from rules.tolerance import evaluate_pair

with open('datasets/golden_benchmarks.json') as f:
    benchmarks = json.load(f)

for tier_name in ["TIER_1_IDENTICAL", "TIER_2_SUBSTITUTE", "TIER_3_INCOMPATIBLE"]:
    subset = [b for b in benchmarks if b["expected_tier"] == tier_name]
    mismatches = []
    for b in subset:
        res = evaluate_pair(b['query_part'], b['candidate_part'])
        act = res.compatibility_tier.name
        if act != tier_name:
            mismatches.append((b['test_id'], b['scenario_description'], act, [v.failure_mode_prevented for v in res.rule_violations]))
    print(f"=== {tier_name}: {len(subset) - len(mismatches)}/{len(subset)} passed ===")
    for m in mismatches:
        print(f"  {m[0]}: actual={m[2]} desc={m[1]}")
        if m[3]:
            print(f"    violations: {m[3]}")
