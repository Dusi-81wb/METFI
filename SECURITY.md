# METFI Security & Safety Boundaries

**Project:** METFI (Autonomous Finance Controller)  
**Security Classification:** Financial Infrastructure Grade  

---

## 1. Core Security & Safety Principles

Financial systems demand strict isolation, defense-in-depth, and non-negotiable boundaries around autonomous AI agents. METFI adheres to the following core security principles:

### 1.1 Model Isolation & Zero Direct Database Writes
- **Read-Only / Inference-Only Agent Access:** AI reasoning models (Investigator, Resolver, Verifier) interact purely with structured in-memory payloads provided to them by the controller service.
- **No Direct DB Connections for LLMs:** Under no circumstances are database credentials, raw SQL execution tools, or write permissions made available to model execution runtimes.
- **Strict Pydantic Output Validation:** LLM output is parsed against strict Pydantic schemas. Unparseable, schema-invalid, or malformed responses are treated as exceptions (`UNRESOLVED`), never coerced or assumed.

### 1.2 Policy-Gated Mutation & Execution
- **Deterministic Policy Supremacy:** AI models can only generate *recommendations*. All state mutations (e.g. marking a case as auto-reconciled, escalating to human review) are executed by deterministic code after passing through the Policy Engine.
- **Hard Constraints Cannot Be Overridden:** An AI model cannot waive mathematical discrepancies, currency mismatches, or missing primary records.

---

## 2. Secrets Management & Environment Security

- **Zero Hardcoded Secrets:** No API keys, database passwords, or private tokens may be committed to version control.
- **Environment Variable Configuration:** Secrets are loaded strictly via `.env` files managed through `pydantic-settings` (`BaseSettings`).
- **Standardized `.env.example`:** Every configurable parameter is documented in `.env.example` with safe placeholder values.
- **Log Sanitization:** Sensitive authorization tokens, database connection URIs with embedded credentials, and customer PII are redacted from structured logging output.

---

## 3. Data Protection & Privacy

- **Synthetic Data by Default:** For development, benchmarking, and hackathon demonstrations, 100% synthetic data generated with deterministic seeds is utilized.
- **PII Minimization:** Customer identifiers in synthetic and production feeds are tokenized (`cust_anon_...`).
- **Prompt Sanitization:** Prompts sent to external AI providers include only the minimum necessary transaction context (amounts, timestamps, status codes, reference IDs), excluding unnecessary payload metadata.

---

## 4. Audit Trail Integrity

- **Append-Only Logging:** Audit records generated for reconciliation decisions are immutable from the application perspective.
- **Cryptographic Traceability:** Audit payloads record the exact engine version, policy version, AI model identifier, timestamp, and cryptographic hash of the input records.
- **Tamper Evidence:** Audit entries provide full historical lineage for compliance and forensic review.

---

## 5. Network & API Security

- **CORS Configuration:** Explicit origin whitelisting in FastAPI backend (`BACKEND_CORS_ORIGINS`).
- **Input Validation:** Every HTTP request body is validated at the FastAPI router boundary with Pydantic v2 schemas to prevent injection and malformed payload attacks.
- **Resource Limits & Rate Limiting:** Batch ingestion and reconciliation endpoints implement payload size validation to guard against Denial-of-Service (DoS) memory exhaustion.
