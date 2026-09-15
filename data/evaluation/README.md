# Golden Benchmark Evaluation Suite (`data/evaluation`)

## 1. Overview
The `evaluation` package provides an automated, objective evaluation benchmark for Samanvay-AI.

In safety-critical procurement systems, standard machine learning benchmarks (like generic F1 score or top-5 accuracy) are insufficient. A model that achieves 99% accuracy but approves a Class 150 flange on a Class 600 sour gas line represents a catastrophic safety failure.

The **Golden Benchmark** consists of 150 curated cross-CPSE test cases designed to rigorously test every ASME, ASTM, and IBR boundary condition.

---

## 2. Benchmark Composition (150 Test Cases)

| Category | Cases | Target Tier | Description & Safety Requirements |
|---|---|---|---|
| **Tier-1 Identical Matches** | 50 | `TIER_1_IDENTICAL` | Exact physical parity across disparate enterprise naming conventions. Must achieve 100% recall. |
| **Tier-2 Functional Upgrades** | 50 | `TIER_2_SUBSTITUTE` | Safe engineering upgrades (e.g. Class 600 for Class 300, SS316 for A105, heavier wall schedule). Must route to HITL triage. |
| **Tier-3 Fatal Safety Traps** | 50 | `TIER_3_INCOMPATIBLE` | Hazardous substitutions (pressure down-rating, metallurgy down-grading, non-IBR on steam, non-NACE in sour service). **Zero False Positives allowed.** |

---

## 3. The 50 Fatal Safety Traps Tested

The Tier-3 evaluation covers subtle, hazardous errors that trip up generic AI models:
1. Pressure Down-Rating: Substituting Class 150 on Class 300 lines, or Class 300 on Class 600 lines.
2. Metallurgical Downgrades:
   - Replacing acid-resistant Stainless Steel F316 with Carbon Steel A105.
   - Replacing Molybdenum-bearing Stainless Steel F316 with SS304 in chloride service.
   - Replacing low-temperature impact-tested ASTM A350 LF2 with standard A105 in cryogenic piping.
   - Replacing Super Duplex S32750 with standard Austenitic stainless steel.
3. Mating Face Mismatch: Pairing Raised Face (RF) with Ring Type Joint (RTJ) or Flat Face (FF).
4. Pipe Wall Thinning: Substituting SCH 40 on a line engineered for high-pressure SCH 80 or SCH 160.
5. Large Flange Series Mismatch: Mixing ASME B16.47 Series A with Series B (different bolt hole counts).
6. Statutory Non-Compliance: Deploying a non-IBR certified part where Indian Boiler Regulations (IBR 1950) certification is legally mandatory.

---

## 4. Running the Benchmark

Execute the automated benchmark runner:
```powershell
uv run python data/evaluation/run_benchmark.py
```

### Expected Output
```
=======================================================
   SAMANVAY-AI GOLDEN BENCHMARK EVALUATION SUITE
   Executing 150 curated edge cases across IOCL, ONGC & BPCL
=======================================================

-------------------------------------------------------
  EVALUATION RESULTS SUMMARY
-------------------------------------------------------
  Total Test Cases Evaluated : 150
  Overall Classification Acc : 100.00%
  Tier-1 Identical Recall    : 100.00% (50/50)
  Tier-2 Substitute Recall   : 100.00% (50/50)
  Tier-3 Trap Rejection Rate : 100.00% (50/50)
  Tier-3 False Positives     : 0 (MUST BE 0)
  ASME Safety Precision      : 100.00%
  Average Latency per Item   : 0.25 ms
  Total Benchmark Time       : 0.038 s
-------------------------------------------------------
Saved full benchmark audit report to data/evaluation/benchmark_report.json
ALL ASME & ASTM SAFETY INVARIANTS SATISFIED (100% PRECISION)
```

The detailed test report is written to `data/evaluation/benchmark_report.json` with per-test latency, violations caught, and rationale strings.
