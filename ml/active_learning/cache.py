from collections import OrderedDict
from typing import Optional, Dict

class CacheEntry:
    def __init__(self, query_text: str, source_sku: str, decision: str, tier_override: str, officer: str):
        self.query_text = query_text
        self.source_sku = source_sku
        self.decision = decision
        self.tier_override = tier_override
        self.officer = officer
        self.stamp = ""
        
class ActiveLearningCache:
    def __init__(self, max_size=10000):
        self.max_size = max_size
        self.cache: Dict[tuple, CacheEntry] = OrderedDict()
        self.sku_stamps = {}
        
    def lookup(self, query_text: str, source_sku: str) -> Optional[CacheEntry]:
        key = (query_text, source_sku)
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
        
    def record_decision(self, query_text: str, source_sku: str, decision: str, tier_override: str, officer: str):
        key = (query_text, source_sku)
        entry = CacheEntry(query_text, source_sku, decision, tier_override, officer)
        self.cache[key] = entry
        self.cache.move_to_end(key)
        
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
            
        if decision == "APPROVE":
            self.boost_approved(source_sku)
        elif decision == "REJECT":
            self.demote_rejected(source_sku)
            
    def boost_approved(self, sku_code: str):
        self.sku_stamps[sku_code] = "[VERIFIED BY HUMAN EXPERT]"
        
    def demote_rejected(self, sku_code: str):
        self.sku_stamps[sku_code] = "[REJECTED BY HUMAN EXPERT]"
