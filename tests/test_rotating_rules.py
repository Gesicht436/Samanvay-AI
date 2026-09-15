"""
Unit Tests for Rotating & Electrical Engineering Tolerance Rules:
- IEC 60034 & IS/IEC 60079: Flameproof Electric Motors
- API 682: Mechanical Seals & Piping Plans
- ISO 15: Rolling Bearings & Radial Internal Clearance
"""

import pytest
from backend.app.contracts.material import ExtractedMaterialAttributes
from backend.app.contracts.matching import EquivalenceTier
from backend.app.matching.tolerance import evaluate_compatibility


class TestRotatingAndElectricalRules:

    def test_motor_flameproof_exact_parity(self):
        """Test identical flameproof motor specifications yield Tier-1 Identical."""
        source = ExtractedMaterialAttributes(
            item_type="MOTOR_FLAMEPROOF",
            power_kw=37.0,
            poles=4,
            speed_rpm=1500,
            hazardous_cert="Ex d IIC T4",
            raw_description="MTR 37KW 4P 415V Ex-d IIC T4"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="MOTOR_FLAMEPROOF",
            power_kw=37.0,
            poles=4,
            speed_rpm=1500,
            hazardous_cert="Ex d IIC T4",
            raw_description="MOTOR FLAMEPROOF 37KW 4 POLE 1500RPM EX D IIC T4"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_1_IDENTICAL
        assert res.is_compatible is True
        assert len(res.violations) == 0

    def test_motor_hazardous_area_explosion_trap(self):
        """Test non-Ex safe area motor proposed for Zone 1 is strictly rejected (Fatal Explosion Trap)."""
        source = ExtractedMaterialAttributes(
            item_type="MOTOR_FLAMEPROOF",
            power_kw=37.0,
            poles=4,
            hazardous_cert="Ex d IIC T4"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="MOTOR_FLAMEPROOF",
            power_kw=37.0,
            poles=4,
            hazardous_cert="Non-Ex"  # Safe area motor in refinery hazardous zone!
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert res.is_compatible is False
        assert any("EXPLOSION TRAP" in v.message for v in res.violations)

    def test_motor_power_overload_trap(self):
        """Test proposed under-rated motor (22 kW for 30 kW requirement) is strictly rejected."""
        source = ExtractedMaterialAttributes(
            item_type="MOTOR_FLAMEPROOF",
            power_kw=30.0,
            poles=4,
            hazardous_cert="Ex d IIC T4"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="MOTOR_FLAMEPROOF",
            power_kw=22.0,  # Under-powered!
            poles=4,
            hazardous_cert="Ex d IIC T4"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert res.is_compatible is False
        assert any("OVERLOAD TRAP" in v.message for v in res.violations)

    def test_motor_power_valid_upgrade(self):
        """Test proposed higher motor power (37 kW for 30 kW pump drive) is a valid Tier-2 upgrade."""
        source = ExtractedMaterialAttributes(
            item_type="MOTOR_FLAMEPROOF",
            power_kw=30.0,
            poles=4,
            hazardous_cert="Ex d IIC T4"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="MOTOR_FLAMEPROOF",
            power_kw=37.0,  # Safe upgrade
            poles=4,
            hazardous_cert="Ex d IIC T4"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_2_SUBSTITUTE
        assert res.is_compatible is True
        assert res.requires_hitl is True
        assert any(p.parameter == "Shaft Power Rating" and p.status == "UPGRADE" for p in res.parameter_checks)

    def test_motor_pole_speed_mismatch_trap(self):
        """Test pole count mismatch (2-pole vs 4-pole) is strictly rejected."""
        source = ExtractedMaterialAttributes(
            item_type="MOTOR_FLAMEPROOF",
            power_kw=37.0,
            poles=4,  # 1500 RPM
            hazardous_cert="Ex d IIC T4"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="MOTOR_FLAMEPROOF",
            power_kw=37.0,
            poles=2,  # 3000 RPM (2x speed!)
            hazardous_cert="Ex d IIC T4"
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert res.is_compatible is False
        assert any("HYDRAULIC COLLAPSE TRAP" in v.message for v in res.violations)

    def test_mechanical_seal_flush_plan_downgrade_trap(self):
        """Test downgrading API 682 Plan 53A barrier flush to Plan 11 is strictly rejected."""
        source = ExtractedMaterialAttributes(
            item_type="MECHANICAL_SEAL",
            size_nb_mm=50.0,
            seal_plan="Plan 53A"  # Pressurized dual barrier
        )
        candidate = ExtractedMaterialAttributes(
            item_type="MECHANICAL_SEAL",
            size_nb_mm=50.0,
            seal_plan="Plan 11"  # Unpressurized single flush!
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert res.is_compatible is False
        assert any("TOXIC SEAL BLOWOUT TRAP" in v.message for v in res.violations)

    def test_bearing_clearance_thermal_seizure_trap(self):
        """Test substituting high-temp pump C3 clearance bearing with normal CN clearance is rejected."""
        source = ExtractedMaterialAttributes(
            item_type="BEARING_ROLLER",
            bearing_bore_mm=50.0,
            bearing_clearance="C3"  # Thermal expansion margin
        )
        candidate = ExtractedMaterialAttributes(
            item_type="BEARING_ROLLER",
            bearing_bore_mm=50.0,
            bearing_clearance="CN"  # Normal clearance -> Thermal seizure!
        )
        res = evaluate_compatibility(source, candidate)
        assert res.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert res.is_compatible is False
        assert any("BEARING SEIZURE TRAP" in v.message for v in res.violations)
