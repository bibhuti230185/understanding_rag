# Idempotency, Correlation, and Trace Propagation

## Idempotency

| Operation | Key | Scope and retention | Replay behavior |
|---|---|---|---|
| Create upload intent | Required `Idempotency-Key` header | Tenant + operation + key; retain at least as long as upload intent/job lifecycle and the configured replay window | Same canonical request returns original document/version/upload-intent result; different payload returns `409 idempotency_key_reused` |
| Complete upload | Required `Idempotency-Key` header plus immutable document/version/object version/checksum | Tenant + document version + completion operation | Same completion returns the same logical job; object/version/checksum mismatch returns conflict |
| Delete document | Required `Idempotency-Key` header | Tenant + document + delete operation | Repeated request returns the same accepted deletion outcome; deleted remains terminal |
| Create conversation | Required key | Tenant + user + create-conversation operation | Same request returns same conversation; key/payload mismatch returns conflict |
| Submit chat message | Required key | Tenant + conversation + user + message operation | A retry attaches to the same message/generation result; never creates a second logical message. Event replay is separate and may use `Last-Event-ID` |
| Submit feedback | Required key | Tenant + user + message + feedback operation | Identical retry is idempotent; a later intentional rating update follows the explicit update policy and creates an audit/version record |
| Start evaluation | Required key | Tenant/scope + requester + evaluation operation | Same request returns same run; different dataset/configuration with same key returns conflict |
| Worker event | Internal deterministic identity | Tenant + document version + job type + parser/chunking/embedding/index configuration version | Duplicate delivery is acknowledged; side effects are upserts/conditional transitions |

Store a one-way digest of the canonical request body with the key, along with operation/resource identity and outcome reference. Never use an idempotency key as an authentication credential. Expired keys must not make a deleted resource visible or create a duplicate effect for the same immutable source version.

## Correlation and Trace Fields

- `X-Correlation-ID`: caller-supplied, bounded and character-validated; otherwise generated server-side. Return it on every HTTP response and include it in structured logs and errors.
- `traceparent`: accept valid W3C Trace Context; reject/replace invalid input by starting a new trace. Do not trust inbound sampling flags for sensitive-data policy.
- `tracestate`: optional, size-limited, and allowlisted before propagation outside the process.
- Queue event envelope: include `event_id`, `correlation_id`, and valid `traceparent`; never include bearer tokens or presigned URLs.
- Logs and traces: include tenant pseudonymous ID, user role, operation/resource IDs, model/prompt/index versions, latency, usage, cache outcome, and error category only where needed; minimize source text and raw prompts.
- Background jobs: create a child span from the enqueue trace where supported; preserve correlation ID and trace context across queue retry/DLQ/replay.
- External providers: propagate trace context only when supported and privacy-approved; do not leak internal identifiers or user content in provider metadata.

## Error Model

HTTP errors use `application/problem+json` based on RFC 9457: `type`, `title`, `status`, optional `detail` and `instance`, plus stable `code`, `correlation_id`, and optional field-level `errors`. `detail` is safe for the caller; stack traces and provider internals remain in protected telemetry.

Use `400` for malformed/cursor errors; `401` for missing/invalid identity; `403` for denied role/membership; `404` for absent or intentionally concealed resources; `409` for idempotency/state conflicts; `413`/`415` for upload limits/type; `422` for schema/domain validation; `429` for quotas; `503` for unavailable dependencies; `500` for unexpected failures. Include `Retry-After` only when a retry is meaningful.

