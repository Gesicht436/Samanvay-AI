import sys, os
sys.path.insert(0, os.path.abspath('.'))
import json
from rules.tolerance import evaluate_pair

with open('datasets/golden_benchmarks.json') as f:
    benchmarks = json.load(f)

t1 = [b for b in benchmarks if b['expected_tier'] == 'TIER_1_IDENTICAL']
for b in t1:
    res = evaluate_pair(b['query_part'], b['candidate_part'])
    if res.compatibility_tier.name != 'TIER_1_IDENTICAL':
        print(f"{b['test_id']}: {b['scenario_description']}")
        print(f"  actual={res.compatibility_tier.name} score={res.composite_score}")
        sc = res.property_scorecard.model_dump()
        for k, v in sc.items():
            if k == 'equipment_specific':
                for eq_k, eq_v in v.items():
                    if eq_v['tier'] != 'TIER_1_IDENTICAL':
                        print(f"    {eq_k}: {eq_v['tier']} {eq_v['comment']}")
            elif v and v.get('tier') != 'TIER_1_IDENTICAL':
                print(f"    {k}: {v.get('tier')} {v.get('comment')}")
