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
│   ├── test_normalization.py     # Schema validation, decimal handling, currency formatting
│   ├── test_rules.py             # Deterministic matching rules (amounts, dates, references)
│   ├── test_policy.py            # Policy engine gate evaluations
│   └── test_audit.py             # Audit trail event creation and serialization
├── integration/
│   ├── test_reconciliation_pipeline.py  # End-to-end ingestion -> matching -> policy flow
│   ├── test_api_endpoints.py            # FastAPI route tests via HTTPX AsyncClient
│   └── test_db_persistence.py           # PostgreSQL persistence and retrieval
└── golden/
    └── test_golden_fixtures.py   # Golden benchmark fixtures across all 10 exception classes
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
