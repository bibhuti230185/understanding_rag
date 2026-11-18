# Product and Architecture Risk Register

| ID | Risk | Likelihood / impact | Mitigation | Owner / trigger |
|---|---|---|---|---|
| R-01 | Cross-tenant document, vector, cache, conversation, or evaluation data leakage | Medium / Critical | Server-derived tenant scope; deny-by-default authorization; tenant filters at every adapter; cache partitioning; negative isolation tests; audited operator access | Security lead; any cross-tenant test failure or incident |
| R-02 | Prompt injection in uploaded/retrieved text influences answer behavior | High / High | Treat content as untrusted evidence; isolate policy from retrieved text; restrict tools; validate citations; adversarial evaluation corpus | AI lead; prompt/model/retrieval change or injection finding |
| R-03 | Incorrect or misleading citations erode trust | Medium / High | Citation-source mapping; validate source IDs/locations; insufficient-evidence behavior; golden-set citation evaluation and release threshold | Product/AI; citation correctness below provisional 95% |
| R-04 | Model/embedding latency, throttling, outage, or price change violates latency and cost goals | High / High | Provider abstraction; deadlines and bounded retries; budget/token telemetry; kill switch and explicit error; evaluate fallback only after quality testing | Platform/AI; p95 or cost target exceeded or provider incident |
| R-05 | Self-managed ChromaDB lacks required production durability or horizontal scale | Medium / High | Keep behind port; isolate state; test backup/restore and failure recovery; define managed-vector migration trigger | Platform; failed restore/scale test or target availability not met |
| R-06 | Malicious/malformed files exploit parsers or exhaust worker resources | Medium / High | Quarantine, MIME/content validation, malware scan, parser isolation, resource/time limits, allowlist, retry/DLQ | Security/ingestion; scanner finding, resource exhaustion, parser CVE |
| R-07 | Duplicate queue delivery or partial writes create duplicate/stale index state | Medium / Medium | Stable idempotency identity; upsert/delete by document version; durable state transitions; reconciliation; replay controls | Ingestion owner; duplicate index or mismatch detected |
| R-08 | Deletion leaves residual content in vectors, cache, backups, logs, or provider traces | Medium / High | Immediate access revocation; async cleanup and reconciliation; retention policy; minimize telemetry payloads; document provider retention | Privacy/platform; deletion request or audit finding |
| R-09 | Provisional SLO targets are unrealistic for selected workload/provider | High / Medium | Label as hypotheses; define workload envelope; benchmark before commitment; separate service and model/provider budgets | Product/platform; Phase 4/9 baseline review |
| R-10 | Unspecified compliance, retention, or residency requirements force architecture rework | Medium / High | Early stakeholder discovery; keep storage/provider adapters replaceable; avoid committing sensitive data to telemetry | Product/security; before production onboarding |
| R-11 | Admin/evaluator/platform-operator permissions become overly broad | Medium / High | Separate roles; resource-level authorization; break-glass workflow with approval/audit; redact evaluation data | Security; access review or privileged operation |
| R-12 | CI/CD or dependency supply-chain compromise introduces malicious code or credentials | Low / Critical | OIDC short-lived roles; least privilege; protected environments; action/dependency/image scanning; deployment audit | Platform/security; release pipeline change or vulnerability alert |

## Risk Review Cadence

Review at Phase 4 vertical-slice exit, before production readiness, and after material identity, parser, model, vector-store, or deployment changes. Record a named owner and due date before any risk is accepted for production.

