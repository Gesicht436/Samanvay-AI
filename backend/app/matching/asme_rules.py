from dataclasses import dataclass


# Explicit upgrade paths: the destination grade is at least as corrosion resistant.
ALLOY_UPGRADES: dict[str, set[str]] = {
    "304": {"304L", "316", "316L"},
    "304L": {"316", "316L"},
    "316": {"316L"},
    "A105": {"F316", "F316L"},
}


@dataclass(frozen=True)
class RuleDecision:
    allowed: bool
    reason: str


def size_matches(requested: float | None, candidate: float | None) -> RuleDecision:
    if requested is None or candidate is None:
        return RuleDecision(True, "size not provided")
    return RuleDecision(requested == candidate, "exact size match" if requested == candidate else "size mismatch")


def pressure_substitutes(requested: int | None, candidate: int | None) -> RuleDecision:
    if requested is None or candidate is None:
        return RuleDecision(True, "pressure class not provided")
    allowed = candidate >= requested
    return RuleDecision(allowed, "pressure upgrade allowed" if allowed else "pressure downgrade rejected")


def metallurgy_substitutes(requested: str | None, candidate: str | None) -> RuleDecision:
    if not requested or not candidate or requested.casefold() == candidate.casefold():
        return RuleDecision(True, "metallurgy matches or is not provided")
    allowed = candidate.upper() in {item.upper() for item in ALLOY_UPGRADES.get(requested, set())}
    return RuleDecision(allowed, "approved alloy upgrade" if allowed else "unapproved alloy substitution")
