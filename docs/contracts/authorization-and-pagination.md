# Authorization, Tenant Scope, and Pagination

## Tenant and Role Resolution

1. Validate the bearer token signature, issuer, audience, expiry, and required claims.
2. Map the verified subject to an active user and active tenant membership. Resolve tenant scope server-side.
3. Authorize the requested action by role and resource-level policy. Client `tenant_id`, document filters, conversation IDs, and citations are selectors only; each selected resource is independently checked.
4. Apply tenant and resource filters in the metadata adapter and `VectorStore` port. Cache retrieval results by tenant and authorized scope and revalidate before returning.
5. Audit privileged actions, denied access, delete/retry/replay, and evaluator/platform access without logging document content.

## Initial Role Matrix

| Operation | Tenant admin | Normal user | Evaluator | Platform operator |
|---|---|---|---|---|
| Upload document | Yes, tenant scope | Yes, tenant policy / own upload | No by default | No by default |
| List/read document status | All tenant documents | Authorized tenant documents; own upload status | Only dataset/run-authorized sources | Operational metadata; content only via approved break-glass |
| Chat/citations | Yes, tenant scope | Yes, authorized document scope | Only approved evaluation context | No by default |
| Delete document | Yes, tenant scope | Own upload subject to tenant policy | No | Recovery/remediation only via audited break-glass |
| Submit feedback | Yes | Yes, authorized conversation | May annotate approved run | No |
| Create/read evaluation run | Tenant-approved scope | No by default | Yes, permitted datasets | Operate service; no implicit content access |
| Retry/replay ingestion | Tenant admin may request | No | No | Yes, audited and idempotent |

This is the initial policy proposal. Tenant policy may narrow these rights; no policy may grant cross-tenant access through a request parameter alone.

## Filtering

- Document list supports server-defined `status` and `createdAfter` filters; no `tenant_id` filter is exposed.
- Chat may request a set of document IDs (maximum 100), but the API verifies each ID belongs to an authorized tenant scope before retrieval.
- Sort fields and directions are allowlisted by endpoint. Arbitrary filter expressions, SQL fragments, vector-store predicates, and model-generated filters are not accepted from clients.
- A malformed, expired, or filter-mismatched cursor returns `400 invalid_cursor`; it never restarts at an unfiltered first page silently.

## Cursor Pagination

- Default `limit=25`, allowed range `1..100`.
- Cursor is opaque, integrity-protected, bound to tenant, endpoint, sort order, and canonical filters, and expires according to the configured replay window.
- Use stable keyset ordering with a unique tie-breaker (for example `(created_at, id)`), not offset pagination for changing datasets.
- Response returns `items` and nullable `next_cursor`; absence means the page is terminal.
- A cursor from a different tenant, endpoint, or filter combination is rejected.

## Resource Concealment

For resources outside the caller's tenant or ACL, return `404` where revealing existence could expose another tenant's identifiers. Use `403` for an authenticated principal whose access decision can be safely disclosed (for example, missing role on a known tenant admin endpoint). Apply one consistent policy across APIs to avoid identifier oracles.

