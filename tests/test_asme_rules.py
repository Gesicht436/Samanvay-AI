"""
Unit Tests for Deterministic ASME B16.5 & ASTM Tolerance Engine.
Verifies:
- 100% precision on safety invariants (zero tolerance on size, pressure down-rating, metallurgy downgrades)
- Accurate categorization into Tier-1 (Identical), Tier-2 (Substitute), and Tier-3 (Incompatible)
"""

import pytest
from backend.app.contracts.material import ExtractedMaterialAttributes
from backend.app.contracts.matching import EquivalenceTier, MatchCandidate
from backend.app.matching.tolerance import evaluate_compatibility, evaluate_candidate_pool


class TestASMESafetyInvariants:

    def test_tier_1_exact_match(self):
        """Test identical physical specifications yield Tier-1 Identical."""
        source = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=100.0,
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RF",
            raw_description="FLG WNRF 4IN 300# A105"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=100.0,
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RF",
            raw_description="FLANGE WELD NECK 4\" CL300 ASTM A105 RF"
        )
        result = evaluate_compatibility(source, candidate)
        assert result.tier == EquivalenceTier.TIER_1_IDENTICAL
        assert result.is_compatible is True
        assert len(result.violations) == 0
        assert result.requires_hitl is False
        assert "Tier-1 Identical" in result.rationale

    def test_tier_3_size_mismatch_zero_tolerance(self):
        """Test zero-tolerance on physical nominal bore size."""
        source = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=100.0,
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RF"
        )
        # Candidate is 80mm (3") instead of 100mm (4")
        candidate = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=80.0,
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RF"
        )
        result = evaluate_compatibility(source, candidate)
        assert result.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert result.is_compatible is False
        assert any(v.field == "size_nb_mm" for v in result.violations)
        assert "bore size mismatch" in result.violations[0].message

    def test_tier_3_pressure_down_rating_trap(self):
        """Test strict blocking of pressure down-rating (Class 150 cannot replace Class 300)."""
        source = ExtractedMaterialAttributes(
            item_type="GATE_VALVE",
            size_nb_mm=50.0,
            pressure_class=300,
            metallurgy="ASTM A216 WCB",
            facing_end="RF"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="GATE_VALVE",
            size_nb_mm=50.0,
            pressure_class=150,  # DANGEROUS DOWN-RATING!
            metallurgy="ASTM A216 WCB",
            facing_end="RF"
        )
        result = evaluate_compatibility(source, candidate)
        assert result.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert result.is_compatible is False
        assert any("rupture" in v.message.lower() for v in result.violations)

    def test_tier_2_pressure_up_rating(self):
        """Test higher pressure rating (Class 600 replacing Class 300) is a valid Tier-2 upgrade."""
        source = ExtractedMaterialAttributes(
            item_type="GATE_VALVE",
            size_nb_mm=50.0,
            pressure_class=300,
            metallurgy="ASTM A216 WCB",
            facing_end="RF"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="GATE_VALVE",
            size_nb_mm=50.0,
            pressure_class=600,  # UP-RATING
            metallurgy="ASTM A216 WCB",
            facing_end="RF"
        )
        result = evaluate_compatibility(source, candidate)
        assert result.tier == EquivalenceTier.TIER_2_SUBSTITUTE
        assert result.is_compatible is True
        assert result.requires_hitl is True
        assert len(result.violations) == 0
        assert any(p.parameter == "Pressure Class" and p.status == "UPGRADE" for p in result.parameter_checks)

    def test_tier_2_metallurgy_upgrade_cs_to_ss(self):
        """Test upgrading carbon steel A105 to stainless steel SS316 is a safe Tier-2 substitute."""
        source = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=100.0,
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RF"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=100.0,
            pressure_class=300,
            metallurgy="ASTM A182 F316",  # SAFE UPGRADE
            facing_end="RF"
        )
        result = evaluate_compatibility(source, candidate)
        assert result.tier == EquivalenceTier.TIER_2_SUBSTITUTE
        assert result.is_compatible is True
        assert result.requires_hitl is True
        assert any(p.parameter == "Metallurgy" and p.status == "UPGRADE" for p in result.parameter_checks)

    def test_tier_2_metallurgy_upgrade_a105_to_lf2(self):
        """Test upgrading A105 to low-temperature certified A350 LF2."""
        source = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=50.0,
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RF"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=50.0,
            pressure_class=300,
            metallurgy="ASTM A350 LF2",
            facing_end="RF"
        )
        result = evaluate_compatibility(source, candidate)
        assert result.tier == EquivalenceTier.TIER_2_SUBSTITUTE
        assert result.is_compatible is True

    def test_tier_3_metallurgy_downgrade_ss_to_cs_trap(self):
        """Test dangerous downgrade: substituting stainless SS316 with carbon steel A105."""
        source = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=100.0,
            pressure_class=300,
            metallurgy="ASTM A182 F316",  # Requires stainless
            facing_end="RF"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=100.0,
            pressure_class=300,
            metallurgy="ASTM A105",  # FATAL DOWNGRADE
            facing_end="RF"
        )
        result = evaluate_compatibility(source, candidate)
        assert result.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert result.is_compatible is False
        assert any("FATAL DOWNGRADE" in v.message for v in result.violations)

    def test_tier_3_cryogenic_lf2_to_a105_trap(self):
        """Test cryogenic safety trap: substituting impact-tested LF2 with standard A105."""
        source = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=50.0,
            pressure_class=300,
            metallurgy="ASTM A350 LF2",  # Low-temperature service
            facing_end="RF"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=50.0,
            pressure_class=300,
            metallurgy="ASTM A105",  # Lacks impact toughness!
            facing_end="RF"
        )
        result = evaluate_compatibility(source, candidate)
        assert result.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert result.is_compatible is False
        assert any("CRYOGENIC SAFETY TRAP" in v.message for v in result.violations)

    def test_tier_3_facing_incompatibility_rf_vs_rtj(self):
        """Test Raised Face (RF) cannot mate with Ring Type Joint (RTJ)."""
        source = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=100.0,
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RF"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=100.0,
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RTJ"  # Deep ring groove!
        )
        result = evaluate_compatibility(source, candidate)
        assert result.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert result.is_compatible is False
        assert any("FACING MISMATCH" in v.message for v in result.violations)

    def test_tier_3_item_type_mismatch(self):
        """Test Gate Valve cannot be replaced by Ball Valve."""
        source = ExtractedMaterialAttributes(
            item_type="GATE_VALVE",
            size_nb_mm=100.0,
            pressure_class=150,
            metallurgy="ASTM A216 WCB",
            facing_end="RF"
        )
        candidate = ExtractedMaterialAttributes(
            item_type="BALL_VALVE",
            size_nb_mm=100.0,
            pressure_class=150,
            metallurgy="ASTM A216 WCB",
            facing_end="RF"
        )
        result = evaluate_compatibility(source, candidate)
        assert result.tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert result.is_compatible is False
        assert any(v.field == "item_type" for v in result.violations)

    def test_evaluate_candidate_pool_sorting(self):
        """Test candidate pool sorting places Tier-1 first, then Tier-2, then Tier-3."""
        source = ExtractedMaterialAttributes(
            item_type="FLANGE_WELD_NECK",
            size_nb_mm=100.0,
            pressure_class=300,
            metallurgy="ASTM A105",
            facing_end="RF"
        )
        candidates = [
            MatchCandidate(
                canonical_id="CAN-003",
                description="Mismatched Size Flange",
                vector_score=0.92,
                attributes=ExtractedMaterialAttributes(
                    item_type="FLANGE_WELD_NECK",
                    size_nb_mm=150.0,  # Size mismatch -> Tier-3
                    pressure_class=300,
                    metallurgy="ASTM A105",
                    facing_end="RF"
                )
            ),
            MatchCandidate(
                canonical_id="CAN-002",
                description="Stainless Upgrade Flange",
                vector_score=0.88,
                attributes=ExtractedMaterialAttributes(
                    item_type="FLANGE_WELD_NECK",
                    size_nb_mm=100.0,
                    pressure_class=300,
                    metallurgy="ASTM A182 F316",  # Upgrade -> Tier-2
                    facing_end="RF"
                )
            ),
            MatchCandidate(
                canonical_id="CAN-001",
                description="Exact Match Flange",
                vector_score=0.95,
                attributes=ExtractedMaterialAttributes(
                    item_type="FLANGE_WELD_NECK",
                    size_nb_mm=100.0,
                    pressure_class=300,
                    metallurgy="ASTM A105",  # Exact -> Tier-1
                    facing_end="RF"
                )
            ),
        ]
        results = evaluate_candidate_pool(source, candidates)
        assert len(results) == 3
        assert results[0].tier == EquivalenceTier.TIER_1_IDENTICAL
        assert results[0].candidate_canonical_id == "CAN-001"
        assert results[1].tier == EquivalenceTier.TIER_2_SUBSTITUTE
        assert results[1].candidate_canonical_id == "CAN-002"
        assert results[2].tier == EquivalenceTier.TIER_3_INCOMPATIBLE
        assert results[2].candidate_canonical_id == "CAN-003"
