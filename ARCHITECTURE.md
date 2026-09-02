# METFI System Architecture Specification
**Production Modular Monolith with Strict Layer Boundaries**

- **Project:** METFI (Autonomous Finance Controller)  
- **Track:** Razorpay AI Buildathon, Track 04 — AI Finance Controller  
- **Architecture Standard:** Separation of Deterministic Truth & Advisory Intelligence  

---

## 1. Architectural Invariant

> **Deterministic Financial Truth > Policy Engine > AI Recommendation > Action Executor.**

In METFI, deterministic code owns mathematical calculation, candidate matching, exception categorization, policy gating, and ledger state transitions. AI reasoning models provide advisory anomaly investigations and causal explanations—subject to independent automated challenge and policy authorization.

```mermaid
flowchart TD
    subgraph DataPlane ["1. Data Plane (Deterministic)"]
        A1[Synthetic Generator] --> A2[Golden Fixtures]
        A3[Ground Truth Isolator]
    end

    subgraph IngestionNormalization ["2. Ingestion & Normalization (Deterministic)"]
        B1[Payment Gateway Feeds] --> C1[Canonical Schemas]
        B2[Bank Settlement Files] --> C1
        B3[General Ledger Records] --> C1
        C1 --> C2[Decimal Monetary & UTC ISO 8601]
    end

    subgraph DeterministicEngine ["3. Deterministic Reconciliation Engine (Deterministic)"]
        C2 --> D1[Candidate Matcher]
        D1 --> D2[10-Rule Classification Precedence]
        D2 --> D3[Evidence Matrix Extraction]
    end

    D2 -->|Exact Matches| F1[Policy Outcome: AUTO_RECONCILE]
    D2 -->|Exceptions & Discrepancies| E1

    subgraph AdvisoryIntelligence ["4. Advisory Intelligence Layer (AI-Assisted)"]
        E1[AI Investigator] -->|Structured Hypothesis| E2[Evidence References]
        E2 --> E3[Independent AI Verifier Gate]
    end

    E3 -->|Verified Envelope| F2

    subgraph Governance ["5. Policy & Controlled Execution (Deterministic)"]
        F1 --> F2[Deterministic Policy Engine]
        F2 -->|Within Tolerances| G1[Action Authorization Token]
        F2 -->|Exceeds Tolerances / Tie| G2[Human Operations Review Queue]
        G1 --> G3[Controlled Action Executor]
        G3 -->|SHA-256 Idempotency Check| G4[Simulation Journal Mutation]
    end

    subgraph AuditObservability ["6. Audit & Observability (Deterministic)"]
        G4 --> H1[SHA-256 Event Hash Chaining]
        G2 --> H1
        H1 --> H2[AuditIntegrityVerifier]
        H2 --> H3[Live Operations Console & Dashboard]
    end
```

---

## 2. Delineation of Layer Responsibilities

| Layer | Component | Execution Nature | Authority Level | Can Mutate State? |
|---|---|---|---|---|
| **Layer 1** | Data Plane & Ingestion | Deterministic | Input Validator | No |
| **Layer 2** | Canonical Normalization | Deterministic | Mathematical Standardizer | No |
| **Layer 3** | Reconciliation Matcher | Deterministic | Authoritative Truth | No |
| **Layer 4** | AI Investigator | **AI-Assisted (Advisory)** | Structured Hypothesis | **NO** |
| **Layer 5** | AI Verifier Gate | **AI-Assisted / Rule Hybrid** | Factual Challenge Gate | **NO** |
| **Layer 6** | Policy Engine | Deterministic | Authorization Authority | No |
| **Layer 7** | Action Executor | Deterministic | Controlled Executor | **YES (Policy Gated)** |
| **Layer 8** | Cryptographic Audit Ledger | Deterministic | Immutable Recorder | Append-Only |
| **Layer 9** | Operations Dashboard & Benchmarks | UI / Evaluator | Presentation & Reporting | No |

---

## 3. Technology Stack

- **Backend**: Python 3.12, FastAPI 0.111, Pydantic v2, SQLAlchemy 2.x (asyncpg), PostgreSQL 16
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide React
- **Containerization**: Multi-stage Dockerfiles, Docker Compose (3-tier stack)
- **Quality Assurance**: Pytest (311+ tests), Ruff, Mypy, Playwright/httpx
