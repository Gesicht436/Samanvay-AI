# Matching

Candidate retrieval is a blocking step. Deterministic validation then enforces exact size matching, directional pressure substitution, and explicit ASTM metallurgy upgrades. Tier-3 candidates are never auto-suggested. Confidence routing is: 90% and above auto-link, 70% through 90% HITL, below 70% manual entry.

The retrieval response includes safety violations and a `Tier` classification: size mismatches, pressure or metallurgy downgrades, incompatible item types, and incompatible valve standards are `Tier-4-Reject`. Otherwise scores at or above 0.85 are Tier-1, scores from 0.60 through 0.84 are Tier-3, and scores below 0.60 are Tier-4-Reject. A configured compatibility reranker adds human-readable reasons; its absence preserves cosine-only ranking.

Known PN designations are mapped to their conventional ASME pressure class. Unknown PN values are left unclassified rather than treated as though the PN number were itself an ASME class. Review items are exposed through `/v1/match/hitl-queue`, can be resolved at `/v1/match/hitl-resolve`, and can be seeded at `/v1/match/hitl-bootstrap`.
