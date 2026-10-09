import pytest

from machine_learning.tiers import Tier, assign_tier


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.59, Tier.TIER_4_REJECT),
        (0.60, Tier.TIER_3),
        (0.84, Tier.TIER_3),
        (0.85, Tier.TIER_1),
    ],
)
def test_tier_score_boundaries(score, expected):
    assert assign_tier(score, []) == expected


def test_any_safety_violation_forces_reject_tier():
    assert assign_tier(1.0, ["size mismatch"]) == Tier.TIER_4_REJECT
