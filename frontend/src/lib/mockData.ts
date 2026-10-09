import type { MatchResult } from "./types";

export const mockMatch: MatchResult = { raw_description: "SS flange 100 NB, class 150", tier: "Tier-2", confidence: 0.84, routing: "hitl", reasons: ["exact size match", "pressure upgrade allowed"], candidate: { canonical_id: "CAN-DEMO-001", similarity: 0.84, item_type: "flange", size_nb_mm: 100, pressure_class: 150, metallurgy: "316L", standard: "ASME B16.5", canonical_description: "Stainless steel flange 100 NB class 150" }, matches: [] };
