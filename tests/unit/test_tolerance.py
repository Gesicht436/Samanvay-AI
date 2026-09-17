import pytest
from backend.app.schemas.material import ExtractedMaterialAttributes, DynamicCompatibilityTier
from rules.tolerance import evaluate_material_compatibility

@pytest.mark.parametrize("query_attrs, candidate_attrs, expected_tier, expected_violation", [
    # 1. Tier-3 Pressure Down-Rating (ASME B16.5)
    (
        {"item_type": "FLANGE", "size": "100mm", "rating": "300", "material": "A105", "facing": "RF"},
        {"item_type": "FLANGE", "size": "100mm", "rating": "150", "material": "A105", "facing": "RF"},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "PRESSURE DOWN-RATING"
    ),
    # 2. Tier-3 Cryogenic Brittle Fracture (ASTM DAG)
    (
        {"item_type": "FLANGE", "size": "50mm", "rating": "300", "material": "A350 LF2", "facing": "RF"},
        {"item_type": "FLANGE", "size": "50mm", "rating": "300", "material": "A105", "facing": "RF"},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "CRYOGENIC"
    ),
    # 3. Tier-3 Liquid Metal Embrittlement
    (
        {"item_type": "STUD_BOLT", "material": "A193 B7", "properties": {"temp": "350°C", "coating": "BARE"}},
        {"item_type": "STUD_BOLT", "material": "A193 B7", "properties": {"temp": "350°C", "coating": "GALVANIZED"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "LIQUID METAL"
    ),
    # 4. Tier-2 Safe Metallurgy Upgrade (SS316 for SS304)
    (
        {"item_type": "GATE_VALVE", "size": "150mm", "rating": "150", "material": "A351 CF8", "facing": "RF"},
        {"item_type": "GATE_VALVE", "size": "150mm", "rating": "150", "material": "A351 CF8M", "facing": "RF"},
        DynamicCompatibilityTier.TIER_2_SUBSTITUTE,
        None
    ),
    # 5. Tier-1 Exact Parity
    (
        {"item_type": "PIPE", "size": "200mm", "schedule": "40", "material": "A106 GR.B", "standard": "ASME B36.10M"},
        {"item_type": "PIPE", "size": "200mm", "schedule": "40", "material": "A106 GR.B", "standard": "ASME B36.10M"},
        DynamicCompatibilityTier.TIER_1_IDENTICAL,
        None
    ),
    # 6. Tier-3 Dimensional Mismatch
    (
        {"item_type": "PIPE", "size": "250mm", "schedule": "40", "material": "A106 GR.B"},
        {"item_type": "PIPE", "size": "200mm", "schedule": "40", "material": "A106 GR.B"},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "DIMENSION"
    ),
    # 7. Tier-3 Schedule Down-Rating
    (
        {"item_type": "PIPE", "size": "200mm", "schedule": "80", "material": "A106 GR.B"},
        {"item_type": "PIPE", "size": "200mm", "schedule": "40", "material": "A106 GR.B"},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "SCHEDULE"
    ),
    # 8. Tier-2 Schedule Upgrade
    (
        {"item_type": "PIPE", "size": "200mm", "schedule": "40", "material": "A106 GR.B"},
        {"item_type": "PIPE", "size": "200mm", "schedule": "80", "material": "A106 GR.B"},
        DynamicCompatibilityTier.TIER_2_SUBSTITUTE,
        None
    ),
    # 9. Tier-3 Facing Mismatch (RF vs RTJ)
    (
        {"item_type": "FLANGE", "size": "100mm", "rating": "300", "material": "A105", "facing": "RF"},
        {"item_type": "FLANGE", "size": "100mm", "rating": "300", "material": "A105", "facing": "RTJ"},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "FACING"
    ),
    # 10. Tier-1 Pressure Over-Rating (Pipe)
    (
        {"item_type": "PIPE", "size": "250mm", "properties": {"pressure_rating_psi": 300}},
        {"item_type": "PIPE", "size": "250mm", "properties": {"pressure_rating_psi": 350}},
        DynamicCompatibilityTier.TIER_1_IDENTICAL, # safe over-rating
        None
    ),
    # 11. Tier-3 Non-Ex Motor in Hazardous Zone
    (
        {"item_type": "MOTOR", "properties": {"ex_rating": "Ex d IIC T4 Gb", "zone": 1}},
        {"item_type": "MOTOR", "properties": {"ex_rating": None, "zone": 1}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "EXPLOSION"
    ),
    # 12. Tier-3 NACE Sour Service Violation
    (
        {"item_type": "FLANGE", "size": "100mm", "rating": "300", "material": "A105", "properties": {"nace_required": True}},
        {"item_type": "FLANGE", "size": "100mm", "rating": "300", "material": "A105", "properties": {"nace_compliant": False}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "SOUR"
    ),
    # 13. Tier-3 Valve Trim Downgrade
    (
        {"item_type": "GATE_VALVE", "size": "150mm", "rating": "300", "material": "WCB", "properties": {"trim_no": 8}},
        {"item_type": "GATE_VALVE", "size": "150mm", "rating": "300", "material": "WCB", "properties": {"trim_no": 1}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "TRIM" # Matches Trim Downgrade or erosive service violation
    ),
    # 14. Tier-3 Reduced Bore in Piggable Pipeline
    (
        {"item_type": "BALL_VALVE", "size": "200mm", "rating": "600", "properties": {"port_bore": "FULL_BORE", "piggable": True}},
        {"item_type": "BALL_VALVE", "size": "200mm", "rating": "600", "properties": {"port_bore": "REDUCED_BORE"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "PIG"
    ),
    # 15. Tier-3 Seal Plan Downgrade
    (
        {"item_type": "PUMP", "properties": {"seal_plan": "Plan 53A", "toxic_service": True}},
        {"item_type": "PUMP", "properties": {"seal_plan": "Plan 11"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "SEAL"
    ),
    # 16. Tier-3 Material Strength Mismatch
    (
        {"item_type": "BOLT", "material": "A320 L7", "properties": {"yield_strength_mpa": 725}},
        {"item_type": "BOLT", "material": "A193 B7", "properties": {"yield_strength_mpa": 600}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "STRENGTH"
    ),
    # 17. Tier-2 Temperature Over-Rating
    (
        {"item_type": "GASKET", "properties": {"max_temp_c": 200}},
        {"item_type": "GASKET", "properties": {"max_temp_c": 300}},
        DynamicCompatibilityTier.TIER_2_SUBSTITUTE,
        None
    ),
    # 18. Tier-3 Temperature Down-Rating
    (
        {"item_type": "GASKET", "properties": {"max_temp_c": 200}},
        {"item_type": "GASKET", "properties": {"max_temp_c": 150}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "TEMPERATURE"
    ),
    # 19. Tier-3 Thread Type Mismatch
    (
        {"item_type": "FITTING", "properties": {"thread": "NPT"}},
        {"item_type": "FITTING", "properties": {"thread": "BSPT"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "THREAD"
    ),
    # 20. Tier-3 Motor IP Rating Downgrade
    (
        {"item_type": "MOTOR", "properties": {"ip_rating": "IP65"}},
        {"item_type": "MOTOR", "properties": {"ip_rating": "IP54"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "IP RATING"
    ),
    # 21. Tier-2 Motor IP Rating Upgrade
    (
        {"item_type": "MOTOR", "properties": {"ip_rating": "IP54"}},
        {"item_type": "MOTOR", "properties": {"ip_rating": "IP65"}},
        DynamicCompatibilityTier.TIER_2_SUBSTITUTE,
        None
    ),
    # 22. Tier-3 Flow Rate Down-Rating
    (
        {"item_type": "PUMP", "properties": {"flow_rate_m3h": 100}},
        {"item_type": "PUMP", "properties": {"flow_rate_m3h": 80}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "FLOW RATE"
    ),
    # 23. Tier-3 Valve End Connection Mismatch
    (
        {"item_type": "VALVE", "properties": {"end_conn": "FLANGED"}},
        {"item_type": "VALVE", "properties": {"end_conn": "BUTTWELD"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "CONNECTION"
    ),
    # 24. Tier-3 Bearing Type Mismatch
    (
        {"item_type": "BEARING", "properties": {"type": "ROLLER"}},
        {"item_type": "BEARING", "properties": {"type": "BALL"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "BEARING TYPE"
    ),
    # 25. Tier-3 API Plan Downgrade
    (
        {"item_type": "COMPRESSOR", "properties": {"api_plan": "53B"}},
        {"item_type": "COMPRESSOR", "properties": {"api_plan": "52"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "API PLAN"
    ),
    # 26. Tier-3 Voltage Mismatch
    (
        {"item_type": "MOTOR", "properties": {"voltage": "415V"}},
        {"item_type": "MOTOR", "properties": {"voltage": "230V"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "VOLTAGE"
    ),
    # 27. Tier-3 Frequency Mismatch
    (
        {"item_type": "MOTOR", "properties": {"frequency": "50Hz"}},
        {"item_type": "MOTOR", "properties": {"frequency": "60Hz"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "FREQUENCY"
    ),
    # 28. Tier-3 Valve Operation Mismatch
    (
        {"item_type": "VALVE", "properties": {"operation": "PNEUMATIC"}},
        {"item_type": "VALVE", "properties": {"operation": "MANUAL"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "OPERATION"
    ),
    # 29. Tier-3 Coupling Type Mismatch
    (
        {"item_type": "PUMP", "properties": {"coupling": "FLEXIBLE"}},
        {"item_type": "PUMP", "properties": {"coupling": "RIGID"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "COUPLING"
    ),
    # 30. Tier-3 Seal Material Mismatch
    (
        {"item_type": "O_RING", "properties": {"material": "VITON"}},
        {"item_type": "O_RING", "properties": {"material": "NBR"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "SEAL MATERIAL"
    ),
    # 31. Tier-2 Seal Material Upgrade
    (
        {"item_type": "O_RING", "properties": {"material": "NBR", "temp": "100°C"}},
        {"item_type": "O_RING", "properties": {"material": "VITON", "temp": "100°C"}},
        DynamicCompatibilityTier.TIER_2_SUBSTITUTE,
        None
    ),
    # 32. Tier-3 Painting System Mismatch
    (
        {"item_type": "TANK", "properties": {"paint_sys": "EPOXY_PHENOLIC"}},
        {"item_type": "TANK", "properties": {"paint_sys": "ALKYD"}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "PAINT"
    ),
    # 33. Tier-3 Coating Thickness Downgrade
    (
        {"item_type": "PIPE", "properties": {"coating_thickness_um": 500}},
        {"item_type": "PIPE", "properties": {"coating_thickness_um": 250}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "THICKNESS"
    ),
    # 34. Tier-2 Coating Thickness Upgrade
    (
        {"item_type": "PIPE", "properties": {"coating_thickness_um": 250}},
        {"item_type": "PIPE", "properties": {"coating_thickness_um": 500}},
        DynamicCompatibilityTier.TIER_2_SUBSTITUTE,
        None
    ),
    # 35. Tier-3 Filter Rating Downgrade
    (
        {"item_type": "FILTER", "properties": {"micron_rating": 10}},
        {"item_type": "FILTER", "properties": {"micron_rating": 25}},
        DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
        "MICRON RATING"
    ),
    # 36. Tier-2 Filter Rating Upgrade (lower micron = better filtration)
    (
        {"item_type": "FILTER", "properties": {"micron_rating": 25}},
        {"item_type": "FILTER", "properties": {"micron_rating": 10}},
        DynamicCompatibilityTier.TIER_2_SUBSTITUTE,
        None
    ),
])
def test_tolerance_rules(query_attrs, candidate_attrs, expected_tier, expected_violation):
    # Construct ExtractedMaterialAttributes based on the input dicts
    query = ExtractedMaterialAttributes(**query_attrs)
    candidate = ExtractedMaterialAttributes(**candidate_attrs)
    
    # Evaluate compatibility
    result = evaluate_material_compatibility(query, candidate)
    
    # Verify the correct tier was identified
    assert result.tier == expected_tier, f"Expected {expected_tier}, got {result.tier}"
    
    # Verify the violation description if one is expected
    if expected_violation:
        assert result.rule_violations, "Expected rule violations, but none found"
        found = False
        for violation in result.rule_violations:
            if expected_violation.upper() in violation.description.upper() or expected_violation.upper() in violation.rule_name.upper():
                found = True
                break
        assert found, f"Expected violation containing '{expected_violation}' not found in {result.rule_violations}"
