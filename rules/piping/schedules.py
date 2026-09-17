from typing import Optional, Tuple
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation

def check_schedules(query_sch: str, cand_sch: str) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    return (DynamicCompatibilityTier.TIER_1_EXACT, 1.0, None)
