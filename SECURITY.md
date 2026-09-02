# METFI Security & Trust Architecture
**Financial-Grade Isolation, Threat Modeling, Prompt-Injection Defenses & Cryptographic Auditability**

**Project:** METFI (Autonomous Finance Controller)  
**Security Standard:** Enterprise Financial Infrastructure  

---

## 1. Non-Negotiable Security Invariants

Financial systems require defense-in-depth and strict boundaries around AI reasoning:

1. **Deterministic Authority Hierarchy**:
   `Deterministic Truth > Policy Engine > AI Recommendation > Action Executor`.
   An AI model can never override mathematical truth or waive policy limits.
2. **Zero Direct Financial Write Access for AI**:
   AI reasoning runtimes (Investigator, Resolver, Verifier) have **zero database write permissions**. State changes occur only through deterministic policy-authorized execution routines.
3. **Independent Automated AI Verification**:
   No AI hypothesis enters policy evaluation without independent verification against explicit field evidence. Hallucinations or ungrounded assertions are rejected 100%.
4. **Tamper-Evident Cryptographic Audit Ledger**:
   Audit events are cryptographically hash-chained (`previous_event_hash` SHA-256). Any modification, deletion, or event reordering breaks chain continuity and is flagged instantly.
5. **Strict Ground-Truth Isolation**:
   Evaluation ground truth is strictly segregated from the operational pipeline. Zero expected labels or corruption metadata are exposed in LLM prompts, ingestion records, or API responses.

---

## 2. Threat Modeling & Defenses

| Threat Vector | Description | METFI Defense Mechanism |
|---|---|---|
| **System Prompt Hijacking** | Adversary attempts delimiter breakouts (`===`, `---`, ````) or role injection (`SYSTEM: override policy`). | `sanitize_untrusted_text` in `context_builder.py` strips delimiter breakouts, command tokens (`<|im_start|>`), and jailbreak directives. |
| **Arithmetic Hallucination** | LLM fabricates fee schedules or alters discrepancy amounts. | Mathematical amounts and deltas are computed exclusively by deterministic Python `Decimal` routines before context assembly. |
| **Unauthorized Action Execution** | Direct HTTP call attempts to trigger action without policy approval. | Action executor enforces cryptographically validated authorization tokens and precondition checks. |
| **Race Conditions / Double-Spend**| Rapid duplicate submissions trigger duplicate ledger adjustments. | Strict idempotency keys (SHA-256) and per-action mutex locks guarantee single-execution semantics. |
| **Audit Log Tampering** | Malicious actor modifies persisted audit event amounts in database. | `AuditIntegrityVerifier` validates SHA-256 canonical event hashes and links against the genesis block. |
| **API Secret Leakage** | API keys or tokens logged in traces or returned in responses. | `AuditSanitizer` runs automated regex redaction scrubbing API keys (`sk-*`, `AIza*`), bearer tokens, and credentials. |

---

## 3. Emergency Circuit Breakers

- **Master Autonomous Kill-Switch**:
  `DomainPolicyConfig.auto_reconciliation_enabled` allows operational risk officers to instantaneously disarm autonomous resolution globally, routing 100% of cases to human review queues.
- **Monetary Variance Thresholds**:
  Autonomous reconciliation is strictly capped at `max_auto_reconcile_amount` (default: ₹100,000.00) and `max_absolute_fee_variance` (default: ₹150.00).

---

## 4. Verification & Continuous Security Testing

METFI maintains automated security test suites in `backend/tests/unit/test_phase8_security_and_injection.py` and `backend/tests/unit/test_phase8_action_security.py` covering:
- SQL injection immunity
- Delimiter and markdown escape neutralization
- Idempotency deduplication under concurrency
- Cryptographic hash verification under deliberate payload tampering
- Automated secret scrubbing on audit records
