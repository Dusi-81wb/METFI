# Phase 5 Specification: Audit Trail, Traceability & Observability

## 1. Executive Overview

METFI operates under a strict principle of financial accountability:
> **A finance controller is only trustworthy if it can explain itself after the fact.**

Every calculation, AI investigation, policy evaluation, action authorization, execution, and human review produces an immutable, append-only, tamper-evident audit record.

```
[State Transition / Lifecycle Stage]
                 │
                 ▼
     [Audit Sanitizer & Redactor]  ──> Masks API keys/credentials, strips synthetic ground truth
                 │
                 ▼
       [Audit Hash Chainer]        ──> Deterministic SHA-256 (canonical JSON + previous_event_hash)
                 │
                 ▼
     [Append-Only Repository]      ──> PostgreSQL (CREATE & READ only; no UPDATE/DELETE)
                 │
                 ▼
  [Integrity Verifier & APIs]      ──> Validates chain continuity, sequence numbers & coherence
```

---

## 2. Audit vs. Application Logging

| Attribute | Application Logs (`logging.py`) | Audit Trail (`AuditEvent`) |
|---|---|---|
| **Purpose** | Operational diagnostics & debugging | Authoritative financial & compliance history |
| **Immutability** | Rotated, truncated, or sampled | Immutable after creation; append-only |
| **Integrity** | Plaintext, vulnerable to alteration | Cryptographically linked via SHA-256 hash chains |
| **Structure** | Unstructured or semi-structured log lines | Strongly typed Pydantic & SQLAlchemy domain records |
| **Attribution** | Process ID / Logger name | Attributable `Actor` (System, Deterministic, AI, Human) |
| **Traceability** | Transient thread IDs | Persistent `case_id` and `correlation_id` chains |

---

## 3. Domain Model & Event Taxonomy

### Event Taxonomy (`AuditEventType`)
- `CASE_CREATED`: Initial intake of reconciliation case.
- `RECONCILIATION_COMPLETED`: Output of deterministic matching engine.
- `INVESTIGATION_STARTED` / `INVESTIGATION_COMPLETED`: AI evidence synthesis & reasoning.
- `VERIFICATION_COMPLETED`: AI verifier adversarial critique & certification.
- `POLICY_EVALUATED`: Deterministic governance decision.
- `ACTION_REQUESTED` / `ACTION_AUTHORIZED` / `ACTION_REJECTED`: Action governance transitions.
- `ACTION_EXECUTING` / `ACTION_EXECUTED` / `ACTION_FAILED`: Controlled simulation executor lifecycle.
- `REVIEW_CREATED` / `REVIEW_CLAIMED` / `REVIEW_RESOLVED` / `REVIEW_ESCALATED`: Controller review operations.

### Immutable Event Schema (`AuditEvent`)
- `event_id`: Unique prefixed ID (`evt_<12-hex>`).
- `event_type`: Categorical event type from taxonomy.
- `case_id`: Primary reconciliation case reference.
- `correlation_id`: End-to-end workflow tracing identifier.
- `sequence_number`: Monotonically increasing sequence number per case (`1, 2, 3...`).
- `timestamp`: ISO 8601 UTC timestamp.
- `source_component`: Originating module name.
- `actor`: `Actor(actor_type, actor_id, display_name)`.
- `payload`: Sanitized, redacted, and ground-truth isolated dictionary.
- `evidence_references`: Cited evidence references.
- `policy_version`: Policy version evaluated.
- `ai_trace`: Safe inference telemetry (`provider`, `model_name`, `prompt_version`, `latency_ms`).
- `reconciliation_id`, `investigation_id`, `verification_id`, `policy_decision_id`, `action_id`, `review_id`.
- `previous_event_hash`: SHA-256 hash of preceding event (or `"GENESIS"`).
- `event_hash`: SHA-256 hash computed over canonical JSON serialization.

---

## 4. Tamper-Evident Hash Chaining

### Serialization & Hashing Specification
1. The event dictionary is extracted, excluding `event_hash`.
2. All keys are sorted recursively and serialized using compact JSON formatting: `json.dumps(..., sort_keys=True, separators=(',', ':'))`.
3. The raw string `f"{previous_event_hash}:{canonical_json}"` is hashed with SHA-256.

$$\text{event\_hash}_n = \text{SHA-256}(\text{previous\_event\_hash}_n \mathbin{\Vert} \text{CanonicalJSON}(\text{Event}_n \setminus \{\text{event\_hash}\}))$$

### Threat Model & Integrity Guarantees
- **Tamper Evidence:** The hash chain provides undeniable mathematical evidence if an adversary modifies event payloads, inserts fake events, deletes events, or breaks sequence continuity.
- **Scope:** Protects against application-level forgery and state corruption. Privileged database administrator modifications are detected immediately upon verification.

---

## 5. Security & Isolation Controls

1. **Automated Secret Redaction (`AuditSanitizer`):**
   - Regex patterns mask API keys (`sk-...`, `AIza...`, `ghp_...`), Bearer JWT tokens, and basic authorization strings.
   - Dictionary keys such as `password`, `secret`, `api_key`, `token` are replaced with `"[REDACTED_SECRET]"`.
2. **Ground-Truth Isolation:**
   - Synthetic evaluation parameters (`ground_truth`, `expected_classification`, `corruption_manifest`, `generator_seed`) are stripped before storage to prevent benchmark leakage into production history.

---

## 6. Audit Query & Verification API

- `GET /api/v1/audit/cases/{case_id}`: Retrieves full chronological case history timeline.
- `GET /api/v1/audit/cases/{case_id}/verify`: Executes mathematical and logical verification, returning `VALID` or `INTEGRITY_FAILURE` with diagnostic violations.
- `GET /api/v1/audit/events/{event_id}`: Retrieves single immutable audit event.
- `GET /api/v1/audit/metrics`: Retrieves structured operational metrics, latencies, and counters.
