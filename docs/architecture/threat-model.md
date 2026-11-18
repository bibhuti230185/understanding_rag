# Threat Model

**Scope**: Browser, public edge, identity, API, ingestion, S3/SQS, metadata, cache, vector store, model providers, telemetry, and deployment pipeline.

**Method**: Lightweight STRIDE review of the trust boundaries in the Phase 1 HLD. This is an initial design review, not a penetration test or compliance assessment.

## Assets

- Tenant documents, extracted text, chunks, embeddings, citations, and derived indexes.
- Tenant/user identity claims, roles, authorization decisions, and API credentials.
- Conversations, questions, generated answers, feedback, and audit records.
- S3 objects, queue messages, database records, cache entries, vector records, and backups.
- Model prompts/completions, API keys, tracing data, deployment credentials, and encryption keys.

## Trust Boundaries

1. Browser to public edge and API.
2. Identity provider to application token validation.
3. User-controlled upload to quarantined object storage and asynchronous worker.
4. API/worker to PostgreSQL, Redis, SQS, S3, and vector adapter.
5. Application to external LLM/embedding and Langfuse services.
6. CI/CD identity to AWS deployment/control plane.
7. Tenant-scoped records to operator/evaluator access.

## Threats and Controls

| ID | Threat / abuse case | Primary controls | Residual risk |
|---|---|---|---|
| T-01 | Broken object-level authorization exposes another tenant's document, conversation, or job | Validate signed identity; derive tenant from trusted claims/membership; enforce ownership in every use case and repository query; deny by default; audit privileged access | Misconfigured policy or missing check remains possible; add tenant-isolation tests in Phase 9 |
| T-02 | Vector search or cache key omits tenant/document ACL filters | Require scope in the vector-store port; adapter enforces mandatory filters; include tenant, authorized filters, and index version in cache keys; re-authorize cache results | Adapter/filter regression can cause cross-tenant leakage; fail closed and test at integration level |
| T-03 | Malicious, malformed, oversized, or parser-exploit file compromises ingestion | Presigned upload restricted to one object/key/size/time; quarantine; MIME and content validation; malware scan; parser isolation/resource limits; allowlisted formats; no public object access | Scanner/parser zero-days remain; require patching, monitoring, and incident response |
| T-04 | Prompt injection embedded in retrieved documents changes instructions or triggers unsafe tool behavior | Treat retrieved content as untrusted evidence; isolate system policy from source text; no secrets in prompts; constrain tools; validate citations and authorization outside the LLM | Model may still produce unsafe or incorrect text; evaluate adversarial corpus and provide refusal/feedback path |
| T-05 | Unsupported or unauthorized content is presented as a cited answer | Retrieve only authorized chunks; validate citation IDs against retrieval set; insufficient-evidence behavior; citation correctness evaluations | Model can misstate supported evidence; use regression evaluation and incident review |
| T-06 | Stolen token or over-broad upload URL is replayed | Short-lived signed tokens; constrained single-object presigned upload; TLS; validate tenant/object association on completion; revoke/expire credentials | Active session compromise remains possible; add rate limits and anomaly detection |
| T-07 | Duplicate or replayed queue message corrupts index or creates duplicate chunks | At-least-once delivery assumed; stable document-version idempotency key; idempotent upsert; durable state transitions; reconciliation | Partial-write scenarios need implementation-level integration tests |
| T-08 | Queue poison message exhausts resources or blocks ingestion | Bounded retries/backoff; visibility timeout; DLQ and queue-age alarms; operator-controlled replay | DLQ backlog can delay one tenant's documents until triaged |
| T-09 | Sensitive prompt, source text, or PII leaks through logs/traces/cache or external provider | Structured logs use IDs/categories rather than content; redact/minimize Langfuse payloads; tenant-scoped cache; TLS and encryption at rest; provider data-processing review | Provider retention/subprocessor exposure depends on contract and configuration |
| T-10 | SSRF, unsafe URL fetch, or credential theft occurs during document processing | Process uploaded bytes only; no automatic URL fetch; strict egress allowlist; secret manager; least-privilege task roles | New parser integrations may introduce outbound fetch behavior; review dependencies |
| T-11 | Publicly exposed or weakly protected database/vector service allows data theft or tampering | Private subnets; security-group allowlists; no public listeners; TLS; KMS encryption; least-privilege service identities; backups | Misconfiguration remains possible; validate IaC and monitor configuration drift |
| T-12 | CI/CD compromise deploys malicious image or exfiltrates AWS credentials | GitHub OIDC short-lived roles; least privilege; branch/environment protection; pinned/reviewed actions; dependency/image scanning; deployment audit | Supply-chain compromise remains possible; add provenance/signing policy before production |
| T-13 | Evaluator or platform operator accesses tenant data without need | Separate roles; least privilege; audited break-glass access; redacted evaluation sets; tenant-scoped admin workflows | Insider misuse cannot be fully eliminated; define approval and review policy |
| T-14 | Deletion leaves searchable copies in vectors, cache, backups, or telemetry | Mark unavailable immediately; delete all derived records and cache keys; reconcile index; enforce documented backup/retention policy; minimize content in telemetry | Backups/provider traces may outlive active data under retention policy; exact deletion SLA and retention need approval |

## Security Requirements for Later Phases

- Implement authorization checks and tenant-scoped repository/vector interfaces before exposing multi-tenant data.
- Test cross-tenant read/write, cache, search, deletion, and admin/evaluator paths with negative cases.
- Define accepted file size/page limits, parser sandbox/resource limits, malware-scanning outcome states, and quarantine retention.
- Decide compliance, region, provider data-retention, encryption-key rotation, audit retention, and deletion SLAs.
- Validate AWS IAM, network, encryption, backup, and CI/CD controls through IaC/security testing before production.
- Run prompt-injection, malicious-file, broken-access-control, and data-leakage evaluations before each release.

