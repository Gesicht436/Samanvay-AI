from backend.app.contracts.matching import Tier


def assign_tier(score: float, violations: list[str]) -> Tier:
    if violations:
        return Tier.TIER_4_REJECT
    if score >= 0.85:
        return Tier.TIER_1
    if score >= 0.60:
        return Tier.TIER_3
    return Tier.TIER_4_REJECT
