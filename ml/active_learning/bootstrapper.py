import json
import os
from ml.active_learning.cache import ActiveLearningCache

def seed_from_golden_benchmarks(cache: ActiveLearningCache, benchmarks_path: str):
    if not os.path.exists(benchmarks_path):
        return
        
    with open(benchmarks_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return
            
    officer = 'CHIEF_MATERIALS_ENGINEER_BOOTSTRAP'
    
    for item in data:
        query = item.get("query_text")
        sku = item.get("source_sku")
        tier = item.get("tier", 3)
        
        if not query or not sku:
            continue
            
        decision = "APPROVE" if tier in [1, 2] else "REJECT"
        tier_override = f"Tier {tier}"
        
        cache.record_decision(query, sku, decision, tier_override, officer)
