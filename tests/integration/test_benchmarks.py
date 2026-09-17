import pytest
import json
import os
from backend.app.schemas.material import ExtractedMaterialAttributes
from rules.tolerance import evaluate_material_compatibility

def test_golden_benchmarks():
    # Mock data since we don't have golden_benchmarks.json
    benchmarks = [
        {
            "query": {"item_type": "PIPE", "size": "200mm", "schedule": "40", "material": "A106 GR.B"},
            "candidate": {"item_type": "PIPE", "size": "200mm", "schedule": "40", "material": "A106 GR.B"},
            "expected_tier": "TIER_1_IDENTICAL"
        },
        {
            "query": {"item_type": "PIPE", "size": "200mm", "schedule": "40", "material": "A106 GR.B"},
            "candidate": {"item_type": "PIPE", "size": "200mm", "schedule": "80", "material": "A106 GR.B"},
            "expected_tier": "TIER_2_SUBSTITUTE"
        }
    ]
    
    for case in benchmarks:
        q_attrs = ExtractedMaterialAttributes(**case["query"])
        c_attrs = ExtractedMaterialAttributes(**case["candidate"])
        result = evaluate_material_compatibility(q_attrs, c_attrs)
        assert result.tier.name == case["expected_tier"]
