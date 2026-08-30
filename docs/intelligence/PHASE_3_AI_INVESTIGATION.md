# METFI Phase 3 Architecture: AI Investigation & Evidence-Grounded Reasoning

## 1. System Overview & Core Invariant

METFI Phase 3 introduces **Layer 4: AI Investigation & Verification**, an evidence-grounded intelligence subsystem designed to explain, categorize root causes, and provide bounded recommendations for reconciliation exceptions.

### Fundamental Principle
> **Financial truth is deterministic. AI provides investigation, explanation, and bounded recommendations.**

Under no circumstances can an AI inference:
1. Override deterministic reconciliation classifications.
2. Mutate ledger records or authorize payments directly.
3. Access ground truth labels, corruption classes, or benchmark metadata.
4. Invent financial policies or assume contract fee/tax rates when unconfigured.
5. Bypass policy gates.

```
+-----------------------------------------------------------------------------------+
|                            INFERENCE EXECUTION PIPELINE                           |
|                                                                                   |
|  [Raw Sources] ➔ [Deterministic Reconciliation Engine] ➔ [ReconciliationResult]   |
|                                                                   |               |
|                                                                   v               |
|                                                      [AI Context Builder]         |
|                                                                   |               |
|                                                                   v               |
|                                                         [AI Investigator]         |
|                                                                   |               |
|                                                                   v               |
|                                                           [AI Verifier]           |
|                                                                   |               |
|                                                                   v               |
|                                                  [VerifiedInvestigationEnvelope]  |
|                                                                   |               |
|                                                                   v               |
|                                                        [Deterministic Policy]     |
|                                                                   |               |
|                                                                   v               |
|                                                            [Audit Trail]          |
+-----------------------------------------------------------------------------------+
```

---

## 2. Component Architecture

### 2.1 Provider Abstraction Layer (`backend/app/intelligence/provider.py`)
Compliant with **ADR-005**:
- Abstract interface: `LLMProvider` (`generate_text`, `generate_structured`, `health_check`).
- `MockLLMProvider`: Deterministic local mock supporting configurable test scenarios (`correct`, `unknown_policy`, `insufficient_evidence`, `unsupported_claim`, `malformed`, `timeout`).
- `GeminiLLMProvider`: Google Gemini provider adapter.
- `OpenAILLMProvider`: OpenAI, NVIDIA NIM / Nemotron, and local Ollama compatible adapter.
- Factory: `get_llm_provider(provider_name, **kwargs)`.

### 2.2 Security Boundary & Context Builder (`backend/app/intelligence/context_builder.py`)
- **Zero Ground Truth Exposure**: The builder accepts only legitimate runtime domain objects (`case_id`, `ReconciliationResult`, `CanonicalTransactionGroup`, `FeeTaxPolicy`).
- **Prompt Injection Defense**: Untrusted merchant metadata, descriptions, and customer comments are sanitized and enclosed within strict boundary blocks (`--- [UNTRUSTED SOURCE RECORD DETAILS] ---`).
- **Citation Whitelisting**: Generates a runtime whitelist of valid dot-notated field paths (`[VALID CITATION FIELD PATHS]`) for verifiable evidence citations.
- **Unknown Policy Notification**: When fee policy is absent, explicitly signals `fee_policy.status: UNKNOWN` and forbids guessing.

### 2.3 AI Investigator (`backend/app/intelligence/investigator.py`)
- Executes evidence-grounded root cause analysis using `investigator_v1.py` system prompts.
- Outputs structured Pydantic schema (`InvestigationResult`) with:
  - `status`: `INVESTIGATED`, `INSUFFICIENT_EVIDENCE`, `POLICY_UNAVAILABLE`, `UNAVAILABLE`, `ERROR`.
  - `root_cause_category`: 12-class standard taxonomy (`PROCESSING_FEE_DEDUCTION`, `CURRENCY_CONVERSION_VARIANCE`, `AMBIGUOUS_CANDIDATE_TIE`, etc.).
  - `evidence_references`: Field-level citations validated against the context whitelist.
  - `recommended_action`: Bounded actions only (`AUTO_RECONCILE`, `REVIEW_REQUIRED`, `UNRESOLVED`).
  - `model_metadata`: Latency, provider name, prompt version.

### 2.4 AI Verifier (`backend/app/intelligence/verifier.py`)
- Independent verification stage challenging the investigation output.
- **Deterministic Hard Gates**:
  1. **Citation Validation**: Rejects investigations citing uncertified or fabricated field paths.
  2. **Truth Preservation Gate**: Rejects any attempt to recommend `AUTO_RECONCILE` on blocking exceptions (`CURRENCY_MISMATCH`, `MISSING_SETTLEMENT`, `DUPLICATE_RECORD`).
  3. **Policy Safety Gate**: Rejects `AUTO_RECONCILE` if contract policy is unknown or unapproved fee/tax variance exists.
- **Second-Opinion Verification**: LLM verifier validates logical consistency.
- Emits `VerificationResult` (`VERIFIED`, `REJECTED`, `INSUFFICIENT_EVIDENCE`).

### 2.5 Investigation Service (`backend/app/services/investigation_service.py`)
- Orchestrates the full closed loop.
- Performs case triage: skips exact matches or returns instant pre-verified envelope.
- Enforces: `envelope.final_canonical_status == deterministic_result.classification`.
- Supports bounded concurrent batch processing.

---

## 3. Evaluation & Benchmarking

### 8-Dimension Evaluation Harness (`backend/app/evaluation/ai_evaluator.py`)
1. **Root-Cause Accuracy**: >= 90.0%
2. **Evidence Grounding Rate**: 100.0%
3. **Unsupported Claim Rate**: 0.0%
4. **Recommendation Safety**: 100.0%
5. **Deterministic Truth Preservation**: **100.0% (Mandatory)**
6. **Verifier Rejection Rate**: Tracked (flags unsafe/hallucinated attempts)
7. **Safe Fallback Rate**: 100.0%
8. **Malformed Output Rate**: 0.0%

### Independent Benchmark Suite (`evaluation/benchmarks/ai_runner.py`)
Executed via:
```bash
python evaluation/benchmarks/ai_runner.py --provider mock
```
Outputs comprehensive comparative report to `evaluation/reports/AI_INVESTIGATION_BENCHMARK_REPORT.md`.
