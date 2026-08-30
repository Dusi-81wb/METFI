# METFI Testing Specification & Quality Assurance

**Project:** METFI (Autonomous Finance Controller)  
**Testing Frameworks:** Pytest (Backend) + Jest/Vitest/Next Build (Frontend)  
**Quality Standards:** Competition Grade / Production Ready  
**Status:** Certified Generalization Suite (Remediation Round 01)  

---

## 1. Testing Philosophy

Testing in METFI is a continuous requirement throughout development. Because METFI handles financial reconciliation:
- **No silent failures:** Mathematical discrepancies, schema errors, and date violations must fail with clear diagnostics.
- **Evidence before assertions:** All claims of system performance or accuracy must be backed by executed test suites.
- **Independent Generalization Verification:** Deterministic matching must pass 100% of independent fixture tests with zero dependency on synthetic generator logic.

---

## 2. Test Architecture & Structure

```text
backend/tests/
├── unit/
│   ├── test_generator_independent.py           # Pure independent tests + generator deletion regression
│   ├── test_fee_tax_matrix.py                  # Matrix across fee rates (1.5%-3.5%) & tax rates (0%-25%)
│   ├── test_partial_and_ambiguity_generalization.py # Arbitrary partial ratios (30%-90%) & candidate ties
│   ├── test_candidate_matcher_safety.py        # Customer isolation guard & candidate ambiguity detection
│   ├── test_candidate_matcher.py               # Candidate generation, hash indexing, Levenshtein recovery
│   ├── test_evidence_extractor.py              # Monetary, currency, timing, reference, cardinality extraction
│   ├── test_reconciliation_engine.py           # 10 canonical exception classes and exact match testing
│   ├── test_classification_precedence.py       # Multi-fault adversarial precedence tests
│   ├── test_policy_engine.py                   # Deterministic policy outcome gatekeeping
│   ├── test_evaluation_metrics.py              # Accuracy, macro-F1, FMR, and confusion matrix testing
│   ├── test_ground_truth_isolation.py          # Adversarial leakage, schema whitelist, opaque ID tests
│   ├── test_security_sanitization.py           # Dataset ID path traversal and injection prevention
│   ├── test_time.py                            # Strict UTC ISO 8601 parsing & date-only rejection
│   ├── test_money.py                           # Decimal quantization and float rejection
│   ├── test_corruption.py                      # 10 deterministic corruption operators
│   ├── test_generator.py                       # Deterministic synthetic dataset generator & distribution
│   ├── test_invariants.py                      # Mathematical and structural integrity invariants
│   ├── test_normalizer.py                      # Raw to canonical normalization pipeline
│   └── test_schemas.py                         # Raw ingest schema validation
├── integration/
│   ├── test_reconciliation_pipeline.py         # End-to-end reconciliation service and FastAPI routes
│   ├── test_dataset_generation_pipeline.py     # End-to-end dataset export and reload
│   └── test_db_persistence.py                   # PostgreSQL persistence and retrieval
└── fixtures/
    └── reconciliation_independent/             # Permanent, hand-authored independent scenario fixtures
        ├── exact_match.json
        ├── amount_mismatch.json
        ├── partial_settlement_matrix.json
        ├── fee_tax_policy_matrix.json
        ├── missing_settlement.json
        ├── duplicate_record.json
        ├── date_mismatch.json
        ├── reference_mismatch.json
        ├── currency_mismatch.json
        └── ambiguous_scenarios.json
```

---

## 3. Test Suites & Commands

### 3.1 Backend Tests
- **Run all unit & integration tests:**
  ```bash
  uv run pytest -v
  ```
- **Run with code coverage:**
  ```bash
  uv run pytest --cov=app --cov-report=term-missing
  ```
- **Run independent fixture tests:**
  ```bash
  uv run pytest tests/unit/test_generator_independent.py tests/unit/test_fee_tax_matrix.py tests/unit/test_partial_and_ambiguity_generalization.py tests/unit/test_candidate_matcher_safety.py -v
  ```

### 3.2 Evaluation Benchmark CLI
```bash
# Run reconciliation benchmark suite (Synthetic + Independent)
uv run python evaluation/benchmarks/runner.py --suite all

# Run AI investigation evaluation suite (Deterministic vs AI vs Verified AI)
uv run python evaluation/benchmarks/ai_runner.py --provider mock
```
