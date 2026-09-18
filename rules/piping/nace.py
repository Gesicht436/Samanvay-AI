"""
Module 4 (Part 1): NACE MR0175 / ISO 15156 Sour Hydrocarbon Service.

Rules:
1. Sour Service Hardness Invariant:
   - For wet H2S duty, carbon steels must satisfy hardness <= 22 HRC, heat-treated,
     and carry certified SSC / HIC resistance.
2. Non-NACE Material Prohibition:
   - Supplying commercial non-NACE material in sour duty is blocked as Tier-3 Incompatible
     (catastrophic sulfide stress cracking blowout).
"""

from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def check_nace_sour_service(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates NACE MR0175 / ISO 15156 sour hydrocarbon compliance.
    """
    nace_req = query_props.get("nace_mr0175", False) or query_props.get("nace_required", False) or query_props.get("sour_service", False)
    cand_compliant = cand_props.get("nace_mr0175", cand_props.get("nace_compliant", True))
    if "nace_compliant" not in cand_props and "nace_mr0175" not in cand_props and "nace" in str(cand_props).lower():
        cand_compliant = True

    if nace_req and not cand_compliant:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="NACE_MR0175_SOUR",
                standard_code="NACE MR0175 / ISO 15156",
                failure_mode_prevented="Catastrophic sulfide stress cracking (SSC) and hydrogen-induced cracking (HIC)",
                explanation=(
                    "SOUR SERVICE VIOLATION: Process medium contains wet H2S. Candidate material lacks "
                    "NACE MR0175 certification (hardness <= 22 HRC and HIC/SSC resistance), risking "
                    "catastrophic brittle sulfide stress cracking blowout."
                ),
            ),
        )

    # Check hardness if specified
    cand_hardness = cand_props.get("hardness_max_hrc", cand_props.get("hardness_hrc"))
    if nace_req and cand_hardness is not None:
        try:
            if float(cand_hardness) > 22.0:
                return (
                    DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                    0.0,
                    RuleViolation(
                        module_name="NACE_MR0175_HARDNESS",
                        standard_code="NACE MR0175 clause A.2.1.2",
                        failure_mode_prevented="Sulfide stress cracking in high hardness carbon steel",
                        explanation=f"NACE HARDNESS VIOLATION: Candidate hardness is {cand_hardness} HRC, exceeding NACE ceiling of 22 HRC.",
                    ),
                )
        except (ValueError, TypeError):
            pass

    # Sour service safe upgrade
    if not nace_req and cand_compliant and (cand_props.get("nace_mr0175") is True or "B7M" in str(cand_props)):
        return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.90, None)

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
