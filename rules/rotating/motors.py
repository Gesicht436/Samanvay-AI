"""
Module 11 (Part 1): Electric Motors & Hazardous Area Enclosures (IS/IEC 60079 / IEEE 841).

Rules:
1. Hazardous Area Ex Enclosure (IS/IEC 60079):
   - In refinery Zone 1 or Zone 2, motors must carry flameproof certification (Ex d IIC T4 Gb).
   - Proposing a non-Ex motor in hazardous zones = Tier-3 Fatal Explosion Trap.
2. Synchronous Speed / Pole Count Parity:
   - Substituting a 2-pole (3000 RPM) motor for a 4-pole (1500 RPM) drive quadruples head
     and causes Tier-3 Hydraulic Shock / Pump Casing Rupture.
3. Power (kW) Under-Rating:
   - Candidate kW < required kW causes motor overheating and trip = Tier-3 Overload Tripping Trap.
4. Electrical Invariants:
   - Voltage mismatch (e.g. 415V vs 230V) = Tier-3 Incompatible.
   - Frequency mismatch (e.g. 50Hz vs 60Hz) = Tier-3 Incompatible.
5. Ingress Protection (IP Rating):
   - IP downgrade (e.g. IP65 -> IP54) = Tier-3 Incompatible.
   - IP upgrade (e.g. IP54 -> IP65) = Tier-2 Substitute.
"""

import re
from typing import Optional, Tuple, Dict, Any
from backend.app.schemas.material import DynamicCompatibilityTier, RuleViolation


def _parse_num(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    m = re.search(r'[-+]?\d*\.?\d+', str(val))
    return float(m.group(0)) if m else None


def check_motor_compatibility(
    query_props: Dict[str, Any],
    cand_props: Dict[str, Any],
) -> Tuple[DynamicCompatibilityTier, float, Optional[RuleViolation]]:
    """
    Evaluates electric motor flameproof enclosures, speed, power, voltage, and IP rating.
    """
    # 1. Hazardous Area Ex Rating
    q_ex = query_props.get("ex_rating")
    c_ex = cand_props.get("ex_rating")
    q_zone_str = str(query_props.get("zone") or query_props.get("area", "")).upper()
    c_zone_str = str(cand_props.get("zone") or cand_props.get("area", "")).upper()
    is_q_hazardous = q_ex or "ZONE_1" in q_zone_str or "ZONE 1" in q_zone_str or "ZONE_2" in q_zone_str or "EX" in q_zone_str or query_props.get("zone") in (1, 2)
    is_c_safe_only = not c_ex and ("SAFE" in c_zone_str or "NON_EX" in c_zone_str or not is_q_hazardous)

    if is_q_hazardous and (not c_ex or is_c_safe_only):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="IEC_60079_MOTOR_EX",
                standard_code="IS/IEC 60079-1",
                failure_mode_prevented="Electric spark igniting explosive vapor atmosphere in refinery unit",
                explanation="FATAL EXPLOSION TRAP: Non-Ex standard motor proposed for hazardous Zone 1/2 area. Flameproof enclosure (Ex d IIC T4 Gb) is mandatory.",
            ),
        )

    # 2. Synchronous Speed / Pole Mismatch
    q_poles = query_props.get("poles") or query_props.get("pole_count")
    c_poles = cand_props.get("poles") or cand_props.get("pole_count")
    q_rpm = _parse_num(query_props.get("rpm"))
    c_rpm = _parse_num(cand_props.get("rpm"))

    if (q_poles and c_poles and q_poles != c_poles) or (q_rpm and c_rpm and abs(q_rpm - c_rpm) > 100):
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="MOTOR_POLE_MISMATCH",
                standard_code="IS 325 / IEC 60034",
                failure_mode_prevented="Hydraulic head surge and pump casing overpressure blowout",
                explanation="HYDRAULIC SHOCK TRAP: Motor pole count or synchronous speed mismatch (e.g. 3000 RPM vs 1500 RPM). Running a 1500 RPM pump at 3000 RPM quadruples head and causes catastrophic casing rupture.",
            ),
        )

    # 3. Power (kW) Under-Rating
    q_kw = _parse_num(query_props.get("power_kw") or query_props.get("kw"))
    c_kw = _parse_num(cand_props.get("power_kw") or cand_props.get("kw"))
    if q_kw and c_kw and c_kw < q_kw:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="MOTOR_POWER_UNDER_RATING",
                standard_code="IEC 60034-1",
                failure_mode_prevented="Motor thermal winding burnout and frequent trip under full pump load",
                explanation=f"MOTOR OVERLOAD TRAP: Candidate power {c_kw} kW is below required {q_kw} kW.",
            ),
        )

    # 4. Voltage Mismatch
    q_volt = str(query_props.get("voltage", "")).upper().replace(" ", "")
    c_volt = str(cand_props.get("voltage", "")).upper().replace(" ", "")
    if q_volt and c_volt and q_volt != c_volt:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="MOTOR_VOLTAGE",
                standard_code="IEC 60038",
                failure_mode_prevented="Motor winding insulation breakdown or phase under-voltage tripping",
                explanation=f"VOLTAGE MISMATCH: Query requires '{q_volt}', candidate is rated for '{c_volt}'.",
            ),
        )

    # 5. Frequency Mismatch
    q_freq = str(query_props.get("frequency", "")).upper().replace(" ", "")
    c_freq = str(cand_props.get("frequency", "")).upper().replace(" ", "")
    if q_freq and c_freq and q_freq != c_freq:
        return (
            DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
            0.0,
            RuleViolation(
                module_name="MOTOR_FREQUENCY",
                standard_code="IEC 60034",
                failure_mode_prevented="Motor magnetic core saturation and excessive slip heating",
                explanation=f"FREQUENCY MISMATCH: Query requires '{q_freq}', candidate is rated for '{c_freq}'.",
            ),
        )

    # 6. Ingress Protection (IP Rating)
    q_ip = str(query_props.get("ip_rating", "")).upper().replace(" ", "")
    c_ip = str(cand_props.get("ip_rating", "")).upper().replace(" ", "")
    if q_ip.startswith("IP") and c_ip.startswith("IP"):
        try:
            q_code = int(q_ip.replace("IP", "")[:2])
            c_code = int(c_ip.replace("IP", "")[:2])
            if c_code < q_code:
                return (
                    DynamicCompatibilityTier.TIER_3_INCOMPATIBLE,
                    0.0,
                    RuleViolation(
                        module_name="MOTOR_IP_RATING",
                        standard_code="IEC 60529",
                        failure_mode_prevented="Water ingress and dust penetration into electrical windings",
                        explanation=f"IP RATING DOWNGRADE: Candidate protection {c_ip} is lower than required {q_ip}.",
                    ),
                )
            elif c_code > q_code:
                return (DynamicCompatibilityTier.TIER_2_SUBSTITUTE, 0.94, None)
        except ValueError:
            pass

    return (DynamicCompatibilityTier.TIER_1_IDENTICAL, 1.0, None)
