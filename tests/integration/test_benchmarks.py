import json
from pathlib import Path
import pytest
from rules.tolerance import evaluate_pair

BENCHMARKS_PATH = Path(__file__).resolve().parent.parent.parent / "datasets" / "golden_benchmarks.json"

def _load_benchmarks():
    if not BENCHMARKS_PATH.exists():
        pytest.skip(f"Golden benchmarks file not found at {BENCHMARKS_PATH}")
    with open(BENCHMARKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

benchmarks = _load_benchmarks()

@pytest.mark.parametrize("case", benchmarks, ids=lambda c: f"{c['test_id']}-{c['expected_tier']}")
def test_golden_benchmark_case(case):
    """
    Validates golden benchmark engineering rule evaluations against the 150 test cases.
    - 50 Tier 1 Drop-in Identical matches
    - 50 Tier 2 Qualified Substitutes
    - 50 Tier 3 Incompatible fatal failure mode traps
    """
    result = evaluate_pair(case["query_part"], case["candidate_part"])

    # 1. Compatibility Tier
    assert result.compatibility_tier.name == case["expected_tier"], (
        f"Test {case['test_id']} failed tier assertion. Expected: {case['expected_tier']}, "
        f"Actual: {result.compatibility_tier.name}. Scenario: {case['scenario_description']}. "
        f"Violations: {[v.failure_mode_prevented for v in result.rule_violations]}"
    )

    # 2. Boolean Compatibility Flag
    assert result.is_compatible == case["expected_is_compatible"], (
        f"Test {case['test_id']} failed is_compatible assertion. "
        f"Expected: {case['expected_is_compatible']}, Actual: {result.is_compatible}"
    )

    # 3. For Tier 3 Incompatible, must catch at least one deterministic rule violation
    if case["expected_tier"] == "TIER_3_INCOMPATIBLE":
        assert len(result.rule_violations) > 0, (
            f"Test {case['test_id']} was flagged Tier-3 but has 0 rule violations."
        )
