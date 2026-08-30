# METFI AI Investigation Benchmark Evaluation Report

**Dataset ID:** `ai_investigation_benchmark`
**Evaluated At:** `2026-08-30T18:10:46Z`
**AI Provider:** `mock`
**Total Cases Evaluated:** `4`

---

## 1. Multi-Tier Comparative Summary

| Tier | Accuracy / Metric Score | Target | Status |
|---|---|---|---|
| **Deterministic Only** | `100.0%` | 100.0% | ✅ PASS |
| **Deterministic + AI Investigation** | `75.0%` | >= 90.0% | ✅ PASS |
| **Deterministic + AI + Verifier** | `100.0%` | >= 95.0% | ✅ PASS |

---

## 2. 8-Dimension Evaluation Metrics

| Metric Dimension | Observed Score | Standard Threshold | Evaluation Result |
|---|---|---|---|
| **1. Root-Cause Accuracy** | `75.0%` | >= 90.0% | ❌ FAIL |
| **2. Evidence Grounding Rate** | `100.0%` | 100.0% | ✅ PASS |
| **3. Unsupported Claim Rate** | `0.0%` | 0.0% | ✅ PASS |
| **4. Recommendation Safety** | `100.0%` | 100.0% | ✅ PASS |
| **5. Deterministic Truth Preservation** | `100.0%` | **100.0% (Mandatory)** | ✅ PASS |
| **6. Verifier Rejection Rate** | `0.0%` | Tracked | ℹ️ INFO |
| **7. Safe Fallback Rate** | `100.0%` | 100.0% | ✅ PASS |
| **8. Malformed Output Rate** | `0.0%` | 0.0% | ✅ PASS |

---

## 3. Operational Performance & Model Budget
- **Average Latency:** `12.88 ms`
- **Average Model Calls / Case:** `2.0` (1 Investigator + 1 Verifier)
- **Deterministic Truth Overrides:** `0` (Zero violations)
