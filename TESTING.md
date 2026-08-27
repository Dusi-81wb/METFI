# METFI Testing Specification & Quality Assurance

**Project:** METFI (Autonomous Finance Controller)  
**Testing Frameworks:** Pytest (Backend) + Jest/Vitest/Next Build (Frontend)  
**Quality Standards:** Competition Grade / Production Ready  

---

## 1. Testing Philosophy

Testing in METFI is a continuous requirement throughout development. Because METFI handles financial reconciliation:
- **No silent failures:** Mathematical discrepancies, schema errors, and date violations must fail with clear diagnostics.
- **Evidence before assertions:** All claims of system performance or accuracy must be backed by executed test suites.
- **Deterministic Golden Sets:** Deterministic matching must pass 100% of golden regression fixtures.

---

## 2. Test Classification & Architecture

```text
tests/
├── unit/
│   ├── test_candidate_matcher.py       # Candidate generation, hash indexing, and Levenshtein recovery
│   ├── test_evidence_extractor.py      # Monetary, currency, timing, reference, cardinality extraction
│   ├── test_reconciliation_engine.py   # 10 canonical exception classes and exact match testing
│   ├── test_classification_precedence.py # Multi-fault adversarial precedence tests
│   ├── test_policy_engine.py           # Deterministic policy outcome gatekeeping
│   ├── test_evaluation_metrics.py      # Accuracy, macro-F1, FMR, and confusion matrix testing
│   ├── test_ground_truth_isolation.py  # Adversarial leakage, schema whitelist, and opaque ID tests
│   ├── test_security_sanitization.py   # Dataset ID path traversal and injection prevention
│   ├── test_time.py                    # Strict UTC ISO 8601 parsing & date-only rejection
│   ├── test_money.py                   # Decimal quantization and float rejection
│   ├── test_corruption.py              # 10 deterministic corruption operators
│   ├── test_generator.py               # Deterministic synthetic dataset generator & distribution
│   ├── test_invariants.py              # Mathematical and structural integrity invariants
│   ├── test_normalizer.py              # Raw to canonical normalization pipeline
│   └── test_schemas.py                 # Raw ingest schema validation
├── integration/
│   ├── test_reconciliation_pipeline.py # End-to-end reconciliation service and FastAPI routes
│   ├── test_dataset_generation_pipeline.py  # End-to-end dataset export and reload
│   └── test_db_persistence.py               # PostgreSQL persistence and retrieval
└── golden/
    └── test_golden_fixtures.py         # Golden benchmark fixtures across all 10 exception classes
```

---

## 3. Test Suites & Commands

### 3.1 Backend Tests
- **Run all unit & integration tests:**
  ```bash
  pytest -v
  ```
- **Run with code coverage:**
  ```bash
  pytest --cov=app --cov-report=term-missing
  ```
- **Run only smoke tests:**
  ```bash
  pytest -m smoke
  ```

### 3.2 Backend Code Quality & Typing
- **Linter & Code Formatting (Ruff):**
  ```bash
  ruff check app tests
  ruff format --check app tests
  ```
- **Static Type Checking (Mypy):**
  ```bash
  mypy app
  ```

### 3.3 Frontend Testing & Verification
- **Type Checking:**
  ```bash
  cd frontend && npm run type-check
  ```
- **Linting:**
  ```bash
  cd frontend && npm run lint
  ```
- **Production Build Verification:**
  ```bash
  cd frontend && npm run build
  ```

---

## 4. Acceptance Gates for Phase Hand-offs

A phase cannot be submitted for Prime adversarial review unless all the following gates pass:

1. `pytest` passes with 0 failures and 0 errors.
2. `ruff check` reports zero linting errors.
3. `mypy` reports zero type errors.
4. `npm run build` inside `frontend/` succeeds cleanly.
5. All newly added public endpoints have corresponding integration tests.
6. Golden regression tests show **0 false matches**.
